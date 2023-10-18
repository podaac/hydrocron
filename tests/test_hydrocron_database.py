"""
==============
test_create_table.py
==============
Test creating a Hydrocron dynamodb table.

Unit tests for creating tables and adding items to the Hydrocron Database.
Requires a local install of DynamoDB to be running.
See https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html # noqa

"""
import os.path

from hydrocron_db.io import swot_reach_node_shp, swot_constants


TEST_SHAPEFILE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data',
    'SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip'  # noqa
)

TEST_TABLE_NAME = 'hydrocron-swot-test-table'
TEST_PARTITION_KEY_NAME = 'reach_id'
TEST_SORT_KEY_NAME = 'range_start_time'
COLUMNS = swot_constants.reach_columns


def test_table_exists(hydrocron_dynamo_table):
    '''
    Test that a table exists in the database
    '''
    assert hydrocron_dynamo_table.exists(TEST_TABLE_NAME)


def test_add_data(hydrocron_dynamo_table):
    '''
    Test adding data from one Reach shapefile to db
    '''
    items = swot_reach_node_shp.read_shapefile(TEST_SHAPEFILE_PATH,
                                               obscure_data=False,
                                               columns=COLUMNS)

    for item_attrs in items:
        # write to the table
        hydrocron_dynamo_table.add_data(**item_attrs)

    assert hydrocron_dynamo_table.table.item_count == 687


def test_query(hydrocron_dynamo_table):
    '''
    Test a query for a reach id
    '''
    items = swot_reach_node_shp.read_shapefile(TEST_SHAPEFILE_PATH,
                                               obscure_data=False,
                                               columns=COLUMNS)
    for item_attrs in items:
        # write to the table
        hydrocron_dynamo_table.add_data(**item_attrs)

    items = hydrocron_dynamo_table.run_query(partition_key='71224100223')
    assert items[0]['wse'] == str(286.2983)


def test_delete_item(hydrocron_dynamo_table):
    '''
    Test delete an item
    '''
    items = swot_reach_node_shp.read_shapefile(TEST_SHAPEFILE_PATH,
                                               obscure_data=False,
                                               columns=COLUMNS)
    for item_attrs in items:
        # write to the table
        hydrocron_dynamo_table.add_data(**item_attrs)

    hydrocron_dynamo_table.delete_item(
        partition_key='71224100203', sort_key='2023-06-10T19:33:37Z')
    assert hydrocron_dynamo_table.table.item_count == 686
