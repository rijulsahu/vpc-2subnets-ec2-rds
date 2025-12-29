# VPC Best Practices Deployment
# This file contains the main VPC resource definition

# VPC Resource
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  instance_tenancy     = "default"

  tags = merge(
    local.common_tags,
    {
      Name = local.vpc_name
    }
  )
}

# Internet Gateway
# Requirement 3.1: Internet Gateway for public internet connectivity
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_prefix}-igw"
    }
  )
}
# Default Security Group - Restrict All Traffic
# Requirement 9.1: Restrict default security group to prevent unintended use
# Best practice: Remove all ingress and egress rules from default SG
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id

  # No ingress rules (deny all inbound)
  # No egress rules (deny all outbound)
  
  tags = merge(
    local.common_tags,
    {
      Name        = "${local.resource_prefix}-default-sg-restricted"
      Description = "Default SG with all rules removed for security"
      Purpose     = "Security Hardening"
    }
  )
}