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
      "${aws_api_gateway_api_key.confluence-user-key.value}",
      "${aws_api_gateway_api_key.fathom-user-key.value}",
      "${aws_api_gateway_api_key.umass-user-key.value}"
    ]
  )
}


resource "aws_ssm_parameter" "hydrocron-reach-track-ingest-runtime" {
  name        = "/service/${var.app_name}/track-ingest-runtime/SWOT_L2_HR_RiverSP_reach_D"
  description = "Hydrocron track ingest last time executed on reaches"
  type        = "String"
  value       = "no_data"
}


resource "aws_ssm_parameter" "hydrocron-node-track-ingest-runtime" {
  name        = "/service/${var.app_name}/track-ingest-runtime/SWOT_L2_HR_RiverSP_node_D"
  description = "Hydrocron track ingest last time executed on nodes"
  type        = "String"
  value       = "no_data"
}


resource "aws_ssm_parameter" "hydrocron-priorlake-track-ingest-runtime" {
  name        = "/service/${var.app_name}/track-ingest-runtime/SWOT_L2_HR_LakeSP_prior_D"
  description = "Hydrocron track ingest last time executed on lakes"
  type        = "String"
  value       = "no_data"
}
