import json
from pathlib import Path

import pytest

from pipeline import load_geojson_zones


def test_shapefile_conversion_returns_dict_if_present():
    """
    This test will pass if `load_geojson_zones` can be called and returns a dictionary mapping
    integer zone ids to GeoJSON geometry strings. It will be skipped if the shapefile does not exist.
    """
    # The shapefile path configured in `config.py` is expected at backend/data/taxi_zones/taxi_zones.shp
    from config import TAXI_ZONES_SHP_PATH

    shp_path = Path(TAXI_ZONES_SHP_PATH)
    if not shp_path.exists():
        pytest.skip("Shapefile not present in test environment: skipping shapefile conversion test")

    zones = load_geojson_zones()
    assert isinstance(zones, dict)
    assert len(zones) > 0

    # Validate keys are integers and values are valid GeoJSON mappings
    for k, v in list(zones.items())[:5]:
        assert isinstance(k, int)
        assert isinstance(v, str)
        obj = json.loads(v)
        assert isinstance(obj, dict)
        assert "type" in obj
