from app.db import fetch_all, fetch_one


def get_all_zones(borough: str | None = None):
    if borough:
        sql = "SELECT zone_id, borough, zone, service_zone, geometry FROM taxi_zones WHERE borough = ? ORDER BY zone;"
        return fetch_all(sql, [borough])

    sql = "SELECT zone_id, borough, zone, service_zone, geometry FROM taxi_zones ORDER BY borough, zone;"
    return fetch_all(sql)


def get_zone_by_id(zone_id: int) -> dict | None:
    sql = "SELECT zone_id, borough, zone, service_zone, geometry FROM taxi_zones WHERE zone_id = ?;"
    return fetch_one(sql, [zone_id])


def get_zones_by_borough(borough: str):
    sql = "SELECT zone_id, borough, zone, service_zone, geometry FROM taxi_zones WHERE borough = ? ORDER BY zone;"
    return fetch_all(sql, [borough])


def get_distinct_boroughs():
    sql = "SELECT DISTINCT borough FROM taxi_zones WHERE borough IS NOT NULL ORDER BY borough;"
    rows = fetch_all(sql)
    return [row["borough"] for row in rows]
