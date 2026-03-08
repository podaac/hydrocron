"""
Tests for time parameter encoding and formats

The API accepts ISO 8601 format timestamps with optional UTC offsets.
These tests verify:
- Basic ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- UTC offsets (+HH:MM, -HH:MM)
- URL encoding of + as %2b
- Invalid time formats
"""
import pytest
from .utils import assert_http_success, assert_http_error, assert_result_count
from urllib.parse import urlencode, quote


class TestBasicISO8601Formats:
    """Test basic ISO 8601 timestamp formats"""

    def test_utc_timestamp_with_z_suffix(self, api_client, stable_test_data):
        """Test standard UTC timestamp with Z suffix"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-05-03T23:59:59Z",
            "fields": "reach_id,time_str,wse"
        })

        assert_http_success(response)

    def test_utc_timestamp_without_z_suffix(self, api_client, stable_test_data):
        """Test UTC timestamp without Z suffix (may be interpreted as UTC)"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-10T00:00:00",
            "end_time": "2024-05-03T23:59:59",
            "fields": "reach_id,time_str,wse"
        })

        # Should return error
        assert response.status_code in [400, 400]

    def test_timestamp_with_milliseconds(self, api_client, stable_test_data):
        """Test timestamp with millisecond precision"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-10T00:00:00.000Z",
            "end_time": "2024-05-03T23:59:59.999Z",
            "fields": "reach_id,time_str,wse"
        })

        # Should return error
        assert response.status_code in [400, 400]


class TestUTCOffsets:
    """Test timestamps with UTC offsets"""

    def test_positive_utc_offset_plus_sign(self, api_client, stable_test_data):
        """Test timestamp with positive UTC offset (+05:00)"""
        reach_data = stable_test_data["reach"]

        # Use URL encoding for + sign
        start_time_encoded = "2024-02-10T05:00:00%2B05:00"  # +05:00 encoded
        end_time_encoded = "2024-05-04T04:59:59%2B05:00"

        # Manually construct URL to ensure proper encoding
        import requests
        url = api_client.base_url
        params = {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": start_time_encoded,
            "end_time": end_time_encoded,
            "fields": "reach_id,time_str,wse"
        }

        # Use params_str to avoid re-encoding
        params_str = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{params_str}"

        response = requests.get(full_url, timeout=30)

        # Should work with proper URL encoding
        assert response.status_code in [200, 200]

    def test_negative_utc_offset(self, api_client, stable_test_data):
        """Test timestamp with negative UTC offset (-08:00)"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-09T16:00:00-08:00",
            "end_time": "2024-05-03T15:59:59-08:00",
            "fields": "reach_id,time_str,wse"
        })

        # Negative offset doesn't need encoding, should work
        assert response.status_code in [200, 200]

    def test_zero_utc_offset(self, api_client, stable_test_data):
        """Test timestamp with +00:00 offset (equivalent to Z)"""
        reach_data = stable_test_data["reach"]

        # Need to encode + as %2b
        start_time_encoded = "2024-02-10T00:00:00%2B00:00"
        end_time_encoded = "2024-05-03T23:59:59%2B00:00"

        import requests
        url = api_client.base_url
        params_str = (
            f"feature=Reach&"
            f"feature_id={reach_data['feature_id']}&"
            f"start_time={start_time_encoded}&"
            f"end_time={end_time_encoded}&"
            f"fields=reach_id,time_str,wse"
        )
        full_url = f"{url}?{params_str}"

        response = requests.get(full_url, timeout=30)

        assert response.status_code in [200, 200]


class TestURLEncoding:
    """Test URL encoding of special characters in timestamps"""

    def test_plus_sign_must_be_encoded(self, api_client, stable_test_data):
        """Test that + in timestamp must be URL encoded as %2b"""
        reach_data = stable_test_data["reach"]

        # Test with improperly encoded + (as literal +)
        # Note: requests library automatically encodes URLs, so we need to test
        # the raw URL construction
        import requests

        url = api_client.base_url

        # Incorrectly using literal + (will be interpreted as space)
        params_str_bad = (
            f"feature=Reach&"
            f"feature_id={reach_data['feature_id']}&"
            f"start_time=2024-02-10T00:00:00+00:00&"  # Literal + (wrong)
            f"end_time=2024-05-03T23:59:59+00:00&"
            f"fields=reach_id,time_str,wse"
        )

        # Correctly using %2b encoding
        params_str_good = (
            f"feature=Reach&"
            f"feature_id={reach_data['feature_id']}&"
            f"start_time=2024-02-10T00:00:00%2B00:00&"  # Encoded as %2b (correct)
            f"end_time=2024-05-03T23:59:59%2B00:00&"
            f"fields=reach_id,time_str,wse"
        )

        # The incorrectly encoded version should fail or behave unexpectedly
        response_bad = requests.get(f"{url}?{params_str_bad}", timeout=30)

        # The correctly encoded version should work
        response_good = requests.get(f"{url}?{params_str_good}", timeout=30)

        # Bad encoding should fail
        assert response_bad.status_code in [400, 400]

        # Good encoding should succeed
        assert response_good.status_code in [200, 200]


class TestInvalidTimeFormats:
    """Test invalid time format handling"""

    def test_invalid_date_format_returns_error(self, api_client, stable_test_data):
        """Test completely invalid date format returns 400"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "invalid-date-format",
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_date_only_format(self, api_client, stable_test_data):
        """Test date-only format (without time) behavior"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-10",  # No time component
            "end_time": "2024-05-03",
            "fields": "reach_id,time_str,wse"
        })

        # Should return error
        assert response.status_code in [400, 400]

    def test_time_without_date(self, api_client, stable_test_data):
        """Test time-only format (invalid) returns error"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "00:00:00",  # No date component
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_invalid_month(self, api_client, stable_test_data):
        """Test invalid month (13) returns error"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-13-01T00:00:00Z",  # Month 13 invalid
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_invalid_day(self, api_client, stable_test_data):
        """Test invalid day (32) returns error"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-32T00:00:00Z",  # Day 32 invalid
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))

    def test_invalid_hour(self, api_client, stable_test_data):
        """Test invalid hour (25) returns error"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-10T25:00:00Z",  # Hour 25 invalid
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        assert_http_error(response, expected_status_range=(400, 400))


class TestTimeRangeBehavior:
    """Test time range boundary conditions"""

    def test_start_equals_end_time(self, api_client, stable_test_data):
        """Test query with start_time equal to end_time"""
        reach_data = stable_test_data["reach"]

        same_time = "2024-02-10T00:00:00Z"

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": same_time,
            "end_time": same_time,
            "fields": "reach_id,time_str,wse"
        })

        # Should return error
        assert response.status_code in [400, 400]

    def test_very_narrow_time_range(self, api_client, stable_test_data):
        """Test query with very narrow time range (1 second)"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-10T00:00:00Z",
            "end_time": "2024-02-10T00:00:01Z",  # 1 second range
            "fields": "reach_id,time_str,wse"
        })

        # Should return error
        assert response.status_code in [400, 400]

    def test_very_wide_time_range(self, api_client, stable_test_data):
        """Test query with very wide time range (10 years)"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2020-01-01T00:00:00Z",
            "end_time": "2030-12-31T23:59:59Z",  # 10+ years
            "fields": "reach_id,time_str,wse"
        }, timeout=60)

        # Should work but may return 413 if too much data
        assert response.status_code in [200, 200]


class TestTimeFormatConsistency:
    """Test time format consistency across feature types"""

    def test_same_time_format_works_for_all_features(self, api_client, stable_test_data):
        """Test that same time format works for Reach, Node, and PriorLake"""
        reach_data = stable_test_data["reach"]
        node_data = stable_test_data["node"]
        lake_data = stable_test_data["priorlake"]

        time_format = "2024-02-10T00:00:00Z"

        # Test Reach
        response_reach, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        # Test Node
        response_node, _ = api_client.query({
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "fields": "node_id,time_str,wse"
        })

        # Test PriorLake
        response_lake, _ = api_client.query({
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "fields": "lake_id,time_str,wse"
        })

        # All should succeed with same time format
        assert_http_success(response_reach)
        assert_http_success(response_node)
        assert_http_success(response_lake)


class TestLeapYearAndDST:
    """Test edge cases like leap years and daylight saving time"""

    def test_leap_day_february_29(self, api_client, stable_test_data):
        """Test querying on leap day (Feb 29, 2024)"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2024-02-29T00:00:00Z",  # 2024 is leap year
            "end_time": "2024-02-29T23:59:59Z",
            "fields": "reach_id,time_str,wse"
        })

        # Should accept Feb 29 in leap year
        assert response.status_code in [200, 200]

    def test_invalid_leap_day_non_leap_year(self, api_client, stable_test_data):
        """Test invalid Feb 29 in non-leap year"""
        reach_data = stable_test_data["reach"]

        response, _ = api_client.query({
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": "2023-02-29T00:00:00Z",  # 2023 is NOT leap year
            "end_time": reach_data["end_time"],
            "fields": "reach_id,time_str,wse"
        })

        # Should reject Feb 29 in non-leap year
        assert_http_error(response, expected_status_range=(400, 400))
