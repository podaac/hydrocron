# Dead letter queue for failed CNM messages
resource "aws_sqs_queue" "hydrocron_cnm_dlq" {
  name                      = "${local.aws_resource_prefix}-cnm-dlq"
  message_retention_seconds = 1209600 # 14 days
  tags                      = var.default_tags
}

# SQS queue between SNS and the CNM Lambda
resource "aws_sqs_queue" "hydrocron_cnm_queue" {
  name                       = "${local.aws_resource_prefix}-cnm-queue"
  visibility_timeout_seconds = 660 # Lambda timeout (600s) + buffer
  message_retention_seconds  = 86400
  tags                       = var.default_tags

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.hydrocron_cnm_dlq.arn
    maxReceiveCount     = 2
  })
}

# Allow SNS to send messages to the SQS queue
resource "aws_sqs_queue_policy" "hydrocron_cnm_queue_policy" {
  queue_url = aws_sqs_queue.hydrocron_cnm_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "sns.amazonaws.com" }
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.hydrocron_cnm_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.hydrocron_sns_topic_cnm_response.arn
          }
        }
      }
    ]
  })
}

# Lambda event source mapping: SQS -> CNM Lambda
resource "aws_lambda_event_source_mapping" "hydrocron_cnm_sqs_trigger" {
  event_source_arn = aws_sqs_queue.hydrocron_cnm_queue.arn
  function_name    = aws_lambda_function.hydrocron_lambda_cnm.arn
  batch_size       = 1
}
