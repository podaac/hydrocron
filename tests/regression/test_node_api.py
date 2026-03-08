"""
Comprehensive Node API regression tests

Tests Node feature queries including Version D specific fields
"""
import pytest
from .utils import (
    assert_http_success,
    assert_http_error,
    validate_geojson_structure,
    validate_csv_structure,
    assert_response_time,
    extract_geojson_from_response,
    assert_matches_reference,
    assert_result_count
)


class TestNodeBasicQueries:
    """Test basic node queries"""

    def test_node_geojson_query(self, api_client, stable_test_data):
        """Test node query with GeoJSON output"""
        node_data = stable_test_data["node"]

        response, elapsed = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "fields": node_data["fields"]
        })

        assert_http_success(response)
        assert_response_time(elapsed, max_seconds=2)
        assert_result_count(response, node_data["expected_count"], output_format="geojson")

        data = response.json()
        geojson = extract_geojson_from_response(data)
        validate_geojson_structure(geojson)

        # Verify node-specific properties
        if len(geojson['features']) > 0:
            feature = geojson['features'][0]
            assert 'node_id' in feature['properties']
            assert 'wse' in feature['properties']

    def test_node_csv_query(self, api_client, stable_test_data):
        """Test node query with CSV output"""
        node_data = stable_test_data["node"]

        response, elapsed = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "csv",
            "fields": "node_id,time_str,wse,width,lat,lon"
        })

        assert_http_success(response)
        assert_response_time(elapsed, max_seconds=30)
        assert_result_count(response, node_data["expected_count"], output_format="csv")

        # Validate CSV structure
        rows = validate_csv_structure(
            response.text,
            expected_fields=["node_id", "time_str", "wse", "width", "lat", "lon"]
        )

        assert len(rows) == node_data["expected_count"], \
            f"Expected {node_data['expected_count']} rows, got {len(rows)}"

    def test_node_with_geometry(self, api_client, stable_test_data):
        """Test node query includes geometry"""
        node_data = stable_test_data["node"]

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "fields": "node_id,time_str,wse,geometry"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        if len(geojson['features']) > 0:
            feature = geojson['features'][0]
            assert 'geometry' in feature
            assert feature['geometry'] is not None
            assert 'type' in feature['geometry']

    def test_default_node_collection(self, api_client, stable_test_data):
        """Test default collection_shortname is SWOT_L2_HR_RiverSP_2.0 when not specified"""
        node_data = stable_test_data["node"]

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "fields": "node_id,time_str,wse,collection_shortname"
            # Note: No collection_name parameter - should default to 2.0
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        # Verify default collection is 2.0
        if len(geojson['features']) > 0:
            props = geojson['features'][0]['properties']
            assert 'collection_shortname' in props, "collection_shortname not found in properties"
            assert props['collection_shortname'] == 'SWOT_L2_HR_RiverSP_2.0', \
                f"Expected default collection 'SWOT_L2_HR_RiverSP_2.0', got '{props['collection_shortname']}'"

@pytest.mark.version_d
class TestNodeVersionDFields:
    """Test Version D specific node fields (wse_sm, etc.)"""

    def test_node_wse_sm_fields_available(self, api_client, test_env):
        """Test wse_sm smoothed fields are accessible in Version D"""
        # Skip if not in UAT (Version D might not be in OPS yet)
        if test_env == "ops":
            pytest.skip("Version D fields may not be available in OPS yet")

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

        # Verify wse_sm fields are in response
        assert 'wse_sm' in response.text
        assert 'wse_sm_u' in response.text
        assert 'wse_sm_q' in response.text
        assert 'wse_sm_q_b' in response.text

    def test_node_wse_sm_fields_in_geojson(self, api_client, test_env):
        """Test wse_sm fields appear in GeoJSON output"""
        if test_env == "ops":
            pytest.skip("Version D fields may not be available in OPS yet")

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": "31241400580011",
            "start_time": "2026-02-01T00:00:00Z",
            "end_time": "2026-02-28T00:00:00Z",
            "output": "geojson",
            "collection_name": "SWOT_L2_HR_RiverSP_D",
            "fields": "node_id,time_str,wse_sm,wse_sm_u"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        if len(geojson['features']) > 0:
            props = geojson['features'][0]['properties']
            assert 'wse_sm' in props
            assert 'wse_sm_u' in props

    def test_node_backward_compatibility(self, api_client):
        """Test queries without new Version D fields still work"""
        # Old-style query without Version D fields should work
        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": "31241400580011",
            "start_time": "2026-02-01T00:00:00Z",
            "end_time": "2026-02-28T00:00:00Z",
            "output": "csv",
            "fields": "node_id,time_str,wse,width"  # No wse_sm fields
        })

        assert_http_success(response)

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


class TestNodePerformance:
    """Test node query performance"""

    def test_response_time_acceptable(self, api_client, stable_test_data):
        """Test node query responds within acceptable time"""
        node_data = stable_test_data["node"]

        response, elapsed = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "csv",
            "fields": "node_id,time_str,wse"
        })

        assert_http_success(response)
        assert_response_time(elapsed, max_seconds=30)

    @pytest.mark.slow
    def test_large_time_range_performs_acceptably(self, api_client):
        """Test query with large time range"""
        response, elapsed = api_client.query({
            "feature": "Node",
            "feature_id": "31241400580011",
            "start_time": "2026-01-01T00:00:00Z",
            "end_time": "2026-12-31T23:59:59Z",  # Full year
            "output": "csv",
            "fields": "node_id,time_str,wse"
        }, timeout=60)

        assert_http_success(response)
        assert elapsed < 60, f"Large query took {elapsed:.2f}s (expected < 60s)"


@pytest.mark.golden
class TestNodeGoldenFiles:
    """
    Test node responses match golden reference files

    These tests validate that API responses haven't changed from known-good outputs.
    If these tests fail, it indicates the API behavior has changed.

    To update reference files after intentional changes:
        HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature node
    """

    def test_node_basic_geojson_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test basic node GeoJSON matches reference file"""
        node_data = stable_test_data["node"]

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "fields": "node_id,time_str,wse,lat,lon"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            node_data["fixtures"]["basic_geojson"],
            fixtures_dir,
            output_format="geojson",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )

    def test_node_basic_csv_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test basic node CSV matches reference file"""
        node_data = stable_test_data["node"]

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "csv",
            "fields": "node_id,time_str,wse,width,lat,lon"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            node_data["fixtures"]["basic_csv"],
            fixtures_dir,
            output_format="csv",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )

    def test_node_comprehensive_geojson_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test comprehensive node GeoJSON matches reference file"""
        node_data = stable_test_data["node"]

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "fields": "node_id,time_str,wse,width,lat,lon,geometry"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            node_data["fixtures"]["comprehensive_geojson"],
            fixtures_dir,
            output_format="geojson",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )
