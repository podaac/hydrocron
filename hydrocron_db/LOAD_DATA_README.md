# How To: Load the Hydrocron Database with data from CMR

## Overview

The main data loading script is hydrocron_db/load_data.py.  This script queries CMR for the data granules from the collection to load into the database.

## Earthdata Login

The script uses the earthaccess python library to handle EDL and token generation. Configure the EDL credentials to use for the CMR query in environment variables called: $EARTHDATA_USERNAME and $EARTHDATA_PASSWORD, or in a .netrc file prior to running the script.

If you skip this configuration, you will be prompted interactively to enter the EDL username and password to use.

## Initial load of the database

Version 1 of Hydrocron uses two database tables, one for SWOT river reaches and one for SWOT river nodes.

To load river reaches into the database, run the load data script directly in a terminal with the following arguments, updating the date after --end_date to today's date.

    poetry run hydrocron_load --table_name hydrocron-swot-reach-table --start_date 2022-12-01T00:00:00 --end_date 2023-10-25T23:59:59 --obscure_data True

To load river nodes into the database, run the load data script directly in a terminal with the following arguments, updating the date after --end_date to today's date.

    poetry run hydrocron_load --table_name hydrocron-swot-node-table --start_date 2022-12-01T00:00:00 --end_date 2023-10-25T23:59:59 --obscure_data True

*Note: the --obscure_data parameter will multiply data values by a randomly generated integer during loading when True. This prevents real data from being made available publicly prior to the public release of the data, allowing for beta-testing. After the public release of the data, the obscured data will be wiped from the tables and --obscure_data will be set to False, allowing real data values to be available through Hydrocron.*

## Subsequent data loading

After the initial load, run the same commands as above to load new data, changing only the --start_date parameter to the date of the last load, and --end_date parameter to the present date. This will be done manually a limited number of times before integration with data ingest to the collection is ready.

## Reporting issues

If you encounter issues or error when loading data, please open an issue on the Hydrocron repository here: [https://github.com/podaac/hydrocron](https://github.com/podaac/hydrocron)
