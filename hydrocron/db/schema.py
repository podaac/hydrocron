"""
Hydrocron Table module
"""
import logging
import sys
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)


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
            The name of the table.
        """
        self.dyn_resource = dyn_resource
        self.table_name = table_name

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

    def batch_fill_table(self, items):
        """
        Fills the DynamoDB table with the specified data, using the Boto3
        Table.batch_writer() function to put the items in the table.
        Inside the context manager, Table.batch_writer builds a list of
        requests. On exiting the context manager, Table.batch_writer starts sending
        batches of write requests to Amazon DynamoDB and automatically
        handles chunking, buffering, and retrying.

        Parameters
        ----------
           items : The data to put in the table.
        """
        table = self.table

        try:
            with table.batch_writer() as writer:
                for item in items:
                    if sys.getsizeof(item) < 409600:
                        writer.put_item(Item=item)
                    else:
                        logger.Warning(
                            "Item larger than 400 KB, could not load: %s %s",
                            self.partition_key_name,
                            item[self.partition_key_name]
                        )
            logger.info("Loaded data into table %s.", table.name)

        except ClientError:
            logger.exception("Couldn't load data into table %s.", table.name)
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
