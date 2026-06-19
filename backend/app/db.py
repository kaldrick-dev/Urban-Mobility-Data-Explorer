import sqlite3
from config import DATABASE_PATH


def get_db_connection():
    conn = sqlite3.connect(str(DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS taxi_zones (
            zone_id INTEGER PRIMARY KEY,
            borough TEXT,
            zone TEXT,
            service_zone TEXT,
            geometry TEXT
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pickup_datetime TEXT NOT NULL,
            dropoff_datetime TEXT NOT NULL,
            passenger_count INTEGER,
            trip_distance REAL,
            pulocation_id INTEGER,
            dolocation_id INTEGER,
            fare_amount REAL,
            tip_amount REAL,
            total_amount REAL,
            average_speed_mph REAL,
            tip_percentage REAL,
            rush_hour_flag INTEGER,
            payment_type INTEGER
        );
        """
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_trips_pulocation_id ON trips(pulocation_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_trips_dolocation_id ON trips(dolocation_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_trips_pickup_datetime ON trips(pickup_datetime);"
    )

    conn.commit()
    conn.close()


def fetch_all(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_one(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def execute_write(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    conn.commit()
    conn.close()


def insert_many(query, rows):
    if not rows:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany(query, rows)
    conn.commit()
    conn.close()
