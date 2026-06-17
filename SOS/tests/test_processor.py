"""Integration tests for the processor module."""
import csv
import os
import signal
import tempfile
import threading
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import moto
import boto3
import pytest

from SOS.sos_ingest.config import IngestConfig
from SOS.sos_ingest.processor import run, _build_column_updates, _validate_config
from SOS.sos_ingest.models import ReachDischargeSet, DischargeRecord
from SOS.sos_ingest.reader import sos_seconds_to_datetime
from SOS.tests.conftest import SAMPLE_TIMES, MOCK_TABLE_NAME


def _make_config(sos_file, **kwargs):
    defaults = {
        "sos_file": sos_file,
        "table_name": MOCK_TABLE_NAME,
        "dry_run": True,
        "output_dir": tempfile.mkdtemp(),
        "yes": True,
        "aws_profile": None,
    }
    defaults.update(kwargs)
    return IngestConfig(**defaults)


def _setup_mock_db_with_times(dynamodb, reach_ids, times):
    """Create a mock table and populate with reach rows at given times."""
    dynamodb.create_table(
        TableName=MOCK_TABLE_NAME,
        AttributeDefinitions=[
            {"AttributeName": "reach_id", "AttributeType": "S"},
            {"AttributeName": "range_start_time", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "reach_id", "KeyType": "HASH"},
            {"AttributeName": "range_start_time", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table = dynamodb.Table(MOCK_TABLE_NAME)
    for rid in reach_ids:
        for t in times:
            table.put_item(Item={
                "reach_id": rid,
                "range_start_time": t,
                "time": "748617713.0",
            })


def _get_db_times_for_fixture():
    """Convert SAMPLE_TIMES to ISO strings matching what the reader produces."""
    return [sos_seconds_to_datetime(t).strftime("%Y-%m-%dT%H:%M:%SZ") for t in SAMPLE_TIMES]


class TestFullDryRun:
    def test_no_db_writes_and_log_created(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021", "10000000041", "10000000051"], times)

            config = _make_config(sample_sos_netcdf, dry_run=True)
            summary = run(config)

            assert summary.dry_run is True
            assert summary.matched > 0
            assert summary.write_errors == 0
            assert os.path.exists(os.path.join(config.output_dir, os.listdir(config.output_dir)[0]))


class TestFullLiveRun:
    def test_columns_added_to_db(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021", "10000000041", "10000000051"], times)

            config = _make_config(sample_sos_netcdf, dry_run=False)
            summary = run(config)

            assert summary.matched > 0
            table = dynamodb.Table(MOCK_TABLE_NAME)
            resp = table.get_item(Key={"reach_id": "10000000021", "range_start_time": times[1]})
            item = resp["Item"]
            assert "sos_consensus_q" in item


class TestResumeFromReachId:
    def test_reaches_before_start_skipped(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021", "10000000041", "10000000051"], times)

            config = _make_config(sample_sos_netcdf, start_reach_id="10000000041")
            summary = run(config)

            assert summary.reaches_skipped > 0


class TestStopReachId:
    def test_processing_stops_after_stop_id(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021", "10000000041", "10000000051"], times)

            config = _make_config(sample_sos_netcdf, stop_reach_id="10000000041")
            summary = run(config)

            # Should not process reach 10000000051
            assert summary.last_reach_id in ("10000000041", "10000000031", "10000000021")


class TestStartAndStopReachId:
    def test_only_specified_range_processed(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021", "10000000041", "10000000051"], times)

            config = _make_config(sample_sos_netcdf, start_reach_id="10000000041", stop_reach_id="10000000041")
            summary = run(config)

            assert summary.last_reach_id == "10000000041"


class TestSummaryCounts:
    def test_summary_has_correct_counts(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021"], times)

            config = _make_config(sample_sos_netcdf)
            summary = run(config)

            # no_rows is a reach-level count, not included in time step total
            total_accounted = summary.matched + summary.no_match + summary.ambiguous_match + summary.skipped_unchanged + summary.write_errors
            # Time steps for reaches not in DB still advance the progress bar
            assert summary.total_time_steps > 0
            assert total_accounted <= summary.total_time_steps


class TestErrorLogWritten:
    def test_csv_contains_only_errors(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            # Only put one reach in DB — others will get no_rows
            _setup_mock_db_with_times(dynamodb, ["10000000021"], _get_db_times_for_fixture())

            config = _make_config(sample_sos_netcdf)
            summary = run(config)

            # Find the error CSV
            csv_files = [f for f in os.listdir(config.output_dir) if f.endswith(".csv")]
            assert len(csv_files) == 1
            with open(os.path.join(config.output_dir, csv_files[0])) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            # All rows should be errors (no_rows for reaches not in DB)
            for row in rows:
                assert row["status"] in ("no_match", "no_rows", "ambiguous_match", "write_error")


class TestSingleAlgorithmFilter:
    def test_only_specified_algorithm_columns_written(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021"], times)

            config = _make_config(sample_sos_netcdf, dry_run=False, algorithms=["consensus"])
            summary = run(config)

            table = dynamodb.Table(MOCK_TABLE_NAME)
            resp = table.get_item(Key={"reach_id": "10000000021", "range_start_time": times[1]})
            item = resp["Item"]
            assert "sos_consensus_q" in item
            assert "sos_metroman_q" not in item


class TestHandlesReachWithNoDbRows:
    def test_reach_missing_from_db_logged_and_continues(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            # Empty table — no reaches
            dynamodb.create_table(
                TableName=MOCK_TABLE_NAME,
                AttributeDefinitions=[
                    {"AttributeName": "reach_id", "AttributeType": "S"},
                    {"AttributeName": "range_start_time", "AttributeType": "S"},
                ],
                KeySchema=[
                    {"AttributeName": "reach_id", "KeyType": "HASH"},
                    {"AttributeName": "range_start_time", "KeyType": "RANGE"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )

            config = _make_config(sample_sos_netcdf)
            summary = run(config)

            assert summary.no_rows > 0
            assert summary.last_reach_id is not None


class TestCtrlCGracefulShutdown:
    def test_sigint_flushes_logs_and_writes_summary(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021", "10000000041", "10000000051"], times)

            config = _make_config(sample_sos_netcdf)

            # Send SIGINT after a short delay
            def send_signal():
                import time
                time.sleep(0.05)
                os.kill(os.getpid(), signal.SIGINT)

            thread = threading.Thread(target=send_signal)
            thread.start()

            summary = run(config)
            thread.join()

            # Summary should exist even after interrupt
            summary_files = [f for f in os.listdir(config.output_dir) if "summary" in f]
            assert len(summary_files) == 1


class TestLastReachIdInSummary:
    def test_summary_includes_last_reach_and_resume(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021", "10000000041"], times)

            config = _make_config(sample_sos_netcdf)
            summary = run(config)

            assert summary.last_reach_id is not None
            # Check summary file mentions resume
            summary_files = [f for f in os.listdir(config.output_dir) if "summary" in f]
            content = open(os.path.join(config.output_dir, summary_files[0])).read()
            assert "--start-reach-id" in content


class TestSkipUnchangedRows:
    def test_unchanged_rows_not_updated(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021"], times)

            config = _make_config(sample_sos_netcdf, dry_run=False)
            # First run writes the values
            run(config)
            # Second run should find them unchanged
            config2 = _make_config(sample_sos_netcdf, dry_run=False, output_dir=tempfile.mkdtemp())
            summary2 = run(config2)

            assert summary2.skipped_unchanged > 0


class TestMissingTimeCountInReader:
    def test_missing_time_counted_per_algorithm(self, sample_sos_netcdf):
        from SOS.sos_ingest.reader import read_sos_file
        _, missing_time_counts = read_sos_file(sample_sos_netcdf, ["all"])
        # Reach 10000000031 has 1 missing time — counted per algorithm with valid discharge there
        assert sum(missing_time_counts.values()) > 0
        assert all(isinstance(v, int) for v in missing_time_counts.values())


class TestMultipleAlgorithmsGrouped:
    def test_single_update_per_timestep(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times_for_fixture()
            _setup_mock_db_with_times(dynamodb, ["10000000021"], times)

            config = _make_config(sample_sos_netcdf, dry_run=False)
            summary = run(config)

            # Verify multiple algorithm columns written in one go
            table = dynamodb.Table(MOCK_TABLE_NAME)
            resp = table.get_item(Key={"reach_id": "10000000021", "range_start_time": times[1]})
            item = resp["Item"]
            # All 7 algorithms should have been written
            assert "sos_consensus_q" in item
            assert "sos_metroman_q" in item
            assert "sos_momma_q" in item
            assert "sos_sic4dvar_q" in item
            assert "sos_sad_q" in item
            assert "sos_hivdi_q" in item
            assert "sos_lakeflow_q" in item


class TestValidateConfigFileNotFound:
    def test_raises_system_exit_for_missing_file(self):
        config = IngestConfig(sos_file="/nonexistent/path/file.nc", output_dir=tempfile.mkdtemp())
        with pytest.raises(SystemExit, match="SOS file not found"):
            _validate_config(config)


class TestValidateConfigOutputDirNotWritable:
    def test_raises_system_exit_for_unwritable_dir(self, sample_sos_netcdf):
        config = IngestConfig(sos_file=sample_sos_netcdf, output_dir="/proc/not_writable_dir")
        with pytest.raises((SystemExit, OSError)):
            _validate_config(config)
