"""
Hydrocron API timeseries controller
"""
# pylint: disable=R0801
# pylint: disable=C0103
import datetime
import json
import logging
import sys
import time

from accept_types import get_best_match
import pandas as pd
import geopandas as gpd
from shapely.wkt import loads

from hydrocron.api.data_access.db import DynamoDataRepository
from hydrocron.utils import connection
from hydrocron.utils import constants


logging.getLogger().setLevel(logging.INFO)


ACCEPT_TYPES = ['application/json', 'text/csv', 'application/geo+json']


class RequestError(Exception):
    """
    Exception thrown if there is an error encoutered with request
    """


def get_request_headers(event):
    """Return request headers from event object.

    :param event: Request data dictionary
    :type event: dict

    :rtype: dict
    """

    headers = {}
    try:
        headers['user_agent'] = event['headers']['User-Agent']
        headers['user_ip'] = event['headers']['X-Forwarded-For'].split(',')[0]
        headers['accept'] = '*/*' if 'Accept' not in event['headers'].keys() else event['headers']['Accept']
    except KeyError as e:
        logging.error('Error encountered with headers: %s', e)
        raise RequestError(f'400: Issue encountered with request header: {e}') from e
    return headers


def get_request_parameters(event, accept_header):
    """Return request parameters from event object.

    :param event: Request data dictionary
    :type event: dict

    :rtype: dict
    """

    parameters = {}
    try:
        parameters['feature'] = event['body']['feature']
        parameters['feature_id'] = event['body']['feature_id']
        parameters['start_time'] = event['body']['start_time']
        parameters['end_time'] = event['body']['end_time']
        parameters['output'] = 'default' if 'output' not in event['body'].keys() else event['body']['output']
        parameters['fields'] = event['body']['fields']
        parameters['compact'] = 'false' if 'compact' not in event['body'].keys() else event['body']['compact']
        if accept_header == 'application/geo+json':   # Default is different for geo+json
            parameters['compact'] = 'true' if 'compact' not in event['body'].keys() else event['body']['compact']
    except KeyError as e:
        logging.error('Error encountered with request parameters: %s', e)
        raise RequestError(f'400: This required parameter is missing: {e}') from e

    error_message = validate_parameters(parameters)
    if error_message:
        raise RequestError(error_message)

    return parameters


def get_return_type(accept_header, output):
    """Determine return type and output value requested by user from Accept header

    :param accept_header: Accept request header
    :type accept_header: str

    :param output: Output type requested by user
    :type output: str

    :rtype: str, str
    """

    return_type = get_best_match(accept_header, ACCEPT_TYPES)

    if return_type is None:
        raise RequestError(f'415: Unsupported media type in Accept request header: {accept_header}. Hydrocron '
                           f'only supports the following media types: {ACCEPT_TYPES}')

    if output != 'default':
        if return_type != 'application/json':
            logging.error('Error encountered with request Accept header: %s and output: %s', return_type, output)
            raise RequestError(f'400: Invalid combination of Accept header ({accept_header}) and '
                               + f'output request parameter ({output}). Remove output request parameter when '
                               + 'requesting application/geo+json or text/csv')

    else:
        if return_type in ('application/json', 'application/geo+json'):
            output = 'geojson'
        elif return_type == 'text/csv':
            output = 'csv'

    return return_type, output


def validate_parameters(parameters):
    """
    Determine if all parameters are present and in the correct format. Return 400
    Bad Request if any errors are found alongside 0 hits.

    :param parameters: Dictionary of query parameters
    :type parameters: dict

    :rtype: str
    """

    error_message = ''

    if parameters['feature'] not in ('Node', 'Reach'):
        error_message = f'400: feature parameter should be Reach or Node, not: {parameters["feature"]}'

    elif not parameters['feature_id'].isdigit():
        error_message = f'400: feature_id cannot contain letters: {parameters["feature_id"]}'

    elif not is_date_valid(parameters['start_time']) or not is_date_valid(parameters['end_time']):
        error_message = ('400: start_time and end_time parameters must conform '
                         'to format: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS-00:00')

    elif parameters['output'] not in ('csv', 'geojson', 'default'):
        error_message = f'400: output parameter should be csv or geojson, not: {parameters["output"]}'

    elif not is_fields_valid(parameters['feature'], parameters['fields']):
        error_message = '400: fields parameter should contain valid SWOT fields'

    elif parameters['compact'] not in ('true', 'false'):
        error_message = f'400: compact parameter should be true or false, not {parameters["compact"]}'

    else:
        parameters['start_time'], parameters['end_time'] = sanitize_time(parameters['start_time'], parameters['end_time'])

    return error_message


def is_date_valid(query_date):
    """
    Check if the query date conforms to the correct format.

    :param query_date: Start or end time of the timeseries
    :type query_date: str

    :rtype: bool
    """

    try:
        datetime.datetime.strptime(query_date, "%Y-%m-%dT%H:%M:%S%z")
        return True
    except ValueError:
        return False


def is_fields_valid(feature, fields):
    """
    Check if fields are present in either the reach or node list of columns

    :param feature: The type of feature, either 'Reach' or 'Node'
    :type feature: str

    :param fields: List of requested columns
    :type fields: str

    :rtype: bool
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

    :param start_time: Start time of the timeseries
    :type start_time: str
    :param end_time: End time of the timeseries
    :type end_time: str

    :rtype: str, str
    """

    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%dT%H:%M:%S%z")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%dT%H:%M:%S%z")
    return start_time, end_time


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
    :type fields: str

    :rtype: Dict, integer
    """

    results = {'Items': []}
    data = {}
    hits = 0

    data_repository = DynamoDataRepository(connection.dynamodb_resource)
    if feature.lower() == 'reach':
        results = data_repository.get_reach_series_by_feature_id(feature_id, start_time, end_time)
    if feature.lower() == 'node':
        results = data_repository.get_node_series_by_feature_id(feature_id, start_time, end_time)

    if len(results['Items']) == 0:
        data['http_code'] = '400 Bad Request'
        data['error_message'] = f'400: Results with the specified Feature ID {feature_id} were not found'
    elif sys.getsizeof(results) > 6291456:
        data['http_code'] = '413 Payload Too Large'
        data['error_message'] = f'413: Query exceeds 6MB with {sys.getsizeof(results)} hits'
    else:
        logging.info('query_size: %s', str(sys.getsizeof(results)))
        gdf = convert_to_df(results['Items'])
        if output == 'geojson':
            data, hits = format_json(gdf, fields)
        if output == 'csv':
            data, hits = format_csv(gdf, fields)

    return data, hits


def convert_to_df(items) -> gpd.GeoDataFrame:
    """Convert reach-level results for GeoPandas Dataframe.

    :param items Dictionary of query results
    :type items: dict

    :rtype: gpd.GeoDataFrame
    """

    df = pd.DataFrame.from_records(items)
    df['geometry'] = df['geometry'].apply(loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    return gdf


def format_json(gdf, fields):  # noqa: E501 # pylint: disable=W0613,R0912
    """ Format the results to the file format that the user selects (geojson)

    :param gdf: DataFrame of results from query
    :type gdf: gpd.GeoDataFrame
    :param fields: List of requested columns
    :type fields: str

    :rtype: dict, integer
    """

    columns = fields.split(',')
    columns = add_units(gdf, columns)
    if 'geometry' not in fields:
        columns.append('geometry')   # Add geometry to convert to geoJSON
    gdf = gdf[columns]
    gdf_json = json.loads(gdf.to_json())

    data = {
        'http_code': '200 OK',
        'response': gdf_json
    }
    hits = gdf.shape[0]

    return data, hits


def format_csv(gdf, fields):  # noqa: E501 # pylint: disable=W0613
    """ Format the results to the file format that the user selects (csv)

    :param gdf: DataFrame of results from query
    :type gdf: gpd.GeoDataFrame
    :param fields: List of requested columns
    :type fields: str

    :rtype: dict, integer
    """

    columns = fields.split(',')
    columns = add_units(gdf, columns)
    gdf = gdf[columns]
    gdf_csv = gdf.to_csv(index=False)

    data = {
        'http_code': '200 OK',
        'response': gdf_csv
    }
    hits = gdf.shape[0]

    return data, hits


def add_units(gdf, columns):
    """Add units to list of columns to return in response

    :param gdf: DataFrame of results from query
    :type gdf: gpd.GeoDataFrame
    :param columns: List of columns to return in response
    :type columns: list of str
    """

    gdf_columns = gdf.columns.values.tolist()
    unit_columns = [f"{column}_units" for column in columns if f"{column}_units" in gdf_columns]
    return columns + unit_columns


def get_response(results, hits, elapsed, return_type, output, compact):
    """Create and return HTTP response based on results.

    :param results: Dictionary of SWOT timeseries results
    :type results: dict
    :param hits: Number of results returned from query
    :type hits: int
    :param elapsed: Number of seconds it took to query for results
    :type elapsed: float
    :param return_type: Accept request header
    :type return_type: str
    :param output: Output to return in request
    :type output: str
    :param compact: Whether to return compact GeoJSON response
    :type compact: str

    rtype: dict
    """

    if results['http_code'] == '200 OK':

        if return_type in ('text/csv', 'application/geo+json'):
            if compact == 'true' and return_type == 'application/geo+json':
                data = compact_results(results['response'])
            else:
                data = results['response']

        else:  # 'application/json'
            data = {
                'status': results['http_code'],
                'time': elapsed,
                'hits': hits,
                'results': {
                    'csv': '',
                    'geojson': {}
                    }
                }
            if output == 'geojson' and compact == 'true':
                results['response'] = compact_results(results['response'])
            data['results'][output] = results['response']

    else:
        logging.error(results)
        raise RequestError(results['error_message'])

    return data


def compact_results(results):
    """Compact GeoJSON results to return a properties object with aggregated 
    time series data.

    :param results: Dictionary of SWOT timeseries results
    :type results: dict

    rtype: dict
    """

    response = {
        'type': 'FeatureCollection',
        'features': [
            {
                'id': '0',
                'type': 'Feature',
                'properties': {},
                'geometry': results['features'][0]['geometry']   # Grab first geometry
            }
        ]
    }

    fields = list(results['features'][0]['properties'].keys())
    for field in fields:
        response['features'][0]['properties'][field] = [ feature['properties'][field] for feature in results['features'] ]

    return response


def lambda_handler(event, context):  # noqa: E501 # pylint: disable=W0613
    """
    This function queries the database for relevant results
    """

    start = time.time()

    logging.info('headers: %s', json.dumps(event['headers']))
    logging.info('request: %s', json.dumps(event['body']))

    try:
        headers = get_request_headers(event)
        # The cloud metrics Elastic Heartbeat is a Health check that occurs
        # every 15 seconds. The following statement checks if the current request is an Elastic Heartbeat
        # and if it is, simply return success immediately instead of further processing the request
        # More background: https://github.com/podaac/hydrocron/issues/89
        if event['body'] == {} and 'Elastic-Heartbeat' in headers['user_agent']:
            return {}
        logging.info('user_ip: %s', headers['user_ip'])
        parameters = get_request_parameters(event, headers['accept'])
        return_type, output = get_return_type(headers['accept'], parameters['output'])
    except RequestError as e:
        raise e

    results, hits = timeseries_get(
        parameters['feature'],
        parameters['feature_id'],
        parameters['start_time'],
        parameters['end_time'],
        output,
        parameters['fields']
    )

    end = time.time()
    elapsed = round((end - start) * 1000, 3)

    try:
        data = get_response(results, hits, elapsed, return_type, output, parameters['compact'])
    except RequestError as e:
        raise e
    logging.info('response: %s', json.dumps(data))
    logging.info('response_size: %s', str(sys.getsizeof(data)))

    return data
