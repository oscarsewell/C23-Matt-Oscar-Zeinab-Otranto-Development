provider "aws" {
  region = "eu-west-2"
}


data "aws_iam_policy_document" "scheduler_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "c23-smearbot-scheduler-role" {
  name               = "c23-smearbot-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role_policy.json
}

## Additional policies will need to be added to satisfy its true role.
data "aws_iam_policy_document" "scheduler_start_sfn_policy" {
  statement {
    sid     = "AllowStartExecutionOnTargetStateMachine"
    effect  = "Allow"
    actions = ["states:StartExecution"]

    resources = [var.step_function_arn]
  }
}

resource "aws_iam_role_policy" "c23_smearbot_scheduler_start_sfn" {
  name   = "c23-smearbot-scheduler-start-sfn"
  role   = aws_iam_role.c23_smearbot_scheduler_role.id
  policy = data.aws_iam_policy_document.scheduler_start_sfn_policy.json
}

resource "aws_scheduler_schedule" "c23_smearbot_step_function_schedule" {
  name       = var.scheduler_name
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = var.schedule_expression

  target {
    arn      = var.step_function_arn
    role_arn = aws_iam_role.c23_smearbot_scheduler_role.arn

    input = jsonencode({
      source = "eventbridge-scheduler"
    })
  }
}

output "scheduler_role_arn" {
  description = "IAM role ARN assumed by EventBridge Scheduler."
  value       = aws_iam_role.c23_smearbot_scheduler_role.arn
}

output "scheduler_name" {
  description = "EventBridge Scheduler schedule name."
  value       = aws_scheduler_schedule.c23_smearbot_step_function_schedule.name
}