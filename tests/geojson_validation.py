"""
GeoJSON validity check shared by the unit and regression tests

Automates the manual check of pasting a response into geojson.io: the response must be strict
JSON (no NaN/Infinity), match the official GeoJSON FeatureCollection JSON Schema, and pass the
geojson package's validation (geometry types and coordinates).

Schema: https://geojson.org/schema/FeatureCollection.json (draft-07, self-contained),
copied to tests/schemas/geojson_feature_collection.json on 2026-10-27 so tests need no network.
"""
import json
from pathlib import Path

import geojson
import jsonschema

FEATURE_COLLECTION_SCHEMA = json.loads((Path(__file__).parent / "schemas" / "geojson_feature_collection.json").read_text())


def assert_valid_geojson(collection):
    """Assert a FeatureCollection dict is valid GeoJSON"""
    try:
        text = json.dumps(collection, allow_nan=False)
    except ValueError as error:
        raise AssertionError(f"GeoJSON is not strict JSON (NaN/Infinity): {error}") from error

    collection = json.loads(text)   # validate what the client receives (tuples become arrays)
    try:
        jsonschema.validate(collection, FEATURE_COLLECTION_SCHEMA)
    except jsonschema.ValidationError as error:
        raise AssertionError(f"GeoJSON fails the FeatureCollection schema at {list(error.absolute_path)}: {error.message}") from error

    parsed = geojson.loads(text)
    assert parsed.is_valid, f"GeoJSON is not valid: {parsed.errors()}"

    # Neither check above tests ranges; geojson.io would plot these off the map
    for index, feature in enumerate(collection["features"]):
        if feature["geometry"] is None:   # allowed by GeoJSON
            continue
        for lon, lat, *_ in geojson.utils.coords(feature["geometry"]):
            assert -180 <= lon <= 180 and -90 <= lat <= 90, f"Feature {index} has coordinate out of range: ({lon}, {lat})"
