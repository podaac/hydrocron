#!/usr/bin/env python3
"""CLI to count rows with fill/sentinel range_start_time or time values.

Since range_start_time is a sort key it can't be null, but rows may have
sentinel time values (e.g. -999999999999) indicating fill data. This script
scans the table and reports:
  1. Rows where time == fill value (-999999999999)
  2. Any unusual range_start_time values found (samples first to detect patterns)

Usage:
    python SOS/dev-utils/count_fill_rows.py <table_name> --profile <aws_profile>

Examples:
    python SOS/dev-utils/count_fill_rows.py hydrocron-swot-reach-table --profile podaac-services-uat
"""
import argparse
import sys
from collections import Counter
from decimal import Decimal

import boto3
from botocore.config import Config

FILL_VALUES_TIME = {
    Decimal("-999999999999"),
    Decimal("-99999999"),
    Decimal("-999"),
}

EXPECTED_RST_PATTERN_LEN = 20  # "2024-07-13T11:18:16Z"


def is_anomalous_rst(val: str) -> bool:
    """Check if a range_start_time value looks anomalous."""
    if not val:
        return True
    if len(val) != EXPECTED_RST_PATTERN_LEN:
        return True
    if not val.endswith("Z"):
        return True
    if val.startswith("-") or val.startswith("0000"):
        return True
    return False


def scan_and_count(table) -> dict:
    """Full scan counting fill rows and anomalous range_start_time values."""
    stats = {
        "total": 0,
        "fill_time": 0,
        "anomalous_rst": 0,
        "rst_samples": Counter(),
        "fill_time_rst_values": Counter(),
    }
    kwargs = {"Limit": 1000}

    while True:
        response = table.scan(**kwargs)
        items = response.get("Items", [])
        stats["total"] += len(items)

        for item in items:
            time_val = item.get("time")
            rst_val = item.get("range_start_time", "")

            if time_val is not None and Decimal(str(time_val)) in FILL_VALUES_TIME:
                stats["fill_time"] += 1
                stats["fill_time_rst_values"][rst_val] += 1

            if is_anomalous_rst(str(rst_val)):
                stats["anomalous_rst"] += 1
                if len(stats["rst_samples"]) < 20:
                    stats["rst_samples"][str(rst_val)] += 1

        if "LastEvaluatedKey" not in response:
            break
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        kwargs["Limit"] = 1000

        if stats["total"] % 50000 == 0:
            print(f"  ... scanned {stats['total']:,} rows so far "
                  f"(fill_time={stats['fill_time']:,}, anomalous_rst={stats['anomalous_rst']:,})")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Count rows with fill/sentinel values.")
    parser.add_argument("table_name", help="DynamoDB table name")
    parser.add_argument("--profile", required=True, help="AWS profile (from ~/.aws/credentials)")
    parser.add_argument("--region", default="us-west-2", help="AWS region (default: us-west-2)")
    args = parser.parse_args()

    config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    dynamodb = session.resource("dynamodb", config=config)
    table = dynamodb.Table(args.table_name)

    print(f"Scanning {args.table_name} for fill/sentinel rows ...")
    print(f"  Known fill values for 'time': {sorted(float(v) for v in FILL_VALUES_TIME)}")
    print()

    stats = scan_and_count(table)

    print(f"\n{'═' * 60}")
    print(f"  RESULTS: {args.table_name}")
    print(f"{'═' * 60}")
    print(f"  Total rows scanned:           {stats['total']:,}")
    print(f"  Rows with fill 'time' value:  {stats['fill_time']:,}")
    print(f"  Rows with anomalous RST:      {stats['anomalous_rst']:,}")

    if stats["fill_time_rst_values"]:
        print(f"\n  range_start_time values on fill rows (top 10):")
        for rst, count in stats["fill_time_rst_values"].most_common(10):
            print(f"    {rst!r:30s}  ({count:,} rows)")

    if stats["rst_samples"]:
        print(f"\n  Anomalous range_start_time samples:")
        for rst, count in stats["rst_samples"].most_common(20):
            print(f"    {rst!r:30s}  ({count:,} rows)")

    pct_fill = (stats["fill_time"] / stats["total"] * 100) if stats["total"] else 0
    print(f"\n  Fill rows = {pct_fill:.2f}% of table")
    print()


if __name__ == "__main__":
    main()
