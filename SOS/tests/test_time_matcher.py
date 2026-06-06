"""Tests for time matching logic."""
from datetime import datetime, timedelta, timezone

from SOS.sos_ingest.time_matcher import find_closest_time


def _utc(year, month, day, hour=0, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


DB_TIMES = [
    ("2023-09-15T10:00:00Z", _utc(2023, 9, 15, 10, 0, 0)),
    ("2023-09-15T10:30:00Z", _utc(2023, 9, 15, 10, 30, 0)),
    ("2023-09-15T11:00:00Z", _utc(2023, 9, 15, 11, 0, 0)),
]


class TestExactMatch:
    def test_exact_match(self):
        sos_dt = _utc(2023, 9, 15, 10, 30, 0)
        key, delta, status = find_closest_time(sos_dt, DB_TIMES, 300)
        assert status == "matched"
        assert key == "2023-09-15T10:30:00Z"
        assert delta == 0.0


class TestCloseMatchWithinTolerance:
    def test_two_minutes_off_within_five_min_tolerance(self):
        sos_dt = _utc(2023, 9, 15, 10, 32, 0)
        key, delta, status = find_closest_time(sos_dt, DB_TIMES, 300)
        assert status == "matched"
        assert key == "2023-09-15T10:30:00Z"
        assert delta == 120.0


class TestNoMatchOutsideTolerance:
    def test_ten_minutes_off_with_five_min_tolerance(self):
        sos_dt = _utc(2023, 9, 15, 10, 40, 0)
        key, delta, status = find_closest_time(sos_dt, DB_TIMES, 300)
        assert status == "no_match"
        assert key is None
        assert delta == 600.0


class TestClosestOfMultiple:
    def test_returns_closer_of_two_within_tolerance(self):
        sos_dt = _utc(2023, 9, 15, 10, 28, 0)
        key, delta, status = find_closest_time(sos_dt, DB_TIMES, 900)
        assert status == "matched"
        assert key == "2023-09-15T10:30:00Z"
        assert delta == 120.0


class TestEmptyDbTimes:
    def test_no_db_times_returns_no_match(self):
        sos_dt = _utc(2023, 9, 15, 10, 0, 0)
        key, delta, status = find_closest_time(sos_dt, [], 900)
        assert status == "no_match"
        assert key is None
        assert delta is None


class TestToleranceBoundary:
    def test_exactly_at_tolerance_boundary_matches(self):
        sos_dt = _utc(2023, 9, 15, 10, 5, 0)
        key, delta, status = find_closest_time(sos_dt, DB_TIMES, 300)
        assert status == "matched"
        assert key == "2023-09-15T10:00:00Z"
        assert delta == 300.0


class TestAmbiguousMatchOnTie:
    def test_two_equidistant_times_flags_ambiguous(self):
        # SOS time exactly between two DB times
        db_times = [
            ("2023-09-15T10:00:00Z", _utc(2023, 9, 15, 10, 0, 0)),
            ("2023-09-15T10:10:00Z", _utc(2023, 9, 15, 10, 10, 0)),
        ]
        sos_dt = _utc(2023, 9, 15, 10, 5, 0)
        key, delta, status = find_closest_time(sos_dt, db_times, 900)
        assert status == "ambiguous_match"
        assert key is None
        assert delta == 300.0
