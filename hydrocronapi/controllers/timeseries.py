"""
Hydrocron API timeseries controller
"""
# pylint: disable=R0801
# pylint: disable=C0103
import logging
import time
from datetime import datetime
from typing import Generator
from hydrocronapi import hydrocron

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
    :param cycleavg: Perform cycle average on the time series
    :type cycleavg: bool
    :param output: Format of the data returned
    :type output: str

    :rtype: None
    """

    start_time = start_time.replace("T", " ")[0:19]
    end_time = end_time.replace("T", " ")[0:19]
    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    start = time.time()
    if feature.lower() == 'reach':
        results = hydrocron.data_repository.get_reach_series_by_feature_id(feature_id, start_time, end_time)
    elif feature.lower() == 'node':
        results = hydrocron.data_repository.get_node_series_by_feature_id(feature_id, start_time, end_time)
    else:
        return {}
    end = time.time()

    data = ""
    if output == 'geojson':
        data = format_json(results, feature_id, start_time, end_time, True, round((end - start) * 1000, 3))
    if output == 'csv':
        data = format_csv(results, feature_id, True, round((end - start) * 1000, 3), fields)

    return data


def format_json(results: Generator, feature_id, start_time, end_time, exact, dataTime):  # noqa: E501 # pylint: disable=W0613
    """

    Parameters
    ----------
    results
    swot_id
    exact
    time

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
        data['status'] = "200 OK"
        data['time'] = str(dataTime) + " ms."
        # data['search on'] = {"feature_id": feature_id}
        data['type'] = "FeatureCollection"
        data['features'] = []
        i = 0
        # st = float(time.mktime(start_time.timetuple()) - 946710000)
        # et = float(time.mktime(end_time.timetuple()) - 946710000)
        # TODO: process type of feature_id (i.e. reach_id or node_id)

        for t in results:
            # TODO: Coordinate to filter in the database instance:
            # if t['reach_id'] == feature_id and t['time'] > start_time and t['time'] < end_time and t['time'] != '-999999999999':  # and (t['width'] != '-999999999999')):
            if t['reach_id'] == feature_id and t['time'] != '-999999999999':  # and (t['width'] != '-999999999999')):
                feature = {'properties': {}, 'geometry': {}, 'type': "Feature"}
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
                i += 1
                feature['properties']['time'] = datetime.fromtimestamp(float(t['time']) + 946710000).strftime(
                    "%Y-%m-%d %H:%M:%S")
                feature['properties']['reach_id'] = float(t['reach_id'])
                feature['properties']['wse'] = float(t['wse'])
                feature['properties']['slope'] = float(t['slope'])
                data['features'].append(feature)

        data['hits'] = i

    return data


def format_csv(results: Generator, feature_id, exact, dataTime, fields):  # noqa: E501 # pylint: disable=W0613
    """

    Parameters
    ----------
    results
    feature_id
    exact
    time

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
        # csv = "feature_id, time_str, wse, geometry\n"
        csv = fields + '\n'
        fields_set = fields.split(", ")
        for t in results:
            if t['time'] != '-999999999999':  # and (t['width'] != '-999999999999')):
                if 'reach_id' in fields_set:
                    csv += t['reach_id']
                    csv += ','
                if 'time_str' in fields_set:
                    csv += t['time_str']
                    csv += ','
                if 'wse' in fields_set:
                    csv += str(t['wse'])
                    csv += ','
                if 'geometry' in fields_set:
                    csv += t['geometry'].replace('; ', ', ')
                    csv += ','
                csv += '\n'

    return csv


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

    results = gettimeseries_get(feature, feature_id, start_time, end_time, output, fields)

    data = {}

    status = "200 OK"

    data['status'] = status
    data['time'] = str(10) + " ms."
    data['hits'] = 10

    data['search on'] = {
        "parameter": "identifier",
        "exact": "exact",
        "page_number": 0,
        "page_size": 20
    }

    data['results'] = results

    return data
