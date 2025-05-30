import pytest

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

from hydrocron.db.io import swot_shp


def test_table_exists(hydrocron_dynamo_table):
    """
    Test that a table exists in the database
    """
    assert hydrocron_dynamo_table.exists(constants.DB_TEST_TABLE_NAME)


def test_add_data_reaches(hydrocron_dynamo_table):
    """
    Test adding data from one Reach shapefile to db
    """
    items = swot_shp.read_shapefile(
        constants.TEST_REACH_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)

    for item_attrs in items:
        hydrocron_dynamo_table.add_data(**item_attrs)

    assert hydrocron_dynamo_table.table.item_count == 687


def test_query(hydrocron_dynamo_table):
    """
    Test a query for a reach id
    """
    items = swot_shp.read_shapefile(
        constants.TEST_REACH_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)

    for item_attrs in items:
        hydrocron_dynamo_table.add_data(**item_attrs)

    items = hydrocron_dynamo_table.run_query(
        partition_key=constants.TEST_REACH_ID_VALUE)

    assert items[0][constants.FIELDNAME_WSE] == constants.TEST_REACH_WSE_VALUE
    assert items[0][constants.FIELDNAME_SWORD_VERSION] == constants.TEST_REACH_SWORD_VERSION_VALUE
    assert items[0][constants.TEST_REACH_UNITS_FIELD] == constants.TEST_REACH_UNITS


def test_delete_item(hydrocron_dynamo_table):
    """
    Test delete an item
    """
    items = swot_shp.read_shapefile(
        constants.TEST_REACH_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)

    for item_attrs in items:
        hydrocron_dynamo_table.add_data(**item_attrs)

    hydrocron_dynamo_table.delete_item(
        partition_key=constants.TEST_REACH_ID_VALUE,
        sort_key=constants.TEST_REACH_TIME_VALUE)
    assert hydrocron_dynamo_table.table.item_count == 686


def test_track_table_mismatch():
    """
    Test track ingest table name mismatch with granule UR.
    """
    import hydrocron.db.load_data
    
    event = {
        "body": {
            "granule_path": "s3://podaac-swot-sit-cumulus-protected/SWOT_L2_HR_LakeSP_2.0/SWOT_L2_HR_LakeSP_Obs_020_150_EU_20240825T234434_20240825T235245_PIC0_01.zip",
            "table_name": "hydrocron-swot-prior-lake-table",
            "load_benchmarking_data": "False",
            "track_table": "hydrocron-swot-prior-lake-track-ingest-table"
        }
    }
    with pytest.raises(hydrocron.db.load_data.MissingTable) as e:
        hydrocron.db.load_data.granule_handler(event, None)
        assert str(e.value) == "Error: Cannot load Observed or Unassigned Lake data"
