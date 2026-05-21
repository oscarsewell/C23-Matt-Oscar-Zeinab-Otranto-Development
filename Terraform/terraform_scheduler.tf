# EventBridge Scheduler configuration for triggering Step Function every 5 minutes

data "aws_iam_policy_document" "scheduler_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "c23_smearbot_scheduler_role" {
  name               = "c23-smearbot-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role_policy.json
}

data "aws_iam_policy_document" "scheduler_start_sfn_policy" {
  statement {
    sid     = "AllowStartExecutionOnTargetStateMachine"
    effect  = "Allow"
    actions = ["states:StartExecution"]

    resources = [local.step_function_arn]
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
    arn      = local.step_function_arn
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