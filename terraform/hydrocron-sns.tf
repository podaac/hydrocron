# SNS topic for CNM responses
resource "aws_sns_topic" "hydrocron_sns_topic_cnm_response" {
  name         = "${local.aws_resource_prefix}-cnm-response"
}


resource "aws_sns_topic_policy" "hydrocron_sns_topic_cnm_response_policy" {
  arn = aws_sns_topic.hydrocron_sns_topic_cnm_response.arn
  policy = data.aws_iam_policy_document.sns-resource-policy.json
}

resource "aws_sns_topic_subscription" "hydrocron_cnm_sqs_target" {
  topic_arn = aws_sns_topic.hydrocron_sns_topic_cnm_response.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.hydrocron_sqs_queue_granule_ingest.arn
}