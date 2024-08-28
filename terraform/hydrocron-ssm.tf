resource "aws_ssm_parameter" "hydrocron-api-url" {
  name  = "/service/${var.app_name}/api-url"
  type  = "String"
  value = aws_api_gateway_deployment.hydrocron-api-gateway-deployment.invoke_url
}


resource "aws_ssm_parameter" "default-user-parameter" {
  name        = "/service/${var.app_name}/api-key-default"
  description = "Hydrocron default user API key"
  type        = "SecureString"
  value       = aws_api_gateway_api_key.default-user-key.value
}


resource "aws_ssm_parameter" "trusted-user-parameter" {
  name        = "/service/${var.app_name}/api-key-trusted"
  description = "Hydrocron trusted user API key"
  type        = "SecureString"
  value = jsonencode(
    [
      "${aws_api_gateway_api_key.confluence-user-key.value}"
    ]
  )
}


resource "aws_ssm_parameter" "hydrocron-track-ingest-runtime" {
  name        = "/service/${var.app_name}/track-ingest-runtime"
  description = "Hydrocron track ingest last time executed"
  type        = "String"
  value       = "no_data"
}