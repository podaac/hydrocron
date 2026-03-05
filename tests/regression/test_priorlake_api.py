"""
Comprehensive PriorLake feature regression tests

Tests PriorLake feature queries including basic queries, drainage fields,
geometry validation, and collection version handling.
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


class TestPriorLakeBasicQueries:
    """Test basic PriorLake queries"""

    def test_lake_geojson_with_standard_fields(self, api_client, stable_test_data):
        """Test prior lake query with standard fields"""
        lake_data = stable_test_data["priorlake"]

        response, elapsed = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": "lake_id,time_str,wse,area_total,quality_f,PLD_version"
        })

        assert_http_success(response)
        assert_response_time(elapsed, max_seconds=30)
        assert_result_count(response, lake_data["expected_count"], output_format="geojson")

        data = response.json()
        geojson = extract_geojson_from_response(data)
        validate_geojson_structure(geojson)

        # Verify lake-specific fields
        if len(geojson['features']) > 0:
            props = geojson['features'][0]['properties']
            assert 'lake_id' in props
            assert 'wse' in props
            assert 'area_total' in props

    def test_lake_csv_query(self, api_client, stable_test_data):
        """Test prior lake query with CSV output"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": "lake_id,time_str,wse,area_total,quality_f"
        })

        assert_http_success(response)
        assert_result_count(response, lake_data["expected_count"], output_format="csv")
        assert "text/csv" in response.headers.get("Content-Type", "")

        rows = validate_csv_structure(
            response.text,
            expected_fields=["lake_id", "time_str", "wse", "area_total", "quality_f"]
        )

        assert len(rows) == lake_data["expected_count"], \
            f"Expected {lake_data['expected_count']} rows, got {len(rows)}"

    def test_lake_with_geometry(self, api_client, stable_test_data):
        """Test prior lake query includes geometry"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": "lake_id,time_str,wse,geometry"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        if len(geojson['features']) > 0:
            feature = geojson['features'][0]
            assert 'geometry' in feature
            assert feature['geometry'] is not None


class TestPriorLakeDrainageFields:
    """Test PriorLake drainage system fields"""

    def test_lake_with_drainage_fields(self, api_client, stable_test_data):
        """Test prior lake query with drainage system fields (ds1/ds2)"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": "lake_id,time_str,wse,ds1_l,ds1_q,ds2_l,ds2_q"
        })

        # Stable test data should always exist - 404 is a failure
        assert_http_success(response)

    def test_lake_with_all_drainage_fields(self, api_client, stable_test_data):
        """Test prior lake query with all drainage system fields"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": "lake_id,time_str,ds1_l,ds1_l_u,ds1_q,ds1_q_u,ds2_l,ds2_l_u,ds2_q,ds2_q_u"
        })

        # Stable test data should always exist - 404 is a failure
        assert_http_success(response)


class TestPriorLakeQualityFields:
    """Test PriorLake quality and metadata fields"""

    def test_lake_with_quality_fields(self, api_client, stable_test_data):
        """Test prior lake query with quality flags"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": "lake_id,time_str,wse,quality_f,dark_frac,ice_clim_f,ice_dyn_f,partial_f"
        })

        assert_http_success(response)

        rows = validate_csv_structure(
            response.text,
            expected_fields=["lake_id", "quality_f", "dark_frac"]
        )

    def test_lake_with_pld_version(self, api_client, stable_test_data):
        """Test prior lake query includes PLD version"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": "lake_id,time_str,wse,PLD_version"
        })

        assert_http_success(response)
        assert 'PLD_version' in response.text


class TestPriorLakeCollectionVersions:
    """Test PriorLake queries across collection versions"""

    def test_lake_2_0_collection(self, api_client, stable_test_data):
        """Test querying 2.0 collection explicitly"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_LakeSP_2.0",
            "fields": "lake_id,time_str,wse"
        })

        # Stable test data should always exist - 404 is a failure
        assert_http_success(response)

    @pytest.mark.version_d
    def test_lake_d_collection(self, api_client, stable_test_data, test_env):
        """Test querying D collection explicitly"""
        if test_env == "ops":
            pytest.skip("Version D may not be in OPS yet")

        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_LakeSP_D",
            "fields": "lake_id,time_str,wse"
        })

        # Stable test data should always exist - 404 is a failure
        assert_http_success(response)

    def test_default_lake_collection(self, api_client, stable_test_data):
        """Test that default collection is used when not specified"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            # No collection_name specified - should use default
            "fields": "lake_id,time_str,wse"
        })

        assert_http_success(response)


@pytest.mark.golden
class TestPriorLakeGoldenFiles:
    """
    Test PriorLake responses match golden reference files

    These tests validate that API responses haven't changed from known-good outputs.
    If these tests fail, it indicates the API behavior has changed.

    To update reference files after intentional changes:
        HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature priorlake
    """

    def test_lake_basic_geojson_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test basic lake GeoJSON matches reference file"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": "lake_id,time_str,wse,area_total"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            lake_data["fixtures"]["basic_geojson"],
            fixtures_dir,
            output_format="geojson",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )

    def test_lake_basic_csv_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test basic lake CSV matches reference file"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": "lake_id,time_str,wse,area_total,quality_f"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            lake_data["fixtures"]["basic_csv"],
            fixtures_dir,
            output_format="csv",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )

    def test_lake_comprehensive_geojson_matches_reference(self, api_client, stable_test_data, fixtures_dir):
        """Test comprehensive lake GeoJSON matches reference file"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": "lake_id,time_str,wse,area_total,quality_f,PLD_version,geometry"
        })

        assert_http_success(response)
        assert_matches_reference(
            response,
            lake_data["fixtures"]["comprehensive_geojson"],
            fixtures_dir,
            output_format="geojson",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )
