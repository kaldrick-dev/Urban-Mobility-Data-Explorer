def get_all_zones(borough: str | None = None):
    """Returns all taxi zones, optionally filtered by borough."""
    pass


def get_zone_by_id(zone_id: int) -> dict | None:
    """Returns a single zone dict by LocationID, or None if not found."""
    pass


def get_zones_by_borough(borough: str):
    """Returns all zones belonging to the given borough."""
    pass


def get_distinct_boroughs():
    """Returns a sorted list of distinct borough names."""
    pass
