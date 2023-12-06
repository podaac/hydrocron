"""
Hydrocron API timeseries controller
"""
# pylint: disable=R0801
# pylint: disable=C0103
import logging
import time
from typing import Generator
from hydrocron.api import hydrocron

from hydrocron.utils import constants

logger = logging.getLogger()


def gettimeseries_get(feature, feature_id, start_time, end_time, output, fields):  # noqa: E501
    """Get Timeseries for a particular Reach, Node, or LakeID

    Get Timeseries for a particular Reach, Node, or LakeID # noqa: E501

    :param feature: Data requested for Reach or Node or Lake
    :type feature: str
    :param feature_id: ID of the feature to retrieve
    :type feature_id: str
    :param start_time: Start time of the timeseries
    :type start_time: str
    :param end_time: End time of the timeseries
    :type end_time: str
    :param output: Format of the data returned
    :type output: str
    :param fields: List of requested columns
    :type output: str

    :rtype: None
    """

    if feature.lower() == 'reach':
        results = hydrocron.data_repository.get_reach_series_by_feature_id(feature_id, start_time, end_time)
    elif feature.lower() == 'node':
        results = hydrocron.data_repository.get_node_series_by_feature_id(feature_id, start_time, end_time)
    else:
        return {}

    data = ""
    if output == 'geojson':
        data, hits = format_json(feature.lower(), results, feature_id, fields)
    if output == 'csv':
        data, hits = format_csv(feature.lower(), results, feature_id, fields)

    return data, hits


def format_json(feature_lower, results: Generator, feature_id, fields):  # noqa: E501 # pylint: disable=W0613
    """

    Parameters
    ----------
    feature_lower
    results
    swot_id
    fields

    Returns
    -------

    """
    # Fetch all results
    results = results['Items']

    data = {}

    if results is None:
        data['error'] = f"404: Results with the specified Feature ID {feature_id} were not found."
    elif len(results) > 5750000:
        data['error'] = f'413: Query exceeds 6MB with {len(results)} hits.'

    else:
        data['type'] = "FeatureCollection"
        data['features'] = []
        i = 0
        fields_set = fields.split(",")

        # st = float(time.mktime(start_time.timetuple()) - 946710000)
        # et = float(time.mktime(end_time.timetuple()) - 946710000)
        # TODO: process type of feature_id (i.e. reach_id or node_id)

        for t in results:
            # TODO: Coordinate to filter in the database instance:
            # if t['reach_id'] == feature_id and t['time'] > start_time and t['time'] < end_time and t['time'] != '-999999999999':  # and (t['width'] != '-999999999999')):
            # if t['reach_id'] == feature_id and t[constants.FIELDNAME_TIME] != '-999999999999':  # and (t['width'] != '-999999999999')):
            feature = {'properties': {}, 'geometry': {}, 'type': "Feature"}
            if 'geometry' in fields_set:
                feature['geometry']['coordinates'] = []
                feature_type = ''
                if 'POINT' in t['geometry']:
                    geometry = t['geometry'].replace('POINT (', '').replace(')', '')
                    geometry = geometry.replace('"', '')
                    geometry = geometry.replace("'", "")
                    feature_type = 'Point'
                if 'LINESTRING' in t['geometry']:
                    geometry = t['geometry'].replace('LINESTRING (', '').replace(')', '')
                    geometry = geometry.replace('"', '')
                    geometry = geometry.replace("'", "")
                    feature_type = 'LineString'
                feature['geometry']['type'] = feature_type
                for p in geometry.split(", "):
                    (x, y) = p.split(" ")
                    if feature_type == 'LineString':
                        feature['geometry']['coordinates'].append([float(x), float(y)])
                    if feature_type == 'Point':
                        feature['geometry']['coordinates'] = [float(x), float(y)]
            columns = []
            if feature_lower == 'reach':
                columns = constants.REACH_ALL_COLUMNS
            if feature_lower == 'node':
                columns = constants.NODE_ALL_COLUMNS
            columns.append('reach_id')
            columns.append('time')
            columns.append('time_str')
            for j in fields_set:
                if j in columns:
                    feature['properties'][j] = t[j]
            data['features'].append(feature)
            i += 1

    return data, i


def format_csv(feature_lower, results: Generator, feature_id, fields):  # noqa: E501 # pylint: disable=W0613
    """

    Parameters
    ----------
    feature_lower
    results
    feature_id
    fields

    Returns
    -------

    """
    # Fetch all results
    results = results['Items']

    data = {}

    if results is None:
        data['error'] = f"404: Results with the specified Feature ID {feature_id} were not found."
    elif len(results) > 5750000:
        data['error'] = f'413: Query exceeds 6MB with {len(results)} hits.'

    else:
        data['type'] = "FeatureCollection"
        data['features'] = []
        i = 0
        csv = fields + '\n'
        fields_set = fields.split(",")
        for t in results:
            i += 1
            if 'geometry' in fields_set:
                csv += t['geometry'].replace('; ', ', ')
                csv += ','
            else:
                columns = []
                if feature_lower == 'reach':
                    columns = constants.REACH_ALL_COLUMNS
                if feature_lower == 'node':
                    columns = constants.NODE_ALL_COLUMNS
                columns.append('reach_id')
                columns.append('time')
                columns.append('time_str')
                for j in fields_set:
                    if j in columns:
                        csv += t[j]
                        csv += ','
            csv += '\n'
    return csv, i


def lambda_handler(event, context):  # noqa: E501 # pylint: disable=W0613
    """
    This function queries the database for relevant results
    """

    feature = event['body']['feature']
    feature_id = event['body']['reach_id']
    start_time = event['body']['start_time']
    end_time = event['body']['end_time']
    output = event['body']['output']
    fields = event['body']['fields']

    start = time.time()
    results, hits = gettimeseries_get(feature, feature_id, start_time, end_time, output, fields)
    end = time.time()
    elapsed_time = round((end - start) * 1000, 3)
    data = {'status': "200 OK", 'time': elapsed_time, 'hits': hits, 'results': {'csv': "", 'geojson': {}}}
    data['results'][event['body']['output']] = results

    return data
