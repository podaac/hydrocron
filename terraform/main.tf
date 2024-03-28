provider "aws" {
  region = "us-west-2"

  ignore_tags {
    key_prefixes = ["gsfc-ngap"]
  }

  default_tags {
    tags = local.default_tags
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_vpc" "default" {
  tags = {
    "Name" : "Application VPC"
  }
}

data "aws_security_groups" "vpc_default_sg" {
  filter {
    name   = "group-name"
    values = ["default"]
  }
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_subnet" "private_application_subnet" {
  for_each = toset(data.aws_subnets.private_application_subnets.ids)
  id       = each.value
}

data "aws_subnets" "private_application_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name   = "tag:Name"
    values = ["Private application*"]
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
  region = data.aws_region.current.name

  # This is the convention we use to know what belongs to each other
  aws_resource_prefix = terraform.workspace == "default" ? "svc-${var.app_name}-${local.environment}" : "svc-${var.app_name}-${local.environment}-${terraform.workspace}"

  default_tags = length(var.default_tags) == 0 ? {
    team : "TVA",
    application : var.app_name,
    Environment = var.stage
    Version     = var.app_version
  } : var.default_tags
}
