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



# Event source mapping: DynamoDB Stream → Lambda
resource "aws_lambda_event_source_mapping" "dynamodb_stream_source" {
  event_source_arn  = aws_dynamodb_table.c23-smearbot-enriched-data-dynamodb-table.stream_arn
  function_name     = aws_lambda_function.blue_sky_poster.function_name
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

  depends_on = [aws_lambda_function.blue_sky_poster]
}

# IAM Role for Lambda
resource "aws_iam_role" "blue_sky_poster_lambda_role" {
  name = "c23-smearbot-blue-sky-poster-lambda-role"

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
resource "aws_iam_role_policy" "blue_sky_poster_lambda_policy" {
  name = "c23-smearbot-blue-sky-poster-lambda-policy"
  role = aws_iam_role.blue_sky_poster_lambda_role.id

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
        Resource = [
          aws_dynamodb_table.c23-smearbot-enriched-data-dynamodb-table.stream_arn,
          "${aws_dynamodb_table.c23-smearbot-enriched-data-dynamodb-table.stream_arn}/*"
        ]
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

resource "aws_lambda_function" "blue_sky_poster" {
  function_name = var.blue_sky_lambda_function_name
  role           = aws_iam_role.blue_sky_poster_lambda_role.arn
  timeout        = 600
  memory_size    = 512

  # Placeholder: Update with actual ECR image URI after pushing to registry
  image_uri = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${local.region}.amazonaws.com/${var.blue_sky_poster_repo_name}:latest"
  package_type  = "Image"

  environment {
    variables = {
      
      SECRETS_MANAGER_SECRET   = "c23-smearbot"
      SECRETS_MANAGER_REGION   = local.region
    }
  }

  depends_on = [aws_cloudwatch_log_group.blue_sky_poster_logs]
}

resource "aws_cloudwatch_log_group" "blue_sky_poster_logs" {
  name              = "/aws/lambda/c23-smearbot-blue-sky-poster"
  retention_in_days = 14
}
