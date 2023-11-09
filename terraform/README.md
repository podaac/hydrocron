
# Deploying HYDROCRON

Hydrocron is an API Gateway REST API which can be deployed to AWS via terraform.

## Using GitHub Actions (Preferred)

The `Build` GitHub action is setup to allow deployments via workflow dispatch to 
the SIT environment from branches that match the following patterns:

- develop
- feature/*
- issue/*
- issues/*

If your work is being done on a feature or issue branch, the easiest way to deploy is
to use the [workflow dispatch](https://github.com/podaac/hydrocron/actions/workflows/build.yml) 
option and specify the `SIT` environment. Contact project members if access is required. 

## Using Local Terraform

> [!IMPORTANT]  
> If deploying manually from a development laptop, make sure the version
of terraform installed locally matches the version used by CICD (see `TERRAFORM_VERSION`
in [build.yml](../.github/workflows/build.yml))

_TODO: Instructions for deploying to LocalStack?_

### Requirements

In order to deploy the application you will need:

- Docker
- Terraform 
  - **Make sure version matches `TERRAFORM_VERSION` in [build.yml](../.github/workflows/build.yml)!**
- AWS credentials

### Building the lambda images
The lambda code needs to be built into a deployable image and uploaded to 
ECR before running terraform. Normally CI/CD handles this task but if you 
are trying to run terraform locally it needs to be done manually.

Follow the instructions in the [README](../README.md) to build the image


### Deploying via Terraform

```bash
export tf_venue=sit
# Needs to point to a valid AWS credential profile. This is an example
export AWS_DEFAULT_PROFILE=ngap-service-${tf_venue}
# Should match the current build version of the software
export app_version=1.0.0a9
# If using a local docker image, needs to match a tag present on your laptop. 
# Additionally, if using local image, comment out the docker pull command in the null_resource.upload_ecr_image otherwise the apply will fail 
# If using an image from ghcr.io, should use the full uri that can be used with docker pull
export lambda_container_image_uri=hydrocron:1.0.0a9

# The backend configuration here is a podaac convention 
terraform init -reconfigure -input=false -backend-config="bucket=podaac-services-${tf_venue}-terraform"
terraform plan -input=false -var-file=tfvars/"${tf_venue}".tfvars -var="app_version=${app_version}" -var="lambda_container_image_uri"=${lambda_container_image_uri} -out="tfplan"
terraform apply -input=false -auto-approve tfplan
```
