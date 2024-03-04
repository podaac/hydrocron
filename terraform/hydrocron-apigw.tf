#  API Gateway
locals {
  api_version = "v${split(".", var.app_version)[0]}"
}

resource "aws_api_gateway_rest_api" "hydrocron-api-gateway" {
  name        = "${local.aws_resource_prefix}-api-gateway"
  description = "API to access Hydrocron"
  body        = templatefile(
    "${path.module}/api-specification-templates/hydrocron_aws_api.yml",
    {
      hydrocron_api_lambda_arn_timeseries = aws_lambda_function.hydrocron_lambda_timeseries.invoke_arn
      api_version                         = local.api_version
      software_version                    = var.app_version
    })
  parameters = {
    "basepath" = "ignore"
  }

  endpoint_configuration {
    types = ["PRIVATE"]
  }
  policy = ""

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_api_gateway_rest_api_policy" "test" {
  rest_api_id = aws_api_gateway_rest_api.hydrocron-api-gateway.id
  policy      = data.aws_iam_policy_document.apigw-resource-policy.json
}


resource "aws_api_gateway_deployment" "hydrocron-api-gateway-deployment" {
  rest_api_id = aws_api_gateway_rest_api.hydrocron-api-gateway.id
  stage_name  = local.api_version
  depends_on  = [aws_api_gateway_rest_api.hydrocron-api-gateway]
  triggers    = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.hydrocron-api-gateway.body
    ]))
  }
}


resource "aws_cloudwatch_log_group" "hydrocron-api-gateway-logs" {
  name              = "${local.aws_resource_prefix}/API-Gateway-Execution-Logs/${aws_api_gateway_deployment.hydrocron-api-gateway-deployment.stage_name}"
  retention_in_days = 60
}

output "url" {
  value = "${aws_api_gateway_deployment.hydrocron-api-gateway-deployment.invoke_url}/api"
}

resource "aws_ssm_parameter" "hydrocron-api-url" {
  name  = "/service/${var.app_name}/api-url"
  type  = "String"
  value = aws_api_gateway_deployment.hydrocron-api-gateway-deployment.invoke_url
}
