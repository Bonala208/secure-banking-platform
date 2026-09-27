variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "ap-southeast-1" # Singapore region (change as desired e.g. us-east-1)
}

variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "banking-platform"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for the 3-tier VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "db_username" {
  description = "Master database administrator username"
  type        = string
  default     = "dbadmin"
}

variable "ecs_task_count" {
  description = "Number of ECS Fargate tasks running across AZs"
  type        = number
  default     = 2
}
