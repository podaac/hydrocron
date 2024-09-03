"""
Tests for track status operations
"""

import datetime
import json
import os
import pathlib
from unittest.mock import MagicMock

import vcr

from hydrocron.utils import constants

def test_query_cmr(mock_ssm):
    """Test the query_cmr function.
    
    Uses vcrpy to record CMR API response.
    """
    from hydrocron.db.track_ingest import Track
    
    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20240630", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    track = Track(collection_shortname, collection_start_date)
    track.query_start = datetime.datetime(2024, 6, 30, 0, 0, 0, tzinfo=datetime.timezone.utc)
    track.query_end = datetime.datetime(2024, 6, 30, 12, 0, 0, tzinfo=datetime.timezone.utc)

    vcr_cassette = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) \
        .joinpath('vcr_cassettes').joinpath('cmr_query.yaml')
    with vcr.use_cassette(vcr_cassette):
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
    
    table_name = constants.SWOT_REACH_TABLE_NAME
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
    track.query_hydrocron(hydrocron_table, cmr_granules)
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


def test_get_status(track_ingest_fixture):
    """Test get_status function.
    
    Parameters
    ----------
    track_ingest_fixture: Fixture ensuring the database is configured for track ingest operations
    """
    import hydrocron.utils.connection 
    from hydrocron.api.data_access.db import DynamoDataRepository
    
    hydrocron_table = DynamoDataRepository(hydrocron.utils.connection._dynamodb_resource)
    items = hydrocron_table.get_status(constants.SWOT_REACH_TRACK_INGEST_TABLE_NAME, "to_ingest")
    expected = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip",
        "revision_date": "2024-05-22T19:15:44.572Z",
        "checksum": "0823db619be0044e809a5f992e067d03",
        "expected_feature_count": 664,
        "actual_feature_count": 0,
        "status": "to_ingest"
    }]
    assert items == expected


def test_count_features(track_ingest_fixture):
    """Test count_features function.
    
    Parameters
    ----------
    track_ingest_fixture: Fixture ensuring the database is configured for track ingest operations
    """
    from hydrocron.db.io.swot_shp import count_features
    import hydrocron.utils.connection
    
    granule_ur = "s3://podaac-swot-ops-cumulus-protected/SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"
    num_features = count_features(granule_ur, hydrocron.utils.connection._s3_resource)
    assert num_features == 664


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
    
    hydrocron_track_table = constants.SWOT_REACH_TRACK_INGEST_TABLE_NAME
    track.query_track_ingest(hydrocron_track_table)
    
    expected = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip",
        "revision_date": "2024-05-22T19:15:44.572Z",
        "checksum": "0823db619be0044e809a5f992e067d03",
        "expected_feature_count": 664,
        "actual_feature_count": 664,
    }]
    assert track.ingested == expected


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
    
    track_reach_table = HydrocronTable(hydrocron.utils.connection._dynamodb_resource, constants.SWOT_REACH_TRACK_INGEST_TABLE_NAME)
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
    
    hydrocron_track_table = constants.SWOT_REACH_TRACK_INGEST_TABLE_NAME
    track.query_track_ingest(hydrocron_track_table)
    
    expected = [{
        "granuleUR": "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip",
        "revision_date": "2024-05-22T19:15:44.572Z",
        "checksum": "0823db619be0044e809a5f992e067d03",
        "expected_feature_count": 665,
        "actual_feature_count": 664,
        "status": "to_ingest"
    }]
    assert track.to_ingest == expected
