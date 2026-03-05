# Hydrocron API Regression Tests

This directory contains regression tests that make real HTTP requests to deployed Hydrocron API endpoints.

## Purpose

These tests verify that the deployed API is:
- Accessible and responding
- Returning properly formatted responses
- Handling errors appropriately
- Supporting all required output formats (GeoJSON, CSV)

Unlike unit tests, these tests do NOT:
- Use mocked services
- Verify exact data values (data may change)
- Require local DynamoDB

## Running the Tests

### Prerequisites

1. Install dependencies including test group:
   ```bash
   poetry install --with test
   ```

### Run Against UAT

```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v
```

### Run Against OPS

```bash
HYDROCRON_ENV=ops poetry run pytest tests/regression/ -v
```

### Skip During Normal Test Runs

By default, if `HYDROCRON_ENV` is not set or invalid, these tests will be skipped:

```bash
# This will skip regression tests
poetry run pytest tests/
```

## Test Categories

### Reach Queries (`TestReachQueries`)
- GeoJSON output format
- CSV output format
- Content negotiation with Accept headers

### Lake Queries (`TestLakeQueries`)
- Prior lake feature queries
- GeoJSON output format

### Error Handling (`TestErrorHandling`)
- Missing required parameters
- Invalid feature types
- Non-existent feature IDs

### Output Formats (`TestOutputFormats`)
- Valid GeoJSON structure
- Valid CSV parsing

### API Availability (`TestAPIAvailability`)
- Basic smoke test that API is reachable

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
- Update `TEST_REACH_ID` and `TEST_LAKE_ID` constants
- Use feature IDs that exist in your deployed data
