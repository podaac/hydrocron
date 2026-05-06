# Hydrocron API Regression Tests

This directory contains regression tests that make real HTTP requests to deployed Hydrocron API endpoints (UAT and OPS).

## Purpose

These tests verify that deployed APIs are:
- ✅ Accessible and responding (smoke tests)
- ✅ Returning properly formatted responses
- ✅ Handling errors appropriately
- ✅ Supporting all output formats (GeoJSON, CSV)
- ✅ Version D fields working correctly
- ✅ New features not breaking existing functionality
- ✅ Performing within acceptable time limits

Unlike unit tests, these tests:
- ❌ Do NOT use mocked services
- ❌ Do NOT verify exact data values (data may change)
- ❌ Do NOT require local DynamoDB
- ✅ Test against real deployed environments

## Test Organization

Tests are organized by purpose and feature type.

### Test Files

```
tests/regression/
├── conftest.py                     # Fixtures and configuration
├── utils.py                        # Shared utility functions
│
├── test_smoke.py                   # Quick smoke tests (< 30s)
│
├── test_reach_api.py               # Reach-specific tests
├── test_node_api.py                # Node-specific tests (includes Version D)
├── test_priorlake_api.py           # PriorLake-specific tests (includes Version D)
│
├── test_compact_parameter.py       # Compact parameter behavior
├── test_error_handling.py          # Comprehensive error handling
├── test_time_encoding.py           # Time format and encoding
├── test_response_formats.py        # Response format negotiation
├── test_api_features.py            # Additional API features
│
├── fixtures/                       # Golden reference files (environment-specific)
│   ├── uat/                        # UAT environment fixtures
│   │   ├── reach/
│   │   ├── node/
│   │   └── priorlake/
│   └── ops/                        # OPS environment fixtures
│       ├── reach/
│       ├── node/
│       └── priorlake/
│
└── dev-utils/                      # Developer utilities
    └── capture_reference_files.py
```

### Key Files

- **`test_smoke.py`** - Quick smoke tests (< 30 sec) - Run after every deployment
- **`test_reach_api.py`** - Comprehensive Reach feature tests
- **`test_node_api.py`** - Comprehensive Node feature tests + Version D wse_sm fields
- **`test_priorlake_api.py`** - Comprehensive PriorLake feature tests + Version D qual_f_b fields
- **`test_compact_parameter.py`** - Compact parameter across all features
- **`test_error_handling.py`** - Error handling and validation
- **`test_time_encoding.py`** - Time format handling
- **`test_response_formats.py`** - Response format negotiation (GeoJSON, CSV)
- **`test_api_features.py`** - Additional API features and edge cases
- **`conftest.py`** - Test configuration and fixtures
- **`utils.py`** - Helper functions for common operations

## Running the Tests

### Prerequisites

1. Install dependencies including test group:
   ```bash
   poetry install --with test
   ```

### Quick Smoke Tests (Recommended After Deployments)

Run only fast smoke tests (< 30 seconds):
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_smoke.py -v -m smoke
```

### Run Against UAT

Full regression suite:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v
```

Run only Version D field tests:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m version_d
```

Run excluding slow tests:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m "not slow"
```

### Run Against OPS

```bash
HYDROCRON_ENV=ops poetry run pytest tests/regression/ -v
```

### Run Specific Test Files

Run only Reach tests:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_reach_api.py -v
```

Run only Node tests:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_node_api.py -v
```

Run only PriorLake tests:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_priorlake_api.py -v
```

Run only error handling tests:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_error_handling.py -v
```

### Run Specific Test Classes or Methods

```bash
# Run specific class
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_reach_api.py::TestReachBasicQueries -v

# Run specific test
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_reach_api.py::TestReachBasicQueries::test_reach_geojson_with_all_standard_fields -v
```

### Generate HTML Report

```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v \
  --html=regression-report.html --self-contained-html
```

### Skip During Normal Test Runs

By default, if `HYDROCRON_ENV` is not set or invalid, these tests will be skipped:

```bash
# This will skip regression tests
poetry run pytest tests/
```

## Test Categories

### Test Suite Summary

| File | Test Classes | Tests | Purpose |
|------|-------------|-------|---------|
| `test_smoke.py` | 4 | 5 | Quick deployment validation |
| `test_reach_api.py` | 6 | 15 | Reach feature tests (note: discharge tests skipped) |
| `test_node_api.py` | 4 | 16 | Node feature + Version D tests (parameterized) |
| `test_priorlake_api.py` | 6 | 18 | PriorLake feature + Version D tests (parameterized) |
| `test_compact_parameter.py` | 5 | 11 | Compact parameter testing |
| `test_error_handling.py` | 8 | 25 | Error cases and validation |
| `test_time_encoding.py` | 6 | 18 | Time format handling |
| `test_response_formats.py` | 7 | 18 | Response format negotiation |
| `test_api_features.py` | 8 | 18 | Additional features and edge cases |
| `test_cors_collection_name.py` | 1 | 4 | CORS header validation with collection_name |
| **TOTAL** | **55** | **148** | Full regression coverage |

### Smoke Tests (`test_smoke.py`)
- **Purpose**: Quick verification API is functioning
- **Run time**: < 30 seconds
- **When**: After every deployment
- **Marker**: `@pytest.mark.smoke`
- **Coverage**: API health, basic queries for all features, output formats, error handling

### Feature Tests

#### Reach Tests (`test_reach_api.py`)
- **Purpose**: Comprehensive Reach feature testing
- **Note**: Discharge field tests are currently marked as `@pytest.mark.skip` - re-enable when needed
- **Note**: Basic query tests default to `reach_d` (Version D) data; 2.0 collection is tested explicitly in `TestReachCollectionVersions`
- **Coverage**:
  - Basic queries (GeoJSON, CSV) - using Version D data by default
  - Discharge fields (all algorithms: consensus, MetroMan, BAM, HiVDI) - currently skipped
  - Content negotiation (Accept headers)
  - Units fields validation
  - Collection version testing (2.0, D); default is Version D
  - Geometry validation
  - Golden file comparisons (parameterized for both 2.0 and D)

#### Node Tests (`test_node_api.py`)
- **Purpose**: Comprehensive Node feature testing + Version D
- **Note**: Basic query tests are parameterized to run with both `node` (2.0) and `node_d` (Version D) data
- **Note**: Default collection when `collection_name` is omitted is `SWOT_L2_HR_RiverSP_D`
- **Coverage**:
  - Basic queries (GeoJSON, CSV) - parameterized for both 2.0 and D
  - Default collection verification (D)
  - **Version D wse_sm field tests** (smoothed water surface elevation)
  - Backward compatibility
  - Performance tests
  - Golden file comparisons (parameterized for both 2.0 and D)

#### PriorLake Tests (`test_priorlake_api.py`)
- **Purpose**: Comprehensive PriorLake feature testing + Version D
- **Note**: Basic query tests are parameterized to run with both `priorlake` (2.0) and `priorlake_d` (Version D) data
- **Note**: Default collection when `collection_name` is omitted is `SWOT_L2_HR_LakeSP_D`
- **Coverage**:
  - Basic queries (GeoJSON, CSV) - parameterized for both 2.0 and D
  - Default collection verification (D)
  - Drainage system fields (ds1/ds2)
  - Quality and metadata fields
  - **Version D qual_f_b field tests** (quality flag)
  - Collection version testing (2.0, D)
  - Geometry validation
  - Golden file comparisons (parameterized for both 2.0 and D)

### API Behavior Tests

#### Compact Parameter (`test_compact_parameter.py`)
Tests the `compact` parameter that controls GeoJSON response format:
- `compact=true` returns single feature with array values
- `compact=false` returns multiple features (one per observation)
- Default compaction behavior based on Accept header
- Accept header (`application/geo+json` vs `application/json`) defaults
- Explicit compact parameter overrides Accept header
- Works across all feature types (Reach, Node, PriorLake)
- No effect on CSV output

#### Error Handling (`test_error_handling.py`)
Comprehensive error handling and validation:
- HTTP 415 errors for invalid Accept headers
- HTTP 400 errors for missing required parameters (feature, feature_id, start_time, end_time, fields)
- HTTP 400 errors for invalid parameter values (dates, field names, feature types)
- HTTP 400 errors for mismatched sub-collection and feature type (e.g. `SWOT_L2_HR_RiverSP_reach_D` with `Node`)
- Start time after end time validation
- Non-existent feature IDs
- Valid features with no data in time range
- HTTP 413 errors for payloads exceeding 6MB
- Field validation across feature types
- Error message quality checks

#### Time Encoding (`test_time_encoding.py`)
Timestamp formats and URL encoding:
- Basic ISO 8601 formats (YYYY-MM-DDTHH:MM:SSZ)
- Timestamps with/without Z suffix
- Millisecond precision timestamps
- UTC offsets (+HH:MM, -HH:MM)
- URL encoding of + as %2B (required)
- Invalid time format error handling
- Time range boundary conditions (start == end, narrow/wide ranges)
- Leap year validation (Feb 29) - uses hardcoded reach_id `14306900121` with known Leap Day data
- Time format consistency across feature types

#### Response Formats (`test_response_formats.py`)
Response format handling and content negotiation:
- JSON wrapper structure (status, time, hits, results)
- Raw GeoJSON format (application/geo+json)
- Raw CSV format (text/csv)
- Content-Type header validation
- `output` parameter vs Accept header interaction
- Units fields automatically included (wse_units, slope_units, etc.)
- Response format consistency across all feature types

#### CORS (`test_cors_collection_name.py`)
CORS header validation for the `collection_name` parameter:
- CORS headers present with explicit `collection_name` (all feature types and versions)
- CORS headers present with no `collection_name` (default D collections only)
- CORS headers present on error responses with `collection_name`
- CORS headers present on error responses without `collection_name`

#### API Features (`test_api_features.py`)
Additional API features and edge cases:
- Optional API key header (x-hydrocron-key) for rate limiting
- Geometry field behavior by type:
  - Reach returns LineString
  - Node returns Point
  - PriorLake returns Point (center coordinates)
  - Geometry optional in queries, excluded from CSV
- Field ordering in CSV responses matches request
- Case sensitivity (feature names, field names, output parameter)
- Special characters in parameters (spaces, duplicates)
- No-data sentinel values (-999999999999.0)
- Query performance characteristics
- Multiple consecutive queries reliability

## Test Coverage

The regression test suite provides comprehensive coverage of the Hydrocron API as documented at:
- https://podaac.github.io/hydrocron/examples.html
- https://podaac.github.io/hydrocron/timeseries.html

### Coverage Highlights

**Feature-Specific Tests:**
- ✅ All three feature types (Reach, Node, PriorLake)
- ✅ Version D fields (wse_sm for Node, qual_f_b for PriorLake)
- ✅ Default collection is Version D for all feature types
- ✅ Collection version testing (2.0, D)
- ✅ Feature-specific fields (discharge algorithms, drainage system, quality fields)
- ✅ Backward compatibility
- ✅ CORS headers (with and without collection_name, on success and error responses)

**API Behavior:**
- ✅ Compact parameter for GeoJSON responses
- ✅ Accept header content negotiation
- ✅ Time format handling (ISO 8601, UTC offsets, URL encoding)
- ✅ Response format wrappers (JSON wrapper vs raw formats)
- ✅ Units fields automatic inclusion
- ✅ Geometry field handling by feature type
- ✅ Field ordering in responses

**Error Handling:**
- ✅ HTTP 400 (missing/invalid parameters)
- ✅ HTTP 413 (payload too large)
- ✅ HTTP 415 (unsupported media type)
- ✅ Non-existent features
- ✅ Empty result sets
- ✅ Invalid time ranges

**Edge Cases:**
- ✅ Special characters and encoding
- ✅ Case sensitivity
- ✅ Boundary conditions (narrow/wide time ranges, leap years)
- ✅ No-data sentinel values
- ✅ Multiple consecutive queries
- ✅ Performance characteristics

## Test Markers

Tests can be filtered using pytest markers:

- `@pytest.mark.smoke` - Quick smoke tests
- `@pytest.mark.version_d` - Version D specific features
- `@pytest.mark.golden` - Golden file comparison tests
- `@pytest.mark.slow` - Tests that take > 10 seconds
- `@pytest.mark.skip` - Skipped tests (require updates)

### Using Markers

Run only smoke tests:
```bash
pytest tests/regression/ -m smoke
```

Exclude slow tests:
```bash
pytest tests/regression/ -m "not slow"
```

Run only Version D tests:
```bash
pytest tests/regression/ -m version_d
```

## Configuring Test Data

Test data is configured in `conftest.py` using environment-specific dictionaries:
- `STABLE_TEST_DATA_UAT` - Test data for UAT environment
- `STABLE_TEST_DATA_OPS` - Test data for OPS environment

Each environment has its own feature IDs, time ranges, and expected counts. The `stable_test_data` fixture automatically selects the correct data based on the `HYDROCRON_ENV` variable.

If features don't exist in your deployed environment, update the corresponding dictionary with feature IDs that exist and have data available.

## Adding to CI/CD

To run these tests automatically after deployment, add a step to your GitHub Actions workflow:

```yaml
- name: Run Regression Tests
  env:
    HYDROCRON_ENV: ${{ steps.lowercase.outputs.TARGET_ENV_LOWERCASE }}
  run: |
    poetry run pytest tests/regression/ -v --tb=short
```

## Best Practices

### When to Run Tests

**After Every Deployment** (5-10 minutes):
```bash
# 1. Run smoke tests first (< 30 sec)
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_smoke.py -v -m smoke

# 2. If smoke tests pass, run full suite
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m "not slow"
```

**Before Promoting UAT → OPS** (10-15 minutes):
```bash
# Run complete test suite including slow tests
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v
```

**After Adding New Fields** (5-10 minutes):
```bash
# Test new Version D fields work and don't break existing functionality
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m version_d
```

**Scheduled Nightly** (15 minutes):
```bash
# Full regression on OPS to catch any issues
HYDROCRON_ENV=ops poetry run pytest tests/regression/ -v --html=report.html
```

### Updating Test Data

If feature IDs don't exist in your environment, update the appropriate environment-specific dictionary in `conftest.py`:

```python
# For UAT environment
STABLE_TEST_DATA_UAT = {
    "reach": {
        "feature_id": "YOUR_UAT_REACH_ID",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-31T23:59:59Z",
        "expected_count": 5,
        "fields": "reach_id,time_str,wse,slope,width,sword_version",
        ...
    },
    ...
}

# For OPS environment
STABLE_TEST_DATA_OPS = {
    "reach": {
        "feature_id": "YOUR_OPS_REACH_ID",
        "start_time": "2024-02-01T00:00:00Z",
        "end_time": "2024-02-28T23:59:59Z",
        "expected_count": 4,
        "fields": "reach_id,time_str,wse,slope,width,sword_version",
        ...
    },
    ...
}
```

Both `reach_d`, `node_d`, and `priorlake_d` test data should also be configured for Version D collection testing.

### Adding New Tests

When adding new features to the API:

1. **Add unit tests** in `tests/test_api.py` for field validation
2. **Add regression tests** here for deployed API verification
3. **Use markers** appropriately (`@pytest.mark.version_d` for new fields)
4. **Update `utils.py`** if you need new helper functions

Example new test:
```python
@pytest.mark.version_d
def test_my_new_field(api_client):
    """Test new field is accessible"""
    response, _ = api_client.query({
        "feature": "Node",
        "feature_id": "31241400580011",
        "start_time": "2026-02-01T00:00:00Z",
        "end_time": "2026-02-28T00:00:00Z",
        "output": "csv",
        "fields": "node_id,time_str,my_new_field"
    })

    assert_http_success(response)
    assert 'my_new_field' in response.text
```

### Skipped Tests and Known Issues

Some tests are marked with `@pytest.mark.skip` and require updates:

**Tests requiring real data:**
- `test_large_payload_returns_413` - Needs a feature ID with dataset exceeding 6MB
- `test_query_with_valid_api_key_succeeds` - Needs a valid API key for testing

## Deployment Workflow

Recommended workflow for safe deployments:

```
1. Deploy to UAT
   └─> Automated smoke tests run (< 1 min)
       ├─ FAIL → Block promotion, investigate
       └─ PASS → Continue

2. Run full regression suite on UAT
   └─> Manual or automated (< 10 min)
       ├─ FAIL → Block promotion, fix issues
       └─ PASS → Continue

3. Manual approval/review

4. Deploy to OPS
   └─> Automated smoke tests run (< 1 min)
       ├─ FAIL → Rollback, investigate
       └─ PASS → Deployment complete

5. Schedule nightly full regression on OPS
```

## Troubleshooting

### Tests are skipped
Make sure `HYDROCRON_ENV` is set to `uat` or `ops`.

### Connection errors
- Verify the API URL is correct in `conftest.py`
- Check network connectivity
- Verify the API is deployed and running

### Test timeouts
- Default timeout is 5 seconds
- If API is slow, increase timeout in test code
- Check API performance and logs

### Feature IDs not found
- Update `STABLE_TEST_DATA` in `conftest.py`
- Use feature IDs that exist in your deployed data
- Check that data has been ingested for the time ranges specified

### Version D tests failing in OPS
- Version D might not be deployed to OPS yet
- Verify collection_name in test matches what's deployed

## Contributing

When adding new regression tests:

1. ✅ Test against real data that exists in both UAT and OPS
2. ✅ Use appropriate markers (`@pytest.mark.smoke`, `@pytest.mark.version_d`)
3. ✅ Add helper functions to `utils.py` for reusable logic
4. ✅ Update this README with new test categories
5. ✅ Test both success and error cases
6. ✅ Include performance assertions where appropriate


## TODO

- Finish golden file tests in `test_node_api.py` and `test_priorlake_api.py` (several are marked `@pytest.mark.skip(reason="Not finished yet")`)
- Add golden tests covering all fields being returned with saved reference files (mentioned when granuleUR was missing)
- Add golden tests covering Accept headers: `application/json`, `application/geo+json`, and `text/csv`
- Enable `test_large_payload_returns_413` once a feature ID with a dataset exceeding 6MB is identified
- Enable `test_query_with_valid_api_key_succeeds` once a valid API key is available for testing
