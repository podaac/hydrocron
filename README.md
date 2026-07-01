## Overview

Hydrocron is an API that repackages hydrology datasets from the Surface Water and Ocean Topography (SWOT) satellite into formats that make time-series analysis easier, including GeoJSON and CSV. To use Hydrocron, see the official documentation with examples and tutorials here: [https://podaac.github.io/hydrocron/](https://podaac.github.io/hydrocron/)

The following sections of this readme describe how to install and run a development version of Hydrocron locally on your own computer. This is not recommended if you just want to access SWOT data through Hydrocron. To access data, see the documentation linked above.

To contribute to the development of Hydrocron, see the [contributing guidelines](https://github.com/podaac/hydrocron/blob/develop/CONTRIBUTING.md) and browse the open issues.

***NOTE: the following instructions for installing and running a local version of Hydrocron are out of date, and may result in a broken install. We are aware of the issue and working on restoring local development functionality. Please open a new issue or ask a question on the [PO.DAAC forum](https://podaac.jpl.nasa.gov/node/584) if you need to run a local installation.***

## Requirements

Python 3.12+

## Running Locally with Docker

1. Build or pull the hydrocron docker image
2. Run docker compose to launch dynamodb local and hydrocron local
3. Load test data into dynamodb local
4. Execute sample requests

### 1. Build or Pull Hydrocron Docker

Build the docker container:

```bash

docker build . -f docker/Dockerfile -t hydrocron:latest
```

Pull a pre-built image from [https://github.com/podaac/hydrocron/pkgs/container/hydrocron](https://github.com/podaac/hydrocron/pkgs/container/hydrocron):

```bash
docker pull ghcr.io/podaac/hydrocron:latest
```

### 2. Run Docker Compose

Launch DynamoDB local on port 8001, Hydrocron Lambda on port 9000, and local API Gateway on port 8080:

```bash
docker compose up
```

### 3. Load Test Data

If you have not setup a python environment yet, use poetry to first initialize the virtual environment.

```bash
poetry install
```

This will load the data in `test/data` into the local dynamo db instance.

```bash
python tests/load_data_local.py
```

**NOTE** - By default data will be removed when the container is stopped. There are some commented lines in `docker-compose.yml`
that can be used to allow the data to persist across container restarts if desired.

### 4. Execute Sample Requests

The local API Gateway on port 8080 accepts GET requests just like the deployed AWS API. Open these URLs in your browser or use curl.

**Note:** The local API Gateway is a Flask proxy that simulates AWS API Gateway behavior. It validates the Lambda logic end-to-end (query params, DB queries, response formatting) but does not execute the actual VTL response templates. API Gateway-specific behavior (header mapping, content-type negotiation via VTL) is only testable after deployment to SIT/UAT.

```
http://localhost:8080/timeseries?feature=Reach&feature_id=71224100223&start_time=2023-06-04T00:00:00Z&end_time=2023-06-23T00:00:00Z&output=csv&collection_name=SWOT_L2_HR_RiverSP_2.0&fields=reach_id,time_str,wse
```

```
http://localhost:8080/timeseries?feature=Node&feature_id=31241400580011&start_time=2026-02-01T00:00:00Z&end_time=2026-02-28T00:00:00Z&output=csv&collection_name=SWOT_L2_HR_RiverSP_D&fields=node_id,time_str,wse,wse_sm,wse_sm_u,wse_sm_q
```

CSV file download (triggers browser Save As):

```
http://localhost:8080/timeseries?feature=Reach&feature_id=71224100223&start_time=2023-06-04T00:00:00Z&end_time=2023-06-23T00:00:00Z&output=csv_file&collection_name=SWOT_L2_HR_RiverSP_2.0&fields=reach_id,time_str,wse
```

You can also invoke the Lambda container directly via POST on port 9000. For example:

Reach data (v2.0 collection):

```bash
curl --location 'http://localhost:9000/2015-03-31/functions/function/invocations' \
--header 'Content-Type: application/json' \
--data '{
    "body":{
        "feature": "Reach",
        "feature_id": "71224100223",
        "start_time": "2023-06-04T00:00:00+00:00",
        "end_time": "2023-06-23T00:00:00+00:00",
        "output": "csv",
        "collection_name": "SWOT_L2_HR_RiverSP_2.0",
        "fields": "reach_id,time_str,wse"
    },
    "headers": {
        "User-Agent": "curl",
        "X-Forwarded-For": "127.0.0.1"
    }
}'
```

Node data with smoothed WSE fields (Version D collection):

```bash
curl --location 'http://localhost:9000/2015-03-31/functions/function/invocations' \
--header 'Content-Type: application/json' \
--data '{
    "body":{
        "feature": "Node",
        "feature_id": "31241400580011",
        "start_time": "2026-02-01T00:00:00+00:00",
        "end_time": "2026-02-28T00:00:00+00:00",
        "output": "csv",
        "collection_name": "SWOT_L2_HR_RiverSP_D",
        "fields": "node_id,time_str,wse,wse_sm,wse_sm_u,wse_sm_q"
    },
    "headers": {
        "User-Agent": "curl",
        "X-Forwarded-For": "127.0.0.1"
    }
}'
```
