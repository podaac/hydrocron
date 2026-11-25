"""
Tests for error handling in the timeseries lambda handler: status codes, JSON-safe messages, response log line
"""
import json
import logging

import pytest
from botocore.exceptions import ClientError


@pytest.fixture()
def timeseries(monkeypatch):
    """The timeseries controller, importable without the DynamoDB fixtures (test env: no SSM call at import)."""
    monkeypatch.setenv('HYDROCRON_ENV', 'test')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-west-2')
    monkeypatch.setenv('DEFAULT_RIVER_COLLECTION', 'SWOT_L2_HR_RiverSP')
    monkeypatch.setenv('DEFAULT_LAKE_COLLECTION', 'SWOT_L2_HR_LakeSP')
    monkeypatch.setenv('DEFAULT_COLLECTION_VERSION', 'D')
    import hydrocron.api.controllers.timeseries  # pylint: disable=import-outside-toplevel
    return hydrocron.api.controllers.timeseries


class _Context:  # pylint: disable=too-few-public-methods
    aws_request_id = 'req-1234'


def _event(**body):
    return {
        'body': {
            'feature': 'Reach',
            'feature_id': '71224100223',
            'start_time': '2023-06-04T00:00:00Z',
            'end_time': '2023-06-23T00:00:00Z',
            'output': 'csv',
            'fields': 'reach_id,time_str,wse',
            **body
        },
        'headers': {'User-Agent': 'pytest', 'X-Forwarded-For': '127.0.0.1'}
    }


def _render(error_message):
    """Render the API Gateway error template ("error" : "$input.path('$.errorMessage')") and parse it."""
    return json.loads('{\n  "error" : "' + error_message + '"\n}')['error']


def _raise_from_query(timeseries, monkeypatch, exception):
    def fail(*args, **kwargs):
        raise exception
    monkeypatch.setattr(timeseries, 'timeseries_get', fail)


def _response_logs(caplog):
    """Parsed response log lines: error lines are plain JSON, success lines are 'response: <json>'."""
    lines = []
    for record in caplog.records:
        message = record.getMessage()
        if message.startswith('response: '):
            lines.append(json.loads(message[len('response: '):]))
        elif message.startswith('{"http_code"'):
            lines.append(json.loads(message))
    return lines


@pytest.mark.parametrize('value', ['Re"ach', 'back\\slash', 'line\nbreak', 'tab\there', 'ctrl\x01', 'snow❄', 'x' * 500])
def test_gateway_error_is_valid_json(timeseries, value):
    """Odd characters in an error message still render as valid JSON, and parse back to the original text."""
    message = f'400: feature {value} is not valid.'
    gateway_message = str(timeseries.to_gateway_error(timeseries.RequestError(message)))

    assert '\n' not in gateway_message and '\t' not in gateway_message
    assert _render(gateway_message) == message


def test_gateway_error_escapes_once(timeseries, monkeypatch, caplog):
    """The raised message is escaped once; the log line keeps the plain text."""
    message = '400: bad "value"\n'
    _raise_from_query(timeseries, monkeypatch, timeseries.RequestError(message))

    with caplog.at_level(logging.INFO), pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.lambda_handler(_event(), _Context())

    assert str(exc_info.value) == '400: bad \\"value\\"\\n'
    assert _render(str(exc_info.value)) == message
    assert _response_logs(caplog)[-1]['error_message'] == message


def test_unhandled_exception_returns_500(timeseries, monkeypatch, caplog):
    """Any unhandled exception -> 500 with the request ID only; the traceback stays in the logs."""
    _raise_from_query(timeseries, monkeypatch, KeyError('geometry'))

    with caplog.at_level(logging.INFO), pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.lambda_handler(_event(), _Context())

    assert str(exc_info.value) == ('500: Internal error (request ID req-1234). '
                                   'Please report it at https://github.com/podaac/hydrocron/issues.')
    assert exc_info.value.http_code == 500
    assert 'Traceback' in caplog.text and "KeyError: 'geometry'" in caplog.text
    log = _response_logs(caplog)[-1]
    assert (log['http_code'], log['code'], log['collection'], log['feature']) == (500, 'INTERNAL_ERROR', 'SWOT_L2_HR_RiverSP_D', 'Reach')


@pytest.mark.parametrize('aws_code', ['ProvisionedThroughputExceededException', 'ThrottlingException', 'RequestLimitExceeded',
                                      'InternalServerError', 'ServiceUnavailable'])
def test_aws_throttling_returns_503(timeseries, monkeypatch, caplog, aws_code):
    """DynamoDB throttling / transient errors -> 503, no boto text."""
    _raise_from_query(timeseries, monkeypatch, ClientError({'Error': {'Code': aws_code, 'Message': 'boto detail'}}, 'Query'))

    with caplog.at_level(logging.INFO), pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.lambda_handler(_event(), _Context())

    assert str(exc_info.value) == '503: Service busy. Retry in a few seconds.'
    assert _response_logs(caplog)[-1]['code'] == 'SERVICE_BUSY'


def test_other_aws_error_returns_500(timeseries, monkeypatch):
    """Any other AWS error -> the generic 500, no boto text."""
    _raise_from_query(timeseries, monkeypatch, ClientError({'Error': {'Code': 'ResourceNotFoundException', 'Message': 'boto detail'}}, 'Query'))

    with pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.lambda_handler(_event(), _Context())

    assert str(exc_info.value).startswith('500: Internal error (request ID req-1234).')
    assert 'boto detail' not in str(exc_info.value)


def test_request_error_log_line(timeseries, caplog):
    """A validation 400 logs one error line with http_code and code, and the raw collection + feature (None if not sent)."""
    with caplog.at_level(logging.INFO), pytest.raises(timeseries.RequestError):
        timeseries.lambda_handler(_event(output='xml'), _Context())

    logs = _response_logs(caplog)
    assert len(logs) == 1
    assert (logs[0]['http_code'], logs[0]['code'], logs[0]['collection'], logs[0]['feature']) == (400, 'BAD_REQUEST', None, 'Reach')
    assert logs[0]['error_message'].startswith('400: output')


def test_success_log_line(hydrocron_api, caplog):  # pylint: disable=unused-argument
    """A 200 logs one 'response:' line with the same keys as errors, plus today's status/hits/response_size."""
    import hydrocron.api.controllers.timeseries  # pylint: disable=import-outside-toplevel

    event = _event(collection_name='SWOT_L2_HR_RiverSP_D', feature_id='57203000041',
                   start_time='2026-04-01T00:00:00Z', end_time='2026-04-30T00:00:00Z')
    with caplog.at_level(logging.INFO):
        result = hydrocron.api.controllers.timeseries.lambda_handler(event, _Context())

    logs = _response_logs(caplog)
    assert len(logs) == 1
    assert logs[0]['http_code'] == 200 and logs[0]['code'] == 'OK' and logs[0]['status'] == '200 OK'
    assert (logs[0]['collection'], logs[0]['feature'], logs[0]['hits']) == ('SWOT_L2_HR_RiverSP_D', 'Reach', result['hits'])
    assert {'time', 'response_size'} <= set(logs[0])


RIVER_2_0 = 'SWOT_L2_HR_RiverSP_2.0'
RETIRED_FIELDS_MESSAGE = ('Version 2.0 reaches serve only SoS discharge, ID, time and SWORD fields. '
                          'Use collection_name=SWOT_L2_HR_RiverSP_D')


def _no_db(timeseries, monkeypatch):
    """Record any DynamoDB repository use (a raise would be caught by lambda_handler as a 500)."""
    calls = []
    monkeypatch.setattr(timeseries, 'DynamoDataRepository', lambda *args: calls.append(args))
    return calls


@pytest.mark.parametrize('body, message', [
    ({'collection_name': 'SWOT_L2_HR_LakeSP_2.0', 'feature': 'PriorLake'},
     '410: PriorLake data for SWOT_L2_HR_LakeSP_2.0 has been retired from Hydrocron. Use collection_name=SWOT_L2_HR_LakeSP_D'),
    ({'collection_name': 'SWOT_L2_HR_LakeSP_prior_2.0', 'feature': 'PriorLake'},
     '410: PriorLake data for SWOT_L2_HR_LakeSP_prior_2.0 has been retired from Hydrocron. Use collection_name=SWOT_L2_HR_LakeSP_D'),
    ({'collection_name': 'SWOT_L2_HR_RiverSP_node_2.0', 'feature': 'Node'},
     '410: Node data for SWOT_L2_HR_RiverSP_node_2.0 has been retired from Hydrocron. Use collection_name=SWOT_L2_HR_RiverSP_D'),
    ({'collection_name': RIVER_2_0, 'feature': 'Node'},
     '410: Node data for SWOT_L2_HR_RiverSP_2.0 has been retired from Hydrocron. Use collection_name=SWOT_L2_HR_RiverSP_D'),
    ({'collection_name': 'SWOT_L2_HR_RiverSP_reach_2.0', 'fields': 'reach_id', 'node_fields': 'node_id,wse'},
     '410: Node data for SWOT_L2_HR_RiverSP_reach_2.0 has been retired from Hydrocron. Use collection_name=SWOT_L2_HR_RiverSP_D'),
    ({'collection_name': RIVER_2_0, 'fields': 'reach_id', 'node_fields': 'node_id,wse'},
     '410: Node data for SWOT_L2_HR_RiverSP_2.0 has been retired from Hydrocron. Use collection_name=SWOT_L2_HR_RiverSP_D'),
    ({'collection_name': RIVER_2_0, 'fields': 'reach_id', 'node_fields': ''},
     '410: Node data for SWOT_L2_HR_RiverSP_2.0 has been retired from Hydrocron. Use collection_name=SWOT_L2_HR_RiverSP_D'),
], ids=['lake', 'lake_prior', 'node_sub_collection', 'node_feature', 'node_fields_reach_sub_collection', 'node_fields',
        'empty_node_fields'])
def test_retired_collection_returns_410(timeseries, monkeypatch, caplog, body, message):
    """Retired 2.0 lake / node data -> 410 naming the collection to use, before any DB call; logged with collection + feature."""
    db_calls = _no_db(timeseries, monkeypatch)

    with caplog.at_level(logging.INFO), pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.lambda_handler(_event(**body), _Context())

    assert _render(str(exc_info.value)) == message
    assert (exc_info.value.http_code, exc_info.value.code) == (410, 'RETIRED_COLLECTION')
    assert not db_calls
    log = _response_logs(caplog)[-1]
    assert (log['http_code'], log['code'], log['collection'], log['feature']) == (410, 'RETIRED_COLLECTION', body['collection_name'],
                                                                                  body.get('feature', 'Reach'))


@pytest.mark.parametrize('collection_name', [RIVER_2_0, 'SWOT_L2_HR_RiverSP_reach_2.0'])
def test_retired_reach_fields_return_410(timeseries, monkeypatch, caplog, collection_name):
    """Known 2.0 reach fields not in REACH_2_0_FIELDS -> 410 listing each once, before any DB call."""
    db_calls = _no_db(timeseries, monkeypatch)

    with caplog.at_level(logging.INFO), pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.lambda_handler(_event(collection_name=collection_name, fields='reach_id,wse,sos_consensus_q,dschg_c,wse'), _Context())

    assert _render(str(exc_info.value)) == (f'410: These fields are no longer served for {collection_name}: wse, dschg_c. '
                                            + RETIRED_FIELDS_MESSAGE)
    assert (exc_info.value.http_code, exc_info.value.code) == (410, 'RETIRED_FIELD')
    assert not db_calls
    assert _response_logs(caplog)[-1]['code'] == 'RETIRED_FIELD'


def test_unknown_and_retired_fields_return_400(timeseries, monkeypatch):
    """An unknown field mixed with retired ones -> the usual 400 (unknown-field check wins)."""
    _no_db(timeseries, monkeypatch)

    with pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.lambda_handler(_event(collection_name=RIVER_2_0, fields='reach_id,wse,not_a_field'), _Context())

    assert str(exc_info.value) == '400: fields parameter should contain valid SWOT fields'


@pytest.mark.parametrize('feature', ['Foo', 'node'])
def test_retired_collection_invalid_feature_returns_400(timeseries, monkeypatch, feature):
    """An invalid feature on a retired collection -> the usual feature 400 (collection + feature are checked first)."""
    _no_db(timeseries, monkeypatch)

    with pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.lambda_handler(_event(collection_name='SWOT_L2_HR_LakeSP_2.0', feature=feature), _Context())

    assert str(exc_info.value) == f'400: feature parameter should be Reach, Node, or PriorLake, not: {feature}'


@pytest.mark.parametrize('collection_name, feature, kind', [
    ('SWOT_L2_HR_LakeSP_2.0', 'Reach', 'Collection'),
    ('SWOT_L2_HR_LakeSP_2.0', 'Node', 'Collection'),
    ('SWOT_L2_HR_LakeSP_D', 'Reach', 'Collection'),
    ('SWOT_L2_HR_LakeSP_prior_2.0', 'Node', 'Sub-collection'),
    ('SWOT_L2_HR_RiverSP_node_2.0', 'Reach', 'Sub-collection'),
    ('SWOT_L2_HR_RiverSP_reach_2.0', 'Node', 'Sub-collection'),
    (RIVER_2_0, 'PriorLake', 'Collection'),
    ('SWOT_L2_HR_RiverSP_D', 'PriorLake', 'Collection'),
])
def test_collection_feature_mismatch_returns_400(timeseries, monkeypatch, collection_name, feature, kind):
    """A collection / feature mismatch -> 400 before any 2.0 retirement 410, and before any DB call."""
    db_calls = _no_db(timeseries, monkeypatch)

    with pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.lambda_handler(_event(collection_name=collection_name, feature=feature, node_fields='node_id'), _Context())

    assert str(exc_info.value) == f"400: {kind} '{collection_name}' is not valid for feature type '{feature}'."
    assert not db_calls


def test_alias_of_retired_field_returns_410(timeseries, monkeypatch):
    """An alias is checked by its own name: an alias of a dropped field is retired too."""
    monkeypatch.setattr(timeseries.constants, 'REACH_ALL_COLUMNS', timeseries.constants.REACH_ALL_COLUMNS + ['wse_alias'])
    monkeypatch.setitem(timeseries.constants.FIELD_ALIASES, 'wse_alias', 'wse')

    with pytest.raises(timeseries.RequestError) as exc_info:
        timeseries.check_retired(RIVER_2_0, 'Reach', 'reach_id,wse_alias', None)

    assert str(exc_info.value).startswith(f'410: These fields are no longer served for {RIVER_2_0}: wse_alias. ')


def test_reach_2_0_fields_allowed(timeseries):
    """All 43 kept fields (incl. the swot_discharge_reanalysis alias) pass on 2.0 reaches; all are known reach fields."""
    fields = timeseries.constants.REACH_2_0_FIELDS
    assert len(fields) == len(set(fields)) == 43
    assert set(fields) <= set(timeseries.constants.REACH_ALL_COLUMNS)
    assert 'swot_discharge_reanalysis' in fields

    timeseries.check_retired(RIVER_2_0, 'Reach', ','.join(fields), None)
    timeseries.check_retired('SWOT_L2_HR_RiverSP_reach_2.0', 'Reach', 'reach_id,swot_discharge_reanalysis', None)


@pytest.mark.parametrize('collection_name, feature, fields, node_fields', [
    ('SWOT_L2_HR_RiverSP_D', 'Reach', 'reach_id,wse,dschg_c', 'node_id,wse'),
    ('SWOT_L2_HR_RiverSP_D', 'Node', 'node_id,wse', None),
    ('SWOT_L2_HR_RiverSP_node_D', 'Node', 'node_id,wse', None),
    ('SWOT_L2_HR_LakeSP_D', 'PriorLake', 'lake_id,wse', None),
    ('SWOT_L2_HR_LakeSP_prior_D', 'PriorLake', 'lake_id,wse', None),
    (RIVER_2_0, 'Reach', '', None),   # empty fields: left to the usual 400
])
def test_version_d_not_retired(timeseries, collection_name, feature, fields, node_fields):
    """Version D requests (and an empty 2.0 fields list) pass check_retired unchanged."""
    timeseries.check_retired(collection_name, feature, fields, node_fields)
