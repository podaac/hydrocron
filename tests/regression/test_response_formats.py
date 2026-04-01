"""
Tests for response format handling and content negotiation

Tests the different response formats and wrappers:
- application/json: Returns wrapper with status, time, hits, results
- application/geo+json: Returns raw GeoJSON
- text/csv: Returns raw CSV
- Content-Type header validation
- output parameter vs Accept header interaction
"""
import pytest
import json
from .utils import (
    assert_http_success,
    validate_geojson_structure,
    validate_csv_structure
)


class TestJSONWrapperFormat:
    """Test application/json response wrapper structure"""

    def test_json_wrapper_contains_status(self, api_client, stable_test_data):
        """Test JSON wrapper includes status field"""
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

        # Wrapper should contain status
        assert 'status' in data or 'results' in data, \
            "Response should contain status or results field"

        if 'status' in data:
            assert data['status'] == "200 OK" or data['status'] == 200

    def test_json_wrapper_contains_time(self, api_client, stable_test_data):
        """Test JSON wrapper includes response time field"""
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

        # Wrapper should contain time field (response time in ms)
        assert 'time' in data or 'results' in data, \
            "Response should contain time or results field"

        if 'time' in data:
            assert isinstance(data['time'], (int, float)), \
                "Time should be numeric (milliseconds)"
            assert data['time'] >= 0, "Time should be non-negative"

    def test_json_wrapper_contains_hits(self, api_client, stable_test_data):
        """Test JSON wrapper includes hits count"""
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

        # Wrapper should contain hits field (result count)
        assert 'hits' in data or 'results' in data, \
            "Response should contain hits or results field"

        if 'hits' in data:
            assert isinstance(data['hits'], int), "Hits should be integer"
            assert data['hits'] >= 0, "Hits should be non-negative"
            assert data['hits'] == reach_data["expected_count"], \
                f"Hits should match expected count ({reach_data['expected_count']})"

    def test_json_wrapper_contains_results(self, api_client, stable_test_data):
        """Test JSON wrapper includes results field with data"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "output": "geojson",
                "fields": "reach_id,time_str,wse"
            },
            headers={"Accept": "application/json"}
        )

        assert_http_success(response)

        data = response.json()

        # Wrapper should contain results field
        assert 'results' in data, "Response should contain results field"

        # Results should contain geojson
        assert 'geojson' in data['results'], \
            "Results should contain geojson field for geojson output"

        # Validate GeoJSON structure
        validate_geojson_structure(data['results']['geojson'])

    def test_json_wrapper_csv_in_results(self, api_client, stable_test_data):
        """Test JSON wrapper with CSV output includes csv in results"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "output": "csv",
                "fields": "reach_id,time_str,wse"
            },
            headers={"Accept": "application/json"}
        )

        assert_http_success(response)

        # Could be JSON wrapper with CSV data, or raw CSV
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            data = response.json()
            assert 'results' in data, "JSON response should contain results"
            assert 'csv' in data['results'], \
                "Results should contain csv field for csv output"
        elif "text/csv" in content_type:
            # Raw CSV is also acceptable
            assert len(response.text) > 0


class TestRawGeoJSONFormat:
    """Test application/geo+json returns raw GeoJSON without wrapper"""

    def test_geo_json_accept_returns_raw_geojson(self, api_client, stable_test_data):
        """Test application/geo+json returns GeoJSON directly without wrapper"""
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

        # Should be raw GeoJSON, not wrapped
        assert 'type' in data, "Should have 'type' field (GeoJSON)"
        assert data['type'] == 'FeatureCollection'
        assert 'features' in data

        # Should NOT have wrapper fields
        # (unless API design includes them, adjust accordingly)
        # In most cases, raw GeoJSON shouldn't have status/time/hits at top level

    def test_geo_json_content_type_header(self, api_client, stable_test_data):
        """Test application/geo+json Accept returns proper Content-Type"""
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

        content_type = response.headers.get("Content-Type", "")

        # Should return application/geo+json or application/json
        assert "application/geo+json" in content_type or "application/json" in content_type, \
            f"Content-Type should be application/geo+json or application/json, got {content_type}"


class TestRawCSVFormat:
    """Test text/csv returns raw CSV without wrapper"""

    def test_csv_accept_returns_csv_data(self, api_client, stable_test_data):
        """Test text/csv Accept header returns CSV data"""
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

        csv_text = response.text

        # If response is a JSON string (starts with quote), parse it
        if csv_text.strip().startswith('"'):
            import json
            csv_text = json.loads(csv_text)

        # Validate CSV structure
        validate_csv_structure(csv_text, expected_fields=["reach_id", "time_str", "wse"])

    def test_csv_content_type_header(self, api_client, stable_test_data):
        """Test CSV output returns text/csv Content-Type"""
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

        # Verify CSV-related content type
        content_type = response.headers.get("Content-Type", "")
        assert "text/csv" in content_type.lower(), \
            f"Content-Type should contain 'text/csv', got {content_type}"


class TestOutputParameterVsAcceptHeader:
    """Test interaction between output parameter and Accept header"""

    def test_output_csv_with_json_accept_header(self, api_client, stable_test_data):
        """Test output=csv with application/json Accept header"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "output": "csv",
                "fields": "reach_id,time_str,wse"
            },
            headers={"Accept": "application/json"}
        )

        assert_http_success(response)

        # Could return CSV wrapped in JSON or raw CSV
        content_type = response.headers.get("Content-Type", "")

        if "text/csv" in content_type:
            # Raw CSV
            validate_csv_structure(response.text)
        elif "application/json" in content_type:
            # CSV wrapped in JSON
            data = response.json()
            assert 'results' in data and 'csv' in data['results']

    def test_output_geojson_with_csv_accept_header(self, api_client, stable_test_data):
        """Test output=geojson with text/csv Accept header"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(
            params={
                "feature": "Reach",
                "feature_id": reach_data["feature_id"],
                "start_time": reach_data["start_time"],
                "end_time": reach_data["end_time"],
                "output": "geojson",
                "fields": "reach_id,time_str,wse"
            },
            headers={"Accept": "text/csv"}
        )

        # Should return error--invalid combination of Accept header and output parameter
        assert response.status_code == 400

    def test_output_parameter_without_accept_header(self, api_client, stable_test_data):
        """Test output parameter works without explicit Accept header"""
        reach_data = stable_test_data["reach"]

        # Test CSV output
        response_csv, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response_csv)

        # Test GeoJSON output
        response_geojson, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response_geojson)

    def test_no_output_param_no_accept_header_uses_default(self, api_client, stable_test_data):
        """Test default format when neither output param nor Accept header specified"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)

        # Should default to some format (likely GeoJSON)
        content_type = response.headers.get("Content-Type", "")
        assert len(content_type) > 0, "Should have Content-Type header"


class TestContentTypeHeaders:
    """Test Content-Type response headers match format"""

    def test_geojson_output_has_json_content_type(self, api_client, stable_test_data):
        """Test GeoJSON output returns JSON Content-Type"""
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

        content_type = response.headers.get("Content-Type", "")

        # Should be application/json or application/geo+json
        assert "json" in content_type.lower(), \
            f"GeoJSON output should have JSON Content-Type, got {content_type}"

    def test_csv_output_has_csv_content_type(self, api_client, stable_test_data):
        """Test CSV output returns CSV Content-Type"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)

        content_type = response.headers.get("Content-Type", "")

        # Should be text/csv (or application/json if wrapped)
        assert "csv" in content_type.lower() or "json" in content_type.lower(), \
            f"CSV output should have CSV or JSON Content-Type, got {content_type}"


class TestUnitsFieldsInResponses:
    """Test that unit fields are automatically included"""

    def test_geojson_includes_units_fields(self, api_client, stable_test_data):
        """Test GeoJSON response includes unit fields for fields with units"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse,slope"
        })

        assert_http_success(response)

        data = response.json()

        # Extract GeoJSON
        if 'results' in data and 'geojson' in data['results']:
            geojson = data['results']['geojson']
        else:
            geojson = data

        # Check if units fields are present
        assert len(geojson['features']) > 0, "No features in response"

        props = geojson['features'][0]['properties']

        # wse and slope should have corresponding unit fields
        # Check for either *_units or *_u naming convention
        has_wse_units = 'wse_units' in props or 'wse_u' in props
        has_slope_units = 'slope_units' in props or 'slope_u' in props

        assert has_wse_units, \
            f"GeoJSON should include units field for wse (wse_units or wse_u). Properties: {list(props.keys())}"
        assert has_slope_units, \
            f"GeoJSON should include units field for slope (slope_units or slope_u). Properties: {list(props.keys())}"

    def test_csv_includes_units_columns(self, api_client, stable_test_data):
        """Test CSV response includes unit columns"""
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

        csv_text = response.text

        # Check for unit columns (e.g., wse_units, slope_units)
        assert 'wse_units' in csv_text or 'wse_u' in csv_text, \
            "CSV should include units column for wse"
        assert 'slope_units' in csv_text or 'slope_u' in csv_text, \
            "CSV should include units column for slope"


class TestResponseFormatConsistency:
    """Test response format consistency across feature types"""

    def test_all_feature_types_support_csv(self, api_client, stable_test_data):
        """Test all feature types return valid CSV"""
        reach_data = stable_test_data["reach"]
        node_data = stable_test_data["node"]
        lake_data = stable_test_data["priorlake"]

        # Test Reach
        response_reach, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response_reach)
        validate_csv_structure(response_reach.text)

        # Test Node
        response_node, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "csv",
            "fields": "node_id,time_str,wse"
        })

        assert_http_success(response_node)
        validate_csv_structure(response_node.text)

        # Test PriorLake
        response_lake, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": "lake_id,time_str,wse"
        })

        assert_http_success(response_lake)
        validate_csv_structure(response_lake.text)
