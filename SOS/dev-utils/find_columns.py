#!/usr/bin/env python3
"""CLI to scan a DynamoDB table for rows containing columns matching a prefix.

Usage:
    python SOS/dev-utils/find_columns.py <table_name> <column_filter> --profile <aws_profile>

Examples:
    python SOS/dev-utils/find_columns.py hydrocron-swot-reach-table sos --profile podaac-services-uat
    python SOS/dev-utils/find_columns.py hydrocron-swot-reach-table dschg_ --profile podaac-services-uat --limit 5
"""
import argparse
import sys
from decimal import Decimal

import boto3
from botocore.config import Config

ID_COLUMNS = ["reach_id", "node_id", "lake_id", "time_str", "range_start_time"]


def format_value(val) -> str:
    """Format a DynamoDB value for compact display."""
    if isinstance(val, Decimal):
        if val == int(val):
            return str(int(val))
        return f"{float(val):.6g}"
    if isinstance(val, str) and len(val) > 60:
        return val[:57] + "..."
    return str(val)


def scan_for_columns(table, prefix: str, max_rows: int, scan_limit: int) -> list[dict]:
    """Scan table and return rows that have at least one column matching the prefix."""
    matched = []
    scanned = 0
    kwargs = {"Limit": min(scan_limit, 1000)}

    while scanned < scan_limit and len(matched) < max_rows:
        response = table.scan(**kwargs)
        items = response.get("Items", [])
        scanned += len(items)

        for item in items:
            matching_cols = [k for k in item.keys() if k.startswith(prefix)]
            if matching_cols:
                matched.append(item)
                if len(matched) >= max_rows:
                    break

        if "LastEvaluatedKey" not in response:
            break
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        kwargs["Limit"] = min(1000, scan_limit - scanned)

    return matched


def print_row(item: dict, prefix: str, index: int):
    """Print a row showing only the ID columns and matching columns."""
    id_parts = []
    for col in ID_COLUMNS:
        if col in item:
            id_parts.append(f"{col}={item[col]}")

    matching = sorted(k for k in item.keys() if k.startswith(prefix))

    print(f"\n{'─' * 70}")
    print(f"  [{index}]  {' | '.join(id_parts)}")
    print(f"{'─' * 70}")

    max_name_len = max((len(c) for c in matching), default=0)
    for col in matching:
        val = format_value(item[col])
        print(f"  {col:<{max_name_len}}  {val}")


def main():
    parser = argparse.ArgumentParser(description="Find rows with columns matching a prefix.")
    parser.add_argument("table_name", help="DynamoDB table name")
    parser.add_argument("column_filter", help="Column name prefix to search for (e.g. 'sos')")
    parser.add_argument("--profile", required=True, help="AWS profile (from ~/.aws/credentials)")
    parser.add_argument("--region", default="us-west-2", help="AWS region (default: us-west-2)")
    parser.add_argument("--limit", type=int, default=10, help="Max rows to display (default: 10)")
    parser.add_argument("--scan-limit", type=int, default=10000, help="Max items to scan before stopping (default: 10000)")
    parser.add_argument("--all-columns", action="store_true", help="Show all columns, not just matching ones")
    args = parser.parse_args()

    config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    dynamodb = session.resource("dynamodb", config=config)
    table = dynamodb.Table(args.table_name)

    prefix = args.column_filter.rstrip("*")

    print(f"Scanning {args.table_name} for columns starting with '{prefix}' ...")
    print(f"  (scan limit: {args.scan_limit} items, display limit: {args.limit} rows)")

    matched = scan_for_columns(table, prefix, args.limit, args.scan_limit)

    if not matched:
        print(f"\nNo rows found with columns starting with '{prefix}' (scanned up to {args.scan_limit} items).")
        sys.exit(0)

    print(f"\nFound {len(matched)} row(s) with '{prefix}*' columns:")

    for i, item in enumerate(matched, 1):
        if args.all_columns:
            matching = sorted(k for k in item.keys() if k != "geometry")
            id_parts = []
            for col in ID_COLUMNS:
                if col in item:
                    id_parts.append(f"{col}={item[col]}")
            print(f"\n{'─' * 70}")
            print(f"  [{i}]  {' | '.join(id_parts)}")
            print(f"{'─' * 70}")
            max_name_len = max((len(c) for c in matching), default=0)
            for col in matching:
                val = format_value(item[col])
                print(f"  {col:<{max_name_len}}  {val}")
        else:
            print_row(item, prefix, i)

    print()


if __name__ == "__main__":
    main()
