"""
conftest file to set up local dynamodb connection
"""
import os.path
import boto3
import pytest

from pytest_dynamodb import factories

from hydrocron.db import HydrocronTable
from hydrocron.db.io import swot_reach_node_shp
from hydrocron.utils import constants

DB_TEST_TABLE_NAME = "hydrocron-swot-test-table"
API_TEST_TABLE_NAME = "hydrocron-swot-reach-table"

TEST_SHAPEFILE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data',
    'SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip'  # noqa
)

dynamo_test_proc = factories.dynamodb_proc(
    dynamodb_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              'dynamodb_local'), port=8000)

dynamo_db_resource = factories.dynamodb("dynamo_test_proc")


@pytest.fixture()
def hydrocron_dynamo_instance(request, dynamo_test_proc):
    """
    Set up a connection to a local dynamodb instance and
    create a table for testing
    """
    dynamo_db = boto3.resource(
        "dynamodb",
        endpoint_url=f"http://{dynamo_test_proc.host}:{dynamo_test_proc.port}",
        aws_access_key_id='fakeMyKeyId',
        aws_secret_access_key='fakeSecretAccessKey',
        region_name='us-west-2',
    )

    dynamo_db.create_table(
        TableName=API_TEST_TABLE_NAME,
        AttributeDefinitions=[
            {'AttributeName': 'reach_id', 'AttributeType': 'S'},
            {'AttributeName': 'range_start_time', 'AttributeType': 'S'}
            ],
        KeySchema=[
            {
                'AttributeName': 'reach_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'range_start_time',
                'KeyType': 'RANGE'
            }
            ],
        BillingMode='PROVISIONED',
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

    hydro_table = HydrocronTable(dynamo_db, API_TEST_TABLE_NAME)

    items = swot_reach_node_shp.read_shapefile(
            TEST_SHAPEFILE_PATH,
            obscure_data=False,
            columns=constants.REACH_DATA_COLUMNS)

    for item_attrs in items:
        # write to the table
        hydro_table.add_data(**item_attrs)

    request.cls.dynamo_db = dynamo_db
    yield dynamo_db
    for table in dynamo_db.tables.all():  # pylint:disable=no-member
        table.delete()

@pytest.fixture()
def hydrocron_dynamo_table(dynamo_db_resource):
    """
    Create table for testing
    """
    dynamo_db_resource.create_table(
        TableName=DB_TEST_TABLE_NAME,
        AttributeDefinitions=[
            {'AttributeName': 'reach_id', 'AttributeType': 'S'},
            {'AttributeName': 'range_start_time', 'AttributeType': 'S'}
            ],
        KeySchema=[
            {
                'AttributeName': 'reach_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'range_start_time',
                'KeyType': 'RANGE'
            }
            ],
        BillingMode='PROVISIONED',
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

    hydro_table = HydrocronTable(dynamo_db_resource, DB_TEST_TABLE_NAME)

    items = swot_reach_node_shp.read_shapefile(
            TEST_SHAPEFILE_PATH,
            obscure_data=False,
            columns=constants.REACH_DATA_COLUMNS)

    for item_attrs in items:
        # write to the table
        hydro_table.add_data(**item_attrs)

    return hydro_table
