Urban Mobility Data Explorer - Backend

## Setup and Run Commands

1. From the `backend` directory, create and activate a virtual environment:
   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install required packages:
   ```powershell
   pip install -r requirements.txt
   pip install -r requirements-pipeline.txt
   ```

3. Confirm the required raw files are available in `backend/data`:
   - `backend/data/yellow_tripdata.parquet`
   - `backend/data/taxi_zone_lookup.csv`
   - `backend/data/taxi_zones.geojson`

4. Run the preprocessing pipeline to populate the SQLite database:
   ```powershell
   py pipeline.py
   ```

5. Start the Flask server:
   ```powershell
   py run.py
   ```

6. API root URL:
   ```text
   http://127.0.0.1:5000/api
   ```

## API Example Calls

- Metrics:

```powershell
curl "http://127.0.0.1:5000/api/analytics/metrics"
```

- Busiest zones:

```powershell
curl "http://127.0.0.1:5000/api/analytics/busiest-zones?limit=10"
```

- Trips (paginated):

```powershell
curl "http://127.0.0.1:5000/api/trips?page=1&per_page=25"
```

- Zones (GeoJSON-like geometry strings):

```powershell
curl "http://127.0.0.1:5000/api/zones"
```

