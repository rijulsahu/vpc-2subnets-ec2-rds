# Network ACL Configuration
# Public and private NACLs for subnet-level network filtering
# Requirements: 4.1-4.7

# Public NACL for public subnets
# Allows inbound HTTP/HTTPS/SSH and ephemeral ports for return traffic
resource "aws_network_acl" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_prefix}-public-nacl"
      Type = "Public"
    }
  )
}

# Public NACL Inbound Rules
# Rule numbering allows insertions: 100, 110, 120...

# Allow HTTP from internet
resource "aws_network_acl_rule" "public_inbound_http" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 100
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 80
  to_port        = 80
}

# Allow HTTPS from internet
resource "aws_network_acl_rule" "public_inbound_https" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 110
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 443
  to_port        = 443
}

# Allow SSH from admin CIDR blocks
resource "aws_network_acl_rule" "public_inbound_ssh" {
  count = length(var.admin_cidr_blocks)

  network_acl_id = aws_network_acl.public.id
  rule_number    = 120
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = var.admin_cidr_blocks[count.index]
  from_port      = 22
  to_port        = 22
}

# Allow ephemeral ports for return traffic (responses to outbound requests)
resource "aws_network_acl_rule" "public_inbound_ephemeral" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 130
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 1024
  to_port        = 65535
}

# Allow ICMP (ping) from private subnets for connectivity testing
resource "aws_network_acl_rule" "public_inbound_icmp" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 140
  egress         = false
  protocol       = "icmp"
  rule_action    = "allow"
  cidr_block     = var.vpc_cidr
  icmp_type      = -1
  icmp_code      = -1
}

# Public NACL Outbound Rules

# Allow HTTP to internet
resource "aws_network_acl_rule" "public_outbound_http" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 100
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 80
  to_port        = 80
}

# Allow HTTPS to internet
resource "aws_network_acl_rule" "public_outbound_https" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 110
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 443
  to_port        = 443
}

# Allow SSH to private subnets (for bastion/jump host functionality)
resource "aws_network_acl_rule" "public_outbound_ssh" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 120
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = var.vpc_cidr
  from_port      = 22
  to_port        = 22
}

# Allow ICMP (ping) to private subnets for connectivity testing
resource "aws_network_acl_rule" "public_outbound_icmp" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 130
  egress         = true
  protocol       = "icmp"
  rule_action    = "allow"
  cidr_block     = var.vpc_cidr
  icmp_type      = -1
  icmp_code      = -1
}

# Allow ephemeral ports for responses to inbound requests
resource "aws_network_acl_rule" "public_outbound_ephemeral" {
  network_acl_id = aws_network_acl.public.id
  rule_number    = 140
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 1024
  to_port        = 65535
}

# Public NACL Subnet Associations
resource "aws_network_acl_association" "public" {
  count = local.az_count

  network_acl_id = aws_network_acl.public.id
  subnet_id      = aws_subnet.public[count.index].id
}

# Private NACL for private subnets
# Restrictive rules: only VPC CIDR traffic and HTTPS for updates
resource "aws_network_acl" "private" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_prefix}-private-nacl"
      Type = "Private"
    }
  )
}

# Private NACL Inbound Rules
# Only allow traffic from within VPC and ephemeral ports for return traffic

# Allow all traffic from VPC CIDR (internal communication)
resource "aws_network_acl_rule" "private_inbound_vpc" {
  network_acl_id = aws_network_acl.private.id
  rule_number    = 100
  egress         = false
  protocol       = "-1" # All protocols
  rule_action    = "allow"
  cidr_block     = var.vpc_cidr
}

# Allow ephemeral ports for return traffic from internet (responses to outbound HTTPS)
resource "aws_network_acl_rule" "private_inbound_ephemeral" {
  network_acl_id = aws_network_acl.private.id
  rule_number    = 110
  egress         = false
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 1024
  to_port        = 65535
}

# Private NACL Outbound Rules

# Allow all traffic to VPC CIDR (internal communication)
resource "aws_network_acl_rule" "private_outbound_vpc" {
  network_acl_id = aws_network_acl.private.id
  rule_number    = 100
  egress         = true
  protocol       = "-1" # All protocols
  rule_action    = "allow"
  cidr_block     = var.vpc_cidr
}

# Allow HTTPS to internet (for package updates, API calls, etc.)
resource "aws_network_acl_rule" "private_outbound_https" {
  network_acl_id = aws_network_acl.private.id
  rule_number    = 110
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 443
  to_port        = 443
}

# Allow HTTP to internet (for connectivity testing and redirects)
resource "aws_network_acl_rule" "private_outbound_http" {
  network_acl_id = aws_network_acl.private.id
  rule_number    = 120
  egress         = true
  protocol       = "tcp"
  rule_action    = "allow"
  cidr_block     = "0.0.0.0/0"
  from_port      = 80
  to_port        = 80
}

# Private NACL Subnet Associations
resource "aws_network_acl_association" "private" {
  count = local.az_count

  network_acl_id = aws_network_acl.private.id
  subnet_id      = aws_subnet.private[count.index].id
}
