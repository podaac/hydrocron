# IAM Policies
data "aws_iam_policy_document" "dynamo-read-policy" {

  statement {
    effect  = "Allow"
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
      aws_dynamodb_table.hydrocron-swot-reach-table.arn
    ]
  }

}

data "aws_iam_policy_document" "dynamo-write-policy" {

  statement {
    effect  = "Allow"
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
      aws_dynamodb_table.hydrocron-swot-reach-table.arn
    ]
  }

}
data "aws_iam_policy_document" "lambda-invoke-policy" {

  statement {
    effect  = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      # "arn:aws:lambda:${data.aws_region.current.id}:${local.account_id}:*",
      aws_lambda_function.hydrocron_lambda_load_granule.invoke_arn
      ]
  }

}
data "aws_iam_policy_document" "ssm-read-policy" {

  statement {
    effect  = "Allow"
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
    effect  = "Allow"
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

# IAM Roles

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
}


resource "aws_iam_role" "hydrocron-lambda-load-data-role" {
  name = "${local.aws_resource_prefix}-lambda-load-data-role"

  permissions_boundary = "arn:aws:iam::${local.account_id}:policy/NGAPShRoleBoundary"
  assume_role_policy   = data.aws_iam_policy_document.assume_role_lambda.json
  managed_policy_arns  = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]

  inline_policy {
    name = "HydrocronLambdaInvoke"
    policy = data.aws_iam_policy_document.lambda-invoke-policy.json
  }
}

resource "aws_iam_role" "hydrocron-lambda-load-granule-role" {
  name = "${local.aws_resource_prefix}-lambda-load-granule-role"

  permissions_boundary = "arn:aws:iam::${local.account_id}:policy/NGAPShRoleBoundary"
  assume_role_policy   = data.aws_iam_policy_document.assume_role_lambda.json
  managed_policy_arns  = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]

  inline_policy {
    name   = "HydrocronDynamoWrite"
    policy = data.aws_iam_policy_document.dynamo-write-policy.json
  }
  inline_policy {
    name = "HydrocronS3Read"
    policy = data.aws_iam_policy_document.s3-read-policy.json
  }
}
