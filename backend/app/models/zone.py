CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS taxi_zones (
        zone_id      INTEGER PRIMARY KEY,
        borough      TEXT,
        zone         TEXT,
        service_zone TEXT,
        geometry     TEXT
    );
"""

INDEXES = []
