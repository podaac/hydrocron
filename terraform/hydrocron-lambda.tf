data "aws_ecr_authorization_token" "token" {}
data "aws_ecr_image" "lambda_image" {
  depends_on = [
    null_resource.upload_ecr_image
  ]
  repository_name = aws_ecr_repository.lambda-image-repo.name
  image_tag       = local.ecr_image_tag

}

locals {
  lambda_container_image_uri_split = split("/", var.lambda_container_image_uri)
  ecr_image_name_and_tag           = split(":", element(local.lambda_container_image_uri_split, length(local.lambda_container_image_uri_split) - 1))
  ecr_image_name                   = "${local.environment}-${element(local.ecr_image_name_and_tag, 0)}"
  ecr_image_tag                    = element(local.ecr_image_name_and_tag, 1)
  timeseries_function_name         = "${local.aws_resource_prefix}-timeseries-lambda"
  authorizer_function_name         = "${local.aws_resource_prefix}-authorizer-lambda"
  load_data_function_name          = "${local.aws_resource_prefix}-load_data-lambda"
  load_granule_function_name       = "${local.aws_resource_prefix}-load_granule-lambda"
  cnm_response_function_name       = "${local.aws_resource_prefix}-cnm-lambda"
  track_ingest_function_name       = "${local.aws_resource_prefix}-track-ingest-lambda"
  sit_env                          = var.stage == "sit" ? "SIT" : ""
  uat_env                          = var.stage == "uat" ? "UAT" : ""
  prod_env                         = var.stage == "ops" ? "PROD" : ""
}

resource "aws_ecr_repository" "lambda-image-repo" {
  name = local.ecr_image_name
  tags = var.default_tags
}

resource "null_resource" "ecr_login" {
  triggers = {
    image_uri = var.lambda_container_image_uri
  }

  provisioner "local-exec" {
    interpreter = ["/bin/sh", "-e", "-c"]
    command     = <<EOF
      docker login ${data.aws_ecr_authorization_token.token.proxy_endpoint} -u AWS -p ${data.aws_ecr_authorization_token.token.password}
      EOF
  }
}

resource "null_resource" "upload_ecr_image" {
  depends_on = [null_resource.ecr_login]
  triggers = {
    image_uri = var.lambda_container_image_uri
  }

  provisioner "local-exec" {
    interpreter = ["/bin/sh", "-e", "-c"]
    command     = <<EOF
      docker pull ${var.lambda_container_image_uri}
      docker tag ${var.lambda_container_image_uri} ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
      docker push ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
      EOF
  }
}


resource "aws_lambda_function" "hydrocron_lambda_timeseries" {
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda-image-repo.repository_url}:${data.aws_ecr_image.lambda_image.image_tag}"
  image_config {
    command = ["hydrocron.api.controllers.timeseries.lambda_handler"]
  }
  function_name = local.timeseries_function_name
  role          = aws_iam_role.hydrocron-lambda-execution-role.arn
  timeout       = 30
  vpc_config {
    subnet_ids         = data.aws_subnets.private_application_subnets.ids
    security_group_ids = data.aws_security_groups.vpc_default_sg.ids
  }
  environment {
    variables = {
      DEFAULT_COLLECTION_VERSION = "2.0"
      DEFAULT_LAKE_COLLECTION    = "SWOT_L2_HR_LakeSP"
      DEFAULT_RIVER_COLLECTION   = "SWOT_L2_HR_RiverSP"
    }
  }
  tags = var.default_tags
}


resource "aws_lambda_permission" "allow_hydrocron-timeseries" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hydrocron_lambda_timeseries.function_name
  principal     = "apigateway.amazonaws.com"
  # The /* part allows invocation from any stage, method and resource path
  # within API Gateway.
  source_arn = "${aws_api_gateway_rest_api.hydrocron-api-gateway.execution_arn}/*"
}

resource "null_resource" "api_key_hash" {
  /**
  This resource is needed because of https://github.com/podaac/hydrocron/issues/205#issuecomment-2250982988
   */
  triggers = {
    default_key      = aws_ssm_parameter.default-user-parameter.value
    trusted_key_list = aws_ssm_parameter.trusted-user-parameter.value
  }
}

resource "aws_lambda_function" "hydrocron_lambda_authorizer" {
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda-image-repo.repository_url}:${data.aws_ecr_image.lambda_image.image_tag}"
  image_config {
    command = ["hydrocron.api.controllers.authorizer.authorization_handler"]
  }
  function_name = local.authorizer_function_name
  role          = aws_iam_role.hydrocron-lambda-authorizer-role.arn
  timeout       = 30
  vpc_config {
    subnet_ids         = data.aws_subnets.private_application_subnets.ids
    security_group_ids = data.aws_security_groups.vpc_default_sg.ids
  }
  tags = var.default_tags

  /**
  This is the preferred solution in lieu of the nonsense below but when using replace_triggered_by, terraform plan fails
  to replace the lambda correctly and results in an error "ResourceConflictException: Function already exist"

  lifecycle { replace_triggered_by = [aws_ssm_parameter.default-user-parameter.value, aws_ssm_parameter.trusted-user-parameter.value]}
   */
  source_code_hash = null_resource.api_key_hash.id
}


resource "aws_lambda_function" "hydrocron_lambda_load_data" {
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda-image-repo.repository_url}:${data.aws_ecr_image.lambda_image.image_tag}"
  image_config {
    command = ["hydrocron.db.load_data.lambda_handler"]
  }
  function_name = local.load_data_function_name
  role          = aws_iam_role.hydrocron-lambda-load-data-role.arn
  timeout       = 600
  memory_size   = 512
  vpc_config {
    subnet_ids         = data.aws_subnets.private_application_subnets.ids
    security_group_ids = data.aws_security_groups.vpc_default_sg.ids
  }
  tags = var.default_tags
  environment {
    variables = {
      EARTHDATA_USERNAME           = data.aws_ssm_parameter.edl_username.value
      EARTHDATA_PASSWORD           = data.aws_ssm_parameter.edl_password.value
      GRANULE_LAMBDA_FUNCTION_NAME = aws_lambda_function.hydrocron_lambda_load_granule.function_name
      CMR_ENV                      = "${coalesce(local.sit_env, local.uat_env, local.prod_env)}"
    }
  }
}


resource "aws_lambda_function" "hydrocron_lambda_load_granule" {
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda-image-repo.repository_url}:${data.aws_ecr_image.lambda_image.image_tag}"
  image_config {
    command = ["hydrocron.db.load_data.granule_handler"]
  }
  function_name = local.load_granule_function_name
  role          = aws_iam_role.hydrocron-lambda-load-granule-role.arn
  timeout       = 900
  memory_size   = 8192
  vpc_config {
    subnet_ids         = data.aws_subnets.private_application_subnets.ids
    security_group_ids = data.aws_security_groups.vpc_default_sg.ids
  }
  tags = var.default_tags
  environment {
    variables = {
      OBSCURE_DATA = "false"
    }
  }
}

resource "aws_lambda_function" "hydrocron_lambda_cnm" {
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda-image-repo.repository_url}:${data.aws_ecr_image.lambda_image.image_tag}"
  image_config {
    command = ["hydrocron.db.load_data.cnm_handler"]
  }
  function_name = local.cnm_response_function_name
  role          = aws_iam_role.hydrocron-lambda-cnm-role.arn
  timeout       = 600
  memory_size   = 2048

  tags = var.default_tags
  environment {
    variables = {
      GRANULE_LAMBDA_FUNCTION_NAME = aws_lambda_function.hydrocron_lambda_load_granule.function_name
    }
  }
}

resource "aws_lambda_permission" "allow_lambda" {
  statement_id  = "AllowExecutionFromLambda"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hydrocron_lambda_load_granule.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_lambda_function.hydrocron_lambda_load_data.arn
}

resource "aws_lambda_permission" "allow_lambda_from_cnm" {
  statement_id  = "AllowExecutionFromLambdaCNM"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hydrocron_lambda_load_granule.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_lambda_function.hydrocron_lambda_cnm.arn
}


resource "aws_lambda_function" "hydrocron_lambda_track_ingest" {
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda-image-repo.repository_url}:${data.aws_ecr_image.lambda_image.image_tag}"
  image_config {
    command = ["hydrocron.db.track_ingest.track_ingest_handler"]
  }
  function_name = local.track_ingest_function_name
  role          = aws_iam_role.hydrocron_lambda_track_ingest_role.arn
  timeout       = 900
  memory_size   = 512

  tags = var.default_tags
  environment {
    variables = {
      GRANULE_LAMBDA_FUNCTION_NAME = aws_lambda_function.hydrocron_lambda_load_granule.function_name
      HYDROCRON_ENV                = local.environment
      EARTHDATA_USERNAME           = data.aws_ssm_parameter.edl_username.value
      EARTHDATA_PASSWORD           = data.aws_ssm_parameter.edl_password.value
      DEBUG_LOGS                   = 0
      BATCH_STATUS                 = 500
      COUNTER_RANGE                = 10
    }
  }
}
