"""
Utility functions for regression tests
"""
import csv
import json
from io import StringIO
from pathlib import Path
from typing import Dict, List, Any, Optional


def validate_geojson_structure(data):
    """
    Validate GeoJSON structure

    Args:
        data: Dictionary containing GeoJSON response

    Raises:
        AssertionError: If structure is invalid
    """
    assert 'type' in data, "GeoJSON must have 'type' field"
    assert data['type'] == 'FeatureCollection', "GeoJSON type must be 'FeatureCollection'"
    assert 'features' in data, "GeoJSON must have 'features' field"
    assert isinstance(data['features'], list), "Features must be a list"

    # Validate each feature
    for i, feature in enumerate(data['features']):
        assert 'type' in feature, f"Feature {i} must have 'type' field"
        assert feature['type'] == 'Feature', f"Feature {i} type must be 'Feature'"
        assert 'geometry' in feature, f"Feature {i} must have 'geometry' field"
        assert 'properties' in feature, f"Feature {i} must have 'properties' field"


def validate_csv_structure(csv_text, expected_fields=None):
    """
    Validate CSV structure and optionally check for expected fields

    Args:
        csv_text: CSV text content
        expected_fields: Optional list of field names that should be present

    Returns:
        List of dictionaries representing rows

    Raises:
        AssertionError: If structure is invalid
    """
    lines = csv_text.strip().split('\n')
    assert len(lines) >= 1, "CSV must have at least a header row"

    # Parse as CSV
    csv_reader = csv.DictReader(StringIO(csv_text))
    rows = list(csv_reader)

    # Validate headers
    if expected_fields:
        headers = set(csv_reader.fieldnames)
        for field in expected_fields:
            assert field in headers, f"Expected field '{field}' not found in CSV headers"

    # Validate all rows have same number of columns
    if len(rows) > 0:
        expected_col_count = len(csv_reader.fieldnames)
        for i, row in enumerate(rows):
            assert len(row) == expected_col_count, \
                f"Row {i} has {len(row)} columns, expected {expected_col_count}"

    return rows


def assert_response_time(elapsed_seconds, max_seconds):
    """
    Assert that response time is within acceptable range

    Args:
        elapsed_seconds: Actual elapsed time
        max_seconds: Maximum acceptable time

    Raises:
        AssertionError: If time exceeds maximum
    """
    assert elapsed_seconds <= max_seconds, \
        f"Response time {elapsed_seconds:.2f}s exceeded maximum {max_seconds}s"


def get_result_count(response, output_format: str = "geojson") -> int:
    """
    Get the number of results from API response

    Handles both JSON-wrapped and raw responses.

    Args:
        response: requests.Response object
        output_format: "geojson" or "csv"

    Returns:
        Number of results/features/rows
    """
    if output_format == "geojson":
        data = response.json()
        # Handle wrapped response
        if 'results' in data and 'geojson' in data['results']:
            data = data['results']['geojson']
        return len(data.get('features', []))
    elif output_format == "csv":
        # Try to parse as JSON first (CSV is often JSON-wrapped)
        try:
            data = response.json()
            if 'hits' in data:
                # Use hits field from JSON wrapper (most accurate)
                return data['hits']
            elif 'results' in data and 'csv' in data['results']:
                # Extract CSV from wrapper and count rows
                csv_text = data['results']['csv']
                lines = csv_text.strip().split('\n')
                return max(0, len(lines) - 1)  # Subtract header
        except (ValueError, json.JSONDecodeError):
            # Not JSON, treat as raw CSV
            pass

        # Handle raw CSV (fallback)
        lines = response.text.strip().split('\n')
        return max(0, len(lines) - 1)  # Subtract header
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def assert_result_count(response, expected_count: int, output_format: str = "geojson"):
    """
    Assert that response has expected number of results

    Args:
        response: requests.Response object
        expected_count: Expected number of results
        output_format: "geojson" or "csv"

    Raises:
        AssertionError: If count doesn't match
    """
    actual_count = get_result_count(response, output_format)

    assert actual_count == expected_count, \
        f"Expected {expected_count} results, got {actual_count}. " \
        f"This may indicate data ingestion issues."


def extract_geojson_from_response(response_data):
    """
    Extract GeoJSON from API response wrapper

    Args:
        response_data: Full API response dictionary

    Returns:
        GeoJSON FeatureCollection
    """
    # Handle both wrapped and unwrapped responses
    if 'results' in response_data and 'geojson' in response_data['results']:
        return response_data['results']['geojson']
    elif 'type' in response_data and response_data['type'] == 'FeatureCollection':
        return response_data
    else:
        raise ValueError("Could not find GeoJSON in response")


def extract_csv_from_response(response_data):
    """
    Extract CSV from API response wrapper

    Args:
        response_data: Full API response dictionary (when output=csv)

    Returns:
        CSV text string
    """
    # Handle wrapped CSV response
    if 'results' in response_data and 'csv' in response_data['results']:
        return response_data['results']['csv']
    # Handle raw CSV (if response is already a string)
    elif isinstance(response_data, str):
        return response_data
    else:
        raise ValueError("Could not find CSV in response")


def compare_field_sets(actual_fields, expected_fields, ignore_fields=None):
    """
    Compare two sets of fields, optionally ignoring some fields

    Args:
        actual_fields: Set or list of actual field names
        expected_fields: Set or list of expected field names
        ignore_fields: Optional set or list of fields to ignore in comparison

    Returns:
        Tuple of (missing_fields, extra_fields)
    """
    actual = set(actual_fields)
    expected = set(expected_fields)

    if ignore_fields:
        ignore = set(ignore_fields)
        actual = actual - ignore
        expected = expected - ignore

    missing = expected - actual
    extra = actual - expected

    return list(missing), list(extra)


def assert_http_success(response, expected_status=200):
    """
    Assert HTTP response is successful

    Args:
        response: requests.Response object
        expected_status: Expected status code (default 200)

    Raises:
        AssertionError: If status code doesn't match
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}. " \
        f"Response: {response.text[:500]}"


def assert_http_error(response, expected_status_range=(400, 499)):
    """
    Assert HTTP response is an error

    Args:
        response: requests.Response object
        expected_status_range: Tuple of (min, max) status codes

    Raises:
        AssertionError: If status code is not in error range
    """
    min_status, max_status = expected_status_range
    assert min_status <= response.status_code <= max_status, \
        f"Expected error status {min_status}-{max_status}, got {response.status_code}"


# ============================================================================
# Golden File Testing Functions
# ============================================================================

def load_reference_file(fixtures_dir: Path, relative_path: str) -> Any:
    """
    Load reference file from fixtures directory

    Args:
        fixtures_dir: Path to fixtures directory
        relative_path: Relative path to reference file (e.g., "reach/reach_basic.json")

    Returns:
        Loaded content (dict for JSON, str for CSV)

    Raises:
        FileNotFoundError: If reference file doesn't exist
    """
    file_path = fixtures_dir / relative_path

    if not file_path.exists():
        raise FileNotFoundError(
            f"Reference file not found: {file_path}\n"
            f"Run 'poetry run python tests/regression/capture_reference_files.py' to generate it."
        )

    if file_path.suffix in ['.json', '.geojson']:
        with open(file_path, 'r') as f:
            return json.load(f)
    elif file_path.suffix == '.csv':
        with open(file_path, 'r') as f:
            content = f.read()

            # Check if CSV file contains JSON-wrapped response
            # (happens if captured file contains entire API response)
            if content.strip().startswith('{'):
                try:
                    data = json.loads(content)
                    # Extract CSV from JSON wrapper
                    if 'results' in data and 'csv' in data['results']:
                        return data['results']['csv']
                except json.JSONDecodeError:
                    pass

            # Return as-is if not JSON-wrapped
            return content
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")


def normalize_geojson_for_comparison(data: Dict, ignore_fields: Optional[List[str]] = None) -> Dict:
    """
    Normalize GeoJSON for comparison by removing dynamic fields

    Args:
        data: GeoJSON FeatureCollection
        ignore_fields: List of property fields to ignore (e.g., ['ingest_time', 'crid'])

    Returns:
        Normalized GeoJSON
    """
    ignore_fields = ignore_fields or ['ingest_time', 'crid', 'granuleUR']

    # Deep copy to avoid modifying original
    normalized = json.loads(json.dumps(data))

    # Handle wrapped response
    if 'results' in normalized and 'geojson' in normalized['results']:
        normalized = normalized['results']['geojson']

    # Remove ignored fields from each feature's properties
    if 'features' in normalized:
        for feature in normalized['features']:
            if 'properties' in feature:
                for field in ignore_fields:
                    feature['properties'].pop(field, None)

    return normalized


def normalize_csv_for_comparison(csv_text: str, ignore_columns: Optional[List[str]] = None) -> List[Dict]:
    """
    Normalize CSV for comparison by removing dynamic columns and sorting rows

    Args:
        csv_text: CSV text content
        ignore_columns: List of columns to ignore (e.g., ['ingest_time', 'crid'])

    Returns:
        List of dictionaries with ignored columns removed, sorted by first column
    """
    ignore_columns = ignore_columns or ['ingest_time', 'crid', 'granuleUR']

    csv_reader = csv.DictReader(StringIO(csv_text))
    rows = list(csv_reader)

    # Remove ignored columns from each row
    for row in rows:
        for col in ignore_columns:
            row.pop(col, None)

    # Sort rows by first column for consistent comparison
    if rows and len(rows) > 0:
        first_key = list(rows[0].keys())[0]
        rows = sorted(rows, key=lambda x: x.get(first_key, ''))

    return rows


def compare_geojson_responses(
    actual: Dict,
    expected: Dict,
    ignore_fields: Optional[List[str]] = None
) -> tuple[bool, str]:
    """
    Compare two GeoJSON responses

    Args:
        actual: Actual API response (GeoJSON)
        expected: Expected response from reference file
        ignore_fields: List of fields to ignore in comparison

    Returns:
        (is_match, diff_message)
    """
    actual_norm = normalize_geojson_for_comparison(actual, ignore_fields)
    expected_norm = normalize_geojson_for_comparison(expected, ignore_fields)

    if actual_norm == expected_norm:
        return True, ""

    # Generate helpful diff message
    actual_features = len(actual_norm.get('features', []))
    expected_features = len(expected_norm.get('features', []))

    diff_msg = f"GeoJSON mismatch:\n"
    diff_msg += f"  Actual features: {actual_features}\n"
    diff_msg += f"  Expected features: {expected_features}\n"

    if actual_features != expected_features:
        diff_msg += f"  ⚠️ Feature count differs!\n"
        return False, diff_msg

    # Count matches but values differ - provide detailed comparison
    if actual_features > 0 and expected_features > 0:
        # Check field schema
        actual_props = set(actual_norm['features'][0]['properties'].keys())
        expected_props = set(expected_norm['features'][0]['properties'].keys())

        missing = expected_props - actual_props
        extra = actual_props - expected_props

        if missing:
            diff_msg += f"  Missing fields: {sorted(missing)}\n"
        if extra:
            diff_msg += f"  Extra fields: {sorted(extra)}\n"

        # Compare features to find differences
        differing_features = []
        for i, (actual_feat, expected_feat) in enumerate(zip(actual_norm['features'], expected_norm['features'])):
            if actual_feat != expected_feat:
                differing_features.append(i)

        if differing_features:
            diff_msg += f"\n  Features with differences: {len(differing_features)} of {actual_features}\n"
            diff_msg += f"  Feature indices: {differing_features[:10]}"
            if len(differing_features) > 10:
                diff_msg += f" ... and {len(differing_features) - 10} more"
            diff_msg += "\n"

            # Show detailed diff for first differing feature
            first_diff_idx = differing_features[0]
            actual_feat = actual_norm['features'][first_diff_idx]
            expected_feat = expected_norm['features'][first_diff_idx]

            diff_msg += f"\n  First difference (feature {first_diff_idx}):\n"

            # Compare properties
            actual_props_dict = actual_feat.get('properties', {})
            expected_props_dict = expected_feat.get('properties', {})

            common_fields = set(actual_props_dict.keys()) & set(expected_props_dict.keys())
            differing_fields = []

            for field in sorted(common_fields):
                actual_val = actual_props_dict[field]
                expected_val = expected_props_dict[field]
                if actual_val != expected_val:
                    differing_fields.append((field, actual_val, expected_val))

            if differing_fields:
                diff_msg += f"    Differing fields ({len(differing_fields)}):\n"
                for field, actual_val, expected_val in differing_fields[:5]:
                    diff_msg += f"      {field}:\n"
                    diff_msg += f"        Actual:   {actual_val}\n"
                    diff_msg += f"        Expected: {expected_val}\n"
                if len(differing_fields) > 5:
                    diff_msg += f"      ... and {len(differing_fields) - 5} more differing fields\n"

            # Check geometry differences
            if actual_feat.get('geometry') != expected_feat.get('geometry'):
                diff_msg += f"    Geometry differs\n"

    return False, diff_msg


def compare_csv_responses(
    actual: str,
    expected: str,
    ignore_columns: Optional[List[str]] = None
) -> tuple[bool, str]:
    """
    Compare two CSV responses

    Args:
        actual: Actual API response (CSV text)
        expected: Expected response from reference file (CSV text)
        ignore_columns: List of columns to ignore in comparison

    Returns:
        (is_match, diff_message)
    """
    actual_rows = normalize_csv_for_comparison(actual, ignore_columns)
    expected_rows = normalize_csv_for_comparison(expected, ignore_columns)

    if actual_rows == expected_rows:
        return True, ""

    # Generate helpful diff message
    diff_msg = f"CSV mismatch:\n"
    diff_msg += f"  Actual rows: {len(actual_rows)}\n"
    diff_msg += f"  Expected rows: {len(expected_rows)}\n"

    if len(actual_rows) != len(expected_rows):
        diff_msg += f"  ⚠️ Row count differs!\n"
        return False, diff_msg

    # Count matches but values differ - provide detailed comparison
    if actual_rows and expected_rows:
        # Check column schema
        actual_cols = set(actual_rows[0].keys())
        expected_cols = set(expected_rows[0].keys())

        missing = expected_cols - actual_cols
        extra = actual_cols - expected_cols

        if missing:
            diff_msg += f"  Missing columns: {sorted(missing)}\n"
        if extra:
            diff_msg += f"  Extra columns: {sorted(extra)}\n"

        # Compare rows to find differences
        differing_rows = []
        for i, (actual_row, expected_row) in enumerate(zip(actual_rows, expected_rows)):
            if actual_row != expected_row:
                differing_rows.append(i)

        if differing_rows:
            diff_msg += f"\n  Rows with differences: {len(differing_rows)} of {len(actual_rows)}\n"
            diff_msg += f"  Row indices: {differing_rows[:10]}"
            if len(differing_rows) > 10:
                diff_msg += f" ... and {len(differing_rows) - 10} more"
            diff_msg += "\n"

            # Show detailed diff for first differing row
            first_diff_idx = differing_rows[0]
            actual_row = actual_rows[first_diff_idx]
            expected_row = expected_rows[first_diff_idx]

            diff_msg += f"\n  First difference (row {first_diff_idx}):\n"

            # Compare columns
            common_cols = set(actual_row.keys()) & set(expected_row.keys())
            differing_cols = []

            for col in sorted(common_cols):
                actual_val = actual_row[col]
                expected_val = expected_row[col]
                if actual_val != expected_val:
                    differing_cols.append((col, actual_val, expected_val))

            if differing_cols:
                diff_msg += f"    Differing columns ({len(differing_cols)}):\n"
                for col, actual_val, expected_val in differing_cols[:5]:
                    diff_msg += f"      {col}:\n"
                    diff_msg += f"        Actual:   {actual_val}\n"
                    diff_msg += f"        Expected: {expected_val}\n"
                if len(differing_cols) > 5:
                    diff_msg += f"      ... and {len(differing_cols) - 5} more differing columns\n"

    return False, diff_msg


def assert_matches_reference(
    actual_response,
    reference_file_path: str,
    fixtures_dir: Path,
    output_format: str = "geojson",
    ignore_fields: Optional[List[str]] = None
):
    """
    Assert that actual API response matches reference file

    Args:
        actual_response: requests.Response object
        reference_file_path: Relative path to reference file in fixtures dir
        fixtures_dir: Path to fixtures directory
        output_format: "geojson" or "csv"
        ignore_fields: List of fields/columns to ignore (e.g., ['ingest_time'])

    Raises:
        AssertionError: If responses don't match
    """
    # Load reference file
    expected = load_reference_file(fixtures_dir, reference_file_path)

    # Compare based on format
    if output_format == "geojson":
        actual_data = actual_response.json()
        is_match, diff_msg = compare_geojson_responses(actual_data, expected, ignore_fields)
    elif output_format == "csv":
        # Extract CSV from JSON-wrapped response if needed
        try:
            response_data = actual_response.json()
            actual_data = extract_csv_from_response(response_data)
        except (ValueError, json.JSONDecodeError):
            # Raw CSV response
            actual_data = actual_response.text

        is_match, diff_msg = compare_csv_responses(actual_data, expected, ignore_fields)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

    assert is_match, f"Response does not match reference file {reference_file_path}:\n{diff_msg}"
