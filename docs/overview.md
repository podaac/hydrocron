# Overview

Hydrocron has a main API endpoint:

- [timeseries/](/timeseries) which returns all of the timesteps for a single feature ID.

## Feature ID

The main timeseries endpoint allows users to search by feature ID.

River reach and node ID numbers are defined in the [SWOT River Database (SWORD)](https://doi.org/10.1029/2021WR030054),
and can be browsed using the [SWORD Explorer Interactive Dashboard](https://www.swordexplorer.com/).

Lake ID numbers are defined in the PLD (Prior Lake Database) and can be located in the SWOT shapefiles, see [SWOT Product Description Document for the L2_HR_LakeSP Dataset](https://podaac.jpl.nasa.gov/SWOT?tab=datasets-information&sections=about) for more information on lake identifiers.

SWOT may observe lakes and rivers that do not have an ID in the prior databases. In those cases, hydrology features are added to the Unassigned Lakes data product.
Hydrocron does not currently support Unassigned rivers and lakes.

Hydrocron currently includes data from these datasets:

- Reach and node shapefiles from the Level 2 KaRIn high rate river single pass vector product (L2_HR_RiverSP)
- PLD-oriented shapefiles from the Level 2 KaRIn high rate lake single pass vector product (L2_HR_LakeSP)

See this PO.DAAC [page](https://podaac.jpl.nasa.gov/SWOT?tab=datasets-information&sections=about) for more information on SWOT datasets.

## Limitations

Data return size is limited to **6 MB**. If your query response is larger than this a 413 error will be returned.

**For Lake data:** Due to the size of the original polygon in the lake (L2_HR_LakeSP) shapefiles, we are only returning the calculated center point of the lake. This is to facilitate conformance with the GeoJSON specification and center points should not be considered accurate.

## Citation

Cite Hydrocron using the following DOI: [10.5281/zenodo.11176233](https://doi.org/10.5281/zenodo.11176233).
