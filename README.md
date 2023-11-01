## Overview
Hydrocron API is a new tool that implements functionalities that will allow 
hydrologists to have direct access to filtered data from our newest satellites. 
This innovative tool will provide an effortless way to filter data by feature ID, 
date range, polygonal area, and more. This data will be returned in formats such 
as CSV and geoJSON.

## Requirements
Python 3.10+

## Usage
Before starting the server you must first start a local database instance. The easiest method is to use docker. 
First, make sure you have installed Docker and AWS CLI. To configure AWS local variables:

```
aws configure
    AWS Access Key ID: a
    AWS Secret Acces Key: a
    Default region name: us-west-2
    Default output format: None
```

Next step is to run docker compose up:

```
docker compose up
```

To run the server, please execute the following from the root directory:

```
HYDROCRON_ENV=dev python -m hydrocron_api
```

and open your browser to here:

```
http://localhost:8080/hydrocron/HydroAPI/1.0.0/ui/
```

Your Swagger definition lives here:

```
http://localhost:8080/hydrocron/HydroAPI/1.0.0/swagger.json
```

## Running with Docker 

To run the server on a Docker container, please execute the following from the root directory:

```bash
# building the image
docker build -t hydrocron_api .

# starting up a container
docker run -p 8080:8080 hydrocron_api
```

## Loading the Database from CMR

Instructions for loading the database with data from CMR instead of the single test granule, are described in hydrocron_db/LOAD_DATA_README.md
