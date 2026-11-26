# Hydrocron Documentation

<a href="#"><img src="_generated_version.svg" alt="Hydrocron version badge" align="left"></a>
<a href="https://zenodo.org/records/11176233"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.11176233.svg" alt="DOI badge" align="left"></a>

Hydrocron is an API that repackages hydrology datasets from the Surface Water and Ocean Topography (SWOT) satellite into formats that make time-series analysis easier.

SWOT data is archived as individually timestamped shapefiles, which would otherwise require users to perform potentially thousands of file IO operations per river feature to view the data as a timeseries. Hydrocron makes this possible with a single API call.

Original SWOT data is archived at NASA's [Earthdata Cloud](https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/swot).

:::{tip} ✨ **NEW:** Get a river reach and all of its nodes in one request ✨
Use the [](#node_fields) parameter to get a reach and all of its nodes in a single request, instead of one request per node. See the [example](examples.md#get-time-series-csv-for-river-reach-and-its-nodes).
:::

Datasets included in Hydrocron:

### Version D (Default)
- [SWOT Level 2 River Single-Pass Vector Data Product, Version D](https://www.earthdata.nasa.gov/data/catalog/pocloud-swot-l2-hr-riversp-d-d)
- [SWOT Level 2 Lake Single-Pass Vector Data Product, Version D](https://www.earthdata.nasa.gov/data/catalog/pocloud-swot-l2-hr-lakesp-d-d)

### Version 2.0 (reaches only)
- [SWOT Level 2 River Single-Pass Vector Data Product, Version 2.0](https://www.earthdata.nasa.gov/data/catalog/pocloud-swot-l2-hr-riversp-2.0-2.0): SoS Discharge, reach IDs, times, and SWORD fields only
- [SWOT Level 4 Sword of Science River Discharge Products, Version 3](https://doi.org/10.5067/SWOT-SOS-RD3)

:::{warning} Version 2.0 retirement
As of **December 1, 2026**, SWOT Level 2 Version 2.0 data is retired from Hydrocron. Version 2.0 node and lake data, and the Level 2 measurement fields on Version 2.0 reaches (such as `wse`), return HTTP 410. Version 2.0 reaches still serve the SWOT Level 4 SoS Discharge fields and the [Version 2.0 reach fields](#version-2-0-reach-fields) (IDs, times, SWORD fields). Use Version D for all other data.
:::

:::{important} Version D is the default
To query Version 2.0 reaches (SoS Discharge), use `collection_name=SWOT_L2_HR_RiverSP_2.0`. Also, some node and reach IDs have changed from version 2.0 to version D. See the [versioning guide](user-guide/versioning.md) and [SWORD Version Differences](user-guide/sword-versions.md) for details.
:::
