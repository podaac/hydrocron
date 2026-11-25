(sword-versions)=
# SWORD Version Differences

River reach and node IDs are defined by the SWOT River Database (SWORD). Version 2.0 and Version D of the SWOT RiverSP data products were produced using different versions of SWORD:

| Collection Version | SWORD Version | Zenodo DOI |
|--------------------|---------------|------------|
| Version 2.0    | SWORD v16  | [10.5281/zenodo.10013982](https://zenodo.org/records/10013982) |
| Version D          | SWORD v17b | [10.5281/zenodo.15299138](https://zenodo.org/records/15299138) |

## What changed in SWORD v17b

SWORD v17b introduced the following changes relative to v16:

- "Type" classification updated for approximately 1,662 reaches and their associated nodes globally
- Updates to reach and node lengths
- Correction of a bug in node length calculation (affecting less than 2% of reaches)

## Impact on Hydrocron queries

Because reach and node definitions changed between SWORD versions, a small number of feature IDs differ between Version 2.0 and Version D data. Users querying the same geographic location across both versions should be aware that results may not align exactly.

The SWORD version used for a given observation can be returned by including `sword_version` in the [](#fields) parameter.

### Example: Reach ID 43210100081

The following example demonstrates how reach ID `43210100081` resolves to different geographic locations depending on which collection version is queried. This reach is one of the approximately 1,662 reaches affected by the SWORD v16 → v17b update. (Version 2.0 nodes are retired, so the example uses the reach center fields `p_lat` and `p_lon`, which Version 2.0 reaches still serve.)

**Version 2.0 request:**

[`GET /timeseries?feature=Reach&feature_id=43210100081&collection_name=SWOT_L2_HR_RiverSP_2.0&output=csv&start_time=2025-01-01T00:00:00Z&end_time=2025-01-31T23:59:59Z&fields=time_str,p_lat,p_lon,sword_version`](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?collection_name=SWOT_L2_HR_RiverSP_2.0&feature=Reach&feature_id=43210100081&output=csv&start_time=2025-01-01T00%3A00%3A00Z&end_time=2025-01-31T23%3A59%3A59Z&fields=time_str,p_lat,p_lon,sword_version)

```
time_str,p_lat,p_lon,sword_version,p_lat_units,p_lon_units
2025-01-09T21:35:33Z,37.53960479,118.3126393,16,degrees_north,degrees_east
2025-01-10T10:49:10Z,37.53960479,118.3126393,16,degrees_north,degrees_east
2025-01-30T18:20:39Z,37.53960479,118.3126393,16,degrees_north,degrees_east
2025-01-31T07:34:15Z,37.53960479,118.3126393,16,degrees_north,degrees_east
```

**Version D request (Default):**

[`GET /timeseries?feature=Reach&feature_id=43210100081&output=csv&start_time=2025-01-01T00:00:00Z&end_time=2025-01-31T23:59:59Z&fields=time_str,p_lat,p_lon,sword_version`](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=43210100081&output=csv&start_time=2025-01-01T00%3A00%3A00Z&end_time=2025-01-31T23%3A59%3A59Z&fields=time_str,p_lat,p_lon,sword_version)

```
time_str,p_lat,p_lon,sword_version,p_lat_units,p_lon_units
2025-01-09T21:35:44Z,37.4650316,118.2539081,17b,degrees_north,degrees_east
2025-01-10T10:49:26Z,37.4650316,118.2539081,17b,degrees_north,degrees_east
2025-01-30T18:20:49Z,37.4650316,118.2539081,17b,degrees_north,degrees_east
2025-01-31T07:34:31Z,37.4650316,118.2539081,17b,degrees_north,degrees_east
```

The Version 2.0 response places the reach center at approximately **37.540°N, 118.313°E**, while the Version D response places the same reach ID at approximately **37.465°N, 118.254°E** — a difference of roughly 10 km. These are physically distinct locations on the river network. The discrepancy is a direct result of the SWORD v16 → v17b update, which reclassified this reach type and reassigned its geometry.

:::{warning}
Do not combine time-series data for the same reach ID across Version 2.0 and Version D without first verifying that the coordinates are consistent. Where coordinates differ, the two records refer to different physical locations.
:::
