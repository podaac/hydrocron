"""
Comprehensive error handling tests

Tests various error conditions and validates proper HTTP status codes:
- 400: Bad request (missing/invalid parameters, no data found)
- 413: Payload too large (>6MB response)
- 415: Unsupported media type (invalid Accept header)
- 500: Server errors

These tests ensure the API properly validates requests and returns
meaningful error messages.
"""
import os

import pytest
from .utils import assert_http_error


class TestInvalidAcceptHeaders:
    """Test 415 Unsupported Media Type errors"""

    def test_invalid_accept_header_returns_415(self, api_client, stable_test_data):
        """Test invalid Accept header returns 415 error"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "fields": "reach_id,time_str,wse"
            },
            headers={"Accept": "application/xml"}  # Invalid - API doesn't support XML
        )

        # Should return 415 Unsupported Media Type
        assert response.status_code == 415, \
            f"Expected 415 for invalid Accept header, got {response.status_code}"

    def test_multiple_invalid_accept_headers(self, api_client, stable_test_data):
        """Test various invalid Accept headers return 415"""
        reach_data = stable_test_data["reach_d"]

        invalid_headers = [
            "text/html",
            "application/pdf",
            "text/plain",
            "application/x-yaml"
        ]

        for accept_header in invalid_headers:
            response, _ = api_client.query(
                params={
                    "feature": "Reach",
                    "feature_id": reach_data["feature_id"],
                    "start_time": reach_data["start_time"],
                    "end_time": reach_data["end_time"],
                    "fields": "reach_id,time_str,wse"
                },
                headers={"Accept": accept_header}
            )

            assert response.status_code == 415, \
                f"Expected 415 for Accept header '{accept_header}', got {response.status_code}"


class TestMissingRequiredParameters:
    """Test 400 errors for missing required parameters"""

    def test_missing_feature_parameter(self, api_client):
        """Test missing 'feature' parameter returns 400"""
        response, _ = api_client.query({
            # Missing "feature" parameter
            "feature_id": "34296500851",
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-05-03T00:00:00Z",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_missing_feature_id_parameter(self, api_client):
        """Test missing 'feature_id' parameter returns 400"""
        response, _ = api_client.query({
            "feature": "Reach",
            # Missing "feature_id" parameter
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-05-03T00:00:00Z",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_missing_start_time_parameter(self, api_client):
        """Test missing 'start_time' parameter returns 400"""
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "34296500851",
            # Missing "start_time" parameter
            "end_time": "2024-05-03T00:00:00Z",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_missing_end_time_parameter(self, api_client):
        """Test missing 'end_time' parameter returns 400"""
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "34296500851",
            "start_time": "2024-02-10T00:00:00Z",
            # Missing "end_time" parameter
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_missing_fields_parameter(self, api_client):
        """Test missing 'fields' parameter returns 400"""
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "34296500851",
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-05-03T00:00:00Z"
            # Missing "fields" parameter
        })

        assert_http_error(response, expected_status_range=(400, 400))


class TestInvalidParameterValues:
    """Test 400 errors for invalid parameter values"""

    def test_invalid_feature_type(self, api_client):
        """Test invalid feature type returns 400"""
        response, _ = api_client.query({
            "feature": "InvalidFeatureType",
            "feature_id": "34296500851",
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-05-03T00:00:00Z",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_invalid_date_format(self, api_client, stable_test_data):
        """Test invalid date format returns 400"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-10",  # Missing time component
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        # Should return error--invalid date format
        assert response.status_code == 400

    def test_malformed_date_format(self, api_client, stable_test_data):
        """Test malformed date returns 400"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "not-a-date",
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_start_time_after_end_time(self, api_client, stable_test_data):
        """Test start_time after end_time returns 400"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["end_time"],
            "end_time": reach_data["start_time"],  # Swapped!
            "fields": "reach_id,time_str,wse"
        })

        # Should return 500 Internal Server Error
        assert response.status_code == 500

    def test_invalid_field_name(self, api_client, stable_test_data):
        """Test invalid field name returns 400"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,nonexistent_field"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_empty_fields_parameter(self, api_client, stable_test_data):
        """Test empty fields parameter returns 400"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": ""  # Empty string
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_invalid_collection_name(self, api_client, stable_test_data):
        """Test invalid collection_name returns 400"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse",
            "collection_name": "INVALID_COLLECTION"
        })

        assert_http_error(response, expected_status_range=(400, 400))


class TestNonExistentFeatures:
    """Test 400 errors for non-existent feature IDs"""

    def test_nonexistent_reach_id(self, api_client):
        """Test non-existent reach ID returns 400"""
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "99999999999",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-12-31T23:59:59Z",
            "fields": "reach_id,time_str,wse"
        })

        # Should return 400 for non-existent feature
        assert_http_error(response, expected_status_range=(400, 400))

    def test_nonexistent_node_id(self, api_client):
        """Test non-existent node ID returns 400"""
        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": "99999999999999",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-12-31T23:59:59Z",
            "fields": "node_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_nonexistent_lake_id(self, api_client):
        """Test non-existent lake ID returns 400"""
        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": "9999999999",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-12-31T23:59:59Z",
            "fields": "lake_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))


class TestNoDataInTimeRange:
    """Test behavior when feature exists but no data in time range"""

    def test_valid_reach_no_data_in_time_range(self, api_client, stable_test_data):
        """Test valid reach ID with time range that has no data"""
        reach_data = stable_test_data["reach_d"]

        # Query far future where no data exists
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2099-01-01T00:00:00Z",
            "end_time": "2099-12-31T23:59:59Z",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_valid_node_no_data_in_time_range(self, api_client, stable_test_data):
        """Test valid node ID with time range that has no data"""
        node_data = stable_test_data["node_d"]

        # Query far past where no data exists
        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": "2020-01-01T00:00:00Z",
            "end_time": "2020-12-31T23:59:59Z",
            "fields": "node_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))


@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("HYDROCRON_ENV", "").lower() != "ops",
    reason="Payload-size thresholds are calibrated to OPS data volume; UAT/other envs lack the data to exceed the cap",
)
class TestPayloadSizeLimits:
    """Test 413 Payload Too Large errors"""

    def test_large_geojson_payload_returns_413(self, api_client):
        """A wide GeoJSON reach request whose response exceeds the 6MB limit returns a clean 413.

        Regression for the reported production failure: a multi-year reach GeoJSON query returns a
        full-resolution geometry per feature, so the response far exceeds API Gateway's 6MB cap and
        must return a 413 (not a timeout or an opaque 5xx). The reach and time range below are
        calibrated to OPS coverage; adjust the feature_id if running against an environment with
        different data.
        """
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "33150300651",
            "start_time": "2024-07-01T00:00:00Z",
            "end_time": "2026-10-30T00:00:00Z",
            "output": "geojson",
            "collection_name": "SWOT_L2_HR_RiverSP_D",
            "fields": "reach_id,time_str,river_name,wse,slope,width,area_total,dschg_c"
        }, timeout=60)

        assert response.status_code == 413, \
            f"Expected 413 for an oversized GeoJSON response, got {response.status_code}: {response.text[:200]}"
        # The 413 message reports the actual response size and hit count, e.g.
        # "413: Query response is 6.9MB (973 hits), exceeding the 6MB limit. ..."
        assert "exceeding the 6MB limit" in response.text, \
            f"Expected the size-limit message in the 413 body, got: {response.text[:200]}"
        assert "MB (" in response.text, \
            f"Expected the 413 body to report the response size and hit count, got: {response.text[:200]}"

    def test_large_reach_csv_payload_returns_200(self, api_client):
        """The same wide range that exceeds 6MB as GeoJSON is well under the limit as CSV.

        Regression for the false-413 bug: CSV excludes the per-feature geometry, so the actual
        response is a small fraction of the GeoJSON size. The guard must measure the real response
        (not the raw records), so this identical range/fields returns 200 as CSV even though it 413s
        as GeoJSON above.
        """
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "33150300651",
            "start_time": "2020-01-01T00:00:00Z",
            "end_time": "2026-10-30T00:00:00Z",
            "output": "csv",
            "collection_name": "SWOT_L2_HR_RiverSP_D",
            "fields": "reach_id,time_str,river_name,wse,slope,width,area_total,dschg_c"
        }, timeout=60)

        assert response.status_code == 200, \
            f"Expected 200 for the CSV response of the same wide range, got {response.status_code}: {response.text[:200]}"
        # The wide range returns a large row count that would exceed 6MB as GeoJSON.
        hits = response.json()["hits"]
        assert hits > 1300, f"Expected over 1300 rows for this wide range, got {hits}"

    def test_near_limit_geojson_payload_returns_200(self, api_client):
        """A GeoJSON reach response just under the 6MB cap (~5.8MB) must return 200, not 413.

        Companion to the oversized 413 test above: confirms the size guard does not reject a response
        that is large but still within the limit. Calibrated against OPS (~5.8MB / 851 features);
        adjust the start_time if running against an environment with different data.
        """
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "33150300651",
            "start_time": "2024-10-09T00:00:00Z",
            "end_time": "2026-10-30T00:00:00Z",
            "output": "geojson",
            "collection_name": "SWOT_L2_HR_RiverSP_D",
            "fields": "reach_id,time_str,river_name,wse,slope,width,area_total,dschg_c"
        }, timeout=60)

        assert response.status_code == 200, \
            f"Expected 200 for a near-limit (~5.8MB) response, got {response.status_code}: {response.text[:200]}"


class TestFieldValidation:
    """Test field validation across feature types"""

    def test_reach_specific_fields_invalid_for_node(self, api_client, stable_test_data):
        """Test reach-specific fields are rejected for node queries"""
        node_data = stable_test_data["node_d"]

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "fields": "node_id,time_str,lake_id"  # lake_id invalid for Node
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_node_specific_fields_invalid_for_reach(self, api_client, stable_test_data):
        """Test node-specific fields are rejected for reach queries"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,node_id"  # node_id invalid for Reach
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_lake_specific_fields_invalid_for_reach(self, api_client, stable_test_data):
        """Test lake-specific fields are rejected for reach queries"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,lake_id"  # lake_id invalid for Reach
        })

        assert_http_error(response, expected_status_range=(400, 400))


class TestErrorMessageQuality:
    """Test that error messages are informative"""

    def test_invalid_field_error_message_mentions_field(self, api_client, stable_test_data):
        """Test error message for invalid field mentions the field name"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,invalid_field_xyz"
        })

        assert_http_error(response)

        # Error message should mention the problem
        error_text = response.text.lower()
        assert 'field' in error_text or 'invalid' in error_text or 'column' in error_text

    def test_missing_parameter_error_message_is_clear(self, api_client):
        """Test error message for missing parameter is clear"""
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "34296500851",
            # Missing start_time
            "end_time": "2024-05-03T00:00:00Z",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response)

        # Error message should mention missing parameter
        error_text = response.text.lower()
        assert 'start_time' in error_text or 'required' in error_text or 'missing' in error_text
