
provider "aws" {
  region = "us-west-2"
  shared_credentials_file = var.credentials
  profile = var.profile

  ignore_tags {
    key_prefixes = ["gsfc-ngap"]
  }
}

data "local_file" "pyproject_toml" {
  filename = abspath("${path.root}/../pyproject.toml")
}

locals {
  name        = regex("name = \"(\\S*)\"", data.local_file.pyproject_toml.content)[0]
  version     = regex("version = \"(\\S*)\"", data.local_file.pyproject_toml.content)[0]
  environment = var.stage
  lambda_resources_name = terraform.workspace == "default" ? "svc-${local.name}-${local.environment}" : "svc-${local.name}-${local.environment}-${terraform.workspace}"

  app_prefix      = "service-${var.app_name}-${local.environment}"
  service_prefix  = "service-${var.app_name}-${local.environment}-${var.service_name}"
  service_path    = "/service/${var.app_name}/${var.service_name}"
  
  account_id = data.aws_caller_identity.current.account_id

  # This is the convention we use to know what belongs to each other
  ec2_resources_name = "service-${local.name}-${local.environment}"

  # Used to refer to the HYDROCRON database resources by the same convention
  hydrocrondb_resource_name = "service-${var.db_app_name}-${local.environment}"

  default_tags = length(var.default_tags) == 0 ? {
    team = "TVA"
    application = local.app_prefix
    version     = local.version
    Environment = local.environment
  } : var.default_tags
}

data "aws_caller_identity" "current" {}