# Urban Mobility Data Explorer

## Backend Setup

1. Open a terminal and navigate to the backend folder:
   ```powershell
   cd "c:\Users\Pc\Downloads\kizito assign\WEB ent\Urban-Mobility-Data-Explorer\backend"
   ```

2. Create and activate a virtual environment:
   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install Flask backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Install data pipeline dependencies:
   ```powershell
   pip install -r requirements-pipeline.txt
   ```

5. Place the raw data files in the `backend/data` folder:
   - `backend/data/yellow_tripdata.parquet`
   - `backend/data/taxi_zone_lookup.csv`
   - `backend/data/taxi_zones.geojson`

6. Load the data into SQLite and populate the database:
   ```powershell
   py pipeline.py
   ```

7. Start the backend server:
   ```powershell
   py run.py
   ```

8. Access the API at:
   ```text
   http://127.0.0.1:5000/api
   ```

## API Example Usage

Basic examples to exercise the backend endpoints once the server is running.

- Get overall metrics (optionally pass `start_date` and `end_date` as ISO datetimes):

```bash
curl "http://127.0.0.1:5000/api/analytics/metrics"
```

- Get busiest pickup zones (top 10 by trip count):

```bash
curl "http://127.0.0.1:5000/api/analytics/busiest-zones?limit=10"
```

- Paginated trips (page 1, 25 per page):

```bash
curl "http://127.0.0.1:5000/api/trips?page=1&per_page=25"
```

- Get all taxi zones geojson for Leaflet:

```bash
curl "http://127.0.0.1:5000/api/zones"
```

Replace `curl` with your preferred HTTP client. The endpoints return JSON responses with `success` and `data` fields.
