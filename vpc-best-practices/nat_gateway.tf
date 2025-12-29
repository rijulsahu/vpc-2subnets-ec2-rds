# NAT Gateway Configuration
# Requirements 3.3, 3.4, 3.6, 7.2, 8.1

# Elastic IP addresses for NAT Gateways
# Create one EIP per NAT Gateway (count determined by strategy)
resource "aws_eip" "nat" {
  count  = local.nat_gateway_count
  domain = "vpc"

  tags = merge(
    local.common_tags,
    {
      Name = var.nat_gateway_strategy == "per_az" ? "${local.resource_prefix}-nat-eip-${local.availability_zones[count.index]}" : "${local.resource_prefix}-nat-eip"
      Type = "nat-gateway"
      AZ   = var.nat_gateway_strategy == "per_az" ? local.availability_zones[count.index] : local.availability_zones[0]
    }
  )

  # NAT Gateway depends on Internet Gateway being attached
  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
# For 'per_az' strategy: creates one NAT Gateway per AZ (high availability)
# For 'single' strategy: creates one NAT Gateway in first AZ (cost-optimized)
resource "aws_nat_gateway" "main" {
  count = local.nat_gateway_count

  allocation_id     = aws_eip.nat[count.index].id
  subnet_id         = aws_subnet.public[count.index].id
  connectivity_type = "public"

  tags = merge(
    local.common_tags,
    {
      Name     = var.nat_gateway_strategy == "per_az" ? "${local.resource_prefix}-nat-${local.availability_zones[count.index]}" : "${local.resource_prefix}-nat"
      Type     = "nat-gateway"
      AZ       = var.nat_gateway_strategy == "per_az" ? local.availability_zones[count.index] : local.availability_zones[0]
      Strategy = var.nat_gateway_strategy
    }
  )

  # NAT Gateway requires Internet Gateway to be available
  depends_on = [aws_internet_gateway.main]
}
