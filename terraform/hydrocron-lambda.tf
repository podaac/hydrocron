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

  tags = var.default_tags
}


resource "aws_lambda_permission" "allow_hydrocron-timeseries" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hydrocron_lambda_timeseries.function_name
  principal     = "apigateway.amazonaws.com"

  # The "/*/*/*" portion grants access from any method on any resource
  # within the API Gateway REST API.
  source_arn = "${aws_api_gateway_rest_api.hydrocron-api-gateway.execution_arn}/*/*/*"
}


resource "aws_lambda_function" "hydrocron_lambda_load_data" {
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda-image-repo.repository_url}:${data.aws_ecr_image.lambda_image.image_tag}"
  image_config {
    command = ["hydrocron.db.load_data.lambda_handler"]
  }
  function_name = local.load_data_function_name
  role          = aws_iam_role.hydrocron-lambda-load-data-role.arn
  timeout       = 120
  memory_size   = 512

  tags = var.default_tags
  environment {
    variables = {
      EARTHDATA_USERNAME = data.aws_ssm_parameter.edl_username.value
      EARTHDATA_PASSWORD = data.aws_ssm_parameter.edl_password.value
    }
  }
}