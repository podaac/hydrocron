#!/usr/bin/env python3
"""CLI to query a DynamoDB reach and display columns/values per time step.

Usage:
    python SOS/dev-utils/query_reach.py <table_name> <reach_id> --profile <aws_profile>

Examples:
    python SOS/dev-utils/query_reach.py hydrocron-swot-reach-table 18180900091 --profile podaac-services-ops
"""
import argparse
import re
import sys
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config

FILL_VALUE_TIME = -999999999999.0

SKIP_COLUMNS = {"geometry"}

HEADER_COLUMNS = ["reach_id", "time_str", "cycle_id", "pass_id", "range_start_time"]

RST_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def query_reach(table, reach_id: str) -> list[dict]:
    """Query all rows for a reach_id with pagination. Filters fill-value rows."""
    response = table.query(KeyConditionExpression=Key("reach_id").eq(reach_id))
    items = response["Items"]
    while "LastEvaluatedKey" in response:
        response = table.query(
            KeyConditionExpression=Key("reach_id").eq(reach_id),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response["Items"])
    return [item for item in items if float(item.get("time", 0)) != FILL_VALUE_TIME]


def format_value(val) -> str:
    """Format a DynamoDB value for compact display."""
    if isinstance(val, Decimal):
        if val == int(val):
            return str(int(val))
        return f"{float(val):.6g}"
    if isinstance(val, str) and len(val) > 60:
        return val[:57] + "..."
    return str(val)


def print_timestep(item: dict, index: int, total: int):
    """Print a single time step in compact columnar format."""
    time_str = item.get("time_str", "?")
    cycle = item.get("cycle_id", "?")
    pass_id = item.get("pass_id", "?")

    print(f"\n{'─' * 70}")
    print(f"  [{index}/{total}]  time_str={time_str}  cycle={cycle}  pass={pass_id}")
    print(f"{'─' * 70}")

    cols = sorted(k for k in item.keys() if k not in SKIP_COLUMNS)

    max_name_len = max((len(c) for c in cols), default=0)

    for col in cols:
        val = format_value(item[col])
        print(f"  {col:<{max_name_len}}  {val}")


def main():
    """Parse arguments and display time-series data for a single reach."""
    parser = argparse.ArgumentParser(description="Query a DynamoDB reach and display time-series data.")
    parser.add_argument("table_name", help="DynamoDB table name")
    parser.add_argument("reach_id", help="Reach ID to query")
    parser.add_argument("--profile", required=True, help="AWS profile (from ~/.aws/credentials)")
    parser.add_argument("--region", default="us-west-2", help="AWS region (default: us-west-2)")
    parser.add_argument("--limit", type=int, default=None, help="Max time steps to display")
    parser.add_argument("--columns", nargs="+", help="Only show these columns")
    args = parser.parse_args()

    config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    dynamodb = session.resource("dynamodb", config=config)
    table = dynamodb.Table(args.table_name)

    print(f"Querying {args.table_name} for reach_id={args.reach_id} ...")
    items = query_reach(table, args.reach_id)

    if not items:
        print("No items found.")
        sys.exit(0)

    items.sort(key=lambda x: x.get("range_start_time", ""))

    bad_rst = [item for item in items if not RST_PATTERN.match(str(item.get("range_start_time", "")))]
    if bad_rst:
        print(f"\n  WARNING: {len(bad_rst)} row(s) with invalid range_start_time:")
        for item in bad_rst:
            print(f"    reach_id={item.get('reach_id')}  range_start_time={item.get('range_start_time')!r}")
        print()

    if args.limit:
        items = items[: args.limit]

    print(f"Found {len(items)} time step(s)")

    for i, item in enumerate(items, 1):
        if args.columns:
            item = {k: v for k, v in item.items() if k in args.columns or k in HEADER_COLUMNS}
        print_timestep(item, i, len(items))

    print()


if __name__ == "__main__":
    main()
