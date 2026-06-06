"""Tests for SOS NetCDF reader."""
from datetime import datetime, timezone

import numpy as np
import pytest

from SOS.sos_ingest.reader import (
    ALGORITHM_CONFIG,
    get_reach_count,
    read_sos_file,
    sos_seconds_to_datetime,
)
from SOS.tests.conftest import SAMPLE_TIMES


class TestReadSosFileAllAlgorithms:
    """test_read_sos_file_all_algorithms"""

    def test_all_six_algorithms_extracted(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["all"])
        algo_names = set()
        for rds in reach_data.values():
            for rec in rds.records:
                algo_names.add(rec.algorithm)
        assert algo_names == {"consensus", "metroman", "momma", "sic4dvar", "sad", "hivdi", "lakeflow"}


class TestReadSosFileSingleAlgorithm:
    """test_read_sos_file_single_algorithm"""

    def test_only_requested_algorithm_returned(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["consensus"])
        for rds in reach_data.values():
            for rec in rds.records:
                assert rec.algorithm == "consensus"


class TestReachIdsSortedAscending:
    """test_reach_ids_sorted_ascending"""

    def test_reach_ids_in_numeric_order(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["all"])
        reach_ids = list(reach_data.keys())
        assert reach_ids == sorted(reach_ids, key=int)


class TestMissingValuesFiltered:
    """test_missing_values_filtered"""

    def test_no_fill_values_in_results(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["all"])
        for rds in reach_data.values():
            for rec in rds.records:
                assert rec.discharge_value != -999999999999.0


class TestMetromanMissingValueWorkaround:
    """test_metroman_missing_value_workaround — uses consensus missing value."""

    def test_metroman_fill_filtered_correctly(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["metroman"])
        # Reach 0 has only fill values — should not appear in results
        assert "10000000011" not in reach_data
        # Reach 1 should have valid metroman records (first time step is fill)
        if "10000000021" in reach_data:
            for rec in reach_data["10000000021"].records:
                assert rec.discharge_value != -999999999999.0


class TestHivdiMissingValueWorkaround:
    """test_hivdi_missing_value_workaround — falls back to consensus missing value."""

    def test_hivdi_fill_filtered_correctly(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["hivdi"])
        # Reach 0 has only fill values — should not appear
        assert "10000000011" not in reach_data
        # Reach 1 valid records should not contain fill
        if "10000000021" in reach_data:
            for rec in reach_data["10000000021"].records:
                assert rec.discharge_value != -999999999999.0


class TestTimeConversion:
    """test_time_conversion"""

    def test_seconds_to_datetime(self):
        dt = sos_seconds_to_datetime(748617713.0)
        assert dt.year == 2023
        assert dt.tzinfo == timezone.utc

    def test_records_have_correct_datetime(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["consensus"])
        rds = reach_data["10000000021"]
        first_rec = rds.records[0]
        expected = sos_seconds_to_datetime(SAMPLE_TIMES[1])
        assert first_rec.sos_datetime == expected


class TestTimeStepsSortedAscending:
    """test_time_steps_sorted_ascending"""

    def test_times_in_order_within_reach(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["consensus"])
        for rds in reach_data.values():
            times = [rec.sos_time_seconds for rec in rds.records]
            assert times == sorted(times)


class TestNoDataTimesSkipped:
    """test_no_data_times_skipped"""

    def test_missing_times_excluded_and_counted(self, sample_sos_netcdf):
        reach_data, missing_time_counts = read_sos_file(sample_sos_netcdf, ["all"])
        # Reach 2 (10000000031) has 1 missing time at index 2
        # missing_time_counts is per-algorithm
        assert isinstance(missing_time_counts, dict)
        assert sum(missing_time_counts.values()) > 0
        # Verify no record has the missing time value as its sos_time_seconds
        for rds in reach_data.values():
            for rec in rds.records:
                assert rec.sos_time_seconds != -999999999999.0
                assert rec.sos_time_seconds != 0.0


class TestSic4dvarStandardGroup:
    """test_sic4dvar_standard_group"""

    def test_sic4dvar_read_from_group(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["sic4dvar"])
        assert len(reach_data) > 0
        for rds in reach_data.values():
            for rec in rds.records:
                assert rec.algorithm == "sic4dvar"
                assert rec.discharge_value != -999999999999.0


class TestLakeflowFixed2dArray:
    """test_lakeflow_fixed_2d_array"""

    def test_lakeflow_reads_valid_data(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["all"])
        lakeflow_records = []
        for rds in reach_data.values():
            for rec in rds.records:
                if rec.algorithm == "lakeflow":
                    lakeflow_records.append(rec)
        assert len(lakeflow_records) > 0
        for rec in lakeflow_records:
            assert rec.discharge_value != -999999999999.0
            assert not np.isnan(rec.discharge_value)

    def test_lakeflow_matches_existing_time(self, sample_sos_netcdf):
        """Lakeflow records should adopt the precise time from other algorithms on the same day."""
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["all"])
        # Reach 10000000021 (index 1) has consensus data at SAMPLE_TIMES[1]
        # and lakeflow data at the same day — lakeflow should adopt that time
        rds = reach_data.get("10000000021")
        assert rds is not None
        lf_recs = [r for r in rds.records if r.algorithm == "lakeflow"]
        non_lf_recs = [r for r in rds.records if r.algorithm != "lakeflow"]
        # Each lakeflow record's time should match an existing record's time on the same day
        non_lf_dates = {r.sos_datetime.strftime("%Y-%m-%d"): r.sos_time_seconds for r in non_lf_recs}
        for lf_rec in lf_recs:
            lf_date = lf_rec.sos_datetime.strftime("%Y-%m-%d")
            if lf_date in non_lf_dates:
                assert lf_rec.sos_time_seconds == non_lf_dates[lf_date]

    def test_lakeflow_filters_nan(self, sample_sos_netcdf):
        """NaN values in lakeflow discharge should be filtered out."""
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["lakeflow"])
        for rds in reach_data.values():
            for rec in rds.records:
                assert not np.isnan(rec.discharge_value)


class TestGetReachCount:
    """test_get_reach_count"""

    def test_returns_correct_total(self, sample_sos_netcdf):
        count = get_reach_count(sample_sos_netcdf)
        assert count == 5


class TestProgressCallback:
    """test_progress_callback"""

    def test_callback_called_per_reach(self, sample_sos_netcdf):
        calls = []
        read_sos_file(sample_sos_netcdf, ["all"], on_reach_progress=lambda n: calls.append(n))
        assert len(calls) == 5
        assert all(c == 1 for c in calls)


class TestInvalidFilePath:
    """test_invalid_file_path"""

    def test_raises_on_nonexistent_file(self):
        with pytest.raises((FileNotFoundError, OSError)):
            read_sos_file("/nonexistent/path/file.nc", ["all"])


class TestEmptyAlgorithmGroup:
    """test_empty_algorithm_group"""

    def test_reach_with_only_fill_excluded(self, sample_sos_netcdf):
        reach_data, _ = read_sos_file(sample_sos_netcdf, ["all"])
        # Reach 0 (10000000011) has only fill values across all algorithms
        assert "10000000011" not in reach_data
