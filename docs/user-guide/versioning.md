# SWOT Data Versioning

SWOT data periodically undergoes reprocessing, where data products are recreated from the original observations with updated processing algorithms. This results in a new data collection version.

Hydrocron supports multiple versions of SWOT data collections. As of version 1.8.0, Version D is the default — omitting the optional _collection_name_ parameter will return Version D data. To retrieve data from a specific collection version, use the [](#collection_name) request parameter.

As of version 1.9.0, Hydrocron also supports the SWOT Level 4 SoS Discharge products, which themselves are generated using (in part) SWOT Level 2 data from an associated version. To request SWOT_L4_HR_DAWG_SOS_DISCHARGE_V3, corresponding to SWOT L2 RiverSP v2.0, please specify `collection_name=SWOT_L2_HR_RiverSP_2.0` in your request

SWOT collection names supported by Hydrocron include:

Version D (default):

- SWOT_L2_HR_RiverSP_D
- SWOT_L2_HR_RiverSP_reach_D
- SWOT_L2_HR_RiverSP_node_D
- SWOT_L2_HR_LakeSP_D
- SWOT_L2_HR_LakeSP_prior_D

Version 2.0 (reaches only, [Version 2.0 reach fields](#version-2-0-reach-fields)):

- SWOT_L2_HR_RiverSP_2.0
- SWOT_L2_HR_RiverSP_reach_2.0
- SWOT_L4_HR_DAWG_SOS_DISCHARGE_V3

Retired on December 1, 2026 (return HTTP 410; use the Version D name instead):

- SWOT_L2_HR_RiverSP_node_2.0, and `feature=Node` or [](#node_fields) with a Version 2.0 river collection
- SWOT_L2_HR_LakeSP_2.0
- SWOT_L2_HR_LakeSP_prior_2.0

(version-2-0-reach-fields)=
## Version 2.0 reach fields

Version 2.0 reaches serve only the SoS Discharge fields and the fields below (IDs, times, pass and granule details, geometry, SWORD topology and SWORD prior fields). Units come with each field. Requesting any other reach field with a Version 2.0 collection returns HTTP 410, listing the fields no longer served; use `collection_name=SWOT_L2_HR_RiverSP_D` for them. An unknown field name still returns HTTP 400.

```
'reach_id', 'time', 'time_tai', 'time_str', 'p_lat', 'p_lon', 'river_name',
'sos_consensus_q', 'sos_hivdi_q', 'sos_metroman_q', 'sos_momma_q',
'sos_sad_q', 'sos_sic4dvar_q', 'sos_lakeflow_q', 'swot_discharge_reanalysis',
'range_start_time', 'range_end_time', 'cycle_id', 'pass_id', 'continent_id', 'crid',
'sword_version', 'collection_shortname', 'collection_version', 'granuleUR', 'ingest_time',
'geometry', 'rch_id_up', 'rch_id_dn', 'n_reach_up', 'n_reach_dn',
'p_maf', 'p_length', 'p_dist_out', 'p_width', 'p_wse', 'p_n_nodes', 'p_dam_id',
'p_wse_var', 'p_wid_var', 'p_n_ch_max', 'p_n_ch_mod', 'p_low_slp'
```

The `p_*` fields are static values from the SWORD prior river database, not SWOT measurements: `p_wse` and `p_width` are not the measured `wse` and `width`.

## SWORD Version and Feature ID Compatibility

Reach and node IDs are defined by the SWOT River Database (SWORD). Version 2.0 uses SWORD v16, while Version D uses SWORD v17b. A small number of reach and node IDs differ between the two versions as a result. Users comparing data across collection versions should be aware that the same feature ID may not refer to the same geographic feature.

See [SWORD Version Differences](sword-versions.md) for details.

## Parent Collections and Sub Collections

SWOT hydrology data products are organized into parent and child collections. The parent collections indicate the general feature type (river or lake):

- SWOT_L2_HR_RiverSP_D
- SWOT_L2_HR_LakeSP_D

and the sub collections indicate the specific feature or subtype of data (reach or node for rivers, prior, observed, or unassigned for lakes)

- SWOT_L2_HR_RiverSP_reach_D
- SWOT_L2_HR_RiverSP_node_D
- SWOT_L2_HR_LakeSP_prior_D

The SWOT Product Description Documents for SWOT Rivers and Lakes contain more information about the differences between subtypes of data. Note that currently Hydrocron does not support the lake subtypes of 'observed' and 'unassigned'.

## Collection name and feature type

Specifying sub collections in requests to Hydrocron is not necessary to distinguish the type of data to return, as you also specify whether you are looking for Reach, Node, or PriorLake data with the [](#feature) parameter.

Note that if you mix feature types in the [](#feature) and [](#collection_name) parameters, the [](#collection_name) parameter takes precedence. If you request [](#feature_id) for a feature type that is different that what you request in [](#collection_name), you will get an error.

For example, here we request feature=Reach with feature_id=78340600051 (a reach feature), but collection_name=SWOT_L2_HR_LakeSP_D. In this case you will get a 400 error, because a lake collection has no reaches.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&collection_name=SWOT_L2_HR_LakeSP_D&fields=reach_id,time_str,wse,slope](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&collection_name=SWOT_L2_HR_LakeSP_D&fields=reach_id,time_str,wse,slope)

## CRID

The CRID indicates the version of the processing software that was used to generate the data. When data is first delivered to PO.DAAC and ingested into the archive, the CRID will be the forward-streaming version. If that data is later reprocessed, the CRID will be updated to indicate the reprocessing version. Hydrocron only keeps one version of a given observation at a time. If the data has been reprocessed, it will overwrite the earlier forward-streaming version with the reprocessed version.

Note that you cannot query by CRID, but you can return it as a field in the request and see which CRID was used to process the data that is being returned.
