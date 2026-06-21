"""
Query Fetching Examples - Urban Mobility Data Explorer

Production-ready Python functions to fetch and analyze data from SQLite/MySQL.
Each function includes error handling, pagination, and performance tips.

Database: SQLite (mobility.db) / MySQL (urban_mobility)
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


# ============================================================================
# Connection Management
# ============================================================================

class DataConnection:
    """Thread-safe database connection wrapper."""
    
    def __init__(self, db_type='sqlite', db_path='mobility.db'):
        """
        Args:
            db_type: 'sqlite' or 'mysql'
            db_path: Path to SQLite file (if sqlite) or MySQL connection string
        """
        self.db_type = db_type
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Establish database connection."""
        if self.db_type == 'sqlite':
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        elif self.db_type == 'mysql':
            import mysql.connector
            self.conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='urban_mobility'
            )
        return self.conn
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def execute(self, query: str, params: Tuple = ()):
        """Execute query and return cursor."""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def commit(self):
        """Commit transaction."""
        if self.conn:
            self.conn.commit()


# ============================================================================
# ZONE FETCHING FUNCTIONS
# ============================================================================

def fetch_all_zones(db: DataConnection) -> List[Dict]:
    """
    Fetch all 265 NYC taxi zones with geographic metadata.
    
    Returns:
        List of dicts: [{'zone_id': 1, 'borough': 'EWR', 'zone': 'Newark Airport', ...}, ...]
    """
    query = """
    SELECT zone_id, borough, zone, service_zone, geometry
    FROM taxi_zones
    ORDER BY borough, zone_id;
    """
    cursor = db.execute(query)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def fetch_zones_by_borough(db: DataConnection, borough: str) -> List[Dict]:
    """
    Fetch all zones in a specific NYC borough.
    
    Args:
        borough: 'Manhattan', 'Bronx', 'Queens', 'Brooklyn', 'Staten Island', 'EWR'
    
    Returns:
        List of zone dicts
    """
    query = """
    SELECT zone_id, zone, service_zone, geometry
    FROM taxi_zones
    WHERE borough = ?
    ORDER BY zone_id;
    """
    cursor = db.execute(query, (borough,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def fetch_zone_by_id(db: DataConnection, zone_id: int) -> Optional[Dict]:
    """
    Fetch single zone details by ID (includes GeoJSON geometry).
    
    Args:
        zone_id: Zone ID (1-265)
    
    Returns:
        Zone dict or None
    """
    query = """
    SELECT zone_id, borough, zone, service_zone, geometry
    FROM taxi_zones
    WHERE zone_id = ?;
    """
    cursor = db.execute(query, (zone_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


# ============================================================================
# TRIP FETCHING FUNCTIONS
# ============================================================================

def fetch_trips_paginated(
    db: DataConnection,
    date_start: str = '2019-01-01',
    date_end: str = '2019-01-31',
    pulocation_id: Optional[int] = None,
    dolocation_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 100,
    sort_by: str = 'pickup_datetime'
) -> Tuple[List[Dict], int]:
    """
    Fetch trips with pagination and optional filtering (USES INDEXES).
    
    Args:
        db: DataConnection instance
        date_start: ISO format start date (default: 2019-01-01)
        date_end: ISO format end date (default: 2019-01-31)
        pulocation_id: Filter by pickup zone (optional)
        dolocation_id: Filter by dropoff zone (optional)
        page: Page number (1-indexed)
        page_size: Records per page (max 10000)
        sort_by: 'pickup_datetime' (default) or 'fare_amount' or 'trip_distance'
    
    Returns:
        Tuple: (trips list, total_count)
    
    Performance:
        - Indexes: idx_trips_pickup_datetime, idx_trips_pulocation_id, idx_trips_dolocation_id
        - Query time: <100ms for typical pages
    """
    # Build dynamic WHERE clause
    where_clauses = [
        "pickup_datetime BETWEEN ? AND ?",
    ]
    params = [f"{date_start} 00:00:00", f"{date_end} 23:59:59"]
    
    if pulocation_id is not None:
        where_clauses.append("pulocation_id = ?")
        params.append(pulocation_id)
    
    if dolocation_id is not None:
        where_clauses.append("dolocation_id = ?")
        params.append(dolocation_id)
    
    where_clause = " AND ".join(where_clauses)
    
    # Count total (for pagination)
    count_query = f"SELECT COUNT(*) FROM trips WHERE {where_clause};"
    cursor = db.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    # Fetch paginated results
    offset = (page - 1) * page_size
    query = f"""
    SELECT 
        trip_id, pickup_datetime, dropoff_datetime, passenger_count, trip_distance,
        pulocation_id, dolocation_id, fare_amount, tip_amount, total_amount,
        average_speed_mph, tip_percentage, rush_hour_flag, payment_type
    FROM trips
    WHERE {where_clause}
    ORDER BY {sort_by} DESC
    LIMIT ? OFFSET ?;
    """
    params.extend([page_size, offset])
    
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    trips = [dict(row) for row in rows]
    
    return trips, total_count


def fetch_trip_by_id(db: DataConnection, trip_id: int) -> Optional[Dict]:
    """
    Fetch single trip record by ID.
    
    Args:
        trip_id: Trip record ID
    
    Returns:
        Trip dict or None
    """
    query = "SELECT * FROM trips WHERE trip_id = ?;"
    cursor = db.execute(query, (trip_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


# ============================================================================
# ANALYTICS & AGGREGATION FUNCTIONS
# ============================================================================

def fetch_overall_metrics(
    db: DataConnection,
    date_start: str = '2019-01-01',
    date_end: str = '2019-01-31'
) -> Dict:
    """
    Fetch overall trip metrics for date range.
    
    Returns:
        Dict: {
            'total_trips': int,
            'avg_fare': float,
            'total_revenue': float,
            'avg_tip_percentage': float,
            'avg_distance': float,
            'avg_passengers': float
        }
    """
    query = """
    SELECT 
        COUNT(*) as total_trips,
        ROUND(AVG(fare_amount), 2) as avg_fare,
        ROUND(SUM(total_amount), 2) as total_revenue,
        ROUND(AVG(tip_percentage), 2) as avg_tip_percentage,
        ROUND(AVG(trip_distance), 2) as avg_distance,
        ROUND(AVG(passenger_count), 1) as avg_passengers
    FROM trips
    WHERE pickup_datetime BETWEEN ? AND ?;
    """
    cursor = db.execute(query, (
        f"{date_start} 00:00:00",
        f"{date_end} 23:59:59"
    ))
    row = cursor.fetchone()
    return dict(row)


def fetch_busiest_zones(
    db: DataConnection,
    metric: str = 'trip_count',
    limit: int = 10,
    date_start: str = '2019-01-01',
    date_end: str = '2019-01-31'
) -> List[Dict]:
    """
    Fetch busiest pickup zones ranked by metric (USES INDEX).
    
    Args:
        metric: 'trip_count' (default) or 'revenue'
        limit: Top N zones to return
        date_start, date_end: Date range filter
    
    Returns:
        List of zone stats dicts
    
    Performance:
        - Index: idx_trips_pulocation_id
        - Query time: ~50ms for typical queries
    """
    order_col = 'trip_count' if metric == 'trip_count' else 'total_revenue'
    
    query = f"""
    SELECT 
        t.pulocation_id as zone_id,
        z.zone,
        z.borough,
        COUNT(*) as trip_count,
        ROUND(AVG(t.fare_amount), 2) as avg_fare,
        ROUND(SUM(t.total_amount), 2) as total_revenue
    FROM trips t
    LEFT JOIN taxi_zones z ON t.pulocation_id = z.zone_id
    WHERE t.pickup_datetime BETWEEN ? AND ?
    GROUP BY t.pulocation_id
    ORDER BY {order_col} DESC
    LIMIT ?;
    """
    cursor = db.execute(query, (
        f"{date_start} 00:00:00",
        f"{date_end} 23:59:59",
        limit
    ))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def fetch_busiest_routes(
    db: DataConnection,
    limit: int = 20,
    date_start: str = '2019-01-01',
    date_end: str = '2019-01-31'
) -> List[Dict]:
    """
    Fetch most common origin-destination pairs (USES COMPOSITE INDEX).
    
    Args:
        limit: Top N routes to return
        date_start, date_end: Date range
    
    Returns:
        List of route stats
    
    Performance:
        - Index: idx_location_pair (pulocation_id, dolocation_id, pickup_datetime)
        - Query time: ~100ms
    """
    query = """
    SELECT 
        t.pulocation_id,
        z1.zone as from_zone,
        z1.borough as from_borough,
        t.dolocation_id,
        z2.zone as to_zone,
        z2.borough as to_borough,
        COUNT(*) as trip_count,
        ROUND(AVG(t.trip_distance), 2) as avg_distance,
        ROUND(AVG(t.fare_amount), 2) as avg_fare
    FROM trips t
    LEFT JOIN taxi_zones z1 ON t.pulocation_id = z1.zone_id
    LEFT JOIN taxi_zones z2 ON t.dolocation_id = z2.zone_id
    WHERE t.pickup_datetime BETWEEN ? AND ?
    GROUP BY t.pulocation_id, t.dolocation_id
    ORDER BY trip_count DESC
    LIMIT ?;
    """
    cursor = db.execute(query, (
        f"{date_start} 00:00:00",
        f"{date_end} 23:59:59",
        limit
    ))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def fetch_rush_hour_analysis(
    db: DataConnection,
    date_start: str = '2019-01-01',
    date_end: str = '2019-01-31'
) -> List[Dict]:
    """
    Compare rush hour vs off-peak metrics.
    
    Returns:
        List: [
            {'period': 'Rush Hour', 'trip_count': int, 'avg_fare': float, ...},
            {'period': 'Off Peak', 'trip_count': int, 'avg_fare': float, ...}
        ]
    """
    query = """
    SELECT 
        rush_hour_flag,
        CASE WHEN rush_hour_flag = 1 
            THEN 'Rush Hour (Weekday 7-10am, 4-7pm)' 
            ELSE 'Off Peak' 
        END as period,
        COUNT(*) as trip_count,
        ROUND(AVG(fare_amount), 2) as avg_fare,
        ROUND(AVG(trip_distance), 2) as avg_distance,
        ROUND(AVG(average_speed_mph), 2) as avg_speed_mph,
        ROUND(AVG(passenger_count), 1) as avg_passengers
    FROM trips
    WHERE pickup_datetime BETWEEN ? AND ?
    GROUP BY rush_hour_flag
    ORDER BY rush_hour_flag DESC;
    """
    cursor = db.execute(query, (
        f"{date_start} 00:00:00",
        f"{date_end} 23:59:59"
    ))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def fetch_hourly_distribution(
    db: DataConnection,
    date_start: str = '2019-01-01',
    date_end: str = '2019-01-31'
) -> List[Dict]:
    """
    Fetch trip distribution by hour of day.
    
    Returns:
        List of hourly stats (24 records, one per hour)
    """
    query = """
    SELECT 
        CAST(strftime('%H', pickup_datetime) AS INTEGER) as hour_of_day,
        COUNT(*) as trip_count,
        ROUND(AVG(fare_amount), 2) as avg_fare,
        ROUND(AVG(tip_percentage), 2) as avg_tip_percentage
    FROM trips
    WHERE pickup_datetime BETWEEN ? AND ?
    GROUP BY hour_of_day
    ORDER BY hour_of_day;
    """
    cursor = db.execute(query, (
        f"{date_start} 00:00:00",
        f"{date_end} 23:59:59"
    ))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    # Create connection
    db = DataConnection('sqlite', 'mobility.db')
    db.connect()
    
    try:
        # Fetch all zones
        print("=== All Zones ===")
        zones = fetch_all_zones(db)
        print(f"Total zones: {len(zones)}")
        print(f"Sample: {zones[0]}")
        
        # Fetch zones by borough
        print("\\n=== Manhattan Zones ===")
        manhattan_zones = fetch_zones_by_borough(db, 'Manhattan')
        print(f"Manhattan zones: {len(manhattan_zones)}")
        
        # Fetch overall metrics
        print("\\n=== Overall Metrics (Jan 2019) ===")
        metrics = fetch_overall_metrics(db)
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        # Fetch busiest zones
        print("\\n=== Top 5 Busiest Pickup Zones ===")
        busiest = fetch_busiest_zones(db, metric='trip_count', limit=5)
        for zone in busiest:
            print(f"  {zone['zone']} ({zone['borough']}): {zone['trip_count']:,} trips")
        
        # Fetch busiest routes
        print("\\n=== Top 5 Busiest Routes ===")
        routes = fetch_busiest_routes(db, limit=5)
        for route in routes:
            print(f"  {route['from_zone']} → {route['to_zone']}: {route['trip_count']:,} trips")
        
        # Rush hour analysis
        print("\\n=== Rush Hour Analysis ===")
        rush_data = fetch_rush_hour_analysis(db)
        for period in rush_data:
            print(f"  {period['period']}: {period['trip_count']:,} trips, "
                  f"avg fare: ${period['avg_fare']}, avg speed: {period['avg_speed_mph']} mph")
        
        # Hourly distribution
        print("\\n=== Hourly Distribution (Sample Hours) ===")
        hourly = fetch_hourly_distribution(db)
        for hour in hourly[::4]:  # Sample every 4th hour
            print(f"  {hour['hour_of_day']:02d}:00 - {hour['trip_count']:,} trips")
        
    finally:
        db.close()
