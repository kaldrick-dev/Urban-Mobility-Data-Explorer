import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from config import (
    DATABASE_PATH,
    DATA_CLEANING_LOG_PATH,
    REJECTED_RECORDS_PATH,
    TAXI_ZONE_LOOKUP_PATH,
    TAXI_ZONES_GEOJSON_PATH,
    TAXI_ZONES_SHP_PATH,
    YELLOW_TRIPDATA_PATH,
)
from app.db import insert_many, initialize_database


def load_zone_lookup():
    df = pd.read_csv(TAXI_ZONE_LOOKUP_PATH)
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={"locationid": "zone_id"})
    df["zone_id"] = df["zone_id"].astype(int)
    return df[["zone_id", "borough", "zone", "service_zone"]]


def load_geojson_zones():
    shp_path = Path(TAXI_ZONES_SHP_PATH)

    if shp_path.exists():
        import geopandas as gpd
        from shapely.geometry import mapping

        gdf = gpd.read_file(str(shp_path))
        if gdf.crs is not None:
            gdf = gdf.to_crs(epsg=4326)

        geo_map = {}
        for _, row in gdf.iterrows():
            zone_id = row.get("LocationID") or row.get("location_id")
            if zone_id is not None:
                geo_map[int(zone_id)] = json.dumps(mapping(row.geometry))
        return geo_map

    data = json.loads(Path(TAXI_ZONES_GEOJSON_PATH).read_text(encoding="utf-8"))
    geo_map = {}
    for feature in data["features"]:
        props = feature["properties"]
        zone_id = props.get("LocationID") or props.get("location_id")
        if zone_id is not None:
            geo_map[int(zone_id)] = json.dumps(feature["geometry"])
    return geo_map


def build_zone_table():
    lookup_df = load_zone_lookup()
    geo_map = load_geojson_zones()

    rows = []
    for _, row in lookup_df.iterrows():
        zone_id = int(row["zone_id"])
        rows.append((
            zone_id,
            str(row["borough"]).strip(),
            str(row["zone"]).strip(),
            str(row["service_zone"]).strip(),
            geo_map.get(zone_id, "null"),
        ))
    return rows


def clean_trip_data(raw_df):
    df = raw_df.copy()
    df = df.rename(columns={
        "tpep_pickup_datetime": "pickup_datetime",
        "tpep_dropoff_datetime": "dropoff_datetime",
    })

    before_dedup = len(df)
    df = df.drop_duplicates()
    duplicates_removed = before_dedup - len(df)

    rejected_frames = []

    def drop_and_track(df, mask, reason):
        bad = df[mask][["pickup_datetime", "dropoff_datetime", "trip_distance",
                         "fare_amount", "total_amount", "PULocationID", "DOLocationID"]].copy()
        bad["rejection_reason"] = reason
        rejected_frames.append(bad)
        return df[~mask], int(mask.sum())

    df, n_invalid_datetime   = drop_and_track(df, df["pickup_datetime"].isna() | df["dropoff_datetime"].isna(), "invalid_datetime")
    df, n_invalid_distance   = drop_and_track(df, df["trip_distance"] <= 0, "invalid_distance")
    df, n_invalid_fare       = drop_and_track(df, df["fare_amount"] <= 0, "invalid_fare")
    df, n_invalid_total      = drop_and_track(df, df["total_amount"] <= 0, "invalid_total")
    df, n_bad_temporal       = drop_and_track(df, df["dropoff_datetime"] <= df["pickup_datetime"], "dropoff_before_pickup")
    df, n_bad_passengers     = drop_and_track(df, df["passenger_count"].fillna(0) <= 0, "invalid_passenger_count")
    df, n_bad_location       = drop_and_track(df, ~(df["PULocationID"].between(1, 263) & df["DOLocationID"].between(1, 263)), "invalid_location_id")
    df, n_distance_outlier   = drop_and_track(df, df["trip_distance"] > 100, "distance_outlier")
    df, n_fare_outlier       = drop_and_track(df, df["fare_amount"] > 500, "fare_outlier")

    duration_seconds = (df["dropoff_datetime"] - df["pickup_datetime"]).dt.total_seconds()
    df["trip_duration_minutes"] = (duration_seconds / 60).round(2)
    df["average_speed_mph"] = (df["trip_distance"] / (duration_seconds / 3600)).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)
    df["tip_percentage"] = (df["tip_amount"].fillna(0) / df["fare_amount"] * 100).fillna(0).round(2)
    df["rush_hour_flag"] = (
        (df["pickup_datetime"].dt.weekday < 5) & df["pickup_datetime"].dt.hour.isin([7, 8, 9, 16, 17, 18])
    ).astype(int)

    df, n_speed_outlier = drop_and_track(df, df["average_speed_mph"] > 100, "speed_outlier")

    rule_counts = {
        "duplicates":              duplicates_removed,
        "invalid_datetime":        n_invalid_datetime,
        "invalid_distance":        n_invalid_distance,
        "invalid_fare":            n_invalid_fare,
        "invalid_total":           n_invalid_total,
        "dropoff_before_pickup":   n_bad_temporal,
        "invalid_passenger_count": n_bad_passengers,
        "invalid_location_id":     n_bad_location,
        "distance_outlier":        n_distance_outlier,
        "fare_outlier":            n_fare_outlier,
        "speed_outlier":           n_speed_outlier,
        "final_row_count":         len(df),
    }

    rejected = pd.concat(rejected_frames, ignore_index=True) if rejected_frames else pd.DataFrame()
    return df, rule_counts, rejected


def build_trip_rows(df):
    rows = []
    for r in df.to_dict("records"):
        rows.append((
            r["pickup_datetime"].isoformat(sep=" "),
            r["dropoff_datetime"].isoformat(sep=" "),
            int(r.get("passenger_count") or 0),
            float(r.get("trip_distance") or 0.0),
            int(r.get("PULocationID") or 0),
            int(r.get("DOLocationID") or 0),
            float(r.get("fare_amount") or 0.0),
            float(r.get("tip_amount") or 0.0),
            float(r.get("total_amount") or 0.0),
            float(r["trip_duration_minutes"]),
            float(r["average_speed_mph"]),
            float(r["tip_percentage"]),
            int(r["rush_hour_flag"]),
        ))
    return rows


def write_cleaning_log(counts, total_initial):
    total_removed = total_initial - counts["final_row_count"]
    lines = [
        "Data cleaning execution log",
        "---------------------------",
        f"Initial row count:               {total_initial}",
        f"Duplicates removed:              {counts['duplicates']}",
        f"Dropped - invalid datetime:      {counts['invalid_datetime']}",
        f"Dropped - non-positive distance: {counts['invalid_distance']}",
        f"Dropped - non-positive fare:     {counts['invalid_fare']}",
        f"Dropped - non-positive total:    {counts['invalid_total']}",
        f"Dropped - dropoff before pickup: {counts['dropoff_before_pickup']}",
        f"Dropped - invalid passengers:    {counts['invalid_passenger_count']}",
        f"Dropped - invalid location IDs:  {counts['invalid_location_id']}",
        f"Dropped - distance > 100 miles:  {counts['distance_outlier']}",
        f"Dropped - fare > $500:           {counts['fare_outlier']}",
        f"Dropped - speed > 100 mph:       {counts['speed_outlier']}",
        "---------------------------",
        f"Total rows removed:              {total_removed}",
        f"Final row count loaded:          {counts['final_row_count']}",
    ]
    Path(DATA_CLEANING_LOG_PATH).write_text("\n".join(lines), encoding="utf-8")


def populate_database():
    db_path = Path(DATABASE_PATH)
    if db_path.exists():
        db_path.unlink()
    initialize_database()

    zone_rows = build_zone_table()
    insert_many(
        "INSERT OR REPLACE INTO taxi_zones (zone_id, borough, zone, service_zone, geometry) VALUES (?, ?, ?, ?, ?);",
        zone_rows,
    )

    total_counts = {
        "duplicates": 0, "invalid_datetime": 0, "invalid_distance": 0,
        "invalid_fare": 0, "invalid_total": 0, "dropoff_before_pickup": 0,
        "invalid_passenger_count": 0, "invalid_location_id": 0,
        "distance_outlier": 0, "fare_outlier": 0, "speed_outlier": 0,
        "final_row_count": 0,
    }

    trip_query = """
        INSERT INTO trips (
            pickup_datetime, dropoff_datetime, passenger_count, trip_distance,
            pulocation_id, dolocation_id, fare_amount, tip_amount, total_amount,
            trip_duration_minutes, average_speed_mph, tip_percentage,
            rush_hour_flag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    total_initial = 0
    all_rejected = []

    for i, batch in enumerate(pq.ParquetFile(str(YELLOW_TRIPDATA_PATH)).iter_batches(batch_size=200_000), start=1):
        chunk = batch.to_pandas()
        total_initial += len(chunk)

        cleaned_df, counts, rejected = clean_trip_data(chunk)
        insert_many(trip_query, build_trip_rows(cleaned_df))

        for key in total_counts:
            total_counts[key] += counts.get(key, 0)

        if not rejected.empty:
            all_rejected.append(rejected)

        print(f"Chunk {i}: {len(chunk)} rows read, {len(cleaned_df)} kept.")

    write_cleaning_log(total_counts, total_initial)

    if all_rejected:
        pd.concat(all_rejected, ignore_index=True).to_csv(str(REJECTED_RECORDS_PATH), index=False)
        print(f"Rejected records saved to {REJECTED_RECORDS_PATH}.")

    print(f"Done. {total_counts['final_row_count']} trips and {len(zone_rows)} zones loaded.")


if __name__ == "__main__":
    populate_database()
