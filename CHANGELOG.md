# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
    - Issue 222 - Add operations to load granule Lambda to write granule record to track ingest database
    - Issue 201 - Create table for tracking granule ingest status
    - Issue 198 - Implement track ingest lambda function CMR and Hydrocron queries
    - Issue 193 - Add new Dynamo table for prior lake data
### Changed
### Deprecated 
### Removed
### Fixed
    - Issue 210 - Features with large geometries cannot be loaded
### Security

## [1.3.0]

### Added
    - Issue 186 - Implement API keys to control usage
    - Issue 183 - Update documentation examples and provide a brief intro to the timeseries endpoint
    - Issue 100 - Add option to 'compact' GeoJSON result into single feature
    - Issue 101 - Add support for HTTP Accept header
    - Issue 102 - Enable compression for API Responses
### Changed
### Deprecated 
### Removed
### Fixed
    - Issue 175 - Update all documentation to point to OPS instead of UAT
### Security

## [1.2.0]

### Added
    - Issue 124 - Log granule name on ingest
    - Issue 155 - Log feature ids on database write
    - Issue 21 - Create tutorial documentation
    - Issue 142 - Add fields to support OPS monitoring and set up indexes to query on them
### Changed
    - Issue 161 - Remove obscure_data option from load data lambdas before OPS loading, add environment variable.
### Deprecated 
### Removed
### Fixed
    - Issue 169 - 403 Error when accessing grnule through bulk load_data
    - Issue 158 - Use Lambda role instead of EDL for s3 connection
    - Issue 104 - Prevent nodes from being loaded into the reach table
### Security

## [1.1.0]

### Added 
    - Issue 77 - Create UMM-S record for hydrocron
    - Issue 89 - Pass headers to timeseries Lambda and test for 'Elastic-Heartbeat' in 'User-Agent' header
    - Issue 126 - Capture and log the client IP address
    - Issue 24 - Indicate which collection version the data belongs to
    - Issue 13 - Add SWORD version from shp.xml to DB entries
    - Issue 85 - Add variable units to API response
    - Issue 78 - Use a VPC endpoint and policies to access DynamoDB
    - Issue 70 - Enable notification of swot shapefile to tva
    - Issue 91 - Add CORS headers to API responses
    - Issue 79 - Generate data for use by benchmarks
    - Issue 88 - There are no CloudWatch logs for the API Gateway
    - Issue 13 - Add SWORD version from shp.xml to DB entries
### Changed
    - Issue 125 - Provide better time series Lambda function logging
    - Issue 132 - Update documentation for OPS release
    - Issue 127 - Return a 400 (not 404) response code and a better error message when there is no data in the start/end dates requested
    - Issue 108 - Update collection to 2.0, backload 2.0 data
    - Issue 59 - Using GeoDataFrame to work with data returned from db
    - Issue 75 - Update log messaging format
    - Issue 60 - Encapsulate DyanmoDB under a single shared module
    - Issue 60 - Improved error handling
### Deprecated 
### Removed
    - Issue 39 - Clean up code, removed comments and unused parameters
### Fixed
    - Issue 131 - Error message when incorrect time format entered suggests a time format that also fails
    - Issue 105 - Only benchmarking data is being loaded even when load_benchmarking_data flag is false
    - Issue 44 - Load data lambda only loads the first granule found in the time range
    - Issue 116 - CICD will not publish when build run as workflow dispatch
    - Issue 146 - Fixed value of URL and RelatedURLs in UMM-S record
### Security

## [1.0.0]

### Added
    - Issue 41 - Update API documentation with query response examples
    - Issue 27 - Create lambda function to execute database loading
    - Issue 9 - Create API Usage Documentation
    - Issue 4 - User guide for how to run database load script manually
    - Issue 12 - Move all constants to separate constants file
    - Issue 6 - Pylint and Flake8 configured
    - Issue 6 - Github Actions
    - Issue 8 - Hydrocron API implementation with mysql local database
    - Issue 23 - Added github actions with Snyk, pylint, flake8
    - Issue 7 - Added actions to build.yml to upload docker container to registry
    - Issue 7 - Fixed poetry.lock to account for new vulnerability detected in Synk, given that we are going to remove flask
### Changed
    - Issue 8 - Hydrocron API implementation with dynamodb local database
    - Issue 8 - Rearrange database code
    - Issue 8 - Rearrange tests
    - Issue 8 - Add script to load data
### Deprecated 
### Removed
    - Issue 18 - Remove Flask
    - Issue 52 - Remove partial_f from data columns to obscure
### Fixed
    - Issue 42 - Change database query to use time range
    - Issue 36 - Request mapping template was not transforming request parameters correctly resulting in 500 internal server errors
    - Issue 33 - Obscure data sometimes fails when 1 is chosen multiplier in randomization
    - Issue 45 - Fixed columns filtering bug
    - Issue 38 - Fix bug: specification does not match actual returned content (csv)
    - Issue 45 - Fixed columns filtering bug
    - Issue 54 - Fixed output format
    - Issue 55 - Fixed cvs with geometry bug
    - Issue 62 - Fix mismatch in specification and api 
    - Issue 64 - Fix bug by parsing just the request query params
### Security
