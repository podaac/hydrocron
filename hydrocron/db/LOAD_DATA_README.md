# How To: Load the Hydrocron Database with data from CMR

## Overview

The main data loading function is hydrocron_db/load_data.py.  This runs as a lambda functrion which queries CMR for the data granules from the collection to load into the database.

## Earthdata Login

The current version uses the earthaccess python library to handle EDL for the initial CMR query.

## Invoke the lambda in the AWS Console for initial data loading

Version 1 of Hydrocron uses two database tables, one for SWOT river reaches and one for SWOT river nodes.

To load river reaches into the database, find the svc-hydrocron-(env)-load_data-lambda lambda function in the AWS Console.
Under Test, enter the following event JSON:

    {
        "body": {
        "table_name": "hydrocron-swot-reach-table",
        "start_date": "2023-10-24T00:00:00",
        "end_date": "2023-10-25T23:59:59",
        "obscure_data": "True",
        "load_benchmarking_data": "False"
        }
    }

To load river nodes into the database, run the same event JSON but replace
    "table_name": "hydrocron-swot-reach-table",
with "table_name": "hydrocron-swot-node-table",

*Note: the --obscure_data parameter will multiply data values by a randomly generated integer during loading when True. This prevents real data from being made available publicly prior to the public release of the data, allowing for beta-testing. This parameter should be set to True when loading data in SIT and UAT. After the public release of the data, the obscured data will be wiped from the tables and --obscure_data will be set to False in OPS, allowing real data values to be available through Hydrocron.*

*Note: the  --load_benchmarking_data parameter should be set to False. Benchmarking data should be loaded using the Load Granule Lambda function, described below.*

## Subsequent data loading

After the initial load, run the same commands as above to load new data, changing only the --start_date parameter to the date of the last load, and --end_date parameter to the present date. This will be done manually a limited number of times before integration with data ingest to the collection is ready.

If parameters are unchanged, previously loaded data will be replaced with the values from the granules in CMR.

## Load a specific granule individually

To load a specific individual granule by name, find the svc-hydrocron-(env)-load_granule-lambda lambda function in the AWS Console.
Under Test, enter the following event JSON:

    {
        "body": {
        "granule_path": "s3://podaac-swot-ops-cumulus-protected/SWOT_L2_HR_RiverSP_1.0/SWOT_L2_HR_RiverSP_Reach_006_545_AU_20231122T000237_20231122T000238_PIB0_01.zip",
        "obscure_data": "True",
        "table_name": "hydrocron-swot-reach-table",
        "load_benchmarking_data": "False"
        }
    }

Update the value of the granule path parameter to load a different granule. If running in SIT or UAT, keep obscure_data set to True. If you not loading the performance data, keep the load_benchmarking_data parameter set to False. When this is True, the granule specified in the granule_path parameter will be ignored.

## Load the performance benchmarking test data in the database

To load the performance benchmarking data, find the svc-hydrocron-(env)-load-granule-lambda lambda function in the AWS Console.

Under Test, enter the following event JSON

    {
        "body": {
        "granule_path": "",
        "obscure_data": "True",
        "table_name": "hydrocron-swot-reach-table",
        "load_benchmarking_data": "True"
        }
    }

## Reporting issues

If you encounter issues or error when loading data, please open an issue on the Hydrocron repository here: [https://github.com/podaac/hydrocron](https://github.com/podaac/hydrocron)