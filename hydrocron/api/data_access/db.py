"""
Database module
"""

import logging

from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key, And  # noqa: E501 # pylint: disable=C0412

from hydrocron.utils import constants


class DynamoDataRepository:
    """
    Class Dynamo Data
    """

    def __init__(self, dynamo_resource: ServiceResource):
        self._dynamo_instance = dynamo_resource
        self._logger = logging.getLogger('hydrocron.api.data_access.db.DynamoDataRepository')

    def get_series_by_feature_id(self, collection_name:str, feature_type: str, feature_id: str, start_time: str, end_time: str):  # noqa: E501 # pylint: disable=W0613
        """

        @param collection_name:
        @param feature_type:
        @param feature_id:
        @param start_time:
        @param end_time:
        @return:
        """

        for table_info in constants.TABLE_COLLECTION_INFO:
            if (table_info['collection_name'] in collection_name) & (table_info['feature_type'].lower() == feature_type.lower()):
                table_name = table_info['table_name']
                partition_key = table_info['partition_key']
                sort_key = table_info['sort_key']
                break
            else:
                return {'Items': []}

        hydrocron_table = self._dynamo_instance.Table(table_name)
        hydrocron_table.load()
        key_condition_expression = (
            Key(partition_key).eq(feature_id) &
            Key(sort_key).between(start_time, end_time)
        )
        items = self._query_hydrocron_table(hydrocron_table, key_condition_expression)
        return items

    def _query_hydrocron_table(self, hydrocron_table: str, key_condition_expression: And):
        """

        @param hydrocron_table:
        @param key_condition_expression:
        @return:
        """

        items = hydrocron_table.query(
                KeyConditionExpression=key_condition_expression
            )
        last_key_evaluated = ''
        if 'LastEvaluatedKey' in items.keys():
            last_key_evaluated = items['LastEvaluatedKey']

        while last_key_evaluated:
            next_items = hydrocron_table.query(
                ExclusiveStartKey=last_key_evaluated,
                KeyConditionExpression=key_condition_expression
            )
            items['Items'].extend(next_items['Items'])
            items['Count'] += next_items['Count']
            items['ScannedCount'] += next_items['ScannedCount']
            items['ResponseMetadata'] = next_items['ResponseMetadata']
            last_key_evaluated = ''
            if 'LastEvaluatedKey' in next_items.keys():
                last_key_evaluated = next_items['LastEvaluatedKey']
            else:
                items.pop('LastEvaluatedKey')

        return items

    def get_series_granule_ur(self, table_name, feature_name, granule_ur):
        """

        @param table_name: str - Hydrocron table to query
        @param granule_ur: str - Granule UR
        @return: dictionary of items
        """

        hydrocron_table = self._dynamo_instance.Table(table_name)
        hydrocron_table.load()

        items = hydrocron_table.query(
            ProjectionExpression=feature_name,
            IndexName="GranuleURIndex",
            KeyConditionExpression=(
                Key("granuleUR").eq(granule_ur)
            )
        )
        last_key_evaluated = ""
        if "LastEvaluatedKey" in items.keys():
            last_key_evaluated = items["LastEvaluatedKey"]

        while last_key_evaluated:
            next_items = hydrocron_table.query(
                ExclusiveStartKey=last_key_evaluated,
                ProjectionExpression=feature_name,
                IndexName="GranuleURIndex",
                KeyConditionExpression=(
                    Key("granuleUR").eq(granule_ur)
                )
            )
            items["Items"].extend(next_items["Items"])
            last_key_evaluated = ""
            if "LastEvaluatedKey" in next_items.keys():
                last_key_evaluated = next_items["LastEvaluatedKey"]

        return items["Items"]

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

    def get_status(self, table_name, status, limit=None):
        """

        @param table_name: str - Hydrocron table to query
        @param status: str - Status to query for
        @param limit: str - Return items up to and including the limit
        """

        hydrocron_table = self._dynamo_instance.Table(table_name)
        items = hydrocron_table.query(
            IndexName="statusIndex",
            KeyConditionExpression=(Key("status").eq(status))
        )

        if limit and items["Count"] >= limit:
            items["Items"] = items["Items"][:limit]
            if "LastEvaluatedKey" in items.keys():
                items.pop("LastEvaluatedKey")

        last_key_evaluated = ""
        if "LastEvaluatedKey" in items.keys():
            last_key_evaluated = items["LastEvaluatedKey"]

        while last_key_evaluated:
            next_items = hydrocron_table.query(
                ExclusiveStartKey=last_key_evaluated,
                IndexName="statusIndex",
                KeyConditionExpression=(Key("status").eq(status))
            )

            items["Items"].extend(next_items["Items"])
            if limit and items["Count"] >= limit:
                items["Items"] = items["Items"][:limit]
                break

            last_key_evaluated = ""
            if "LastEvaluatedKey" in next_items.keys():
                last_key_evaluated = next_items["LastEvaluatedKey"]

        if limit and len(items["Items"]) >= limit:
            items["Items"] = items["Items"][:limit]

        return items["Items"]
