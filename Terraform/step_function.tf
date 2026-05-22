# IAM role for Step Function execution
data "aws_iam_policy_document" "step_function_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "step_function_role" {
  name               = "c23-smearbot-step-function-role"
  assume_role_policy = data.aws_iam_policy_document.step_function_assume_role_policy.json
}

# IAM policy to allow Step Function to invoke Lambda functions
data "aws_iam_policy_document" "step_function_lambda_policy" {
  statement {
    sid    = "AllowLambdaInvocation"
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.rss_extraction.arn,
      aws_lambda_function.web_scraping.arn,
      aws_lambda_function.data_enrichment.arn
    ]
  }
}

resource "aws_iam_role_policy" "step_function_lambda_policy" {
  name   = "c23-smearbot-step-function-lambda-policy"
  role   = aws_iam_role.step_function_role.id
  policy = data.aws_iam_policy_document.step_function_lambda_policy.json
}

# AWS Step Function state machine
resource "aws_sfn_state_machine" "c23_smearbot_step_function" {
  name       = "c23-smearbot-rss-extraction-pipeline"
  role_arn   = aws_iam_role.step_function_role.arn
  definition = jsonencode({
    Comment = "C23 Smearbot RSS Extraction Pipeline"
    StartAt = "ExtractRSSFeeds"
    States = {
      ExtractRSSFeeds = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.rss_extraction.arn
          Payload = {
            feed_urls = [
              "https://feeds.bbci.co.uk/news/rss.xml",
              "https://www.theguardian.com/world/rss",
              "https://feeds.bbci.co.uk/news/politics/rss.xml",
              "https://www.theguardian.com/us-news/us-politics/rss"
            ]
          }
        }
        ResultPath = "$.rss_extraction_result"
        Next       = "ScrapeWebContent"
      }
      ScrapeWebContent = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.web_scraping.arn
          Payload = {
            "urls.$" = "$.rss_extraction_result.Payload.new_urls"
          }
        }
        ResultPath = "$.scraping_result"
        Next       = "EnrichArticles"
      }
      EnrichArticles = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.data_enrichment.arn
          Payload = {
            "s3_bucket.$" = "$.scraping_result.Payload.s3_bucket"
            "s3_key.$"    = "$.scraping_result.Payload.s3_key"
          }
        }
        ResultPath = "$.enrichment_result"
        End = true
      }
    }
  })
}

output "step_function_arn" {
  description = "ARN of the Step Function state machine"
  value       = aws_sfn_state_machine.c23_smearbot_step_function.arn
}
