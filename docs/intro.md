# Hydrocron Documentation

Hydrocron is an API that repackages hydrology datasets from the Surface Water and Ocean Topography (SWOT) satellite into formats that make time-series analysis easier.

SWOT data is archived as individually timestamped shapefiles, which would otherwise require users to perform potentially thousands of file IO operations per river feature to view the data as a timeseries. Hydrocron makes this possible with a single API call.

Original SWOT data is archived at NASA's [Physical Oceanography Distributed Active Archive Center (PO.DAAC)](https://podaac.jpl.nasa.gov/SWOT).

Datasets included in Hydrocron:

- [SWOT Level 2 River Single-Pass Vector Data Product, Version 2.0](https://podaac.jpl.nasa.gov/dataset/SWOT_L2_HR_RiverSP_2.0)
