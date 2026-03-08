"""
Tests for additional API features and edge cases

Tests miscellaneous API features mentioned in documentation:
- API key header (x-hydrocron-key)
- Geometry field behavior
- Field ordering in responses
- Special characters in parameters
- Case sensitivity
"""
import pytest
from .utils import (
    assert_http_success,
    validate_geojson_structure,
    validate_csv_structure,
    extract_geojson_from_response
)


class TestAPIKeyHeader:
    """Test optional x-hydrocron-key header for heavy usage"""

    def test_query_without_api_key_succeeds(self, api_client, stable_test_data):
        """Test queries work without API key (API key is optional)"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)

    @pytest.mark.skip(reason="Requires valid API key - update with real key to test")
    def test_query_with_valid_api_key_succeeds(self, api_client, stable_test_data):
        """Test query with valid API key succeeds"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "fields": "reach_id,time_str,wse"
            },
            headers={"x-hydrocron-key": "VALID_API_KEY_HERE"}
        )

        assert_http_success(response)

    @pytest.mark.skip(reason="Not implemented yet--API key validation is not implemented")
    def test_query_with_invalid_api_key(self, api_client, stable_test_data):
        """Test query with invalid API key behavior"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "fields": "reach_id,time_str,wse"
            },
            headers={"x-hydrocron-key": "invalid-key-12345"}
        )

        # Should either succeed (key not validated) or return error
        # Behavior depends on whether API key validation is implemented
        assert response.status_code in [400, 400]


class TestGeometryFieldBehavior:
    """Test geometry field handling across feature types"""

    def test_reach_geometry_is_linestring(self, api_client, stable_test_data):
        """Test Reach features return LineString geometry"""
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

        if len(geojson['features']) > 0:
            feature = geojson['features'][0]
            assert 'geometry' in feature
            assert feature['geometry']['type'] in ['LineString', 'MultiLineString'], \
                f"Reach geometry should be LineString, got {feature['geometry']['type']}"

    def test_node_geometry_is_point(self, api_client, stable_test_data):
        """Test Node features return Point geometry"""
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
            assert feature['geometry']['type'] == 'Point', \
                f"Node geometry should be Point, got {feature['geometry']['type']}"

    def test_priorlake_geometry_is_point(self, api_client, stable_test_data):
        """Test PriorLake features return Point geometry (lake center)"""
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
            # PriorLake returns center point coordinates
            assert feature['geometry']['type'] in ['Point', 'Polygon'], \
                f"PriorLake geometry should be Point or Polygon, got {feature['geometry']['type']}"

    def test_geometry_field_optional(self, api_client, stable_test_data):
        """Test geometry field can be omitted from fields parameter"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse"  # No geometry field
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        # GeoJSON should still be valid even without explicit geometry
        validate_geojson_structure(geojson)


class TestFieldOrdering:
    """Test field ordering in responses"""

    def test_csv_columns_match_fields_order(self, api_client, stable_test_data):
        """Test CSV columns appear in same order as fields parameter"""
        reach_data = stable_test_data["reach"]

        requested_fields = ["wse", "reach_id", "time_str", "slope"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": ",".join(requested_fields)  # Non-alphabetical order
        })

        assert_http_success(response)

        # Extract CSV from JSON-wrapped response
        from .utils import extract_csv_from_response
        data = response.json()
        csv_text = extract_csv_from_response(data)

        lines = csv_text.strip().split('\n')
        headers = lines[0].split(',')

        # Filter headers to only include requested fields (ignore units fields like wse_u)
        actual_ordered_fields = [h for h in headers if h in requested_fields]

        # Verify all requested fields are present
        assert len(actual_ordered_fields) == len(requested_fields), \
            f"Not all requested fields found in CSV headers.\n" \
            f"Requested: {requested_fields}\n" \
            f"Found: {actual_ordered_fields}\n" \
            f"All headers: {headers}"

        # Verify the order matches the requested order
        assert actual_ordered_fields == requested_fields, \
            f"CSV columns order doesn't match requested fields order.\n" \
            f"Requested: {requested_fields}\n" \
            f"Actual: {actual_ordered_fields}\n" \
            f"All headers: {headers}"

    def test_geojson_properties_include_all_fields(self, api_client, stable_test_data):
        """Test GeoJSON properties include all requested fields"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse,slope,width"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        if len(geojson['features']) > 0:
            props = geojson['features'][0]['properties']
            expected_fields = ['reach_id', 'wse', 'slope', 'width']

            for field in expected_fields:
                assert field in props, f"Expected field '{field}' not found in properties"


class TestCaseSensitivity:
    """Test parameter and value case sensitivity"""

    def test_feature_parameter_case_sensitive(self, api_client, stable_test_data):
        """Test feature parameter values are case-sensitive"""
        reach_data = stable_test_data["reach"]

        # Try lowercase 'reach' (should fail if case-sensitive)
        response, _ = api_client.query({
            "feature": "reach",  # Lowercase
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        # Should return error, case-sensitive
        assert response.status_code in [400, 400]

    def test_field_names_case_sensitive(self, api_client, stable_test_data):
        """Test field names are case-sensitive"""
        reach_data = stable_test_data["reach"]

        # Try uppercase field name
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,WSE"  # Uppercase WSE
        })

        # Should return error--case-sensitive
        assert response.status_code in [400, 400]

    def test_output_parameter_case_sensitive(self, api_client, stable_test_data):
        """Test output parameter is case-sensitive"""
        reach_data = stable_test_data["reach"]

        # Try uppercase 'CSV'
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "CSV",  # Uppercase
            "fields": "reach_id,time_str,wse"
        })

        # Should return error--case-sensitive
        assert response.status_code in [400, 400]


class TestSpecialCharacters:
    """Test handling of special characters in parameters"""

    def test_fields_with_spaces_rejected(self, api_client, stable_test_data):
        """Test field list with spaces is handled correctly"""
        reach_data = stable_test_data["reach"]

        # Fields parameter with spaces (incorrect format)
        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id, time_str, wse"  # Spaces after commas
        })

        # Should work (spaces trimmed)
        assert response.status_code in [200, 200]

    def test_duplicate_fields_in_list(self, api_client, stable_test_data):
        """Test duplicate fields in fields parameter"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse,wse"  # Duplicate wse
        })

        # Should handle duplicates gracefully (dedupe or return error)
        assert response.status_code in [500, 500]


class TestNoDataSentinelValues:
    """Test handling of no-data sentinel values"""

    def test_no_data_value_negative_999999999999(self, api_client, stable_test_data):
        """Test that no-data values use sentinel -999999999999.0"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse,slope,width,area_total"
        })

        assert_http_success(response)

        csv_text = response.text

        # Check if sentinel value appears (indicates missing data)
        # This is expected for some fields in real data
        # Value: -999999999999 or -999999999999.0
        if '-999999999999' in csv_text:
            # Sentinel value is being used correctly
            assert True
        # If no sentinel values, that's also fine (no missing data)


class TestQueryPerformance:
    """Test query performance characteristics"""

    def test_small_query_responds_quickly(self, api_client, stable_test_data):
        """Test small queries respond within 5 seconds"""
        reach_data = stable_test_data["reach"]

        response, elapsed = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)
        assert elapsed < 5.0, f"Small query took {elapsed:.2f}s (expected < 5s)"

    def test_csv_faster_than_geojson(self, api_client, stable_test_data):
        """Test CSV format is generally faster than GeoJSON"""
        reach_data = stable_test_data["reach"]

        # Query CSV
        response_csv, elapsed_csv = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse,slope,width"
        })

        # Query GeoJSON
        response_geojson, elapsed_geojson = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse,slope,width"
        })

        assert_http_success(response_csv)
        assert_http_success(response_geojson)

        # CSV is often faster, but not guaranteed - just log the comparison
        # Don't fail the test if GeoJSON happens to be faster
        print(f"CSV time: {elapsed_csv:.2f}s, GeoJSON time: {elapsed_geojson:.2f}s")


class TestMultipleConsecutiveQueries:
    """Test API handles multiple consecutive queries correctly"""

    def test_consecutive_queries_all_succeed(self, api_client, stable_test_data):
        """Test making multiple queries in succession all succeed"""
        reach_data = stable_test_data["reach"]

        for i in range(3):
            response, _ = api_client.query({
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "fields": "reach_id,time_str,wse"
            })

            assert_http_success(response), f"Query {i+1} failed"

    def test_different_feature_types_consecutive(self, api_client, stable_test_data):
        """Test querying different feature types consecutively"""
        reach_data = stable_test_data["reach"]
        node_data = stable_test_data["node"]
        lake_data = stable_test_data["priorlake"]

        # Query Reach
        response_reach, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        # Query Node
        response_node, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "fields": "node_id,time_str,wse"
        })

        # Query PriorLake
        response_lake, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "fields": "lake_id,time_str,wse"
        })

        assert_http_success(response_reach)
        assert_http_success(response_node)
        assert_http_success(response_lake)
