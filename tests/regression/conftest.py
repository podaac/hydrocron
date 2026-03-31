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

# Known stable test data - feature IDs are for OPS only
# These are used for regression testing and should always return data (200 OK)
# If any stable test returns 404, it indicates a deployment or data ingestion problem
# Update these if the feature IDs don't exist in your deployment
#
# Reference files ("golden" responses) are stored in fixtures/ directory
# Tests compare live API responses against these references to detect regressions
# Use capture_reference_files.py to generate/update reference files
STABLE_TEST_DATA_OPS = {
    "reach": {
        "feature_id": "18180900091",
        "start_time": "2024-02-02T00:00:00Z",
        "end_time": "2024-03-20T00:00:00Z",
        "expected_count": 5,
        "collection_name": "SWOT_L2_HR_RiverSP_2.0",
        "fields": "reach_id,time_str,wse,slope,width,sword_version",
        "fixtures": {
            "basic_geojson": "reach/reach_basic.geojson",
            "basic_csv": "reach/reach_basic.csv",
            "discharge_csv": "reach/reach_discharge.csv",
            "comprehensive_geojson": "reach/reach_comprehensive.geojson"
        }
    },
    "reach_d": {
        "feature_id": "18180900091",
        "start_time": "2024-01-12T00:00:00Z",
        "end_time": "2024-02-03T00:00:00Z",
        "expected_count": 3,
        "collection_name": "SWOT_L2_HR_RiverSP_D",
        "fields": "reach_id,time_str,wse,slope,width,sword_version",
        "fixtures": {
            "basic_geojson": "reach/reach_d_basic.geojson",
            "basic_csv": "reach/reach_d_basic.csv",
            "discharge_csv": "reach/reach_d_discharge.csv",
            "comprehensive_geojson": "reach/reach_d_comprehensive.geojson"
        }
    },
    "node": {
        "feature_id": "45311101670065",
        "start_time": "2023-09-17T00:00:00Z",
        "end_time": "2023-10-30T00:00:00Z",
        "expected_count": 5,
        "collection_name": "SWOT_L2_HR_RiverSP_2.0",
        "fields": "node_id,time_str,wse,width,lat,lon,sword_version",
        "fixtures": {
            "basic_geojson": "node/node_basic.geojson",
            "basic_csv": "node/node_basic.csv",
            "comprehensive_geojson": "node/node_comprehensive.geojson"
        }
    },
    "node_d": {
        "feature_id": "44404000150591",
        "start_time": "2024-01-02T00:00:00Z",
        "end_time": "2024-02-10T00:00:00Z",
        "expected_count": 4,
        "collection_name": "SWOT_L2_HR_RiverSP_D",
        "fields": "node_id,time_str,wse,width,lat,lon,sword_version",
#        "fields": "node_id,time_str,wse,width,wse_sm,wse_sm_u,wse_sm_q,wse_sm_q_b,lat,lon,sword_version",
        "fixtures": {
            "basic_geojson": "node/node_d_basic.geojson",
            "basic_csv": "node/node_d_basic.csv",
            "comprehensive_geojson": "node/node_d_comprehensive.geojson"
        }
    },
    "priorlake": {
        "feature_id": "8510353162",
        "start_time": "2024-09-12T00:00:00Z",
        "end_time": "2024-09-18T23:59:59Z",
        "expected_count": 2,
        "collection_name": "SWOT_L2_HR_LakeSP_2.0",
        "fields": "lake_id,time_str,wse,area_total,quality_f",
        "fixtures": {
            "basic_geojson": "priorlake/lake_basic.geojson",
            "basic_csv": "priorlake/lake_basic.csv",
            "comprehensive_geojson": "priorlake/lake_comprehensive.geojson"
        }
    },
    "priorlake_d": {
        "feature_id": "7230381002",
        "start_time": "2024-06-29T00:00:00Z",
        "end_time": "2024-07-19T23:59:59Z",
        "expected_count": 4,
        "collection_name": "SWOT_L2_HR_LakeSP_D",
        "fields": "lake_id,time_str,wse,area_total,quality_f",
#        "fields": "lake_id,time_str,wse,area_total,quality_f,qual_f_b",
        "fixtures": {
            "basic_geojson": "priorlake/lake_d_basic.geojson",
            "basic_csv": "priorlake/lake_d_basic.csv",
            "comprehensive_geojson": "priorlake/lake_d_comprehensive.geojson"
        }
    }
}

# Known stable test data - feature IDs are for UAT only
# These are used for regression testing and should always return data (200 OK)
# If any stable test returns 404, it indicates a deployment or data ingestion problem
# Update these if the feature IDs don't exist in your deployment
#
# Reference files ("golden" responses) are stored in fixtures/ directory
# Tests compare live API responses against these references to detect regressions
# Use capture_reference_files.py to generate/update reference files
STABLE_TEST_DATA_UAT = {
    "reach": {
        "feature_id": "34296500851",
        "start_time": "2024-02-10T00:00:00Z",
        "end_time": "2024-05-03T00:00:00Z",
        "expected_count": 6,
        "collection_name": "SWOT_L2_HR_RiverSP_2.0",
        "fields": "reach_id,time_str,wse,slope,width,sword_version",
        "fixtures": {
            "basic_geojson": "reach/reach_basic.geojson",
            "basic_csv": "reach/reach_basic.csv",
            "discharge_csv": "reach/reach_discharge.csv",
            "comprehensive_geojson": "reach/reach_comprehensive.geojson"
        }
    },
    "reach_d": {
        "feature_id": "33129200271",
        "start_time": "2025-06-04T00:00:00Z",
        "end_time": "2025-06-06T00:00:00Z",
        "expected_count": 2,
        "collection_name": "SWOT_L2_HR_RiverSP_D",
        "fields": "reach_id,time_str,wse,slope,width,sword_version",
        "fixtures": {
            "basic_geojson": "reach/reach_d_basic.geojson",
            "basic_csv": "reach/reach_d_basic.csv",
            "discharge_csv": "reach/reach_d_discharge.csv",
            "comprehensive_geojson": "reach/reach_d_comprehensive.geojson"
        }
    },
    "node": {
        "feature_id": "28311800020621",
        "start_time": "2024-01-28T00:00:00Z",
        "end_time": "2024-02-01T00:00:00Z",
        "expected_count": 2,
        "collection_name": "SWOT_L2_HR_RiverSP_2.0",
        "fields": "node_id,time_str,wse,width,lat,lon,sword_version",
        "fixtures": {
            "basic_geojson": "node/node_basic.geojson",
            "basic_csv": "node/node_basic.csv",
            "comprehensive_geojson": "node/node_comprehensive.geojson"
        }
    },
    "node_d": {
        "feature_id": "33122000170101",
        "start_time": "2025-06-04T00:00:00Z",
        "end_time": "2025-06-06T20:00:00Z",
        "expected_count": 2,
        "collection_name": "SWOT_L2_HR_RiverSP_D",
        "fields": "node_id,time_str,wse,width,wse_sm,wse_sm_u,wse_sm_q,wse_sm_q_b,lat,lon,sword_version",
        "fixtures": {
            "basic_geojson": "node/node_d_basic.geojson",
            "basic_csv": "node/node_d_basic.csv",
            "comprehensive_geojson": "node/node_d_comprehensive.geojson"
        }
    },
    "priorlake": {
        "feature_id": "7211251032",
        "start_time": "2023-09-09T00:00:00Z",
        "end_time": "2024-08-20T23:59:59Z",
        "expected_count": 2,
        "collection_name": "SWOT_L2_HR_LakeSP_2.0",
        "fields": "lake_id,time_str,wse,area_total,quality_f",
        "fixtures": {
            "basic_geojson": "priorlake/lake_basic.geojson",
            "basic_csv": "priorlake/lake_basic.csv",
            "comprehensive_geojson": "priorlake/lake_comprehensive.geojson"
        }
    },
    "priorlake_d": {
        "feature_id": "8223592002",
        "start_time": "2025-06-04T00:00:00Z",
        "end_time": "2025-06-06T23:59:59Z",
        "expected_count": 2,
        "collection_name": "SWOT_L2_HR_LakeSP_D",
        "fields": "lake_id,time_str,wse,area_total,quality_f,qual_f_b",
        "fixtures": {
            "basic_geojson": "priorlake/lake_d_basic.geojson",
            "basic_csv": "priorlake/lake_d_basic.csv",
            "comprehensive_geojson": "priorlake/lake_d_comprehensive.geojson"
        }
    }
}

@pytest.fixture(scope="session")
def test_env():
    """
    Get the test environment name
    """
    return os.environ.get("HYDROCRON_ENV", "").lower()


@pytest.fixture(scope="session")
def api_url(test_env):
    """
    Get the API URL to test against based on HYDROCRON_ENV environment variable.

    Set HYDROCRON_ENV to 'uat' or 'ops' before running tests.
    If not set, tests will be skipped.
    """
    if test_env not in API_URLS:
        pytest.skip(f"HYDROCRON_ENV not set or invalid. Set to 'uat' or 'ops' to run regression tests. Current value: '{test_env}'")

    return API_URLS[test_env]


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

        def query(self, params, timeout=5, headers=None):
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


@pytest.fixture(scope="session")
def stable_test_data(test_env):
    """
    Known stable test data for regression tests based on environment
    """
    return STABLE_TEST_DATA_OPS if test_env == "ops" else STABLE_TEST_DATA_UAT


@pytest.fixture
def fixtures_dir(test_env):
    """
    Get the fixtures directory path for the current environment
    """
    import pathlib
    return pathlib.Path(__file__).parent / "fixtures" / test_env


# Pytest markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "smoke: Quick smoke tests (run after every deployment)")
    config.addinivalue_line("markers", "slow: Slow tests that take > 10 seconds")
    config.addinivalue_line("markers", "version_d: Tests for Version D specific features")
    config.addinivalue_line("markers", "golden: Tests that compare against golden reference files")
