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
    --lambda_container_image_uri)
    lambda_container_image_uri="$2"
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

terraform init -reconfigure -input=false -backend-config="bucket=podaac-services-${tf_venue}-terraform"

if [[ "${ticket}" ]]; then
  set +e
  terraform workspace new "${ticket}"
  set -e
  terraform workspace select "${ticket}"
else
  terraform workspace select default
fi

terraform plan -input=false -var-file=tfvars/"${tf_venue}".tfvars -var="app_version=${app_version}" -var="lambda_container_image_uri"=${lambda_container_image_uri} -out="tfplan"

terraform apply -input=false -auto-approve tfplan