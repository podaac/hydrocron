"""
==============
test_io_swot_reach_node_shp.py
==============
Test unpacking a swot reach or node shapefile.

Unit tests for unpacking swot reach and node shapefiles.
"""
from datetime import datetime, timedelta, timezone
import pytz
from hydrocron.utils import constants

from hydrocron.db.io import swot_shp


def test_parse_from_filename_reach():
    """
    Tests parsing cycle, pass, and time ranges from filename
    """
    filename_attrs = swot_shp.parse_from_filename(
        constants.TEST_REACH_FILENAME)

    assert filename_attrs['cycle_id'] == "548"
    assert filename_attrs['pass_id'] == "011"
    assert filename_attrs['continent_id'] == "NA"
    assert filename_attrs['range_start_time'] == "2023-06-10T19:33:37Z"
    assert filename_attrs['range_end_time'] == "2023-06-10T19:33:44Z"
    assert filename_attrs['crid'] == "PIA1"
    assert filename_attrs['collection_shortname'] == constants.SWOT_REACH_COLLECTION_NAME
    assert filename_attrs['collection_version'] == constants.SWOT_REACH_COLLECTION_VERSION
    assert filename_attrs['granuleUR'] == constants.TEST_REACH_FILENAME
    assert datetime.strptime(filename_attrs['ingest_time'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc) - datetime.now(timezone.utc) <= timedelta(minutes=5)


def test_parse_from_filename_lake():
    """
    Tests parsing cycle, pass, and time ranges from filename
    """
    filename_attrs = swot_shp.parse_from_filename(
        constants.TEST_PLAKE_FILENAME)

    assert filename_attrs['cycle_id'] == "018"
    assert filename_attrs['pass_id'] == "100"
    assert filename_attrs['continent_id'] == "GR"
    assert filename_attrs['range_start_time'] == "2024-07-13T11:17:41Z"
    assert filename_attrs['range_end_time'] == "2024-07-13T11:20:27Z"
    assert filename_attrs['crid'] == "PIC0"
    assert filename_attrs['collection_shortname'] == constants.SWOT_PRIOR_LAKE_COLLECTION_NAME
    assert filename_attrs['collection_version'] == constants.SWOT_PRIOR_LAKE_COLLECTION_VERSION
    assert filename_attrs['granuleUR'] == constants.TEST_PLAKE_FILENAME
    assert datetime.strptime(filename_attrs['ingest_time'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc) - datetime.now(timezone.utc) <= timedelta(minutes=5)


def test_read_reach_shapefile():
    """
    Tests reading attributes from the shapefile
    """
    items = swot_shp.read_shapefile(
        constants.TEST_REACH_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)

    assert len(items) == 687
    for key, val in constants.TEST_REACH_ITEM_DICT.items():
        assert val == items[2][key]


def test_read_lake_shapefile():
    """
    Tests reading attributes from the shapefile
    """
    items = swot_shp.read_shapefile(
        constants.TEST_PLAKE_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.PRIOR_LAKE_DATA_COLUMNS)

    assert len(items) == 5389
    for key, val in constants.TEST_PLAKE_ITEM_DICT.items():
        assert val == items[4596][key]


def test_read_shapefile_obscured():
    """
    Tests reading attributes from the shapefile with real values obscured
    """
    items = swot_shp.read_shapefile(
        constants.TEST_REACH_SHAPEFILE_PATH,
        obscure_data=True,
        columns=constants.REACH_DATA_COLUMNS)

    assert len(items) == 687
    for key, val in constants.TEST_REACH_ITEM_DICT.items():
        if key == constants.FIELDNAME_WSE:
            assert val != items[2][key]
