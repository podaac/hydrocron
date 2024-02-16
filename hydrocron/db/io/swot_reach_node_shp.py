"""
Unpacks SWOT Reach & Node Shapefiles
"""
import os.path
import json
from datetime import datetime
from importlib import resources

import geopandas as gpd
import numpy as np
import pandas as pd


def read_shapefile(filepath, obscure_data, columns, s3_resource=None):
    """
    Reads a SWOT River Reach shapefile packaged as a zip

    Parameters
    ----------
    filepath :  string
        The full path to the file to read
    obscure_data : boolean
        If true, obscure the data values to avoid exposing real data.
        Used during beta testing.
    columns : list
        The shapefile attributes to obscure if obscure_data=True
    s3_resource : the s3 granule object to open
        Optional - the s3 object to open

    Returns
    -------
    items : list
        A list containing json dictionaries of each item attributes to add
        to the database table
    """
    filename = os.path.basename(filepath)
    lambda_temp_file = '/tmp/' + filename

    if filepath.startswith('s3'):
        bucket_name, key = filepath.replace("s3://", "").split("/", 1)
        s3_resource.Bucket(bucket_name).download_file(key, lambda_temp_file)

        shp_file = gpd.read_file('zip://' + lambda_temp_file)
    else:
        shp_file = gpd.read_file('zip://' + filepath)

    numeric_columns = shp_file[columns].select_dtypes(include=[np.number]).columns
    if obscure_data:
        shp_file[numeric_columns] = np.where(
            (np.rint(shp_file[numeric_columns]) != -999) &
            (np.rint(shp_file[numeric_columns]) != -99999999) &
            (np.rint(shp_file[numeric_columns]) != -999999999999),
            np.random.default_rng().integers(low=2, high=10)*shp_file[numeric_columns],
            shp_file[numeric_columns])

    shp_file = shp_file.astype(str)
    filename_attrs = parse_from_filename(filename)

    items = assemble_attributes(shp_file, filename_attrs)

    if os.path.exists(lambda_temp_file):
        os.remove(lambda_temp_file)

    return items


def assemble_attributes(file_as_str, attributes):
    """
    Helper function to concat file attributes to records

    Parameters
    ----------
    file_as_str : string
        The file records as a string

    attributes : dict
        A dictionary of attributes to concatenate
    """

    items = []

    for _index, row in file_as_str.iterrows():

        shp_attrs = json.loads(
            row.to_json(default_handler=str))

        item_attrs = shp_attrs | attributes
        items.append(item_attrs)

    return items


def parse_from_filename(filename):
    """
    Parses the cycle, pass, start and end time from
    the shapefile name and add to each item

    Parameters
    ----------
    filename :  string
        The string to parse

    Returns
    -------
    filename_attrs : dict
        A dictionary of attributes from the filename
    """

    filename_components = filename.split("_")

    filename_attrs = {
        'cycle_id': filename_components[5],
        'pass_id': filename_components[6],
        'continent_id': filename_components[7],
        'range_start_time': datetime.strptime(
            filename_components[8],
            '%Y%m%dT%H%M%S').strftime('%Y-%m-%dT%H:%M:%SZ'),
        'range_end_time': datetime.strptime(
            filename_components[9],
            '%Y%m%dT%H%M%S').strftime('%Y-%m-%dT%H:%M:%SZ'),
        'crid': filename_components[10]
    }

    return filename_attrs


def load_test_reach():
    """
    Loads many time steps for a fake reach_id to enable performance testing

    Returns
    -------
    items : list
        A list containing json dictionaries of each item attributes to add
        to the database table
    """
    items = []

    with resources.path("hydrocron.db", "test_reaches.csv") as csv:
        csv_file = pd.read_csv(csv, dtype=str)

        csv_file = csv_file.astype(str)
        filename_attrs = {
            'cycle_id': '000',
            'pass_id': '000',
            'continent_id': 'XX',
            'range_start_time': '2021-01-01T00:00:00Z',
            'range_end_time': '2024-12-31T23:59:00Z',
            'crid': 'TEST'
            }

        items = assemble_attributes(csv_file, filename_attrs)

    return items
