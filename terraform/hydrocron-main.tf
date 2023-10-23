
# SSM Parameter values
data "aws_ssm_parameter" "hydrocron-db-user" {
  name = "${local.hydrocrondb_resource_name}-user"
}

data "aws_ssm_parameter" "hydrocron-db-user-pass" {
  name = "${local.hydrocrondb_resource_name}-user-pass"
}

data "aws_ssm_parameter" "hydrocron-db-host" {
  name = "${local.hydrocrondb_resource_name}-host"
}

data "aws_ssm_parameter" "hydrocron-db-name" {
  name = "${local.hydrocrondb_resource_name}-name"
}

data "aws_ssm_parameter" "hydrocron-db-sg" {
  name = "${local.hydrocrondb_resource_name}-sg"
}



data "aws_ecr_authorization_token" "token" {}

locals {
  lambda_container_image_uri_split = split("/", var.lambda_container_image_uri)
  ecr_image_name_and_tag           = split(":", element(local.lambda_container_image_uri_split, length(local.lambda_container_image_uri_split) - 1))
  ecr_image_name                   = "${local.environment}-${element(local.ecr_image_name_and_tag, 0)}/hydrocron"
  ecr_image_tag                    = element(local.ecr_image_name_and_tag, 1)
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
    interpreter = ["/bin/bash", "-e", "-c"]
    command = <<EOF
      docker login ${data.aws_ecr_authorization_token.token.proxy_endpoint} -u AWS -p ${data.aws_ecr_authorization_token.token.password}
      EOF
  }
}

resource null_resource upload_ecr_image {
  depends_on = [null_resource.ecr_login]
  triggers = {
    image_uri = var.lambda_container_image_uri
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-e", "-c"]
    command = <<EOF
      docker pull ${var.lambda_container_image_uri}
      #docker tag ${var.lambda_container_image_uri} ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
      docker tag ${var.lambda_container_image_uri} ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
      #docker push ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
      docker push ${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}
      EOF
  }
}


resource "aws_lambda_function" "hydrocron_lambda_timeseries" {
  depends_on = [
    null_resource.upload_ecr_image
  ]

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda-image-repo.repository_url}:${local.ecr_image_tag}"
  image_config {
    command = ["hydrocron_api.controllers.timeseries.lambda_handler"]
  }
  function_name = "${local.lambda_resources_name}-hydrocron_lambda_timeseries"
  role          = aws_iam_role.hydrocron-service-role.arn
  timeout       = 5
  runtime       = "python3.8"

  vpc_config {
    subnet_ids = var.private_subnets
    security_group_ids = [var.default_vpc_sg]
  }

  environment {
    variables = {
      DB_HOST=data.aws_ssm_parameter.hydrocron-db-host.value
      DB_NAME=data.aws_ssm_parameter.hydrocron-db-name.value
      DB_USERNAME=data.aws_ssm_parameter.hydrocron-db-user.value
      DB_PASSWORD_SSM_NAME=data.aws_ssm_parameter.hydrocron-db-user-pass.name
    }
  }

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


#  API Gateway
resource "aws_api_gateway_rest_api" "hydrocron-api-gateway" {
  name        = "${local.ec2_resources_name}-api-gateway"
  description = "API to access Hydrocron"
  body        = templatefile(
                  "${path.module}/api-specification-templates/hydrocron_aws_api.yml",
                  {
                    hydrocron_api_lambda_arn_timeseries = aws_lambda_function.hydrocron_lambda_timeseries.invoke_arn
                    vpc_id = var.vpc_id
                  })
  parameters = {
    "basemap" = "split"
  }
  lifecycle {
    prevent_destroy = true
  }
}


resource "aws_api_gateway_deployment" "hydrocron-api-gateway-deployment" {
  rest_api_id = aws_api_gateway_rest_api.hydrocron-api-gateway.id
  stage_name  = "default"
  depends_on = [aws_api_gateway_rest_api.hydrocron-api-gateway]
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.hydrocron-api-gateway.body
    ]))
  }
}


resource "aws_cloudwatch_log_group" "hydrocron-api-gateway-logs" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.hydrocron-api-gateway.id}/${aws_api_gateway_deployment.hydrocron-api-gateway-deployment.stage_name}"
  retention_in_days = 60
}

output "url" {
  value = "${aws_api_gateway_deployment.hydrocron-api-gateway-deployment.invoke_url}/api"
}

resource "aws_ssm_parameter" "hydrocron-api-url" {
  name  = "hydrocron-api-url"
  type  = "String"
  value = aws_api_gateway_deployment.hydrocron-api-gateway-deployment.invoke_url
  overwrite = true
}
