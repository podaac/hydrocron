"""
Retired Version 2.0 data regression tests (1.12.0)

2.0 node and lake data are retired: requests return HTTP 410 with {"error": "410: ..."} naming the
collection to use. 2.0 reaches stay, but serve only REACH_2_0_FIELDS (SoS discharge, IDs, time,
SWORD fields); other known reach fields return 410. Proves the API Gateway ^410 mapping (else HTTP 200).
"""
import pytest

from hydrocron.utils.constants import REACH_2_0_FIELDS
from .utils import assert_http_success, extract_csv_from_response, validate_csv_structure, on_failure_show_curl

RIVER_D_HINT = "Use collection_name=SWOT_L2_HR_RiverSP_D"
RETIRED_FIELDS_HINT = f"Version 2.0 reaches serve only SoS discharge, ID, time and SWORD fields. {RIVER_D_HINT}"


def query_params(test_data, feature, fields, **overrides):
    """Build a request for a stable feature"""
    params = {
        "feature": feature,
        "feature_id": test_data["feature_id"],
        "start_time": test_data["start_time"],
        "end_time": test_data["end_time"],
        "output": "csv",
        "collection_name": test_data["collection_name"],
        "fields": fields
    }
    params.update(overrides)
    return params


def assert_gone(response, message):
    """HTTP 410, the exact error message, and the CORS header"""
    with on_failure_show_curl(response):
        assert response.status_code == 410, f"Expected 410, got {response.status_code}: {response.text[:300]}"
        assert response.json() == {"error": message}
        assert "Access-Control-Allow-Origin" in response.headers, "Missing Access-Control-Allow-Origin header"


class TestRetiredCollections:
    """2.0 node and lake requests return 410 (feature=Node on 2.0: smoke test in test_smoke.py)"""

    def test_node_sub_collection_2_0_returns_410(self, api_client, stable_test_data):
        """The 2.0 node sub-collection name"""
        response, _ = api_client.query(query_params(stable_test_data["node"], "Node", "node_id,time_str,wse",
                                                    collection_name="SWOT_L2_HR_RiverSP_node_2.0"))

        assert_gone(response, f"410: Node data for SWOT_L2_HR_RiverSP_node_2.0 has been retired from Hydrocron. {RIVER_D_HINT}")

    @pytest.mark.parametrize("output", ["csv", "geojson"])
    def test_lake_2_0_returns_410(self, api_client, stable_test_data, output):
        """The 2.0 lake collection, either output"""
        response, _ = api_client.query(query_params(stable_test_data["priorlake"], "PriorLake", "lake_id,time_str,wse", output=output))

        assert_gone(response, "410: PriorLake data for SWOT_L2_HR_LakeSP_2.0 has been retired from Hydrocron. "
                              "Use collection_name=SWOT_L2_HR_LakeSP_D")

    def test_node_fields_on_2_0_returns_410(self, api_client, stable_test_data):
        """node_fields (reach + nodes) on a 2.0 reach"""
        response, _ = api_client.query(query_params(stable_test_data["reach"], "Reach", "reach_id,time_str",
                                                    node_fields="node_id,time_str"))

        assert_gone(response, f"410: Node data for SWOT_L2_HR_RiverSP_2.0 has been retired from Hydrocron. {RIVER_D_HINT}")


class TestReach2_0Fields:
    """2.0 reaches serve only REACH_2_0_FIELDS (dropped field -> 410: smoke test in test_smoke.py)"""

    def test_unknown_and_dropped_fields_return_400(self, api_client, stable_test_data):
        """An unknown field wins: the usual 400"""
        response, _ = api_client.query(query_params(stable_test_data["reach"], "Reach", "reach_id,wse,not_a_field"))

        with on_failure_show_curl(response):
            assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text[:300]}"

    def test_all_allowlist_fields_served(self, api_client, stable_test_data):
        """Every REACH_2_0_FIELDS field returns 200, and no dropped field comes back"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query(query_params(reach_data, "Reach", ",".join(REACH_2_0_FIELDS)), timeout=30)

        with on_failure_show_curl(response):
            assert_http_success(response)
            rows = validate_csv_structure(extract_csv_from_response(response.json()), expected_fields=REACH_2_0_FIELDS)
            assert len(rows) == reach_data["expected_count"]
            served = {column[:-len("_units")] if column.endswith("_units") else column for column in rows[0]}
            assert served <= set(REACH_2_0_FIELDS), f"Dropped fields returned: {sorted(served - set(REACH_2_0_FIELDS))}"
