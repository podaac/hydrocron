"""
==============
test_create_table.py
==============
Test creating a Hydrocron dynamodb table.

Unit tests for creating tables and adding items to the Hydrocron Database.
Requires a local install of DynamoDB to be running.
See https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html # noqa

"""
from hydrocron.utils import constants

from hydrocron.db.io import swot_reach_node_shp


def test_table_exists(hydrocron_dynamo_table):
    """
    Test that a table exists in the database
    """
    assert hydrocron_dynamo_table.exists(constants.DB_TEST_TABLE_NAME)


def test_add_data(hydrocron_dynamo_table):
    """
    Test adding data from one Reach shapefile to db
    """
    items = swot_reach_node_shp.read_shapefile(
        constants.TEST_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)

    for item_attrs in items:
        hydrocron_dynamo_table.add_data(**item_attrs)

    assert hydrocron_dynamo_table.table.item_count == 687


def test_query(hydrocron_dynamo_table):
    """
    Test a query for a reach id
    """
    items = swot_reach_node_shp.read_shapefile(
        constants.TEST_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)

    for item_attrs in items:
        hydrocron_dynamo_table.add_data(**item_attrs)

    items = hydrocron_dynamo_table.run_query(
        partition_key=constants.TEST_REACH_ID_VALUE)
    assert items[0][constants.FIELDNAME_WSE] == constants.TEST_WSE_VALUE


def test_delete_item(hydrocron_dynamo_table):
    """
    Test delete an item
    """
    items = swot_reach_node_shp.read_shapefile(
        constants.TEST_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)

    for item_attrs in items:
        hydrocron_dynamo_table.add_data(**item_attrs)

    hydrocron_dynamo_table.delete_item(
        partition_key=constants.TEST_REACH_ID_VALUE,
        sort_key=constants.TEST_TIME_VALUE)
    assert hydrocron_dynamo_table.table.item_count == 686
