# Public Route Table Configuration
# Requirements 3.2, 3.7

# Public Route Table
# Single route table for all public subnets (they share the same internet gateway)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_prefix}-public-rt"
      Type = "public"
    }
  )
}

# Route to Internet Gateway
# All public subnet traffic destined for internet goes through IGW
resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# Public Subnet Route Table Associations
# Associate each public subnet with the public route table
resource "aws_route_table_association" "public" {
  count = local.az_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private Route Tables Configuration
# Requirements 3.5, 3.7, 7.5

# Private Route Tables
# For per_az strategy: one route table per AZ for high availability
# For single strategy: one shared route table (cost-optimized)
resource "aws_route_table" "private" {
  count = local.nat_gateway_count

  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = var.nat_gateway_strategy == "per_az" ? "${local.resource_prefix}-private-rt-${local.availability_zones[count.index]}" : "${local.resource_prefix}-private-rt"
      Type = "private"
      AZ   = var.nat_gateway_strategy == "per_az" ? local.availability_zones[count.index] : "shared"
    }
  )
}

# Routes to NAT Gateways
# Each private route table routes internet traffic to its corresponding NAT Gateway
resource "aws_route" "private_nat" {
  count = local.nat_gateway_count

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
}

# Private Subnet Route Table Associations
# For per_az strategy: each subnet associated with its AZ's route table
# For single strategy: all subnets share the single route table
resource "aws_route_table_association" "private" {
  count = local.az_count

  subnet_id = aws_subnet.private[count.index].id
  # For per_az: use matching index; for single: all use index 0
  route_table_id = var.nat_gateway_strategy == "per_az" ? aws_route_table.private[count.index].id : aws_route_table.private[0].id
}
