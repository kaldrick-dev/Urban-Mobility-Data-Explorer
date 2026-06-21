"""
Optimized SQL Queries for Urban Mobility Data Explorer

This module provides production-ready queries with proper indexing leverage,
filtering strategies, and performance considerations.

Database: SQLite (mobility.db)
"""

# ============================================================================
# 1. ZONE QUERIES - Geographic Reference Data
# ============================================================================

# Fetch all zones with borough
QUERY_ALL_ZONES = """
SELECT zone_id, borough, zone, service_zone
FROM taxi_zones
ORDER BY borough, zone_id;
"""

# Fetch zones by borough (uses PK scan)
QUERY_ZONES_BY_BOROUGH = """
SELECT zone_id, zone, service_zone
FROM taxi_zones
WHERE borough = ?
ORDER BY zone_id;
"""

# Fetch single zone with geometry
QUERY_ZONE_BY_ID = """
SELECT zone_id, borough, zone, service_zone, geometry
FROM taxi_zones
WHERE zone_id = ?;
"""

# Fetch distinct boroughs
QUERY_DISTINCT_BOROUGHS = """
SELECT DISTINCT borough
FROM taxi_zones
ORDER BY borough;
"""


# ============================================================================
# 2. TRIP QUERIES - Fact Table Analytics
# ============================================================================

# Fetch paginated trips with filtering (uses idx_trips_pickup_datetime)
QUERY_TRIPS_PAGINATED = """
SELECT 
    trip_id,
    pickup_datetime,
    dropoff_datetime,
    passenger_count,
    trip_distance,
    pulocation_id,
    dolocation_id,
    fare_amount,
    tip_amount,
    total_amount,
    average_speed_mph,
    tip_percentage,
    rush_hour_flag,
    payment_type
FROM trips
WHERE 1=1
    {date_filter}
    {borough_filter}
    {distance_filter}
    {fare_filter}
    {speed_filter}
ORDER BY pickup_datetime DESC
LIMIT ? OFFSET ?;
"""

# Example filters (plug into QUERY_TRIPS_PAGINATED):
FILTER_DATE_RANGE = "AND pickup_datetime BETWEEN ? AND ?"  # Uses idx_trips_pickup_datetime
FILTER_BOROUGH = """
    AND (pulocation_id IN (
        SELECT zone_id FROM taxi_zones WHERE borough = ?
    ) OR dolocation_id IN (
        SELECT zone_id FROM taxi_zones WHERE borough = ?
    ))
"""
FILTER_DISTANCE = "AND trip_distance BETWEEN ? AND ?"
FILTER_FARE = "AND fare_amount BETWEEN ? AND ?"
FILTER_SPEED = "AND average_speed_mph > ?"

# Fetch a single trip
QUERY_TRIP_BY_ID = """
SELECT * FROM trips WHERE trip_id = ?;
"""


# ============================================================================
# 3. AGGREGATION QUERIES - Analytics & Metrics
# ============================================================================

# Overall trip metrics (date-filtered)
QUERY_OVERALL_METRICS = """
SELECT 
    COUNT(*) as total_trips,
    ROUND(AVG(fare_amount), 2) as avg_fare,
    ROUND(SUM(total_amount), 2) as total_revenue,
    ROUND(AVG(tip_percentage), 2) as avg_tip_percentage,
    ROUND(AVG(trip_distance), 2) as avg_distance,
    ROUND(AVG(passenger_count), 1) as avg_passengers
FROM trips
WHERE 1=1
    {date_filter}
    {borough_filter};
"""

# Busiest zones by trip count (uses idx_trips_pulocation_id)
QUERY_BUSIEST_ZONES_BY_COUNT = """
SELECT 
    t.pulocation_id as zone_id,
    z.zone,
    z.borough,
    COUNT(*) as trip_count,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(SUM(t.total_amount), 2) as total_revenue
FROM trips t
LEFT JOIN taxi_zones z ON t.pulocation_id = z.zone_id
WHERE 1=1
    {date_filter}
GROUP BY t.pulocation_id
ORDER BY trip_count DESC
LIMIT ?;
"""

# Busiest zones by revenue (uses idx_trips_pulocation_id)
QUERY_BUSIEST_ZONES_BY_REVENUE = """
SELECT 
    t.pulocation_id as zone_id,
    z.zone,
    z.borough,
    COUNT(*) as trip_count,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(SUM(t.total_amount), 2) as total_revenue
FROM trips t
LEFT JOIN taxi_zones z ON t.pulocation_id = z.zone_id
WHERE 1=1
    {date_filter}
GROUP BY t.pulocation_id
ORDER BY total_revenue DESC
LIMIT ?;
"""

# Zone pair analysis: most common routes (uses both location indexes)
QUERY_BUSIEST_ROUTES = """
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
WHERE 1=1
    {date_filter}
GROUP BY t.pulocation_id, t.dolocation_id
ORDER BY trip_count DESC
LIMIT ?;
"""

# Rush hour analysis (uses idx_trips_pickup_datetime indirectly)
QUERY_RUSH_HOUR_ANALYSIS = """
SELECT 
    rush_hour_flag,
    CASE WHEN rush_hour_flag = 1 THEN 'Rush Hour (Weekday 7-10am, 4-7pm)' ELSE 'Off Peak' END as period,
    COUNT(*) as trip_count,
    ROUND(AVG(fare_amount), 2) as avg_fare,
    ROUND(AVG(trip_distance), 2) as avg_distance,
    ROUND(AVG(average_speed_mph), 2) as avg_speed_mph,
    ROUND(AVG(passenger_count), 1) as avg_passengers
FROM trips
WHERE 1=1
    {date_filter}
GROUP BY rush_hour_flag
ORDER BY rush_hour_flag DESC;
"""

# Payment type breakdown
QUERY_PAYMENT_TYPE_ANALYSIS = """
SELECT 
    payment_type,
    CASE 
        WHEN payment_type = 1 THEN 'Credit Card'
        WHEN payment_type = 2 THEN 'Cash'
        WHEN payment_type = 3 THEN 'No Charge'
        WHEN payment_type = 4 THEN 'Dispute'
        ELSE 'Unknown'
    END as payment_method,
    COUNT(*) as trip_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM trips), 2) as percentage,
    ROUND(AVG(tip_percentage), 2) as avg_tip_percentage
FROM trips
WHERE payment_type IS NOT NULL
GROUP BY payment_type
ORDER BY trip_count DESC;
"""

# Tipping analysis
QUERY_TIPPING_ANALYSIS = """
SELECT 
    CASE
        WHEN tip_percentage = 0 THEN 'No Tip'
        WHEN tip_percentage BETWEEN 0.01 AND 10 THEN '1-10%'
        WHEN tip_percentage BETWEEN 10.01 AND 20 THEN '10-20%'
        WHEN tip_percentage > 20 THEN '>20%'
    END as tip_range,
    COUNT(*) as frequency,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM trips WHERE tip_percentage IS NOT NULL), 2) as percentage
FROM trips
WHERE tip_percentage IS NOT NULL AND payment_type = 1
GROUP BY tip_range
ORDER BY CASE tip_range 
    WHEN 'No Tip' THEN 1
    WHEN '1-10%' THEN 2
    WHEN '10-20%' THEN 3
    WHEN '>20%' THEN 4
END;
"""


# ============================================================================
# 4. DISTANCE & SPEED QUERIES
# ============================================================================

# Trips by distance bucket (sequential scan, but useful)
QUERY_DISTANCE_BUCKETS = """
SELECT 
    CASE
        WHEN trip_distance <= 1 THEN '0-1 mi'
        WHEN trip_distance <= 3 THEN '1-3 mi'
        WHEN trip_distance <= 5 THEN '3-5 mi'
        WHEN trip_distance <= 10 THEN '5-10 mi'
        ELSE '>10 mi'
    END as distance_bucket,
    COUNT(*) as trip_count,
    ROUND(AVG(fare_amount), 2) as avg_fare,
    ROUND(AVG(trip_distance), 2) as avg_distance,
    ROUND(AVG(average_speed_mph), 2) as avg_speed
FROM trips
WHERE trip_distance > 0
GROUP BY distance_bucket
ORDER BY CASE distance_bucket
    WHEN '0-1 mi' THEN 1
    WHEN '1-3 mi' THEN 2
    WHEN '3-5 mi' THEN 3
    WHEN '5-10 mi' THEN 4
    WHEN '>10 mi' THEN 5
END;
"""

# Speed analysis
QUERY_SPEED_ANALYSIS = """
SELECT 
    ROUND(AVG(average_speed_mph), 2) as avg_speed_mph,
    MIN(average_speed_mph) as min_speed_mph,
    MAX(average_speed_mph) as max_speed_mph,
    ROUND((SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY average_speed_mph)
           FROM trips WHERE average_speed_mph > 0), 2) as median_speed_mph
FROM trips
WHERE average_speed_mph > 0;
"""


# ============================================================================
# 5. TIME-BASED QUERIES
# ============================================================================

# Trips by hour of day (uses idx_trips_pickup_datetime indirectly)
QUERY_HOURLY_DISTRIBUTION = """
SELECT 
    CAST(strftime('%H', pickup_datetime) AS INTEGER) as hour_of_day,
    COUNT(*) as trip_count,
    ROUND(AVG(fare_amount), 2) as avg_fare,
    ROUND(AVG(tip_percentage), 2) as avg_tip_percentage
FROM trips
WHERE 1=1
    {date_filter}
GROUP BY hour_of_day
ORDER BY hour_of_day;
"""

# Trips by day of week (uses idx_trips_pickup_datetime indirectly)
QUERY_DAY_OF_WEEK_DISTRIBUTION = """
SELECT 
    CASE CAST(strftime('%w', pickup_datetime) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as day_name,
    COUNT(*) as trip_count,
    ROUND(AVG(fare_amount), 2) as avg_fare
FROM trips
WHERE 1=1
    {date_filter}
GROUP BY CAST(strftime('%w', pickup_datetime) AS INTEGER)
ORDER BY CAST(strftime('%w', pickup_datetime) AS INTEGER);
"""


# ============================================================================
# 6. EXAMPLE USAGE IN PYTHON
# ============================================================================

"""
Example usage with SQLite:

import sqlite3

conn = sqlite3.connect('mobility.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Fetch all zones
cursor.execute(QUERY_ALL_ZONES)
zones = [dict(row) for row in cursor.fetchall()]

# Fetch trips in Manhattan with date filter
cursor.execute(QUERY_TRIPS_PAGINATED.format(
    date_filter='AND pickup_datetime BETWEEN ? AND ?',
    borough_filter=FILTER_BOROUGH,
    distance_filter='',
    fare_filter='',
    speed_filter=''
), ('2019-01-01 00:00:00', '2019-01-02 23:59:59', 'Manhattan', 'Manhattan', 0, 100))
trips = [dict(row) for row in cursor.fetchall()]

# Fetch metrics
cursor.execute(QUERY_OVERALL_METRICS.format(
    date_filter='',
    borough_filter=''
))
metrics = dict(cursor.fetchone())

conn.close()
"""

