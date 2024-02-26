# SNS topic for CNM responses
resource "aws_sns_topic" "hydrocron_sns_topic_cnm_response" {
  name         = "${var.app_name}-cnm-response"
  display_name = "${var.app_name}-cnm-response"
}


resource "aws_sns_topic_policy" "hydrocron_sns_topic_cnm_response_policy" {
  arn = aws_sns_topic.hydrocron_sns_topic_cnm_response.arn
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "CumulusSitAccountPublish",
        "Effect" : "Allow",
        "Principal" : {
          "AWS" : "arn:aws:iam::${var.stage}:root"
        },
        "Action" : "sns:Publish",
        "Resource" : "${aws_sns_topic.hydrocron_sns_topic_cnm_response.arn}"
      }
    ]
  })
}