# SWOT Data Versioning

SWOT data periodically undergoes reprocessing, where data products are recreated from the original observations with updated processing algorithms. This results in a new data collection version.

In version 1.6.0, Hydrocron will support multiple versions of SWOT data collections. To specify which collection you want to retrieve data from, use the new [](collection_name) request parameter.

SWOT collection names supported by Hydrocron inclcude:

Version C/2.0 (default):

- SWOT_L2_HR_RiverSP_2.0
- SWOT_L2_HR_RiverSP_reach_2.0
- SWOT_L2_HR_RiverSP_node_2.0
- SWOT_L2_HR_LakeSP_2.0
- SWOT_L2_HR_LakeSP_prior_2.0

Version D (coming early 2025):

- SWOT_L2_HR_RiverSP_D
- SWOT_L2_HR_RiverSP_reach_D
- SWOT_L2_HR_RiverSP_node_D
- SWOT_L2_HR_LakeSP_D
- SWOT_L2_HR_LakeSP_prior_D

## Parent Collections and Sub Collections

SWOT hydrology data products are organized into parent and child collections. The parent collections indicate the general feature type (river or lake):

- SWOT_L2_HR_RiverSP_2.0
- SWOT_L2_HR_LakeSP_2.0

and the sub collections indicate the specific feature or subtype of data (reach or node for rivers, prior, observed, or unassigned for lakes)

- SWOT_L2_HR_RiverSP_reach_2.0
- SWOT_L2_HR_RiverSP_node_2.0
- SWOT_L2_HR_LakeSP_prior_2.0

The SWOT Product Description Documents for SWOT Rivers and Lakes contain more information about the differences between subtypes of data. Note that currently Hydrocron does not support the lake subtypes of 'observed' and 'unassigned'.

## Collection name and feature type

Specifying sub collections in requests to Hydrocron is not necessary to distinguish the type of data to return, as you also specify whether you are looking for Reach, Node, or PriorLake data with the [](feature) parameter.

Note that if you mix feature types in the [](feature) and [](collection_name) parameters, the [](collection_name) parameter takes precedence. If you request [](feature_id) for a feature type that is different that what you request in [](collection_name), you will get an error.

For example, here we request feature=Reach with a feature_id= a reach feature, but collection_name=SWOT_L2_HR_LakeSP_2.0. In this case you will get an error because Hydrocron will try to query the Lakes table for the reach_id.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&collection_name=SWOT_L2_HR_LakeSP_2.0&fields=reach_id,time_str,wse,slope](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&collection_name=SWOT_L2_HR_LakeSP_2.0&fields=reach_id,time_str,wse,slope)

## CRID

The CRID indicates the version of the processing software that was used to generate the data. When data is first delivered to PO.DAAC and ingested into the archive, the CRID will be the forward-streaming version. If that data is later reprocessed, the CRID will be updated to indicate the reprocessing version. Hydrocron only keeps one version of a given observation at a time. If the data has been reprocessed, it will overwrite the earlier forward-streaming version with the reprocessed version.

Note that you cannot query by CRID, but you can return it as a field in the request and see which CRID was used to process the data that is being returned.
