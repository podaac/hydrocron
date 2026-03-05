# Regression Tests Setup Complete ✓

## What Was Created

### 1. Test Directory Structure
```
tests/regression/
├── __init__.py              # Package marker
├── conftest.py              # Test configuration and fixtures
├── test_api_regression.py   # Regression test suite
├── README.md                # Usage documentation
└── SETUP.md                 # This file
```

### 2. Test Suite Components

**test_api_regression.py** includes:
- ✓ Reach queries (GeoJSON, CSV, Accept headers)
- ✓ Lake queries (Prior lakes)
- ✓ Error handling (missing params, invalid features)
- ✓ Output format validation (valid GeoJSON, CSV)
- ✓ API availability smoke tests

### 3. GitHub Actions Workflow
- ✓ `.github/workflows/regression-tests.yml`
- Can be run manually via workflow_dispatch
- Can be called by other workflows after deployment
- Uploads test results as artifacts

### 4. Dependencies
- ✓ Added `requests` to `[tool.poetry.group.test.dependencies]`

## Quick Start

### 1. Install Dependencies
```bash
poetry install --with test
```

### 2. Run Tests Locally

Against UAT:
```bash
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v
```

Against OPS:
```bash
HYDROCRON_ENV=ops poetry run pytest tests/regression/ -v
```

### 3. Run via GitHub Actions

1. Go to **Actions** tab in GitHub
2. Select **Regression Tests** workflow
3. Click **Run workflow**
4. Select environment (UAT or OPS)
5. Click **Run workflow**

## Integration with Deployment

### Option 1: Add to build.yml (Recommended for automated testing)

Add this job to `.github/workflows/build.yml` after the `deploy` job:

```yaml
  regression-tests:
    name: Regression Tests
    needs: [build, deploy]
    if: |
      github.ref == 'refs/heads/develop' ||
      startsWith(github.ref, 'refs/heads/release') ||
      github.event_name == 'workflow_dispatch'
    uses: ./.github/workflows/regression-tests.yml
    with:
      environment: ${{ needs.build.outputs.deploy_env == 'SIT' && 'uat' || (needs.build.outputs.deploy_env == 'UAT' && 'uat' || 'ops') }}
```

This will automatically run regression tests after each deployment.

### Option 2: Manual Trigger (Current setup)

Run regression tests manually after verifying deployment is complete.

## Configuration

### API URLs
Configured in `tests/regression/conftest.py`:
- **UAT**: https://soto.podaac.uat.earthdatacloud.nasa.gov/hydrocron/v1/timeseries
- **OPS**: https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries

### Test Feature IDs
Configured in `tests/regression/test_api_regression.py`:
- **Reach**: `71224100223`
- **Lake**: `9120274662`

Update these if the features don't exist in your deployed data.

## Next Steps

1. **Verify test data**: Ensure the test feature IDs exist in your deployed environments
2. **Run initial tests**: Test against UAT to verify everything works
3. **Update CI/CD** (optional): Add regression tests to build.yml for automatic testing
4. **Monitor results**: Review test results after each deployment

## Troubleshooting

### Tests are skipped
- Ensure `HYDROCRON_ENV` environment variable is set
- Valid values: `uat` or `ops`

### Connection errors
- Verify API is deployed and accessible
- Check URLs in `conftest.py`
- Verify network connectivity

### Feature not found errors
- Update `TEST_REACH_ID` and `TEST_LAKE_ID` constants
- Use feature IDs that exist in your environment

## Test Philosophy

These regression tests:
- ✓ Test real deployed API endpoints
- ✓ Verify API is up and responding correctly
- ✓ Check response formats and structures
- ✗ Don't verify exact data values (data changes)
- ✗ Don't require mocked services
- ✗ Don't replace unit tests

Use these tests to verify successful deployments and catch integration issues early.
