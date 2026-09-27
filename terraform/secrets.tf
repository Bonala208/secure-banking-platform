# Generate a secure random password for PostgreSQL
resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# AWS Secrets Manager Secret
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.project_name}-db-secret-${random_password.db_password.result != "" ? "prod" : "init"}"
  recovery_window_in_days = 0 # Immediate purge upon destroy for testing/assignments

  tags = {
    Name = "${var.project_name}-db-credentials"
  }
}

# Store the JSON payload in Secrets Manager
resource "aws_secretsmanager_secret_version" "db_credentials_val" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    dbname   = "banking_db"
  })
}
