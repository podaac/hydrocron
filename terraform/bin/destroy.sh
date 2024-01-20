#!/usr/bin/env bash

set -Eexo pipefail

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --ticket)
    ticket="$2"
    shift
    shift
    ;;
    --app-version)
    app_version="$2"
    shift
    shift
    ;;
    -v|--tf-venue)
    tf_venue="$2"
    case $tf_venue in
     sit|uat|ops) ;;
     *)
        echo "tf_venue must be sit, uat, or ops"
        exit 1;;
    esac
    shift
    shift
    ;;
    *)
    POSITIONAL+=("$1")
    shift
    ;;
esac
done
set -- "${POSITIONAL[@]}"

# https://www.terraform.io/docs/commands/environment-variables.html#tf_in_automation
TF_IN_AUTOMATION=true

current_workspace=$(terraform workspace show)

if [ $current_workspace == ${ticket} ]; then
  terraform init -reconfigure -input=false -backend-config="bucket=podaac-services-${tf_venue}-terraform"
  terraform destroy -auto-approve -var-file=tfvars/"${tf_venue}".tfvars -var="app_version=${app_version}" -var="lambda_container_image_uri"=${lambda_container_image_uri}
  terraform workspace select default
  terraform workspace delete ${ticket}
else
  exit 1
fi