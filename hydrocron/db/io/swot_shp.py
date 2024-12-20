"""
Unpacks SWOT Shapefiles
"""
import os.path
import tempfile
from datetime import datetime, timezone
from importlib import resources
import xml.etree.ElementTree as ET
import zipfile
import logging

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import Polygon

from hydrocron.utils import constants


logging.getLogger().setLevel(logging.INFO)


def read_shapefile(filepath, obscure_data, columns, s3_resource=None):
    """
    Reads a SWOT shapefile packaged as a zip

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

    with tempfile.TemporaryDirectory() as lambda_temp_dir_name:
        lambda_temp_file = os.path.join(lambda_temp_dir_name, filename)
        if filepath.startswith('s3'):
            bucket_name, key = filepath.replace("s3://", "").split("/", 1)
            logging.info("Opening granule %s from bucket %s", key, bucket_name)

            s3_resource.Bucket(bucket_name).download_file(key, lambda_temp_file)

            shp_file = gpd.read_file('zip://' + lambda_temp_file)
            with zipfile.ZipFile(lambda_temp_file) as archive:
                shp_xml_tree = ET.fromstring(archive.read(filename[:-4] + ".shp.xml"))

        elif filepath.startswith('https'):
            _, bucket_name, key = filepath.replace("https://", "").split("/", 2)
            logging.info("Opening granule %s from bucket %s", key, bucket_name)

            s3_resource.Bucket(bucket_name).download_file(key, lambda_temp_file)

            shp_file = gpd.read_file('zip://' + lambda_temp_file)
            with zipfile.ZipFile(lambda_temp_file) as archive:
                shp_xml_tree = ET.fromstring(archive.read(filename[:-4] + ".shp.xml"))
        else:
            shp_file = gpd.read_file('zip://' + filepath)
            with zipfile.ZipFile(filepath) as archive:
                shp_xml_tree = ET.fromstring(archive.read(filename[:-4] + ".shp.xml"))

    if 'LakeSP_Prior' in filename:
        shp_file = handle_null_geometries(shp_file)
        shp_file = convert_polygon_to_centerpoint(shp_file)

    if obscure_data:
        numeric_columns = shp_file[columns].select_dtypes(include=[np.number]).columns

        shp_file[numeric_columns] = np.where(
            (np.rint(shp_file[numeric_columns]) != -999) &
            (np.rint(shp_file[numeric_columns]) != -99999999) &
            (np.rint(shp_file[numeric_columns]) != -999999999999),
            np.random.default_rng().integers(low=2, high=10)*shp_file[numeric_columns],
            shp_file[numeric_columns])

    filename_attrs = parse_from_filename(filepath)

    xml_attrs = parse_metadata_from_shpxml(shp_xml_tree)

    attributes = filename_attrs | xml_attrs
    items = assemble_attributes(shp_file, attributes)

    return items


def handle_null_geometries(geodf):
    """
    Assign fill value polygon to any features that contain null geometries

    Parameters
    ----------
    geodf : geopandas.GeoDataFrame
        the geodataframe containing the unpacked shapefile features

    Returns
    -------
    geodf_no_nulls : geopandas.GeoDataFrame
        the geodataframe with null geometries handled
    """
    logging.info('Starting handle null geometries')
    geodf['geometry'].fillna(
        value=Polygon(constants.SWOT_PRIOR_LAKE_FILL_GEOMETRY_COORDS),
        inplace=True)

    return geodf


def convert_polygon_to_centerpoint(geodf_polygon):
    """
    Converts polygon geometries to centerpoints. Used to reduce the size of lake features

    Parameters
    ----------
    geodf_polygon : geopandas.GeoDataFrame
        the geodataframe containing the unpacked shapefile features with polygon feature types

    Returns
    -------
    geodf_centerpoint : geopandas.GeoDataFrame
        the geodataframe with point feature types and calculated centerpoint geometries
    """
    logging.info('Starting convert polygon to centerpoint')

    geodf_centerpoint = geodf_polygon
    geodf_centerpoint['geometry'] = geodf_polygon['geometry'].centroid

    return geodf_centerpoint


def parse_metadata_from_shpxml(xml_elem):
    """
    Read the prior database (SWORD or PLD) version number from the shp.xml file
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
    logging.info('Starting parse metadata from shpfile')
    # get SWORD version
    for globs in xml_elem.findall('global_attributes'):
        prior_db_files = globs.find('xref_prior_river_db_files').text
        metadata_attrs = {'sword_version': prior_db_files[-5:-3]}

    # get PLD version
    for globs in xml_elem.findall('global_metadata'):
        prior_db_files = globs.find('xref_prior_lake_db_file').text
        metadata_attrs = {'PLD_version': prior_db_files[-10:-7]}

    # get units on fields that have them
    for child in xml_elem:
        if child.tag in ('attributes', 'attribute_metadata'):
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


def assemble_attributes(geodf, attributes):
    """
    Helper function to concat file attributes to records

    Parameters
    ----------
    geodf : geodataframe
        The file records as a geodataframe

    attributes : dict
        A dictionary of attributes to concatenate
    """
    logging.info('Starting assemble attributes')

    items = []

    geodf = geodf.astype(str)
    geodf = geodf.assign(**attributes)
    items = geodf.to_dict('records')

    return items


def parse_from_filename(filepath):
    """
    Parses the cycle, pass, start and end time from
    the shapefile name and add to each item

    Parameters
    ----------
    filepath :  string
        The full uri of the granule to parse

    Returns
    -------
    filename_attrs : dict
        A dictionary of attributes from the filename
    """
    logging.info('Starting parse attributes from filename')

    filename = os.path.basename(filepath)
    filename_components = filename.split("_")

    collection = ""
    collection_version = ""

    for table_info in constants.TABLE_COLLECTION_INFO:
        if (table_info['feature_type'] in filename) & (table_info['collection_name'] in filepath):
            collection = table_info['collection_name']

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
        'collection_shortname': collection,
        'collection_version': collection_version,
        'granuleUR': filename,
        'ingest_time': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
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

    csv_resource = resources.files("hydrocron.db").joinpath("benchmarking_data_reaches.csv")
    with resources.as_file(csv_resource) as csv:
        csv_file = pd.read_csv(csv, dtype=str)

        logging.info("Read CSV")

        csv_file = csv_file.astype(str)

        filename_attrs = {
            'cycle_id': '000',
            'pass_id': '000',
            'continent_id': 'XX',
            'range_end_time': '2024-12-31T23:59:00Z',
            'crid': 'TEST',
            'collection_shortname': constants.TABLE_COLLECTION_INFO[0]['collection_name']
            }

        items = assemble_attributes(csv_file, filename_attrs)

        count = str(len(items))
        logging.info("Benchmarking items: %s", count)

    return items
