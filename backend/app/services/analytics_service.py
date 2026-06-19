from app.db import fetch_one, fetch_all


def _build_filter_clause(filters):
    conditions = []
    params = []

    if filters.get("start_date"):
        conditions.append("pickup_datetime >= ?")
        params.append(filters["start_date"])

    if filters.get("end_date"):
        conditions.append("pickup_datetime <= ?")
        params.append(filters["end_date"])

    if filters.get("pickup_borough"):
        conditions.append("pz.borough = ?")
        params.append(filters["pickup_borough"])

    return conditions, params


def get_overall_summary(filters: dict):
    """
    Returns total trips, average fare, total revenue, and average tip percentage
    for an optional filtered trip set.
    """
    conditions, params = _build_filter_clause(filters)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT
            COUNT(*) AS total_trips,
            COALESCE(AVG(fare_amount), 0.0) AS avg_fare,
            COALESCE(SUM(total_amount), 0.0) AS total_revenue,
            COALESCE(AVG(tip_percentage), 0.0) AS avg_tip_percentage
        FROM trips t
        LEFT JOIN taxi_zones pz ON t.pulocation_id = pz.zone_id
        {where_clause};
    """

    result = fetch_one(sql, params)
    return {
        "total_trips": int(result["total_trips"]),
        "avg_fare": float(result["avg_fare"]),
        "total_revenue": float(result["total_revenue"]),
        "avg_tip_percentage": float(result["avg_tip_percentage"]),
    }


def _merge_sort(items, key, reverse=False):
    """
    Stable merge sort implementation for ranking dictionaries by a numeric key.

    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    if len(items) <= 1:
        return items

    mid = len(items) // 2
    left = _merge_sort(items[:mid], key, reverse=reverse)
    right = _merge_sort(items[mid:], key, reverse=reverse)

    merged = []
    left_index = 0
    right_index = 0

    while left_index < len(left) and right_index < len(right):
        left_value = left[left_index].get(key, 0)
        right_value = right[right_index].get(key, 0)

        if reverse:
            if left_value >= right_value:
                merged.append(left[left_index])
                left_index += 1
            else:
                merged.append(right[right_index])
                right_index += 1
        else:
            if left_value <= right_value:
                merged.append(left[left_index])
                left_index += 1
            else:
                merged.append(right[right_index])
                right_index += 1

    merged.extend(left[left_index:])
    merged.extend(right[right_index:])
    return merged


def rank_items(items, key, limit=20, reverse=True):
    sorted_items = _merge_sort(items, key, reverse=reverse)
    return sorted_items[:limit]


def get_busiest_zones(filters: dict, metric: str = "trip_count", limit: int = 20):
    """
    Returns the top zones ranked by trip count or total revenue.
    """
    metric = metric if metric in {"trip_count", "total_revenue"} else "trip_count"
    conditions, params = _build_filter_clause(filters)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT
            pz.zone_id AS zone_id,
            pz.zone AS zone,
            pz.borough AS borough,
            COUNT(*) AS trip_count,
            COALESCE(SUM(t.total_amount), 0.0) AS total_revenue
        FROM trips t
        JOIN taxi_zones pz ON t.pulocation_id = pz.zone_id
        {where_clause}
        GROUP BY pz.zone_id, pz.zone, pz.borough;
    """

    rows = fetch_all(sql, params)
    ranked = rank_items(rows, metric, limit=limit, reverse=True)
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = idx
    return ranked
