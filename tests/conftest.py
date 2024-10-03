"""
conftest file to set up local dynamodb connection
"""
import datetime
import os.path

import boto3
import moto
import pytest
from pytest_dynamodb import factories

from hydrocron.db import HydrocronTable
from hydrocron.db.io import swot_shp
from hydrocron.utils import constants

DB_TEST_TABLE_NAME = "hydrocron-swot-test-table"

TEST_SHAPEFILE_PATH_REACH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data',
    'SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip'  # noqa
)

TEST_SHAPEFILE_PATH_REACH_TRACK = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data',
    "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"
)

TEST_SHAPEFILE_PATH_LAKE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data',
    'SWOT_L2_HR_LakeSP_Prior_018_100_GR_20240713T111741_20240713T112027_PIC0_01.zip'  # noqa
)

dynamo_test_proc = factories.dynamodb_proc(
    dynamodb_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              'dynamodb_local'), port=8000)

dynamo_db_resource = factories.dynamodb("dynamo_test_proc")

def create_tables(dynamo_db, table_name, feature_id, non_key_atts):
    """Create DynamoDB tables for testing."""
    
    dynamo_db.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {'AttributeName': feature_id, 'AttributeType': 'S'},
            {'AttributeName': 'range_start_time', 'AttributeType': 'S'},
            {'AttributeName': 'granuleUR', 'AttributeType': 'S'}
        ],
        KeySchema=[
            {
                'AttributeName': feature_id,
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
        },
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GranuleURIndex",
                "KeySchema": [
                    {
                        "AttributeName": "granuleUR",
                        "KeyType": "HASH"
                    },
                    {
                        "AttributeName": "range_start_time",
                        "KeyType": "RANGE"
                    }
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": non_key_atts
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                }
            }
        ]
    )


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
    
    create_tables(
        dynamo_db, 
        constants.SWOT_REACH_TABLE_NAME, 
        'reach_id', 
        ['reach_id', 'collection_shortname', 'collection_version', 'crid', 'cycle_id', 'pass_id', 'continent_id', 'ingest_time']
    )
    
    create_tables(
        dynamo_db, 
        constants.SWOT_PRIOR_LAKE_TABLE_NAME, 
        'lake_id', 
        ['lake_id', 'collection_shortname', 'collection_version', 'crid', 'cycle_id', 'pass_id', 'continent_id', 'ingest_time']
    )
    
    # load reach table
    reach_hydro_table = HydrocronTable(dynamo_db, constants.SWOT_REACH_TABLE_NAME)
    reach_items = swot_shp.read_shapefile(
        TEST_SHAPEFILE_PATH_REACH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)
    for item_attrs in reach_items:
        reach_hydro_table.add_data(**item_attrs)
    
    # load lake table
    lake_hydro_table = HydrocronTable(dynamo_db, constants.SWOT_PRIOR_LAKE_TABLE_NAME)
    lake_items = swot_shp.read_shapefile(
        TEST_SHAPEFILE_PATH_LAKE,
        obscure_data=False,
        columns=constants.PRIOR_LAKE_DATA_COLUMNS)
    for item_attrs in lake_items:
        lake_hydro_table.add_data(**item_attrs)

    try:
        request.cls.dynamo_db = dynamo_db
    except AttributeError:
        pass

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

    items = swot_shp.read_shapefile(
        TEST_SHAPEFILE_PATH_REACH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)

    for item_attrs in items:
        hydro_table.add_data(**item_attrs)

    return hydro_table


@pytest.fixture()
def mock_s3():
   
    mock_aws = moto.mock_aws()
    mock_aws.start()
   
    s3 = boto3.resource("s3")
    s3.Bucket("podaac-swot-ops-cumulus-protected").create(CreateBucketConfiguration={"LocationConstraint": "us-west-2"})
    key = f"SWOT_L2_HR_RiverSP_2.0/{os.path.basename(TEST_SHAPEFILE_PATH_REACH_TRACK)}"
    s3.Bucket("podaac-swot-ops-cumulus-protected").upload_file(Filename=TEST_SHAPEFILE_PATH_REACH_TRACK, Key=key)

    yield s3

    mock_aws.stop()


@pytest.fixture()
def mock_ssm():
   
    mock_aws = moto.mock_aws()
    mock_aws.start()
   
    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
   
    ssm = boto3.client("ssm")
    runtime = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    ssm.put_parameter(Name="/service/hydrocron/track-ingest-runtime/SWOT_L2_HR_RiverSP_reach_2.0", Value=runtime, Type="String")
   
    yield mock_aws

    mock_aws.stop()

@pytest.fixture()
def hydrocron_api(hydrocron_dynamo_instance, dynamo_test_proc, mock_ssm):
    os.environ['HYDROCRON_ENV'] = 'test'
    os.environ['HYDROCRON_dynamodb_endpoint_url'] = f"http://{dynamo_test_proc.host}:{dynamo_test_proc.port}"    
    import hydrocron.utils.connection    # noqa: E501 # pylint: disable=import-outside-toplevel
    hydrocron.utils.connection._dynamodb_resource = hydrocron_dynamo_instance


@pytest.fixture()
def s3_connection():
    import hydrocron.utils.connection  # noqa: E501 # pylint: disable=import-outside-toplevel
    hydrocron.utils.connection.retrieve_credentials = lambda: {
        "accessKeyId": "testkey",
        "secretAccessKey": "testsecret",
        "sessionToken": "testtoken"
    }


@pytest.fixture()
def track_ingest_dynamo_instance(request, dynamo_test_proc):
    dynamo_db = boto3.resource(
        "dynamodb",
        endpoint_url=f"http://{dynamo_test_proc.host}:{dynamo_test_proc.port}",
        aws_access_key_id='fakeMyKeyId',
        aws_secret_access_key='fakeSecretAccessKey',
        region_name='us-west-2',
    )
    
    # reach table
    create_tables(
        dynamo_db, 
        constants.SWOT_REACH_TABLE_NAME, 
        'reach_id', 
        ['reach_id', 'collection_shortname', 'collection_version', 'crid', 'cycle_id', 'pass_id', 'continent_id', 'ingest_time']
    )
    reach_hydro_table = HydrocronTable(dynamo_db, constants.SWOT_REACH_TABLE_NAME)
    reach_items = swot_shp.read_shapefile(
        TEST_SHAPEFILE_PATH_REACH_TRACK,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)
    for item_attrs in reach_items:
        reach_hydro_table.add_data(**item_attrs)
    
    # track table
    dynamo_db.create_table(
        TableName=constants.SWOT_REACH_TRACK_INGEST_TABLE_NAME,
        AttributeDefinitions=[
            {'AttributeName': 'granuleUR', 'AttributeType': 'S'},
            {'AttributeName': 'revision_date', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'}
        ],
        KeySchema=[
            {
                'AttributeName': 'granuleUR',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'revision_date',
                'KeyType': 'RANGE'
            }
        ],
        BillingMode='PROVISIONED',
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        },
        GlobalSecondaryIndexes=[
            {
                "IndexName": "statusIndex",
                "KeySchema": [
                    {
                        "AttributeName": "status",
                        "KeyType": "HASH"
                    }
                ],
                "Projection": {
                    "ProjectionType": "ALL",
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                }
            }
        ]
    )
    track_reach_table = HydrocronTable(dynamo_db, constants.SWOT_REACH_TRACK_INGEST_TABLE_NAME)
    track_items = swot_shp.read_shapefile(
        TEST_SHAPEFILE_PATH_REACH_TRACK,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)
    track_ingest_record = [{
        "granuleUR": os.path.basename(TEST_SHAPEFILE_PATH_REACH_TRACK),
        "revision_date": "2024-05-22T19:15:44.572Z",
        "expected_feature_count": len(track_items),
        "actual_feature_count": 0,
        "checksum": "0823db619be0044e809a5f992e067d03",
        "status": "to_ingest"
        }]
    track_reach_table.batch_fill_table(track_ingest_record)
    
    try:
        request.cls.dynamo_db = dynamo_db
    except AttributeError:
        pass

    yield dynamo_db
    for table in dynamo_db.tables.all():  # pylint:disable=no-member
        table.delete()
        
@pytest.fixture()
def track_ingest_fixture(track_ingest_dynamo_instance, dynamo_test_proc, mock_ssm, mock_s3):
    os.environ['HYDROCRON_ENV'] = 'test'
    os.environ['HYDROCRON_dynamodb_endpoint_url'] = f"http://{dynamo_test_proc.host}:{dynamo_test_proc.port}"    
    import hydrocron.utils.connection    # noqa: E501 # pylint: disable=import-outside-toplevel
    hydrocron.utils.connection._dynamodb_resource = track_ingest_dynamo_instance
    hydrocron.utils.connection._s3_resource = mock_s3