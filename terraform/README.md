
# Deploying the HYDROCRON


## Dependencies
There are a handful of dependencies needed to deploy the entire Hydrocron

* Terraform - deployment technology.  >= Terraform v0.12.7
* AWS CLI - Amazon Web Service command line interface. >= aws-cli/1.11.120
* python3 environment - tested with python 3.7, needed for packaging the lambda functions.

## Soft dependencies
These are dependencies for deploying the entire Hydrocron that exist outside of this build.

* access key for NGAP environment
* Terraform variables defined below

## Terraform Variables

| variable        | Defined In   | Example                                                 | Description |
| --------------- | ------------ | ------------------------------------------------------- | ----------- |
| stage           | tf_vars      | sit                                                     | staging environment to which we are deploying |
| app_name        | tf_vars      | HYDROCRON                                                     | Name of the application being deployed - same for all environments|
| credentials     | command line | ~/.aws/credentials                                      | AWS credential file to use for authentication |
| profile         | command line | ngap-services-sit                                       | AWS Profile to use for authentication |
| docker_tag      | command line | podaac/podaac-cloud/podaac-hydrocron:1.0.0-alpha.3            | Name of docker image and tag as returned from `docker/build-docker.sh`. |
| vpc_id          | tf_vars      | vpc-04d8fc64e8ce5cca8                                   | VPC Id for use. This is predefined by NGAP. |
| private_subnets | tf_vars      | ["subnet-0d15606f25bd4047b","subnet-0adee3417fedb7f05"] | private subnets for use within VPC. This is defined by NGAP |


## Building the lambda images
The lambda code needs to be built into a deployable image and uploaded to ECR before running terraform. Normally CI/CD handles this task but if you are trying to run terraform locally it needs to be done manually.

Follow the instructions in the [docker README](../docker/README.md) to build the image


## Build and deploy the application
We use a pre-built docker container to do the deployment (Please do not use local terraform!)

## Destroying the Application
Similarly, use the pre-built docker container to do the destroy (Please do not use local terraform!)


