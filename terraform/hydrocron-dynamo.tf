resource "aws_dynamodb_table" "hydrocron-swot-reach-table" {
  name           = "hydrocron-swot-reach-table"
  read_capacity  = "30"
  write_capacity = "30"
  hash_key       = "reach_id"
  range_key      = "range_start_time"
  attribute {
    name = "reach_id"
    type = "S"
  }
  attribute {
    name = "range_start_time"
    type = "S"
  }
  lifecycle { ignore_changes = [write_capacity, read_capacity] }
}

module "reach_table_autoscaling" {
  source     = "snowplow-devops/dynamodb-autoscaling/aws"
  table_name = aws_dynamodb_table.hydrocron-swot-reach-table.name
}

resource "aws_dynamodb_table" "hydrocron-swot-node-table" {
  name           = "hydrocron-swot-node-table"
  read_capacity  = "30"
  write_capacity = "30"
  hash_key       = "node_id"
  range_key      = "range_start_time"
  attribute {
    name = "node_id"
    type = "S"
  }
  attribute {
    name = "range_start_time"
    type = "S"
  }
}

module "node_table_autoscaling" {
  source     = "snowplow-devops/dynamodb-autoscaling/aws"
  table_name = aws_dynamodb_table.hydrocron-swot-node-table.name
}
