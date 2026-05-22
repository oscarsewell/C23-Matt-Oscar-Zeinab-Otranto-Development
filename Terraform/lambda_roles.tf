# Lambda Execution Roles and Policies

# IAM role for RSS Extraction Lambda
data "aws_iam_policy_document" "rss_extraction_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "rss_extraction_role" {
  name               = "c23-smearbot-rss-extraction-role"
  assume_role_policy = data.aws_iam_policy_document.rss_extraction_assume_role_policy.json
}

# Policy for RSS Extraction Lambda - S3 cache access + CloudWatch logs
data "aws_iam_policy_document" "rss_extraction_policy" {
  statement {
    sid    = "S3CacheAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = ["arn:aws:s3:::${var.s3_name}/*"]
  }

  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:${local.region}:*:log-group:/aws/lambda/*"]
  }
}

resource "aws_iam_role_policy" "rss_extraction_policy" {
  name   = "c23-smearbot-rss-extraction-policy"
  role   = aws_iam_role.rss_extraction_role.id
  policy = data.aws_iam_policy_document.rss_extraction_policy.json
}

# IAM role for Web Scraping Lambda
data "aws_iam_policy_document" "web_scraping_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "web_scraping_role" {
  name               = "c23-smearbot-web-scraping-role"
  assume_role_policy = data.aws_iam_policy_document.web_scraping_assume_role_policy.json
}

# Policy for Web Scraping Lambda - S3 write access + CloudWatch logs
data "aws_iam_policy_document" "web_scraping_policy" {
  statement {
    sid    = "S3WriteAccess"
    effect = "Allow"
    actions = [
      "s3:PutObject"
    ]
    resources = ["arn:aws:s3:::${var.s3_name}/*"]
  }

  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:${local.region}:*:log-group:/aws/lambda/*"]
  }
}

resource "aws_iam_role_policy" "web_scraping_policy" {
  name   = "c23-smearbot-web-scraping-policy"
  role   = aws_iam_role.web_scraping_role.id
  policy = data.aws_iam_policy_document.web_scraping_policy.json
}

# IAM role for Data Enrichment Lambda
data "aws_iam_policy_document" "data_enrichment_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "data_enrichment_role" {
  name               = "c23-smearbot-data-enrichment-role"
  assume_role_policy = data.aws_iam_policy_document.data_enrichment_assume_role_policy.json
}

# Policy for Data Enrichment Lambda - S3 read, DynamoDB write + CloudWatch logs
data "aws_iam_policy_document" "data_enrichment_policy" {
  statement {
    sid    = "S3ReadAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject"
    ]
    resources = ["arn:aws:s3:::${var.s3_name}/*"]
  }

  statement {
    sid    = "DynamoDBWrite"
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:BatchWriteItem"
    ]
    resources = ["arn:aws:dynamodb:${local.region}:*:table/${var.dynamodb_table_name}"]
  }

  statement {
    sid    = "SecretsManagerRead"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = ["arn:aws:secretsmanager:${local.region}:${data.aws_caller_identity.current.account_id}:secret:c23-smearbot-*"]
  }

  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:${local.region}:*:log-group:/aws/lambda/*"]
  }
}

resource "aws_iam_role_policy" "data_enrichment_policy" {
  name   = "c23-smearbot-data-enrichment-policy"
  role   = aws_iam_role.data_enrichment_role.id
  policy = data.aws_iam_policy_document.data_enrichment_policy.json
}
