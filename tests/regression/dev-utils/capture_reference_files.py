#!/usr/bin/env python3
"""
Capture golden reference files for regression testing

This script queries the deployed API and saves responses as reference files
in the fixtures/ directory. These files are used by regression tests to detect
changes in API responses.

Usage:
    # Capture from UAT environment
    HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py

    # Capture from OPS environment
    HYDROCRON_ENV=ops poetry run python tests/regression/dev-utils/capture_reference_files.py

    # Capture specific feature only
    HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature reach

IMPORTANT:
    - Review captured files before committing to ensure they represent correct API behavior
    - Update reference files when API behavior changes intentionally
    - Don't capture from broken deployments
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.regression.conftest import API_URLS, STABLE_TEST_DATA_UAT, STABLE_TEST_DATA_OPS


def capture_geojson_response(api_url, params, output_file):
    """Capture GeoJSON response"""
    print(f"  Querying API for GeoJSON...")
    response = requests.get(api_url, params=params, timeout=60)

    if response.status_code != 200:
        print(f"    ❌ Failed: {response.status_code} - {response.text[:200]}")
        return False

    data = response.json()

    # Extract geojson from wrapped response if needed
    if 'results' in data and 'geojson' in data['results']:
        data = data['results']['geojson']

    # Save to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    feature_count = len(data.get('features', []))
    print(f"    ✓ Saved {feature_count} features to {output_file}")
    return True


def capture_csv_response(api_url, params, output_file):
    """Capture CSV response"""
    print(f"  Querying API for CSV...")
    response = requests.get(api_url, params=params, timeout=60)

    if response.status_code != 200:
        print(f"    ❌ Failed: {response.status_code} - {response.text[:200]}")
        return False

    # Save to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(response.text)

    line_count = len(response.text.strip().split('\n'))
    print(f"    ✓ Saved {line_count} lines to {output_file}")
    return True


def capture_reach_fixtures(api_url, test_data, fixtures_dir):
    """Capture reach reference files"""
    print("\n📊 Capturing Reach fixtures...")

    reach_data = test_data["reach"]
    fields = reach_data["fields"]

    # Basic GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": fields
        },
        fixtures_dir / "reach" / "reach_basic.geojson"
    )

    # Basic CSV
    capture_csv_response(
        api_url,
        {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": fields
        },
        fixtures_dir / "reach" / "reach_basic.csv"
    )

    # Discharge fields CSV
    capture_csv_response(
        api_url,
        {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "fields": "reach_id,time_str,wse,dschg_c,dschg_c_u,dschg_c_q"
        },
        fixtures_dir / "reach" / "reach_discharge.csv"
    )

    # Comprehensive GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": f"{fields},area_total,collection_shortname,crid,geometry"
        },
        fixtures_dir / "reach" / "reach_comprehensive.geojson"
    )


def capture_reach_d_fixtures(api_url, test_data, fixtures_dir):
    """Capture reach Version D reference files"""
    print("\n📊 Capturing Reach Version D fixtures...")

    reach_data = test_data["reach_d"]
    fields = reach_data["fields"]

    # Basic GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "collection_name": reach_data["collection_name"],
            "fields": fields
        },
        fixtures_dir / "reach" / "reach_d_basic.geojson"
    )

    # Basic CSV
    capture_csv_response(
        api_url,
        {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "collection_name": reach_data["collection_name"],
            "fields": fields
        },
        fixtures_dir / "reach" / "reach_d_basic.csv"
    )

    # Discharge fields CSV
    capture_csv_response(
        api_url,
        {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "csv",
            "collection_name": reach_data["collection_name"],
            "fields": "reach_id,time_str,wse,dschg_c,dschg_c_u,dschg_c_q"
        },
        fixtures_dir / "reach" / "reach_d_discharge.csv"
    )

    # Comprehensive GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "collection_name": reach_data["collection_name"],
            "fields": f"{fields},area_total,collection_shortname,crid,geometry"
        },
        fixtures_dir / "reach" / "reach_d_comprehensive.geojson"
    )


def capture_node_fixtures(api_url, test_data, fixtures_dir):
    """Capture node reference files"""
    print("\n📊 Capturing Node fixtures...")

    node_data = test_data["node"]
    fields = node_data["fields"]

    # Basic GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "fields": fields
        },
        fixtures_dir / "node" / "node_basic.geojson"
    )

    # Basic CSV
    capture_csv_response(
        api_url,
        {
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "csv",
            "fields": fields
        },
        fixtures_dir / "node" / "node_basic.csv"
    )

    # Comprehensive GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "fields": f"{fields},area_total,collection_shortname,crid,geometry"
        },
        fixtures_dir / "node" / "node_comprehensive.geojson"
    )


def capture_node_d_fixtures(api_url, test_data, fixtures_dir):
    """Capture node Version D reference files"""
    print("\n📊 Capturing Node Version D fixtures...")

    node_data = test_data["node_d"]
    fields = node_data["fields"]

    # Strip Version D specific fields for basic captures
    fields_list = [f.strip() for f in fields.split(",")]
    basic_fields = [f for f in fields_list if not f.startswith("wse_sm")]
    basic_fields_str = ",".join(basic_fields)

    # Basic GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "collection_name": node_data["collection_name"],
            "fields": basic_fields_str
        },
        fixtures_dir / "node" / "node_d_basic.geojson"
    )

    # Basic CSV
    capture_csv_response(
        api_url,
        {
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "csv",
            "collection_name": node_data["collection_name"],
            "fields": basic_fields_str
        },
        fixtures_dir / "node" / "node_d_basic.csv"
    )

    # Comprehensive GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "collection_name": node_data["collection_name"],
            "fields": f"{basic_fields_str},area_total,collection_shortname,crid,geometry"
        },
        fixtures_dir / "node" / "node_d_comprehensive.geojson"
    )


def capture_priorlake_fixtures(api_url, test_data, fixtures_dir):
    """Capture prior lake reference files"""
    print("\n📊 Capturing PriorLake fixtures...")

    lake_data = test_data["priorlake"]
    fields = lake_data["fields"]

    # Basic GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": fields
        },
        fixtures_dir / "priorlake" / "lake_basic.geojson"
    )

    # Basic CSV
    capture_csv_response(
        api_url,
        {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "fields": fields
        },
        fixtures_dir / "priorlake" / "lake_basic.csv"
    )

    # Comprehensive GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": f"{fields},geometry"
        },
        fixtures_dir / "priorlake" / "lake_comprehensive.geojson"
    )


def capture_priorlake_d_fixtures(api_url, test_data, fixtures_dir):
    """Capture prior lake Version D reference files"""
    print("\n📊 Capturing PriorLake Version D fixtures...")

    lake_data = test_data["priorlake_d"]
    fields = lake_data["fields"]

    # Strip Version D specific fields for basic captures
    fields_list = [f.strip() for f in fields.split(",")]
    basic_fields = [f for f in fields_list if f != "qual_f_b"]
    basic_fields_str = ",".join(basic_fields)

    # Basic GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "collection_name": lake_data["collection_name"],
            "fields": basic_fields_str
        },
        fixtures_dir / "priorlake" / "lake_d_basic.geojson"
    )

    # Basic CSV
    capture_csv_response(
        api_url,
        {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "collection_name": lake_data["collection_name"],
            "fields": basic_fields_str
        },
        fixtures_dir / "priorlake" / "lake_d_basic.csv"
    )

    # qual_f_b field CSV (Version D specific)
    capture_csv_response(
        api_url,
        {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "csv",
            "collection_name": lake_data["collection_name"],
            "fields": fields
        },
        fixtures_dir / "priorlake" / "lake_d_qual_f_b.csv"
    )

    # Comprehensive GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "collection_name": lake_data["collection_name"],
            "fields": f"{fields},geometry"
        },
        fixtures_dir / "priorlake" / "lake_d_comprehensive.geojson"
    )


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Capture API reference files for regression testing")
    parser.add_argument(
        '--feature',
        choices=['reach', 'node', 'priorlake', 'all'],
        default='all',
        help='Feature type to capture (default: all)'
    )
    args = parser.parse_args()

    # Get environment
    env = os.environ.get("HYDROCRON_ENV", "").lower()
    if env not in API_URLS:
        print(f"❌ Error: HYDROCRON_ENV must be set to 'uat' or 'ops'")
        print(f"   Current value: '{env}'")
        sys.exit(1)

    api_url = API_URLS[env]

    # Get environment-specific test data
    stable_test_data = STABLE_TEST_DATA_UAT if env == "uat" else STABLE_TEST_DATA_OPS

    # Fixtures directory is environment-specific
    fixtures_dir = Path(__file__).parent.parent / "fixtures" / env

    print("=" * 80)
    print("Hydrocron API Reference File Capture")
    print("=" * 80)
    print(f"\nEnvironment: {env.upper()}")
    print(f"API URL: {api_url}")
    print(f"Fixtures directory: {fixtures_dir}")
    print(f"Feature: {args.feature}")

    print("\n⚠️  WARNING: Review captured files before committing!")
    print("   Only capture from a known-good API deployment.\n")

    # Capture based on feature selection
    if args.feature in ['reach', 'all']:
        capture_reach_fixtures(api_url, stable_test_data, fixtures_dir)
        capture_reach_d_fixtures(api_url, stable_test_data, fixtures_dir)

    if args.feature in ['node', 'all']:
        capture_node_fixtures(api_url, stable_test_data, fixtures_dir)
        capture_node_d_fixtures(api_url, stable_test_data, fixtures_dir)

    if args.feature in ['priorlake', 'all']:
        capture_priorlake_fixtures(api_url, stable_test_data, fixtures_dir)
        capture_priorlake_d_fixtures(api_url, stable_test_data, fixtures_dir)

    print("\n" + "=" * 80)
    print("✓ Capture complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review captured files in fixtures/ directory")
    print("2. Verify responses are correct")
    print("3. Run regression tests: HYDROCRON_ENV={} poetry run pytest tests/regression/ -v".format(env))
    print("4. Commit reference files to repository\n")


if __name__ == "__main__":
    main()
