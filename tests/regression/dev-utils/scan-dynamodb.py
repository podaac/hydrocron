"""
Scan DynamoDB tables and compare old vs new "D" table schemas.

This script:
1. Connects to DynamoDB using the current AWS_PROFILE
2. Lists all DynamoDB tables starting with "hydro" (excludes ingest tables)
3. Scans 6 main tables (3 old + 3 new D versions) to collect column names
4. Pairs up tables by feature type (reach, node, prior-lake)
5. For each pair, displays:
   - OLD table columns with ❌ marking removed columns
   - NEW D table columns with ✨ marking new columns
   - Summary showing what changed between versions

Usage:
    AWS_PROFILE=myprofile poetry run python tests/regression/scan-dynamodb.py
"""

import sys
import os
from collections import defaultdict
import boto3
from botocore.exceptions import ClientError


def get_table_attributes(table):
    """
    Scan a DynamoDB table and collect all unique attribute names.

    Parameters
    ----------
    table : boto3.resources.base.ServiceResource
        DynamoDB table resource

    Returns
    -------
    set
        Set of all attribute names found in the table
    """
    attributes = set()

    try:
        # Scan just a few items to get column names (Limit=10)
        response = table.scan(Limit=10)

        # Collect attributes from items
        items = response.get('Items', [])

        for item in items:
            attributes.update(item.keys())

        if len(items) == 0:
            print(f"  ⚠️  Table appears to be empty!")

    except ClientError as e:
        print(f"  ❌ Error scanning table: {e}")
        return set()
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return set()

    return attributes


def categorize_tables(table_names):
    """
    Categorize tables into old and new versions by feature type.
    Excludes track-ingest tables.

    Parameters
    ----------
    table_names : list
        List of table names

    Returns
    -------
    dict
        Dictionary with keys 'reach', 'node', 'prior-lake' and values being
        dicts with 'old' and 'new' table names
    """
    categories = {
        'reach': {'old': None, 'new': None},
        'node': {'old': None, 'new': None},
        'prior-lake': {'old': None, 'new': None}
    }

    for name in table_names:
        # Skip ingest tables
        if 'ingest' in name.lower():
            continue

        # Reach tables
        if 'reach' in name.lower():
            if '_D-reach-table' in name:
                categories['reach']['new'] = name
            elif 'swot-reach-table' in name:
                categories['reach']['old'] = name

        # Node tables
        elif 'node' in name.lower():
            if '_D-node-table' in name:
                categories['node']['new'] = name
            elif 'swot-node-table' in name:
                categories['node']['old'] = name

        # Prior lake tables
        elif 'lake' in name.lower():
            if '_D-prior-lake-table' in name:
                categories['prior-lake']['new'] = name
            elif 'swot-prior-lake-table' in name:
                categories['prior-lake']['old'] = name

    return categories


def display_table_pair(old_attrs, new_attrs, old_name, new_name):
    """
    Display column comparison for a pair of old and new tables.

    Parameters
    ----------
    old_attrs : set
        Attributes from old table
    new_attrs : set
        Attributes from new table
    old_name : str
        Name of old table
    new_name : str
        Name of new table
    """
    only_in_old = old_attrs - new_attrs
    only_in_new = new_attrs - old_attrs
    in_both = old_attrs & new_attrs

    print(f"\n{'='*80}")
    print(f"PAIR: {old_name.split('-')[-2].upper()}")
    print(f"{'='*80}")

    # OLD TABLE
    print(f"\n📊 OLD TABLE: {old_name}")
    print(f"   Total columns: {len(old_attrs)}")
    print(f"\n   Columns:")
    for attr in sorted(old_attrs):
        if attr in only_in_old:
            print(f"   ❌ {attr}  [REMOVED in new table]")
        else:
            print(f"      {attr}")

    # NEW TABLE
    print(f"\n📊 NEW TABLE: {new_name}")
    print(f"   Total columns: {len(new_attrs)}")
    print(f"\n   Columns:")
    for attr in sorted(new_attrs):
        if attr in only_in_new:
            print(f"   ✨ {attr}  [NEW in this table]")
        else:
            print(f"      {attr}")

    # SUMMARY
    print(f"\n📈 SUMMARY:")
    print(f"   Columns in both tables: {len(in_both)}")
    print(f"   Columns removed (in old only): {len(only_in_old)}")
    print(f"   Columns added (in new only): {len(only_in_new)}")

    if only_in_old:
        print(f"\n   ❌ REMOVED COLUMNS:")
        for attr in sorted(only_in_old):
            print(f"      - {attr}")

    if only_in_new:
        print(f"\n   ✨ NEW COLUMNS:")
        for attr in sorted(only_in_new):
            print(f"      - {attr}")


def main():
    """Main function to scan and compare DynamoDB tables."""
    print("Hydrocron DynamoDB Table Scanner")
    print("=" * 80)

    # Show environment info
    aws_profile = os.getenv('AWS_PROFILE', 'default')
    aws_region = os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION', 'us-west-2'))
    print(f"\nAWS Profile: {aws_profile}")
    print(f"AWS Region: {aws_region}")

    # Connect to DynamoDB using the current AWS profile
    try:
        session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
        dynamodb = session.resource('dynamodb')
        client = dynamodb.meta.client
        print("✓ Successfully connected to DynamoDB")
    except Exception as e:
        print(f"❌ Error connecting to DynamoDB: {e}")
        sys.exit(1)

    # List all tables starting with "hydro"
    print("\nListing tables starting with 'hydro'...")
    try:
        response = client.list_tables()
        all_tables = response.get('TableNames', [])

        # Handle pagination
        while 'LastEvaluatedTableName' in response:
            response = client.list_tables(
                ExclusiveStartTableName=response['LastEvaluatedTableName']
            )
            all_tables.extend(response.get('TableNames', []))

        # Filter tables starting with "hydro" and exclude ingest tables
        all_hydro_tables = [t for t in all_tables if t.startswith('hydro')]
        hydro_tables = [t for t in all_hydro_tables if 'ingest' not in t.lower()]

        print(f"\nFound {len(all_hydro_tables)} total hydro tables")
        print(f"Analyzing {len(hydro_tables)} tables (excluding {len(all_hydro_tables) - len(hydro_tables)} ingest tables):")
        for table_name in sorted(hydro_tables):
            print(f"  - {table_name}")

        if len(hydro_tables) != 6:
            print(f"\n⚠️  Warning: Expected 6 non-ingest tables, but found {len(hydro_tables)}")

    except ClientError as e:
        print(f"Error listing tables: {e}")
        sys.exit(1)

    # Get attributes for each table
    print(f"\n{'='*80}")
    print("SCANNING TABLES FOR COLUMN NAMES")
    print(f"{'='*80}")

    table_attributes = {}
    for table_name in sorted(hydro_tables):
        print(f"\n  Scanning: {table_name}...", end=" ")
        table = dynamodb.Table(table_name)
        attrs = get_table_attributes(table)
        table_attributes[table_name] = attrs
        print(f"✓ ({len(attrs)} columns)")

    # Categorize tables into pairs
    categories = categorize_tables(hydro_tables)

    # Display each pair with comparisons
    print(f"\n{'='*80}")
    print("TABLE PAIR COMPARISONS")
    print(f"{'='*80}")

    for feature_type in ['reach', 'node', 'prior-lake']:
        tables = categories[feature_type]
        if tables['old'] and tables['new']:
            old_attrs = table_attributes[tables['old']]
            new_attrs = table_attributes[tables['new']]
            display_table_pair(
                old_attrs, new_attrs,
                tables['old'], tables['new']
            )
        elif tables['old']:
            print(f"\n⚠️  Only found old {feature_type} table: {tables['old']}")
        elif tables['new']:
            print(f"\n⚠️  Only found new {feature_type} table: {tables['new']}")

    print(f"\n{'='*80}")
    print("SCAN COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
