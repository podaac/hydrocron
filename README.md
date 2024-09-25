## Overview

Hydrocron API is a new tool that implements functionalities that will allow 
hydrologists to have direct access to filtered data from our newest satellites. 
This innovative tool will provide an effortless way to filter data by feature ID, 
date range, polygonal area, and more. This data will be returned in formats such 
as CSV and geoJSON.

## Requirements

Python 3.10+

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

Launch dynamodb local on port 8000 and hyrdrocron on port 9000

```bash
docker-compose up
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

The docker container is running a lambda container image. By posting data to port 9000, the lambda handler will be invoked
and will return results from the loaded test data. For example:

```bash
curl --location 'http://localhost:9000/2015-03-31/functions/function/invocations' \
--header 'Content-Type: application/json' \
--data '{
    "body":{
        "feature": "Reach",
        "reach_id": "71224100223",
        "start_time": "2022-08-04T00:00:00+00:00",
        "end_time": "2022-08-23T00:00:00+00:00",
        "output": "csv",
        "fields": "feature_id,time_str,wse"
    }
}'
```

## Loading the Database from CMR

Instructions for loading the database with data from CMR instead of the single test granule, are described in hydrocron_db/LOAD_DATA_README.md
