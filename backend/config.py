import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "mobility.db"
RAW_DATA_DIR = BASE_DIR / "data"
YELLOW_TRIPDATA_PATH = RAW_DATA_DIR / "yellow_tripdata.csv"
TAXI_ZONE_LOOKUP_PATH = RAW_DATA_DIR / "taxi_zone_lookup.csv"
TAXI_ZONES_GEOJSON_PATH = RAW_DATA_DIR / "taxi_zones.geojson"
TAXI_ZONES_SHP_PATH = RAW_DATA_DIR / "taxi_zones" / "taxi_zones.shp"
DATA_CLEANING_LOG_PATH = BASE_DIR / "data_cleaning_log.txt"


class Config:
    DEBUG = os.environ.get("FLASK_DEBUG", "1").lower() in {"1", "true", "yes"}
    DATABASE_PATH = str(DATABASE_PATH)
    DATA_CLEANING_LOG_PATH = str(DATA_CLEANING_LOG_PATH)


class DevelopmentConfig(Config):
    pass


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    DEBUG = False
