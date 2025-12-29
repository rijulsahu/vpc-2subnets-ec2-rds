# Subnet Resources for VPC Best Practices
# This file contains public and private subnet definitions

# Public Subnets
# These subnets have direct internet access via Internet Gateway
resource "aws_subnet" "public" {
  count = local.az_count

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = local.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    local.common_tags,
    local.public_subnet_tags,
    {
      Name = local.public_subnet_names[count.index]
      AZ   = local.availability_zones[count.index]
    }
  )
}

# Private Subnets
# These subnets have no direct internet access, use NAT Gateway for outbound
resource "aws_subnet" "private" {
  count = local.az_count

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_cidrs[count.index]
  availability_zone       = local.availability_zones[count.index]
  map_public_ip_on_launch = false

  tags = merge(
    local.common_tags,
    local.private_subnet_tags,
    {
      Name = local.private_subnet_names[count.index]
      AZ   = local.availability_zones[count.index]
    }
  )
}
