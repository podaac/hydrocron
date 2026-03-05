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

Tests are organized by purpose and feature type:

- **`test_smoke.py`** - Quick smoke tests (< 30 sec) - Run after every deployment
- **`test_reach_api.py`** - Comprehensive Reach feature tests
- **`test_node_api.py`** - Comprehensive Node feature tests
- **`test_priorlake_api.py`** - Comprehensive PriorLake feature tests
- **`test_version_d_fields.py`** - Version D specific fields (wse_sm, qual_f_b)
- **`conftest.py`** - Test configuration and fixtures
- **`utils.py`** - Helper functions for common operations
- **`scan-dynamodb.py`** - Utility script to scan and compare DynamoDB table schemas

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

Run only Version D field tests:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_version_d_fields.py -v
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

### Smoke Tests (`test_smoke.py`) - 8 tests
- **Purpose**: Quick verification API is functioning
- **Run time**: < 30 seconds
- **When**: After every deployment
- **Marker**: `@pytest.mark.smoke`
- **Coverage**: API health, basic queries for all features, output formats, error handling

### Reach Tests (`test_reach_api.py`) - 13 tests
- **Purpose**: Comprehensive Reach feature testing
- **Coverage**:
  - Basic queries (GeoJSON, CSV)
  - Discharge fields (all algorithms: consensus, MetroMan, BAM, HiVDI)
  - Content negotiation (Accept headers)
  - Units fields validation
  - Collection version testing (2.0, D)
  - Geometry validation

### Node Tests (`test_node_api.py`) - 11 tests
- **Purpose**: Comprehensive Node feature testing
- **Coverage**:
  - Basic queries (GeoJSON, CSV)
  - Version D wse_sm field tests
  - Error handling
  - Performance tests
  - Backward compatibility

### PriorLake Tests (`test_priorlake_api.py`) - 8 tests
- **Purpose**: Comprehensive PriorLake feature testing
- **Coverage**:
  - Basic queries (GeoJSON, CSV)
  - Drainage system fields (ds1/ds2)
  - Quality and metadata fields
  - Collection version testing (2.0, D)
  - Geometry validation

### Version D Field Tests (`test_version_d_fields.py`) - 9 tests
- **Purpose**: Test new fields added in Version D
- **Fields tested**:
  - Node: `wse_sm`, `wse_sm_u`, `wse_sm_q`, `wse_sm_q_b`
  - PriorLake: `qual_f_b`
- **Marker**: `@pytest.mark.version_d`
- **When**: Before promoting UAT to OPS
- **Coverage**: Field validation, feature-type restrictions, backward compatibility

**Total: 49 regression tests**

## Test Markers

Tests can be filtered using pytest markers:

- `@pytest.mark.smoke` - Quick smoke tests
- `@pytest.mark.slow` - Tests taking > 10 seconds
- `@pytest.mark.version_d` - Version D specific features
- `@pytest.mark.uat_only` - Only run in UAT environment

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

The tests use known feature IDs at the top of `test_api_regression.py`:

```python
TEST_REACH_ID = "71224100223"
TEST_LAKE_ID = "9120274662"
```

If these features don't exist in your deployed environment, update these constants to use feature IDs that do exist.

## Running Specific Tests

Run only reach tests:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_api_regression.py::TestReachQueries -v
```

Run only error handling tests:
```bash
HYDROCRON_ENV=ops poetry run pytest tests/regression/test_api_regression.py::TestErrorHandling -v
```

Run a single test:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_api_regression.py::TestReachQueries::test_reach_geojson_query -v
```

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
# Test new fields work and don't break existing functionality
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_version_d_fields.py -v
```

**Scheduled Nightly** (15 minutes):
```bash
# Full regression on OPS to catch any issues
HYDROCRON_ENV=ops poetry run pytest tests/regression/ -v --html=report.html
```

### Updating Test Data

If feature IDs don't exist in your environment, update `STABLE_TEST_DATA` in `conftest.py`:

```python
STABLE_TEST_DATA = {
    "reach": {
        "feature_id": "YOUR_REACH_ID",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-31T23:59:59Z",
        ...
    },
    ...
}
```

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
- Default timeout is 30 seconds
- If API is slow, increase timeout in test code
- Check API performance and logs

### Feature IDs not found
- Update `STABLE_TEST_DATA` in `conftest.py`
- Use feature IDs that exist in your deployed data
- Check that data has been ingested for the time ranges specified

### Version D tests failing in OPS
- Version D might not be deployed to OPS yet
- Tests marked `@pytest.mark.uat_only` will skip in OPS
- Verify collection_name in test matches what's deployed

## Contributing

When adding new regression tests:

1. ✅ Test against real data that exists in both UAT and OPS
2. ✅ Use appropriate markers (`@pytest.mark.smoke`, `@pytest.mark.version_d`)
3. ✅ Add helper functions to `utils.py` for reusable logic
4. ✅ Update this README with new test categories
5. ✅ Test both success and error cases
6. ✅ Include performance assertions where appropriate
