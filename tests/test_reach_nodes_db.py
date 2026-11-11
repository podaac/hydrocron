"""
Tests for the reach + node DB layer: ReachIdIndex lookup and parallel per-node queries
"""
import os
import subprocess
import sys

import pytest

REACH_2_0 = '71140300273'          # 56 nodes, two passes (2024-08-25, 2024-09-15)
REACH_2_0_UNOBSERVED = '71140100251'
REACH_D = '57203000041'            # 52 nodes, two passes (2026-04-19, 2026-05-10)
START = '2024-01-01T00:00:00+0000'
END = '2026-12-31T23:59:59+0000'


def _repository():
    """Repository wired to the test DynamoDB (resource + shared client)."""
    from hydrocron.api.data_access.db import DynamoDataRepository
    from hydrocron.utils import connection
    return DynamoDataRepository(connection.dynamodb_resource, connection.dynamodb_client)


class StubClient:
    """Low-level client stub returning canned query pages and recording calls."""

    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return self.pages.pop(0)


def _key_page(node_ids, last=False):
    page = {'Items': [{'node_id': {'S': n}} for n in node_ids], 'Count': len(node_ids)}
    if not last:
        page['LastEvaluatedKey'] = {'reach_id': {'S': 'x'}}
    return page


def test_get_table_info():
    """Collections and sub-collections resolve to their table; unknown returns None."""
    from hydrocron.api.data_access.db import get_table_info
    from hydrocron.utils import constants

    assert get_table_info('SWOT_L2_HR_RiverSP_D', 'Node')['table_name'] == constants.API_TEST_NODE_TABLE_NAME_D
    assert get_table_info('SWOT_L2_HR_RiverSP_reach_D', 'Node')['table_name'] == constants.API_TEST_NODE_TABLE_NAME_D
    assert get_table_info('SWOT_L2_HR_RiverSP_reach_2.0', 'node')['table_name'] == constants.API_TEST_NODE_TABLE_NAME
    assert get_table_info('SWOT_L2_HR_RiverSP_2.0', 'Reach')['table_name'] == constants.API_TEST_REACH_TABLE_NAME
    assert get_table_info('SWOT_L2_HR_LakeSP_D', 'Node') is None
    assert get_table_info('nope', 'Reach') is None


@pytest.mark.parametrize("collection_name,reach_id,expected_nodes,expected_rows", [
    ('SWOT_L2_HR_RiverSP_2.0', REACH_2_0, 56, 112),      # two passes
    ('SWOT_L2_HR_RiverSP_reach_2.0', REACH_2_0, 56, 112),
    ('SWOT_L2_HR_RiverSP_2.0', REACH_2_0_UNOBSERVED, 55, 110),
    ('SWOT_L2_HR_RiverSP_D', REACH_D, 52, 104),          # two passes
    ('SWOT_L2_HR_RiverSP_reach_D', REACH_D, 52, 104),
])
def test_get_node_ids_by_reach_id(hydrocron_api, collection_name, reach_id, expected_nodes, expected_rows):
    """The GSI returns every node of the reach once (de-duplicated across passes), sorted, with the row count."""
    node_ids, count = _repository().get_node_ids_by_reach_id(collection_name, reach_id, START, END)

    assert len(node_ids) == expected_nodes
    assert count == expected_rows
    assert node_ids == sorted(node_ids)
    assert all(n.startswith(reach_id[:10]) for n in node_ids)


def test_get_node_ids_by_reach_id_time_range(hydrocron_api):
    """Only rows inside the time range are returned."""
    node_ids, count = _repository().get_node_ids_by_reach_id('SWOT_L2_HR_RiverSP_2.0', REACH_2_0,
                                                             '2023-01-01T00:00:00+0000', '2023-12-31T23:59:59+0000')
    assert node_ids == [] and count == 0


def test_get_node_ids_by_reach_id_limit_real_db(hydrocron_api):
    """Over the limit raises ItemLimitExceeded; at the limit is fine."""
    from hydrocron.api.data_access.db import ItemLimitExceeded

    with pytest.raises(ItemLimitExceeded) as exc_info:   # 104 node rows (52 nodes x 2 passes)
        _repository().get_node_ids_by_reach_id('SWOT_L2_HR_RiverSP_D', REACH_D, START, END, max_items=103)
    assert exc_info.value.count == 104 and exc_info.value.limit == 103

    node_ids, _ = _repository().get_node_ids_by_reach_id('SWOT_L2_HR_RiverSP_D', REACH_D, START, END, max_items=104)
    assert len(node_ids) == 52


def test_get_node_ids_by_reach_id_pagination():
    """Pages are followed via LastEvaluatedKey; node_ids are de-duplicated across pages."""
    from hydrocron.api.data_access.db import DynamoDataRepository
    from hydrocron.utils import constants

    client = StubClient([_key_page(['n2', 'n1']), _key_page(['n1', 'n3']), _key_page(['n4'], last=True)])
    node_ids, count = DynamoDataRepository(None, client).get_node_ids_by_reach_id('SWOT_L2_HR_RiverSP_D', 'r', START, END)

    assert node_ids == ['n1', 'n2', 'n3', 'n4']
    assert count == 5
    assert len(client.calls) == 3
    assert 'ExclusiveStartKey' not in client.calls[0]
    assert client.calls[1]['ExclusiveStartKey'] == {'reach_id': {'S': 'x'}}
    assert all(c['IndexName'] == constants.SWOT_NODE_REACH_INDEX_NAME for c in client.calls)
    assert all(c['TableName'] == constants.API_TEST_NODE_TABLE_NAME_D for c in client.calls)


def test_get_node_ids_by_reach_id_stops_paging_at_limit():
    """The limit check runs per page, so paging stops as soon as it is exceeded."""
    from hydrocron.api.data_access.db import DynamoDataRepository, ItemLimitExceeded

    client = StubClient([_key_page(['n1', 'n2', 'n3']), _key_page(['n4', 'n5', 'n6']), _key_page(['n7'], last=True)])
    with pytest.raises(ItemLimitExceeded) as exc_info:
        DynamoDataRepository(None, client).get_node_ids_by_reach_id('SWOT_L2_HR_RiverSP_D', 'r', START, END, max_items=4)

    assert exc_info.value.count == 6
    assert len(client.calls) == 2   # third page never requested


def test_get_node_series(hydrocron_api):
    """Rows come back in node_ids order, projected to the requested attributes (incl. reserved words)."""
    repository = _repository()
    node_ids, _ = repository.get_node_ids_by_reach_id('SWOT_L2_HR_RiverSP_D', REACH_D, START, END)
    attributes = ['node_id', 'reach_id', 'range_start_time', 'time', 'width', 'wse', 'wse_units', 'geometry', 'wse']

    items = repository.get_node_series('SWOT_L2_HR_RiverSP_D', node_ids, START, END, attributes)

    assert [item['node_id'] for item in items] == [node_id for node_id in node_ids for _ in range(2)]   # 2 passes each
    assert all(set(item) <= set(attributes) for item in items)
    assert all({'node_id', 'reach_id', 'range_start_time', 'time', 'width', 'wse', 'geometry'} <= set(item) for item in items)
    assert all(item['reach_id'] == REACH_D for item in items)
    assert all(isinstance(item['wse'], str) for item in items)


def test_get_node_series_time_order(hydrocron_api):
    """Rows are grouped in the given node order, and each node's passes come back in time order."""
    repository = _repository()
    node_ids, _ = repository.get_node_ids_by_reach_id('SWOT_L2_HR_RiverSP_D', REACH_D, START, END)
    first, second = node_ids[:2]

    items = repository.get_node_series('SWOT_L2_HR_RiverSP_D', [second, first], START, END, ['node_id', 'range_start_time'])

    assert [item['node_id'] for item in items] == [second, second, first, first]
    for node_id in (first, second):
        times = [item['range_start_time'] for item in items if item['node_id'] == node_id]
        assert times == sorted(times) and times[0].startswith('2026-04-19') and times[1].startswith('2026-05-10')


def test_get_node_series_pages_with_stub():
    """A node whose rows span several pages returns all of them, in order."""
    from hydrocron.api.data_access.db import DynamoDataRepository

    client = StubClient([
        {'Items': [{'node_id': {'S': 'n1'}, 'range_start_time': {'S': 't1'}}], 'LastEvaluatedKey': {'k': {'S': '1'}}},
        {'Items': [{'node_id': {'S': 'n1'}, 'range_start_time': {'S': 't2'}}]},
    ])
    items = DynamoDataRepository(None, client).get_node_series('SWOT_L2_HR_RiverSP_D', ['n1'], START, END, ['node_id', 'range_start_time'])

    assert items == [{'node_id': 'n1', 'range_start_time': 't1'}, {'node_id': 'n1', 'range_start_time': 't2'}]
    assert client.calls[1]['ExclusiveStartKey'] == {'k': {'S': '1'}}
    assert client.calls[0]['ExpressionAttributeNames'] == {'#a0': 'node_id', '#a1': 'range_start_time'}


def test_get_node_series_failure_leaves_nothing_running():
    """If one node query fails, the error is raised and no other node query is still running or queued.

    Lambda freezes leftover threads and resumes them in the next invocation, so work for a failed
    request must stop (not-started queries cancelled, running ones finished) before returning.
    """
    import threading
    import time
    from hydrocron.api.data_access.db import DynamoDataRepository

    lock = threading.Lock()
    state = {'started': 0, 'running': 0}

    class SlowFailingClient:
        def query(self, **kwargs):
            with lock:
                state['started'] += 1
                state['running'] += 1
            try:
                if kwargs['ExpressionAttributeValues'][':node_id']['S'] == 'n0':
                    raise RuntimeError('query failed')
                time.sleep(0.05)
                return {'Items': []}
            finally:
                with lock:
                    state['running'] -= 1

    node_ids = [f'n{i}' for i in range(200)]
    with pytest.raises(RuntimeError, match='query failed'):
        DynamoDataRepository(None, SlowFailingClient()).get_node_series('SWOT_L2_HR_RiverSP_D', node_ids, START, END, ['node_id'])

    assert state['running'] == 0                  # nothing still running
    started = state['started']
    time.sleep(0.2)
    assert state['started'] == started            # nothing queued that starts later
    assert started < len(node_ids)                # queries not yet started were cancelled


def test_thread_count_and_pool_from_env():
    """Thread count is read from the env at import and sizes both the pool and the client's connections."""
    code = (
        "from hydrocron.utils import connection, constants\n"
        "from hydrocron.api.data_access import db\n"
        "print(constants.REACH_AND_NODE_QUERY_THREADS, constants.MAX_REACH_NODE_ITEMS,\n"
        "      db.NODE_QUERY_POOL._max_workers, connection.dynamodb_client.meta.config.max_pool_connections)\n"
    )
    env = dict(os.environ, HYDROCRON_ENV='test', AWS_DEFAULT_REGION='us-west-2',
               HYDROCRON_REACH_AND_NODE_QUERY_THREADS='7', HYDROCRON_MAX_REACH_NODE_ITEMS='123')
    out = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, check=True).stdout

    assert out.split() == ['7', '123', '7', '7']
