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

    def test_api_responds(self, api_client):
        """Test API is up and responding"""
        response, elapsed = api_client.query({
            "feature": "Reach",
            "feature_id": "34296500851",
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-02-10T00:01:00Z",  # Very short range
            "output": "geojson",
            "fields": "reach_id,time_str"
        })

        assert_http_success(response)
        assert elapsed < 10, f"API response took {elapsed:.2f}s (expected < 10s)"


@pytest.mark.smoke
@pytest.mark.parametrize("feature,feature_id,start_time,end_time", [
    ("Reach", "34296500851", "2024-02-10T00:00:00Z", "2024-02-11T00:00:00Z"),
    ("Node", "31241400580011", "2026-02-01T00:00:00Z", "2026-02-02T00:00:00Z"),
    ("PriorLake", "9120274662", "2024-06-22T00:00:00Z", "2024-06-23T00:00:00Z"),
])
class TestBasicQueryPerFeature:
    """Test basic query for each feature type"""

    def test_feature_type_works(self, api_client, feature, feature_id, start_time, end_time):
        """Test each feature type returns 200 OK"""
        # Determine field name based on feature type
        id_field = {
            "Reach": "reach_id",
            "Node": "node_id",
            "PriorLake": "lake_id"
        }[feature]

        response, _ = api_client.query({
            "feature": feature,
            "feature_id": feature_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": "csv",
            "fields": f"{id_field},time_str,wse"
        })

        assert_http_success(response)
        assert len(response.text) > 0, f"{feature} query returned empty response"


@pytest.mark.smoke
@pytest.mark.parametrize("output_format,content_type", [
    ("csv", "text/csv"),
    ("geojson", "application/json"),
])
class TestOutputFormats:
    """Test both output formats work"""

    def test_output_format_works(self, api_client, output_format, content_type):
        """Test output format produces correct content type"""
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "34296500851",
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-02-11T00:00:00Z",
            "output": output_format,
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)

        # Check content type
        response_content_type = response.headers.get("Content-Type", "")
        assert content_type in response_content_type, \
            f"Expected {content_type} in Content-Type, got {response_content_type}"

        # Validate structure
        if output_format == "geojson":
            data = response.json()
            # Handle wrapped response
            if 'results' in data and 'geojson' in data['results']:
                data = data['results']['geojson']
            validate_geojson_structure(data)
        elif output_format == "csv":
            validate_csv_structure(response.text, expected_fields=["reach_id", "time_str", "wse"])


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

        assert response.status_code >= 400, \
            f"Expected error status, got {response.status_code}"

    def test_invalid_feature_type_returns_error(self, api_client):
        """Test invalid feature type returns 400"""
        response, _ = api_client.query({
            "feature": "InvalidFeature",
            "feature_id": "123456789",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-02T00:00:00Z"
        })

        assert response.status_code >= 400, \
            f"Expected error status, got {response.status_code}"
