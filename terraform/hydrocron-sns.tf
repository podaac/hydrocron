# SNS topic for CNM responses
resource "aws_sns_topic" "hydrocron_sns_topic_cnm_response" {
  name         = "${local.aws_resource_prefix}-cnm-response"
}


resource "aws_sns_topic_policy" "hydrocron_sns_topic_cnm_response_policy" {
  arn = aws_sns_topic.hydrocron_sns_topic_cnm_response.arn
  policy = data.aws_iam_policy_document.sns-resource-policy.json
}

