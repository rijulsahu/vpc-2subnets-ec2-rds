# Crete postgresql RDS db instance
resource "aws_db_instance" "demo-db" {
  name = "demodb"
  db_subnet_group_name = aws_db_subnet_group.demo-db-subnet-group.name
  vpc_security_group_ids = [aws_security_group.demo-database-sg.id]
  engine               = "postgres"
  engine_version       = "11.6"
  identifier           = "${var.project_prefix}-db-server-${var.env}"
  instance_class       = "db.t2.medium"
  username             = var.db_admin_user
  password             = var.rds_password
  allocated_storage    = var.db_storage
  port                 = "5432"
  skip_final_snapshot  = true
  apply_immediately    = true
  backup_retention_period = "30"
  storage_encrypted    = true
  publicly_accessible  = false
  }
