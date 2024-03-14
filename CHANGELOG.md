# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
    - Issue 105 - Only benchmarking data is being loaded even when load_benchmarking_data flag is false
    - Issue 79 - Generate data for use by benchmarks
    - Issue 88 - There are no CloudWatch logs for the API Gateway
    - Issue 75 - Update log messaging format
    - Issue 60 - Encapsulate DyanmoDB under a single shared module
    - Issue 60 - Improved error handling
### Changed
### Deprecated 
### Removed
    - Issue 39 - Clean up code, removed comments and unused parameters
### Fixed
    - Issue 44 - Load data lambda only loads the first granule found in the time range
    - Issue 116 - CICD will not publish when build run as workflow dispatch
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
