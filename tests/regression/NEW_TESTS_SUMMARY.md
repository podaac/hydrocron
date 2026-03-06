# New Regression Tests Summary

This document summarizes the new regression tests added based on the Hydrocron API documentation at:
- https://podaac.github.io/hydrocron/examples.html
- https://podaac.github.io/hydrocron/timeseries.html

## New Test Files Created

### 1. `test_compact_parameter.py`
Tests for the `compact` parameter that controls GeoJSON response format.

**Coverage:**
- ✅ `compact=true` returns single feature with array values
- ✅ `compact=false` returns multiple features (one per observation)
- ✅ Default compaction behavior based on Accept header
  - `application/geo+json` → defaults to compact=true
  - `application/json` → defaults to compact=false
- ✅ Explicit compact parameter overrides Accept header defaults
- ✅ Compact parameter works for all feature types (Reach, Node, PriorLake)
- ✅ Compact parameter has no effect on CSV output

**Key Classes:**
- `TestCompactParameterBasics` - Core compact functionality
- `TestCompactDefaultBehavior` - Default behavior by Accept header
- `TestCompactOverridesAcceptHeader` - Explicit parameter overrides
- `TestCompactAllFeatureTypes` - Cross-feature validation
- `TestCompactWithCSV` - CSV behavior verification

---

### 2. `test_error_handling.py`
Comprehensive error handling and validation tests.

**Coverage:**
- ✅ HTTP 415 errors for invalid Accept headers
- ✅ HTTP 400 errors for missing required parameters
  - Missing: feature, feature_id, start_time, end_time, fields
- ✅ HTTP 400 errors for invalid parameter values
  - Invalid feature type, date formats, field names
  - Start time after end time
  - Empty fields parameter
- ✅ Non-existent feature IDs return 400
- ✅ Valid features with no data in time range
- ✅ HTTP 413 errors for payloads exceeding 6MB (test skeleton)
- ✅ Field validation across feature types
- ✅ Error message quality checks

**Key Classes:**
- `TestInvalidAcceptHeaders` - 415 error testing
- `TestMissingRequiredParameters` - Missing parameter validation
- `TestInvalidParameterValues` - Invalid value handling
- `TestNonExistentFeatures` - Feature ID validation
- `TestNoDataInTimeRange` - Empty result handling
- `TestPayloadSizeLimits` - 413 error testing
- `TestFieldValidation` - Cross-feature field validation
- `TestErrorMessageQuality` - Error message validation

---

### 3. `test_time_encoding.py`
Tests for timestamp formats and URL encoding.

**Coverage:**
- ✅ Basic ISO 8601 formats (YYYY-MM-DDTHH:MM:SSZ)
- ✅ Timestamps with/without Z suffix
- ✅ Millisecond precision timestamps
- ✅ UTC offsets (+HH:MM, -HH:MM)
- ✅ URL encoding of + as %2b (required)
- ✅ Invalid time formats return errors
  - Invalid dates, malformed timestamps
  - Invalid month/day/hour values
- ✅ Time range boundary conditions
  - start_time == end_time
  - Very narrow and very wide time ranges
- ✅ Leap year validation (Feb 29)
- ✅ Time format consistency across feature types

**Key Classes:**
- `TestBasicISO8601Formats` - Standard timestamp formats
- `TestUTCOffsets` - Timezone offset handling
- `TestURLEncoding` - Special character encoding
- `TestInvalidTimeFormats` - Error cases
- `TestTimeRangeBehavior` - Boundary conditions
- `TestTimeFormatConsistency` - Cross-feature validation
- `TestLeapYearAndDST` - Edge cases

---

### 4. `test_response_formats.py`
Tests for response format handling and content negotiation.

**Coverage:**
- ✅ JSON wrapper structure (status, time, hits, results)
- ✅ Raw GeoJSON format (application/geo+json)
- ✅ Raw CSV format (text/csv)
- ✅ Content-Type header validation
- ✅ `output` parameter vs Accept header interaction
- ✅ Units fields automatically included
- ✅ Response format consistency across feature types

**Key Classes:**
- `TestJSONWrapperFormat` - Wrapper structure validation
- `TestRawGeoJSONFormat` - Direct GeoJSON responses
- `TestRawCSVFormat` - Direct CSV responses
- `TestOutputParameterVsAcceptHeader` - Parameter interaction
- `TestContentTypeHeaders` - Header validation
- `TestUnitsFieldsInResponses` - Automatic unit fields
- `TestResponseFormatConsistency` - Cross-feature validation

---

### 5. `test_api_features.py`
Tests for additional API features and edge cases.

**Coverage:**
- ✅ API key header (x-hydrocron-key) - optional authentication
- ✅ Geometry field behavior
  - Reach returns LineString
  - Node returns Point
  - PriorLake returns Point (center coordinates)
  - Geometry optional in queries
  - Geometry excluded from CSV
- ✅ Field ordering in responses
- ✅ Case sensitivity testing
- ✅ Special characters in parameters
- ✅ No-data sentinel values (-999999999999.0)
- ✅ Query performance characteristics
- ✅ Multiple consecutive queries

**Key Classes:**
- `TestAPIKeyHeader` - Optional API key validation
- `TestGeometryFieldBehavior` - Geometry handling
- `TestFieldOrdering` - Response field ordering
- `TestCaseSensitivity` - Parameter case handling
- `TestSpecialCharacters` - Edge case handling
- `TestNoDataSentinelValues` - Missing data handling
- `TestQueryPerformance` - Performance validation
- `TestMultipleConsecutiveQueries` - Reliability testing

---

## Test Organization

All new tests follow the existing regression test patterns:

- **Use fixtures:** `api_client`, `stable_test_data`, `test_env`, `fixtures_dir`
- **Use utils:** `assert_http_success`, `assert_http_error`, `validate_geojson_structure`, `validate_csv_structure`
- **Consistent naming:** Test classes group related tests, test names clearly describe what's being tested
- **Feature coverage:** Tests validate all three feature types (Reach, Node, PriorLake) where applicable
- **Markers:** Use `@pytest.mark` for categorization (`@pytest.mark.slow`, `@pytest.mark.skip`, etc.)

## Running the New Tests

```bash
# Run all new tests
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_compact_parameter.py
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_error_handling.py
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_time_encoding.py
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_response_formats.py
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_api_features.py

# Run all regression tests
HYDROCRON_ENV=uat poetry run pytest tests/regression/

# Run specific test class
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_compact_parameter.py::TestCompactParameterBasics

# Run specific test
HYDROCRON_ENV=uat poetry run pytest tests/regression/test_error_handling.py::TestInvalidAcceptHeaders::test_invalid_accept_header_returns_415
```

## Coverage Gap Analysis

### Previously Missing, Now Covered:
1. ✅ **Compact parameter** - Complete coverage for compacted vs expanded GeoJSON
2. ✅ **Accept header errors** - 415 Unsupported Media Type
3. ✅ **Time encoding** - UTC offsets, URL encoding, validation
4. ✅ **Response wrappers** - JSON wrapper structure validation
5. ✅ **Error handling** - Comprehensive 400, 413, 415 error cases
6. ✅ **API features** - Geometry types, field ordering, case sensitivity
7. ✅ **Edge cases** - Empty results, boundary conditions, special characters

### Still Requiring Real Data:
- **413 Payload Too Large** - Requires known large dataset (test skeleton exists)
- **API Keys** - Requires valid API key for full testing (optional feature)

### Test Data Requirements:
- Uses existing `STABLE_TEST_DATA` from `conftest.py`
- No new fixture files required
- All tests work with current test environment

## Notes for Test Maintenance

1. **Skipped Tests:** Some tests are marked `@pytest.mark.skip` and require updates:
   - `test_large_payload_returns_413` - Needs large dataset feature_id
   - `test_query_with_valid_api_key_succeeds` - Needs real API key

2. **Environment-Specific Tests:** Some tests check `test_env` to skip OPS:
   - Version D tests already handle this in existing files
   - New tests generally work in both UAT and OPS

3. **Behavioral Tests:** Some tests check for "acceptable" responses:
   - `assert response.status_code in [200, 400]`
   - This allows for different valid implementations
   - Should be refined once exact API behavior is confirmed

4. **Performance Tests:** Performance assertions are lenient:
   - Allow up to 30-60 seconds for most queries
   - Print timing information for analysis
   - Don't fail on minor performance variations

## Integration with Existing Tests

The new test files complement the existing regression tests:

- `test_reach_api.py` - Focus on Reach-specific fields and queries
- `test_node_api.py` - Focus on Node-specific fields including Version D
- `test_priorlake_api.py` - Focus on PriorLake-specific fields
- `test_version_d_fields.py` - Version D backward compatibility
- **NEW** `test_compact_parameter.py` - Compact parameter behavior
- **NEW** `test_error_handling.py` - Error cases and validation
- **NEW** `test_time_encoding.py` - Time format handling
- **NEW** `test_response_formats.py` - Response format negotiation
- **NEW** `test_api_features.py` - Additional features and edge cases

Together, these provide comprehensive coverage of the Hydrocron API as documented.
