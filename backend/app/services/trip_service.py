from app.db import fetch_all, fetch_one


def _build_trip_filters(filters):
    conditions = []
    params = []

    if filters.get("start_date"):
        conditions.append("t.pickup_datetime >= ?")
        params.append(filters["start_date"])

    if filters.get("end_date"):
        conditions.append("t.pickup_datetime <= ?")
        params.append(filters["end_date"])

    if filters.get("pickup_borough"):
        conditions.append("pz.borough = ?")
        params.append(filters["pickup_borough"])

    if filters.get("dropoff_borough"):
        conditions.append("dz.borough = ?")
        params.append(filters["dropoff_borough"])

    if filters.get("pickup_zone_id") is not None:
        conditions.append("t.pulocation_id = ?")
        params.append(int(filters["pickup_zone_id"]))

    if filters.get("dropoff_zone_id") is not None:
        conditions.append("t.dolocation_id = ?")
        params.append(int(filters["dropoff_zone_id"]))

    if filters.get("min_distance") is not None:
        conditions.append("t.trip_distance >= ?")
        params.append(float(filters["min_distance"]))

    if filters.get("max_distance") is not None:
        conditions.append("t.trip_distance <= ?")
        params.append(float(filters["max_distance"]))

    if filters.get("min_fare") is not None:
        conditions.append("t.fare_amount >= ?")
        params.append(float(filters["min_fare"]))

    if filters.get("max_fare") is not None:
        conditions.append("t.fare_amount <= ?")
        params.append(float(filters["max_fare"]))

    if filters.get("payment_type") is not None:
        conditions.append("t.payment_type = ?")
        params.append(int(filters["payment_type"]))

    if filters.get("is_rush_hour") is not None:
        is_rush = filters["is_rush_hour"]
        conditions.append("t.rush_hour_flag = ?")
        params.append(1 if str(is_rush).lower() in {"1", "true", "yes", "y"} else 0)

    if filters.get("time_of_day"):
        period = str(filters["time_of_day"]).lower()
        if period == "morning":
            conditions.append("CAST(strftime('%H', t.pickup_datetime) AS INTEGER) BETWEEN 5 AND 11")
        elif period == "afternoon":
            conditions.append("CAST(strftime('%H', t.pickup_datetime) AS INTEGER) BETWEEN 12 AND 16")
        elif period == "evening":
            conditions.append("CAST(strftime('%H', t.pickup_datetime) AS INTEGER) BETWEEN 17 AND 20")
        elif period == "night":
            conditions.append(
                "(CAST(strftime('%H', t.pickup_datetime) AS INTEGER) >= 21 OR CAST(strftime('%H', t.pickup_datetime) AS INTEGER) < 5)"
            )

    return conditions, params


def _build_order_by(sort):
    sort_columns = {
        "pickup_datetime": "t.pickup_datetime",
        "total_amount": "t.total_amount",
        "trip_distance": "t.trip_distance",
        "duration_minutes": "(CAST(strftime('%s', t.dropoff_datetime) AS INTEGER) - CAST(strftime('%s', t.pickup_datetime) AS INTEGER)) / 60.0",
    }
    column = sort_columns.get(sort.get("sort_by"), "t.pickup_datetime")
    direction = "ASC" if sort.get("sort_order", "desc").lower() == "asc" else "DESC"
    return f"ORDER BY {column} {direction}"


def get_trips(filters: dict, pagination: dict, sort: dict):
    conditions, params = _build_trip_filters(filters)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    count_sql = f"SELECT COUNT(*) as total FROM trips t LEFT JOIN taxi_zones pz ON t.pulocation_id = pz.zone_id LEFT JOIN taxi_zones dz ON t.dolocation_id = dz.zone_id {where_clause};"
    count_result = fetch_one(count_sql, params)
    total = int(count_result["total"])

    page = max(1, int(pagination.get("page", 1)))
    per_page = max(1, int(pagination.get("per_page", 25)))
    offset = (page - 1) * per_page

    order_clause = _build_order_by(sort)
    query = f"""
        SELECT
            t.trip_id,
            t.pickup_datetime,
            t.dropoff_datetime,
            t.passenger_count,
            t.trip_distance,
            t.pulocation_id,
            pz.zone AS pickup_zone,
            pz.borough AS pickup_borough,
            t.dolocation_id,
            dz.zone AS dropoff_zone,
            dz.borough AS dropoff_borough,
            t.fare_amount,
            t.tip_amount,
            t.total_amount,
            t.average_speed_mph,
            t.tip_percentage,
            t.rush_hour_flag,
            t.payment_type,
            ROUND((CAST(strftime('%s', t.dropoff_datetime) AS INTEGER) - CAST(strftime('%s', t.pickup_datetime) AS INTEGER)) / 60.0, 2) AS duration_minutes
        FROM trips t
        LEFT JOIN taxi_zones pz ON t.pulocation_id = pz.zone_id
        LEFT JOIN taxi_zones dz ON t.dolocation_id = dz.zone_id
        {where_clause}
        {order_clause}
        LIMIT ? OFFSET ?;
    """
    rows = fetch_all(query, params + [per_page, offset])

    pages = (total + per_page - 1) // per_page
    return {
        "items": rows,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def get_trip_by_id(trip_id: int):
    sql = """
        SELECT
            t.trip_id,
            t.pickup_datetime,
            t.dropoff_datetime,
            t.passenger_count,
            t.trip_distance,
            t.pulocation_id,
            pz.zone AS pickup_zone,
            pz.borough AS pickup_borough,
            t.dolocation_id,
            dz.zone AS dropoff_zone,
            dz.borough AS dropoff_borough,
            t.fare_amount,
            t.tip_amount,
            t.total_amount,
            t.average_speed_mph,
            t.tip_percentage,
            t.rush_hour_flag,
            t.payment_type
        FROM trips t
        LEFT JOIN taxi_zones pz ON t.pulocation_id = pz.zone_id
        LEFT JOIN taxi_zones dz ON t.dolocation_id = dz.zone_id
        WHERE t.trip_id = ?;
    """
    return fetch_one(sql, [trip_id])


def get_trip_stats(filters: dict):
    conditions, params = _build_trip_filters(filters)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT
            COUNT(*) AS total_trips,
            COALESCE(AVG(t.fare_amount), 0.0) AS avg_fare,
            COALESCE(AVG(t.trip_distance), 0.0) AS avg_distance,
            COALESCE(AVG((CAST(strftime('%s', t.dropoff_datetime) AS INTEGER) - CAST(strftime('%s', t.pickup_datetime) AS INTEGER)) / 60.0), 0.0) AS avg_duration_minutes,
            COALESCE(AVG(t.average_speed_mph), 0.0) AS avg_speed_mph,
            COALESCE(AVG(t.tip_amount), 0.0) AS avg_tip_amount,
            COALESCE(AVG(t.passenger_count), 0.0) AS avg_passenger_count,
            COALESCE(SUM(t.total_amount), 0.0) AS total_revenue
        FROM trips t
        LEFT JOIN taxi_zones pz ON t.pulocation_id = pz.zone_id
        LEFT JOIN taxi_zones dz ON t.dolocation_id = dz.zone_id
        {where_clause};
    """
    result = fetch_one(sql, params)
    return {
        "total_trips": int(result["total_trips"]),
        "avg_fare": float(result["avg_fare"]),
        "avg_distance": float(result["avg_distance"]),
        "avg_duration_minutes": float(result["avg_duration_minutes"]),
        "avg_speed_mph": float(result["avg_speed_mph"]),
        "avg_tip_amount": float(result["avg_tip_amount"]),
        "avg_passenger_count": float(result["avg_passenger_count"]),
        "total_revenue": float(result["total_revenue"]),
    }
