# Granule ingest
resource "aws_sqs_queue" "hydrocron_sqs_queue_granule_ingest" {
  name                       = "${local.aws_resource_prefix}-sqs-granule_ingest"
  visibility_timeout_seconds = 5400
}

resource "aws_sqs_queue_policy" "hydrocron_sqs_queue_policy_granule_ingest" {
  queue_url = aws_sqs_queue.hydrocron_sqs_queue_granule_ingest.id
  policy = aws_iam_policy_document.sqs-resource-policy.json
}