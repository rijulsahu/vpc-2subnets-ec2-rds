# Security Group Configuration
# 4-tier security group architecture: bastion, web, application, database
# Requirements: 5.1-5.7, 9.5

# Bastion Security Group
# Jump host for SSH access to private instances
resource "aws_security_group" "bastion" {
  name        = "${local.resource_prefix}-bastion-sg"
  description = "Security group for bastion host - SSH access from admin networks"
  vpc_id      = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_prefix}-bastion-sg"
      Type = "Bastion"
      Role = "Jump Host"
    }
  )
}

# Bastion Ingress: SSH from admin CIDR blocks
resource "aws_security_group_rule" "bastion_ingress_ssh" {
  count = length(var.admin_cidr_blocks)

  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr_blocks[count.index]]
  description       = "SSH access from admin CIDR ${var.admin_cidr_blocks[count.index]}"
  security_group_id = aws_security_group.bastion.id
}

# Bastion Egress: SSH to application tier
# Note: Application SG must be created first, so this references it
resource "aws_security_group_rule" "bastion_egress_ssh_to_app" {
  type                     = "egress"
  from_port                = 22
  to_port                  = 22
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.application.id
  description              = "SSH access to application tier"
  security_group_id        = aws_security_group.bastion.id
}

# Web Tier Security Group
# For load balancers and web servers
resource "aws_security_group" "web" {
  name        = "${local.resource_prefix}-web-sg"
  description = "Security group for web tier - HTTP/HTTPS from internet"
  vpc_id      = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_prefix}-web-sg"
      Type = "Web"
      Role = "Load Balancer / Web Server"
    }
  )
}

# Web Ingress: HTTP from internet
resource "aws_security_group_rule" "web_ingress_http" {
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "HTTP access from internet"
  security_group_id = aws_security_group.web.id
}

# Web Ingress: HTTPS from internet
resource "aws_security_group_rule" "web_ingress_https" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "HTTPS access from internet"
  security_group_id = aws_security_group.web.id
}

# Web Egress: To application tier
resource "aws_security_group_rule" "web_egress_to_app" {
  type                     = "egress"
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.application.id
  description              = "Access to application tier"
  security_group_id        = aws_security_group.web.id
}

# Application Tier Security Group
# For application servers
resource "aws_security_group" "application" {
  name        = "${local.resource_prefix}-app-sg"
  description = "Security group for application tier - access from web and bastion"
  vpc_id      = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_prefix}-app-sg"
      Type = "Application"
      Role = "Application Server"
    }
  )
}

# Application Ingress: From web tier
resource "aws_security_group_rule" "app_ingress_from_web" {
  type                     = "ingress"
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.web.id
  description              = "Application traffic from web tier"
  security_group_id        = aws_security_group.application.id
}

# Application Ingress: SSH from bastion
resource "aws_security_group_rule" "app_ingress_ssh_from_bastion" {
  type                     = "ingress"
  from_port                = 22
  to_port                  = 22
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.bastion.id
  description              = "SSH access from bastion host"
  security_group_id        = aws_security_group.application.id
}

# Application Egress: To database tier
resource "aws_security_group_rule" "app_egress_to_db" {
  type                     = "egress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.database.id
  description              = "MySQL/MariaDB access to database tier"
  security_group_id        = aws_security_group.application.id
}

# Application Egress: HTTPS to internet (for updates, API calls)
resource "aws_security_group_rule" "app_egress_https" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "HTTPS access to internet for updates and API calls"
  security_group_id = aws_security_group.application.id
}

# Database Tier Security Group
# For RDS instances
resource "aws_security_group" "database" {
  name        = "${local.resource_prefix}-db-sg"
  description = "Security group for database tier - access from application only"
  vpc_id      = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_prefix}-db-sg"
      Type = "Database"
      Role = "RDS Database"
    }
  )
}

# Database Ingress: MySQL/MariaDB from application tier
resource "aws_security_group_rule" "db_ingress_from_app" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.application.id
  description              = "MySQL/MariaDB access from application tier"
  security_group_id        = aws_security_group.database.id
}

# No egress rules for database tier (deny all outbound by default)
