"""
Unpacks SWOT Reach & Node Shapefiles
"""
import os.path
import json
from datetime import datetime
import geopandas as gpd
import numpy as np


def read_shapefile(filepath, obscure_data, columns):
    """
    Reads a SWOT River Reach shapefile packaged as a zip

    Parameters
    ----------
    filename :  string
        The full path to the file to read
    obscure_data : boolean
        If true, obscure the data values to avoid exposing real data.
        Used during beta testing.
    columns : list
        The shapefile attributes to obscure if obscure_data=True

    Returns
    -------
    items : list
        A list containing json dictionaries of each item attributes to add
        to the database table
    """

    if filepath.startswith('s3'):
        shp_file = gpd.read_file('zip+' + filepath)
    else:
        shp_file = gpd.read_file('zip://' + filepath)

    if obscure_data:
        shp_file[columns] = np.where(
            (np.rint(shp_file[columns]) != -999) &
            (np.rint(shp_file[columns]) != -99999999) &
            (np.rint(shp_file[columns]) != -999999999999),
            np.random.default_rng().integers(low=0, high=10)*shp_file[columns],
            shp_file[columns])

    shp_file = shp_file.astype(str)

    filename = os.path.basename(filepath)
    filename_attrs = parse_from_filename(filename)

    items = []

    for _index, row in shp_file.iterrows():

        shp_attrs = json.loads(
            row.to_json(default_handler=str))

        item_attrs = shp_attrs | filename_attrs
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
