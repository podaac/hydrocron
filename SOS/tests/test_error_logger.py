"""Tests for CSV error log writer."""
import csv
import os
import tempfile
from datetime import datetime, timezone

from SOS.sos_ingest.config import IngestConfig
from SOS.sos_ingest.error_logger import IngestErrorLogger, ERROR_CSV_COLUMNS
from SOS.sos_ingest.models import ProcessingSummary


def _make_logger():
    output_dir = tempfile.mkdtemp()
    logger = IngestErrorLogger(output_dir, "test_sos_file.nc", table_name="test-table")
    return logger, output_dir


class TestCsvFileCreated:
    def test_creates_csv_with_correct_header(self):
        logger, output_dir = _make_logger()
        logger.close()
        assert os.path.exists(logger.error_path)
        with open(logger.error_path) as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header == ERROR_CSV_COLUMNS


class TestLogWritesRow:
    def test_writes_row_with_all_columns(self):
        logger, _ = _make_logger()
        sos_time = datetime(2023, 9, 15, 10, 0, 0, tzinfo=timezone.utc)
        logger.log(
            reach_id="18180900091",
            sos_time=sos_time,
            sos_time_seconds=748617713.0,
            closest_time="2023-09-15T10:02:00Z",
            time_delta=120.0,
            status="no_match",
            error_message="outside tolerance",
        )
        logger.close()

        with open(logger.error_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["reach_id"] == "18180900091"
        assert rows[0]["status"] == "no_match"
        assert rows[0]["db_table"] == "test-table"
        assert rows[0]["time_delta_seconds"] == "120.0"


class TestMultipleStatuses:
    def test_all_status_types_written(self):
        logger, _ = _make_logger()
        sos_time = datetime(2023, 9, 15, 10, 0, 0, tzinfo=timezone.utc)

        for status in ["no_match", "no_rows", "ambiguous_match", "write_error"]:
            logger.log(
                reach_id="18180900091",
                sos_time=sos_time,
                sos_time_seconds=748617713.0,
                closest_time=None,
                time_delta=None,
                status=status,
            )
        logger.close()

        with open(logger.error_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 4
        statuses = [r["status"] for r in rows]
        assert statuses == ["no_match", "no_rows", "ambiguous_match", "write_error"]


class TestWriteSummaryCreatesFile:
    def test_summary_file_created_with_stats(self):
        logger, _ = _make_logger()
        summary = ProcessingSummary(
            total_reaches=100,
            reaches_processed=80,
            reaches_skipped=20,
            total_time_steps=500,
            matched=450,
            updated=400,
            no_match=30,
            no_rows=10,
            ambiguous_match=2,
            skipped_unchanged=50,
            write_errors=3,
            dry_run=False,
            last_reach_id="18180900091",
            start_time=datetime(2026, 5, 6, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 5, 6, 10, 15, 0, tzinfo=timezone.utc),
        )
        config = IngestConfig(
            sos_file="/path/to/af_sword_v16_SOS_results.nc",
            aws_profile=None,
            table_name="hydrocron-swot-reach-table",
            time_tolerance_seconds=900,
        )
        logger.write_summary(summary, config)
        logger.close()

        assert os.path.exists(logger.summary_path)
        content = open(logger.summary_path).read()
        assert "Reaches processed: 80" in content
        assert "Matched:" in content and "450" in content
        assert "Last reach ID processed: 18180900091" in content
        assert "15m 00s" in content
        assert "Reaches not in DB: 10" in content
        assert "File:" in content and "af_sword_v16_SOS_results.nc" in content
        assert "Table:" in content and "hydrocron-swot-reach-table" in content
        assert "Time tolerance:" in content and "900s" in content


class TestFlushOnClose:
    def test_all_rows_flushed_after_close(self):
        logger, _ = _make_logger()
        sos_time = datetime(2023, 9, 15, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(10):
            logger.log(
                reach_id=f"reach_{i}",
                sos_time=sos_time,
                sos_time_seconds=748617713.0,
                closest_time=None,
                time_delta=None,
                status="no_rows",
            )
        logger.close()

        with open(logger.error_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 10
