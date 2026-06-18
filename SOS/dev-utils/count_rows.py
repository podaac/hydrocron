#!/usr/bin/env python3
"""CLI to count rows in a DynamoDB table, optionally filtered by reach_id.

Usage:
    python SOS/dev-utils/count_rows.py <table_name> --profile <aws_profile> [--reach-id <id>]

Examples:
    python SOS/dev-utils/count_rows.py hydrocron-swot-reach-table --profile podaac-services-uat
    python SOS/dev-utils/count_rows.py hydrocron-swot-reach-table --profile podaac-services-uat --reach-id 18180900091
"""
import argparse
import sys

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config


def count_rows(table) -> int:
    """Full scan count of all items in the table."""
    count = 0
    kwargs = {"Select": "COUNT"}

    while True:
        response = table.scan(**kwargs)
        count += response["Count"]

        if "LastEvaluatedKey" not in response:
            break
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    return count


def count_rows_for_reach(table, reach_id: str) -> int:
    """Query count of all items for a specific reach_id."""
    count = 0
    kwargs = {
        "KeyConditionExpression": Key("reach_id").eq(reach_id),
        "Select": "COUNT",
    }

    while True:
        response = table.query(**kwargs)
        count += response["Count"]

        if "LastEvaluatedKey" not in response:
            break
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    return count


def main():
    """Parse arguments and count rows in the specified DynamoDB table."""
    parser = argparse.ArgumentParser(description="Count rows in a DynamoDB table.")
    parser.add_argument("table_name", help="DynamoDB table name")
    parser.add_argument("--reach-id", default=None, help="Optional reach_id to count rows for")
    parser.add_argument("--profile", required=True, help="AWS profile (from ~/.aws/credentials)")
    parser.add_argument("--region", default="us-west-2", help="AWS region (default: us-west-2)")
    parser.add_argument("--estimate", action="store_true", help="Use table metadata estimate (fast, ~6hr lag)")
    args = parser.parse_args()

    config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    dynamodb = session.resource("dynamodb", config=config)
    table = dynamodb.Table(args.table_name)

    if args.estimate:
        table.reload()
        print(f"{args.table_name}: ~{table.item_count:,} rows (estimated, up to 6hr lag)")
        sys.exit(0)

    if args.reach_id:
        print(f"Counting rows in {args.table_name} for reach_id={args.reach_id} ...")
        total = count_rows_for_reach(table, args.reach_id)
        print(f"{args.table_name} [reach_id={args.reach_id}]: {total:,} rows")
    else:
        print(f"Counting rows in {args.table_name} (full scan, may take a while) ...")
        total = count_rows(table)
        print(f"{args.table_name}: {total:,} rows")


if __name__ == "__main__":
    main()
