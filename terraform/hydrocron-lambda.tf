data "aws_ecr_authorization_token" "token" {}
data aws_ecr_image lambda_image {
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
  load_data_function_name          = "${local.aws_resource_prefix}-load_data-lambda"
  load_granule_function_name       = "${local.aws_resource_prefix}-load_granule-lambda"
  cnm_response_function_name       = "${local.aws_resource_prefix}-cnm-lambda"
}

resource aws_ecr_repository "lambda-image-repo" {
  name = local.ecr_image_name
  tags = var.default_tags
}

resource null_resource ecr_login {
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

resource null_resource upload_ecr_image {
  depends_on = [null_resource.ecr_login]
  triggers   = {
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
      EARTHDATA_USERNAME = data.aws_ssm_parameter.edl_username.value
      EARTHDATA_PASSWORD = data.aws_ssm_parameter.edl_password.value
      GRANULE_LAMBDA_FUNCTION_NAME = aws_lambda_function.hydrocron_lambda_load_granule.function_name
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
  timeout       = 600
  memory_size   = 2048
  vpc_config {
    subnet_ids         = data.aws_subnets.private_application_subnets.ids
    security_group_ids = data.aws_security_groups.vpc_default_sg.ids
  }
  tags = var.default_tags
  environment {
    variables = {
      EARTHDATA_USERNAME = data.aws_ssm_parameter.edl_username.value
      EARTHDATA_PASSWORD = data.aws_ssm_parameter.edl_password.value
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
  source_arn = aws_lambda_function.hydrocron_lambda_load_data.arn
}

resource "aws_lambda_permission" "allow_lambda_from_cnm" {
  statement_id  = "AllowExecutionFromLambdaCNM"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hydrocron_lambda_load_granule.function_name
  principal     = "sns.amazonaws.com"
  source_arn = aws_lambda_function.hydrocron_lambda_cnm.arn
}
