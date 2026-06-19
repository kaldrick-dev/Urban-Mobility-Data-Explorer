import json
from pathlib import Path

import pandas as pd

from config import (
    DATABASE_PATH,
    DATA_CLEANING_LOG_PATH,
    TAXI_ZONE_LOOKUP_PATH,
    TAXI_ZONES_GEOJSON_PATH,
    TAXI_ZONES_SHP_PATH,
    YELLOW_TRIPDATA_PATH,
)
from app.db import execute_write, insert_many, initialize_database, get_db_connection


def load_zone_lookup():
    df = pd.read_csv(TAXI_ZONE_LOOKUP_PATH)
    df.columns = [c.lower() for c in df.columns]
    expected = {"locationid", "borough", "zone", "service_zone"}
    if not expected.issubset(set(df.columns)):
        raise ValueError(
            f"Expected taxi zone lookup columns to include {expected}, got {set(df.columns)}"
        )
    df = df.rename(columns={"locationid": "zone_id"})
    df["zone_id"] = df["zone_id"].astype(int)
    return df[["zone_id", "borough", "zone", "service_zone"]]


def load_geojson_zones():
    # Prefer shapefile if available. The shapefile is expected at backend/data/taxi_zones/taxi_zones.shp
    shp_path = Path(TAXI_ZONES_SHP_PATH)
    if shp_path.exists():
        try:
            import geopandas as gpd
            from shapely.geometry import mapping
        except Exception as e:
            raise ImportError(
                "geopandas and shapely are required to read the shapefile. Install requirements-pipeline.txt"
            ) from e

        gdf = gpd.read_file(str(shp_path))
        # Reproject to WGS84 (EPSG:4326) so Leaflet can consume the geometries
        if gdf.crs is not None:
            try:
                gdf = gdf.to_crs(epsg=4326)
            except Exception:
                # If reprojection fails, continue but warn
                pass

        geo_map = {}
        # Common property names for LocationID vary; try several
        id_cols = [c for c in ["LocationID", "locationid", "location_id", "LOCATIONID"] if c in gdf.columns]
        for idx, row in gdf.iterrows():
            zone_id = None
            for col in id_cols:
                zone_id = row.get(col)
                if zone_id is not None:
                    break
            if zone_id is None:
                # If no id column, try the index as fallback
                continue
            try:
                zone_id = int(zone_id)
            except (ValueError, TypeError):
                continue
            geom = row.geometry
            if geom is None:
                continue
            geo_map[zone_id] = json.dumps(mapping(geom))
        return geo_map

    # Fallback: read a provided geojson file
    raw_geojson = json.loads(Path(TAXI_ZONES_GEOJSON_PATH).read_text(encoding="utf-8"))
    features = raw_geojson.get("features", [])
    geo_map = {}
    for feature in features:
        props = feature.get("properties", {})
        zone_id = props.get("LocationID") or props.get("locationid") or props.get("location_id")
        if zone_id is None:
            continue
        try:
            zone_id = int(zone_id)
        except (ValueError, TypeError):
            continue
        geometry = feature.get("geometry")
        geo_map[zone_id] = json.dumps(geometry)
    return geo_map


def load_trip_data():
    df = pd.read_parquet(YELLOW_TRIPDATA_PATH)
    return df


def build_zone_table():
    lookup_df = load_zone_lookup()
    geo_map = load_geojson_zones()

    rows = []
    for _, row in lookup_df.iterrows():
        zone_id = int(row["zone_id"])
        rows.append(
            (
                zone_id,
                str(row["borough"]).strip(),
                str(row["zone"]).strip(),
                str(row["service_zone"]).strip(),
                geo_map.get(zone_id, "null"),
            )
        )
    return rows


def clean_trip_data(raw_df: pd.DataFrame):
    df = raw_df.copy()
    if "pickup_datetime" not in df.columns or "dropoff_datetime" not in df.columns:
        raise ValueError("Expected columns pickup_datetime and dropoff_datetime in trip data.")

    df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], errors="coerce")
    df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"], errors="coerce")

    initial_count = len(df)
    rule_counts = {
        "invalid_datetime": int(df["pickup_datetime"].isna() | df["dropoff_datetime"].isna()).sum(),
        "invalid_distance": int((df.get("trip_distance", 0) <= 0).sum()),
        "invalid_fare": int((df.get("fare_amount", 0) <= 0).sum()),
        "invalid_total": int((df.get("total_amount", 0) <= 0).sum()),
    }

    df = df.dropna(subset=["pickup_datetime", "dropoff_datetime"])
    df = df[df["trip_distance"] > 0]
    df = df[df["fare_amount"] > 0]
    df = df[df["total_amount"] > 0]
    df = df[df["dropoff_datetime"] > df["pickup_datetime"]]

    duration_hours = (df["dropoff_datetime"] - df["pickup_datetime"]).dt.total_seconds() / 3600.0
    df["average_speed_mph"] = duration_hours.replace({0: float("nan")})
    df["average_speed_mph"] = df["trip_distance"] / df["average_speed_mph"]
    df["average_speed_mph"] = df["average_speed_mph"].replace([float("inf"), -float("inf")], 0).fillna(0)

    df["tip_percentage"] = df["tip_amount"].fillna(0) / df["fare_amount"].replace(0, float("nan")) * 100
    df["tip_percentage"] = df["tip_percentage"].replace([float("inf"), -float("inf")], 0).fillna(0)

    pickup_hours = df["pickup_datetime"].dt.hour
    is_weekday = df["pickup_datetime"].dt.weekday < 5
    morning = pickup_hours.isin([7, 8, 9])
    evening = pickup_hours.isin([16, 17, 18])
    df["rush_hour_flag"] = ((is_weekday & (morning | evening)).astype(int))

    filtered_count = len(df)
    rule_counts["final_row_count"] = filtered_count
    rule_counts["removed_records"] = initial_count - filtered_count

    return df, rule_counts


def write_cleaning_log(rule_counts):
    lines = [
        "Data cleaning execution log",
        "---------------------------",
        f"Initial row count: {rule_counts.get('final_row_count', 0) + rule_counts.get('removed_records', 0)}",
        f"Rows dropped due to invalid pickup or dropoff datetime: {rule_counts['invalid_datetime']}",
        f"Rows dropped due to non-positive trip distance: {rule_counts['invalid_distance']}",
        f"Rows dropped due to non-positive fare amount: {rule_counts['invalid_fare']}",
        f"Rows dropped due to non-positive total amount: {rule_counts['invalid_total']}",
        f"Rows dropped due to dropoff <= pickup: {rule_counts['removed_records'] - rule_counts['invalid_datetime'] - rule_counts['invalid_distance'] - rule_counts['invalid_fare'] - rule_counts['invalid_total']}",
        f"Final row count loaded: {rule_counts['final_row_count']}",
    ]
    Path(DATA_CLEANING_LOG_PATH).write_text("\n".join(lines), encoding="utf-8")


def populate_database():
    initialize_database()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM taxi_zones")
    cursor.execute("DELETE FROM trips")
    conn.commit()
    conn.close()

    zone_rows = build_zone_table()
    insert_many(
        "INSERT OR REPLACE INTO taxi_zones (zone_id, borough, zone, service_zone, geometry) VALUES (?, ?, ?, ?, ?);",
        zone_rows,
    )

    raw_df = load_trip_data()
    cleaned_df, rule_counts = clean_trip_data(raw_df)
    write_cleaning_log(rule_counts)

    insert_rows = []
    for _, row in cleaned_df.iterrows():
        insert_rows.append(
            (
                row["pickup_datetime"].isoformat(sep=" "),
                row["dropoff_datetime"].isoformat(sep=" "),
                int(row.get("passenger_count", 0) or 0),
                float(row.get("trip_distance", 0.0) or 0.0),
                int(row.get("PULocationID", row.get("pulocation_id", 0)) or 0),
                int(row.get("DOLocationID", row.get("dolocation_id", 0)) or 0),
                float(row.get("fare_amount", 0.0) or 0.0),
                float(row.get("tip_amount", 0.0) or 0.0),
                float(row.get("total_amount", 0.0) or 0.0),
                float(row["average_speed_mph"]),
                float(row["tip_percentage"]),
                int(row["rush_hour_flag"]),
                int(row.get("payment_type", 0) or 0),
            )
        )

    insert_many(
        """
        INSERT INTO trips (
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
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        insert_rows,
    )

    print(f"Loaded {rule_counts['final_row_count']} trips into the database.")
    print(f"Taxi zones loaded: {len(zone_rows)}")


if __name__ == "__main__":
    populate_database()
