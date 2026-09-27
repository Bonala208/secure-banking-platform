# DB Subnet Group (Isolated Private DB Subnets)
resource "aws_db_subnet_group" "db_group" {
  name        = "${var.project_name}-db-subnet-group"
  subnet_ids  = aws_subnet.private_db[*].id
  description = "Subnets dedicated for Amazon RDS PostgreSQL"

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# Amazon RDS PostgreSQL Instance
resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-postgres"
  allocated_storage      = 20
  max_allocated_storage  = 50
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = "db.t3.micro" # Free Tier Eligible
  db_name                = "banking_db"
  username               = var.db_username
  password               = random_password.db_password.result
  db_subnet_group_name   = aws_db_subnet_group.db_group.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  # Security requirements
  publicly_accessible = false
  storage_encrypted   = true # Data at rest encryption via AWS KMS
  
  # Clean teardown for assignment lifecycle
  skip_final_snapshot = true
  deletion_protection = false

  tags = {
    Name = "${var.project_name}-db"
  }
}
