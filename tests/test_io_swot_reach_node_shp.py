"""
==============
test_io_swot_reach_node_shp.py
==============
Test unpacking a swot reach or node shapefile.

Unit tests for unpacking swot reach and node shapefiles.
"""
from datetime import datetime, timedelta, timezone
import pytz
import numpy as np
from shapely import Polygon, Point, geometry, wkt, centroid
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


def test_lake_null_geometry():
    """
    Tests replacing null geometry with fillvalue for lake polygons
    """
    items = swot_shp.read_shapefile(
        constants.TEST_PLAKE_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.PRIOR_LAKE_DATA_COLUMNS)

    geojson = geometry.mapping(wkt.loads(items[0]['geometry']))
    coords_0 = np.round(np.array(geojson['coordinates']), 3)

    assert str(Point(coords_0) == str(centroid(Polygon(
        constants.SWOT_PRIOR_LAKE_FILL_GEOMETRY_COORDS))))


def test_lake_centerpoints():
    """
    Tests replacing polygons with centerpoints
    """
    items = swot_shp.read_shapefile(
        constants.TEST_PLAKE_SHAPEFILE_PATH,
        obscure_data=False,
        columns=constants.PRIOR_LAKE_DATA_COLUMNS)

    geojson = geometry.mapping(wkt.loads(items[0]['geometry']))
    coords_0 = np.round(np.array(geojson['coordinates']), 3)

    assert str(Point(coords_0) == str(centroid(Polygon(
        constants.SWOT_PRIOR_LAKE_FILL_GEOMETRY_COORDS))))

    geojson_4596 = geometry.mapping(wkt.loads(items[4596]['geometry']))
    coords_4596 = np.round(np.array(geojson_4596['coordinates']), 3)

    geojson_test_4596 = geometry.mapping(centroid(Polygon(
        constants.TEST_PLAKE_GEOM_DICT['geometry'])))
    test_4596 = np.round(np.array(geojson_test_4596['coordinates']), 3)

    assert str(Point(coords_4596)) == str(Point(test_4596))


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


def test_read_benchmarking_data():
    """
    Tests reading the benchmarking data
    """
    items = swot_shp.load_benchmarking_data()

    assert len(items) == 1199
