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

from tests.regression.conftest import API_URLS, STABLE_TEST_DATA


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

    # Basic GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Reach",
            "feature_id": reach_data["feature_id"],
            "start_time": reach_data["start_time"],
            "end_time": reach_data["end_time"],
            "output": "geojson",
            "fields": "reach_id,time_str,wse"
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
            "fields": "reach_id,time_str,wse,slope,width"
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
            "fields": "reach_id,time_str,wse,slope,width,area_total,sword_version,collection_shortname,crid,geometry"
        },
        fixtures_dir / "reach" / "reach_comprehensive.geojson"
    )


def capture_node_fixtures(api_url, test_data, fixtures_dir):
    """Capture node reference files"""
    print("\n📊 Capturing Node fixtures...")

    node_data = test_data["node"]

    # Basic GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "fields": "node_id,time_str,wse,lat,lon"
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
            "fields": "node_id,time_str,wse,width,lat,lon"
        },
        fixtures_dir / "node" / "node_basic.csv"
    )

    # wse_sm fields CSV (Version D)
    print("  Note: Skipping wse_sm fixture (requires Version D with specific node ID)")
    # Uncomment when you have stable Version D node data:
    # capture_csv_response(
    #     api_url,
    #     {
    #         "feature": "Node",
    #         "feature_id": node_data["feature_id"],
    #         "start_time": node_data["start_time"],
    #         "end_time": node_data["end_time"],
    #         "output": "csv",
    #         "collection_name": "SWOT_L2_HR_RiverSP_D",
    #         "fields": "node_id,time_str,wse,wse_sm,wse_sm_u"
    #     },
    #     fixtures_dir / "node" / "node_wse_sm.csv"
    # )

    # Comprehensive GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "Node",
            "feature_id": node_data["feature_id"],
            "start_time": node_data["start_time"],
            "end_time": node_data["end_time"],
            "output": "geojson",
            "fields": "node_id,time_str,wse,width,lat,lon,geometry"
        },
        fixtures_dir / "node" / "node_comprehensive.geojson"
    )


def capture_priorlake_fixtures(api_url, test_data, fixtures_dir):
    """Capture prior lake reference files"""
    print("\n📊 Capturing PriorLake fixtures...")

    lake_data = test_data["priorlake"]

    # Basic GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": "lake_id,time_str,wse,area_total"
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
            "fields": "lake_id,time_str,wse,area_total,quality_f"
        },
        fixtures_dir / "priorlake" / "lake_basic.csv"
    )

    # qual_f_b field CSV (Version D)
    print("  Note: Skipping qual_f_b fixture (requires Version D)")
    # Uncomment when Version D is deployed:
    # capture_csv_response(
    #     api_url,
    #     {
    #         "feature": "PriorLake",
    #         "feature_id": lake_data["feature_id"],
    #         "start_time": lake_data["start_time"],
    #         "end_time": lake_data["end_time"],
    #         "output": "csv",
    #         "collection_name": "SWOT_L2_HR_LakeSP_D",
    #         "fields": "lake_id,time_str,wse,area_total,quality_f,qual_f_b"
    #     },
    #     fixtures_dir / "priorlake" / "lake_qual_f_b.csv"
    # )

    # Comprehensive GeoJSON
    capture_geojson_response(
        api_url,
        {
            "feature": "PriorLake",
            "feature_id": lake_data["feature_id"],
            "start_time": lake_data["start_time"],
            "end_time": lake_data["end_time"],
            "output": "geojson",
            "fields": "lake_id,time_str,wse,area_total,quality_f,PLD_version,geometry"
        },
        fixtures_dir / "priorlake" / "lake_comprehensive.geojson"
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
    fixtures_dir = Path(__file__).parent.parent / "fixtures"

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
        capture_reach_fixtures(api_url, STABLE_TEST_DATA, fixtures_dir)

    if args.feature in ['node', 'all']:
        capture_node_fixtures(api_url, STABLE_TEST_DATA, fixtures_dir)

    if args.feature in ['priorlake', 'all']:
        capture_priorlake_fixtures(api_url, STABLE_TEST_DATA, fixtures_dir)

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
