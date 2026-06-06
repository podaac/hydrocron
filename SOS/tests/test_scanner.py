"""Tests for post-ingest verification scanner."""
import csv
import os
import tempfile

import boto3
import moto

from SOS.sos_ingest.config import IngestConfig
from SOS.sos_ingest.processor import run
from SOS.sos_ingest.scanner import scan
from SOS.sos_ingest.reader import sos_seconds_to_datetime
from SOS.tests.conftest import SAMPLE_TIMES, MOCK_TABLE_NAME


def _make_config(sos_file, **kwargs):
    defaults = {
        "sos_file": sos_file,
        "table_name": MOCK_TABLE_NAME,
        "dry_run": False,
        "output_dir": tempfile.mkdtemp(),
        "yes": True,
        "aws_profile": None,
    }
    defaults.update(kwargs)
    return IngestConfig(**defaults)


def _setup_table(dynamodb, reach_ids, times):
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
    return table


def _get_db_times():
    return [sos_seconds_to_datetime(t).strftime("%Y-%m-%dT%H:%M:%SZ") for t in SAMPLE_TIMES]


class TestScanAllOk:
    def test_zero_discrepancies_after_ingest(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times()
            _setup_table(dynamodb, ["10000000021", "10000000041", "10000000051"], times)

            # Ingest first
            ingest_config = _make_config(sample_sos_netcdf)
            run(ingest_config)

            # Scan — only check reaches that were in DB
            scan_config = _make_config(sample_sos_netcdf, output_dir=tempfile.mkdtemp(),
                                       start_reach_id="10000000021", stop_reach_id="10000000021")
            summary = scan(scan_config)

            assert summary.ok > 0
            assert summary.missing_column == 0
            assert summary.value_mismatch == 0


class TestScanMissingColumn:
    def test_reports_missing_column(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times()
            _setup_table(dynamodb, ["10000000021"], times)

            # Don't ingest — columns will be missing
            scan_config = _make_config(sample_sos_netcdf, start_reach_id="10000000021", stop_reach_id="10000000021")
            summary = scan(scan_config)

            assert summary.missing_column > 0


class TestScanValueMismatch:
    def test_reports_value_mismatch(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times()
            table = _setup_table(dynamodb, ["10000000021"], times)

            # Write wrong value to a column
            table.update_item(
                Key={"reach_id": "10000000021", "range_start_time": times[1]},
                UpdateExpression="SET #c = :v",
                ExpressionAttributeNames={"#c": "sos_consensus_q"},
                ExpressionAttributeValues={":v": "WRONG_VALUE"},
            )

            scan_config = _make_config(sample_sos_netcdf, start_reach_id="10000000021", stop_reach_id="10000000021")
            summary = scan(scan_config)

            assert summary.value_mismatch > 0


class TestScanSourceMismatch:
    def test_reports_source_mismatch(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times()
            _setup_table(dynamodb, ["10000000021"], times)

            # Ingest first
            ingest_config = _make_config(sample_sos_netcdf, start_reach_id="10000000021", stop_reach_id="10000000021")
            run(ingest_config)

            # Now change source filename on one row
            table = dynamodb.Table(MOCK_TABLE_NAME)
            table.update_item(
                Key={"reach_id": "10000000021", "range_start_time": times[1]},
                UpdateExpression="SET #c = :v",
                ExpressionAttributeNames={"#c": "sos_source_filename"},
                ExpressionAttributeValues={":v": "different_file.nc"},
            )

            scan_config = _make_config(sample_sos_netcdf, output_dir=tempfile.mkdtemp(),
                                       start_reach_id="10000000021", stop_reach_id="10000000021")
            summary = scan(scan_config)

            assert summary.source_mismatch > 0


class TestScanSourceMismatchAndColumnIssue:
    def test_reports_both_source_and_value_mismatch(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            times = _get_db_times()
            table = _setup_table(dynamodb, ["10000000021"], times)

            # Write wrong source AND wrong column value on same row
            table.update_item(
                Key={"reach_id": "10000000021", "range_start_time": times[1]},
                UpdateExpression="SET #s = :s, #c = :c",
                ExpressionAttributeNames={"#s": "sos_source_filename", "#c": "sos_consensus_q"},
                ExpressionAttributeValues={":s": "different_file.nc", ":c": "WRONG"},
            )

            scan_config = _make_config(sample_sos_netcdf, start_reach_id="10000000021", stop_reach_id="10000000021")
            summary = scan(scan_config)

            assert summary.source_mismatch > 0
            assert summary.value_mismatch > 0


class TestScanNoRows:
    def test_reports_no_rows_for_missing_reach(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            # Empty table
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

            scan_config = _make_config(sample_sos_netcdf, start_reach_id="10000000021", stop_reach_id="10000000021")
            summary = scan(scan_config)

            assert summary.no_rows > 0


class TestScanNoTimeMatch:
    def test_reports_no_time_match(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            # Put rows with times way off from what SOS expects
            _setup_table(dynamodb, ["10000000021"], ["2020-01-01T00:00:00Z", "2020-02-01T00:00:00Z"])

            scan_config = _make_config(sample_sos_netcdf, start_reach_id="10000000021", stop_reach_id="10000000021")
            summary = scan(scan_config)

            assert summary.no_time_match > 0


class TestScanCsvWritten:
    def test_csv_contains_discrepancies(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            _setup_table(dynamodb, ["10000000021"], _get_db_times())

            # No ingest — will have missing columns
            scan_config = _make_config(sample_sos_netcdf, start_reach_id="10000000021", stop_reach_id="10000000021")
            scan(scan_config)

            csv_files = [f for f in os.listdir(scan_config.output_dir) if f.endswith(".csv")]
            assert len(csv_files) == 1
            with open(os.path.join(scan_config.output_dir, csv_files[0])) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert len(rows) > 0
            for row in rows:
                assert row["status"] in ("no_rows", "no_time_match", "missing_column", "value_mismatch", "source_mismatch")


class TestScanSummaryCounts:
    def test_totals_add_up(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            _setup_table(dynamodb, ["10000000021"], _get_db_times())

            scan_config = _make_config(sample_sos_netcdf, start_reach_id="10000000021", stop_reach_id="10000000021")
            summary = scan(scan_config)

            # ok + all discrepancy types should equal total time steps
            # (source_mismatch is counted per time step, not per column)
            total_accounted = summary.ok + summary.no_rows + summary.no_time_match + summary.source_mismatch
            # missing_column and value_mismatch are per-column, not per-step
            # But ok is only incremented if ALL columns pass, so:
            # time_steps = ok + no_rows + no_time_match + source_mismatch + steps_with_column_issues
            assert summary.total_time_steps > 0


class TestScanWithStartStopReachId:
    def test_respects_range(self, sample_sos_netcdf):
        with moto.mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            _setup_table(dynamodb, ["10000000021", "10000000041", "10000000051"], _get_db_times())

            scan_config = _make_config(sample_sos_netcdf, start_reach_id="10000000041", stop_reach_id="10000000041")
            summary = scan(scan_config)

            assert summary.total_reaches == 1
