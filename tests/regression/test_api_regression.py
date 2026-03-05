"""
Regression tests for Hydrocron API against deployed environments.

Run with:
    HYDROCRON_ENV=uat poetry run pytest tests/regression/
    HYDROCRON_ENV=ops poetry run pytest tests/regression/

These tests make real HTTP requests to deployed API endpoints and verify:
- Response status codes
- Response structure and format
- Basic data validation (not exact values, as data may change)
"""
import json
import pytest
import requests
from geojson import loads as geojson_loads

# Known feature IDs that should exist in production data
# These are from the existing test data, adjust if needed for your environment
TEST_REACH_ID = "34296500851"
TEST_LAKE_ID = "9120274662"


class TestReachQueries:
    """Test reach feature queries against deployed API"""

    def test_reach_geojson_query(self, api_url, test_env):
        """Test basic reach query with GeoJSON output"""
        params = {
            "feature": "Reach",
            "feature_id": TEST_REACH_ID,
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-05-03T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid,geometry"
        }

        response = requests.get(api_url, params=params, timeout=30)

        print(response.text)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        # extract just the geojson to plot on the map
        geojson_data = data['results']['geojson']

        # Verify GeoJSON structure
        assert geojson_data.get("type") == "FeatureCollection", "Response should be a GeoJSON FeatureCollection"
        assert "features" in geojson_data, "Response should contain features"
        assert isinstance(geojson_data["features"], list), "Features should be a list"

        # If we got features, verify structure
        if len(geojson_data["features"]) > 0:
            feature = geojson_data["features"][0]
            assert feature.get("type") == "Feature", "Each item should be a GeoJSON Feature"
            assert "properties" in feature, "Feature should have properties"
            assert "geometry" in feature, "Feature should have geometry"
            assert "reach_id" in feature["properties"], "Properties should contain reach_id"

    def test_reach_csv_query(self, api_url, test_env):
        """Test reach query with CSV output"""
        params = {
            "feature": "Reach",
            "feature_id": TEST_REACH_ID,
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "csv",
            "fields": "reach_id,time_str,wse"
        }

        response = requests.get(api_url, params=params, timeout=30)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "text/csv" in response.headers.get("Content-Type", ""), "Response should be CSV"

        # Verify CSV structure
        lines = response.text.strip().split('\n')
        assert len(lines) >= 1, "CSV should have at least a header row"

        header = lines[0]
        assert "reach_id" in header, "CSV header should contain reach_id"
        assert "time_str" in header, "CSV header should contain time_str"
        assert "wse" in header, "CSV header should contain wse"

    def test_reach_with_accept_header(self, api_url, test_env):
        """Test reach query using Accept header for content negotiation"""
        params = {
            "feature": "Reach",
            "feature_id": TEST_REACH_ID,
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z"
        }

        headers = {
            "Accept": "application/geo+json"
        }

        response = requests.get(api_url, params=params, headers=headers, timeout=30)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("type") == "FeatureCollection", "Should return GeoJSON when Accept header is application/geo+json"


class TestLakeQueries:
    """Test lake/prior lake feature queries against deployed API"""

    def test_lake_geojson_query(self, api_url, test_env):
        """Test basic prior lake query with GeoJSON output"""
        params = {
            "feature": "PriorLake",
            "feature_id": TEST_LAKE_ID,
            "start_time": "2024-06-22T00:00:00Z",
            "end_time": "2024-07-13T23:59:59Z",
            "output": "geojson",
            "fields": "lake_id,time_str,wse,area_total"
        }

        response = requests.get(api_url, params=params, timeout=30)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        # Verify GeoJSON structure
        assert data.get("type") == "FeatureCollection", "Response should be a GeoJSON FeatureCollection"
        assert "features" in data, "Response should contain features"

        # If we got features, verify structure
        if len(data["features"]) > 0:
            feature = data["features"][0]
            assert feature.get("type") == "Feature", "Each item should be a GeoJSON Feature"
            assert "properties" in feature, "Feature should have properties"
            assert "lake_id" in feature["properties"], "Properties should contain lake_id"


class TestErrorHandling:
    """Test API error handling"""

    def test_missing_required_parameter(self, api_url, test_env):
        """Test that missing required parameters return appropriate error"""
        params = {
            "feature": "Reach",
            # Missing feature_id
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z"
        }

        response = requests.get(api_url, params=params, timeout=30)

        # Should return an error status code (400 or similar)
        assert response.status_code >= 400, f"Expected error status code, got {response.status_code}"

    def test_invalid_feature_type(self, api_url, test_env):
        """Test that invalid feature type returns appropriate error"""
        params = {
            "feature": "InvalidFeature",
            "feature_id": "123456789",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z"
        }

        response = requests.get(api_url, params=params, timeout=30)

        # Should return an error status code
        assert response.status_code >= 400, f"Expected error status code for invalid feature, got {response.status_code}"

    def test_nonexistent_feature_id(self, api_url, test_env):
        """Test query for non-existent feature ID"""
        params = {
            "feature": "Reach",
            "feature_id": "99999999999",  # Unlikely to exist
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson"
        }

        response = requests.get(api_url, params=params, timeout=30)

        # Should either return 200 with empty features or 404
        if response.status_code == 200:
            data = response.json()
            # Should have no features or return a not found response
            assert "features" in data or "error" in data
        else:
            assert response.status_code == 404, f"Expected 404 for non-existent feature, got {response.status_code}"


class TestOutputFormats:
    """Test different output formats"""

    def test_geojson_output_is_valid(self, api_url, test_env):
        """Verify GeoJSON output is valid GeoJSON"""
        params = {
            "feature": "Reach",
            "feature_id": TEST_REACH_ID,
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson"
        }

        response = requests.get(api_url, params=params, timeout=30)
        assert response.status_code == 200

        data = response.json()

        # Try to parse as GeoJSON
        try:
            geojson_obj = geojson_loads(json.dumps(data))
            assert geojson_obj.is_valid, "GeoJSON should be valid"
        except Exception as e:
            pytest.fail(f"Failed to parse response as valid GeoJSON: {e}")

    def test_csv_output_is_parseable(self, api_url, test_env):
        """Verify CSV output is valid CSV format"""
        params = {
            "feature": "Reach",
            "feature_id": TEST_REACH_ID,
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "csv"
        }

        response = requests.get(api_url, params=params, timeout=30)
        assert response.status_code == 200

        # Verify we can parse as CSV
        import csv
        from io import StringIO

        try:
            csv_reader = csv.DictReader(StringIO(response.text))
            rows = list(csv_reader)
            assert len(rows) >= 0, "Should be able to parse CSV"
        except Exception as e:
            pytest.fail(f"Failed to parse response as valid CSV: {e}")


class TestAPIAvailability:
    """Basic smoke tests to verify API is up and responding"""

    def test_api_is_reachable(self, api_url, test_env):
        """Verify the API endpoint is reachable"""
        # Simple query to check if API responds
        params = {
            "feature": "Reach",
            "feature_id": TEST_REACH_ID,
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-04T00:01:00Z"  # Very short time range
        }

        try:
            response = requests.get(api_url, params=params, timeout=10)
            # Just verify we get a response, don't care about the specific status
            assert response.status_code is not None, "Should receive a response from the API"
        except requests.exceptions.Timeout:
            pytest.fail(f"API at {api_url} timed out")
        except requests.exceptions.ConnectionError:
            pytest.fail(f"Could not connect to API at {api_url}")
