resource "aws_dynamodb_table" "hydrocron-swot-reach-table" {
  name         = "hydrocron-swot-reach-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "reach_id"
  range_key    = "range_start_time"
  attribute {
    name = "reach_id"
    type = "S"
  }
  attribute {
    name = "range_start_time"
    type = "S"
  }
  attribute {
    name = "granuleUR"
    type = "S"
  }
  global_secondary_index {
    name               = "GranuleURIndex"
    hash_key           = "granuleUR"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["reach_id", "collection_shortname", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-SWOT_L2_HR_RiverSP_D-reach-table" {
  name         = "hydrocron-SWOT_L2_HR_RiverSP_D-reach-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "reach_id"
  range_key    = "range_start_time"
  attribute {
    name = "reach_id"
    type = "S"
  }
  attribute {
    name = "range_start_time"
    type = "S"
  }
  attribute {
    name = "granuleUR"
    type = "S"
  }
  global_secondary_index {
    name               = "GranuleURIndex"
    hash_key           = "granuleUR"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["reach_id", "collection_shortname", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-swot-node-table" {
  name         = "hydrocron-swot-node-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "node_id"
  range_key    = "range_start_time"
  attribute {
    name = "node_id"
    type = "S"
  }
  attribute {
    name = "range_start_time"
    type = "S"
  }
  attribute {
    name = "granuleUR"
    type = "S"
  }

  global_secondary_index {
    name               = "GranuleURIndex"
    hash_key           = "granuleUR"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["node_id", "collection_shortname", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-SWOT_L2_HR_RiverSP_D-node-table" {
  name         = "hydrocron-SWOT_L2_HR_RiverSP_D-node-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "node_id"
  range_key    = "range_start_time"
  attribute {
    name = "node_id"
    type = "S"
  }
  attribute {
    name = "range_start_time"
    type = "S"
  }
  attribute {
    name = "granuleUR"
    type = "S"
  }

  global_secondary_index {
    name               = "GranuleURIndex"
    hash_key           = "granuleUR"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["node_id", "collection_shortname", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-swot-prior-lake-table" {
  name         = "hydrocron-swot-prior-lake-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "lake_id"
  range_key    = "range_start_time"
  attribute {
    name = "lake_id"
    type = "S"
  }
  attribute {
    name = "range_start_time"
    type = "S"
  }
  attribute {
    name = "granuleUR"
    type = "S"
  }

  global_secondary_index {
    name               = "GranuleURIndex"
    hash_key           = "granuleUR"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["lake_id", "collection_shortname", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-SWOT_L2_HR_LakeSP_D-prior-lake-table" {
  name         = "hydrocron-SWOT_L2_HR_LakeSP_D-prior-lake-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "lake_id"
  range_key    = "range_start_time"
  attribute {
    name = "lake_id"
    type = "S"
  }
  attribute {
    name = "range_start_time"
    type = "S"
  }
  attribute {
    name = "granuleUR"
    type = "S"
  }

  global_secondary_index {
    name               = "GranuleURIndex"
    hash_key           = "granuleUR"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["lake_id", "collection_shortname", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-reach-track-ingest-table" {
  name         = "hydrocron-swot-reach-track-ingest-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "granuleUR"
  range_key    = "revision_date"
  attribute {
    name = "granuleUR"
    type = "S"
  }
  attribute {
    name = "revision_date"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }
  global_secondary_index {
    name            = "statusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-SWOT_L2_HR_RiverSP_D-reach-track-ingest-table" {
  name         = "hydrocron-SWOT_L2_HR_RiverSP_D-reach-track-ingest"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "granuleUR"
  range_key    = "revision_date"
  attribute {
    name = "granuleUR"
    type = "S"
  }
  attribute {
    name = "revision_date"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }
  global_secondary_index {
    name            = "statusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-node-track-ingest-table" {
  name         = "hydrocron-swot-node-track-ingest-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "granuleUR"
  range_key    = "revision_date"
  attribute {
    name = "granuleUR"
    type = "S"
  }
  attribute {
    name = "revision_date"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }
  global_secondary_index {
    name            = "statusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-SWOT_L2_HR_RiverSP_D-node-track-ingest-table" {
  name         = "hydrocron-SWOT_L2_HR_RiverSP_D-node-track-ingest"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "granuleUR"
  range_key    = "revision_date"
  attribute {
    name = "granuleUR"
    type = "S"
  }
  attribute {
    name = "revision_date"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }
  global_secondary_index {
    name            = "statusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-priorlake-track-ingest-table" {
  name         = "hydrocron-swot-prior-lake-track-ingest-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "granuleUR"
  range_key    = "revision_date"
  attribute {
    name = "granuleUR"
    type = "S"
  }
  attribute {
    name = "revision_date"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }
  global_secondary_index {
    name            = "statusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}

resource "aws_dynamodb_table" "hydrocron-SWOT_L2_HR_LakeSP_D-prior-lake-track-ingest-table" {
  name         = "hydrocron-SWOT_L2_HR_LakeSP_D-prior-lake-track-ingest"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "granuleUR"
  range_key    = "revision_date"
  attribute {
    name = "granuleUR"
    type = "S"
  }
  attribute {
    name = "revision_date"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }
  global_secondary_index {
    name            = "statusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }
  point_in_time_recovery {
    enabled = var.stage == "ops" ? true : false
  }
}