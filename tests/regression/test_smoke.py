"""
Smoke tests - Quick tests to verify API is functioning (< 30 seconds total)

Run these after every deployment to quickly verify basic functionality.

Usage:
    HYDROCRON_ENV=uat poetry run pytest tests/regression/test_smoke.py -v -m smoke
"""
import pytest
from .utils import assert_http_success, validate_geojson_structure, validate_csv_structure


@pytest.mark.smoke
class TestAPIHealth:
    """Basic API health checks"""

    def test_api_responds(self, api_client, stable_test_data):
        """Test API is up and responding"""
        reach_data = stable_test_data["reach"]

        response, elapsed = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str"
        })

        assert_http_success(response)
        assert elapsed < 3, f"API response took {elapsed:.2f}s (expected < 3s)"


@pytest.mark.smoke
@pytest.mark.parametrize("feature_key,feature_name", [
    ("reach", "Reach"),
    ("node", "Node"),
    ("priorlake", "PriorLake"),
])
class TestBasicQueryPerFeature:
    """Test basic query for each feature type"""

    def test_feature_type_works(self, api_client, stable_test_data, feature_key, feature_name):
        """Test each feature type returns 200 OK"""
        # Get test data from stable_test_data
        test_data = stable_test_data[feature_key]

        # Determine field name based on feature type
        id_field = {
            "Reach": "reach_id",
            "Node": "node_id",
            "PriorLake": "lake_id"
        }[feature_name]

        response, _ = api_client.query({
            "feature": feature_name,
            "feature_id": test_data["feature_id"],
            "start_time": test_data["start_time"],
            "end_time": test_data["end_time"],
            "output": "csv",
            "fields": f"{id_field},time_str,wse"
        })

        assert_http_success(response)

        # Verify response has data
        data = response.json()
        assert 'hits' in data, f"{feature_name} query returned no hits field"
        assert data['hits'] > 0, f"{feature_name} query returned 0 results"


@pytest.mark.smoke
@pytest.mark.parametrize("output_format", ["csv", "geojson"])
class TestOutputFormats:
    """Test both output formats work"""

    def test_output_format_works(self, api_client, output_format):
        """Test output format returns valid data"""
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "34296500851",
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-02-11T00:00:00Z",
            "output": output_format,
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)

        # Both formats are JSON-wrapped
        data = response.json()
        assert 'status' in data
        assert 'results' in data

        # Validate structure based on output format
        if output_format == "geojson":
            assert 'geojson' in data['results']
            geojson = data['results']['geojson']
            validate_geojson_structure(geojson)
        elif output_format == "csv":
            assert 'csv' in data['results']
            from .utils import extract_csv_from_response
            csv_text = extract_csv_from_response(data)
            validate_csv_structure(csv_text, expected_fields=["reach_id", "time_str", "wse"])


@pytest.mark.smoke
class TestErrorHandling:
    """Quick tests for error handling"""

    def test_missing_required_parameter_returns_error(self, api_client):
        """Test missing required parameter returns 400"""
        response, _ = api_client.query({
            "feature": "Reach",
            # Missing feature_id
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-02T00:00:00Z"
        })

        assert response.status_code == 400, \
            f"Expected error status, got {response.status_code}"

    def test_invalid_feature_type_returns_error(self, api_client):
        """Test invalid feature type returns 400"""
        response, _ = api_client.query({
            "feature": "InvalidFeature",
            "feature_id": "123456789",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-02T00:00:00Z"
        })

        assert response.status_code == 400, \
            f"Expected error status, got {response.status_code}"
