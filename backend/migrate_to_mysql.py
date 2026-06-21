"""
MySQL Migration Script - Urban Mobility Data Explorer

This script exports data from SQLite and creates an optimized MySQL database.

Prerequisites:
  - MySQL Server 5.7+
  - Python: mysql-connector-python (pip install mysql-connector-python)
  - SQLite database: mobility.db

Usage:
  python migrate_to_mysql.py --sqlite-path ./mobility.db --mysql-host localhost --mysql-user root --mysql-password yourpassword --mysql-db urban_mobility

"""

import sqlite3
import argparse
import sys
from pathlib import Path


# ============================================================================
# MySQL Schema (3NF with explicit foreign keys and constraints)
# ============================================================================

MYSQL_CREATE_TAXI_ZONES = """
CREATE TABLE IF NOT EXISTS taxi_zones (
    zone_id INT PRIMARY KEY COMMENT 'Unique NYC taxi zone identifier',
    borough VARCHAR(50) NOT NULL COMMENT 'NYC borough name',
    zone VARCHAR(100) NOT NULL COMMENT 'Zone name',
    service_zone VARCHAR(50) COMMENT 'Service classification',
    geometry LONGTEXT COMMENT 'GeoJSON polygon boundary (WGS84 EPSG:4326)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_zone_name (zone, borough),
    INDEX idx_borough (borough),
    
    CHECK (zone_id > 0 AND zone_id <= 265)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='NYC Taxi Zone Reference Data';
"""

MYSQL_CREATE_TRIPS = """
CREATE TABLE IF NOT EXISTS trips (
    trip_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'Unique trip identifier',
    
    -- Temporal fields (indexed for range queries)
    pickup_datetime DATETIME NOT NULL COMMENT 'ISO 8601 pickup timestamp',
    dropoff_datetime DATETIME NOT NULL COMMENT 'ISO 8601 dropoff timestamp',
    
    -- Geography (indexed for zone-based analytics)
    pulocation_id INT COMMENT 'Pickup zone ID',
    dolocation_id INT COMMENT 'Dropoff zone ID',
    
    -- Trip metrics
    passenger_count INT UNSIGNED COMMENT 'Number of passengers',
    trip_distance DECIMAL(8, 2) COMMENT 'Distance in miles',
    fare_amount DECIMAL(10, 2) COMMENT 'Base fare (USD)',
    tip_amount DECIMAL(10, 2) DEFAULT 0 COMMENT 'Tip amount (USD)',
    total_amount DECIMAL(10, 2) COMMENT 'Total fare (USD)',
    payment_type INT COMMENT '1=Credit,2=Cash,3=No Charge,4=Dispute',
    
    -- Computed fields
    average_speed_mph DECIMAL(8, 2) COMMENT 'Computed: distance/duration',
    tip_percentage DECIMAL(9, 2) COMMENT 'Computed: (tip/fare)*100',
    rush_hour_flag TINYINT(1) DEFAULT 0 COMMENT '1=Weekday 7-10am or 4-7pm, 0=Other',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Primary and Foreign Keys
    FOREIGN KEY (pulocation_id) REFERENCES taxi_zones(zone_id) ON DELETE SET NULL,
    FOREIGN KEY (dolocation_id) REFERENCES taxi_zones(zone_id) ON DELETE SET NULL,
    
    -- Indexes for query optimization
    INDEX idx_pickup_datetime (pickup_datetime, dolocation_id, pulocation_id),
    INDEX idx_pulocation_id (pulocation_id),
    INDEX idx_dolocation_id (dolocation_id),
    INDEX idx_rush_hour_flag (rush_hour_flag),
    INDEX idx_payment_type (payment_type),
    INDEX idx_dropoff_datetime (dropoff_datetime),
    INDEX idx_trip_distance (trip_distance),
    INDEX idx_avg_speed_mph (average_speed_mph),
    
    -- Composite indexes for common queries
    INDEX idx_location_pair (pulocation_id, dolocation_id, pickup_datetime),
    INDEX idx_zone_metrics (pulocation_id, fare_amount, total_amount, trip_distance),
    
    -- Constraints (data quality)
    CHECK (trip_distance > 0),
    CHECK (fare_amount > 0),
    CHECK (total_amount > 0),
    CHECK (dropoff_datetime > pickup_datetime),
    CHECK (passenger_count > 0),
    CHECK (payment_type IN (1, 2, 3, 4)),
    CHECK (rush_hour_flag IN (0, 1))
    
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='NYC Taxi Trip Records - 7.6M trips from January 2019';
"""

def export_sqlite_to_mysql(sqlite_path, mysql_connection):
    """
    Export data from SQLite and insert into MySQL.

    Args:
        sqlite_path (str): Path to SQLite database file
        mysql_connection: Active mysql.connector connection object
    """
    print(f"[INFO] Connecting to SQLite: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_cursor = mysql_connection.cursor()
    
    # ========== Export taxi_zones ==========
    print("[INFO] Exporting taxi_zones...")
    sqlite_cursor.execute("SELECT * FROM taxi_zones ORDER BY zone_id;")
    zones = sqlite_cursor.fetchall()
    
    insert_zone_query = """
    INSERT INTO taxi_zones (zone_id, borough, zone, service_zone, geometry)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        borough=VALUES(borough),
        zone=VALUES(zone),
        service_zone=VALUES(service_zone),
        geometry=VALUES(geometry);
    """
    
    zone_data = [
        (z['zone_id'], z['borough'], z['zone'], z['service_zone'], z['geometry'])
        for z in zones
    ]
    mysql_cursor.executemany(insert_zone_query, zone_data)
    mysql_connection.commit()
    print(f"[OK] Inserted {len(zone_data)} taxi zones")
    
    # ========== Export trips (batch insert for performance) ==========
    print("[INFO] Exporting trips (batch processing)...")
    valid_trip_filter = (
        "WHERE passenger_count > 0 "
        "AND trip_distance > 0 "
        "AND fare_amount > 0 "
        "AND total_amount > 0 "
        "AND payment_type IN (1, 2, 3, 4) "
        "AND dropoff_datetime > pickup_datetime "
        "AND rush_hour_flag IN (0, 1)"
    )
    sqlite_cursor.execute(f"SELECT COUNT(*) as count FROM trips {valid_trip_filter};")
    total_trips = sqlite_cursor.fetchone()['count']
    sqlite_cursor.execute("SELECT COUNT(*) as count FROM trips;")
    raw_trips = sqlite_cursor.fetchone()['count']
    skipped_trips = raw_trips - total_trips
    print(f"[INFO] Total valid trips to export: {total_trips:,}")
    if skipped_trips > 0:
        print(f"[WARN] Skipping {skipped_trips:,} invalid rows that do not meet MySQL constraints")
    
    insert_trip_query = """
    INSERT INTO trips (
        pickup_datetime, dropoff_datetime, passenger_count, trip_distance,
        pulocation_id, dolocation_id, fare_amount, tip_amount, total_amount,
        payment_type, average_speed_mph, tip_percentage, rush_hour_flag
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    
    batch_size = 50000
    offset = 0
    batches = (total_trips + batch_size - 1) // batch_size
    
    for batch_num in range(batches):
        sqlite_cursor.execute(f"""
            SELECT 
                pickup_datetime, dropoff_datetime, passenger_count, trip_distance,
                pulocation_id, dolocation_id, fare_amount, tip_amount, total_amount,
                payment_type, average_speed_mph, tip_percentage, rush_hour_flag
            FROM trips
            {valid_trip_filter}
            LIMIT ? OFFSET ?;
        """, (batch_size, offset))
        
        trips = sqlite_cursor.fetchall()
        trip_data = [
            (
                t['pickup_datetime'], t['dropoff_datetime'], t['passenger_count'], t['trip_distance'],
                t['pulocation_id'], t['dolocation_id'], t['fare_amount'], t['tip_amount'], t['total_amount'],
                t['payment_type'], t['average_speed_mph'], t['tip_percentage'], t['rush_hour_flag']
            )
            for t in trips
        ]
        
        mysql_cursor.executemany(insert_trip_query, trip_data)
        mysql_connection.commit()
        
        progress_pct = min(100, ((batch_num + 1) / batches) * 100)
        print(f"[OK] Batch {batch_num + 1}/{batches} ({progress_pct:.1f}%): "
              f"Inserted {len(trip_data):,} trips")
        
        offset += batch_size
    
    print(f"[OK] Exported {total_trips:,} total trips")
    
    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()


# ============================================================================
# Main Migration Function
# ============================================================================

def migrate_to_mysql(sqlite_path, mysql_host, mysql_user, mysql_password, mysql_db, mysql_port=3306):
    """
    Complete migration: create MySQL schema and import data from SQLite.
    """
    import mysql.connector
    from mysql.connector import Error
    
    try:
        # Connect to MySQL
        print(f"[INFO] Connecting to MySQL: {mysql_host}:{mysql_port}")
        mysql_conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            port=mysql_port,
            autocommit=False
        )
        
        mysql_cursor = mysql_conn.cursor()
        
        # Create database if not exists
        print(f"[INFO] Creating database: {mysql_db}")
        mysql_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_db} "
                           f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        mysql_cursor.execute(f"USE {mysql_db};")
        mysql_conn.commit()
        print(f"[OK] Database created/selected: {mysql_db}")
        
        # Recreate tables to ensure schema changes are applied cleanly
        print("[INFO] Dropping existing tables if present...")
        mysql_cursor.execute("DROP TABLE IF EXISTS trips;")
        mysql_cursor.execute("DROP TABLE IF EXISTS taxi_zones;")
        mysql_conn.commit()
        
        # Create tables
        print("[INFO] Creating tables...")
        mysql_cursor.execute(MYSQL_CREATE_TAXI_ZONES)
        mysql_cursor.execute(MYSQL_CREATE_TRIPS)
        mysql_conn.commit()
        print("[OK] Tables created successfully")
        
        # Export and import data
        export_sqlite_to_mysql(sqlite_path, mysql_conn)
        
        # Verify
        mysql_cursor.execute("SELECT COUNT(*) as count FROM taxi_zones;")
        zone_count = mysql_cursor.fetchone()[0]
        mysql_cursor.execute("SELECT COUNT(*) as count FROM trips;")
        trip_count = mysql_cursor.fetchone()[0]
        
        print(f"\\n[SUMMARY]")
        print(f"  - taxi_zones: {zone_count:,} rows")
        print(f"  - trips: {trip_count:,} rows")
        print(f"[OK] Migration complete!")
        
        mysql_cursor.close()
        mysql_conn.close()
        
        return True
        
    except Error as err:
        print(f"[ERROR] MySQL Error: {err}")
        return False
    except Exception as err:
        print(f"[ERROR] Unexpected error: {err}")
        return False


# ============================================================================
# Command-line Interface
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Migrate Urban Mobility data from SQLite to MySQL'
    )
    parser.add_argument('--sqlite-path', default='./mobility.db',
                       help='Path to SQLite database (default: ./mobility.db)')
    parser.add_argument('--mysql-host', default='localhost',
                       help='MySQL server host (default: localhost)')
    parser.add_argument('--mysql-port', type=int, default=3306,
                       help='MySQL server port (default: 3306)')
    parser.add_argument('--mysql-user', default='root',
                       help='MySQL username (default: root)')
    parser.add_argument('--mysql-password', default='',
                       help='MySQL password (default: empty)')
    parser.add_argument('--mysql-db', default='urban_mobility',
                       help='Target MySQL database name (default: urban_mobility)')
    
    args = parser.parse_args()
    
    # Verify SQLite file exists
    if not Path(args.sqlite_path).exists():
        print(f"[ERROR] SQLite file not found: {args.sqlite_path}")
        sys.exit(1)
    
    # Run migration
    success = migrate_to_mysql(
        args.sqlite_path,
        args.mysql_host,
        args.mysql_user,
        args.mysql_password,
        args.mysql_db,
        args.mysql_port
    )
    
    sys.exit(0 if success else 1)
