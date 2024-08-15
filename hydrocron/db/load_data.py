"""
This module searches for new granules and loads data into
the appropriate DynamoDB table
"""
import logging
import os
import json

import boto3
import earthaccess
from botocore.exceptions import ClientError

from hydrocron.db import HydrocronTable
from hydrocron.db.io import swot_shp
from hydrocron.utils import connection
from hydrocron.utils import constants

logging.getLogger().setLevel(logging.INFO)


class MissingTable(Exception):
    """
    Exception thrown if expected table is missing
    """


class TableMisMatch(Exception):
    """
    Exception thrown if table does not match feature type
    """


def lambda_handler(event, _):  # noqa: E501 # pylint: disable=W0613
    """
    Lambda entrypoint for loading the database
    """

    logging.info("Starting lambda handler")

    table_name = event['body']['table_name']
    start_date = event['body']['start_date']
    end_date = event['body']['end_date']
    load_benchmarking_data = event['body']['load_benchmarking_data']

    match table_name:
        case constants.SWOT_REACH_TABLE_NAME:
            collection_shortname = constants.SWOT_REACH_COLLECTION_NAME
            feature_type = 'Reach'
        case constants.SWOT_NODE_TABLE_NAME:
            collection_shortname = constants.SWOT_NODE_COLLECTION_NAME
            feature_type = 'Node'
        case constants.SWOT_PRIOR_LAKE_TABLE_NAME:
            collection_shortname = constants.SWOT_PRIOR_LAKE_COLLECTION_NAME
            feature_type = 'LakeSP_prior'
        case constants.DB_TEST_TABLE_NAME:
            collection_shortname = constants.SWOT_REACH_COLLECTION_NAME
            feature_type = 'Reach'
        case _:
            raise MissingTable(f"Hydrocron table '{table_name}' does not exist.")

    logging.info("Searching for granules in collection %s", collection_shortname)

    new_granules = find_new_granules(
        collection_shortname,
        start_date,
        end_date)

    lambda_client = boto3.client('lambda')

    for granule in new_granules:
        granule_path = granule.data_links(access='direct')[0]
        logging.info('Granule: %s', granule_path)
        try:
            checksum = granule['umm']['Checksum']['Value']
        except KeyError:
            checksum = "Not Found"
            logging.info('No UMM checksum')

        try:
            revision_date = [date["Date"] for date in granule["umm"]["ProviderDates"] if "Update" in date["Type"]]
        except KeyError:
            revision_date = "Not Found"
            logging.info('No UMM revision date')

        if feature_type in granule_path:
            event2 = ('{"body": {"granule_path": "' + granule_path
                      + '","table_name": "' + table_name
                      + '","checksum": "' + checksum
                      + '","revisionDate": "' + revision_date
                      + '","load_benchmarking_data": "' + load_benchmarking_data + '"}}')

            logging.info("Invoking granule load lambda with event json %s", str(event2))

            lambda_client.invoke(
                FunctionName=os.environ['GRANULE_LAMBDA_FUNCTION_NAME'],
                InvocationType='Event',
                Payload=event2)


def granule_handler(event, _):
    """
    Second Lambda entrypoint for loading individual granules
    """
    granule_path = event['body']['granule_path']
    table_name = event['body']['table_name']

    load_benchmarking_data = event['body']['load_benchmarking_data']

    try:
        checksum = event['body']['checksum']
    except KeyError:
        checksum = "Not Found"
        logging.info('No CNM checksum')

    try:
        revision_date = event['body']['revisionDate']
    except KeyError:
        revision_date = "Not Found"
        logging.info('No CNM revision date')

    if ("Reach" in granule_path) & (table_name != constants.SWOT_REACH_TABLE_NAME):
        raise TableMisMatch(f"Error: Cannot load Reach data into table: '{table_name}'")

    if ("Node" in granule_path) & (table_name != constants.SWOT_NODE_TABLE_NAME):
        raise TableMisMatch(f"Error: Cannot load Node data into table: '{table_name}'")

    if ("LakeSP_Prior" in granule_path) & (table_name != constants.SWOT_PRIOR_LAKE_TABLE_NAME):
        raise TableMisMatch(f"Error: Cannot load Prior Lake data into table: '{table_name}'")

    logging.info("Value of load_benchmarking_data is: %s", load_benchmarking_data)

    obscure_data = "true" in os.getenv("OBSCURE_DATA").lower()
    logging.info("Value of obscure_data is: %s", obscure_data)

    if load_benchmarking_data == "True":
        logging.info("Loading benchmarking data")
        items = swot_shp.load_benchmarking_data()
    else:
        logging.info("Setting up S3 connection")
        s3_resource = connection.s3_resource

        logging.info("Starting read granule")
        items = read_data(granule_path, obscure_data, s3_resource)

    logging.info("Set up dynamo connection")
    dynamo_resource = connection.dynamodb_resource

    logging.info("Adding granule to track ingest table")
    track_ingest_record = [{
        "granuleUR": os.path.basename(granule_path),
        "revision_date": revision_date,
        "expected_feature_count": len(items),
        "actual_feature_count": 0,
        "checksum": checksum,
        "status": "to_ingest"
        }]
    load_data(dynamo_resource, table_name=constants.TRACK_INGEST_TABLE_NAME, items=track_ingest_record)

    logging.info("Begin loading data from granule: %s", os.path.basename(granule_path))
    load_data(dynamo_resource, table_name, items)


def cnm_handler(event, _):
    """
    Unpacks CNM-R message and invokes granule_load lambda
    """
    load_benchmarking_data = "False"

    lambda_client = boto3.client('lambda')

    # Parse message
    for message in event['Records']:
        cnm = json.loads(message['Sns']['Message'])
        revision_date = cnm['submissionTime']

        logging.info("Begin processing message %s", str(cnm))

        for files in cnm['product']['files']:
            if files['type'] == 'data':
                granule_uri = files['uri']
                checksum = files['checksum']

                if 'Reach' in granule_uri:
                    event2 = ('{"body": {"granule_path": "' + granule_uri
                              + '","table_name": "' + constants.SWOT_REACH_TABLE_NAME
                              + '","checksum": "' + checksum
                              + '","revisionDate": "' + revision_date
                              + '","load_benchmarking_data": "' + load_benchmarking_data + '"}}')

                    logging.info("Invoking granule load lambda with event json %s", str(event2))

                    lambda_client.invoke(
                        FunctionName=os.environ['GRANULE_LAMBDA_FUNCTION_NAME'],
                        InvocationType='Event',
                        Payload=event2)

                if 'Node' in granule_uri:
                    event2 = ('{"body": {"granule_path": "' + granule_uri
                              + '","table_name": "' + constants.SWOT_NODE_TABLE_NAME
                              + '","checksum": "' + checksum
                              + '","revisionDate": "' + revision_date
                              + '","load_benchmarking_data": "' + load_benchmarking_data + '"}}')

                    logging.info("Invoking granule load lambda with event json %s", str(event2))

                    lambda_client.invoke(
                        FunctionName=os.environ['GRANULE_LAMBDA_FUNCTION_NAME'],
                        InvocationType='Event',
                        Payload=event2)

                if 'LakeSP_Prior' in granule_uri:
                    event2 = ('{"body": {"granule_path": "' + granule_uri
                              + '","table_name": "' + constants.SWOT_PRIOR_LAKE_TABLE_NAME
                              + '","checksum": "' + checksum
                              + '","revisionDate": "' + revision_date
                              + '","load_benchmarking_data": "' + load_benchmarking_data + '"}}')

                    logging.info("Invoking granule load lambda with event json %s", str(event2))

                    lambda_client.invoke(
                        FunctionName=os.environ['GRANULE_LAMBDA_FUNCTION_NAME'],
                        InvocationType='Event',
                        Payload=event2)


def find_new_granules(collection_shortname, start_date, end_date):
    """
    Find granules to ingest

    Parameters
    ----------
    collection_shortname : string
        The shortname of the collection to search
    start_date
    end_date

    Returns
    -------
    results : list of Granule objects
        List of S3 paths to the granules that have not yet been ingested
    """
    auth = earthaccess.login(persist=True)

    logging.info("Searching for granules in collection %s", collection_shortname)

    cmr_search = earthaccess.DataGranules(auth).short_name(collection_shortname).temporal(start_date, end_date)

    results = cmr_search.get()

    logging.info("Found %s granules", str(len(results)))

    return results


def read_data(granule_path, obscure_data, s3_resource=None):
    """
    Read data from shapefiles

    Parameters
    ----------
    granule_path : string
        the S3 url to the granule to unpack
    obscure_data : boolean
        whether to obscure the data on load
    s3_resource : boto3 session resource

    Returns
    -------
    items : the unpacked granule data
    """
    items = {}

    if 'Reach' in granule_path:
        logging.info("Start reading reach shapefile")
        items = swot_shp.read_shapefile(
            granule_path,
            obscure_data,
            constants.REACH_DATA_COLUMNS,
            s3_resource=s3_resource)

    if 'Node' in granule_path:
        logging.info("Start reading node shapefile")
        items = swot_shp.read_shapefile(
            granule_path,
            obscure_data,
            constants.NODE_DATA_COLUMNS,
            s3_resource=s3_resource)

    if 'LakeSP_Prior' in granule_path:
        logging.info("Start reading prior lake shapefile")
        items = swot_shp.read_shapefile(
            granule_path,
            obscure_data,
            constants.PRIOR_LAKE_DATA_COLUMNS,
            s3_resource=s3_resource)

    return items


def load_data(dynamo_resource, table_name, items):
    """
    Load data into dynamo DB

    Parameters
    ----------
    dynamo_resource : Resource
        Dynamo resource
    table_name : String
        The name of the table
    items : Dictionary
        The unpacked granule to load
    """

    try:
        logging.info("Set up dynamo table connection")
        hydrocron_table = HydrocronTable(dyn_resource=dynamo_resource, table_name=table_name)
    except ClientError as err:
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            raise MissingTable(f"Hydrocron table '{table_name}' does not exist.") from err
        raise err

    match hydrocron_table.table_name:
        case constants.SWOT_REACH_TABLE_NAME:
            feature_name = 'reach'
            feature_id = feature_name + '_id'
        case constants.SWOT_NODE_TABLE_NAME:
            feature_name = 'node'
            feature_id = feature_name + '_id'
        case constants.SWOT_PRIOR_LAKE_TABLE_NAME:
            feature_name = 'prior_lake'
            feature_id = 'lake_id'
        case constants.TRACK_INGEST_TABLE_NAME:
            feature_name = 'track ingest'
            feature_id = 'granuleUR'
        case _:
            logging.warning('Items cannot be parsed, file reader not implemented for table %s', hydrocron_table.table_name)

    if len(items) > 5:
        logging.info("Batch adding %s %s items. First 5 feature ids in batch: ", len(items), feature_name)
        for i in range(5):
            logging.info("Item %s: %s", feature_id, items[i][feature_id])
        hydrocron_table.batch_fill_table(items)

    else:
        logging.info("Adding %s items to table individually", feature_name)
        for item_attrs in items:
            logging.info("Item %s: %s", feature_id, item_attrs[feature_id])
            hydrocron_table.add_data(**item_attrs)
