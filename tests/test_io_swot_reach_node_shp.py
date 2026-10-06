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
import geopandas as gpd
from shapely import Polygon, Point, geometry, wkt, centroid
from hydrocron.utils import constants

from hydrocron.db.io import swot_shp


def test_parse_from_filename_reach():
    """
    Tests parsing cycle, pass, and time ranges from filename
    """
    filename_attrs = swot_shp.parse_from_filename(
        constants.TEST_REACH_PATHNAME)

    assert filename_attrs['cycle_id'] == "548"
    assert filename_attrs['pass_id'] == "011"
    assert filename_attrs['continent_id'] == "NA"
    assert filename_attrs['range_start_time'] == "2023-06-10T19:33:37Z"
    assert filename_attrs['range_end_time'] == "2023-06-10T19:33:44Z"
    assert filename_attrs['crid'] == "PIA1"
    assert filename_attrs['collection_shortname'] == constants.TEST_REACH_COLLECTION_NAME
    assert filename_attrs['collection_version'] == "2.0"
    assert filename_attrs['granuleUR'] == constants.TEST_REACH_FILENAME
    assert datetime.strptime(filename_attrs['ingest_time'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc) - datetime.now(timezone.utc) <= timedelta(minutes=5)


def test_parse_from_filename_lake():
    """
    Tests parsing cycle, pass, and time ranges from filename
    """
    filename_attrs = swot_shp.parse_from_filename(
        constants.TEST_PLAKE_PATHNAME)

    assert filename_attrs['cycle_id'] == "018"
    assert filename_attrs['pass_id'] == "100"
    assert filename_attrs['continent_id'] == "GR"
    assert filename_attrs['range_start_time'] == "2024-07-13T11:17:41Z"
    assert filename_attrs['range_end_time'] == "2024-07-13T11:20:27Z"
    assert filename_attrs['crid'] == "PIC0"
    assert filename_attrs['collection_shortname'] == constants.TEST_PLAKE_COLLECTION_NAME
    assert filename_attrs['collection_version'] == "2.0"
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


def test_assemble_attributes_stringifies_nan():
    """A NaN in a numeric column must be replaced by the fill value, not survive as a Python float.

    Regression: DynamoDB's batch writer rejects Python floats ("Float types are not supported"),
    so a genuine NaN (not the -999... fill value) in a numeric field crashed the whole granule
    load and sent it to the DLQ. On pandas 3.0, astype(str) leaves NaN as a Python float (it no
    longer renders it as the string "nan"), so assemble_attributes must fill it first. Assert both
    the fix's contract (NaN -> FILL_VALUE) and the invariant (no Python float in any item).
    """
    geodf = gpd.GeoDataFrame(
        {
            "reach_id": ["11111111111", "22222222222"],
            "wse": [12.3, np.nan],
            "xtrk_dist": [np.nan, 4.5],
            "geometry": [Point(0, 0), Point(1, 1)],
        },
        geometry="geometry",
    )

    items = swot_shp.assemble_attributes(geodf, {"granuleUR": "test_granule.zip"})

    # NaN cells become the fill value; real values still stringify.
    assert items[0]["xtrk_dist"] == constants.FILL_VALUE
    assert items[1]["wse"] == constants.FILL_VALUE
    assert items[0]["wse"] == "12.3"
    assert items[1]["xtrk_dist"] == "4.5"

    # No Python float leaks into any item.
    float_values = [(k, v) for item in items for k, v in item.items() if isinstance(v, float)]
    assert not float_values, \
        f"NaN/float leaked into items; DynamoDB rejects Python floats: {float_values}"


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
