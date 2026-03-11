# Golden Reference Files

This directory contains "golden" reference files - known-good API responses used for regression testing.

## Purpose

Golden file testing validates that API responses haven't changed unexpectedly. Tests compare live API responses against these reference files to detect:

- ✅ Field additions or removals
- ✅ Data format changes
- ✅ Response structure changes
- ✅ Unexpected behavioral changes

## Directory Structure

```
fixtures/
├── reach/
│   ├── reach_basic.geojson              # Basic reach query (GeoJSON)
│   ├── reach_basic.csv                  # Basic reach query (CSV)
│   ├── reach_discharge.csv              # Reach with discharge fields
│   └── reach_comprehensive.geojson      # Reach with many fields
├── node/
│   ├── node_basic.geojson               # Basic node query (GeoJSON)
│   ├── node_basic.csv                   # Basic node query (CSV)
│   ├── node_wse_sm.csv                  # Node with wse_sm fields (Version D)
│   └── node_comprehensive.geojson       # Node with many fields
└── priorlake/
    ├── lake_basic.geojson               # Basic lake query (GeoJSON)
    ├── lake_basic.csv                   # Basic lake query (CSV)
    ├── lake_qual_f_b.csv                # Lake with qual_f_b field (Version D)
    └── lake_comprehensive.geojson       # Lake with many fields
```

## Capturing Reference Files

### Initial Capture (First Time)

```bash
# Capture all reference files from UAT
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py
```

### Updating After Intentional Changes

When you intentionally change API behavior:

```bash
# Capture specific feature
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py --feature reach

# Capture all
HYDROCRON_ENV=uat poetry run python tests/regression/dev-utils/capture_reference_files.py
```

### Workflow

1. **Make API changes** (add fields, change behavior, etc.)
2. **Deploy to UAT**
3. **Run tests** - Golden tests will fail
4. **Review changes** - Verify API behavior is correct
5. **Recapture references** - Update golden files
6. **Commit changes** - Include updated reference files in PR
7. **Tests pass** - Golden tests now pass with new behavior

## Running Golden Tests

```bash
# Run all golden tests
HYDROCRON_ENV=uat poetry run pytest tests/regression/ -v -m golden

# Run for specific feature
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_reach_api.py::TestReachGoldenFiles -v
```

## What Gets Ignored

These fields are automatically ignored in comparisons (they change between deployments):

- `ingest_time` - Changes with each data ingestion
- `crid` - Processing run ID changes
- `granuleUR` - Granule identifier may change

See `utils.py` for normalization functions that handle this.

## When Tests Fail

### Golden Test Failed ❌

**Cause**: API response doesn't match reference file

**Action**:
1. **Check if change was intentional**
   - Did you add/remove fields?
   - Did you change data processing?
   - Expected behavior change?

2. **If intentional**: Recapture reference files
   ```bash
   HYDROCRON_ENV=uat poetry run python tests/regression/capture_reference_files.py
   ```

3. **If NOT intentional**: This is a regression!
   - Review recent changes
   - Check API logs
   - Investigate why behavior changed

### Reference File Missing ⚠️

**Cause**: Reference file doesn't exist yet

**Action**: Capture reference files
```bash
HYDROCRON_ENV=uat poetry run python tests/regression/capture_reference_files.py
```

## Best Practices

✅ **DO**:
- Capture from a known-good deployment (UAT after testing)
- Review captured files before committing
- Update references when API behavior changes intentionally
- Document why references were updated in commit message
- Keep reference files under version control

❌ **DON'T**:
- Capture from broken deployments
- Commit references without review
- Update references to make tests pass without understanding why they failed
- Ignore golden test failures
- Capture from OPS as source of truth (use UAT)

## File Format

### GeoJSON Files (.geojson)
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {...},
      "properties": {
        "reach_id": "34296500851",
        "time_str": "2024-02-10T00:00:00Z",
        "wse": 123.45,
        ...
      }
    },
    ...
  ]
}
```

### CSV Files (.csv)
```csv
reach_id,time_str,wse,slope,width
34296500851,2024-02-10T00:00:00Z,123.45,0.001,50.2
34296500851,2024-02-11T00:00:00Z,123.50,0.001,50.3
...
```

## Maintenance

Review and update reference files:
- When adding new API fields
- When changing data processing logic
- When upgrading SWOT data versions
- Periodically (quarterly) to ensure they're still valid

## Questions?

- See `tests/regression/README.md` for overall testing guide
- See `tests/regression/utils.py` for comparison logic
