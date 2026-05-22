# Lambda Functions using ECR container images

# CloudWatch Log Group for RSS Extraction Lambda
resource "aws_cloudwatch_log_group" "rss_extraction_logs" {
  name              = "/aws/lambda/c23-smearbot-rss-extraction"
  retention_in_days = 14
}

# RSS Extraction Lambda Function
resource "aws_lambda_function" "rss_extraction" {
  function_name = "c23-smearbot-rss-extraction"
  role           = aws_iam_role.rss_extraction_role.arn
  timeout        = 60
  memory_size    = 512

  # Placeholder: Update with actual ECR image URI after pushing to registry
  image_uri = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${local.region}.amazonaws.com/${var.rss_extraction_repo_name}:latest"
  package_type  = "Image"

  environment {
    variables = {
      S3_CACHING_BUCKET     = var.s3_name
      S3_CACHE_PREFIX       = "rss_feed_cache/"
    }
  }

  depends_on = [aws_cloudwatch_log_group.rss_extraction_logs]
}

# CloudWatch Log Group for Web Scraping Lambda
resource "aws_cloudwatch_log_group" "web_scraping_logs" {
  name              = "/aws/lambda/c23-smearbot-web-scraping"
  retention_in_days = 14
}

# Web Scraping Lambda Function
resource "aws_lambda_function" "web_scraping" {
  function_name = "c23-smearbot-web-scraping"
  role           = aws_iam_role.web_scraping_role.arn
  timeout        = 120
  memory_size    = 512

  # Placeholder: Update with actual ECR image URI after pushing to registry
  image_uri = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${local.region}.amazonaws.com/${var.article_scraping_repo_name}:latest"
  package_type  = "Image"

  environment {
    variables = {
      S3_CACHING_BUCKET = var.s3_name
    }
  }

  depends_on = [aws_cloudwatch_log_group.web_scraping_logs]
}

# CloudWatch Log Group for Data Enrichment Lambda
resource "aws_cloudwatch_log_group" "data_enrichment_logs" {
  name              = "/aws/lambda/c23-smearbot-data-enrichment"
  retention_in_days = 14
}

# Data Enrichment Lambda Function
resource "aws_lambda_function" "data_enrichment" {
  function_name = "c23-smearbot-data-enrichment"
  role           = aws_iam_role.data_enrichment_role.arn
  timeout        = 600
  memory_size    = 512

  # Placeholder: Update with actual ECR image URI after pushing to registry
  image_uri = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${local.region}.amazonaws.com/${var.data_enrichment_repo_name}:latest"
  package_type  = "Image"

  environment {
    variables = {
      DYNAMODB_TABLE           = var.dynamodb_table_name
      SECRETS_MANAGER_SECRET   = "c23-smearbot"
      SECRETS_MANAGER_REGION   = local.region
    }
  }

  depends_on = [aws_cloudwatch_log_group.data_enrichment_logs]
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}
