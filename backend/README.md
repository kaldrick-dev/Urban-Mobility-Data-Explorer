# Urban Mobility Data Explorer — Backend

Flask + SQLite backend that ingests NYC Yellow Taxi trip data, cleans it, and exposes it through a REST API.

---

## Project Structure

```
backend/
├── app/
│   ├── db.py              # SQLite helpers (fetch, insert, execute)
│   ├── models/            # Table schemas and indexes
│   ├── routes/            # API route definitions
│   └── services/          # Business logic / query layer
├── data/                  # Raw data files (not committed — see below)
├── config.py              # File paths and app config
├── pipeline.py            # Data ingestion and cleaning script
├── run.py                 # Flask app entry point
└── requirements.txt       # Python dependencies
```

---

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Mac/Linux
   .\.venv\Scripts\Activate.ps1     # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Data Files

The raw data files are not committed to this repo. Download them from the Canvas assignment page and place them under `backend/data/`:

```
backend/data/
├── yellow_tripdata_2026-01.parquet
├── taxi_zone_lookup.csv
└── taxi_zones/
    └── taxi_zones.shp  (plus .dbf, .prj, .shx, etc.)
```

---

## Running the Pipeline

The pipeline loads the raw data, cleans it, and populates the SQLite database.

```bash
python pipeline.py
```

What it does:

1. Drops and recreates `mobility.db`
2. Loads 263 taxi zones from `taxi_zone_lookup.csv` + shapefile geometry
3. Reads the parquet file in batches of 200,000 rows
4. For each batch: removes duplicates, filters invalid/outlier rows, computes derived features, inserts clean rows into `trips`
5. Writes `data_cleaning_log.txt` (aggregate counts per rule)
6. Writes `data_cleaning_rejected.csv` (every dropped row with its rejection reason)

---

## Database Schema

### `taxi_zones`

| Column       | Type       | Description                 |
| ------------ | ---------- | --------------------------- |
| zone_id      | INTEGER PK | NYC TLC location ID (1–263) |
| borough      | TEXT       | Borough name                |
| zone         | TEXT       | Zone name                   |
| service_zone | TEXT       | Service category            |
| geometry     | TEXT       | GeoJSON geometry string     |

### `trips`

| Column                | Type       | Description                          |
| --------------------- | ---------- | ------------------------------------ |
| trip_id               | INTEGER PK | Auto-incremented                     |
| pickup_datetime       | TEXT       | Trip start timestamp                 |
| dropoff_datetime      | TEXT       | Trip end timestamp                   |
| passenger_count       | INTEGER    | Number of passengers                 |
| trip_distance         | REAL       | Distance in miles                    |
| pulocation_id         | INTEGER FK | Pickup zone (→ taxi_zones)           |
| dolocation_id         | INTEGER FK | Dropoff zone (→ taxi_zones)          |
| fare_amount           | REAL       | Base fare                            |
| tip_amount            | REAL       | Tip amount                           |
| total_amount          | REAL       | Total charged                        |
| trip_duration_minutes | REAL       | Derived: dropoff − pickup in minutes |
| average_speed_mph     | REAL       | Derived: distance / duration         |
| tip_percentage        | REAL       | Derived: tip / fare × 100            |
| rush_hour_flag        | INTEGER    | Derived: 1 if weekday 7–9am or 4–6pm |

---

## Starting the API Server

```bash
python run.py
```

API is available at `http://127.0.0.1:5000/api`

---

## Data Cleaning Rules

Rows are dropped sequentially (no double-counting):

| Rule                  | Condition                             |
| --------------------- | ------------------------------------- |
| Duplicate             | Exact duplicate row                   |
| Invalid datetime      | Null pickup or dropoff                |
| Invalid distance      | `trip_distance <= 0`                  |
| Invalid fare          | `fare_amount <= 0`                    |
| Invalid total         | `total_amount <= 0`                   |
| Dropoff before pickup | `dropoff_datetime <= pickup_datetime` |
| Invalid passengers    | `passenger_count <= 0`                |
| Invalid location ID   | Pickup or dropoff outside zones 1–263 |
| Distance outlier      | `trip_distance > 100 miles`           |
| Fare outlier          | `fare_amount > $500`                  |
| Speed outlier         | `average_speed_mph > 100`             |
