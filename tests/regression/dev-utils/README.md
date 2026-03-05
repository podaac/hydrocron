# Developer Utilities

This directory contains manual utility scripts for developers working with regression tests and DynamoDB.

## Scripts

### capture_reference_files.py

**Purpose**: Generate/update golden reference files for regression testing

**When to use**:
- First time setting up regression tests
- After intentionally changing API behavior
- After adding new fields to the API
- When updating test data

**Usage**:
```bash
# Capture all reference files from UAT
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py

# Capture specific feature only
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature reach
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature node
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature priorlake
```

**Output**: Creates/updates JSON and CSV files in `tests/regression/fixtures/`

**Important**:
- ⚠️ Always capture from a known-good deployment (UAT after testing)
- ⚠️ Review captured files before committing
- ⚠️ Don't capture from broken deployments

### scan-dynamodb.py

**Purpose**: Scan and compare DynamoDB table schemas

**When to use**:
- Debugging schema differences between old and new tables
- Verifying table structures after deployment
- Understanding what columns exist in each table
- Comparing Version 2.0 vs Version D table schemas

**Usage**:
```bash
# Scan tables in current AWS profile
AWS_PROFILE=myprofile poetry run python tests/regression/dev-utils/scan-dynamodb.py
```

**Output**: Console output showing:
- All tables starting with "hydro"
- Column names for each table
- Comparison between old and new D tables

## Workflow Examples

### Adding New API Fields

1. **Add field to API code**

2. **Deploy to UAT**

3. **Test manually**:
   ```bash
   curl "https://uat-api/timeseries?feature=Node&feature_id=...&fields=my_new_field"
   ```

4. **Recapture references**:
   ```bash
   HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature node
   ```

5. **Run regression tests**:
   ```bash
   HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v
   ```

6. **Commit updated references**:
   ```bash
   git add tests/regression/fixtures/
   git commit -m "Add my_new_field and update reference files"
   ```

### Investigating Schema Differences

```bash
# Check what columns exist in deployed tables
AWS_PROFILE=uat poetry run python tests/regression/dev-utils/scan-dynamodb.py

# Compare old vs new table schemas
# Output will show:
# - Columns in old table only (removed)
# - Columns in new D table only (added)
# - Columns in both (unchanged)
```

### First-Time Setup

```bash
# 1. Capture all reference files from UAT
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py

# 2. Review captured files
ls -lh tests/regression/fixtures/*/

# 3. Run tests to verify references work
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m golden

# 4. Commit reference files
git add tests/regression/fixtures/
git commit -m "Add golden reference files for regression testing"
```

## Script Locations

These scripts are in `dev-utils/` to indicate they are:
- ✅ Run manually by developers (not automated)
- ✅ Tools for test maintenance
- ✅ Not part of the automated test suite
- ✅ Safe to run without side effects (except file creation)

## Best Practices

✅ **DO**:
- Run these scripts when needed for test maintenance
- Review outputs before committing
- Use UAT as source for golden references
- Document why you're updating references

❌ **DON'T**:
- Run these in CI/CD pipelines
- Capture from production/OPS as primary source
- Commit outputs without review
- Use these to "fix" failing tests without understanding why they fail

## Getting Help

See:
- `tests/regression/README.md` - Full regression testing guide
- `tests/regression/fixtures/README.md` - Golden file documentation
- `tests/regression/TESTING_GUIDE.md` - Quick reference
