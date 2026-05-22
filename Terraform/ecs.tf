# ECR repository for dashboard
resource "aws_ecr_repository" "dashboard" {
  name                 = "c23-smearbot-dashboard"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }
}

# Data source for ECS cluster
data "aws_ecs_cluster" "existing" {
  cluster_name = "c23-ecs-cluster"
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs_dashboard" {
  name              = "/ecs/c23-smearbot-dashboard"
  retention_in_days = 7
}

# ECS Task Definition
resource "aws_ecs_task_definition" "dashboard" {
  family                   = "c23-smearbot-dashboard"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn      = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "dashboard"
      image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${local.region}.amazonaws.com/c23-smearbot-dashboard:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DYNAMODB_TABLE"
          value = var.dynamodb_table_name
        },
        {
          name  = "AWS_REGION"
          value = local.region
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_dashboard.name
          "awslogs-region"        = local.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# Security Group for ECS service
resource "aws_security_group" "ecs_dashboard" {
  name        = "c23-smearbot-dashboard-sg"
  description = "Security group for dashboard ECS service"
  vpc_id      = data.aws_vpc.c23.id

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Get c23-VPC and its public subnets
data "aws_vpc" "c23" {
  tags = {
    Name = "c23-VPC"
  }
}

data "aws_subnets" "c23_public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.c23.id]
  }
  
  filter {
    name   = "tag:Name"
    values = ["c23-public-subnet-1", "c23-public-subnet-2", "c23-public-subnet-3"]
  }
}

# ECS Service
resource "aws_ecs_service" "dashboard" {
  name            = "c23-smearbot-dashboard"
  cluster         = data.aws_ecs_cluster.existing.id
  task_definition = aws_ecs_task_definition.dashboard.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.c23_public.ids
    security_groups  = [aws_security_group.ecs_dashboard.id]
    assign_public_ip = true
  }
}

output "dashboard_ecr_repository_url" {
  description = "ECR repository URL for dashboard"
  value       = aws_ecr_repository.dashboard.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = data.aws_ecs_cluster.existing.cluster_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.dashboard.name
}
