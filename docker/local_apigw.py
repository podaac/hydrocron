"""
Local API Gateway proxy that mimics AWS API Gateway behavior.

Translates browser GET requests into Lambda invocation events,
forwards to the Lambda container, and transforms the response
including Content-Disposition headers for csv_file downloads.
"""
import json
import os

import requests
from flask import Flask, request, Response

app = Flask(__name__)

LAMBDA_URL = os.environ.get('LAMBDA_URL', 'http://hydrocron-lambda:8080/2015-03-31/functions/function/invocations')


@app.route('/timeseries', methods=['GET'])
def timeseries():
    """Proxy GET /timeseries to the Lambda container."""
    query_params = dict(request.args)
    headers_dict = {
        'User-Agent': request.headers.get('User-Agent', 'local-apigw'),
        'X-Forwarded-For': request.remote_addr,
        'Accept': request.headers.get('Accept', '*/*'),
    }

    x_hydrocron_key = request.headers.get('x-hydrocron-key', '')
    if x_hydrocron_key:
        headers_dict['x-hydrocron-key'] = x_hydrocron_key

    event = {
        'body': query_params,
        'headers': headers_dict,
    }

    try:
        resp = requests.post(LAMBDA_URL, json=event, timeout=30)
        try:
            lambda_result = resp.json()
        except ValueError:
            lambda_result = resp.text
    except Exception as e:
        return Response(json.dumps({'error': str(e)}), status=502, content_type='application/json')

    if 'errorMessage' in lambda_result:
        error_msg = lambda_result['errorMessage']
        try:
            status_code = int(error_msg.split(':')[0])
        except (ValueError, IndexError):
            status_code = 500
        return Response(
            json.dumps({'error': error_msg}),
            status=status_code,
            content_type='application/json',
            headers={'Access-Control-Allow-Origin': '*'}
        )

    if isinstance(lambda_result, dict) and '__hydrocron_download__' in lambda_result:
        filename = lambda_result.get('filename', 'hydrocron_download.csv')
        csv_data = lambda_result.get('csv_data', '')
        return Response(
            csv_data,
            status=200,
            content_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Expose-Headers': 'Content-Disposition',
            }
        )

    accept = request.headers.get('Accept', '*/*')

    if accept == 'text/csv':
        if isinstance(lambda_result, str):
            return Response(lambda_result, status=200, content_type='text/csv',
                            headers={'Access-Control-Allow-Origin': '*'})
        csv_data = lambda_result.get('results', {}).get('csv', '')
        return Response(csv_data, status=200, content_type='text/csv',
                        headers={'Access-Control-Allow-Origin': '*'})

    if accept == 'application/geo+json':
        if isinstance(lambda_result, dict) and 'type' in lambda_result:
            body = json.dumps(lambda_result)
        else:
            body = json.dumps(lambda_result.get('results', {}).get('geojson', {}))
        return Response(body, status=200, content_type='application/geo+json',
                        headers={'Access-Control-Allow-Origin': '*'})

    return Response(
        json.dumps(lambda_result),
        status=200,
        content_type='application/json',
        headers={'Access-Control-Allow-Origin': '*'}
    )


@app.route('/timeseries', methods=['OPTIONS'])
def timeseries_options():
    """CORS preflight."""
    return Response('', status=200, headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-hydrocron-key',
        'Access-Control-Expose-Headers': 'Content-Disposition',
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
