"""
Database module
"""

import logging
from datetime import datetime
from typing import Generator

from boto3.resources.base import ServiceResource
from hydrocron_db.hydrocron_database import HydrocronDB
from boto3.dynamodb.conditions import Key  # noqa: E501 # pylint: disable=C0412


class DynamoDataRepository:
    """
    Class Dynamo Data
    """

    def __init__(self, dynamo_resource: ServiceResource):
        self._dynamo_instance = HydrocronDB(dyn_resource=dynamo_resource)
        self._logger = logging.getLogger('hydrocronapi.data_access.db.DynamoDataRepository')

    def get_reach_series_by_feature_id(self, feature_id: str, start_time: datetime, end_time: datetime) -> Generator:  # noqa: E501 # pylint: disable=W0613
        """

        @param feature_id:
        @param start_time:
        @param end_time:
        @return:
        """
        table_name = 'hydrocron-swot-reach-table'

        hydrocron_reach_table = self._dynamo_instance.load_table(table_name)
        items = hydrocron_reach_table.query(KeyConditionExpression=Key('reach_id').eq(feature_id))
        return items

    def get_node_series_by_feature_id(self, feature_id, start_time, end_time):  # noqa: E501 # pylint: disable=W0613
        """

        @param feature_id:
        @param start_time:
        @param end_time:
        @return:
        """
        table_name = 'hydrocron-swot-node-table'

        hydrocron_reach_table = self._dynamo_instance.load_table(table_name)
        items = hydrocron_reach_table.query(KeyConditionExpression=Key('node_id').eq(feature_id))
        return items
