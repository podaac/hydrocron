"""
Tests for SQS-based CNM and granule load handlers.
"""

import json
import os
from unittest.mock import patch, MagicMock

import boto3
import moto
import pytest

from hydrocron.utils import constants


TEST_CNM_MESSAGE = {
    "identifier": "SWOT_L2_HR_RiverSP_Reach_020_457_NA_20240905T233134_20240905T233135_PIC0_01",
    "collection": "SWOT_L2_HR_RiverSP_2.0",
    "provider": "JPL-SWOT",
    "version": "1.6.0",
    "submissionTime": "2024-09-09T01:25:25.739Z",
    "product": {
        "dataVersion": "2.0",
        "files": [
            {
                "type": "data",
                "name": "SWOT_L2_HR_RiverSP_Reach_020_457_NA_20240905T233134_20240905T233135_PIC0_01.zip",
                "checksumType": "md5",
                "checksum": "6ce27e868bd90055252de186f554759f",
                "size": 745878,
                "uri": "s3://podaac-swot-ops-cumulus-protected/SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_020_457_NA_20240905T233134_20240905T233135_PIC0_01.zip"
            }
        ]
    }
}


@moto.mock_aws
def test_cnm_handler_sends_to_sqs():
    """Test that cnm_handler parses CNM message and sends to SQS."""

    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
    sqs = boto3.client("sqs", region_name="us-west-2")
    queue = sqs.create_queue(QueueName="test-granule-queue")
    queue_url = queue["QueueUrl"]

    os.environ["GRANULE_QUEUE_URL"] = queue_url

    from hydrocron.db.load_data import cnm_handler

    event = {
        "Records": [
            {"body": json.dumps(TEST_CNM_MESSAGE)}
        ]
    }

    cnm_handler(event, None)

    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
    assert len(messages["Messages"]) == 1

    msg_body = json.loads(messages["Messages"][0]["Body"])
    assert msg_body["body"]["granule_path"] == "s3://podaac-swot-ops-cumulus-protected/SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_020_457_NA_20240905T233134_20240905T233135_PIC0_01.zip"
    assert msg_body["body"]["checksum"] == "6ce27e868bd90055252de186f554759f"
    assert msg_body["body"]["revisionDate"] == "2024-09-09T01:25:25.739Z"
    assert msg_body["body"]["table_name"] is not None
    assert msg_body["body"]["track_table"] is not None
    assert msg_body["body"]["load_benchmarking_data"] == "False"


def test_granule_handler_sqs_record_format():
    """Test that granule_handler can unwrap SQS record format."""

    from hydrocron.db.load_data import granule_handler, MissingTable

    sqs_event = {
        "Records": [{
            "body": json.dumps({
                "body": {
                    "granule_path": "s3://podaac-swot-ops-cumulus-protected/SWOT_L2_HR_LakeSP_2.0/SWOT_L2_HR_LakeSP_Obs_020_150_EU_20240825T234434_20240825T235245_PIC0_01.zip",
                    "table_name": "hydrocron-swot-prior-lake-table",
                    "track_table": "hydrocron-swot-prior-lake-track-ingest-table",
                    "checksum": "abc123",
                    "revisionDate": "2024-09-09T01:25:25.739Z",
                    "load_benchmarking_data": "False"
                }
            })
        }]
    }

    with pytest.raises(MissingTable):
        granule_handler(sqs_event, None)


@moto.mock_aws
def test_cnm_handler_missing_table():
    """Test that cnm_handler raises MissingTable for unknown collection."""

    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
    sqs = boto3.client("sqs", region_name="us-west-2")
    queue = sqs.create_queue(QueueName="test-granule-queue")
    os.environ["GRANULE_QUEUE_URL"] = queue["QueueUrl"]

    from hydrocron.db.load_data import cnm_handler, MissingTable

    bad_cnm = {
        "submissionTime": "2024-09-09T01:25:25.739Z",
        "product": {
            "files": [{
                "type": "data",
                "checksum": "abc",
                "uri": "s3://bucket/UNKNOWN_COLLECTION/file.zip"
            }]
        }
    }

    event = {
        "Records": [
            {"body": json.dumps(bad_cnm)}
        ]
    }

    with pytest.raises(MissingTable):
        cnm_handler(event, None)
