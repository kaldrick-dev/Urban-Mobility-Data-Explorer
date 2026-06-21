CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS trips (
        trip_id               INTEGER PRIMARY KEY AUTOINCREMENT,
        pickup_datetime       TEXT    NOT NULL,
        dropoff_datetime      TEXT    NOT NULL,
        passenger_count       INTEGER,
        trip_distance         REAL,
        pulocation_id         INTEGER,
        dolocation_id         INTEGER,
        fare_amount           REAL,
        tip_amount            REAL,
        total_amount          REAL,
        trip_duration_minutes REAL,
        average_speed_mph     REAL,
        tip_percentage        REAL,
        rush_hour_flag        INTEGER
    );
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_trips_pulocation_id   ON trips(pulocation_id);",
    "CREATE INDEX IF NOT EXISTS idx_trips_dolocation_id   ON trips(dolocation_id);",
    "CREATE INDEX IF NOT EXISTS idx_trips_pickup_datetime ON trips(pickup_datetime);",
]
