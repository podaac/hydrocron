# Overview

Hydrocron has a main API endpoint:

- [timeseries/](/timeseries) which returns all of the timesteps for a single feature ID.

## Feature ID

The main timeseries endpoint allows users to search by feature ID.

River reach and node ID numbers are defined in the [SWOT River Database (SWORD)](https://doi.org/10.1029/2021WR030054),
and can be browsed using the [SWORD Explorer Interactive Dashboard](https://www.swordexplorer.com/).

SWOT may observe lakes and rivers that do not have an ID in the prior databases. In those cases, hydrology features are added to the Unassigned Lakes data product.
Hydrocron does not currently support Unassigned rivers and lakes.

## Limitations

Data return size is limited to 6 MB. If your query response is larger than this a 413 error will be returned.

## Citation

Cite Hydrocron using the following DOI: [10.5281/zenodo.11176233](https://doi.org/10.5281/zenodo.11176233).
