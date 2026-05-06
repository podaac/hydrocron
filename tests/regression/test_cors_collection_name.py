"""
CORS regression tests for collection_name parameter

Tests to ensure CORS headers are properly returned when using the collection_name
parameter. This addresses the issue where API Gateway was not handling requests
with collection_name parameter correctly due to missing parameter definition
in the OpenAPI specification.

Before the fix: Requests with collection_name parameter would fail with CORS errors
After the fix: All requests should include proper CORS headers regardless of parameters
"""
import pytest
from .utils import (
    assert_http_success
)


class TestCORSWithCollectionName:
    """Test CORS functionality when using collection_name parameter"""

    @pytest.mark.parametrize("data_key", ["reach", "reach_d", "node", "node_d", "priorlake", "priorlake_d"])
    def test_cors_with_explicit_collection_name(self, api_client, stable_test_data, data_key):
        """Test CORS headers with explicit collection_name parameter for all feature types and versions"""
        test_data = stable_test_data[data_key]

        # Determine feature type based on data key
        if "reach" in data_key:
            feature = "Reach"
        elif "node" in data_key:
            feature = "Node"
        else:  # priorlake
            feature = "PriorLake"

        params = {
            "feature": feature,
            "feature_id": test_data["feature_id"],
            "start_time": test_data["start_time"],
            "end_time": test_data["end_time"],
            "output": "geojson",
            "fields": test_data["fields"],  # Use fields from stable data
            "collection_name": test_data["collection_name"]  # Explicit collection_name
        }

        response, _ = api_client.query(params)

        # Check request succeeds
        assert_http_success(response)

        # Verify CORS header is present (only Access-Control-Allow-Origin is configured for GET requests)
        assert 'Access-Control-Allow-Origin' in response.headers, \
            "Missing Access-Control-Allow-Origin header"

    @pytest.mark.parametrize("data_key", ["reach_d", "node_d", "priorlake_d"])
    def test_cors_with_default_collection_name(self, api_client, stable_test_data, data_key):
        """Test CORS headers with default collection_name (no explicit parameter) for all feature types (D versions only)"""
        test_data = stable_test_data[data_key]

        # Determine feature type based on data key
        if "reach" in data_key:
            feature = "Reach"
        elif "node" in data_key:
            feature = "Node"
        else:  # priorlake
            feature = "PriorLake"

        params = {
            "feature": feature,
            "feature_id": test_data["feature_id"],
            "start_time": test_data["start_time"],
            "end_time": test_data["end_time"],
            "output": "geojson",
            "fields": test_data["fields"]  # Use fields from stable data
            # No collection_name - uses default
        }

        response, _ = api_client.query(params)

        # Check request succeeds
        assert_http_success(response)

        # Verify CORS header is present (only Access-Control-Allow-Origin is configured for GET requests)
        assert 'Access-Control-Allow-Origin' in response.headers, \
            "Missing Access-Control-Allow-Origin header"

    def test_cors_on_error_response_with_collection_name(self, api_client):
        """
        Test CORS headers are present on error responses when using collection_name parameter.

        This is a critical test - CORS headers must be present on ALL responses including errors,
        otherwise browsers will block the error response and users won't see the actual error message.
        """
        # Use an invalid feature_id that will trigger a 400 error
        params = {
            "feature": "Reach",
            "feature_id": "00000000000",  # Invalid feature_id
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-02T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse",
            "collection_name": "SWOT_L2_HR_RiverSP_D"
        }

        response, _ = api_client.query(params)

        # We expect a 400 error for invalid feature_id
        assert response.status_code == 400, \
            f"Expected 400 error for invalid feature_id, got {response.status_code}"

        # CORS header MUST be present even on error responses
        assert 'Access-Control-Allow-Origin' in response.headers, \
            "Missing Access-Control-Allow-Origin header on error response. " \
            "This causes browsers to block error messages from being displayed to users."

    def test_cors_on_error_response_without_collection_name(self, api_client):
        """
        Test CORS headers are present on error responses without collection_name parameter.

        Verifies that error responses include CORS headers regardless of whether
        collection_name is explicitly provided.
        """
        # Use an invalid feature_id that will trigger a 400 error
        params = {
            "feature": "Reach",
            "feature_id": "00000000000",  # Invalid feature_id
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-02T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse"
            # No collection_name - uses default
        }

        response, _ = api_client.query(params)

        # We expect a 400 error for invalid feature_id
        assert response.status_code == 400, \
            f"Expected 400 error for invalid feature_id, got {response.status_code}"

        # CORS header MUST be present even on error responses
        assert 'Access-Control-Allow-Origin' in response.headers, \
            "Missing Access-Control-Allow-Origin header on error response. " \
            "This causes browsers to block error messages from being displayed to users."
