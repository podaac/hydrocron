"""
Reach + node (node_fields) regression tests

Tests requests that return a reach and all its nodes in one call: row layout,
output formats, compact, file download and node_fields validation.
Uses the stable reach data, so node rows come from the same reach and window.
"""
import pytest
from .utils import (
    assert_http_success,
    validate_geojson_structure,
    validate_csv_structure,
    extract_geojson_from_response,
    extract_csv_from_response,
    on_failure_show_curl
)

REACH_KEYS = ["reach", "reach_d"]
ID_COLUMNS = ["feature_type", "reach_id", "node_id"]


def reach_nodes_params(reach_data, **overrides):
    """Build a reach + node request for a stable reach"""
    params = {
        "feature": "Reach",
        "feature_id": reach_data["feature_id"],
        "start_time": reach_data["start_time"],
        "end_time": reach_data["end_time"],
        "collection_name": reach_data["collection_name"],
        "fields": "reach_id,time_str,wse",
        "node_fields": "node_id,time_str,wse"
    }
    params.update(overrides)
    return params


def assert_node_ids_belong_to_reach(node_ids, reach_id):
    """Node IDs start with the reach ID's first 10 digits"""
    assert node_ids, "Expected node rows for the reach"
    for node_id in node_ids:
        assert node_id.startswith(reach_id[:10]), f"Node {node_id} does not belong to reach {reach_id}"


def query_csv_rows(api_client, params, expected_fields=None):
    """Run a CSV request and return (response, rows)"""
    response, _ = api_client.query(params, timeout=30)
    with on_failure_show_curl(response):
        assert_http_success(response)
        rows = validate_csv_structure(extract_csv_from_response(response.json()), expected_fields=expected_fields)
    return response, rows


class TestReachNodesCsv:
    """Test reach + node CSV responses"""

    @pytest.mark.parametrize("reach_key", REACH_KEYS)
    def test_reach_nodes_csv(self, api_client, stable_test_data, reach_key):
        """Reach rows first, then node rows; id columns first; hits = reach + node rows"""
        reach_data = stable_test_data[reach_key]
        reach_id = reach_data["feature_id"]

        response, _ = api_client.query(reach_nodes_params(reach_data, output="csv"), timeout=30)

        with on_failure_show_curl(response):
            assert_http_success(response)
            data = response.json()
            csv_text = extract_csv_from_response(data)
            rows = validate_csv_structure(csv_text, expected_fields=ID_COLUMNS + ["time_str", "wse", "wse_units"])

            assert csv_text.split("\n")[0].split(",")[:3] == ID_COLUMNS, "CSV must start with feature_type,reach_id,node_id"

            reach_rows = [row for row in rows if row["feature_type"] == "Reach"]
            node_rows = [row for row in rows if row["feature_type"] == "Node"]
            assert len(reach_rows) + len(node_rows) == len(rows), "Every row must be a Reach or Node row"
            assert len(reach_rows) == reach_data["expected_count"], \
                f"Expected {reach_data['expected_count']} reach rows, got {len(reach_rows)}"
            assert rows[:len(reach_rows)] == reach_rows, "Reach rows must come before node rows"
            assert data["hits"] == len(rows), f"hits {data['hits']} != {len(rows)} rows"

            assert all(row["reach_id"] == reach_id for row in rows), "Every row must carry the requested reach_id"
            assert all(row["node_id"] == "" for row in reach_rows), "node_id must be blank on reach rows"
            assert_node_ids_belong_to_reach([row["node_id"] for row in node_rows], reach_id)

    @pytest.mark.parametrize("reach_key", REACH_KEYS)
    def test_reach_nodes_time_window_and_order(self, api_client, stable_test_data, reach_key):
        """Node rows fall inside the requested window, sorted by node_id, then time within each node"""
        reach_data = stable_test_data[reach_key]
        params = reach_nodes_params(reach_data, output="csv", node_fields="node_id,time_str,wse,range_start_time")

        response, rows = query_csv_rows(api_client, params, expected_fields=ID_COLUMNS + ["range_start_time"])
        node_rows = [row for row in rows if row["feature_type"] == "Node"]

        with on_failure_show_curl(response):
            assert node_rows, "Expected node rows for the reach"
            for row in node_rows:
                assert params["start_time"] <= row["range_start_time"] <= params["end_time"], \
                    f"Node {row['node_id']} row at {row['range_start_time']} is outside the requested window"

            keys = [(row["node_id"], row["range_start_time"]) for row in node_rows]
            assert keys == sorted(keys), "Node rows must be sorted by node_id, then time"

    @pytest.mark.parametrize("reach_key", REACH_KEYS)
    def test_reach_nodes_match_node_request(self, api_client, stable_test_data, reach_key):
        """An observed node's rows match a feature=Node request for that node"""
        reach_data = stable_test_data[reach_key]
        node_fields = "node_id,time_str,wse,range_start_time"
        params = reach_nodes_params(reach_data, output="csv", node_fields=node_fields)

        _, rows = query_csv_rows(api_client, params)
        node_rows = [row for row in rows if row["feature_type"] == "Node"]
        observed = [row["node_id"] for row in node_rows if row["time_str"] != "no_data"]
        assert observed, "Expected at least one observed node"
        node_id = observed[0]

        response, single_rows = query_csv_rows(api_client, {
            **{k: params[k] for k in ("start_time", "end_time", "collection_name")},
            "feature": "Node",
            "feature_id": node_id,
            "output": "csv",
            "fields": node_fields
        })

        def values(rows_):
            return sorted((row["range_start_time"], row["time_str"], row["wse"]) for row in rows_ if row["node_id"] == node_id)

        with on_failure_show_curl(response):
            assert values(node_rows) == values(single_rows), \
                f"Node {node_id}: reach + node rows differ from the feature=Node request"

    @pytest.mark.version_d
    def test_reach_nodes_default_collection_is_d(self, api_client, stable_test_data):
        """Without collection_name, reach and node rows come from the D collection"""
        reach_data = stable_test_data["reach_d"]
        params = reach_nodes_params(reach_data, output="csv", fields="reach_id,time_str,collection_shortname",
                                    node_fields="node_id,time_str,collection_shortname")
        del params["collection_name"]

        response, rows = query_csv_rows(api_client, params, expected_fields=ID_COLUMNS + ["collection_shortname"])

        with on_failure_show_curl(response):
            assert any(row["feature_type"] == "Node" for row in rows), "Expected node rows for the reach"
            shortnames = {row["collection_shortname"] for row in rows}
            assert shortnames == {"SWOT_L2_HR_RiverSP_D"}, f"Expected only SWOT_L2_HR_RiverSP_D rows, got {shortnames}"

    @pytest.mark.slow
    def test_reach_nodes_worst_case_reach(self, api_client, stable_test_data):
        """Largest known reach, full range: 200 within the time limit, or a clean 413 (data only grows)"""
        if "reach_nodes_worst" not in stable_test_data:
            pytest.skip("No worst-case reach configured for this environment")
        reach_data = stable_test_data["reach_nodes_worst"]

        response, elapsed = api_client.query(reach_nodes_params(reach_data, output="csv"), timeout=35)

        with on_failure_show_curl(response):
            if response.status_code == 413:
                # Node-row limit or 6 MB response limit
                assert "node rows in the requested time range" in response.text or "exceeding the" in response.text, \
                    f"Unexpected 413 message: {response.text[:300]}"
                return
            assert_http_success(response)
            assert elapsed <= reach_data["max_seconds"], \
                f"Worst-case reach took {elapsed:.1f}s, limit {reach_data['max_seconds']}s (API Gateway times out at 29s)"
            rows = validate_csv_structure(extract_csv_from_response(response.json()))
            assert any(row["feature_type"] == "Node" for row in rows), "Expected node rows for the reach"

    def test_reach_nodes_csv_file_download(self, api_client, stable_test_data):
        """csv_file returns an attachment with the reach + nodes default filename"""
        reach_data = stable_test_data["reach_d"]
        params = reach_nodes_params(reach_data, output="csv_file")

        response, _ = api_client.query(params, timeout=30)

        with on_failure_show_curl(response):
            assert_http_success(response)
            expected_name = f"hydrocron_Reach_nodes_{reach_data['feature_id']}_{params['start_time'][:10]}_{params['end_time'][:10]}.csv"
            disposition = response.headers.get("Content-Disposition", "")
            assert expected_name in disposition, f"Expected filename {expected_name}, got '{disposition}'"
            assert response.text.split("\n")[0].startswith(",".join(ID_COLUMNS)), "CSV must start with feature_type,reach_id,node_id"


class TestReachNodesGeojson:
    """Test reach + node GeoJSON responses"""

    @pytest.mark.parametrize("reach_key", REACH_KEYS)
    def test_reach_nodes_geojson(self, api_client, stable_test_data, reach_key):
        """One Feature per row; reaches are lines, nodes are points; all Features share keys"""
        reach_data = stable_test_data[reach_key]

        response, _ = api_client.query(reach_nodes_params(reach_data, output="geojson"), timeout=30)

        with on_failure_show_curl(response):
            assert_http_success(response)
            data = response.json()
            geojson = extract_geojson_from_response(data)
            validate_geojson_structure(geojson)

            features = geojson["features"]
            assert data["hits"] == len(features), f"hits {data['hits']} != {len(features)} Features"

            reach_features = [f for f in features if f["properties"]["feature_type"] == "Reach"]
            node_features = [f for f in features if f["properties"]["feature_type"] == "Node"]
            assert len(reach_features) == reach_data["expected_count"]
            assert node_features, "Expected node Features"

            keys = set(features[0]["properties"])
            assert all(set(f["properties"]) == keys for f in features), "All Features must have the same property keys"
            assert all(f["properties"]["node_id"] is None for f in reach_features), "node_id must be null on reach Features"
            assert all(f["geometry"]["type"] == "Point" for f in node_features), "Node geometry must be a Point"
            assert all(f["geometry"]["type"] != "Point" for f in reach_features), "Reach geometry must not be a Point"
            assert_node_ids_belong_to_reach([f["properties"]["node_id"] for f in node_features], reach_data["feature_id"])

    @pytest.mark.parametrize("reach_key", REACH_KEYS)
    def test_reach_nodes_compact(self, api_client, stable_test_data, reach_key):
        """geo+json defaults to compact: one Feature for the reach, one per node"""
        reach_data = stable_test_data[reach_key]

        response, _ = api_client.query(
            reach_nodes_params(reach_data),
            timeout=30,
            headers={"Accept": "application/geo+json"}
        )

        with on_failure_show_curl(response):
            assert_http_success(response)
            geojson = extract_geojson_from_response(response.json())
            validate_geojson_structure(geojson)

            feature_types = [f["properties"]["feature_type"] for f in geojson["features"]]
            assert all(isinstance(value, list) and len(set(value)) == 1 for value in feature_types), \
                "Compact properties must be arrays, one feature_type per Feature"
            assert [value[0] for value in feature_types].count("Reach") == 1, "Expected exactly one compact reach Feature"

            node_ids = [f["properties"]["node_id"][0] for f in geojson["features"] if f["properties"]["feature_type"][0] == "Node"]
            assert len(node_ids) == len(set(node_ids)), "Expected one compact Feature per node"
            assert_node_ids_belong_to_reach(node_ids, reach_data["feature_id"])


class TestReachNodesValidation:
    """Test node_fields validation errors"""

    @pytest.mark.parametrize("overrides, message", [
        ({"feature": "Node", "feature_id": "18180900090011"}, "node_fields parameter is only valid when feature=Reach"),
        ({"node_fields": ""}, "node_fields parameter should contain valid SWOT node fields"),
        ({"node_fields": "node_id,not_a_field"}, "node_fields parameter should contain valid SWOT node fields"),
        ({"node_fields": "node_id,wse_sm"}, "node_fields parameter should contain valid SWOT node fields"),
    ], ids=["feature_node", "empty", "invalid_field", "version_d_field_on_2_0"])
    def test_node_fields_rejected(self, api_client, stable_test_data, overrides, message):
        """Invalid node_fields requests return 400 with a clear message"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(reach_nodes_params(reach_data, output="csv", **overrides))

        with on_failure_show_curl(response):
            assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text[:300]}"
            assert message in response.text

    @pytest.mark.version_d
    def test_version_d_node_field_accepted_for_d(self, api_client, stable_test_data):
        """wse_sm is a valid node field for the D collection"""
        reach_data = stable_test_data["reach_d"]

        response, _ = api_client.query(reach_nodes_params(reach_data, output="csv", node_fields="node_id,wse_sm"), timeout=30)

        with on_failure_show_curl(response):
            assert_http_success(response)
            csv_text = extract_csv_from_response(response.json())
            validate_csv_structure(csv_text, expected_fields=ID_COLUMNS + ["wse_sm"])
