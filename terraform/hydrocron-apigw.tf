#  API Gateway
locals {
  api_version = "v${split(".", var.app_version)[0]}"
}

resource "aws_api_gateway_rest_api" "hydrocron-api-gateway" {
  name        = "${local.aws_resource_prefix}-api-gateway"
  description = "API to access Hydrocron"
  body = templatefile(
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
  minimum_compression_size = 20480
}

resource "aws_api_gateway_rest_api_policy" "hydrocron-api-gateway-policy" {
  rest_api_id = aws_api_gateway_rest_api.hydrocron-api-gateway.id
  policy      = data.aws_iam_policy_document.apigw-resource-policy.json
  lifecycle {
    ignore_changes = [policy]
  }
}


resource "aws_api_gateway_deployment" "hydrocron-api-gateway-deployment" {
  rest_api_id = aws_api_gateway_rest_api.hydrocron-api-gateway.id
  depends_on  = [aws_api_gateway_rest_api.hydrocron-api-gateway]
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.hydrocron-api-gateway.body
    ]))
  }
  variables = {
    app_version = "${var.app_version}"
  }

  lifecycle {
    create_before_destroy = true
  }
}


resource "aws_api_gateway_stage" "hydrocron-api-gateway-stage" {
  deployment_id = aws_api_gateway_deployment.hydrocron-api-gateway-deployment.id
  rest_api_id   = aws_api_gateway_rest_api.hydrocron-api-gateway.id
  stage_name    = local.api_version
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.hydrocron-api-gateway-logs.arn
    format          = "$context.identity.sourceIp $context.identity.caller $context.identity.user [$context.requestTime] \"$context.httpMethod $context.resourcePath $context.protocol\" $context.status $context.responseLength $context.requestId $context.extendedRequestId"
  }
}


resource "aws_api_gateway_method_settings" "hydrocron-api-gateway-settings" {
  rest_api_id = aws_api_gateway_rest_api.hydrocron-api-gateway.id
  stage_name  = aws_api_gateway_stage.hydrocron-api-gateway-stage.stage_name
  method_path = "*/*"
  settings {
    metrics_enabled    = true
    logging_level      = "INFO"
    data_trace_enabled = true
  }
}


resource "aws_cloudwatch_log_group" "hydrocron-api-gateway-logs" {
  name              = "${local.aws_resource_prefix}/API-Gateway-Execution-Logs/${local.api_version}"
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
