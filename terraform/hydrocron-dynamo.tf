resource "aws_dynamodb_table" "hydrocron-swot-reach-table" {
    name = "hydrocron-swot-reach-table"
    billing_mode = "PROVISIONED"
    read_capacity= "30"
    write_capacity= "30"
    attribute {
        name = "reach_id"
        type = "S"
    }
    attribute {
        name = "range_start_time"
        type = "S"
    }
    hash_key = "reach_id"
    global_secondary_index {
        name            = "range_start_time"
        hash_key        = "range_start_time"
        write_capacity  = 1
        read_capacity   = 1
        projection_type = "ALL"
    }
    ttl {
     enabled = true
     attribute_name = "expiryPeriod"
    }
    point_in_time_recovery { enabled = true }
    server_side_encryption { enabled = true }
    lifecycle { ignore_changes = [ write_capacity, read_capacity ] }
}

module  "table_autoscaling" {
   source = "snowplow-devops/dynamodb-autoscaling/aws"
   table_name = aws_dynamodb_table.hydrocron-swot-reach-table.name
}
