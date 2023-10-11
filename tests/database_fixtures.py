"""
Database fixture to use to test with local dynamodb
"""
import pytest
from hydrocron_db.hydrocron_database import HydrocronTable

TABLE_NAME = "hydrocron_test_table"


@pytest.fixture()
def hydrocron_dynamo_table(dynamo_db_resource):
    """
    Create table for testing
    """
    dynamo_db_resource.create_table(
        TableName=TABLE_NAME,
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

    hydro_table = HydrocronTable(dynamo_db_resource, TABLE_NAME)

    return hydro_table
