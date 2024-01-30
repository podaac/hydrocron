"""
Hydrocron API timeseries controller
"""
# pylint: disable=R0801
# pylint: disable=C0103
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
        data['type'] = "FeatureCollection"
        data['features'] = []
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
            data['features'].append(feature)
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

    if results is None:
        data['error'] = f'404: Results with the specified Feature ID {feature_id} were not found.'
    elif len(results) > 5750000:
        data['error'] = f'413: Query exceeds 6MB with {len(results)} hits.'

    else:
        data['type'] = "FeatureCollection"
        data['features'] = []
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
                    csv += ','
            csv += '\n'
            i += 1
    return csv, i


def lambda_handler(event, context):  # noqa: E501 # pylint: disable=W0613
    """
    This function queries the database for relevant results
    """

    error_code = '200 OK'

    feature = event['body']['feature']
    feature_id = event['body']['feature_id']
    start_time = event['body']['start_time']
    end_time = event['body']['end_time']
    output = event['body']['output']
    fields = event['body']['fields']

    missing_params = []
    if feature == '':
        missing_params.append('Feature')
    if feature_id == '':
        missing_params.append('Feature ID')
    if start_time == '':
        missing_params.append('Start time')
    if end_time == '':
        missing_params.append('End time')
    if output == '':
        missing_params.append('Output')
    if fields == '':
        missing_params.append('Fields')

    if missing_params:
        error_code = f'400: These required parameters are missing: {missing_params}'

    start = time.time()
    results, hits = timeseries_get(feature, feature_id, start_time, end_time, output, fields)
    if isinstance(results, dict) and results['error'] != '':
        error_code = results['error']

    end = time.time()
    elapsed = round((end - start) * 1000, 3)
    print({"start": start, "end": end, "elapsed": elapsed})

    data = {'status': error_code, 'time': elapsed, 'hits': hits, 'results': {'csv': "", 'geojson': {}}}
    data['results'][event['body']['output']] = results

    return data
