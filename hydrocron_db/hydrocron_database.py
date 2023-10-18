"""
Hydrocron Table module
"""
import logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)


class DynamoKeys:  # pylint: disable=R0903
    """
    Represents the partition and sort keys for a dynamoDB table
    """

    def __init__(
            self,
            partition_key,
            partition_key_type,
            sort_key,
            sort_key_type):
        self.partition_key = partition_key
        self.partition_key_type = partition_key_type
        self.sort_key = sort_key
        self.sort_key_type = sort_key_type


class HydrocronTable:
    """
    Class representing a Hydrocron DynamoDB table
    """

    def __init__(self, dyn_resource,
                 table_name):
        """
        Parameters
        -----------
        dyn_resource : boto3.session.resource('dynamodb')
            A Boto3 DynamoDB resource.
        table_name : string
            The name of the table to create.
        """
        self.dyn_resource = dyn_resource

        if self.exists(table_name):
            self.table = self.dyn_resource.Table(table_name)
            self.table.load()

            self.partition_key_name = self.table.key_schema[0]['AttributeName']
            self.sort_key_name = self.table.key_schema[1]['AttributeName']
        else:
            logger.error(
                "Table %s does not exist",
                table_name)

    def exists(self, table_name):
        """
        Determines whether a table exists.

        Parameters
        ----------
        table_name : string
            The name of the table to check.

        Returns
        -------
        boolean
            True when the table exists; otherwise, False.
        """
        try:
            table = self.dyn_resource.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceNotFoundException':
                exists = False
            else:
                logger.error(
                    "Couldn't check for existence of %s. %s: %s",
                    table_name,
                    err.response['Error']['Code'],
                    err.response['Error']['Message'])
                raise
        else:
            self.table = table

        return exists

    def add_data(self, **kwargs):
        """
        Adds a data item to the table.

        Parameters
        ---------
        **kwargs: All attributes to add to the item. Must include partition and sort keys # noqa
        """

        item_dict = {}

        for key, value in kwargs.items():
            item_dict[key] = value

        try:
            self.table.put_item(
                Item=item_dict
            )
        except ClientError as err:
            logger.error(
                "Couldn't add item %s to table %s. Here's why: %s: %s",
                self.partition_key_name, self.table.name,
                err.response['Error']['Code'],
                err.response['Error']['Message'])
            raise

    def run_query(self, partition_key, sort_key=None):
        """
        Perform a query. This is a helper function for testing purposes.
        More advanced queries can be configured outside of this class.

        Parameters
        ----------
        partition_key : string
            the feature id to query
        sort_key : integer
            the value of the sort keys to query

        Returns
        -------
            The item.
        """
        if sort_key is None:
            key_condition_expression = (Key(self.partition_key_name).eq(partition_key))
        else:
            key_condition_expression = (
                        Key(self.partition_key_name).eq(partition_key) & Key(self.sort_key_name).eq(sort_key))

        try:
            response = self.table.query(KeyConditionExpression=key_condition_expression)
        except ClientError as err:
            logger.error(
                "Couldn't query for items: %s: %s",
                err.response['Error']['Code'],
                err.response['Error']['Message'])
            raise

        return response['Items']

    def delete_item(self, partition_key, sort_key):
        """
        Deletes an item from the table.

        Parameters
        ----------
        partition_key: string
            The ID of the item to delete.
        sort_key: string
            The timestamp of the item to delete.
        """
        try:
            self.table.delete_item(Key={self.partition_key_name: partition_key,
                                        self.sort_key_name: sort_key})
        except ClientError as err:
            logger.error(
                "Couldn't delete item %s. %s: %s", partition_key,
                err.response['Error']['Code'],
                err.response['Error']['Message'])
            raise
