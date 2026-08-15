"""Tests for the standalone DynamoDB bulk updater (all AWS objects are fakes)."""
import csv
import json
import threading
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from scripts import bulk_update_hydrocron_db as bulk


KEY_SCHEMA_REVERSED = [
    {"AttributeName": "range_start_time", "KeyType": "RANGE"},
    {"AttributeName": "reach_id", "KeyType": "HASH"},
]
ATTRIBUTE_DEFINITIONS = [
    {"AttributeName": "reach_id", "AttributeType": "S"},
    {"AttributeName": "range_start_time", "AttributeType": "S"},
]


class FakeTable:
    """Minimal table double supporting schema discovery, scans, and updates."""

    key_schema = KEY_SCHEMA_REVERSED
    attribute_definitions = ATTRIBUTE_DEFINITIONS

    def __init__(self, pages=None, update_error=None, scan_error=None, update_response=None):
        self.pages = pages or [{"Items": [], "ScannedCount": 0}]
        self.update_error = update_error
        self.scan_error = scan_error
        self.update_response = update_response or {}
        self.scan_calls = []
        self.update_calls = []
        self.client_config = None

    def scan(self, **kwargs):
        self.scan_calls.append(kwargs)
        if self.scan_error:
            raise self.scan_error
        return self.pages[len(self.scan_calls) - 1]

    def update_item(self, **kwargs):
        raise AssertionError("the boto3 Table resource must not be used by worker threads")

    def client_update_item(self, **kwargs):
        self.update_calls.append(kwargs)
        if self.update_error:
            raise self.update_error
        return self.update_response


class InterruptingTable(FakeTable):
    def client_update_item(self, **kwargs):
        self.update_calls.append(kwargs)
        raise KeyboardInterrupt


class ConcurrentTable(FakeTable):
    """Require two update calls to overlap and record peak concurrency."""

    def __init__(self, pages):
        super().__init__(pages=pages)
        self.barrier = threading.Barrier(2)
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def client_update_item(self, **kwargs):
        with self.lock:
            self.update_calls.append(kwargs)
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            self.barrier.wait(timeout=2)
            return {}
        finally:
            with self.lock:
                self.active -= 1


class InterruptDrainTable(ConcurrentTable):
    """Interrupt one worker after two requests are known to be in flight."""

    def client_update_item(self, **kwargs):
        with self.lock:
            self.update_calls.append(kwargs)
        self.barrier.wait(timeout=2)
        reach_id = kwargs["Key"]["reach_id"]["S"]
        if reach_id == "1":
            raise KeyboardInterrupt
        return {}


class FakeClient:
    """Low-level DynamoDB client double used by worker threads."""

    def __init__(self, table):
        self.table = table

    def update_item(self, **kwargs):
        return self.table.client_update_item(**kwargs)


class FakeSession:
    def __init__(self, table):
        self.table = table

    def resource(self, service_name, config=None):
        assert service_name == "dynamodb"
        assert config is not None
        return self

    def client(self, service_name, config=None):
        assert service_name == "dynamodb"
        assert config is not None
        self.table.client_config = config
        return FakeClient(self.table)

    def Table(self, table_name):
        assert table_name == "test-table"
        return self.table


def install_fake_session(monkeypatch, table):
    monkeypatch.setattr(bulk.boto3, "Session", lambda profile_name=None: FakeSession(table))


def invoke(tmp_path, extra_args, table, monkeypatch):
    install_fake_session(monkeypatch, table)
    return bulk.main([
        "test-table",
        *extra_args,
        "--output-dir",
        str(tmp_path),
        "--yes",
    ])


def one_output(tmp_path, suffix):
    matches = list(Path(tmp_path).glob(f"test-table_*_{suffix}"))
    assert len(matches) == 1
    return matches[0]


def test_parse_updates_rejects_duplicates_and_invalid_pairs():
    assert bulk.parse_updates(["a=1", "b=two=parts"]) == {"a": "1", "b": "two=parts"}
    with pytest.raises(ValueError, match="more than once"):
        bulk.parse_updates(["a=1", "a=2"])
    with pytest.raises(ValueError, match="not a column=value"):
        bulk.parse_updates(["missing-separator"])
    with pytest.raises(ValueError, match="empty"):
        bulk.parse_updates(["a="])


def test_positive_int_rejects_zero_negative_and_non_integer():
    assert bulk.positive_int("4") == 4
    for value in ("0", "-1", "nope"):
        with pytest.raises(Exception):
            bulk.positive_int(value)


def test_worker_count_accepts_safe_range_and_rejects_out_of_range():
    assert bulk.worker_count("1") == 1
    assert bulk.worker_count(str(bulk.WORKERS_MAX)) == bulk.WORKERS_MAX
    for value in ("0", str(bulk.WORKERS_MAX + 1), "nope"):
        with pytest.raises(Exception):
            bulk.worker_count(value)


def test_key_discovery_uses_key_type_not_list_order():
    partition_key, sort_key, columns = bulk.get_key_columns(KEY_SCHEMA_REVERSED)
    assert partition_key == "reach_id"
    assert sort_key == "range_start_time"
    assert columns == ["reach_id", "range_start_time"]


def test_validate_inputs_rejects_key_targets_and_bad_resume_keys():
    with pytest.raises(ValueError, match="primary-key columns"):
        bulk.validate_inputs({"reach_id": "x"}, None, ["reach_id", "range_start_time"], ATTRIBUTE_DEFINITIONS)
    with pytest.raises(ValueError, match="missing: range_start_time"):
        bulk.validate_inputs(
            {"value": "x"}, {"reach_id": "1"},
            ["reach_id", "range_start_time"], ATTRIBUTE_DEFINITIONS,
        )
    with pytest.raises(ValueError, match="must be a JSON string"):
        bulk.validate_inputs(
            {"value": "x"}, {"reach_id": 1, "range_start_time": "t"},
            ["reach_id", "range_start_time"], ATTRIBUTE_DEFINITIONS,
        )


def test_build_update_is_aliased_and_protects_against_deleted_items():
    result = bulk.build_update_args(
        "test-table",
        {"reach_id": "1", "range_start_time": "t"},
        {"status": "new", "size": "large"},
        ["reach_id", "range_start_time"],
    )
    assert result["TableName"] == "test-table"
    assert result["Key"] == {
        "reach_id": {"S": "1"},
        "range_start_time": {"S": "t"},
    }
    assert result["UpdateExpression"] == "SET #c0 = :v0, #c1 = :v1"
    assert result["ExpressionAttributeNames"]["#c0"] == "status"
    assert result["ExpressionAttributeValues"] == {
        ":v0": {"S": "new"},
        ":v1": {"S": "large"},
    }
    assert result["ConditionExpression"] == "attribute_exists(#k0) AND attribute_exists(#k1)"
    assert result["ReturnConsumedCapacity"] == "INDEXES"
    assert result["ReturnValues"] == "UPDATED_OLD"


def test_dry_run_paginates_checkpoints_skips_and_writes_valid_csv(tmp_path, monkeypatch, capsys):
    checkpoint = {"reach_id": "2", "range_start_time": "t2"}
    table = FakeTable(pages=[
        {
            "Items": [
                {"reach_id": "1", "range_start_time": "t1", "status": "old"},
                {"reach_id": "2", "range_start_time": "t2", "status": "new", "note": "a,b"},
            ],
            "ScannedCount": 2,
            "LastEvaluatedKey": checkpoint,
        },
        {
            "Items": [{"reach_id": "3", "range_start_time": "t3"}],
            "ScannedCount": 1,
        },
    ])

    result = invoke(
        tmp_path, ["status=new", "note=a,b", "--dry-run", "--checkpoint-pages", "1"],
        table, monkeypatch,
    )

    assert result == 0
    assert not table.update_calls
    assert table.scan_calls[1]["ExclusiveStartKey"] == checkpoint
    output = capsys.readouterr().out
    assert "Started. Scanning but not updating rows (DRY RUN)..." in output
    assert "Checkpoint:" in output
    with one_output(tmp_path, "dry_run.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows == [
        ["reach_id", "range_start_time", "columns"],
        ["1", "t1", "status=new; note=a,b"],
        ["3", "t3", "status=new; note=a,b"],
    ]
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Status: COMPLETED" in log
    assert "Rows read: 3" in log
    assert "Rows updated: 2" in log
    assert "Rows skipped: 1" in log


def test_live_update_uses_existence_condition(tmp_path, monkeypatch):
    table = FakeTable(pages=[{
        "Items": [{"reach_id": "1", "range_start_time": "t1", "status": "old"}],
        "ScannedCount": 1,
    }])

    assert invoke(tmp_path, ["status=new"], table, monkeypatch) == 0
    assert len(table.update_calls) == 1
    assert table.update_calls[0]["ConditionExpression"] == "attribute_exists(#k0) AND attribute_exists(#k1)"
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Rows actually changed: 1" in log
    assert "Redundant successful writes: 0" in log


def test_live_update_only_writes_fields_that_differ(tmp_path, monkeypatch):
    table = FakeTable(pages=[{
        "Items": [{
            "reach_id": "1",
            "range_start_time": "t1",
            "collection_version": "D",
            "sword_version": "old",
        }],
        "ScannedCount": 1,
    }])

    assert invoke(
        tmp_path, ["collection_version=D", "sword_version=17b"], table, monkeypatch,
    ) == 0
    names = table.update_calls[0]["ExpressionAttributeNames"]
    values = table.update_calls[0]["ExpressionAttributeValues"]
    assert "collection_version" not in names.values()
    assert "sword_version" in names.values()
    assert list(values.values()) == [{"S": "17b"}]


def test_live_update_classifies_redundant_write_without_per_row_file(tmp_path, monkeypatch):
    table = FakeTable(
        pages=[{
            "Items": [{"reach_id": "1", "range_start_time": "t1", "status": "stale"}],
            "ScannedCount": 1,
        }],
        update_response={"Attributes": {"status": {"S": "new"}}},
    )

    assert invoke(tmp_path, ["status=new"], table, monkeypatch) == 0
    assert list(Path(tmp_path).glob("test-table_*_updates.csv")) == []
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Rows actually changed: 0" in log
    assert "Redundant successful writes: 1" in log


def test_workers_overlap_and_size_the_connection_pool(tmp_path, monkeypatch):
    table = ConcurrentTable(pages=[{
        "Items": [
            {"reach_id": "1", "range_start_time": "t1", "status": "old"},
            {"reach_id": "2", "range_start_time": "t2", "status": "old"},
        ],
        "ScannedCount": 2,
    }])

    assert invoke(tmp_path, ["status=new", "--workers", "2"], table, monkeypatch) == 0
    assert table.max_active == 2
    assert table.client_config.max_pool_connections == 2
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Workers: 2" in log


def test_live_update_prints_time_based_progress_within_a_page(
    tmp_path, monkeypatch, capsys,
):
    table = FakeTable(pages=[{
        "Items": [
            {"reach_id": "1", "range_start_time": "t1", "status": "old"},
            {"reach_id": "2", "range_start_time": "t2", "status": "old"},
        ],
        "ScannedCount": 2,
    }])
    ticks = iter([0, 11, 11, 11])
    monkeypatch.setattr(bulk, "monotonic", lambda: next(ticks))

    assert invoke(
        tmp_path, ["status=new", "--workers", "1", "--progress-seconds", "10"],
        table, monkeypatch,
    ) == 0
    output = capsys.readouterr().out
    assert "Started. Scanning and updating rows..." in output
    progress_lines = [
        line for line in output.splitlines()
        if line.startswith("  ") and "updated=" in line
    ]
    assert len(progress_lines) == 2
    assert "updated=1" in progress_lines[0]
    assert "updated=2" in progress_lines[1]


def test_interrupt_exits_130_and_records_restart_from_beginning(tmp_path, monkeypatch, capsys):
    table = InterruptingTable(pages=[{
        "Items": [{"reach_id": "1", "range_start_time": "t1", "status": "old"}],
        "ScannedCount": 1,
    }])

    assert invoke(tmp_path, ["status=new"], table, monkeypatch) == 130
    captured = capsys.readouterr()
    assert "Interrupted." in captured.err
    assert "Done." not in captured.out
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Status: INTERRUPTED" in log
    assert "Resume: omit --start-key (restart from the beginning)" in log


def test_interrupt_accounts_for_other_in_flight_result(tmp_path, monkeypatch):
    table = InterruptDrainTable(pages=[{
        "Items": [
            {"reach_id": "1", "range_start_time": "t1", "status": "old"},
            {"reach_id": "2", "range_start_time": "t2", "status": "old"},
        ],
        "ScannedCount": 2,
    }])

    assert invoke(tmp_path, ["status=new", "--workers", "2"], table, monkeypatch) == 130
    assert len(table.update_calls) == 2
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Status: INTERRUPTED" in log
    assert "Rows updated: 1" in log


def test_limit_is_safe_and_distinguishes_read_from_examined(tmp_path, monkeypatch):
    table = FakeTable(pages=[{
        "Items": [
            {"reach_id": "1", "range_start_time": "t1", "status": "old"},
            {"reach_id": "2", "range_start_time": "t2", "status": "old"},
        ],
        "ScannedCount": 2,
    }])

    assert invoke(tmp_path, ["status=new", "--limit", "1"], table, monkeypatch) == 0
    assert len(table.update_calls) == 1
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Status: LIMITED" in log
    assert "Rows read: 2" in log
    assert "Rows examined: 1" in log
    assert "Resume: omit --start-key (restart from the beginning)" in log


def test_limited_run_emits_resume_key_that_resumes_the_scan(tmp_path, monkeypatch):
    checkpoint = {"reach_id": "2", "range_start_time": "t2"}
    pages = [
        {
            "Items": [
                {"reach_id": "1", "range_start_time": "t1", "status": "old"},
                {"reach_id": "2", "range_start_time": "t2", "status": "old"},
            ],
            "ScannedCount": 2,
            "LastEvaluatedKey": checkpoint,
        },
        {
            "Items": [{"reach_id": "3", "range_start_time": "t3", "status": "old"}],
            "ScannedCount": 1,
        },
    ]

    # First run: limit is reached at the end of the first page. It must stop without
    # paying to fetch the second page and use the first page's LastEvaluatedKey.
    first = FakeTable(pages=pages)
    assert invoke(tmp_path, ["status=new", "--limit", "2"], first, monkeypatch) == 0
    assert len(first.update_calls) == 2
    assert len(first.scan_calls) == 1
    resume_arg = json.dumps(checkpoint, separators=(",", ":"))
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Status: LIMITED" in log
    assert f"--start-key '{resume_arg}'" in log

    # Second run: feed that resume key back in; the first scan must use it as ExclusiveStartKey
    # so the already-processed first page is skipped.
    resumed = FakeTable(pages=[
        {"Items": [{"reach_id": "3", "range_start_time": "t3", "status": "old"}], "ScannedCount": 1},
    ])
    assert invoke(tmp_path, ["status=new", "--start-key", resume_arg], resumed, monkeypatch) == 0
    assert resumed.scan_calls[0]["ExclusiveStartKey"] == checkpoint
    assert len(resumed.update_calls) == 1


def test_max_rows_read_caps_scan_and_emits_resume_key(tmp_path, monkeypatch):
    checkpoint = {"reach_id": "2", "range_start_time": "t2"}
    table = FakeTable(pages=[{
        "Items": [
            {"reach_id": "1", "range_start_time": "t1", "status": "old"},
            {"reach_id": "2", "range_start_time": "t2", "status": "old"},
        ],
        "ScannedCount": 2,
        "LastEvaluatedKey": checkpoint,
    }])

    assert invoke(tmp_path, ["status=new", "--max-rows-read", "2"], table, monkeypatch) == 0
    assert len(table.scan_calls) == 1
    assert table.scan_calls[0]["Limit"] == 2
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Status: READ_LIMITED" in log
    assert "Maximum rows read: 2" in log
    assert f"--start-key '{json.dumps(checkpoint, separators=(',', ':'))}'" in log


def test_bounded_run_with_row_error_fails_and_restarts_from_original_key(tmp_path, monkeypatch):
    checkpoint = {"reach_id": "2", "range_start_time": "t2"}
    error = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "temporary failure"}},
        "UpdateItem",
    )
    table = FakeTable(
        pages=[{
            "Items": [
                {"reach_id": "1", "range_start_time": "t1", "status": "old"},
                {"reach_id": "2", "range_start_time": "t2", "status": "old"},
            ],
            "ScannedCount": 2,
            "LastEvaluatedKey": checkpoint,
        }],
        update_error=error,
    )

    assert invoke(
        tmp_path, ["status=new", "--max-rows-read", "2"],
        table, monkeypatch,
    ) == 1
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Status: FAILED" in log
    assert "Resume: omit --start-key (restart from the beginning)" in log


def test_reported_capacity_is_totaled_for_table_and_gsi(tmp_path, monkeypatch):
    table = FakeTable(
        pages=[{
            "Items": [{"reach_id": "1", "range_start_time": "t1", "status": "old"}],
            "ScannedCount": 1,
            "ConsumedCapacity": {
                "CapacityUnits": 0.5,
                "Table": {"CapacityUnits": 0.5},
            },
        }],
        update_response={
            "ConsumedCapacity": {
                "CapacityUnits": 3.0,
                "Table": {"CapacityUnits": 2.0},
                "GlobalSecondaryIndexes": {"GranuleURIndex": {"CapacityUnits": 1.0}},
            }
        },
    )

    assert invoke(tmp_path, ["status=new"], table, monkeypatch) == 0
    assert table.scan_calls[0]["ReturnConsumedCapacity"] == "INDEXES"
    assert table.update_calls[0]["ReturnConsumedCapacity"] == "INDEXES"
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Reported read capacity units: 0.500" in log
    assert "Reported write capacity units: 3.000" in log
    assert "Reported base-table write units: 2.000" in log
    assert "Reported GSI write units: 1.000" in log


def test_row_error_is_quoted_aborts_wave_and_exits_nonzero(tmp_path, monkeypatch):
    error = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "deleted, concurrently\nretry"}},
        "UpdateItem",
    )
    table = FakeTable(
        pages=[{
            "Items": [{"reach_id": "1", "range_start_time": "t1", "status": "old"}],
            "ScannedCount": 1,
        }],
        update_error=error,
    )

    assert invoke(tmp_path, ["status=new"], table, monkeypatch) == 1
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Status: FAILED" in log
    assert "aborted after 1 row update error(s) in the current worker wave" in log
    with one_output(tmp_path, "errors.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[1] == ["1", "t1", "deleted, concurrently\nretry"]


def test_row_error_stops_before_submitting_another_worker_wave(tmp_path, monkeypatch):
    error = ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "failure"}},
        "UpdateItem",
    )
    items = [
        {"reach_id": str(index), "range_start_time": f"t{index}", "status": "old"}
        for index in range(1, 9)
    ]
    table = FakeTable(
        pages=[{"Items": items, "ScannedCount": len(items)}],
        update_error=error,
    )

    assert invoke(
        tmp_path, ["status=new", "--workers", "3"],
        table, monkeypatch,
    ) == 1
    assert len(table.update_calls) == 3
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Errors: 3" in log
    with one_output(tmp_path, "errors.csv").open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.reader(handle))) == 4


def test_unexpected_worker_exception_is_counted_and_logged(tmp_path, monkeypatch):
    table = FakeTable(
        pages=[{
            "Items": [{"reach_id": "1", "range_start_time": "t1", "status": "old"}],
            "ScannedCount": 1,
        }],
        update_error=RuntimeError("worker broke"),
    )

    assert invoke(tmp_path, ["status=new"], table, monkeypatch) == 1
    log = one_output(tmp_path, "log.txt").read_text(encoding="utf-8")
    assert "Errors: 1" in log
    with one_output(tmp_path, "errors.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[1] == ["1", "t1", "RuntimeError: worker broke"]


def test_scan_failure_exits_nonzero_and_does_not_print_done(tmp_path, monkeypatch, capsys):
    table = FakeTable(scan_error=RuntimeError("scan unavailable"))

    assert invoke(tmp_path, ["status=new"], table, monkeypatch) == 1
    captured = capsys.readouterr()
    assert "scan unavailable" in captured.err
    assert "Done." not in captured.out
    assert "Status: FAILED" in one_output(tmp_path, "log.txt").read_text(encoding="utf-8")


def test_key_target_is_rejected_before_scan(tmp_path, monkeypatch):
    table = FakeTable()

    assert invoke(tmp_path, ["reach_id=new"], table, monkeypatch) == 1
    assert table.scan_calls == []


def test_timestamped_outputs_do_not_overwrite_previous_runs(tmp_path, monkeypatch):
    table = FakeTable()
    install_fake_session(monkeypatch, table)
    args = ["test-table", "status=new", "--output-dir", str(tmp_path), "--dry-run", "--yes"]

    assert bulk.main(args) == 0
    table.scan_calls.clear()
    assert bulk.main(args) == 0
    assert len(list(Path(tmp_path).glob("test-table_*_log.txt"))) == 2
    assert len(list(Path(tmp_path).glob("test-table_*_dry_run.csv"))) == 2
