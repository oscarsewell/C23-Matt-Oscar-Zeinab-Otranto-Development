resource "aws_ecr_repository" "blue_sky_poster" {
  name                 = var.blue_sky_poster_repo_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}


resource "aws_ecr_lifecycle_policy" "blue_sky_poster_policy" {
  repository = aws_ecr_repository.blue_sky_poster.name
    policy     = jsonencode({
        rules = [
            {
                rulePriority = 1,
                description = "Keep only the 5 most recent images",
                selection = {
                    tagStatus = "any",
                    countType = "imageCountMoreThan",
                    countNumber = 5
                }
                action = {
                    type = "expire"
                }
            }
        ]
    })
}

data "aws_lambda_function" "bluesky_poster" {
  function_name = var.blue_sky_lambda_function_name  
  }

# Event source mapping: DynamoDB Stream → Lambda
resource "aws_lambda_event_source_mapping" "dynamodb_stream_source" {
  event_source_arn  = aws_dynamodb_table.c23-smearbot-enriched-data-dynamodb-table.stream_arn
  function_name     = data.aws_lambda_function.bluesky_poster.function_name
  enabled           = true
  batch_size        = 1
  starting_position = "LATEST"

  filter_criteria {
    filter {
      pattern = jsonencode({
        eventName = ["INSERT"]
      })
    }
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_execution_role" {
  name = "bluesky-poster-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy: Stream access + Secrets Manager + CloudWatch logs
resource "aws_iam_role_policy" "lambda_policy" {
  name = "bluesky-poster-lambda-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:DescribeStream",
          "dynamodb:ListStreams",
          "dynamodb:ListShards"
        ]
        Resource = "${aws_dynamodb_table.c23-smearbot-enriched-data-dynamodb-table.stream_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "bluesky_poster_logs"{
    
  name              = "/aws/lambda/bluesky-poster-lambda"
  retention_in_days = 14  # Adjust as needed (7, 14, 30, 90, etc.)

  tags = {
    Name = "bluesky-poster-lambda-logs"
  }
}