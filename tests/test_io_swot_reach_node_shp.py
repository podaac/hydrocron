"""
==============
test_io_swot_reach_node_shp.py
==============
Test unpacking a swot reach or node shapefile.

Unit tests for unpacking swot reach and node shapefiles.
"""
import os.path

from hydrocron_db.io import swot_reach_node_shp, swot_constants

TEST_SHAPEFILE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data',
    'SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip'  # noqa E501
)

TEST_FILENAME = (
    "SWOT_L2_HR_RiverSP_Reach_548_011_NA_"
    "20230610T193337_20230610T193344_PIA1_01.zip")

TEST_ITEM_DICT = {
    "reach_id": "71224100223",
    "time": "739741183.129",
    "time_str": "2023-06-10T19:39:43Z",
    "wse": "286.2983",
    "cycle_id": "548"
}


def test_parse_from_filename():
    '''
    Tests parsing cycle, pass, and time ranges from filename
    '''
    filename_attrs = swot_reach_node_shp.parse_from_filename(TEST_FILENAME)

    assert filename_attrs['cycle_id'] == "548"
    assert filename_attrs['pass_id'] == "011"
    assert filename_attrs['continent_id'] == "NA"
    assert filename_attrs['range_start_time'] == "2023-06-10T19:33:37Z"
    assert filename_attrs['range_end_time'] == "2023-06-10T19:33:44Z"
    assert filename_attrs['crid'] == "PIA1"


def test_read_shapefile():
    '''
    Tests reading attributes from the shapefile
    '''
    items = swot_reach_node_shp.read_shapefile(
        TEST_SHAPEFILE_PATH,
        obscure_data=False,
        columns=swot_constants.reach_columns)

    assert len(items) == 687
    for key, val in TEST_ITEM_DICT.items():
        assert val == items[2][key]


def test_read_shapefile_obscured():
    '''
    Tests reading attributes from the shapefile with real values obscured
    '''
    items = swot_reach_node_shp.read_shapefile(
        TEST_SHAPEFILE_PATH,
        obscure_data=True,
        columns=swot_constants.reach_columns)

    assert len(items) == 687
    for key, val in TEST_ITEM_DICT.items():
        if key == 'wse':
            assert val != items[2][key]
