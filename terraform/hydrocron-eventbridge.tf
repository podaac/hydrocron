resource "aws_scheduler_schedule" "aws_schedule_reach" {
  name       = "${local.aws_resource_prefix}-reach-track-ingest-schedule"
  group_name = "default"
  flexible_time_window {
    mode = "OFF"
  }
  schedule_expression = "cron(0 23 ? * SUN *)"
  state               = "DISABLED"
  target {
    arn      = aws_lambda_function.hydrocron_lambda_track_ingest.arn
    role_arn = aws_iam_role.hydrocron_schedule_role.arn
    input = jsonencode({
      "collection_shortname" : "SWOT_L2_HR_RiverSP_reach_2.0",
      "hydrocron_table" : "${aws_dynamodb_table.hydrocron-swot-reach-table.name}",
      "hydrocron_track_table" : "${aws_dynamodb_table.hydrocron-reach-track-ingest-table.name}",
      "collection_start_date" : "2024-11-01T00:00:00",
      "reprocessed_crid": "PGC0"
    })
  }
}


resource "aws_scheduler_schedule" "aws_schedule_node" {
  name       = "${local.aws_resource_prefix}-node-track-ingest-schedule"
  group_name = "default"
  flexible_time_window {
    mode = "OFF"
  }
  schedule_expression = "cron(5 23 ? * SUN *)"
  state               = "DISABLED"
  target {
    arn      = aws_lambda_function.hydrocron_lambda_track_ingest.arn
    role_arn = aws_iam_role.hydrocron_schedule_role.arn
    input = jsonencode({
      "collection_shortname" : "SWOT_L2_HR_RiverSP_node_2.0",
      "hydrocron_table" : "${aws_dynamodb_table.hydrocron-swot-node-table.name}",
      "hydrocron_track_table" : "${aws_dynamodb_table.hydrocron-node-track-ingest-table.name}",
      "collection_start_date" : "2024-11-01T00:00:00",
      "reprocessed_crid": "PGC0"
    })
  }
}


resource "aws_scheduler_schedule" "aws_schedule_prior_lake" {
  name       = "${local.aws_resource_prefix}-prior-lake-track-ingest-schedule"
  group_name = "default"
  flexible_time_window {
    mode = "OFF"
  }
  schedule_expression = "cron(10 23 ? * SUN *)"
  state               = "DISABLED"
  target {
    arn      = aws_lambda_function.hydrocron_lambda_track_ingest.arn
    role_arn = aws_iam_role.hydrocron_schedule_role.arn
    input = jsonencode({
      "collection_shortname" : "SWOT_L2_HR_LakeSP_prior_2.0",
      "hydrocron_table" : "${aws_dynamodb_table.hydrocron-swot-prior-lake-table.name}",
      "hydrocron_track_table" : "${aws_dynamodb_table.hydrocron-priorlake-track-ingest-table.name}",
      "collection_start_date" : "2024-11-01T00:00:00",
      "reprocessed_crid": "PGC0"
    })
  }
}