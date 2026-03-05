"""
Configuration for regression tests
"""
import os
import pytest


# Environment URLs
API_URLS = {
    "uat": "https://soto.podaac.uat.earthdatacloud.nasa.gov/hydrocron/v1/timeseries",
    "ops": "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries",
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
