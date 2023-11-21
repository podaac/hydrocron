provider "aws" {
  region = "us-west-2"

  ignore_tags {
    key_prefixes = ["gsfc-ngap"]
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_vpc" "default" {
  tags = {
    "Name" : "Application VPC"
  }
}

data "aws_ssm_parameter" "edl_username" {
  name = "urs_podaaccloud_user"
}
data "aws_ssm_parameter" "edl_password" {
  name = "urs_podaaccloud_pass"
  with_decryption = true
}

locals {
  environment = var.stage
  account_id  = data.aws_caller_identity.current.account_id

  # This is the convention we use to know what belongs to each other
  aws_resource_prefix = terraform.workspace == "default" ? "svc-${var.app_name}-${local.environment}" : "svc-${var.app_name}-${local.environment}-${terraform.workspace}"

  default_tags = length(var.default_tags) == 0 ? {
    team : "TVA",
    application : var.app_name,
    Environment = var.stage
    Version     = var.app_version
  } : var.default_tags
}
