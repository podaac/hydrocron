#!/usr/bin/env python3
"""CLI to list all reach_ids between a start and end reach_id.

Usage:
    python SOS/utils/list_reaches.py <start_reach_id> <end_reach_id> [--profile <aws_profile>]

Examples:
    python SOS/utils/list_reaches.py 18180900091 18180900095
    python SOS/utils/list_reaches.py 18180900091 18180900095 --profile podaac-services-uat
"""
import argparse

import boto3
from botocore.config import Config

TABLE_NAME = "hydrocron-swot-reach-table"


def list_reach_ids(table, start_id: str, end_id: str) -> list[str]:
    """Scan for all unique reach_ids between start and end (inclusive)."""
    reach_ids = set()
    kwargs = {
        "ProjectionExpression": "reach_id",
        "FilterExpression": "reach_id BETWEEN :start AND :end",
        "ExpressionAttributeValues": {":start": start_id, ":end": end_id},
    }

    while True:
        response = table.scan(**kwargs)
        for item in response.get("Items", []):
            reach_ids.add(item["reach_id"])

        if "LastEvaluatedKey" not in response:
            break
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    return sorted(reach_ids)


def main():
    parser = argparse.ArgumentParser(description="List reach_ids between a start and end range.")
    parser.add_argument("start_reach_id", help="Start reach_id (inclusive)")
    parser.add_argument("end_reach_id", help="End reach_id (inclusive)")
    parser.add_argument("--profile", default="podaac-services-ops", help="AWS profile (default: podaac-services-ops)")
    parser.add_argument("--region", default="us-west-2", help="AWS region (default: us-west-2)")
    parser.add_argument("--table", default=TABLE_NAME, help=f"DynamoDB table name (default: {TABLE_NAME})")
    args = parser.parse_args()

    config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    dynamodb = session.resource("dynamodb", config=config)
    table = dynamodb.Table(args.table)

    print(f"Scanning {args.table} for reach_ids between {args.start_reach_id} and {args.end_reach_id} ...")

    reach_ids = list_reach_ids(table, args.start_reach_id, args.end_reach_id)

    if not reach_ids:
        print("No reach_ids found in that range.")
        return

    print(f"\nFound {len(reach_ids)} unique reach_id(s):\n")
    for rid in reach_ids:
        print(f"  {rid}")
    print()


if __name__ == "__main__":
    main()
