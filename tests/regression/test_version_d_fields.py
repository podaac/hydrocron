"""
Tests for Version D specific fields

These tests verify new fields added in Version D collections:
- Node: wse_sm, wse_sm_u, wse_sm_q, wse_sm_q_b (smoothed WSE fields)
- PriorLake: qual_f_b (quality flag boolean)

Run these tests before promoting UAT to OPS to ensure Version D features work correctly.
"""
import pytest
from .utils import assert_http_success, assert_http_error, validate_csv_structure


@pytest.mark.version_d
class TestNodeWSESmoothedFields:
    """Test Node wse_sm smoothed fields in Version D"""

    @pytest.mark.uat_only
    def test_wse_sm_fields_accessible(self, api_client, test_env):
        """Test all wse_sm fields are accessible"""
        if test_env != "uat":
            pytest.skip("Version D fields being tested in UAT first")

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": "31241400580011",
            "start_time": "2026-02-01T00:00:00Z",
            "end_time": "2026-02-28T00:00:00Z",
            "output": "csv",
            "collection_name": "SWOT_L2_HR_RiverSP_D",
            "fields": "node_id,time_str,wse,wse_sm,wse_sm_u,wse_sm_q,wse_sm_q_b"
        })

        assert_http_success(response)

        rows = validate_csv_structure(
            response.text,
            expected_fields=["node_id", "wse_sm", "wse_sm_u", "wse_sm_q", "wse_sm_q_b"]
        )

        assert len(rows) > 0, "Should return data rows"

    def test_wse_sm_only_valid_for_node(self, api_client, stable_test_data):
        """Test wse_sm fields are only valid for Node feature type"""
        # Should work for Node with stable test data
        node_data = stable_test_data["node"]
        response_node, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_RiverSP_D",
            "fields": "node_id,time_str,wse_sm"
        })

        # Stable test data should always exist - field is valid for Node
        assert_http_success(response_node)

        # Should NOT work for Reach - field validation should fail
        response_reach, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "99999999999",
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-12-31T23:59:59Z",
            "output": "csv",
            "fields": "reach_id,time_str,wse_sm"
        })

        assert_http_error(response_reach)

        # Should NOT work for PriorLake - field validation should fail
        response_lake, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": "99999999999",
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-12-31T23:59:59Z",
            "output": "csv",
            "fields": "lake_id,time_str,wse_sm"
        })

        assert_http_error(response_lake)

    def test_wse_sm_not_available_in_2_0(self, api_client):
        """Test wse_sm fields are not available in 2.0 collection"""
        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": "31241400580011",
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-12-31T23:59:59Z",
            "output": "csv",
            "collection_name": "SWOT_L2_HR_RiverSP_2.0",
            "fields": "node_id,time_str,wse_sm"
        })

        # Should return field validation error
        assert_http_error(response)
        assert "field" in response.text.lower() or "invalid" in response.text.lower()


@pytest.mark.version_d
class TestPriorLakeQualFbField:
    """Test PriorLake qual_f_b field in Version D"""

    @pytest.mark.uat_only
    def test_qual_f_b_accessible(self, api_client, test_env):
        """Test qual_f_b field is accessible for PriorLake"""
        if test_env != "uat":
            pytest.skip("Version D fields being tested in UAT first")

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": "9120274662",
            "start_time": "2024-06-22T00:00:00Z",
            "end_time": "2024-07-13T23:59:59Z",
            "output": "csv",
            "collection_name": "SWOT_L2_HR_LakeSP_D",
            "fields": "lake_id,time_str,wse,area_total,quality_f,qual_f_b"
        })

        assert_http_success(response)

        rows = validate_csv_structure(
            response.text,
            expected_fields=["lake_id", "qual_f_b"]
        )

        assert len(rows) > 0, "Should return data rows"

    def test_qual_f_b_only_valid_for_priorlake(self, api_client, stable_test_data):
        """Test qual_f_b field is only valid for PriorLake feature type"""
        # Should work for PriorLake with stable test data
        lake_data = stable_test_data["priorlake"]
        response_lake, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_LakeSP_D",
            "fields": "lake_id,time_str,qual_f_b"
        })

        # Stable test data should always exist - field is valid for PriorLake
        assert_http_success(response_lake)

        # Should NOT work for Reach - field validation should fail
        response_reach, _ = api_client.query({
            "feature": "Reach",
            "feature_id": "99999999999",
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-12-31T23:59:59Z",
            "output": "csv",
            "fields": "reach_id,time_str,qual_f_b"
        })

        assert_http_error(response_reach)

        # Should NOT work for Node - field validation should fail
        response_node, _ = api_client.query({
            "feature": "Node",
            "feature_id": "99999999999",
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-12-31T23:59:59Z",
            "output": "csv",
            "fields": "node_id,time_str,qual_f_b"
        })

        assert_http_error(response_node)

    def test_qual_f_b_not_available_in_2_0(self, api_client):
        """Test qual_f_b field is not available in 2.0 collection"""
        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": "9120274662",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-12-31T23:59:59Z",
            "output": "csv",
            "collection_name": "SWOT_L2_HR_LakeSP_2.0",
            "fields": "lake_id,time_str,qual_f_b"
        })

        # Should return field validation error
        assert_http_error(response)
        assert "field" in response.text.lower() or "invalid" in response.text.lower()


@pytest.mark.version_d
class TestVersionDBackwardCompatibility:
    """Test backward compatibility of Version D collections"""

    def test_old_queries_still_work_node(self, api_client):
        """Test queries without new Version D fields still work for Node"""
        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": "31241400580011",
            "start_time": "2026-02-01T00:00:00Z",
            "end_time": "2026-02-28T00:00:00Z",
            "output": "csv",
            "collection_name": "SWOT_L2_HR_RiverSP_D",
            "fields": "node_id,time_str,wse,width"  # No new fields
        })

        assert_http_success(response)

    def test_old_queries_still_work_priorlake(self, api_client):
        """Test queries without new Version D fields still work for PriorLake"""
        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": "9120274662",
            "start_time": "2024-06-22T00:00:00Z",
            "end_time": "2024-07-13T23:59:59Z",
            "output": "csv",
            "collection_name": "SWOT_L2_HR_LakeSP_D",
            "fields": "lake_id,time_str,wse,area_total"  # No qual_f_b
        })

        assert_http_success(response)

    def test_can_query_both_versions(self, api_client, stable_test_data):
        """Test can query both 2.0 and D versions of same feature"""
        node_data = stable_test_data["node"]

        # Query D version with stable test data
        response_d, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_RiverSP_D",
            "fields": "node_id,time_str,wse"
        })

        # Stable test data should always exist in D collection
        assert_http_success(response_d)

        # Query 2.0 version with stable reach data (as Node may not have 2.0 data)
        reach_data = stable_test_data["reach"]
        response_2_0, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_RiverSP_2.0",
            "fields": "reach_id,time_str,wse"
        })

        # Stable test data should always exist in 2.0 collection
        assert_http_success(response_2_0)
