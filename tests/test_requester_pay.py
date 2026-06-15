"""
Tests for requester pay S3 downloads.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import boto3
import moto
import pytest

from hydrocron.db.io import swot_shp


TEST_SHAPEFILE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data',
    "SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"
)


@moto.mock_aws
def test_read_shapefile_s3_requester_pay():
    """Test that read_shapefile passes RequestPayer=requester to S3."""
    from hydrocron.utils import constants

    s3 = boto3.resource("s3", region_name="us-west-2")
    bucket_name = "podaac-swot-ops-cumulus-protected"
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "us-west-2"}
    )

    key = "SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"
    s3.Bucket(bucket_name).upload_file(
        Filename=TEST_SHAPEFILE_PATH,
        Key=key
    )

    filepath = f"s3://{bucket_name}/{key}"
    items = swot_shp.read_shapefile(
        filepath,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS,
        s3_resource=s3
    )

    assert len(items) > 0


@moto.mock_aws
def test_read_shapefile_https_requester_pay():
    """Test that read_shapefile handles https:// paths with RequestPayer."""
    from hydrocron.utils import constants

    s3 = boto3.resource("s3", region_name="us-west-2")
    bucket_name = "podaac-swot-ops-cumulus-protected"
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "us-west-2"}
    )

    key = "SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"
    s3.Bucket(bucket_name).upload_file(
        Filename=TEST_SHAPEFILE_PATH,
        Key=key
    )

    filepath = f"https://s3.amazonaws.com/{bucket_name}/{key}"
    items = swot_shp.read_shapefile(
        filepath,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS,
        s3_resource=s3
    )

    assert len(items) > 0


def test_s3_download_called_with_requester_pays():
    """Test that download_file is called with RequestPayer=requester for s3:// paths."""
    mock_bucket = MagicMock()
    mock_s3 = MagicMock()
    mock_s3.Bucket.return_value = mock_bucket

    filepath = "s3://podaac-swot-ops-cumulus-protected/SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"

    mock_bucket.download_file.side_effect = lambda key, dest, **kwargs: _copy_test_file(dest)

    from hydrocron.utils import constants
    items = swot_shp.read_shapefile(
        filepath,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS,
        s3_resource=mock_s3
    )

    mock_bucket.download_file.assert_called_once()
    call_kwargs = mock_bucket.download_file.call_args
    assert call_kwargs.kwargs.get("ExtraArgs") == {"RequestPayer": "requester"} or \
        call_kwargs[1].get("ExtraArgs") == {"RequestPayer": "requester"}


def test_https_download_called_with_requester_pays():
    """Test that download_file is called with RequestPayer=requester for https:// paths."""
    mock_bucket = MagicMock()
    mock_s3 = MagicMock()
    mock_s3.Bucket.return_value = mock_bucket

    filepath = "https://s3.amazonaws.com/podaac-swot-ops-cumulus-protected/SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_020_149_NA_20240825T231711_20240825T231722_PIC0_01.zip"

    mock_bucket.download_file.side_effect = lambda key, dest, **kwargs: _copy_test_file(dest)

    from hydrocron.utils import constants
    items = swot_shp.read_shapefile(
        filepath,
        obscure_data=False,
        columns=constants.REACH_DATA_COLUMNS,
        s3_resource=mock_s3
    )

    mock_bucket.download_file.assert_called_once()
    call_kwargs = mock_bucket.download_file.call_args
    assert call_kwargs.kwargs.get("ExtraArgs") == {"RequestPayer": "requester"} or \
        call_kwargs[1].get("ExtraArgs") == {"RequestPayer": "requester"}


def _copy_test_file(dest):
    """Helper to copy the test shapefile to the download destination."""
    import shutil
    shutil.copy(TEST_SHAPEFILE_PATH, dest)
