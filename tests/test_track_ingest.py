"""
Tests for track status operations
"""

import datetime
import json
import os
import pathlib

import vcr

from hydrocron.utils import constants

def test_query_cmr():
    """Test the query_cmr function.
    
    Uses vcrpy to record CMR API response.
    """
    from hydrocron.db.track_ingest import Track
    
    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20240630", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    hydrocron_table = "hydrocron-swot-reach-table"
    track = Track(collection_shortname, collection_start_date, hydrocron_table)
    track.revision_end = datetime.datetime(2024, 6, 30, 12, 0, 0, tzinfo=datetime.timezone.utc)

    vcr_cassette = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) \
        .joinpath('vcr_cassettes').joinpath('cmr_query.yaml')
    with vcr.use_cassette(vcr_cassette, decode_compressed_response=True):
        track.query_cmr()
        actual_data = track.cmr_granules
        
    expected_file = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('query_cmr_granule_results.json'))
    with open(expected_file) as jf:
        expected_data = json.load(jf)

    assert sorted(actual_data.items()) == sorted(expected_data.items())


def test_get_granule_ur(hydrocron_api):
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
    granule_ur = "SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip"
    actual_data = data_repository.get_granule_ur(table_name, granule_ur)
        
    assert actual_data["Items"][0]["granuleUR"] == granule_ur
    
def test_query_hydrocron(hydrocron_api):
    """
    Test query_hydrocron function.
    
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    from hydrocron.db.track_ingest import Track
    
    collection_shortname = "SWOT_L2_HR_RiverSP_reach_2.0"
    collection_start_date = datetime.datetime.strptime("20240630", "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    hydrocron_table = "hydrocron-swot-reach-table"
    track = Track(collection_shortname, collection_start_date, hydrocron_table)
    track.cmr_granules = {
        "SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01": {
            "revision_date": "2024-06-30T01:33:13.037Z",
            "checksum": "edda7230d20f1a85bae82f9917c86aa1"
        }
    }
    track.query_hydrocron()
    actual_data = track.hydrocron_granules
    print(actual_data)
    
    assert sorted(actual_data.items()) == sorted(track.cmr_granules.items())