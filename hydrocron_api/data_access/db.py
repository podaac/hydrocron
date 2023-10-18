"""
Database module
"""

import logging
from datetime import datetime
from typing import Generator

from boto3.resources.base import ServiceResource
from hydrocron_db.hydrocron_database import HydrocronDB
from boto3.dynamodb.conditions import Key  # noqa: E501 # pylint: disable=C0412

from utils import constants

class DynamoDataRepository:
    """
    Class Dynamo Data
    """

    def __init__(self, dynamo_resource: ServiceResource):
        self._dynamo_instance = dynamo_resource
        self._logger = logging.getLogger('hydrocron_api.data_access.db.DynamoDataRepository')

    def get_reach_series_by_feature_id(self, feature_id: str, start_time: datetime, end_time: datetime) -> Generator:  # noqa: E501 # pylint: disable=W0613
        """

        @param feature_id:
        @param start_time:
        @param end_time:
        @return:
        """
        table_name = constants.SWOT_REACH_TABLE_NAME

        hydrocron_table = self._dynamo_instance.Table(table_name)
        hydrocron_table.load()

        items = hydrocron_table.query(KeyConditionExpression=Key(
            constants.SWOT_REACH_PARTITION_KEY).eq(feature_id))
        return items

    def get_node_series_by_feature_id(self, feature_id, start_time, end_time):  # noqa: E501 # pylint: disable=W0613
        """

        @param feature_id:
        @param start_time:
        @param end_time:
        @return:
        """
        table_name = constants.SWOT_NODE_TABLE_NAME

        hydrocron_table = self._dynamo_instance.Table(table_name)
        hydrocron_table.load()

        items = hydrocron_table.query(KeyConditionExpression=Key(
            constants.SWOT_NODE_PARTITION_KEY).eq(feature_id))
        return items
