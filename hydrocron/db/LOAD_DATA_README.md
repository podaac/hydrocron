# How To: Load the Hydrocron Database with data from CMR

## Overview

The main data loading function is hydrocron_db/load_data.py.  This runs as a lambda functrion which queries CMR for the data granules from the collection to load into the database.

## Earthdata Login

The current version uses both the earthaccess python library to handle EDL for the initial CMR query, and the S3FS package fo attempt to open the data files in cloud. Configure the EDL credentials to use in the parameters when invoking the lambda function.

## Invoke the lambda in the AWS Console for initial data loading

Version 1 of Hydrocron uses two database tables, one for SWOT river reaches and one for SWOT river nodes.

To load river reaches into the database, find the svc-hydrocron-(env)-load_data-lambda lambda function in the AWS Console.

Under Test, enter the following event JSON, entering your EDL credentials and access key/tokens generated from the [PODAAC S3 credentials endpoint](https://archive.podaac.earthdata.nasa.gov/s3credentials)

    {
        "body": {
        "table_name": "hydrocron-swot-reach-table",
        "start_date": "2023-10-24T00:00:00",
        "end_date": "2023-10-25T23:59:59",
        "obscure_data": "True",
        "edl_username": "",
        "edl_password": "",
        "accessKeyId": "",
        "secretAccessKey": "",
        "sessionToken": ""
        }
    }

To load river nodes into the database, run the same event JSON but replace
    "table_name": "hydrocron-swot-reach-table",
with "table_name": "hydrocron-swot-node-table",

*Note: the --obscure_data parameter will multiply data values by a randomly generated integer during loading when True. This prevents real data from being made available publicly prior to the public release of the data, allowing for beta-testing. After the public release of the data, the obscured data will be wiped from the tables and --obscure_data will be set to False, allowing real data values to be available through Hydrocron.*

## Subsequent data loading

After the initial load, run the same commands as above to load new data, changing only the --start_date parameter to the date of the last load, and --end_date parameter to the present date. This will be done manually a limited number of times before integration with data ingest to the collection is ready.

If parameters are unchanged, previously loaded data will be replaced with the values from the granules in CMR.

## Reporting issues

If you encounter issues or error when loading data, please open an issue on the Hydrocron repository here: [https://github.com/podaac/hydrocron](https://github.com/podaac/hydrocron)
