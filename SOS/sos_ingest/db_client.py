"""DynamoDB query and update operations for SOS ingest."""
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)

FILL_VALUE_TIME = -999999999999.0


class SosDbClient:
    """Wraps DynamoDB query and update operations for the reach table."""

    def __init__(self, table_name: str, dry_run: bool, aws_profile: str | None):
        config = Config(retries={"max_attempts": 5, "mode": "adaptive"})
        session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
        self._resource = session.resource("dynamodb", config=config)
        self._table = self._resource.Table(table_name)
        self._table_name = table_name
        self._dry_run = dry_run

    def query_reach(self, reach_id: str) -> list[dict]:
        """Query all rows for a reach_id. Handles pagination. Filters fill-value rows."""
        response = self._table.query(
            KeyConditionExpression=Key("reach_id").eq(reach_id)
        )
        items = response["Items"]

        while "LastEvaluatedKey" in response:
            response = self._table.query(
                KeyConditionExpression=Key("reach_id").eq(reach_id),
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response["Items"])

        return [item for item in items if float(item.get("time", 0)) != FILL_VALUE_TIME]

    def update_row(self, reach_id: str, range_start_time: str, column_updates: dict[str, str]) -> bool:
        """Update an existing row with new SOS discharge columns. Returns True on success."""
        if self._dry_run:
            logger.debug("DRY RUN: would update %s/%s with %d columns", reach_id, range_start_time, len(column_updates))
            return True

        set_parts = [f"#col_{i} = :val_{i}" for i in range(len(column_updates))]
        expr_names = {f"#col_{i}": k for i, k in enumerate(column_updates)}
        expr_values = {f":val_{i}": v for i, v in enumerate(column_updates.values())}

        try:
            self._table.update_item(
                Key={"reach_id": reach_id, "range_start_time": range_start_time},
                UpdateExpression=f"SET {', '.join(set_parts)}",
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
            )
            return True
        except ClientError as e:
            logger.error("DynamoDB update failed for %s/%s: %s", reach_id, range_start_time, e.response["Error"]["Message"])
            return False
