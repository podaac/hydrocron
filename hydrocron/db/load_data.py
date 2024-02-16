"""
This module searches for new granules and loads data into
the appropriate DynamoDB table
"""
import logging
import os
import base64
import json
import requests

import boto3
import earthaccess
from botocore.exceptions import ClientError

from hydrocron.db import HydrocronTable
from hydrocron.db.io import swot_reach_node_shp
from hydrocron.utils import constants

logging.getLogger().setLevel(logging.INFO)


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

    new_granules = find_new_granules(
        collection_shortname,
        start_date,
        end_date)

    lambda_client = boto3.client('lambda')

    for granule in new_granules:
        granule_path = granule.data_links(access='direct')[0]

        event2 = ('{"body": {"granule_path": "'
                  + granule_path + '","obscure_data": "'
                  + obscure_data + '","table_name": "'
                  + table_name + '"}}')

        lambda_client.invoke(
            FunctionName=os.environ['GRANULE_LAMBDA_FUNCTION_NAME'],
            InvocationType='Event',
            Payload=event2)


def granule_handler(event, _):
    """
    Second Lambda entrypoint for loading individual granules
    """
    granule_path = event['body']['granule_path']
    obscure_data = event['body']['obscure_data']
    table_name = event['body']['table_name']
    load_test_reach = event['body']['load_test_reach']

    if load_test_reach:
        print("Loading benchmarking data")
        items = swot_reach_node_shp.load_test_reach()
    else:
        print("Setting up S3 connection")
        s3_resource = setup_s3connection()

        logging.info("Starting read granule")
        items = read_data(granule_path, obscure_data, s3_resource)

    print("Set up dynamo connection")
    dynamo_resource = setup_dynamoconnection()
    print("loading data items")
    load_data(dynamo_resource, table_name, items)


def retrieve_credentials():
    """Makes the Oauth calls to authenticate with EDS and return a set of s3
    same-region, read-only credntials.
    """
    login_resp = requests.get(
        constants.S3_CREDS_ENDPOINT,
        allow_redirects=False,
        timeout=5
    )
    login_resp.raise_for_status()

    auth = f"{os.environ['EARTHDATA_USERNAME']}:{os.environ['EARTHDATA_PASSWORD']}"
    encoded_auth = base64.b64encode(auth.encode('ascii'))

    auth_redirect = requests.post(
        login_resp.headers['location'],
        data={"credentials": encoded_auth},
        headers={"Origin": constants.S3_CREDS_ENDPOINT},
        allow_redirects=False,
        timeout=5
    )
    auth_redirect.raise_for_status()

    final = requests.get(
        auth_redirect.headers['location'],
        allow_redirects=False,
        timeout=5
    )

    results = requests.get(
        constants.S3_CREDS_ENDPOINT,
        cookies={'accessToken': final.cookies['accessToken']},
        timeout=5
    )
    results.raise_for_status()

    return json.loads(results.content)


def setup_s3connection():
    """
    Set up S3 resource connections

    Returns
    -------
    s3_resource : S3 resource
    """

    creds = retrieve_credentials()

    s3_session = boto3.session.Session(
        aws_access_key_id=creds['accessKeyId'],
        aws_secret_access_key=creds['secretAccessKey'],
        aws_session_token=creds['sessionToken'],
        region_name='us-west-2')

    s3_resource = s3_session.resource('s3')

    return s3_resource


def setup_dynamoconnection():
    """
    Set up DynamoDB resource connections

    Returns
    -------
    dynamo_resource : HydrocronDB

    """

    dyn_session = boto3.session.Session()

    if endpoint_url := os.getenv('HYDROCRON_dynamodb_endpoint_url'):
        dyndb_resource = dyn_session.resource('dynamodb', endpoint_url=endpoint_url)
    else:
        dyndb_resource = dyn_session.resource('dynamodb')

    return dyndb_resource


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

    cmr_search = earthaccess.DataGranules(auth).short_name(collection_shortname).temporal(start_date, end_date)

    results = cmr_search.get()

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
        items = swot_reach_node_shp.read_shapefile(
            granule_path,
            obscure_data,
            constants.REACH_DATA_COLUMNS,
            s3_resource=s3_resource)

    if 'Node' in granule_path:
        logging.info("Start reading node shapefile")
        items = swot_reach_node_shp.read_shapefile(
            granule_path,
            obscure_data,
            constants.NODE_DATA_COLUMNS,
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
        print("Set dynamo table connection")
        hydrocron_table = HydrocronTable(dyn_resource=dynamo_resource, table_name=table_name)
    except ClientError as err:
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            raise MissingTable(f"Hydrocron table '{table_name}' does not exist.") from err
        raise err

    if hydrocron_table.table_name == constants.SWOT_REACH_TABLE_NAME:
        print("Adding reach items to table")
        for item_attrs in items:
            hydrocron_table.add_data(**item_attrs)

    elif hydrocron_table.table_name == constants.SWOT_NODE_TABLE_NAME:
        print("Adding node items to table")
        for item_attrs in items:
            hydrocron_table.add_data(**item_attrs)

    else:
        logging.warning('Items cannot be parsed, file reader not implemented for table %s', hydrocron_table.table_name)
