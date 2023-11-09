#!/usr/bin/env bash

set -Eexo pipefail

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --ticket)
    ticket="$2"
    shift # past argument
    shift # past value
    ;;
    --app-version)
    app_version="$2"
    shift # past argument
    shift # past value
    ;;
    -v|--tf-venue)
    tf_venue="$2"
    case $tf_venue in
     sit|uat|ops) ;;
     *)
        echo "tf_venue must be sit, uat, or ops"
        exit 1;;
    esac
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

# https://www.terraform.io/docs/commands/environment-variables.html#tf_in_automation
TF_IN_AUTOMATION=true

# Verify that you are in test workspace
current_workspace=$(terraform workspace show)

if [ $current_workspace == ${ticket} ]; then
  # Terraform initialization
  terraform init -reconfigure -input=false -backend-config="bucket=podaac-services-${tf_venue}-terraform"
  terraform destroy -auto-approve -var-file=tfvars/"${tf_venue}".tfvars -var="app_version=${app_version}" -var="lambda_container_image_uri"=${lambda_container_image_uri}
  terraform workspace select default
  terraform workspace delete ${ticket}
else
  exit 1
fi