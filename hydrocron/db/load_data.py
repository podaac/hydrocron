"""
This module searches for new granules and loads data into
the appropriate DynamoDB table
"""
import logging
import os
import requests

import boto3
import earthaccess
from botocore.exceptions import ClientError

from hydrocron.db import HydrocronTable
from hydrocron.db.io import swot_reach_node_shp
from hydrocron.utils import constants


class MissingTable(Exception):
    """
    Exception thrown if expected table is missing
    """


def lambda_handler(event, _):  # noqa: E501 # pylint: disable=W0613
    """
    Lambda entrypoint for loading the database
    """

    table_name = event['body']['table_name']
    start_date = event['body']['start_date']
    end_date = event['body']['end_date']
    obscure_data = event['body']['obscure_data']

    match table_name:
        case constants.SWOT_REACH_TABLE_NAME:
            collection_shortname = constants.SWOT_REACH_COLLECTION_NAME
        case constants.SWOT_NODE_TABLE_NAME:
            collection_shortname = constants.SWOT_NODE_COLLECTION_NAME
        case constants.DB_TEST_TABLE_NAME:
            collection_shortname = constants.SWOT_REACH_COLLECTION_NAME
        case _:
            raise MissingTable(f"Hydrocron table '{table_name}' does not exist.")

    dynamo_resource, s3_resource = setup_connection()

    try:
        table = HydrocronTable(dyn_resource=dynamo_resource, table_name=table_name)
    except ClientError as err:
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            raise MissingTable(f"Hydrocron table '{table_name}' does not exist.") from err
        raise err

    new_granules = find_new_granules(
        collection_shortname,
        start_date,
        end_date)

    for granule in new_granules:
        load_data(table, granule, obscure_data, s3_resource)

def get_temp_creds():
    """
    Get temporary AWS credentials
    """
    s3_cred_endpoint = 'https://archive.podaac.earthdata.nasa.gov/s3credentials'
    temp_creds_url = s3_cred_endpoint
    return requests.get(temp_creds_url).json()


def setup_connection():
    """
    Set up DynamoDB and S3 resource connections

    Returns
    -------
    dynamo_resource : HydrocronDB
    s3_resource : S3 resource
    """

    creds = get_temp_creds()

    session = boto3.session.Session(
        aws_access_key_id=creds['accessKeyId'],
        aws_secret_access_key=creds['secretAccessKey'],
        aws_session_token=creds['sessionToken'],
        region_name='us-west-2')

    if endpoint_url := os.getenv('HYDROCRON_dynamodb_endpoint_url'):
        dyndb_resource = session.resource('dynamodb', endpoint_url=endpoint_url)
        s3_resource = None
    else:
        dyndb_resource = session.resource('dynamodb')
        s3_resource = session.resource('s3')

    return dyndb_resource, s3_resource


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
    auth = earthaccess.login()

    cmr_search = earthaccess.DataGranules(auth).short_name(collection_shortname).temporal(start_date, end_date)

    results = cmr_search.get()

    return results


def load_data(hydrocron_table, granule, obscure_data, s3_resource=None):
    """
    Create table and load data

    hydrocron_table : HydrocronTable
        The table to load data into
    granules : Granule object
        The list of S3 paths of granules to load data from
    obscure_data : boolean
        If true, scramble the data values during load to prevent
        release of real data. Used during beta testing.
    """
    granule_path = granule.data_links(access='direct')[0]

    if hydrocron_table.table_name == constants.SWOT_REACH_TABLE_NAME:
        if 'Reach' in granule_path:
            items = swot_reach_node_shp.read_shapefile(
                granule_path,
                obscure_data,
                constants.REACH_DATA_COLUMNS,
                s3_resource=s3_resource)

            for item_attrs in items:
                # write to the table
                hydrocron_table.add_data(**item_attrs)

    elif hydrocron_table.table_name == constants.SWOT_NODE_TABLE_NAME:
        if 'Node' in granule_path:
            items = swot_reach_node_shp.read_shapefile(
                granule_path,
                obscure_data,
                constants.NODE_DATA_COLUMNS,
                s3_resource=s3_resource)

            for item_attrs in items:
                # write to the table
                hydrocron_table.add_data(**item_attrs)

    else:
        logging.warning('Items cannot be parsed, file reader not implemented for table %s', hydrocron_table.table_name)
