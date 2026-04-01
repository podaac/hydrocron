"""
Comprehensive PriorLake feature regression tests

Tests PriorLake feature queries including basic queries, drainage fields,
geometry validation, and collection version handling.
"""
import pytest
from .utils import (
    assert_http_success,
    assert_http_error,
    validate_geojson_structure,
    validate_csv_structure,
    extract_geojson_from_response,
    extract_csv_from_response,
    assert_response_time,
    assert_matches_reference,
    assert_result_count
)


class TestPriorLakeBasicQueries:
    """Test basic PriorLake queries"""

    @pytest.mark.parametrize("lake_key", ["priorlake", "priorlake_d"])
    def test_lake_geojson_with_standard_fields(self, api_client, stable_test_data, lake_key):
        """Test prior lake query with standard fields"""
        lake_data = stable_test_data[lake_key]

        params = {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": lake_data["fields"]
        }

        # Add collection_name if present (for Version D)
        if "collection_name" in lake_data:
            params["collection_name"] = lake_data["collection_name"]

        # Warm-up call to handle cold starts / cache warming
        api_client.query(params)

        # Actual timed test
        response, elapsed = api_client.query(params)

        assert_http_success(response)
        assert_response_time(elapsed, max_seconds=2)
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

    @pytest.mark.parametrize("lake_key", ["priorlake", "priorlake_d"])
    def test_lake_csv_query(self, api_client, stable_test_data, lake_key):
        """Test prior lake query with CSV output"""
        lake_data = stable_test_data[lake_key]

        params = {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": lake_data["fields"]
        }

        # Add collection_name if present (for Version D)
        if "collection_name" in lake_data:
            params["collection_name"] = lake_data["collection_name"]

        response, elapsed = api_client.query(params)

        assert_http_success(response)
        assert_response_time(elapsed, max_seconds=2)
        assert_result_count(response, lake_data["expected_count"], output_format="csv")

        # Extract and validate CSV structure
        data = response.json()
        csv_text = extract_csv_from_response(data)
        fields_list = [f.strip() for f in lake_data["fields"].split(",")]
        validate_csv_structure(csv_text, expected_fields=fields_list)

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

    def test_default_lake_collection(self, api_client, stable_test_data):
        """Test default collection_shortname is SWOT_L2_HR_LakeSP_2.0 when not specified"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": "lake_id,time_str,wse,collection_shortname"
            # Note: No collection_name parameter - should default to 2.0
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        # Verify default collection is 2.0
        if len(geojson['features']) > 0:
            props = geojson['features'][0]['properties']
            assert 'collection_shortname' in props, "collection_shortname not found in properties"
            assert props['collection_shortname'] == 'SWOT_L2_HR_LakeSP_2.0', \
                f"Expected default collection 'SWOT_L2_HR_LakeSP_2.0', got '{props['collection_shortname']}'"


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

        # Extract CSV from JSON-wrapped response
        data = response.json()
        csv_text = extract_csv_from_response(data)

        rows = validate_csv_structure(
            csv_text,
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
        assert_result_count(response, lake_data["expected_count"], output_format="csv")

    @pytest.mark.version_d
    def test_lake_d_collection(self, api_client, stable_test_data, test_env):
        """Test querying D collection explicitly"""

        lake_data = stable_test_data["priorlake_d"]

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
        assert_result_count(response, lake_data["expected_count"], output_format="csv")

    def test_default_lake_collection_csv(self, api_client, stable_test_data):
        """Test that default collection is SWOT_L2_HR_LakeSP_2.0 when collection_name not specified"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            # No collection_name specified - should use default 2.0
            "fields": "lake_id,time_str,wse,collection_shortname"
        })

        assert_http_success(response)

        # Extract CSV from JSON-wrapped response
        data = response.json()
        csv_text = extract_csv_from_response(data)

        # Verify default collection is 2.0
        rows = validate_csv_structure(
            csv_text,
            expected_fields=["lake_id", "collection_shortname"]
        )

        assert len(rows) > 0, "Should return at least one row"
        assert rows[0]['collection_shortname'] == 'SWOT_L2_HR_LakeSP_2.0', \
            f"Expected default collection 'SWOT_L2_HR_LakeSP_2.0', got '{rows[0]['collection_shortname']}'"


@pytest.mark.version_d
class TestPriorLakeVersionDFields:
    """Test Version D specific PriorLake fields (qual_f_b, etc.)"""

    def test_qual_f_b_accessible(self, api_client, test_env, stable_test_data):
        """Test qual_f_b field is accessible for PriorLake"""

        lake_data = stable_test_data["priorlake_d"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "collection_name": lake_data["collection_name"],
            "fields": lake_data["fields"]
        })

        assert_http_success(response)

        # Extract and validate CSV structure
        data = response.json()
        csv_text = extract_csv_from_response(data)
        rows = validate_csv_structure(
            csv_text,
            expected_fields=["lake_id", "qual_f_b"]
        )

        assert len(rows) > 0, "Should return data rows"

    def test_qual_f_b_only_valid_for_priorlake(self, api_client, stable_test_data):
        """Test qual_f_b field is only valid for PriorLake feature type"""
        # Should work for PriorLake with stable test data
        lake_data = stable_test_data["priorlake_d"]
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

    def test_qual_f_b_not_available_in_2_0(self, api_client, stable_test_data):
        """Test qual_f_b field is not available in 2.0 collection"""
        lake_data = stable_test_data["priorlake"]  # Use 2.0 lake data

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_LakeSP_2.0",
            "fields": "lake_id,time_str,qual_f_b"  # qual_f_b not valid for 2.0
        })

        # Should return field validation error
        assert_http_error(response)

    def test_priorlake_backward_compatibility(self, api_client, stable_test_data):
        """Test queries without new Version D fields still work for PriorLake"""
        lake_data = stable_test_data["priorlake_d"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "collection_name": "SWOT_L2_HR_LakeSP_D",
            "fields": "lake_id,time_str,wse,area_total"  # No qual_f_b
        })

        assert_http_success(response)
        assert_result_count(response, lake_data["expected_count"], output_format="csv")


@pytest.mark.golden
class TestPriorLakeGoldenFiles:
    """
    Test PriorLake responses match golden reference files

    These tests validate that API responses haven't changed from known-good outputs.
    If these tests fail, it indicates the API behavior has changed.

    To update reference files after intentional changes:
        HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature priorlake
    """

    @pytest.mark.parametrize("lake_key", ["priorlake", "priorlake_d"])
    def test_lake_basic_geojson_matches_reference(self, api_client, stable_test_data, fixtures_dir, lake_key):
        """Test basic lake GeoJSON matches reference file"""
        lake_data = stable_test_data[lake_key]

        params = {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": lake_data["fields"]
        }

        if "collection_name" in lake_data:
            params["collection_name"] = lake_data["collection_name"]

        response, _ = api_client.query(params)

        assert_http_success(response)
        assert_matches_reference(
            response,
            lake_data["fixtures"]["basic_geojson"],
            fixtures_dir,
            output_format="geojson",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )

    @pytest.mark.parametrize("lake_key", ["priorlake", "priorlake_d"])
    def test_lake_basic_csv_matches_reference(self, api_client, stable_test_data, fixtures_dir, lake_key):
        """Test basic lake CSV matches reference file"""
        lake_data = stable_test_data[lake_key]

        params = {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": lake_data["fields"]
        }

        if "collection_name" in lake_data:
            params["collection_name"] = lake_data["collection_name"]

        response, _ = api_client.query(params)

        assert_http_success(response)
        assert_matches_reference(
            response,
            lake_data["fixtures"]["basic_csv"],
            fixtures_dir,
            output_format="csv",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )

    @pytest.mark.parametrize("lake_key", ["priorlake", "priorlake_d"])
    def test_lake_comprehensive_geojson_matches_reference(self, api_client, stable_test_data, fixtures_dir, lake_key):
        """Test comprehensive lake GeoJSON matches reference file"""
        lake_data = stable_test_data[lake_key]

        params = {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": f"{lake_data['fields']},PLD_version,collection_shortname,crid,geometry"
        }

        if "collection_name" in lake_data:
            params["collection_name"] = lake_data["collection_name"]

        response, _ = api_client.query(params)

        assert_http_success(response)
        assert_matches_reference(
            response,
            lake_data["fixtures"]["comprehensive_geojson"],
            fixtures_dir,
            output_format="geojson",
            ignore_fields=['ingest_time', 'crid', 'granuleUR']
        )
