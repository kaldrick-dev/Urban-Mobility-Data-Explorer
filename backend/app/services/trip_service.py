from app.db import fetch_all, fetch_one
from app.helpers.sorting import merge_sort
from app.helpers.filtering import build_where

_ALLOWED_SORT_KEYS = {
    "pickup_datetime", "trip_distance", "fare_amount",
    "total_amount", "duration_minutes", "speed_mph",
    "tip_percentage", "passenger_count",
}


def get_trips(filters:dict, pagination:dict,sort:dict):
    page = max(1,int(pagination.get("page") or 1))
    per_page = min(100, max(1,int(pagination.get("per_page") or 50)))
    offset = (page - 1) * per_page

    #Sorting
    sort_by = sort.get("sort_by") or "pickup_datetime"
    sort_dir = (sort.get("sort_dir") or "desc").lower()

    if sort_by not in _ALLOWED_SORT_KEYS:
        sort_by = "pickup_datetime"
    reverse = sort_dir == "desc"

    where,params,needs_join = build_where(filters)

    query = f"""
    SELECT
        t.trip_id,
        t.pickup_datetime,
        pu.zone  AS pickup_zone,
        do.zone  AS dropoff_zone,
        t.trip_distance,
        t.trip_duration_minutes AS duration_minutes,
        t.average_speed_mph     AS speed_mph,
        t.total_amount,
        t.fare_amount,
        t.tip_amount,
        t.tip_percentage,
        t.passenger_count,
        t.rush_hour_flag        AS is_rush_hour
    FROM trips t
    LEFT JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id
    LEFT JOIN taxi_zones do ON t.dolocation_id = do.zone_id
    {where}
    LIMIT ? OFFSET ?
    """
    rows = fetch_all(query, params + [per_page, offset])

    rows = merge_sort(rows, sort_by,reverse=reverse)
    join_pu = "LEFT JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id" if needs_join else ""

    count_query = f"""
    SELECT COUNT(*) AS total
    FROM trips t
    {join_pu}
    {where}
    """

    total_row = fetch_one(count_query, params)
    total = total_row["total"] if total_row else 0

    return {
        "trips":    rows,
        "page":     page,
        "per_page": per_page,
        "total":    total,
    }



def get_trip(trip_id: int):
    return fetch_one("""
        SELECT t.*, pu.zone AS pickup_zone, do.zone AS dropoff_zone
        FROM trips t
        LEFT JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id
        LEFT JOIN taxi_zones do ON t.dolocation_id = do.zone_id
        WHERE t.trip_id = ?
    """, [trip_id])


def get_trip_stats(filters:dict):
    where, params, needs_join = build_where(filters)
    join = "LEFT JOIN taxi_zones pu ON t.pulocation_id = pu.zone_id" if needs_join else ""

    query = f"""
        SELECT
            COUNT(*) AS total_trips,
            ROUND(AVG(t.fare_amount), 2) AS avg_fare,
            ROUND(AVG(t.trip_distance), 2) AS avg_distance,
            ROUND(AVG(t.trip_duration_minutes), 2) AS avg_duration_minutes,
            ROUND(AVG(t.passenger_count), 2) AS avg_passengers_count,
            ROUND(AVG(t.tip_amount), 2) AS avg_tip_count,
            ROUND(AVG(t.average_speed_mph), 2) AS avg_speed_mph,
            ROUND(SUM(t.total_amount), 2) AS total_revenue
        FROM trips t
        {join}
        {where}
    """
    return fetch_one(query, params)


