_FILTER_MAP = {
    "pickup_borough": ("pu.borough",        "=",  str,   None),
    "rush_hour":      ("t.rush_hour_flag",  "=",  int,   None),
    "date_from":      ("t.pickup_datetime", ">=", str,   lambda v: v + " 00:00:00"),
    "date_to":        ("t.pickup_datetime", "<=", str,   lambda v: v + " 23:59:59"),
    "min_fare":       ("t.fare_amount",     ">=", float, None),
    "max_fare":       ("t.fare_amount",     "<=", float, None),
    "min_distance":   ("t.trip_distance",   ">=", float, None),
    "max_distance":   ("t.trip_distance",   "<=", float, None),
}

def build_where(filters: dict) -> tuple:
    conditions = []
    params     = []
    needs_zone_join = False

    for key, (col, op, cast, transform) in _FILTER_MAP.items():
        val = filters.get(key)
        if val is None or val == "":
            continue
        try:
            typed = cast(val)
            if transform:
                typed = transform(typed)
        except (ValueError, TypeError):
            continue
        conditions.append(f"{col} {op} ?")
        params.append(typed)
        if "pu." in col:
            needs_zone_join = True

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params, needs_zone_join
