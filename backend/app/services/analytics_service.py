from app.db import fetch_all
from app.helpers.filtering import build_where

def trips_by_hour(filters: dict):
    where, params, needs_join = build_where(filters)
    join = "LEFT JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id" if needs_join else ""

    return fetch_all(f"""
        SELECT
            CAST(strftime('%H', t.pickup_datetime) AS INTEGER) AS hour,
            COUNT(*) AS trip_count,
            ROUND(AVG(t.fare_amount), 2) AS avg_fare
        FROM trips t
        {join}
        {where}
        GROUP BY hour
        ORDER BY hour
    """, params)

def trips_by_day(filters: dict):
    where, params, needs_join = build_where(filters)
    join = "LEFT JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id" if needs_join else ""

    return fetch_all(f"""
        SELECT
            date(t.pickup_datetime) AS date,
            COUNT(*) AS trip_count
        FROM trips t
        {join}
        {where}
        GROUP BY date
        ORDER BY date
    """, params)

def trips_by_borough(filters: dict):
    where, params, _ = build_where(filters)
    return fetch_all(f"""
        SELECT
            pu.borough,
            COUNT(*) AS trip_count,
            ROUND(SUM(t.total_amount), 2) AS total_revenue
        FROM trips t
        JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id
        {where}
        GROUP BY pu.borough
        ORDER BY trip_count DESC
    """, params)


def fare_distribution(filters: dict):
    where, params, needs_join = build_where(filters)
    join = "LEFT JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id" if needs_join else ""
    return fetch_all(f"""
        SELECT
            CASE
                WHEN t.fare_amount < 5  THEN '0-5'
                WHEN t.fare_amount < 10 THEN '5-10'
                WHEN t.fare_amount < 15 THEN '10-15'
                WHEN t.fare_amount < 20 THEN '15-20'
                WHEN t.fare_amount < 30 THEN '20-30'
                WHEN t.fare_amount < 40 THEN '30-40'
                WHEN t.fare_amount < 60 THEN '40-60'
                ELSE '60+'
            END AS bucket,
            COUNT(*) AS count,
            MIN(t.fare_amount) AS _sort_key
        FROM trips t
        {join}
        {where}
        GROUP BY bucket
        ORDER BY _sort_key
    """, params)


def distance_distribution(filters: dict):
    where, params, needs_join = build_where(filters)
    join = "LEFT JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id" if needs_join else ""
    return fetch_all(f"""
        SELECT
            CASE
                WHEN t.trip_distance < 1  THEN '0-1'
                WHEN t.trip_distance < 2  THEN '1-2'
                WHEN t.trip_distance < 3  THEN '2-3'
                WHEN t.trip_distance < 4  THEN '3-4'
                WHEN t.trip_distance < 5  THEN '4-5'
                WHEN t.trip_distance < 8  THEN '5-8'
                WHEN t.trip_distance < 12 THEN '8-12'
                ELSE '12+'
            END AS bucket,
            COUNT(*) AS count,
            MIN(t.trip_distance) AS _sort_key
        FROM trips t
        {join}
        {where}
        GROUP BY bucket
        ORDER BY _sort_key
    """, params)


def speed_by_hour(filters: dict):
    where, params, needs_join = build_where(filters)
    join = "LEFT JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id" if needs_join else ""
    return fetch_all(f"""
        SELECT
            CAST(strftime('%H', t.pickup_datetime) AS INTEGER) AS hour,
            ROUND(AVG(t.average_speed_mph), 2) AS avg_speed_mph,
            COUNT(*) AS trip_count
        FROM trips t
        {join}
        {where}
        GROUP BY hour
        ORDER BY hour
    """, params)


def payment_breakdown(_filters: dict):
    return None


def top_routes(filters: dict, limit: int = 8):
    where, params, _ = build_where(filters)
    return fetch_all(f"""
        SELECT
            pu.zone       AS pickup_zone,
            do.zone       AS dropoff_zone,
            pu.borough    AS pickup_borough,
            do.borough    AS dropoff_borough,
            COUNT(*)      AS trip_count,
            ROUND(AVG(t.fare_amount), 2) AS avg_fare
        FROM trips t
        JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id
        JOIN taxi_zones do ON t.dolocation_id = do.zone_id
        {where}
        GROUP BY t.pulocation_id, t.dolocation_id
        ORDER BY trip_count DESC
        LIMIT ?
    """, params + [limit])


def trips_by_zone(filters: dict):
    where, params, _ = build_where(filters)
    return fetch_all(f"""
        SELECT
            pu.zone_id,
            pu.zone,
            pu.borough,
            COUNT(*) AS trip_count,
            ROUND(AVG(t.fare_amount), 2) AS avg_fare
        FROM trips t
        JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id
        {where}
        GROUP BY pu.zone_id
        ORDER BY trip_count DESC
    """, params)
