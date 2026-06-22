# Data directory

Place raw input files under `backend/data/` before running the ingestion pipeline.

Expected files (examples):

- `backend/data/yellow_tripdata_YYYY-MM.parquet` — monthly trip parquet files.
- `backend/data/taxi_zone_lookup.csv` — zone lookup metadata (zone id, borough, zone name).
- `backend/data/taxi_zones/` — shapefile pieces for zone geometries (`.shp`, `.dbf`, `.prj`, `.shx`, etc.).

Notes

- Raw data are not tracked in this repository. Download them from your data provider
  or assignment page and place them in the locations above.
- The ingestion pipeline expects the files listed; if filenames differ, update `backend/config.py`.
- The pipeline writes two useful artifacts to `backend/`:
  - `data_cleaning_log.txt` — aggregate counts of rows removed per rule
  - `data_cleaning_rejected.csv` — full list of rejected rows with reasons
