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

