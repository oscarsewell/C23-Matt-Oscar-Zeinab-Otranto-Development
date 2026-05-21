## Will need referencing the Step Function ARN from the Step Function Terraform module
variable "step_function_arn" {
  description = "ARN of the Step Function state machine to trigger."
  type        = string
}

variable "scheduler_name" {
  description = "Name of the EventBridge Scheduler schedule."
  type        = string
  default     = "c23-smearbot-step-function-schedule"
}

variable "schedule_expression" {
  description = "Schedule expression for EventBridge Scheduler."
  type        = string
  default     = "cron(0/5 * * * ? *)"
}

variable "s3_name" {
  description = "Name of the S3 bucket."
  type        = string
  default     = "c23-smearbot-caching-bucket"
}

variable "rss_extraction_repo_name" {
  description = "Name for RSS extraction Lambda function ECR repository."
  type        = string
  default     = "c23-smearbot-rss-extraction"
}

variable "article_scraping_repo_name" {
  description = "Name for article scraping Lambda function ECR repository."
  type        = string
  default     = "c23-smearbot-article-scraping"
}

variable "data_enrichment_repo_name" {
  description = "Name for data enrichment Lambda function ECR repository."
  type        = string
  default     = "c23-smearbot-data-enrichment"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table."
  type        = string
  default     = "c23-smearbot-dynamodb-table"
}
