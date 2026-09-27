output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = "http://${aws_lb.main.dns_name}"
}

output "api_docs_swagger_url" {
  description = "Interactive Swagger UI for Testing the Banking Endpoints"
  value       = "http://${aws_lb.main.dns_name}/docs"
}

output "ecr_repository_url" {
  description = "URL of the Amazon ECR Docker repository"
  value       = aws_ecr_repository.app.repository_url
}

output "rds_endpoint" {
  description = "Private endpoint of the Amazon RDS PostgreSQL instance"
  value       = aws_db_instance.postgres.endpoint
}

output "secrets_manager_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
}
