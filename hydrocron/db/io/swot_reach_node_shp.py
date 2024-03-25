"""
Unpacks SWOT Reach & Node Shapefiles
"""
import os.path
import json
from datetime import datetime
from importlib import resources
import xml.etree.ElementTree as ET
import zipfile
import logging

import geopandas as gpd
import numpy as np
import pandas as pd
from hydrocron.utils import constants


logging.getLogger().setLevel(logging.INFO)


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
        with zipfile.ZipFile(lambda_temp_file) as archive:
            shp_xml_tree = ET.fromstring(archive.read(filename[:-4] + ".shp.xml"))
            
    elif filepath.startswith('https'):
        url, bucket_name, key = filepath.replace("https://", "").split("/", 2)
        s3_resource.Bucket(bucket_name).download_file(key, lambda_temp_file)

        shp_file = gpd.read_file('zip://' + lambda_temp_file)
        with zipfile.ZipFile(lambda_temp_file) as archive:
            shp_xml_tree = ET.fromstring(archive.read(filename[:-4] + ".shp.xml"))
    else:
        shp_file = gpd.read_file('zip://' + filepath)
        with zipfile.ZipFile(filepath) as archive:
            shp_xml_tree = ET.fromstring(archive.read(filename[:-4] + ".shp.xml"))

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

    xml_attrs = parse_metadata_from_shpxml(shp_xml_tree)

    attributes = filename_attrs | xml_attrs
    items = assemble_attributes(shp_file, attributes)

    if os.path.exists(lambda_temp_file):
        os.remove(lambda_temp_file)

    return items


def parse_metadata_from_shpxml(xml_elem):
    """
    Read the SWORD version number from the shp.xml file
    and add to the database fields

    Parameters
    ----------
    xml_elem : xml.etree.ElementTree.Element
        an Element representation of the shp.xml metadata file

    Returns
    -------
    metadata_attrs : dict
        a dictionary of metadata attributes to add to record
    """
    # get SWORD version
    for globs in xml_elem.findall('global_attributes'):
        prior_db_files = globs.find('xref_prior_river_db_files').text

    metadata_attrs = {
        'sword_version': prior_db_files[-5:-3]
    }

    # get units on fields that have them
    for child in xml_elem:
        if child.tag == 'attributes':
            for field in child:
                try:
                    units = field.find('units').text
                except AttributeError:
                    units = ""
                    logging.info('No units on field %s', field.tag)

                if units != "":
                    unit_field_name = field.tag + "_units"
                    metadata_attrs[unit_field_name] = units

    return metadata_attrs


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

    if 'Reach' in filename:
        collection = constants.SWOT_REACH_COLLECTION_NAME

    if 'Node' in filename:
        collection = constants.SWOT_NODE_COLLECTION_NAME

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
        'crid': filename_components[10],
        'collection_shortname': collection
    }

    return filename_attrs


def load_benchmarking_data():
    """
    Loads many time steps for a fake reach_id to enable performance testing

    Returns
    -------
    items : list
        A list containing json dictionaries of each item attributes to add
        to the database table
    """
    items = []

    with resources.path("hydrocron.db", "benchmarking_data_reaches.csv") as csv:
        csv_file = pd.read_csv(csv, dtype=str)

        logging.info("Read CSV")

        csv_file = csv_file.astype(str)

        filename_attrs = {
            'cycle_id': '000',
            'pass_id': '000',
            'continent_id': 'XX',
            'range_end_time': '2024-12-31T23:59:00Z',
            'crid': 'TEST',
            'collection_shortname': constants.SWOT_REACH_COLLECTION_NAME
            }

        items = assemble_attributes(csv_file, filename_attrs)

        count = str(len(items))
        logging.info("Benchmarking items: %s", count)

    return items
