"""
Hydrocron API timeseries controller
"""
# pylint: disable=R0801
# pylint: disable=C0103
import datetime
import json
import logging
import time

import pandas as pd
import geopandas as gpd
from shapely.wkt import loads

from hydrocron.api.data_access.db import DynamoDataRepository
from hydrocron.utils import connection
from hydrocron.utils import constants

logger = logging.getLogger()


class RequestError(Exception):
    """
    Exception thrown if there is an error encoutered with request
    """


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
    elif len(results) > 5750000:
        data['http_code'] = '413 Payload Too Large'
        data['error_message'] = f'413: Query exceeds 6MB with {len(results)} hits'
    else:
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
    :type fields: dict

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
    :type fields: dict

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


def validate_parameters(feature, feature_id, start_time, end_time, output, fields):
    """
    Determine if all parameters are present and in the correct format. Return 400
    Bad Request if any errors are found alongside 0 hits.

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

    :rtype: dict, integer
    """

    data = {'http_code': '200 OK'}
    if feature not in ('Node', 'Reach'):
        data['http_code'] = '400 Bad Request'
        data['error_message'] = f'400: feature parameter should be Reach or Node, not: {feature}'

    elif not feature_id.isdigit():
        data['http_code'] = '400 Bad Request'
        data['error_message'] = f'400: feature_id cannot contain letters: {feature_id}'

    elif not is_date_valid(start_time) or not is_date_valid(end_time):
        data['http_code'] = '400 Bad Request'
        data['error_message'] = '400: start_time and end_time parameters must conform to format: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS-00:00'

    elif output not in ('csv', 'geojson'):
        data['http_code'] = '400 Bad Request'
        data['error_message'] = f'400: output parameter should be csv or geojson, not: {output}'

    elif not is_fields_valid(feature, fields):
        data['http_code'] = '400 Bad Request'
        data['error_message'] = '400: fields parameter should contain valid SWOT fields'

    return data, 0


def is_date_valid(query_date):
    """
    Check if the query date conforms to the correct format.

    :param start_time: Start or end time of the timeseries
    :type start_time: str

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

    :param fields: List of requested columns
    :type fields: dict

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


def lambda_handler(event, context):  # noqa: E501 # pylint: disable=W0613
    """
    This function queries the database for relevant results
    """

    start = time.time()
    print(f'Event - {event}')

    results = {'http_code': '200 OK'}

    try:
        if event['body'] == {} and 'Elastic-Heartbeat' in event['headers']['User-Agent']:
            return {}
        print(f'user_ip: {event["headers"]["X-Forwarded-For"].split(",")[0]}')
    except KeyError as e:
        print(f'Error encountered with headers: {e}')
        raise RequestError('400: Issue encountered with request headers') from e

    try:
        feature = event['body']['feature']
        feature_id = event['body']['feature_id']
        start_time = event['body']['start_time']
        end_time = event['body']['end_time']
        output = event['body']['output']
        fields = event['body']['fields']
        results, hits = validate_parameters(feature, feature_id, start_time, end_time, output, fields)
    except KeyError as e:
        missing_parameter = str(e).rsplit(' ', maxsplit=1)[-1]
        results['http_code'] = '400 Bad Request'
        results['error_message'] = f'400: This required parameter is missing: {missing_parameter}'
        hits = 0

    if results['http_code'] == '200 OK':
        start_time, end_time = sanitize_time(start_time, end_time)
        results, hits = timeseries_get(feature, feature_id, start_time, end_time, output, fields)

    end = time.time()
    elapsed = round((end - start) * 1000, 3)

    data = {'status': results['http_code'], 'time': elapsed, 'hits': hits, 'results': {'csv': "", 'geojson': {}}}
    if results['http_code'] == '200 OK':
        data['results'][event['body']['output']] = results['response']
    else:
        raise RequestError(results['error_message'])

    return data
