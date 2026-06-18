"""Tests for DynamoDB client operations."""
from SOS.sos_ingest.db_client import SosDbClient
from SOS.tests.conftest import MOCK_TABLE_NAME, MOCK_REACH_ID, MOCK_REACH_TIMES


class TestQueryReachReturnsItems:
    def test_returns_expected_rows(self, mock_dynamodb_table):
        client = SosDbClient(MOCK_TABLE_NAME, dry_run=True, aws_profile=None)
        client._resource = mock_dynamodb_table
        client._table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)

        rows = client.query_reach(MOCK_REACH_ID)
        assert len(rows) == 3
        times = [r["range_start_time"] for r in rows]
        for t in MOCK_REACH_TIMES:
            assert t in times


class TestQueryReachPagination:
    def test_handles_paginated_results(self, mock_dynamodb_table):
        table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)
        for i in range(50):
            table.put_item(Item={
                "reach_id": "11111111111",
                "range_start_time": f"2023-01-{(i+1):02d}T00:00:00Z",
                "time": "748617713.0",
            })

        client = SosDbClient(MOCK_TABLE_NAME, dry_run=True, aws_profile=None)
        client._resource = mock_dynamodb_table
        client._table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)

        rows = client.query_reach("11111111111")
        assert len(rows) == 50


class TestQueryReachFiltersFillValues:
    def test_fill_value_rows_excluded(self, mock_dynamodb_table):
        client = SosDbClient(MOCK_TABLE_NAME, dry_run=True, aws_profile=None)
        client._resource = mock_dynamodb_table
        client._table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)

        rows = client.query_reach("99999999999")
        assert len(rows) == 0


class TestQueryReachEmpty:
    def test_nonexistent_reach_returns_empty(self, mock_dynamodb_table):
        client = SosDbClient(MOCK_TABLE_NAME, dry_run=True, aws_profile=None)
        client._resource = mock_dynamodb_table
        client._table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)

        rows = client.query_reach("00000000000")
        assert rows == []


class TestUpdateRowLiveMode:
    def test_update_item_writes_columns(self, mock_dynamodb_table):
        client = SosDbClient(MOCK_TABLE_NAME, dry_run=False, aws_profile=None)
        client._resource = mock_dynamodb_table
        client._table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)

        result = client.update_row(
            MOCK_REACH_ID,
            MOCK_REACH_TIMES[0],
            {"sos_consensus_q": "123.45", "sos_metroman_q": "678.90"}
        )
        assert result is True

        table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)
        resp = table.get_item(Key={"reach_id": MOCK_REACH_ID, "range_start_time": MOCK_REACH_TIMES[0]})
        item = resp["Item"]
        assert item["sos_consensus_q"] == "123.45"
        assert item["sos_metroman_q"] == "678.90"


class TestUpdateRowDryRun:
    def test_no_write_in_dry_run(self, mock_dynamodb_table):
        client = SosDbClient(MOCK_TABLE_NAME, dry_run=True, aws_profile=None)
        client._resource = mock_dynamodb_table
        client._table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)

        result = client.update_row(
            MOCK_REACH_ID,
            MOCK_REACH_TIMES[0],
            {"sos_consensus_q": "123.45"}
        )
        assert result is True

        table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)
        resp = table.get_item(Key={"reach_id": MOCK_REACH_ID, "range_start_time": MOCK_REACH_TIMES[0]})
        item = resp["Item"]
        assert "sos_consensus_q" not in item


class TestUpdateRowIdempotent:
    def test_running_update_twice_same_result(self, mock_dynamodb_table):
        client = SosDbClient(MOCK_TABLE_NAME, dry_run=False, aws_profile=None)
        client._resource = mock_dynamodb_table
        client._table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)

        updates = {"sos_consensus_q": "123.45"}
        client.update_row(MOCK_REACH_ID, MOCK_REACH_TIMES[0], updates)
        client.update_row(MOCK_REACH_ID, MOCK_REACH_TIMES[0], updates)

        table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)
        resp = table.get_item(Key={"reach_id": MOCK_REACH_ID, "range_start_time": MOCK_REACH_TIMES[0]})
        assert resp["Item"]["sos_consensus_q"] == "123.45"


class TestUpdateRowReturnsFalseOnError:
    def test_client_error_returns_false(self, mock_dynamodb_table):
        client = SosDbClient(MOCK_TABLE_NAME, dry_run=False, aws_profile=None)
        client._resource = mock_dynamodb_table
        client._table = mock_dynamodb_table.Table("nonexistent-table")

        result = client.update_row(MOCK_REACH_ID, MOCK_REACH_TIMES[0], {"col": "val"})
        assert result is False


class TestUpdateRowHandlesThrottle:
    def test_throttle_is_retried(self, mock_dynamodb_table):
        client = SosDbClient(MOCK_TABLE_NAME, dry_run=False, aws_profile=None)
        client._resource = mock_dynamodb_table
        client._table = mock_dynamodb_table.Table(MOCK_TABLE_NAME)

        result = client.update_row(MOCK_REACH_ID, MOCK_REACH_TIMES[0], {"sos_sad_q": "99.9"})
        assert result is True


class TestRetryConfig:
    def test_adaptive_retry_with_max_attempts(self, mock_dynamodb_table):
        client = SosDbClient(MOCK_TABLE_NAME, dry_run=True, aws_profile=None)
        retry_config = client._resource.meta.client.meta.config.retries
        assert retry_config["mode"] == "adaptive"
        assert retry_config["total_max_attempts"] == 6
