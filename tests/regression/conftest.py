"""
Configuration for regression tests
"""
import os
import pytest
import requests
import time


# Environment URLs
API_URLS = {
    "uat": "https://soto.podaac.uat.earthdatacloud.nasa.gov/hydrocron/v1/timeseries",
    "ops": "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries",
}

# Known stable test data - feature IDs that MUST exist in both UAT and OPS
# These are used for regression testing and should always return data (200 OK)
# If any stable test returns 404, it indicates a deployment or data ingestion problem
# Update these if the feature IDs don't exist in your deployment
#
# Reference files ("golden" responses) are stored in fixtures/ directory
# Tests compare live API responses against these references to detect regressions
# Use capture_reference_files.py to generate/update reference files
STABLE_TEST_DATA = {
    "reach": {
        "feature_id": "34296500851",
        "start_time": "2024-02-10T00:00:00Z",
        "end_time": "2024-05-03T00:00:00Z",
        "expected_count": 6,  # Number of results expected for this query
        "fields": "reach_id,time_str,wse,slope,width,sword_version",
        "fixtures": {
            "basic_geojson": "reach/reach_basic.geojson",
            "basic_csv": "reach/reach_basic.csv",
            "discharge_csv": "reach/reach_discharge.csv",
            "comprehensive_geojson": "reach/reach_comprehensive.geojson"
        }
    },
    "node": {
        "feature_id": "81292900150551",
        "start_time": "2024-02-06T00:00:00Z",
        "end_time": "2024-02-26T00:00:00Z",
        "expected_count": 4,  # Number of results expected for this query
        "fields": "node_id,time_str,wse,width,lat,lon",
        "fixtures": {
            "basic_geojson": "node/node_basic.geojson",
            "basic_csv": "node/node_basic.csv",
            "wse_sm_csv": "node/node_wse_sm.csv",
            "comprehensive_geojson": "node/node_comprehensive.geojson"
        }
    },
    "priorlake": {
        "feature_id": "8223592002",
        "start_time": "2024-08-16T00:00:00Z",
        "end_time": "2024-08-25T23:59:59Z",
        "expected_count": 3,  # Number of results expected for this query
        "fields": "lake_id,time_str,wse,area_total,quality_f",
        "fixtures": {
            "basic_geojson": "priorlake/lake_basic.geojson",
            "basic_csv": "priorlake/lake_basic.csv",
            "qual_f_b_csv": "priorlake/lake_qual_f_b.csv",
            "comprehensive_geojson": "priorlake/lake_comprehensive.geojson"
        }
    },
    "node_d": {
        "feature_id": "33129600450223",  # Update with Version D node_id
        "start_time": "2025-06-04T00:00:00Z",  # Update with actual date range
        "end_time": "2025-06-05T00:00:00Z",
        "expected_count": 5,  # Update with actual count
        "collection_name": "SWOT_L2_HR_RiverSP_D",
        "fields": "node_id,time_str,wse,wse_sm,wse_sm_u,wse_sm_q,wse_sm_q_b",
        "fixtures": {
            "basic_geojson": "node/node_d_basic.geojson",
            "basic_csv": "node/node_d_basic.csv",
            "wse_sm_csv": "node/node_d_wse_sm.csv",
            "comprehensive_geojson": "node/node_d_comprehensive.geojson"
        }
    },
    "priorlake_d": {
        "feature_id": "8121554212",  # Update with Version D lake_id
        "start_time": "2024-06-22T00:00:00Z",  # Update with actual date range
        "end_time": "2025-07-13T23:59:59Z",
        "expected_count": 1,  # Update with actual count
        "collection_name": "SWOT_L2_HR_LakeSP_D",
        "fields": "lake_id,time_str,wse,area_total,quality_f,qual_f_b",
        "fixtures": {
            "basic_geojson": "priorlake/lake_d_basic.geojson",
            "basic_csv": "priorlake/lake_d_basic.csv",
            "qual_f_b_csv": "priorlake/lake_d_qual_f_b.csv",
            "comprehensive_geojson": "priorlake/lake_d_comprehensive.geojson"
        }
    }
}


@pytest.fixture(scope="session")
def api_url():
    """
    Get the API URL to test against based on HYDROCRON_ENV environment variable.

    Set HYDROCRON_ENV to 'uat' or 'ops' before running tests.
    If not set, tests will be skipped.
    """
    env = os.environ.get("HYDROCRON_ENV", "").lower()

    if env not in API_URLS:
        pytest.skip(f"HYDROCRON_ENV not set or invalid. Set to 'uat' or 'ops' to run regression tests. Current value: '{env}'")

    return API_URLS[env]


@pytest.fixture(scope="session")
def test_env():
    """
    Get the test environment name
    """
    return os.environ.get("HYDROCRON_ENV", "").lower()


@pytest.fixture
def api_client(api_url):
    """
    API client with common configuration and helper methods
    """
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'hydrocron-regression-tests/1.0'
            })

        def query(self, params, timeout=30, headers=None):
            """
            Make API request with timing

            Returns: (response, elapsed_time)
            """
            start = time.time()

            if headers:
                response = self.session.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )
            else:
                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=timeout
                )

            elapsed = time.time() - start
            return response, elapsed

    return APIClient(api_url)


@pytest.fixture
def stable_test_data():
    """
    Known stable test data for regression tests
    """
    return STABLE_TEST_DATA


@pytest.fixture
def fixtures_dir():
    """
    Get the fixtures directory path
    """
    import pathlib
    return pathlib.Path(__file__).parent / "fixtures"


# Pytest markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "smoke: Quick smoke tests (run after every deployment)")
    config.addinivalue_line("markers", "slow: Slow tests that take > 10 seconds")
    config.addinivalue_line("markers", "version_d: Tests for Version D specific features")
    config.addinivalue_line("markers", "uat_only: Tests that only run in UAT environment")
    config.addinivalue_line("markers", "golden: Tests that compare against golden reference files")
