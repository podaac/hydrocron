"""
conftest file to set up local dynamodb connection
"""
import os.path

import boto3
import pytest
from pytest_dynamodb import factories

dynamo_test_proc = factories.dynamodb_proc(
    dynamodb_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dynamodb_local'),
    port=8000)


@pytest.fixture(scope="class")
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

    request.cls.dynamo_db = dynamo_db
    yield dynamo_db
    for table in dynamo_db.tables.all():  # pylint:disable=no-member
        table.delete()
