# Hydrocron API Regression Testing Guide

## Overview

This guide explains how to use the regression test suite to verify deployed APIs (UAT and OPS) are functioning correctly.

## Quick Start

### After Deploying to UAT
```bash
# 1. Quick smoke test (30 seconds)
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_smoke.py -v -m smoke

# 2. If smoke passes, run full suite (10 minutes)
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v
```

### Testing New Fields
```bash
# Test Version D fields work correctly
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_version_d_fields.py -v
```

### Before Promoting to OPS
```bash
# Full regression suite must pass
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v --html=report.html
```

## Test Structure

### Files and Purpose

| File | Purpose | Run Time | When to Run |
|------|---------|----------|-------------|
| `test_smoke.py` | Quick health checks | < 30 sec | After every deployment |
| `test_api_regression.py` | Original comprehensive tests | 3-5 min | Before promotion |
| `test_node_api.py` | Node feature tests | 2-3 min | Before promotion |
| `test_version_d_fields.py` | Version D field validation | 2-3 min | Before promotion |
| `conftest.py` | Test configuration | N/A | Config |
| `utils.py` | Helper functions | N/A | Library |

### Test Coverage

**Smoke Tests** (`test_smoke.py`):
- ✅ API is responding
- ✅ Each feature type works (Reach, Node, PriorLake)
- ✅ Both output formats work (CSV, GeoJSON)
- ✅ Basic error handling

**Node Tests** (`test_node_api.py`):
- ✅ Basic queries (GeoJSON, CSV)
- ✅ Version D wse_sm fields
- ✅ Error handling
- ✅ Performance testing

**Version D Field Tests** (`test_version_d_fields.py`):
- ✅ Node: `wse_sm`, `wse_sm_u`, `wse_sm_q`, `wse_sm_q_b`
- ✅ PriorLake: `qual_f_b`
- ✅ Field validation (only valid for correct feature types)
- ✅ Not available in 2.0 collections
- ✅ Backward compatibility

## Common Commands

### Run by Test Type

```bash
# Smoke tests only (fastest)
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -m smoke -v

# Version D tests only
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -m version_d -v

# Exclude slow tests
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -m "not slow" -v

# Node tests only
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_node_api.py -v
```

### Run Specific Tests

```bash
# Single test class
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_node_api.py::TestNodeBasicQueries -v

# Single test method
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_node_api.py::TestNodeBasicQueries::test_node_geojson_query -v
```

### Generate Reports

```bash
# HTML report
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v \
  --html=regression-report.html --self-contained-html

# JUnit XML (for CI/CD)
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v \
  --junit-xml=test-results.xml
```

## Recommended Workflows

### Workflow 1: Regular Development

```bash
# 1. Make code changes
# 2. Run unit tests
poetry run pytest tests/test_api.py -v

# 3. Deploy to UAT
# 4. Run smoke tests
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_smoke.py -m smoke -v

# 5. If new fields added, test them
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_version_d_fields.py -v
```

### Workflow 2: Pre-OPS Deployment

```bash
# 1. Full regression on UAT
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v --html=uat-report.html

# 2. Review report, verify all pass
# 3. Get approval
# 4. Deploy to OPS
# 5. Smoke test OPS
HYDROCRON_ENV=ops poetry run pytest tests/regression/test_smoke.py -m smoke -v
```

### Workflow 3: Adding New API Fields

```bash
# 1. Add field validation to unit tests
# tests/test_api.py

# 2. Add regression test
# tests/regression/test_version_d_fields.py or create new file

# 3. Run new test against UAT
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_version_d_fields.py::TestYourNewField -v

# 4. Run full suite to ensure no breakage
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v
```

## Test Data Configuration

Update stable test data in `conftest.py` if feature IDs don't exist:

```python
STABLE_TEST_DATA = {
    "reach": {
        "feature_id": "34296500851",  # Update if not found
        "start_time": "2024-02-10T00:00:00Z",
        "end_time": "2024-05-03T00:00:00Z",
        ...
    },
    ...
}
```

## CI/CD Integration

See `.github/workflows/regression-tests.yml` for automated testing after deployments.

Key points:
- Smoke tests run automatically after UAT deployment
- Full suite runs before OPS promotion
- Tests block promotion if they fail
- Nightly full regression on OPS

## Troubleshooting

### Tests Skip
```bash
# Make sure environment is set
export HYDROCRON_ENV=uat
poetry run pytest tests/regression/ -v
```

### Connection Errors
- Check VPN/network connectivity
- Verify API URLs in `conftest.py`
- Confirm deployment completed

### Feature Not Found Errors
- Update `STABLE_TEST_DATA` in `conftest.py`
- Use feature IDs that exist in your environment
- Check data ingestion status

### Version D Tests Fail
- Verify Version D is deployed to target environment
- Check collection_name in tests matches deployment
- UAT-only tests will skip in OPS (expected)

## Best Practices

✅ **DO**:
- Run smoke tests after every deployment
- Run full suite before promoting to OPS
- Update test data when feature IDs change
- Add regression tests for new API features
- Use markers appropriately (`@pytest.mark.smoke`, etc.)
- Test both success and error cases

❌ **DON'T**:
- Skip regression tests before OPS promotion
- Ignore test failures ("it works on my machine")
- Test against unstable/changing data
- Make tests too specific (exact values, timestamps)
- Forget to test backward compatibility

## Developer Workflows

### Workflow 1: First-Time Setup

Set up golden reference files for the first time:

```bash
# 1. Make sure you have test dependencies
poetry install --with test

# 2. Capture golden reference files from UAT
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py

# 3. Review captured files
ls -lh tests/regression/fixtures/*/

# 4. Run all tests including golden tests
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v

# 5. Commit reference files
git add tests/regression/fixtures/
git commit -m "Add golden reference files for regression testing"
```

### Workflow 2: Adding New Fields to API

Complete workflow when adding new fields (e.g., adding `my_new_field` to Node):

```bash
# 1. Add field to API code and unit tests
# ... code changes ...

# 2. Run local unit tests
poetry run pytest tests/test_api.py -v

# 3. Deploy to UAT
# ... deployment ...

# 4. Test manually that new field works
curl "https://uat-api/timeseries?feature=Node&feature_id=81292900150551&start_time=2024-02-06T00:00:00Z&end_time=2024-02-07T00:00:00Z&fields=node_id,my_new_field"

# 5. Run regression tests (golden tests will fail - expected!)
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m golden

# 6. Review failure - verify it shows new field added
# Output should show: "Extra fields: {'my_new_field'}"

# 7. Recapture reference files with new field
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature node

# 8. Re-run golden tests (should now pass)
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m golden

# 9. Run full test suite
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v

# 10. Commit changes
git add tests/regression/fixtures/node/
git commit -m "Add my_new_field to Node API and update reference files"
```

### Workflow 3: After Deploying to UAT

Quick verification after deployment:

```bash
# 1. Run smoke tests first (< 30 sec)
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_smoke.py -v -m smoke

# 2. If smoke passes, run full suite excluding slow tests (5-10 min)
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m "not slow"

# 3. If everything passes, deployment is good ✓
```

### Workflow 4: Before Promoting UAT → OPS

Complete validation before production deployment:

```bash
# 1. Run full regression suite on UAT (10-15 min)
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v --html=uat-report.html --self-contained-html

# 2. Review HTML report
open uat-report.html

# 3. If all tests pass, get approval and deploy to OPS

# 4. After OPS deployment, run smoke tests (< 30 sec)
HYDROCRON_ENV=ops poetry run pytest tests/regression/test_smoke.py -v -m smoke

# 5. Run full OPS validation (10-15 min)
HYDROCRON_ENV=ops poetry run pytest tests/regression/ -v --html=ops-report.html
```

### Workflow 5: Investigating Schema Differences

When debugging table schema issues:

```bash
# 1. Scan DynamoDB tables in UAT
AWS_PROFILE=uat poetry run python tests/regression/dev-utils/scan-dynamodb.py

# Output shows:
# - All 6 main tables (3 old + 3 new D tables)
# - Columns in each table
# - Comparison showing:
#   ❌ Columns removed (in old only)
#   ✨ Columns added (in new D only)

# 2. Identify what changed between versions

# 3. Update tests/code accordingly
```

### Workflow 6: Updating Test Data

When stable test data changes (feature IDs, dates):

```bash
# 1. Update STABLE_TEST_DATA in tests/regression/conftest.py
# Edit conftest.py and change feature_id, start_time, end_time

# 2. Recapture ALL reference files with new test data
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py

# 3. Run all tests to verify
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v

# 4. Commit changes
git add tests/regression/conftest.py tests/regression/fixtures/
git commit -m "Update stable test data and reference files"
```

### Workflow 7: Testing Version D Features

When testing new Version D fields before OPS deployment:

```bash
# 1. Run all Version D field tests
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m version_d

# 2. Run backward compatibility tests
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_version_d_fields.py::TestVersionDBackwardCompatibility -v

# 3. Verify old queries still work
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m "not version_d"

# 4. If all pass, Version D is ready for OPS
```

## Getting Help

- See main `README.md` for detailed documentation
- Check `SETUP.md` for environment setup
- Review `utils.py` for available helper functions
- Check `dev-utils/README.md` for tool usage
- Check `fixtures/README.md` for golden file details
- Ask in #hydrocron-dev Slack channel
