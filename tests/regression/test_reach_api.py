"""
Comprehensive Reach feature regression tests

Tests Reach feature queries including basic queries, field validation,
output formats, and collection version handling.
"""
import pytest
from .utils import (
    assert_http_success,
    validate_geojson_structure,
    validate_csv_structure,
    extract_geojson_from_response,
    assert_response_time,
    assert_matches_reference,
    assert_result_count
)


class TestReachBasicQueries:
    """Test basic reach queries"""

    def test_reach_geojson_with_all_standard_fields(self, api_client, stable_test_data):
        """Test reach query with comprehensive field list"""
        reach_data = stable_test_data["reach"]

        response, elapsed = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse,slope,width,area_total,sword_version,collection_shortname,crid,geometry"
        })

        assert_http_success(response)
        assert_response_time(elapsed, max_seconds=30)
        assert_result_count(response, reach_data["expected_count"], output_format="geojson")

        data = response.json()
        geojson = extract_geojson_from_response(data)
        validate_geojson_structure(geojson)

        # Verify comprehensive field presence
        if len(geojson['features']) > 0:
            props = geojson['features'][0]['properties']
            expected_fields = ['reach_id', 'wse', 'slope', 'width', 'area_total', 'sword_version']
            for field in expected_fields:
                assert field in props, f"Expected field '{field}' not found in properties"

    def test_reach_csv_basic(self, api_client, stable_test_data):
        """Test basic reach CSV query"""
        reach_data = stable_test_data["reach"]

        response, elapsed = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)
        assert_response_time(elapsed, max_seconds=30)
        assert_result_count(response, reach_data["expected_count"], output_format="csv")
        assert "text/csv" in response.headers.get("Content-Type", "")

        rows = validate_csv_structure(
            response.text,
            expected_fields=["reach_id", "time_str", "wse"]
        )

        assert len(rows) == reach_data["expected_count"], \
            f"Expected {reach_data['expected_count']} rows, got {len(rows)}"

    def test_reach_with_geometry_field(self, api_client, stable_test_data):
        """Test reach query explicitly includes geometry"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse,geometry"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        # Verify geometry exists and is valid
        if len(geojson['features']) > 0:
            feature = geojson['features'][0]
            assert 'geometry' in feature
            assert feature['geometry'] is not None
            assert 'type' in feature['geometry']
            assert 'coordinates' in feature['geometry']


class TestReachDischargeFields:
    """Test reach discharge field queries"""

    def test_reach_csv_with_discharge_fields(self, api_client, stable_test_data):
        """Test reach query with discharge fields"""
        reach_data = stable_test_data["reach"]

        response, elapsed = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse,dschg_c,dschg_c_u,dschg_c_q"
        })

        assert_http_success(response)

        rows = validate_csv_structure(
            response.text,
            expected_fields=["reach_id", "dschg_c", "dschg_c_u", "dschg_c_q"]
        )

        assert len(rows) > 0, "Should return data rows"

    def test_reach_with_multiple_discharge_algorithms(self, api_client, stable_test_data):
        """Test reach query with multiple discharge algorithm fields"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,dschg_c,dschg_m,dschg_b,dschg_h"
        })

        assert_http_success(response)

        # Verify all discharge algorithms present
        assert 'dschg_c' in response.text  # Consensus
        assert 'dschg_m' in response.text  # MetroMan
        assert 'dschg_b' in response.text  # BAM
        assert 'dschg_h' in response.text  # HiVDI


class TestReachContentNegotiation:
    """Test Accept header content negotiation for reach queries"""

    def test_reach_accept_header_geojson(self, api_client, stable_test_data):
        """Test reach query using Accept header for GeoJSON"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "fields": "reach_id,time_str,wse"
            },
            headers={"Accept": "application/geo+json"}
        )

        assert_http_success(response)

        data = response.json()
        # Should return GeoJSON based on Accept header
        assert 'type' in data or ('results' in data and 'geojson' in data['results'])

    def test_reach_accept_header_csv(self, api_client, stable_test_data):
        """Test reach query using Accept header for CSV"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "fields": "reach_id,time_str,wse"
            },
            headers={"Accept": "text/csv"}
        )

        assert_http_success(response)
        assert "text/csv" in response.headers.get("Content-Type", "")


class TestReachUnitsFields:
    """Test reach unit field handling"""

    def test_reach_with_units(self, api_client, stable_test_data):
        """Test reach query returns unit fields"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse,slope"
        })

        assert_http_success(response)

        # Units fields should be automatically added
        assert 'wse_units' in response.text
        assert 'slope_units' in response.text


class TestReachCollectionVersions:
    """Test reach queries across collection versions"""

    def test_reach_2_0_collection(self, api_client, stable_test_data):
        """Test querying 2.0 collection explicitly"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_RiverSP_2.0",
            "fields": "reach_id,time_str,wse"
        })

        # Stable test data should always exist - 404 is a failure
        assert_http_success(response)

    @pytest.mark.version_d
    def test_reach_d_collection(self, api_client, stable_test_data, test_env):
        """Test querying D collection explicitly"""
        if test_env == "ops":
            pytest.skip("Version D may not be in OPS yet")

        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_RiverSP_D",
            "fields": "reach_id,time_str,wse"
        })

        # Stable test data should always exist - 404 is a failure
        assert_http_success(response)

    def test_default_collection_used_when_not_specified(self, api_client, stable_test_data):
        """Test that default collection is used when collection_name not specified"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            # No collection_name specified - should use default
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)


@pytest.mark.golden
class TestReachGoldenFiles:
    """
    Test reach responses match golden reference files

    These tests validate that API responses haven't changed from known-good outputs.
    If these tests fail, it indicates the API behavior has changed.

    To update reference files after intentional changes:
        HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature reach
    """

    def test_reach_basic_geojson_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test basic reach GeoJSON matches reference file"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            reach_data["fixtures"]["basic_geojson"],
            fixtures_dir,
            output_format="geojson",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )

    def test_reach_basic_csv_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test basic reach CSV matches reference file"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse,slope,width"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            reach_data["fixtures"]["basic_csv"],
            fixtures_dir,
            output_format="csv",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )

    def test_reach_discharge_csv_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test reach discharge fields CSV matches reference file"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse,dschg_c,dschg_c_u,dschg_c_q"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            reach_data["fixtures"]["discharge_csv"],
            fixtures_dir,
            output_format="csv",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )

    def test_reach_comprehensive_geojson_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test comprehensive reach GeoJSON matches reference file"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse,slope,width,area_total,sword_version,collection_shortname,crid,geometry"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            reach_data["fixtures"]["comprehensive_geojson"],
            fixtures_dir,
            output_format="geojson",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )
