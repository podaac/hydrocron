"""
Database module
"""

import logging
from concurrent.futures import ThreadPoolExecutor, wait

from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key, And  # noqa: E501 # pylint: disable=C0412
from boto3.dynamodb.types import TypeDeserializer
from botocore.client import BaseClient

from hydrocron.utils import constants


# Shared across invocations of a warm Lambda; used for the parallel per-node queries.
NODE_QUERY_POOL = ThreadPoolExecutor(max_workers=constants.REACH_AND_NODE_QUERY_THREADS)
_DESERIALIZER = TypeDeserializer()


class ItemLimitExceeded(Exception):
    """
    Exception thrown when a reach has more node rows in the time range than allowed
    """

    def __init__(self, count, limit):
        super().__init__(f'{count} node rows exceeds the limit of {limit}')
        self.count = count
        self.limit = limit


def get_table_info(collection_name: str, feature_type: str):
    """Return the TABLE_COLLECTION_INFO entry for a collection and feature type, or None.

    Sub-collection names (e.g. SWOT_L2_HR_RiverSP_reach_D) resolve to their parent collection.

    @param collection_name: str - collection or sub-collection name
    @param feature_type: str - Reach, Node or PriorLake (case-insensitive)
    @return: dict or None
    """

    parent_collection = constants.SHORTNAME.get(collection_name, collection_name)
    for table_info in constants.TABLE_COLLECTION_INFO:
        if (table_info['collection_name'] == parent_collection) and (table_info['api_feature_type'].lower() == feature_type.lower()):
            return table_info
    return None


class DynamoDataRepository:
    """
    Class Dynamo Data
    """

    def __init__(self, dynamo_resource: ServiceResource, dynamo_client: BaseClient = None):
        self._dynamo_instance = dynamo_resource
        self._dynamo_client = dynamo_client
        self._logger = logging.getLogger('hydrocron.api.data_access.db.DynamoDataRepository')

    def get_series_by_feature_id(self, collection_name: str, feature_type: str, feature_id: str, start_time: str, end_time: str):  # pylint: disable=too-many-positional-arguments
        """

        @param collection_name:
        @param feature_type:
        @param feature_id:
        @param start_time:
        @param end_time:
        @return:
        """

        # If a sub-collection name was provided, validate it matches the requested feature type.
        if collection_name in constants.SUBCOLLECTION_FEATURE_TYPE:
            expected_feature_type = constants.SUBCOLLECTION_FEATURE_TYPE[collection_name]
            if feature_type != expected_feature_type:
                raise ValueError(
                    f"400: Sub-collection '{collection_name}' is not valid for feature type '{feature_type}'."
                )

        table_info = get_table_info(collection_name, feature_type)
        if table_info is None:
            return {'Items': []}

        hydrocron_table = self._dynamo_instance.Table(table_info['table_name'])
        hydrocron_table.load()
        key_condition_expression = (
            Key(table_info['partition_key']).eq(feature_id) &
            Key(table_info['sort_key']).between(start_time, end_time)
        )
        items = self._query_hydrocron_table(hydrocron_table, key_condition_expression)
        return items

    def get_node_ids_by_reach_id(self, collection_name: str, reach_id: str, start_time: str, end_time: str,  # pylint: disable=too-many-positional-arguments
                                 max_items: int = constants.MAX_REACH_NODE_ITEMS):
        """Return the sorted distinct node_ids with rows for a reach in the time range, from the node table's ReachIdIndex.

        Stops paging and raises ItemLimitExceeded as soon as the key count exceeds max_items,
        before any node rows are fetched.

        @param collection_name: str - collection or sub-collection name (resolved to its node table)
        @param reach_id: str - reach to find nodes for
        @param start_time: str - start of the time range
        @param end_time: str - end of the time range
        @param max_items: int - maximum number of node rows (GSI keys) allowed
        @return: tuple of (list of node_id str, number of node rows); ([], 0) if the collection has no node table
        """

        table_info = get_table_info(collection_name, 'Node')
        if table_info is None:
            return [], 0

        kwargs = {
            'TableName': table_info['table_name'],
            'IndexName': constants.SWOT_NODE_REACH_INDEX_NAME,
            'KeyConditionExpression': 'reach_id = :reach_id AND range_start_time BETWEEN :start_time AND :end_time',
            'ExpressionAttributeValues': {':reach_id': {'S': reach_id}, ':start_time': {'S': start_time}, ':end_time': {'S': end_time}},
            'ProjectionExpression': 'node_id'
        }
        node_ids = set()
        count = 0
        while True:
            response = self._dynamo_client.query(**kwargs)
            count += response['Count']
            if count > max_items:
                raise ItemLimitExceeded(count, max_items)
            node_ids.update(item['node_id']['S'] for item in response['Items'])
            if 'LastEvaluatedKey' not in response:
                return sorted(node_ids), count
            kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

    def get_node_series(self, collection_name: str, node_ids: list, start_time: str, end_time: str, attributes: list):  # pylint: disable=too-many-positional-arguments
        """Return node rows for each node_id in the time range, queried in parallel.

        Rows are in node_ids order, then time order within each node. Uses the shared low-level
        client (no Table.load() per node) and fetches only the given attributes.

        @param collection_name: str - collection or sub-collection name (resolved to its node table)
        @param node_ids: list of str - nodes to query
        @param start_time: str - start of the time range
        @param end_time: str - end of the time range
        @param attributes: list of str - attributes to return (ProjectionExpression)
        @return: list of dict items, deserialized like the boto3 resource; [] if the collection has no node table
        """

        table_info = get_table_info(collection_name, 'Node')
        if table_info is None:
            return []

        table_name = table_info['table_name']
        names = {f'#a{i}': attribute for i, attribute in enumerate(dict.fromkeys(attributes))}
        base_kwargs = {
            'TableName': table_name,
            'KeyConditionExpression': 'node_id = :node_id AND range_start_time BETWEEN :start_time AND :end_time',
            'ProjectionExpression': ', '.join(names),
            'ExpressionAttributeNames': names
        }

        def query_node(node_id):
            kwargs = dict(base_kwargs, ExpressionAttributeValues={
                ':node_id': {'S': node_id}, ':start_time': {'S': start_time}, ':end_time': {'S': end_time}})
            items = []
            while True:
                response = self._dynamo_client.query(**kwargs)
                items.extend({key: _DESERIALIZER.deserialize(value) for key, value in item.items()} for item in response['Items'])
                if 'LastEvaluatedKey' not in response:
                    return items
                kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

        futures = [NODE_QUERY_POOL.submit(query_node, node_id) for node_id in node_ids]
        try:
            return [item for future in futures for item in future.result()]
        finally:
            # On error, stop the rest before returning: Lambda freezes leftover threads and resumes them in
            # the next invocation. cancel() only stops queries not yet started, so also wait for running ones.
            for future in futures:
                future.cancel()
            wait(futures)

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
