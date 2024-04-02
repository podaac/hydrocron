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
  attribute {
    name = "granuleUR"
    type = "S"
  }
  attribute {
    name = "collection_shortname"
    type = "S"
  }
  attribute {
    name = "collection_version"
    type = "S"
  }
  attribute {
    name = "ingest_time"
    type = "S"
  }
  global_secondary_index {
    name               = "GranuleURIndex"
    hash_key           = "granuleUR"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["reach_id", "collection_shortname", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  global_secondary_index {
    name               = "CollectionNameIndex"
    hash_key           = "collection_shortname"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["reach_id", "granuleUR", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  global_secondary_index {
    name               = "CollectionVersionIndex"
    hash_key           = "collection_version"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["reach_id", "collection_shortname", "granuleUR", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }

  global_secondary_index {
    name               = "IngestTimeIndex"
    hash_key           = "ingest_time"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["reach_id", "collection_shortname", "granuleUR", "crid", "cycle_id", "pass_id", "continent_id", "collection_version"]
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
  attribute {
    name = "granuleUR"
    type = "S"
  }
  attribute {
    name = "collection_shortname"
    type = "S"
  }
  attribute {
    name = "collection_version"
    type = "S"
  }
  attribute {
    name = "ingest_time"
    type = "S"
  }
  global_secondary_index {
    name               = "GranuleURIndex"
    hash_key           = "granuleUR"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["node_id", "collection_shortname", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  global_secondary_index {
    name               = "CollectionNameIndex"
    hash_key           = "collection_shortname"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["node_id", "granuleUR", "collection_version", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }
  global_secondary_index {
    name               = "CollectionVersionIndex"
    hash_key           = "collection_version"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["node_id", "collection_shortname", "granuleUR", "crid", "cycle_id", "pass_id", "continent_id", "ingest_time"]
  }

  global_secondary_index {
    name               = "IngestTimeIndex"
    hash_key           = "ingest_time"
    range_key          = "range_start_time"
    projection_type    = "INCLUDE"
    non_key_attributes = ["node_id", "collection_shortname", "granuleUR", "crid", "cycle_id", "pass_id", "continent_id", "collection_version"]
  }
}
