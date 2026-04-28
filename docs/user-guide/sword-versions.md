(sword-versions)=
# SWORD Version Differences

River reach and node IDs are defined by the SWOT River Database (SWORD). Version C/2.0 and Version D of the SWOT RiverSP data products were produced using different versions of SWORD:

| Collection Version | SWORD Version | Zenodo DOI |
|--------------------|---------------|------------|
| Version C / 2.0    | SWORD v16  | [10.5281/zenodo.10013982](https://zenodo.org/records/10013982) |
| Version D          | SWORD v17b | [10.5281/zenodo.15299138](https://zenodo.org/records/15299138) |

## What changed in SWORD v17b

SWORD v17b introduced the following changes relative to v16:

- "Type" classification updated for approximately 1,662 reaches and their associated nodes globally
- Updates to reach and node lengths
- Correction of a bug in node length calculation (affecting less than 2% of reaches)

## Impact on Hydrocron queries

Because reach and node definitions changed between SWORD versions, a small number of feature IDs differ between Version C/2.0 and Version D data. Users querying the same geographic location across both versions should be aware that results may not align exactly.

The SWORD version used for a given observation can be returned by including `sword_version` in the [](fields) parameter.

## Example: Node ID 43210100080371

The following example demonstrates how node ID `43210100080371` resolves to different geographic locations depending on which collection version is queried. This node is one of the approximately 1,662 reaches affected by the SWORD v16 → v17b update.

**Version 2.0 request:**

[`GET /timeseries?feature=Node&feature_id=43210100080371&collection_name=SWOT_L2_HR_RiverSP_2.0&output=csv&start_time=2025-01-01T00:00:00Z&end_time=2025-01-31T23:59:59Z&fields=time_str,wse,lat,lon,sword_version`](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?collection_name=SWOT_L2_HR_RiverSP_2.0&feature=Node&feature_id=43210100080371&output=csv&start_time=2025-01-01T00%3A00%3A00Z&end_time=2025-01-31T23%3A59%3A59Z&fields=time_str,wse,lat,lon,sword_version)

```
time_str,wse,lat,lon,sword_version,wse_units,lat_units,lon_units
2025-01-10T10:49:10Z,8.9169,37.5212176,118.3068612,16,m,degrees_north,degrees_east
2025-01-30T18:20:39Z,9.12682,37.52121762,118.3058295,16,m,degrees_north,degrees_east
2025-01-31T07:34:15Z,9.26057,37.52126843,118.3069193,16,m,degrees_north,degrees_east
```

**Version D request (Default):**

[`GET /timeseries?feature=Node&feature_id=43210100080371&output=csv&start_time=2025-01-01T00:00:00Z&end_time=2025-01-31T23:59:59Z&fields=time_str,wse,lat,lon,sword_version`](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=43210100080371&output=csv&start_time=2025-01-01T00%3A00%3A00Z&end_time=2025-01-31T23%3A59%3A59Z&fields=time_str,wse,lat,lon,sword_version)

```
time_str,wse,lat,lon,sword_version,wse_units,lat_units,lon_units
2025-01-10T10:49:26Z,9.96666,37.44975457,118.2463678,7b,m,degrees_north,degrees_east
2025-01-30T18:20:50Z,10.09558,37.44958043,118.2461186,7b,m,degrees_north,degrees_east
2025-01-31T07:34:31Z,10.16265,37.44973246,118.246709,7b,m,degrees_north,degrees_east
```

The Version 2.0 response places the node at approximately **37.521°N, 118.307°E**, while the Version D response places the same node ID at approximately **37.450°N, 118.246°E** — a difference of roughly 9 km. These are physically distinct locations on the river network. The discrepancy is a direct result of the SWORD v16 → v17b update, which reclassified this reach type and reassigned its node geometry.

:::{warning}
Do not combine time-series data for the same node ID across Version 2.0 and Version D without first verifying that the coordinates are consistent. Where coordinates differ, the two records refer to different physical locations.
:::
