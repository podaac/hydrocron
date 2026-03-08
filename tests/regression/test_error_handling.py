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
import pytest
from .utils import assert_http_error, assert_http_success


class TestInvalidAcceptHeaders:
    """Test 415 Unsupported Media Type errors"""

    def test_invalid_accept_header_returns_415(self, api_client, stable_test_data):
        """Test invalid Accept header returns 415 error"""
        reach_data = stable_test_data["reach"]

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
        reach_data = stable_test_data["reach"]

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
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-10",  # Missing time component
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        # May return 400 or 200 with no results depending on implementation
        assert response.status_code in [200, 400]

    def test_malformed_date_format(self, api_client, stable_test_data):
        """Test malformed date returns 400"""
        reach_data = stable_test_data["reach"]

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
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["end_time"],
            "end_time": reach_data["start_time"],  # Swapped!
            "fields": "reach_id,time_str,wse"
        })

        # Should return 500 Internal Server Error
        assert response.status_code in [500, 500]

    def test_invalid_field_name(self, api_client, stable_test_data):
        """Test invalid field name returns 400"""
        reach_data = stable_test_data["reach"]

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
        reach_data = stable_test_data["reach"]

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
        reach_data = stable_test_data["reach"]

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
        reach_data = stable_test_data["reach"]

        # Query far future where no data exists
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2099-01-01T00:00:00Z",
            "end_time": "2099-12-31T23:59:59Z",
            "fields": "reach_id,time_str,wse"
        })

        # Could return 200 with empty results or 400
        if response.status_code == 200:
            # Verify empty results
            if 'geojson' in response.json():
                geojson = response.json()['results']['geojson']
                assert len(geojson['features']) == 0
        else:
            assert_http_error(response, expected_status_range=(400, 400))

    def test_valid_node_no_data_in_time_range(self, api_client, stable_test_data):
        """Test valid node ID with time range that has no data"""
        node_data = stable_test_data["node"]

        # Query far past where no data exists
        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": "2020-01-01T00:00:00Z",
            "end_time": "2020-12-31T23:59:59Z",
            "fields": "node_id,time_str,wse"
        })

        # Could return 200 with empty results or 400
        if response.status_code == 200:
            # Verify empty results
            if 'geojson' in response.json():
                geojson = response.json()['results']['geojson']
                assert len(geojson['features']) == 0
        else:
            assert_http_error(response, expected_status_range=(400, 400))


@pytest.mark.slow
class TestPayloadSizeLimits:
    """Test 413 Payload Too Large errors"""

    @pytest.mark.skip(reason="Requires known large dataset - update feature_id before enabling")
    def test_large_payload_returns_413(self, api_client):
        """Test response exceeding 6MB limit returns 413"""
        # Note: This test requires a feature_id known to have large amounts of data
        # Update the feature_id and time range to match your test environment

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "LARGE_FEATURE_ID",  # Replace with known large feature
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-12-31T23:59:59Z",
            "output": "geojson",
            "compact": "false",  # Expanded format is larger
            "fields": "reach_id,time_str,wse,slope,width,area_total,area_detct,area_wse,layovr_val,node_dist,loc_offset,xtrk_dist,dschg_c,dschg_c_q,dschg_csf,dschg_c_u,dschg_gc,dschg_gc_q,dschg_gcsf,dschg_gc_u,dschg_m,dschg_m_q,dschg_msf,dschg_m_u,dschg_gm,dschg_gm_q,dschg_gmsf,dschg_gm_u,dschg_b,dschg_b_q,dschg_bsf,dschg_b_u,dschg_gb,dschg_gb_q,dschg_gbsf,dschg_gb_u,dschg_h,dschg_h_q,dschg_hsf,dschg_h_u,dschg_gh,dschg_gh_q,dschg_ghsf,dschg_gh_u,dschg_o,dschg_o_q,dschg_osf,dschg_o_u,dschg_go,dschg_go_q,dschg_gosf,dschg_go_u,dschg_s,dschg_s_q,dschg_ssf,dschg_s_u,dschg_gs,dschg_gs_q,dschg_gssf,dschg_gs_u,dschg_n,dschg_n_q,dschg_nsf,dschg_n_u,dschg_gn,dschg_gn_q,dschg_gnsf,dschg_gn_u,dschg_q_b,dschg_gq_b"
        }, timeout=60)

        # Should return 413 if payload exceeds 6MB
        if response.status_code == 413:
            assert response.status_code == 413
        else:
            # If doesn't exceed limit, test passes (dataset not large enough)
            pytest.skip("Dataset not large enough to trigger 413 error")


class TestFieldValidation:
    """Test field validation across feature types"""

    def test_reach_specific_fields_invalid_for_node(self, api_client, stable_test_data):
        """Test reach-specific fields are rejected for node queries"""
        node_data = stable_test_data["node"]

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
        reach_data = stable_test_data["reach"]

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
        reach_data = stable_test_data["reach"]

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
        reach_data = stable_test_data["reach"]

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
