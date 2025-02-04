## Overview

Hydrocron is an API that repackages hydrology datasets from the Surface Water and Ocean Topography (SWOT) satellite into formats that make time-series analysis easier, including GeoJSON and CSV. To use Hydrocron, see the official documentation with examples and tutorials here: [https://podaac.github.io/hydrocron/intro.html](https://podaac.github.io/hydrocron/intro.html)

The following sections of this readme describe how to install and run a development version of Hydrocron locally on your own computer. This is not recommended if you just want to access SWOT data through Hydrocron. To access data, see the documentation linked above.

To contribute to the development of Hydrocron, see the [contributing guidelines](https://github.com/podaac/hydrocron/blob/develop/CONTRIBUTING.md) and browse the open issues.

***NOTE: the following instructions for installing and running a local version of Hydrocron are out of date, and may result in a broken install. We are aware of the issue and working on restoring local development functionality. Please open a new issue or ask a question on the [PO.DAAC forum](https://podaac.jpl.nasa.gov/forum/viewforum.php?f=6) if you need to run a local installation.***

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
