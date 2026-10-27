"""
Hydrocron API timeseries controller
"""
# pylint: disable=R0801
# pylint: disable=C0103
import datetime
import json
import logging
import os
import re
import time
from concurrent.futures import wait

from accept_types import get_best_match
import pandas as pd
import geopandas as gpd
from shapely.wkt import loads

from hydrocron.api.data_access.db import DynamoDataRepository, ItemLimitExceeded, NODE_QUERY_POOL
from hydrocron.utils import connection
from hydrocron.utils import constants


logging.getLogger().setLevel(logging.INFO)


ACCEPT_TYPES = ['application/json', 'text/csv', 'application/geo+json']
# Lambda's synchronous response payload limit (6 MB; API Gateway REST allows 10 MB); larger responses return a 413.
MAX_RESPONSE_SIZE_BYTES = 6 * 1024 * 1024
# Columns added first to every row of a reach + node (node_fields) response.
REACH_AND_NODE_ID_COLUMNS = ['feature_type', 'reach_id', 'node_id']
DEFAULT_RIVER_COLLECTION = os.environ['DEFAULT_RIVER_COLLECTION']
DEFAULT_LAKE_COLLECTION = os.environ['DEFAULT_LAKE_COLLECTION']
DEFAULT_COLLECTION_VERSION = os.environ['DEFAULT_COLLECTION_VERSION']


class RequestError(Exception):
    """
    Exception thrown if there is an error encoutered with request
    """


class DataIntegrityError(Exception):
    """
    Exception thrown if stored data is inconsistent (e.g. a node's reach_id differs from the reach it was found for).
    Not a RequestError: its message doesn't start with an HTTP code, so API Gateway returns 500.
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
        parameters['filename'] = '' if 'filename' not in event['body'].keys() else event['body']['filename']
        parameters['collection_name'] = get_collection_name(event)
    except KeyError as e:
        raise RequestError(f'400: This required parameter is missing: {e}') from e

    if not parameters['collection_name']:
        raise RequestError(f'400: feature parameter should be Reach, Node, or PriorLake, not: {parameters["feature"]}')

    # remove spaces from fields list
    parameters['fields'] = [field.strip() for field in parameters['fields'].split(',') if field.strip()]
    parameters['fields'] = ','.join(parameters['fields'])

    # node_fields (optional): its presence requests the reach's node data too
    parameters['node_fields'] = event['body'].get('node_fields')
    if parameters['node_fields'] is not None:
        parameters['node_fields'] = ','.join(field.strip() for field in parameters['node_fields'].split(',') if field.strip())

    error_message = validate_parameters(parameters)
    if error_message:
        raise RequestError(error_message)

    return parameters


def get_collection_name(event):
    """Return request parameters from event object.

    :param event: Request data dictionary
    :type event: dict

    :rtype: str
    """

    feature = event['body']['feature'].lower()
    if 'collection_name' not in event['body'].keys():
        if feature in ('reach', 'node'):
            collection_name = f'{DEFAULT_RIVER_COLLECTION}_{DEFAULT_COLLECTION_VERSION}'
        elif feature == 'priorlake':
            collection_name = f'{DEFAULT_LAKE_COLLECTION}_{DEFAULT_COLLECTION_VERSION}'
        else:
            collection_name = ''
    else:
        collection_name = event['body']['collection_name']
    return collection_name


def get_return_type(accept_header, output):
    """Determine return type and output value requested by user from Accept header

    :param accept_header: Accept request header
    :type accept_header: str

    :param output: Output type requested by user: 'default', 'csv', 'geojson', or 'csv_file'.
        'csv_file' is validated like 'csv' (a JSON Accept is required) and then mapped to 'csv'.
    :type output: str

    :rtype: str, str
    """

    return_type = get_best_match(accept_header, ACCEPT_TYPES)

    if return_type is None:
        raise RequestError(f'415: Unsupported media type in Accept request header: {accept_header}. Hydrocron '
                           f'only supports the following media types: {ACCEPT_TYPES}')

    if output != 'default':
        if return_type != 'application/json':
            raise RequestError(f'400: Invalid combination of Accept header ({accept_header}) and '
                               + f'output request parameter ({output}). Remove output request parameter when '
                               + 'requesting application/geo+json or text/csv')

    else:
        if return_type in ('application/json', 'application/geo+json'):
            output = 'geojson'
        elif return_type == 'text/csv':
            output = 'csv'

    # csv_file validates like output=csv above (a JSON Accept is required), then maps to csv for
    # downstream formatting; the caller detects csv_file separately to wrap the download.
    if output == 'csv_file':
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

    collections_list = []
    for version in constants.CURRENT_VERSION_LIST:
        collections_list.extend([f"{collection}_{version}" for collection in constants.COLLECTIONS_LIST])

    if parameters['collection_name'] not in collections_list:
        error_message = f'400: collection_name parameter should be one of the following: {", ".join(collections_list)}'

    elif parameters['feature'] not in ('Node', 'Reach', 'PriorLake'):
        error_message = f'400: feature parameter should be Reach, Node, or PriorLake, not: {parameters["feature"]}'

    elif not parameters['feature_id'].isdigit():
        error_message = f'400: feature_id cannot contain letters: {parameters["feature_id"]}'

    elif not is_date_valid(parameters['start_time']) or not is_date_valid(parameters['end_time']):
        error_message = ('400: start_time and end_time parameters must conform '
                         'to format: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS-00:00')

    elif parameters['output'] not in ('csv', 'geojson', 'csv_file', 'default'):
        error_message = f'400: output parameter should be csv, geojson, or csv_file, not: {parameters["output"]}'

    elif parameters['feature'] == 'Reach' and parameters['collection_name'].endswith('_D') and \
            any(f in constants.REACH_VERSION_2_0_ONLY_FIELDS for f in parameters['fields'].split(',')):
        error_message = ('400: SOS Discharge fields are not available for the SWOT vD collection at this time. '
                         'If wishing to request SOS Discharge fields corresponding to SWOT v2.0, '
                         'please specify collection_name=SWOT_L2_HR_RiverSP_2.0 in your request.')

    elif not is_fields_valid(parameters['feature'], parameters['fields'], parameters['collection_name']):
        error_message = '400: fields parameter should contain valid SWOT fields'

    elif parameters.get('node_fields') is not None and parameters['feature'] != 'Reach':
        error_message = '400: node_fields parameter is only valid when feature=Reach'

    elif parameters.get('node_fields') is not None and \
            (not parameters['node_fields'] or not is_fields_valid('Node', parameters['node_fields'], parameters['collection_name'])):
        error_message = '400: node_fields parameter should contain valid SWOT node fields'

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


def is_fields_valid(feature, fields, collection_name):
    """
    Check if fields are present in either the reach or node list of columns

    :param feature: The type of feature, either 'Reach', 'Node', or 'PriorLake'
    :type feature: str

    :param fields: List of requested columns
    :type fields: str

    :param collection_name: Name of collection being queried
    :type collection_name: str

    :rtype: bool
    """

    fields_list = fields.split(',')

    # First check if all fields are valid for the feature type
    if feature == 'Reach':
        columns = constants.REACH_ALL_COLUMNS
    elif feature == 'Node':
        columns = constants.NODE_ALL_COLUMNS
    elif feature == 'PriorLake':
        columns = constants.PRIOR_LAKE_ALL_COLUMNS
    else:
        columns = []

    if not all(field in columns for field in fields_list):
        return False

    # For Node feature, check if Version D only fields are being requested with 2.0 collection
    if feature == 'Node' and collection_name.endswith('_2.0'):
        # Check if any requested fields are Version D only
        if any(field in constants.NODE_VERSION_D_ONLY_FIELDS for field in fields_list):
            return False

    # For PriorLake feature, check if Version D only fields are being requested with 2.0 collection
    if feature == 'PriorLake' and collection_name.endswith('_2.0'):
        # Check if any requested fields are Version D only
        if any(field in constants.PRIOR_LAKE_VERSION_D_ONLY_FIELDS for field in fields_list):
            return False

    # For Reach feature, check if 2.0-only fields are being requested with Version D collection
    if feature == 'Reach' and collection_name.endswith('_D'):
        if any(field in constants.REACH_VERSION_2_0_ONLY_FIELDS for field in fields_list):
            return False

    return True


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


def sanitize_filename(filename):
    """Sanitize user-provided filename, keeping only safe characters."""
    # Coerce to str so non-string inputs don't raise.
    sanitized = re.sub(r'[^a-zA-Z0-9_\-.]', '_', str(filename))
    if not sanitized.lower().endswith('.csv'):
        sanitized += '.csv'
    if len(sanitized) > 200:
        sanitized = sanitized[:196] + '.csv'
    return sanitized


def build_default_filename(feature, feature_id, start_time, end_time):
    """Build default download filename from request parameters."""
    start_date = start_time[:10]
    end_date = end_time[:10]
    return f"hydrocron_{feature}_{feature_id}_{start_date}_{end_date}.csv"


def timeseries_get(collection_name, feature, feature_id, start_time, end_time, output, fields,  # pylint: disable=too-many-arguments,too-many-positional-arguments
                   node_fields=None):
    """Get Timeseries for a particular Reach, Node, or LakeID

    Get Timeseries for a particular Reach, Node, or LakeID # noqa: E501

    :param collection_name: Name of collection to query data for
    :type collection_name: str
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
    :param node_fields: List of requested node columns; if set (feature=Reach), the reach's nodes are returned too
    :type node_fields: str

    :rtype: Dict, integer
    """

    if node_fields is not None:
        return timeseries_get_reach_and_nodes(collection_name, feature_id, start_time, end_time, output, fields, node_fields)

    results = {'Items': []}
    data = {}
    hits = 0

    data_repository = DynamoDataRepository(connection.dynamodb_resource)
    try:
        results = data_repository.get_series_by_feature_id(collection_name, feature, feature_id, start_time, end_time)
    except ValueError as e:
        data['http_code'] = '400 Bad Request'
        data['error_message'] = str(e)
        return data, hits

    if len(results['Items']) == 0:
        data['http_code'] = '400 Bad Request'
        data['error_message'] = f'400: Results with the specified Feature ID {feature_id} were not found'
    else:
        gdf = convert_to_df(results['Items'])
        if output == 'geojson':
            data, hits = format_json(gdf, fields)
        if output == 'csv':
            data, hits = format_csv(gdf, fields)

    return data, hits


def timeseries_get_reach_and_nodes(collection_name, reach_id, start_time, end_time, output, fields,  # pylint: disable=too-many-arguments,too-many-positional-arguments
                                   node_fields):
    """Get the time series for a reach and all of its nodes.

    The reach query and the ReachIdIndex lookup run in parallel; node rows are then fetched with
    one projected query per node. Returns a 413 before fetching nodes if the reach has more node
    rows than constants.MAX_REACH_NODE_ITEMS.

    :param collection_name: Name of collection to query data for (reach and node tables of the same version)
    :type collection_name: str
    :param reach_id: ID of the reach to retrieve
    :type reach_id: str
    :param start_time: Start time of the timeseries
    :type start_time: str
    :param end_time: End time of the timeseries
    :type end_time: str
    :param output: Format of the data returned
    :type output: str
    :param fields: List of requested reach columns
    :type fields: str
    :param node_fields: List of requested node columns
    :type node_fields: str

    :rtype: Dict, integer
    """

    data = {}
    hits = 0

    data_repository = DynamoDataRepository(connection.dynamodb_resource, connection.dynamodb_client)
    reach_future = NODE_QUERY_POOL.submit(data_repository.get_series_by_feature_id,
                                          collection_name, 'Reach', reach_id, start_time, end_time)
    try:
        node_ids, node_row_count = data_repository.get_node_ids_by_reach_id(collection_name, reach_id, start_time, end_time,
                                                                            constants.MAX_REACH_NODE_ITEMS)
    except ItemLimitExceeded as e:
        data['http_code'] = '413 Payload Too Large'
        data['error_message'] = (f'413: Reach {reach_id} has more than {e.limit} node rows in the requested time range. '
                                 'Reduce the time range.')
        return data, hits
    finally:
        # Never return with the reach query still running: Lambda freezes leftover threads and resumes them
        # in the next invocation (and the boto3 resource it uses isn't thread-safe).
        wait([reach_future])

    try:
        reach_items = reach_future.result()['Items']
    except ValueError as e:
        data['http_code'] = '400 Bad Request'
        data['error_message'] = str(e)
        return data, hits

    node_items = data_repository.get_node_series(collection_name, node_ids, start_time, end_time, build_node_projection(node_fields))
    logging.info('reach_and_nodes: %s', json.dumps(
        {'reach_id': reach_id, 'reach_rows': len(reach_items), 'nodes': len(node_ids),
         'node_keys': node_row_count, 'node_rows': len(node_items)}))

    for item in node_items:
        if item.get('reach_id') != reach_id:
            logging.error(json.dumps({'error': 'node reach_id mismatch', 'node_id': item.get('node_id'),
                                      'stored_reach_id': item.get('reach_id'), 'requested_reach_id': reach_id}))
            raise DataIntegrityError(f"Data integrity error: node {item.get('node_id')} has reach_id "
                                     f"{item.get('reach_id')}, expected {reach_id}")

    if not reach_items and not node_items:
        data['http_code'] = '400 Bad Request'
        data['error_message'] = f'400: Results with the specified Feature ID {reach_id} were not found'
    else:
        data, hits = format_reach_and_nodes(reach_items, node_items, fields, node_fields, output)

    return data, hits


def build_node_projection(node_fields):
    """Return the node attributes to fetch: requested fields, their units, alias sources, keys and geometry.

    Geometry is always fetched (convert_to_df requires it; a node point is small).

    :param node_fields: List of requested node columns
    :type node_fields: str

    :rtype: list of str
    """

    fields_list = node_fields.split(',')
    attributes = fields_list + ['node_id', 'reach_id', 'range_start_time', 'geometry']
    attributes += [f'{field}_units' for field in fields_list]
    attributes += [constants.FIELD_ALIASES[field] for field in fields_list if field in constants.FIELD_ALIASES]
    return list(dict.fromkeys(attributes))


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


def _fill_missing_columns(gdf, columns):
    """Add missing columns to GeoDataFrame with fill value. Resolves aliases."""
    # First, ensure all non-alias columns exist and are filled (order-independent).
    for col in columns:
        if col == "geometry" or col in constants.FIELD_ALIASES:
            continue
        if col not in gdf.columns:
            gdf[col] = constants.FILL_VALUE
        else:
            gdf[col] = gdf[col].fillna(constants.FILL_VALUE)

    # Second, resolve aliases after sources have been created/filled.
    for alias, source in constants.FIELD_ALIASES.items():
        if alias not in columns:
            continue
        if source in gdf.columns:
            gdf[alias] = gdf[source].fillna(constants.FILL_VALUE)
        else:
            gdf[alias] = constants.FILL_VALUE

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
    gdf = _fill_missing_columns(gdf, columns)
    gdf = gdf[columns]
    # Build the GeoJSON FeatureCollection dict directly; it is serialized once at the response boundary.
    gdf_json = gdf.to_geo_dict()

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
    gdf = _fill_missing_columns(gdf, columns)
    gdf = gdf[columns]
    gdf_csv = gdf.to_csv(index=False)

    data = {
        'http_code': '200 OK',
        'response': gdf_csv
    }
    hits = gdf.shape[0]

    return data, hits


def format_reach_and_nodes(reach_items, node_items, fields, node_fields, output):  # pylint: disable=too-many-locals
    """Format reach rows then node rows into one GeoJSON FeatureCollection or CSV.

    Each feature type is filled for its own fields (real missing -> fill value). CSV: all rows are
    reindexed to one union of columns, so columns that don't apply to a row's feature type are blank.
    GeoJSON: each Feature carries only its own type's columns (no node_id on reaches, no node-only
    fields on reaches, no reach-only fields on nodes). Column order: feature_type, reach_id, node_id,
    requested fields (fields first, then new node_fields), then units.

    :param reach_items: Reach rows
    :type reach_items: list of dict
    :param node_items: Node rows, in node_id then time order
    :type node_items: list of dict
    :param fields: List of requested reach columns
    :type fields: str
    :param node_fields: List of requested node columns
    :type node_fields: str
    :param output: 'geojson' or 'csv'
    :type output: str

    :rtype: dict, integer
    """

    reach_columns = list(dict.fromkeys(fields.split(',')))
    node_columns = list(dict.fromkeys(node_fields.split(',')))
    frames = []
    unit_columns = []
    for feature_type, items, columns in (('Reach', reach_items, reach_columns), ('Node', node_items, node_columns)):
        if not items:
            continue
        gdf = convert_to_df(items)
        ids = {'feature_type': feature_type, 'reach_id': gdf['reach_id']}
        if feature_type == 'Node' or output == 'csv':   # GeoJSON reaches get no node_id
            ids['node_id'] = gdf['node_id'] if feature_type == 'Node' else None
        columns_with_units = add_units(gdf, columns)
        unit_columns.extend(columns_with_units[len(columns):])
        if output == 'geojson' and 'geometry' not in columns_with_units:
            columns_with_units.append('geometry')
        gdf = _fill_missing_columns(gdf, columns_with_units)
        frame = gdf[columns_with_units].assign(**ids)
        if output == 'csv':
            frame = pd.DataFrame(frame)
            if 'geometry' in frame.columns:
                frame['geometry'] = frame['geometry'].apply(lambda geometry: geometry.wkt)
        frames.append(frame)

    requested = [column for column in dict.fromkeys(reach_columns + node_columns) if column not in REACH_AND_NODE_ID_COLUMNS]
    if output == 'geojson':
        requested = [column for column in requested if column != 'geometry']
    union = REACH_AND_NODE_ID_COLUMNS + requested + list(dict.fromkeys(unit_columns))
    if output == 'geojson':
        union.append('geometry')

    if output == 'geojson':
        # Each type keeps only its own columns, in union order; Feature ids are assigned once
        features = []
        for frame in frames:
            own_columns = [column for column in union if column in frame.columns]
            features.extend(gpd.GeoDataFrame(frame[own_columns], geometry='geometry').to_geo_dict()['features'])
        for index, feature in enumerate(features):
            feature['id'] = str(index)
        response = {'type': 'FeatureCollection', 'features': features}
        hits = len(features)
    else:
        combined = pd.concat([frame.reindex(columns=union) for frame in frames], ignore_index=True)
        response = combined.to_csv(index=False)
        hits = combined.shape[0]

    data = {
        'http_code': '200 OK',
        'response': response
    }

    return data, hits


def add_units(gdf, columns):
    """Add units to list of columns to return in response

    :param gdf: DataFrame of results from query
    :type gdf: gpd.GeoDataFrame
    :param columns: List of columns to return in response
    :type columns: list of str
    """

    # Inject units for fields not carried in the source data (e.g. SoS discharge), served as
    # constants, without overwriting any units already present from ingest.
    for column in columns:
        unit = constants.FIELD_UNITS.get(column)
        if unit is not None and f"{column}_units" not in gdf.columns:
            gdf[f"{column}_units"] = unit

    gdf_columns = gdf.columns.values.tolist()
    unit_columns = [f"{column}_units" for column in columns if f"{column}_units" in gdf_columns]
    return columns + unit_columns


def get_response(results, hits, elapsed, return_type, output, compact, group_by_feature=False):  # pylint: disable=too-many-arguments,too-many-positional-arguments
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
    :param group_by_feature: Compact per reach / node (reach + node responses)
    :type group_by_feature: bool

    rtype: dict
    """

    if results['http_code'] == '200 OK':

        if return_type in ('text/csv', 'application/geo+json'):
            if compact == 'true' and return_type == 'application/geo+json':
                data = compact_results(results['response'], group_by_feature)
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
                results['response'] = compact_results(results['response'], group_by_feature)
            data['results'][output] = results['response']

    else:
        raise RequestError(results['error_message'])

    return data


def build_csv_file_response(results, parameters):
    """Wrap a successful CSV result as a file download.

    Raises RequestError for non-200 results (matching get_response) so the caller's error handling
    stays uniform, and avoids building the JSON wrapper that a csv_file request would discard.

    :param results: Dictionary of SWOT timeseries results (must contain a CSV 'response')
    :type results: dict
    :param parameters: Request parameters (feature, feature_id, start_time, end_time, filename)
    :type parameters: dict

    :rtype: dict
    """

    if results['http_code'] != '200 OK':
        raise RequestError(results['error_message'])

    filename = parameters['filename']
    if filename:
        filename = sanitize_filename(filename)
    else:
        feature = f"{parameters['feature']}_nodes" if parameters.get('node_fields') else parameters['feature']
        filename = sanitize_filename(build_default_filename(
            feature, parameters['feature_id'],
            parameters['start_time'], parameters['end_time']
        ))

    return {
        '__hydrocron_download__': True,
        'csv_data': results['response'],
        'filename': filename
    }


def compact_results(results, group_by_feature=False):
    """Compact GeoJSON results to return a properties object with aggregated
    time series data.

    :param results: Dictionary of SWOT timeseries results
    :type results: dict
    :param group_by_feature: Compact each reach and each node separately (reach + node responses),
        keyed on feature_type and node_id (nodes) or reach_id (reaches), in first-seen order
    :type group_by_feature: bool

    rtype: dict
    """

    groups = {}
    for feature in results['features']:
        key = None
        if group_by_feature:
            properties = feature['properties']
            key = (properties['feature_type'], properties['node_id'] if properties['feature_type'] == 'Node' else properties['reach_id'])
        groups.setdefault(key, []).append(feature)

    response = {
        'type': 'FeatureCollection',
        'features': []
    }
    for index, features in enumerate(groups.values()):
        compact_feature = {
            'id': str(index),
            'type': 'Feature',
            'properties': {},
            'geometry': features[0]['geometry']   # Grab first geometry
        }
        for field in features[0]['properties'].keys():
            compact_feature['properties'][field] = [feature['properties'][field] for feature in features]
        response['features'].append(compact_feature)

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
        logging.info('collection_name: %s', parameters['collection_name'])
        return_type, output = get_return_type(headers['accept'], parameters['output'])
    except RequestError as e:
        error_code = int(str(e).split(':')[0])    # pylint: disable=use-maxsplit-arg
        logging.error(json.dumps({'http_code': error_code, 'error_message': str(e)}))
        raise e

    results, hits = timeseries_get(
        parameters['collection_name'],
        parameters['feature'],
        parameters['feature_id'],
        parameters['start_time'],
        parameters['end_time'],
        output,
        parameters['fields'],
        parameters['node_fields']
    )

    end = time.time()
    elapsed = round((end - start) * 1000, 3)

    try:
        if parameters['output'] == 'csv_file':
            data = build_csv_file_response(results, parameters)
        else:
            data = get_response(results, hits, elapsed, return_type, output, parameters['compact'],
                                parameters['node_fields'] is not None)
    except RequestError as e:
        error_code = int(str(e).split(':')[0])    # pylint: disable=use-maxsplit-arg
        logging.error(json.dumps({'http_code': error_code, 'error_message': str(e)}))
        raise e

    # Size the final response (after compaction and any wrappers) as the Lambda Python 3.12+ runtime
    # serializes it: JSON with Unicode unescaped. A CSV string grows when JSON-encoded (quotes, \n escapes).
    response_size = len(json.dumps(data, default=str, ensure_ascii=False).encode('utf-8'))

    # Enforce Lambda's response payload limit.
    if response_size > MAX_RESPONSE_SIZE_BYTES:
        size_mb = response_size / (1024 * 1024)
        limit_mb = MAX_RESPONSE_SIZE_BYTES // (1024 * 1024)
        error_message = (f'413: Query response is {size_mb:.1f}MB ({hits} hits), exceeding the {limit_mb}MB '
                         f'limit. Reduce the time range or number of requested fields.')
        logging.error(json.dumps({'http_code': 413, 'error_message': error_message}))
        raise RequestError(error_message)

    logging.info('response: %s', json.dumps(
        {'status': results['http_code'], 'time': elapsed, 'hits': hits, 'response_size': response_size}))

    return data
