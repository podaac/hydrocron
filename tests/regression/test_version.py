"""
Regression tests for version fields (collection_version, sword_version)

Verifies that version fields are populated correctly in DynamoDB
and returned in API responses.

Expected collection_version values:
  - SWOT_L2_HR_RiverSP_2.0 / SWOT_L2_HR_LakeSP_2.0 -> "2.0"
  - SWOT_L2_HR_RiverSP_D / SWOT_L2_HR_LakeSP_D -> "D"

Expected sword_version values:
  - v2 (PIC) -> "16"
  - vD (PID) -> "17b"

Usage:
    HYDROCRON_ENV=ops poetry run pytest tests/regression/test_version.py -v
"""
import csv
from io import StringIO

import pytest
from .utils import assert_http_success, extract_csv_from_response, extract_geojson_from_response


@pytest.mark.parametrize("data_key,expected_version", [
    ("reach", "2.0"),
    ("node", "2.0"),
    ("priorlake", "2.0"),
    ("reach_d", "D"),
    ("node_d", "D"),
    ("priorlake_d", "D"),
])
class TestCollectionVersion:
    """Test that collection_version is populated correctly in API responses (issue #288)"""

    def test_collection_version_in_geojson(self, api_client, stable_test_data, data_key, expected_version):
        """Test collection_version field is present and correct in GeoJSON response"""
        test_data = stable_test_data[data_key]

        if "reach" in data_key:
            feature = "Reach"
            id_field = "reach_id"
        elif "node" in data_key:
            feature = "Node"
            id_field = "node_id"
        else:
            feature = "PriorLake"
            id_field = "lake_id"

        response, _ = api_client.query({
            "feature": feature,
            "feature_id": test_data["feature_id"],
            "start_time": test_data["start_time"],
            "end_time": test_data["end_time"],
            "output": "geojson",
            "fields": f"{id_field},time_str,collection_version",
            "collection_name": test_data["collection_name"]
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        assert len(geojson['features']) > 0, \
            f"No features returned for {data_key}"

        for i, feature_obj in enumerate(geojson['features']):
            version = feature_obj['properties'].get('collection_version', '')
            assert version == expected_version, \
                f"Feature {i}: collection_version = '{version}', expected '{expected_version}'"


    def test_collection_version_in_csv(self, api_client, stable_test_data, data_key, expected_version):
        """Test collection_version field is present and correct in CSV response"""
        test_data = stable_test_data[data_key]

        if "reach" in data_key:
            feature = "Reach"
            id_field = "reach_id"
        elif "node" in data_key:
            feature = "Node"
            id_field = "node_id"
        else:
            feature = "PriorLake"
            id_field = "lake_id"

        response, _ = api_client.query({
            "feature": feature,
            "feature_id": test_data["feature_id"],
            "start_time": test_data["start_time"],
            "end_time": test_data["end_time"],
            "output": "csv",
            "fields": f"{id_field},time_str,collection_version",
            "collection_name": test_data["collection_name"]
        })

        assert_http_success(response)

        data = response.json()
        csv_text = extract_csv_from_response(data)
        rows = list(csv.DictReader(StringIO(csv_text)))

        assert len(rows) > 0, f"No data rows returned for {data_key}"
        assert 'collection_version' in rows[0], \
            "collection_version field not in CSV headers"

        for i, row in enumerate(rows):
            version = row['collection_version']
            assert version == expected_version, \
                f"Row {i}: collection_version = '{version}', expected '{expected_version}'"


@pytest.mark.parametrize("data_key,expected_sword_version", [
    ("reach", "16"),
    ("node", "16"),
    ("reach_d", "17b"),
    ("node_d", "17b"),
])
class TestSwordVersion:
    """Test that sword_version is populated correctly in API responses"""

    def test_sword_version_in_geojson(self, api_client, stable_test_data, data_key, expected_sword_version):
        """Test sword_version field is present and correct in GeoJSON response"""
        test_data = stable_test_data[data_key]

        if "reach" in data_key:
            feature = "Reach"
            id_field = "reach_id"
        else:
            feature = "Node"
            id_field = "node_id"

        response, _ = api_client.query({
            "feature": feature,
            "feature_id": test_data["feature_id"],
            "start_time": test_data["start_time"],
            "end_time": test_data["end_time"],
            "output": "geojson",
            "fields": f"{id_field},time_str,sword_version",
            "collection_name": test_data["collection_name"]
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        assert len(geojson['features']) > 0, \
            f"No features returned for {data_key}"

        for i, feature_obj in enumerate(geojson['features']):
            version = feature_obj['properties'].get('sword_version', '')
            assert version == expected_sword_version, \
                f"Feature {i}: sword_version = '{version}', expected '{expected_sword_version}'"

    def test_sword_version_in_csv(self, api_client, stable_test_data, data_key, expected_sword_version):
        """Test sword_version field is present and correct in CSV response"""
        test_data = stable_test_data[data_key]

        if "reach" in data_key:
            feature = "Reach"
            id_field = "reach_id"
        else:
            feature = "Node"
            id_field = "node_id"

        response, _ = api_client.query({
            "feature": feature,
            "feature_id": test_data["feature_id"],
            "start_time": test_data["start_time"],
            "end_time": test_data["end_time"],
            "output": "csv",
            "fields": f"{id_field},time_str,sword_version",
            "collection_name": test_data["collection_name"]
        })

        assert_http_success(response)

        data = response.json()
        csv_text = extract_csv_from_response(data)
        rows = list(csv.DictReader(StringIO(csv_text)))

        assert len(rows) > 0, f"No data rows returned for {data_key}"
        assert 'sword_version' in rows[0], \
            "sword_version field not in CSV headers"

        for i, row in enumerate(rows):
            version = row['sword_version']
            assert version == expected_sword_version, \
                f"Row {i}: sword_version = '{version}', expected '{expected_sword_version}'"
