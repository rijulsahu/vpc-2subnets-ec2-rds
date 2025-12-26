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
