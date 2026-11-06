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
    """A validation 400 logs one error line with http_code and code (collection/feature not parsed yet)."""
    with caplog.at_level(logging.INFO), pytest.raises(timeseries.RequestError):
        timeseries.lambda_handler(_event(output='xml'), _Context())

    logs = _response_logs(caplog)
    assert len(logs) == 1
    assert (logs[0]['http_code'], logs[0]['code'], logs[0]['collection']) == (400, 'BAD_REQUEST', None)
    assert logs[0]['error_message'].startswith('400: output')


def test_success_log_line(hydrocron_api, caplog):  # pylint: disable=unused-argument
    """A 200 logs one 'response:' line with the same keys as errors, plus today's status/hits/response_size."""
    import hydrocron.api.controllers.timeseries  # pylint: disable=import-outside-toplevel

    event = _event(collection_name='SWOT_L2_HR_RiverSP_2.0')
    with caplog.at_level(logging.INFO):
        result = hydrocron.api.controllers.timeseries.lambda_handler(event, _Context())

    logs = _response_logs(caplog)
    assert len(logs) == 1
    assert logs[0]['http_code'] == 200 and logs[0]['code'] == 'OK' and logs[0]['status'] == '200 OK'
    assert (logs[0]['collection'], logs[0]['feature'], logs[0]['hits']) == ('SWOT_L2_HR_RiverSP_2.0', 'Reach', result['hits'])
    assert {'time', 'response_size'} <= set(logs[0])
