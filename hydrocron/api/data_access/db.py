"""
Database module
"""

import logging

from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key  # noqa: E501 # pylint: disable=C0412

from hydrocron.utils import constants


class DynamoDataRepository:
    """
    Class Dynamo Data
    """

    def __init__(self, dynamo_resource: ServiceResource):
        self._dynamo_instance = dynamo_resource
        self._logger = logging.getLogger('hydrocron.api.data_access.db.DynamoDataRepository')

    def get_reach_series_by_feature_id(self, feature_id: str, start_time: str, end_time: str):  # noqa: E501 # pylint: disable=W0613
        """

        @param feature_id:
        @param start_time:
        @param end_time:
        @return:
        """
        table_name = constants.SWOT_REACH_TABLE_NAME

        hydrocron_table = self._dynamo_instance.Table(table_name)
        hydrocron_table.load()

        items = hydrocron_table.query(KeyConditionExpression=(
            Key(constants.SWOT_REACH_PARTITION_KEY).eq(feature_id) &
            Key(constants.SWOT_REACH_SORT_KEY).between(start_time, end_time))
        )
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

        items = hydrocron_table.query(KeyConditionExpression=(
            Key(constants.SWOT_NODE_PARTITION_KEY).eq(feature_id) &
            Key(constants.SWOT_NODE_SORT_KEY).between(start_time, end_time))
        )
        return items

    def get_prior_lake_series_by_feature_id(self, feature_id, start_time, end_time):  # noqa: E501 # pylint: disable=W0613
        """

        @param feature_id:
        @param start_time:
        @param end_time:
        @return:
        """
        table_name = constants.SWOT_PRIOR_LAKE_TABLE_NAME

        hydrocron_table = self._dynamo_instance.Table(table_name)
        hydrocron_table.load()

        items = hydrocron_table.query(KeyConditionExpression=(
            Key(constants.SWOT_PRIOR_LAKE_PARTITION_KEY).eq(feature_id) &
            Key(constants.SWOT_PRIOR_LAKE_SORT_KEY).between(start_time, end_time))
        )
        return items

    def get_granule_ur(self, table_name, granule_ur):
        """

        @param table_name: str - Hydrocron table to query
        @param granule_ur: str - Granule UR
        @return: dictionary of items
        """

        hydrocron_table = self._dynamo_instance.Table(table_name)
        hydrocron_table.load()

        items = hydrocron_table.query(
            ProjectionExpression="granuleUR",
            Limit=1,
            IndexName="GranuleURIndex",
            KeyConditionExpression=(
                Key("granuleUR").eq(granule_ur)
            )
        )
        return items
