"""
Hydrocron API timeseries controller
"""
# pylint: disable=R0801
# pylint: disable=C0103
import datetime
import logging
import time
from hydrocron.api import hydrocron

from hydrocron.utils import constants

logger = logging.getLogger()


def timeseries_get(feature, feature_id, start_time, end_time, output, fields):  # noqa: E501
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
    :type fields: dict

    :rtype: Dict, integer
    """

    data = {}
    hits = 0

    if feature.lower() == 'reach':
        results = hydrocron.data_repository.get_reach_series_by_feature_id(feature_id, start_time, end_time)
    elif feature.lower() == 'node':
        results = hydrocron.data_repository.get_node_series_by_feature_id(feature_id, start_time, end_time)
    else:
        return data, hits

    if output == 'geojson':
        data, hits = format_json(feature.lower(), results, feature_id, fields)
    if output == 'csv':
        data, hits = format_csv(feature.lower(), results, feature_id, fields)

    return data, hits


def format_json(feature_lower, results, feature_id, fields):  # noqa: E501 # pylint: disable=W0613,R0912
    """ Format the results to the file format that the user selects (geojson)

    :param feature_lower: Lowercase version of the type of feature
    :type feature_lower: str
    :param results: We pass the result of the query
    :type results: dict
    :param feature_id: ID of the requested feature
    :type feature_id: str
    :param fields: List of requested columns
    :type fields: dict

    :rtype: dict, integer
    """

    results = results['Items']

    data = {}
    i = 0

    data['error'] = '200 OK'
    if results is None:
        data['error'] = f'404: Results with the specified Feature ID {feature_id} were not found.'
    elif len(results) > 5750000:
        data['error'] = f'413: Query exceeds 6MB with {len(results)} hits.'
    else:
        data['response'] = {}
        data['response']['type'] = "FeatureCollection"
        data['response']['features'] = []
        fields_set = fields.split(",")
        for t in results:
            feature = {'properties': {}, 'geometry': {}, 'type': "Feature"}
            columns = []
            if feature_lower == 'reach':
                columns = constants.REACH_ALL_COLUMNS
            if feature_lower == 'node':
                columns = constants.NODE_ALL_COLUMNS
            for j in fields_set:
                if j in columns:
                    if j == 'geometry':
                        feature['geometry']['coordinates'] = []
                        feature_type = ''
                        geometry = ''
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
                    else:
                        feature['properties'][j] = t[j]
            data['response']['features'].append(feature)
            i += 1
    return data, i


def format_csv(feature_lower, results, feature_id, fields):  # noqa: E501 # pylint: disable=W0613
    """ Format the results to the file format that the user selects (csv)

    :param feature_lower: Lowercase version of the type of feature
    :type feature_lower: str
    :param results: We pass the result of the query
    :type results: dict
    :param feature_id: ID of the requested feature
    :type feature_id: str
    :param fields: List of requested columns
    :type fields: dict

    :rtype: dict, integer
    """

    results = results['Items']

    data = {}
    i = 0
    csv = fields + '\n'

    data['error'] = '200 OK'
    if results is None:
        data['error'] = f'404: Results with the specified Feature ID {feature_id} were not found.'
    elif len(results) > 5750000:
        data['error'] = f'413: Query exceeds 6MB with {len(results)} hits.'
    else:
        data['response'] = ""
        fields_set = fields.split(",")
        for t in results:
            columns = []
            if feature_lower == 'reach':
                columns = constants.REACH_ALL_COLUMNS
            if feature_lower == 'node':
                columns = constants.NODE_ALL_COLUMNS
            for j in fields_set:
                if j in columns:
                    if j == 'geometry':
                        csv += t['geometry'].replace('; ', ', ')
                    else:
                        csv += t[j]
                    if j != fields_set[-1]:
                        csv += ','
            csv += '\n'
            i += 1
        data['response'] = csv
    return data, i


def validate_parameters(feature, feature_id, start_time, end_time, output, fields):
    """
    Determine if all parameters are present and in the correct format. Return 400
    Bad Request if any errors are found alongside 0 hits.
    """

    data = {'error': '200 OK'}
    if feature not in ('Node', 'Reach'):
        data['error'] = f'400: feature parameter should be Reach or Node, not: {feature}'

    elif not feature_id.isdigit():
        data['error'] = f'400: feature_id cannot contain letters: {feature_id}'

    elif not is_date_valid(start_time) or not is_date_valid(end_time):
        data['error'] = '400: start_time and end_time parameters must conform to format: YYYY-MM-DDTHH:MM:SS+00:00'

    elif output not in ('csv', 'geojson'):
        data['error'] = f'400: output parameter should be csv or geojson, not: {output}'

    elif not is_fields_valid(feature, fields):
        data['error'] = '400: fields parameter should contain valid SWOT fields'

    return data, 0


def is_date_valid(query_date):
    """
    Check if the query date conforms to the correct format.
    """

    try:
        datetime.datetime.strptime(query_date, "%Y-%m-%dT%H:%M:%S%z")
        return True
    except ValueError:
        return False


def is_fields_valid(feature, fields):
    """
    Check if fields are present in either the reach or node list of columns
    """

    fields = fields.split(',')
    if feature == 'Reach':
        columns = constants.REACH_ALL_COLUMNS
    elif feature == 'Node':
        columns = constants.NODE_ALL_COLUMNS
    else:
        columns = []
    return all(field in columns for field in fields)


def sanitize_time(start_time, end_time):
    """
    Return formatted string to handle cases where request includes non-padded numbers
    """

    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%dT%H:%M:%S%z")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%dT%H:%M:%S%z")
    return start_time, end_time


def lambda_handler(event, context):  # noqa: E501 # pylint: disable=W0613
    """
    This function queries the database for relevant results
    """

    start = time.time()
    print(f"Event - {event}")

    results = {}
    try:
        feature = event['body']['feature']
        feature_id = event['body']['feature_id']
        start_time = event['body']['start_time']
        end_time = event['body']['end_time']
        output = event['body']['output']
        fields = event['body']['fields']

        results, hits = validate_parameters(feature, feature_id, start_time, end_time, output, fields)

        if results['error'] == '200 OK':
            start_time, end_time = sanitize_time(start_time, end_time)
            results, hits = timeseries_get(feature, feature_id, start_time, end_time, output, fields)

    except KeyError as e:
        missing_parameter = str(e).rsplit(' ', maxsplit=1)[-1]
        results['error'] = f'400: This required parameter is missing: {missing_parameter}'
        hits = 0

    end = time.time()
    elapsed = round((end - start) * 1000, 3)

    data = {'status': results['error'], 'time': elapsed, 'hits': hits, 'results': {'csv': "", 'geojson': {}}}
    if results['error'] == '200 OK':
        data['results'][event['body']['output']] = results['response']

    return data
