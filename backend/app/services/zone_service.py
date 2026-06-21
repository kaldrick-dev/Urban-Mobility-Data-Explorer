from app.db import fetch_all

def get_boroughs():
    return fetch_all("""
        SELECT DISTINCT borough FROM taxi_zones
        WHERE borough IS NOT NULL
          AND borough != 'Unknown'
          AND borough != 'nan'
        ORDER BY borough
    """)


