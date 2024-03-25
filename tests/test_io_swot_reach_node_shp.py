"""
==============
test_io_swot_reach_node_shp.py
==============
Test unpacking a swot reach or node shapefile.

Unit tests for unpacking swot reach and node shapefiles.
"""
from hydrocron.utils import constants

from hydrocron.db.io import swot_reach_node_shp


def test_parse_from_filename():
    """
    Tests parsing cycle, pass, and time ranges from filename
    """
    filename_attrs = swot_reach_node_shp.parse_from_filename(
        constants.TEST_FILENAME)

    assert filename_attrs['cycle_id'] == "548"
    assert filename_attrs['pass_id'] == "011"
    assert filename_attrs['continent_id'] == "NA"
    assert filename_attrs['range_start_time'] == "2023-06-10T19:33:37Z"
    assert filename_attrs['range_end_time'] == "2023-06-10T19:33:44Z"
    assert filename_attrs['crid'] == "PIA1"
    assert filename_attrs['collection_shortname'] == constants.SWOT_REACH_COLLECTION_NAME


def test_read_shapefile():
    """
    Tests reading attributes from the shapefile
    """
    items = swot_reach_node_shp.read_shapefile(
        constants.TEST_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS)

    assert len(items) == 687
    for key, val in constants.TEST_ITEM_DICT.items():
        assert val == items[2][key]


def test_read_shapefile_obscured():
    """
    Tests reading attributes from the shapefile with real values obscured
    """
    items = swot_reach_node_shp.read_shapefile(
        constants.TEST_SHAPEFILE_PATH,
        obscure_data=True,
        columns=constants.REACH_DATA_COLUMNS)

    assert len(items) == 687
    for key, val in constants.TEST_ITEM_DICT.items():
        if key == constants.FIELDNAME_WSE:
            assert val != items[2][key]
