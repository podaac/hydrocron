"""
Tests for track status operations
"""

import datetime
import json
import os
import pathlib
from unittest.mock import MagicMock
from unittest.mock import patch

from moto.core import DEFAULT_ACCOUNT_ID
from moto.sns import sns_backends
import pytest
import vcr

from hydrocron.utils import constants

FEATURE_ID = {
    "SWOT_L2_HR_RiverSP_reach_2.0": "reach_id",
    "SWOT_L2_HR_RiverSP_node_2.0": "node_id",
    "SWOT_L2_HR_LakeSP_prior_2.0": "lake_id"
}

SHORTNAME = {
    "SWOT_L2_HR_RiverSP_reach_2.0": "SWOT_L2_HR_RiverSP_2.0",
    "SWOT_L2_HR_RiverSP_node_2.0": "SWOT_L2_HR_RiverSP_2.0",
    "SWOT_L2_HR_LakeSP_prior_2.0": "SWOT_L2_HR_LakeSP_2.0"
}

TABLE_COLLECTION_INFO = [
    {'collection_name': 'SWOT_L2_HR_RiverSP_2.0',
     'table_name': 'hydrocron-swot-reach-table',
     'track_table': 'hydrocron-swot-reach-track-ingest-table',
     'feature_type': 'Reach',
     'api_feature_type': 'reach',
     'feature_id': 'reach_id',
     'partition_key': constants.SWOT_REACH_PARTITION_KEY,
     'sort_key': constants.SWOT_REACH_SORT_KEY
     },
    {'collection_name': 'SWOT_L2_HR_RiverSP_2.0',
     'table_name': 'hydrocron-swot-node-table',
     'track_table': 'hydrocron-swot-node-track-ingest-table',
     'feature_type': 'Node',
     'api_feature_type': 'node',
     'feature_id': 'node_id',
     'partition_key': constants.SWOT_NODE_PARTITION_KEY,
     'sort_key': constants.SWOT_NODE_SORT_KEY
     },
    {'collection_name': 'SWOT_L2_HR_LakeSP_2.0',
     'table_name': 'hydrocron-swot-prior-lake-table',
     'track_table': 'hydrocron-swot-prior-lake-track-ingest-table',
     'feature_type': 'LakeSP_Prior',
     'api_feature_type': 'priorlake',
     'feature_id': 'lake_id',
     'partition_key': constants.SWOT_PRIOR_LAKE_PARTITION_KEY,
     'sort_key': constants.SWOT_PRIOR_LAKE_SORT_KEY
     }
]

@patch("hydrocron.utils.constants.SHORTNAME", SHORTNAME)
def test_query_cmr(mock_ssm):
    """Test the query_cmr function.
    
    Uses vcrpy to record CMR API response.
    """
    os.environ['HYDROCRON_ENV'] = 'OPS'
    from hydrocron.db.track_ingest import Track

    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20240630", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    track.query_start = datetime.datetime(2024, 6, 30, 0, 0, 0, tzinfo=datetime.timezone.utc)
    track.query_end = datetime.datetime(2024, 6, 30, 12, 0, 0, tzinfo=datetime.timezone.utc)

    vcr_cassette = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) \
        .joinpath('vcr_cassettes').joinpath('cmr_query.yaml')
    with vcr.use_cassette(vcr_cassette, decode_compressed_response=True):
        track.query_cmr(False)
        actual_data = track.query_cmr(False)
        
    expected_file = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                .joinpath('test_data').joinpath('query_cmr_granule_results.json'))
    with open(expected_file) as jf:
        expected_data = json.load(jf)

    assert sorted(actual_data.items()) == sorted(expected_data.items())


def test_get_granule_ur(track_ingest_fixture):
    """
    Test query granuleUR item.
    
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    from hydrocron.utils import connection
    from hydrocron.api.data_access.db import DynamoDataRepository
    
    data_repository = DynamoDataRepository(connection.dynamodb_resource)
    
    table_name = constants.API_TEST_REACH_TABLE_NAME
    granule_ur = "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"
    actual_data = data_repository.get_granule_ur(table_name, granule_ur)
        
    assert actual_data["Items"][0]["granuleUR"] == granule_ur


def test_query_hydrocron(track_ingest_fixture):
    """
    Test query_hydrocron function.
    
    Parameters
    ----------
    track_ingest_fixture: Fixture ensuring the database is configured for track ingest operations
    """
    from hydrocron.db.track_ingest import Track
    
    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20240630", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    cmr_granules = {
        "SWOT_L2_HR_RiverSP_Reach_584_024_NA_20230610T193337_20230610T193344_PIA1_01": {
            "revision_date": "2024-06-30T01:33:13.037Z",
            "checksum": "edda7230d20f1a85bae82f9917c86aa1"
        }
    }
    hydrocron_table = "hydrocron-swot-reach-table"
    track.query_hydrocron(hydrocron_table, cmr_granules, "PGC0")
    actual_data = track.to_ingest

    expected = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_584_024_NA_20230610T193337_20230610T193344_PIA1_01",
        "revision_date": "2024-06-30T01:33:13.037Z",
        "checksum": "edda7230d20f1a85bae82f9917c86aa1",
        "expected_feature_count": -1,
        "actual_feature_count": 0,
        "status": "to_ingest"
    }]
    assert actual_data == expected


def test_query_hydrocron_reprocessed(track_ingest_fixture):
    """Test cases where reprocessed CRID comes in after forward stream."""
    from hydrocron.db.track_ingest import Track

    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20231201", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    cmr_granules = {
        "SWOT_L2_HR_RiverSP_Reach_009_499_AF_20240121T225107_20240121T225110_PGC0_01.zip": {
            "revision_date": "2024-07-17T06:06:42.102Z",
            "checksum": "7620183b46f90758241a5eac86c4efb3"
        }
    }
    hydrocron_table = "hydrocron-swot-reach-table"
    track.query_hydrocron(hydrocron_table, cmr_granules, "PGC0")
    actual_data = track.to_ingest

    expected = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_009_499_AF_20240121T225107_20240121T225110_PGC0_01.zip",
        "revision_date": "2024-07-17T06:06:42.102Z",
        "checksum": "7620183b46f90758241a5eac86c4efb3",
        "expected_feature_count": -1,
        "actual_feature_count": 0,
        "status": "to_ingest"
    }]

    assert actual_data == expected


def test_query_hydrocron_product_counter_increment(track_ingest_fixture):
    """Test cases where product counter is incremented."""
    from hydrocron.db.track_ingest import Track

    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20231201", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    cmr_granules = {
        "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_02.zip": {
            "revision_date": "2024-01-01T06:06:42.102Z",
            "checksum": "abc1234"
        }
    }
    hydrocron_table = "hydrocron-swot-reach-table"
    track.query_hydrocron(hydrocron_table, cmr_granules, "PGC0")
    actual_data = track.to_ingest

    expected = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_02.zip",
        "revision_date": "2024-01-01T06:06:42.102Z",
        "checksum": "abc1234",
        "expected_feature_count": -1,
        "actual_feature_count": 0,
        "status": "to_ingest"
    }]

    assert actual_data == expected


def test_query_hydrocron_product_counter_previous(track_ingest_fixture):
    """Test cases where previous product counter arrives after increment."""
    from hydrocron.db.track_ingest import Track

    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20231201", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    cmr_granules = {
        "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_00.zip": {
            "revision_date": "2024-01-01T06:06:42.102Z",
            "checksum": "abc1234"
        }
    }
    hydrocron_table = "hydrocron-swot-reach-table"
    track.query_hydrocron(hydrocron_table, cmr_granules, "PGC0")
    actual_data = track.to_ingest

    print(actual_data)

    expected = []
    assert actual_data == expected


def test_get_status(track_ingest_fixture):
    """Test get_status function.
    
    Parameters
    ----------
    track_ingest_fixture: Fixture ensuring the database is configured for track ingest operations
    """
    import hydrocron.utils.connection 
    from hydrocron.api.data_access.db import DynamoDataRepository
    
    hydrocron_table = DynamoDataRepository(hydrocron.utils.connection._dynamodb_resource)
    items = hydrocron_table.get_status(constants.TEST_REACH_TRACK_INGEST_TABLE_NAME, "to_ingest")
    expected = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip",
        "revision_date": "2024-05-22T19:15:44.572Z",
        "checksum": "0823db619be0044e809a5f992e067d03",
        "expected_feature_count": 664,
        "actual_feature_count": 0,
        "status": "to_ingest"
    }]
    assert items == expected


def test_get_series_granule_ur(track_ingest_fixture):
    """Test get_series_granule_ur.
    
    Parameters
    ----------
    track_ingest_fixture: Fixture ensuring the database is configured for track ingest operations
    """

    import hydrocron.utils.connection 
    from hydrocron.api.data_access.db import DynamoDataRepository
    
    hydrocron_table = DynamoDataRepository(hydrocron.utils.connection._dynamodb_resource)
    table_name = constants.API_TEST_REACH_TABLE_NAME
    feature_name = "reach_id"
    granule_ur = "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"
    items = hydrocron_table.get_series_granule_ur(table_name, feature_name, granule_ur)
    assert len(items) == 664


@patch("hydrocron.utils.constants.FEATURE_ID", FEATURE_ID)
def test_query_ingest(track_ingest_fixture):
    """Test query_ingest function.
    
    Parameters
    ----------
    track_ingest_fixture: Fixture ensuring the database is configured for track ingest operations
    """
    from hydrocron.db.track_ingest import Track
            
    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20240630", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    track._query_for_granule_ur = MagicMock(name="_query_for_granule_ur")
    track._query_for_granule_ur.return_value = "s3://podaac-swot-ops-cumulus-protected/SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"
    
    hydrocron_track_table = constants.TEST_REACH_TRACK_INGEST_TABLE_NAME
    hydrocron_table = constants.API_TEST_REACH_TABLE_NAME
    track.query_track_ingest(hydrocron_track_table, hydrocron_table, "PGC0")
    
    expected = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip",
        "revision_date": "2024-05-22T19:15:44.572Z",
        "checksum": "0823db619be0044e809a5f992e067d03",
        "expected_feature_count": 664,
        "actual_feature_count": 664,
    }]
    assert track.ingested == expected


@patch("hydrocron.utils.constants.FEATURE_ID", FEATURE_ID)
def test_query_ingest_to_ingest(track_ingest_fixture):
    """Test query_ingest function for require ingest.
    
    Parameters
    ----------
    track_ingest_fixture: Fixture ensuring the database is configured for track ingest operations
    """
    from hydrocron.db.track_ingest import Track
    from hydrocron.db import HydrocronTable
    import hydrocron.utils.connection
    
    TEST_SHAPEFILE_PATH_REACH_TRACK = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'data',
        "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"
    )
    
    track_reach_table = HydrocronTable(hydrocron.utils.connection._dynamodb_resource, constants.TEST_REACH_TRACK_INGEST_TABLE_NAME)
    track_ingest_record = [{
        "granuleUR": os.path.basename(TEST_SHAPEFILE_PATH_REACH_TRACK),
        "revision_date": "2024-05-22T19:15:44.572Z",
        "expected_feature_count": 665,
        "actual_feature_count": 0,
        "checksum": "0823db619be0044e809a5f992e067d03",
        "status": "to_ingest"
    }]
    track_reach_table.batch_fill_table(track_ingest_record)
        
    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20240630", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    track._query_for_granule_ur = MagicMock(name="_query_for_granule_ur")
    track._query_for_granule_ur.return_value = "s3://podaac-swot-ops-cumulus-protected/SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"

    hydrocron_track_table = constants.TEST_REACH_TRACK_INGEST_TABLE_NAME
    hydrocron_table = constants.API_TEST_REACH_TABLE_NAME
    track.query_track_ingest(hydrocron_track_table, hydrocron_table, "PGC0")
    
    expected = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip",
        "revision_date": "2024-05-22T19:15:44.572Z",
        "checksum": "0823db619be0044e809a5f992e067d03",
        "expected_feature_count": 665,
        "actual_feature_count": 664,
        "status": "to_ingest"
    }]
    assert track.to_ingest == expected


@patch("hydrocron.utils.constants.TABLE_COLLECTION_INFO", TABLE_COLLECTION_INFO)
def test_update_track_to_ingest(track_ingest_fixture):
    """Test query_ingest function for require ingest.
    
    Parameters
    ----------
    track_ingest_fixture: Fixture ensuring the database is configured for track ingest operations
    """
    from boto3.dynamodb.conditions import Key
    from hydrocron.db.track_ingest import Track
    import hydrocron.utils.connection
    
    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20240630", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    track.to_ingest = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_010_177_NA_20240131T074748_20240131T074759_PIC0_01.zip",
        "revision_date": "2024-06-30T21:22:23.123Z",
        "checksum": "1234",
        "expected_feature_count": -1,
        "actual_feature_count": 0,
        "status": "to_ingest"
    }]
    track.update_track_ingest(constants.TEST_REACH_TRACK_INGEST_TABLE_NAME)

    dynamodb = hydrocron.utils.connection._dynamodb_resource
    table = dynamodb.Table(constants.TEST_REACH_TRACK_INGEST_TABLE_NAME)
    table.load()
    actual_item = table.query(
        KeyConditionExpression=(Key("granuleUR").eq("SWOT_L2_HR_RiverSP_Reach_010_177_NA_20240131T074748_20240131T074759_PIC0_01.zip"))
    )
    assert actual_item["Items"] == track.to_ingest


@patch("hydrocron.utils.constants.TABLE_COLLECTION_INFO", TABLE_COLLECTION_INFO)
def test_update_track_ingested(track_ingest_fixture):
    """Test query_ingest function for require ingest.
    
    Parameters
    ----------
    track_ingest_fixture: Fixture ensuring the database is configured for track ingest operations
    """
    from boto3.dynamodb.conditions import Key
    from hydrocron.db.track_ingest import Track
    import hydrocron.utils.connection
    
    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20240630", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    track = Track(collection_shortname, collection_start_date)
    track.ingested = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip",
        "revision_date": "2024-05-22T19:15:44.572Z",
        "checksum": "0823db619be0044e809a5f992e067d03",
        "expected_feature_count":664,
        "actual_feature_count": 664,
    }]
    track.update_track_ingest(constants.TEST_REACH_TRACK_INGEST_TABLE_NAME)

    dynamodb = hydrocron.utils.connection._dynamodb_resource
    table = dynamodb.Table(constants.TEST_REACH_TRACK_INGEST_TABLE_NAME)
    table.load()
    actual_item = table.query(
        KeyConditionExpression=(Key("granuleUR").eq("SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"))
    )
    assert actual_item["Items"] == track.ingested


@patch("hydrocron.utils.constants.SHORTNAME", SHORTNAME)
def test_track_ingest_publish_cnm(track_ingest_cnm_fixture):
    """Test publish_cnm function.

    Parameters
    ----------
    track_ingest_cnm_fixture: Fixture ensuring SNS connection is configured
    """

    from hydrocron.db.track_ingest import Track

    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    query_start = datetime.datetime.strptime("2024-09-05T23:00:00", "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    query_end = datetime.datetime.strptime("2024-09-05T23:32:00", "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, query_start=query_start, query_end=query_end)
    track.to_ingest = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_020_457_NA_20240905T233134_20240905T233135_PIC0_01.zip",
        "revision_date": "2024-09-09T01:25:25.739Z",
        "checksum": "6ce27e868bd90055252de186f554759f",
        "expected_feature_count": -1,
        "actual_feature_count": 0,
        "status": "to_ingest"
    }]
    track.ENV = "test"

    vcr_cassette = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) \
        .joinpath('vcr_cassettes').joinpath('publish_cnm.yaml')
    with vcr.use_cassette(vcr_cassette, decode_compressed_response=True):
        track.publish_cnm_ingest(DEFAULT_ACCOUNT_ID)

    sns_backend = sns_backends[DEFAULT_ACCOUNT_ID]["us-west-2"]
    actual = json.loads(sns_backend.topics[f"arn:aws:sns:us-west-2:{DEFAULT_ACCOUNT_ID}:svc-hydrocron-test-cnm-response"].sent_notifications[0][1])

    expected_file = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                .joinpath('test_data').joinpath('track_ingest_cnm_message.json'))
    with open(expected_file) as jf:
        expected = json.load(jf)

    assert actual == expected


@patch("hydrocron.utils.constants.SHORTNAME", SHORTNAME)
@patch("hydrocron.utils.constants.TABLE_COLLECTION_INFO", TABLE_COLLECTION_INFO)
def test_track_ingest_mismatch(track_ingest_fixture):
    """Test cases where incorrect combination of shortname and table names are
    passed to track ingest operations."""

    import hydrocron.db.track_ingest

    class LambdaContext:
        def __init__(self):
            self.invoked_function_arn = "arn:aws:lambda:us-west-2:12345678910:function:svc-hydrocron-sit-track-ingest-lambda"

    event = {
        "collection_shortname": "SWOT_L2_HR_LakeSP_stream_2.0",
        "temporal": "",
        "query_start": "2024-09-05T23:00:00",
        "query_end": "2024-09-05T23:59:59",
        "reprocessed_crid": "PGC0"
    }
    context = LambdaContext()
    with pytest.raises(hydrocron.db.track_ingest.TableMisMatch) as e:
        hydrocron.db.track_ingest.track_ingest_handler(event, context)
        assert str(e.value) == "Error: Cannot query data for collection: 'SWOT_L2_HR_LakeSP_stream_2.0'"
