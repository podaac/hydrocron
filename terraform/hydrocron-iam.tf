# IAM Policies
data "aws_iam_policy_document" "assume_role_lambda" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}


data "aws_iam_policy_document" "assume_role_authorizer" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}


data "aws_iam_policy_document" "dynamo-read-policy" {

  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:BatchGetItem",
      "dynamodb:Scan",
      "dynamodb:Query",
      "dynamodb:ConditionCheckItem",
      "dynamodb:DescribeTable"
    ]

    resources = [
      aws_dynamodb_table.hydrocron-swot-node-table.arn,
      "${aws_dynamodb_table.hydrocron-swot-node-table.arn}/index/*",
      aws_dynamodb_table.hydrocron-swot-reach-table.arn,
      "${aws_dynamodb_table.hydrocron-swot-reach-table.arn}/index/*",
      aws_dynamodb_table.hydrocron-swot-prior-lakes-table.arn,
      "${aws_dynamodb_table.hydrocron-swot-prior-lakes-table.arn}/index/*"
    ]
  }

}


data "aws_iam_policy_document" "dynamo-read-policy-track-ingest" {

  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:BatchGetItem",
      "dynamodb:Scan",
      "dynamodb:Query",
      "dynamodb:ConditionCheckItem",
      "dynamodb:DescribeTable"
    ]

    resources = [
      aws_dynamodb_table.hydrocron-track-ingest-table.arn,
    ]
  }

}


data "aws_iam_policy_document" "dynamo-write-policy" {

  statement {
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:GetItem",
      "dynamodb:BatchGetItem",
      "dynamodb:Scan",
      "dynamodb:Query",
      "dynamodb:ConditionCheckItem",
      "dynamodb:DescribeTable"
    ]

    resources = [
      aws_dynamodb_table.hydrocron-swot-node-table.arn,
      aws_dynamodb_table.hydrocron-swot-reach-table.arn,
      aws_dynamodb_table.hydrocron-swot-prior-lake-table.arn
    ]
  }

}


data "aws_iam_policy_document" "dynamo-write-policy-track-ingest" {

  statement {
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:GetItem",
      "dynamodb:BatchGetItem",
      "dynamodb:Scan",
      "dynamodb:Query",
      "dynamodb:ConditionCheckItem",
      "dynamodb:DescribeTable"
    ]

    resources = [
      aws_dynamodb_table.hydrocron-track-ingest-table.arn
    ]
  }

}


data "aws_iam_policy_document" "lambda-invoke-policy" {

  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.hydrocron_lambda_load_granule.arn
    ]
  }
}


data "aws_iam_policy_document" "lambda-invoke-authorizer-policy" {

  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.hydrocron_lambda_authorizer.arn
    ]
  }
}


data "aws_iam_policy_document" "ssm-read-policy" {

  statement {
    effect = "Allow"
    actions = [
      "ssm:DescribeParameters"
    ]
    resources = ["arn:aws:ssm:${data.aws_region.current.id}:${local.account_id}:parameter/service/${var.app_name}/*"]
  }
  statement {
    effect = "Allow"

    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath"
    ]

    resources = ["arn:aws:ssm:${data.aws_region.current.id}:${local.account_id}:parameter/service/${var.app_name}/*"]
  }

}


data "aws_iam_policy_document" "s3-read-policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:Get*",
      "s3:List*",
      "s3:Describe*",
      "s3-object-lambda:Get*",
      "s3-object-lambda:List*"
    ]

    resources = [
      "arn:aws:s3:::podaac-*",
      "arn:aws:s3:::podaac-*/*"
    ]
  }
}


data "aws_iam_policy_document" "lambda_log_to_cloudwatch" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup"
    ]
    resources = [
      "arn:aws:logs:region:${local.account_id}:parameter/service/${var.app_name}/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      #"arn:aws:logs:region:${local.account_id}:log-group:/aws/lambda/${aws_lambda_function.hydrocron_lambda_load_data.function_name}:*",
      "arn:aws:logs:region:${local.account_id}:log-group:/aws/lambda:*"
    ]
  }
}


data "aws_iam_policy_document" "sns-resource-policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.cross_account_id}:root"]
    }

    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.hydrocron_sns_topic_cnm_response.arn]

  }
}


data "aws_iam_policy_document" "apigw-resource-policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions   = ["execute-api:Invoke"]
    resources = [aws_api_gateway_rest_api.hydrocron-api-gateway.execution_arn]

    condition {
      test     = "StringEquals"
      values   = [data.aws_vpc.default.id]
      variable = "aws:SourceVpc"
    }
  }


  statement {
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions   = ["execute-api:Invoke"]
    resources = [aws_api_gateway_rest_api.hydrocron-api-gateway.execution_arn]
  }
}


data "aws_iam_policy_document" "lambda-vpc" {

  statement {
    effect    = "Allow"
    actions   = ["ec2:CreateNetworkInterface"]
    resources = ["arn:aws:ec2:${local.region}:${local.account_id}:*/*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["ec2:DeleteNetworkInterface"]
    resources = ["arn:aws:ec2:${local.region}:${local.account_id}:*/*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["ec2:DescribeNetworkInterfaces"]
    resources = ["*"]
  }
}


# IAM Roles

resource "aws_iam_role" "hydrocron-gateway-authorizer-role" {
  name                 = "${local.aws_resource_prefix}-api-gateway-authorizer-role"
  permissions_boundary = "arn:aws:iam::${local.account_id}:policy/NGAPShRoleBoundary"
  assume_role_policy   = data.aws_iam_policy_document.assume_role_authorizer.json
  inline_policy {
    name   = "HydrocronInvokeLambdaAuthorizer"
    policy = data.aws_iam_policy_document.lambda-invoke-authorizer-policy.json
  }
}


resource "aws_iam_role" "hydrocron-lambda-execution-role" {
  name = "${local.aws_resource_prefix}-lambda-execution-role"

  permissions_boundary = "arn:aws:iam::${local.account_id}:policy/NGAPShRoleBoundary"
  assume_role_policy   = data.aws_iam_policy_document.assume_role_lambda.json
  managed_policy_arns  = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]

  inline_policy {
    name   = "HydrocronDynamoRead"
    policy = data.aws_iam_policy_document.dynamo-read-policy.json
  }
  inline_policy {
    name   = "HydrocronSSMRead"
    policy = data.aws_iam_policy_document.ssm-read-policy.json
  }
  inline_policy {
    name   = "HydrocronLambdaVPC"
    policy = data.aws_iam_policy_document.lambda-vpc.json
  }
}


resource "aws_iam_role" "hydrocron-lambda-authorizer-role" {
  name = "${local.aws_resource_prefix}-lambda-authorizer-role"

  permissions_boundary = "arn:aws:iam::${local.account_id}:policy/NGAPShRoleBoundary"
  assume_role_policy   = data.aws_iam_policy_document.assume_role_lambda.json
  managed_policy_arns  = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]

  inline_policy {
    name   = "HydrocronLambdaVPC"
    policy = data.aws_iam_policy_document.lambda-vpc.json
  }
  inline_policy {
    name   = "HydrocronSSMRead"
    policy = data.aws_iam_policy_document.ssm-read-policy.json
  }
}


resource "aws_iam_role" "hydrocron-lambda-load-data-role" {
  name = "${local.aws_resource_prefix}-lambda-load-data-role"

  permissions_boundary = "arn:aws:iam::${local.account_id}:policy/NGAPShRoleBoundary"
  assume_role_policy   = data.aws_iam_policy_document.assume_role_lambda.json
  managed_policy_arns  = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]

  inline_policy {
    name   = "HydrocronLambdaInvoke"
    policy = data.aws_iam_policy_document.lambda-invoke-policy.json
  }
  inline_policy {
    policy = data.aws_iam_policy_document.lambda_log_to_cloudwatch.json
  }
  inline_policy {
    name   = "HydrocronSSMRead"
    policy = data.aws_iam_policy_document.ssm-read-policy.json
  }
  inline_policy {
    name   = "HydrocronLambdaVPC"
    policy = data.aws_iam_policy_document.lambda-vpc.json
  }
}


resource "aws_iam_role" "hydrocron-lambda-load-granule-role" {
  name = "${local.aws_resource_prefix}-lambda-load-granule-role"

  permissions_boundary = "arn:aws:iam::${local.account_id}:policy/NGAPShRoleBoundary"
  assume_role_policy   = data.aws_iam_policy_document.assume_role_lambda.json
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ]

  inline_policy {
    name   = "HydrocronDynamoWrite"
    policy = data.aws_iam_policy_document.dynamo-write-policy.json
  }
  inline_policy {
    name   = "HydrocronTrackIngestDynamoWrite"
    policy = data.aws_iam_policy_document.dynamo-write-policy-track-ingest.json
  }
  inline_policy {
    name   = "HydrocronS3Read"
    policy = data.aws_iam_policy_document.s3-read-policy.json
  }
  inline_policy {
    policy = data.aws_iam_policy_document.lambda_log_to_cloudwatch.json
  }
  inline_policy {
    name   = "HydrocronSSMRead"
    policy = data.aws_iam_policy_document.ssm-read-policy.json
  }
  inline_policy {
    name   = "HydrocronLambdaVPC"
    policy = data.aws_iam_policy_document.lambda-vpc.json
  }
}


resource "aws_iam_role" "hydrocron-lambda-cnm-role" {
  name = "${local.aws_resource_prefix}-lambda-cnm-role"

  permissions_boundary = "arn:aws:iam::${local.account_id}:policy/NGAPShRoleBoundary"
  assume_role_policy   = data.aws_iam_policy_document.assume_role_lambda.json
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
  "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"]

  inline_policy {
    name   = "HydrocronLambdaInvoke"
    policy = data.aws_iam_policy_document.lambda-invoke-policy.json
  }
  inline_policy {
    policy = data.aws_iam_policy_document.lambda_log_to_cloudwatch.json
  }
  inline_policy {
    name   = "HydrocronSSMRead"
    policy = data.aws_iam_policy_document.ssm-read-policy.json
  }
  inline_policy {
    name   = "HydrocronS3Read"
    policy = data.aws_iam_policy_document.s3-read-policy.json
  }
}


resource "aws_lambda_permission" "aws_lambda_cnm_responder_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hydrocron_lambda_cnm.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.hydrocron_sns_topic_cnm_response.arn
}


resource "aws_iam_role" "hydrocron_lambda_track_ingest_role" {
  name = "${local.aws_resource_prefix}-lambda-track-ingest-role"

  permissions_boundary = "arn:aws:iam::${local.account_id}:policy/NGAPShRoleBoundary"
  assume_role_policy   = data.aws_iam_policy_document.assume_role_lambda.json
  managed_policy_arns  = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]

  inline_policy {
    name   = "HydrocronDynamoRead"
    policy = data.aws_iam_policy_document.dynamo-read-policy.json
  }
  inline_policy {
    name   = "HydrocronDynamoReadIngest"
    policy = data.aws_iam_policy_document.dynamo-read-policy-track-ingest.json
  }
  inline_policy {
    name   = "HydrocronDynamoWriteIngest"
    policy = data.aws_iam_policy_document.dynamo-write-policy-track-ingest.json
  }
  inline_policy {
    name   = "HydrocronSSMRead"
    policy = data.aws_iam_policy_document.ssm-read-policy.json
  }
}