# Overview

Hydrocron has two main API endpoints:

- [timeseries/](/timeseries) which returns all of the timesteps for a single feature ID, and

- timeseriesSubset/ which returns all of the timesteps for all of the features within a given GeoJSON polygon (not yet released)

## Feature ID

The main timeseries endpoint allows users to search by feature ID.

River reach and node ID numbers are defined in the [SWOT River Database (SWORD)](https://doi.org/10.1029/2021WR030054),
and can be browsed using the [SWORD Explorer Interactive Dashboard](https://www.swordexplorer.com/).

SWOT may observe lakes and rivers that do not have an ID in the prior databases. In those cases, hydrology features are added to the Unassigned Lakes data product.
Hydrocron does not currently support Unassigned rivers and lakes.

## Limitations

Data return size is limited to 6 MB. If your query response is larger than this a 413 error will be returned.
