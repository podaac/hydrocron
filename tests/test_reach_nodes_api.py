"""
Tests for reach + node requests (node_fields) through the timeseries lambda handler
"""
import csv
import io

import pytest

from hydrocron.utils.constants import FILL_VALUE

REACH_D = '57203000041'            # D: 52 nodes; passes 2026-04-19 (cycle 049) and 2026-05-10 (cycle 050)
REACH_D_START = '2026-04-01T00:00:00Z'
REACH_D_END = '2026-04-30T00:00:00Z'      # first pass only
TWO_PASS_END = '2026-05-31T00:00:00Z'     # both passes
REACH_D_NODES = 52
PASS_1_TIME = '2026-04-19T19:08:16Z'
PASS_2_TIME = '2026-05-10T15:53:20Z'
NODE_OBSERVED_BOTH = '57203000040201'     # observed on both passes


def _event(node_fields='node_id,time_str,wse,flow_angle', fields='reach_id,time_str,wse,slope', accept=None,
           **body):
    """Build a reach + node request event (D reach by default)."""
    event = {
        'body': {
            'feature': 'Reach',
            'feature_id': REACH_D,
            'start_time': REACH_D_START,
            'end_time': REACH_D_END,
            'output': 'csv',
            'collection_name': 'SWOT_L2_HR_RiverSP_D',
            'fields': fields,
            **body
        },
        'headers': {'User-Agent': 'pytest', 'X-Forwarded-For': '127.0.0.1'}
    }
    if node_fields is not None:
        event['body']['node_fields'] = node_fields
    if accept:
        event['headers']['Accept'] = accept
        event['body'].pop('output', None)
    return event


def _handler(event):
    import hydrocron.api.controllers.timeseries
    return hydrocron.api.controllers.timeseries.lambda_handler(event, '_')


def _csv_rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def test_reach_and_nodes_csv(hydrocron_api):
    """CSV: id columns first, reach row then node rows, blanks where a field doesn't apply, fill values kept."""
    result = _handler(_event())
    assert result['status'] == '200 OK'
    assert result['hits'] == 1 + REACH_D_NODES

    text = result['results']['csv']
    header = text.splitlines()[0].split(',')
    assert header == ['feature_type', 'reach_id', 'node_id', 'time_str', 'wse', 'slope', 'flow_angle',
                      'wse_units', 'slope_units', 'flow_angle_units']

    rows = _csv_rows(text)
    reach, nodes = rows[0], rows[1:]
    assert reach['feature_type'] == 'Reach' and reach['reach_id'] == REACH_D and reach['node_id'] == ''
    assert reach['flow_angle'] == '' and reach['flow_angle_units'] == ''
    assert reach['slope'] != '' and reach['slope_units'] == 'm/m'

    assert len(nodes) == REACH_D_NODES
    assert all(n['feature_type'] == 'Node' and n['reach_id'] == REACH_D for n in nodes)
    assert [n['node_id'] for n in nodes] == sorted(n['node_id'] for n in nodes)
    assert all(n['slope'] == '' and n['slope_units'] == '' for n in nodes)
    assert all(n['wse_units'] == 'm' and n['flow_angle_units'] != '' for n in nodes)
    # unobserved nodes are kept with fill values (real missing), observed ones have data
    assert any(n['wse'] == FILL_VALUE for n in nodes) and any(n['wse'] != FILL_VALUE for n in nodes)
    assert 'geometry' not in header


def test_reach_and_nodes_csv_geometry_only_in_fields(hydrocron_api):
    """geometry requested for the reach only: WKT on the reach row, blank on node rows."""
    rows = _csv_rows(_handler(_event(fields='reach_id,time_str,geometry', node_fields='node_id,wse'))['results']['csv'])

    assert rows[0]['geometry'].startswith('LINESTRING')
    assert all(row['geometry'] == '' for row in rows[1:])


def test_reach_and_nodes_csv_duplicate_fields(hydrocron_api):
    """Fields in both lists (and the auto-added ids) appear once."""
    text = _handler(_event(fields='reach_id,wse,time_str', node_fields='reach_id,node_id,wse,time_str,wse'))['results']['csv']
    assert text.splitlines()[0] == 'feature_type,reach_id,node_id,wse,time_str,wse_units'


def test_reach_and_nodes_geojson(hydrocron_api):
    """GeoJSON: one Feature per row, unique ids, same property keys everywhere, null where not applicable."""
    result = _handler(_event(output='geojson'))
    features = result['results']['geojson']['features']

    assert result['hits'] == len(features) == 1 + REACH_D_NODES
    assert [f['id'] for f in features] == [str(i) for i in range(len(features))]
    keys = list(features[0]['properties'])
    assert keys == ['feature_type', 'reach_id', 'node_id', 'time_str', 'wse', 'slope', 'flow_angle',
                    'wse_units', 'slope_units', 'flow_angle_units']
    assert all(list(f['properties']) == keys for f in features)

    reach, nodes = features[0], features[1:]
    assert reach['properties']['node_id'] is None and reach['properties']['flow_angle'] is None
    assert reach['geometry']['type'] == 'LineString'
    assert all(n['properties']['slope'] is None for n in nodes)
    assert all(n['geometry']['type'] == 'Point' for n in nodes)


def test_reach_and_nodes_geojson_compact(hydrocron_api):
    """compact=true: one Feature per reach and per node, values as arrays; hits counts rows."""
    result = _handler(_event(output='geojson', compact='true'))
    features = result['results']['geojson']['features']

    assert len(features) == 1 + REACH_D_NODES
    assert result['hits'] == 1 + REACH_D_NODES
    assert [f['id'] for f in features] == [str(i) for i in range(len(features))]
    assert features[0]['properties']['feature_type'] == ['Reach']
    assert features[0]['geometry']['type'] == 'LineString'
    node_ids = [f['properties']['node_id'][0] for f in features[1:]]
    assert node_ids == sorted(set(node_ids))
    assert all(isinstance(value, list) for f in features for value in f['properties'].values())


def test_reach_and_nodes_two_passes_csv(hydrocron_api):
    """Two passes (2026-04-19, 2026-05-10): reach rows first in time order, then each node's rows in time order."""
    result = _handler(_event(end_time=TWO_PASS_END))
    rows = _csv_rows(result['results']['csv'])

    assert result['hits'] == 2 * (1 + REACH_D_NODES)
    reach, nodes = rows[:2], rows[2:]
    assert [r['feature_type'] for r in reach] == ['Reach', 'Reach']
    assert [r['time_str'] for r in reach] == [PASS_1_TIME, PASS_2_TIME]
    assert all(r['feature_type'] == 'Node' for r in nodes) and len(nodes) == 2 * REACH_D_NODES
    assert [n['node_id'] for n in nodes] == [n['node_id'] for n in nodes[::2] for _ in range(2)]   # grouped by node
    both = [n for n in nodes if n['node_id'] == NODE_OBSERVED_BOTH]
    assert [n['time_str'] for n in both] == [PASS_1_TIME, PASS_2_TIME]
    assert all(n['wse'] != FILL_VALUE for n in both)


def test_reach_and_nodes_compact_two_passes(hydrocron_api):
    """compact=true over two passes: still one Feature per reach and per node, each holding both time steps."""
    result = _handler(_event(output='geojson', compact='true', end_time=TWO_PASS_END))
    features = result['results']['geojson']['features']

    assert len(features) == 1 + REACH_D_NODES
    assert result['hits'] == 2 * (1 + REACH_D_NODES)
    assert features[0]['properties']['feature_type'] == ['Reach', 'Reach']
    assert features[0]['properties']['time_str'] == [PASS_1_TIME, PASS_2_TIME]
    assert all(len(f['properties']['time_str']) == 2 for f in features[1:])
    target = next(f for f in features[1:] if f['properties']['node_id'][0] == NODE_OBSERVED_BOTH)
    assert target['properties']['time_str'] == [PASS_1_TIME, PASS_2_TIME]
    assert target['geometry']['type'] == 'Point'


def test_reach_and_nodes_geo_json_accept(hydrocron_api):
    """Accept: application/geo+json defaults to compact and returns the raw FeatureCollection."""
    result = _handler(_event(accept='application/geo+json'))
    assert result['type'] == 'FeatureCollection'
    assert len(result['features']) == 1 + REACH_D_NODES


def test_reach_and_nodes_text_csv_accept(hydrocron_api):
    """Accept: text/csv returns the raw CSV."""
    result = _handler(_event(accept='text/csv'))
    assert result.startswith('feature_type,reach_id,node_id,')


def test_reach_and_nodes_csv_file(hydrocron_api):
    """csv_file uses the Reach_nodes default filename."""
    result = _handler(_event(output='csv_file'))
    assert result['__hydrocron_download__'] is True
    assert result['filename'] == f'hydrocron_Reach_nodes_{REACH_D}_2026-04-01_2026-04-30.csv'
    assert result['csv_data'].startswith('feature_type,reach_id,node_id,')


@pytest.mark.parametrize("collection_name", ['SWOT_L2_HR_RiverSP_reach_D', 'SWOT_L2_HR_RiverSP_D'])
def test_reach_and_nodes_sub_collection(hydrocron_api, collection_name):
    """A Reach sub-collection name resolves to the parent's node table."""
    rows = _csv_rows(_handler(_event(collection_name=collection_name))['results']['csv'])
    assert len(rows) == 1 + REACH_D_NODES


def test_reach_and_nodes_2_0(hydrocron_api):
    """2.0 collection: nodes come from the 2.0 node table."""
    rows = _csv_rows(_handler(_event(feature_id='71140300273', collection_name='SWOT_L2_HR_RiverSP_2.0',
                                     start_time='2024-08-01T00:00:00Z', end_time='2024-08-31T00:00:00Z'))['results']['csv'])
    assert rows[0]['feature_type'] == 'Reach'
    assert len(rows) == 1 + 56


@pytest.mark.parametrize("compact", ['false', 'true'])
def test_reach_and_nodes_2_0_two_passes(hydrocron_api, compact):
    """2.0 over two passes (2024-08-25, 2024-09-15): both reach rows, and each node's two time steps in order."""
    result = _handler(_event(feature_id='71140300273', collection_name='SWOT_L2_HR_RiverSP_2.0', output='geojson', compact=compact,
                             start_time='2024-08-01T00:00:00Z', end_time='2024-09-30T00:00:00Z'))
    features = result['results']['geojson']['features']
    assert result['hits'] == 2 * (1 + 56)

    if compact == 'true':
        assert len(features) == 1 + 56
        reach_times = features[0]['properties']['time_str']
        node_times = next(f for f in features[1:] if f['properties']['node_id'][0] == '71140300270313')['properties']['time_str']
    else:
        assert len(features) == 2 * (1 + 56)
        reach_times = [f['properties']['time_str'] for f in features if f['properties']['feature_type'] == 'Reach']
        node_times = [f['properties']['time_str'] for f in features if f['properties']['node_id'] == '71140300270313']

    assert reach_times == ['2024-08-25T23:27:23Z', '2024-09-15T20:12:30Z']
    assert [t[:10] for t in node_times] == ['2024-08-25', '2024-09-15']   # observed on both passes


def test_reach_only_when_no_nodes(hydrocron_api):
    """A reach with no nodes in the table returns just the reach rows."""
    rows = _csv_rows(_handler(_event(feature_id='71224100223', collection_name='SWOT_L2_HR_RiverSP_2.0',
                                     start_time='2023-06-04T00:00:00Z', end_time='2023-06-23T00:00:00Z'))['results']['csv'])
    assert [row['feature_type'] for row in rows] == ['Reach']
    assert rows[0]['node_id'] == ''


def test_nodes_only_when_no_reach(hydrocron_api):
    """Nodes without reach rows are still returned."""
    from hydrocron.utils import connection, constants

    table = connection.dynamodb_resource.Table(constants.API_TEST_REACH_TABLE_NAME_D)
    for item in table.query(KeyConditionExpression='reach_id = :r', ExpressionAttributeValues={':r': REACH_D})['Items']:
        table.delete_item(Key={'reach_id': REACH_D, 'range_start_time': item['range_start_time']})

    result = _handler(_event())
    rows = _csv_rows(result['results']['csv'])
    assert result['hits'] == REACH_D_NODES
    assert all(row['feature_type'] == 'Node' for row in rows)


def test_reach_and_nodes_not_found(hydrocron_api):
    """No reach and no nodes: 400 not found."""
    import hydrocron.api.controllers.timeseries
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as exc_info:
        _handler(_event(feature_id='57203000000'))
    assert str(exc_info.value).startswith('400: Results with the specified Feature ID 57203000000 were not found')


@pytest.mark.parametrize("body,message", [
    ({'feature': 'Node', 'feature_id': '57203000040011', 'fields': 'node_id,wse'}, 'node_fields parameter is only valid when feature=Reach'),
    ({'feature': 'PriorLake', 'feature_id': '5160001832', 'fields': 'lake_id,wse', 'collection_name': 'SWOT_L2_HR_LakeSP_D'},
     'node_fields parameter is only valid when feature=Reach'),
    ({'node_fields': ''}, 'node_fields parameter should contain valid SWOT node fields'),
    ({'node_fields': ' , '}, 'node_fields parameter should contain valid SWOT node fields'),
    ({'node_fields': 'node_id,slope'}, 'node_fields parameter should contain valid SWOT node fields'),
    ({'node_fields': 'node_id,wse_sm', 'collection_name': 'SWOT_L2_HR_RiverSP_2.0'}, 'node_fields parameter should contain valid SWOT node fields'),
])
def test_reach_and_nodes_400(hydrocron_api, body, message):
    """Invalid node_fields requests are rejected with a 400."""
    import hydrocron.api.controllers.timeseries
    event = _event()
    event['body'].update(body)
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as exc_info:
        _handler(event)
    assert str(exc_info.value) == f'400: {message}'


def test_reach_and_nodes_wse_sm_on_d(hydrocron_api):
    """D-only node fields are accepted on D."""
    rows = _csv_rows(_handler(_event(node_fields='node_id,wse_sm,wse_sm_q'))['results']['csv'])
    assert 'wse_sm' in rows[0] and rows[1]['wse_sm'] != ''


def test_reach_and_nodes_413_before_node_fetch(hydrocron_api, monkeypatch):
    """Over MAX_REACH_NODE_ITEMS: 413 from the GSI key count, and no node rows are fetched."""
    import hydrocron.api.controllers.timeseries
    from hydrocron.api.data_access.db import DynamoDataRepository
    from hydrocron.utils import constants

    def fail(*args, **kwargs):
        raise AssertionError('node rows fetched')

    monkeypatch.setattr(constants, 'MAX_REACH_NODE_ITEMS', REACH_D_NODES - 1)
    monkeypatch.setattr(DynamoDataRepository, 'get_node_series', fail)
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as exc_info:
        _handler(_event())
    assert str(exc_info.value).startswith(f'413: Reach {REACH_D} has more than {REACH_D_NODES - 1} node rows')


def test_reach_and_nodes_413_waits_for_reach_query(hydrocron_api, monkeypatch):
    """The early 413 returns only after the parallel reach query has finished (no leftover thread)."""
    import threading
    import time
    import hydrocron.api.controllers.timeseries
    from hydrocron.api.data_access.db import DynamoDataRepository
    from hydrocron.utils import constants

    finished = threading.Event()

    def slow_reach_query(self, *args, **kwargs):
        time.sleep(0.3)
        finished.set()
        return {'Items': []}

    monkeypatch.setattr(constants, 'MAX_REACH_NODE_ITEMS', 1)
    monkeypatch.setattr(DynamoDataRepository, 'get_series_by_feature_id', slow_reach_query)
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as exc_info:
        _handler(_event())

    assert str(exc_info.value).startswith('413:')
    assert finished.is_set()


def test_reach_and_nodes_unit_columns_follow_returned_rows(hydrocron_api):
    """Unit columns come from the rows returned: a reach-only result keeps the requested node field
    column (empty) but has no unit column for it, since there are no node rows to take units from."""
    text = _handler(_event(feature_id='71224100223', collection_name='SWOT_L2_HR_RiverSP_2.0',
                           start_time='2023-06-04T00:00:00Z', end_time='2023-06-23T00:00:00Z',
                           fields='reach_id,time_str,wse', node_fields='node_id,flow_angle'))['results']['csv']
    header = text.splitlines()[0].split(',')

    assert header == ['feature_type', 'reach_id', 'node_id', 'time_str', 'wse', 'flow_angle', 'wse_units']


def test_reach_and_nodes_integrity_error(hydrocron_api, monkeypatch, caplog):
    """A node row whose reach_id differs from the request is logged and raises a 500-class error."""
    import hydrocron.api.controllers.timeseries
    from hydrocron.api.data_access.db import DynamoDataRepository

    monkeypatch.setattr(DynamoDataRepository, 'get_node_series', lambda self, *args, **kwargs: [
        {'node_id': '57203000040011', 'reach_id': '99999999999', 'range_start_time': 't', 'geometry': 'POINT (0 0)'}])
    with pytest.raises(hydrocron.api.controllers.timeseries.DataIntegrityError) as exc_info:
        _handler(_event())

    message = str(exc_info.value)
    assert not isinstance(exc_info.value, hydrocron.api.controllers.timeseries.RequestError)
    assert message.startswith('Data integrity error') and not message[0].isdigit()
    assert 'node reach_id mismatch' in caplog.text and '99999999999' in caplog.text


def test_build_node_projection():
    """Projection: requested fields, keys, geometry, units for each field, no duplicates."""
    from hydrocron.api.controllers.timeseries import build_node_projection
    assert build_node_projection('node_id,wse,time') == [
        'node_id', 'wse', 'time', 'reach_id', 'range_start_time', 'geometry', 'node_id_units', 'wse_units', 'time_units']


def test_compact_results_default_unchanged():
    """Without grouping, compact_results still merges every feature into one."""
    from hydrocron.api.controllers.timeseries import compact_results
    results = {'features': [{'properties': {'a': i}, 'geometry': {'g': i}} for i in range(3)]}
    assert compact_results(results) == {'type': 'FeatureCollection', 'features': [
        {'id': '0', 'type': 'Feature', 'properties': {'a': [0, 1, 2]}, 'geometry': {'g': 0}}]}
