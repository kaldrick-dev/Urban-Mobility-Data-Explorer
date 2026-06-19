def get_trips(filters: dict, pagination: dict, sort: dict):
    """
    Returns a paginated list of trips matching the given filters.

    Returns:
      {
        "items": [...],
        "total": int,
        "page": int,
        "per_page": int,
        "pages": int
      }
    """
    pass


def get_trip_by_id(trip_id: int):
    """Returns a single trip dict by primary key, or None if not found."""
    pass


def get_trip_stats(filters: dict):
    """
    Returns aggregate stats for the filtered trip set.

    Returns:
      {
        "total_trips": int,
        "avg_fare": float,
        "avg_distance": float,
        "avg_duration_minutes": float,
        "avg_speed_mph": float,
        "avg_tip_amount": float,
        "avg_passenger_count": float,
        "total_revenue": float
      }
    """
    pass
