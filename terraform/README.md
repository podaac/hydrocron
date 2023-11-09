
# Deploying HYDROCRON

Hydrocron is an API Gateway REST API which can be deployed to AWS via terraform.

## Requirements

In order to deploy the application you will need:

- Docker
- Terraform
- AWS credentials

## Building the lambda images
The lambda code needs to be built into a deployable image and uploaded to 
ECR before running terraform. Normally CI/CD handles this task but if you 
are trying to run terraform locally it needs to be done manually.

Follow the instructions in the [README](../README.md) to build the image


## Deploying via Terraform

```bash
export tf_venue=sit
export aws_profile=ngap-service-${tf_venue}

docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock -v ${HOME}/.aws/:/usr/local/.aws -v $(pwd):/hydrocron -w /hydrocron/terraform -e AWS_SHARED_CREDENTIALS_FILE=/usr/local/.aws/credentials -e AWS_CONFIG_FILE=/usr/local/.aws/config -e AWS_PROFILE=${aws_profile} -e tf_venue=${tf_venue} -e TF_VAR_stage=${tf_venue} -e TF_VAR_region=us-west-2 -e TF_INPUT=false --entrypoint=/bin/sh hashicorp/terraform:1.3.7

export app_version=1.0.0a9
export lambda_container_image_uri=hydrocron:1.0.0a9

terraform init -reconfigure -input=false -backend-config="bucket=podaac-services-${tf_venue}-terraform"
terraform plan -input=false -var-file=tfvars/"${tf_venue}".tfvars -var="app_version=${app_version}" -var="lambda_container_image_uri"=${lambda_container_image_uri} -out="tfplan"
terraform apply -input=false -auto-approve tfplan
```
