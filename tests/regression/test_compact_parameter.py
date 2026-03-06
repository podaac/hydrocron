"""
Comprehensive tests for the compact parameter

The compact parameter controls whether GeoJSON responses are returned in a
compacted format (single feature with arrays) or expanded format (multiple features).

Default behavior:
- Accept: application/geo+json → compact=true (compacted)
- Accept: application/json → compact=false (expanded)
- Can be explicitly overridden with compact parameter
"""
import pytest
from .utils import (
    assert_http_success,
    validate_geojson_structure,
    extract_geojson_from_response
)


class TestCompactParameterBasics:
    """Test basic compact parameter functionality"""

    def test_compact_true_returns_single_feature_with_arrays(self, api_client, stable_test_data):
        """Test compact=true returns single feature with array values"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "compact": "true",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        # Compacted format should have single feature with array values
        assert len(geojson['features']) == 1, "Compact format should have exactly 1 feature"

        feature = geojson['features'][0]
        props = feature['properties']

        # Properties should contain arrays, not single values
        # Check if values are lists (arrays)
        for key, value in props.items():
            if key not in ['reach_id', 'feature_id', 'lake_id', 'node_id']:
                # Time-series fields should be arrays
                if isinstance(value, list):
                    assert len(value) > 0, f"Array field {key} should not be empty"

    def test_compact_false_returns_multiple_features(self, api_client, stable_test_data):
        """Test compact=false returns one feature per observation"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "compact": "false",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        # Expanded format should have multiple features (one per time observation)
        expected_count = reach_data["expected_count"]
        assert len(geojson['features']) == expected_count, \
            f"Expanded format should have {expected_count} features"

        # Each feature should have scalar values, not arrays
        for feature in geojson['features']:
            props = feature['properties']
            for key, value in props.items():
                # In expanded format, values should be scalars, not arrays
                if key == 'time_str' or key == 'wse':
                    assert not isinstance(value, list), \
                        f"Field {key} should be scalar in expanded format, got {type(value)}"


class TestCompactDefaultBehavior:
    """Test default compact behavior based on Accept header"""

    def test_geo_json_accept_header_defaults_to_compact_true(self, api_client, stable_test_data):
        """Test application/geo+json defaults to compact=true"""
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
        # With geo+json Accept header, should default to compact format
        assert 'type' in data
        assert data['type'] == 'FeatureCollection'
        # Should have single feature (compacted)
        assert len(data['features']) == 1

    def test_json_accept_header_defaults_to_compact_false(self, api_client, stable_test_data):
        """Test application/json defaults to compact=false (with wrapper)"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "fields": "reach_id,time_str,wse"
            },
            headers={"Accept": "application/json"}
        )

        assert_http_success(response)

        data = response.json()
        # With json Accept header, should have wrapper
        if 'results' in data:
            geojson = data['results']['geojson']
            # Should be expanded format (multiple features)
            expected_count = reach_data["expected_count"]
            assert len(geojson['features']) == expected_count


class TestCompactOverridesAcceptHeader:
    """Test that compact parameter overrides Accept header defaults"""

    def test_compact_true_overrides_json_accept_header(self, api_client, stable_test_data):
        """Test compact=true works even with application/json Accept header"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "fields": "reach_id,time_str,wse",
                "compact": "true"
            },
            headers={"Accept": "application/json"}
        )

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)

        # Should be compacted despite application/json Accept header
        assert len(geojson['features']) == 1

    def test_compact_false_overrides_geo_json_accept_header(self, api_client, stable_test_data):
        """Test compact=false works even with application/geo+json Accept header"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "fields": "reach_id,time_str,wse",
                "compact": "false"
            },
            headers={"Accept": "application/geo+json"}
        )

        assert_http_success(response)

        data = response.json()
        # Should be expanded despite application/geo+json Accept header
        expected_count = reach_data["expected_count"]
        assert len(data['features']) == expected_count


class TestCompactAllFeatureTypes:
    """Test compact parameter works for all feature types"""

    def test_compact_true_node(self, api_client, stable_test_data):
        """Test compact=true works for Node features"""
        node_data = stable_test_data["node"]

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "compact": "true",
            "fields": "node_id,time_str,wse"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)
        assert len(geojson['features']) == 1

    def test_compact_true_priorlake(self, api_client, stable_test_data):
        """Test compact=true works for PriorLake features"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "compact": "true",
            "fields": "lake_id,time_str,wse"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)
        assert len(geojson['features']) == 1

    def test_compact_false_node(self, api_client, stable_test_data):
        """Test compact=false works for Node features"""
        node_data = stable_test_data["node"]

        response, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "compact": "false",
            "fields": "node_id,time_str,wse"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)
        assert len(geojson['features']) == node_data["expected_count"]

    def test_compact_false_priorlake(self, api_client, stable_test_data):
        """Test compact=false works for PriorLake features"""
        lake_data = stable_test_data["priorlake"]

        response, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "compact": "false",
            "fields": "lake_id,time_str,wse"
        })

        assert_http_success(response)

        data = response.json()
        geojson = extract_geojson_from_response(data)
        assert len(geojson['features']) == lake_data["expected_count"]


class TestCompactWithCSV:
    """Test that compact parameter doesn't affect CSV output"""

    def test_compact_ignored_for_csv_output(self, api_client, stable_test_data):
        """Test compact parameter is ignored for CSV output format"""
        reach_data = stable_test_data["reach"]

        # Test with compact=true
        response_compact_true, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "compact": "true",
            "fields": "reach_id,time_str,wse"
        })

        # Test with compact=false
        response_compact_false, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "compact": "false",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response_compact_true)
        assert_http_success(response_compact_false)

        # CSV output should be identical regardless of compact parameter
        # Both should have same number of rows (one per observation)
        rows_compact_true = len(response_compact_true.text.strip().split('\n')) - 1
        rows_compact_false = len(response_compact_false.text.strip().split('\n')) - 1

        assert rows_compact_true == rows_compact_false == reach_data["expected_count"]
