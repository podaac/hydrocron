"""
This module searches for new granules and loads data into
the appropriate DynamoDB table
"""
import logging
import argparse
import sys

import boto3
import earthaccess
from botocore.exceptions import ClientError

from utils import constants

from hydrocron_db.hydrocron_database import HydrocronTable
from hydrocron_db.io import swot_reach_node_shp


def parse_args():
    """
    Argument parser
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--table_name",
                        dest='table_name',
                        required=True,
                        help="The name of the database table to add data")
    parser.add_argument("-sd", "--start_date",
                        dest="start",
                        required=False,
                        help="The ISO date time after which data should be retrieved. For Example, --start-date 2023-01-01T00:00:00")  # noqa E501
    parser.add_argument("-ed", "--end_date",
                        required=False,
                        dest="end",
                        help="The ISO date time before which data should be retrieved. For Example, --end-date 2023-02-14T00:00:00")  # noqa E501
    parser.add_argument("-obscure", "--obscure_data",
                        dest="obscure",
                        required=False,
                        help="Boolean to control whether real data is obscured on database loading. Default is False")  # noqa E501

    return parser.parse_args()


def setup_connection():
    """
    Set up DynamoDB connection

    Returns
    -------
    dynamo_instance : HydrocronDB
    """
    session = boto3.session.Session()
    dyndb_resource = session.resource('dynamodb')

    return dyndb_resource


def find_new_granules(collection_shortname, start_date, end_date):
    """
    Find granules to ingest

    Parameters
    ----------
    collection_shortname : string
        The shortname of the collection to search

    Returns
    -------
    granule_paths : list of strings
        List of S3 paths to the granules that have not yet been ingested
    """
    auth = earthaccess.login()

    cmr_search = earthaccess.DataGranules(auth). \
        short_name(collection_shortname).temporal(start_date, end_date)

    results = cmr_search.get()

    granule_paths = [g.data_links(access='direct') for g in results]
    return granule_paths


def load_data(hydrocron_table, granule_path, obscure_data):
    """
    Create table and load data

    hydrocron_table : HydrocronTable
        The table to load data into
    granules : list of strings
        The list of S3 paths of granules to load data from
    obscure_data : boolean
        If true, scramble the data values during load to prevent
        release of real data. Used during beta testing.
    """
    if hydrocron_table.table_name == constants.SWOT_REACH_TABLE_NAME:
        if 'Reach' in granule_path:
            items = swot_reach_node_shp.read_shapefile(
                granule_path,
                obscure_data,
                constants.REACH_DATA_COLUMNS)

            for item_attrs in items:
                # write to the table
                hydrocron_table.add_data(**item_attrs)

    elif hydrocron_table.table_name == constants.SWOT_NODE_TABLE_NAME:
        if 'Node' in granule_path:
            items = swot_reach_node_shp.read_shapefile(
                granule_path,
                obscure_data,
                constants.NODE_DATA_COLUMNS)

            for item_attrs in items:
                # write to the table
                hydrocron_table.add_data(**item_attrs)

    else:
        print('Items cannot be parsed, file reader not implemented for table '
              + hydrocron_table.table_name)


def main(args=None):
    """
    Main function to manage loading data into Hydrocron

    """
    if args is None:
        args = parse_args()

    table_name = args.table_name
    start_date = args.start
    end_date = args.end
    obscure_data = args.obscure

    match table_name:
        case constants.SWOT_REACH_TABLE_NAME:
            collection_shortname = constants.SWOT_REACH_COLLECTION_NAME
        case constants.SWOT_NODE_TABLE_NAME:
            collection_shortname = constants.SWOT_NODE_COLLECTION_NAME
        case constants.DB_TEST_TABLE_NAME:
            collection_shortname = constants.SWOT_REACH_COLLECTION_NAME
        case _:
            logging.warning(
                "Hydrocron table '%s' does not exist.", table_name)

    dynamo_resource = setup_connection()
    try:
        table = HydrocronTable(dyn_resource=dynamo_resource, table_name=table_name)
    except ClientError as err:
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            logging.info("Table '%s' does not exist.", table_name)

    new_granules = find_new_granules(
        collection_shortname,
        start_date,
        end_date)

    for granule in new_granules:
        load_data(table, granule[0], obscure_data)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pylint: disable=broad-except
        logging.exception("Uncaught exception occurred during execution.")
        sys.exit(hash(e))
