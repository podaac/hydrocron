resource "aws_dynamodb_table" "hydrocron-swot-reach-table" {
  name           = "hydrocron-swot-reach-table"
  billing_mode   = "PAY_PER_REQUEST"
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

}

resource "aws_dynamodb_table" "hydrocron-swot-node-table" {
  name           = "hydrocron-swot-node-table"
  billing_mode   = "PAY_PER_REQUEST"
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

