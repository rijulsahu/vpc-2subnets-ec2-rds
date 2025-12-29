# Output values for VPC Best Practices deployment

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "vpc_arn" {
  description = "ARN of the VPC"
  value       = aws_vpc.main.arn
}

# Internet Gateway Outputs
output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "internet_gateway_arn" {
  description = "ARN of the Internet Gateway"
  value       = aws_internet_gateway.main.arn
}

# NAT Gateway Outputs
output "nat_gateway_ids" {
  description = "IDs of NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_public_ips" {
  description = "Public IP addresses of NAT Gateways"
  value       = aws_eip.nat[*].public_ip
}

output "nat_gateway_allocation_ids" {
  description = "Allocation IDs of Elastic IPs for NAT Gateways"
  value       = aws_eip.nat[*].id
}

output "nat_gateway_strategy" {
  description = "NAT Gateway deployment strategy (per_az or single)"
  value       = var.nat_gateway_strategy
}

output "nat_gateway_count" {
  description = "Number of NAT Gateways deployed"
  value       = local.nat_gateway_count
}

# Route Table Outputs
output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

output "public_route_table_associations" {
  description = "IDs of public subnet route table associations"
  value       = aws_route_table_association.public[*].id
}

output "private_route_table_ids" {
  description = "IDs of private route tables"
  value       = aws_route_table.private[*].id
}

output "private_route_table_associations" {
  description = "IDs of private subnet route table associations"
  value       = aws_route_table_association.private[*].id
}

output "route_table_ids" {
  description = "Map of route table names to IDs for easy reference"
  value = {
    public  = aws_route_table.public.id
    private = aws_route_table.private[*].id
  }
}
# Network ACL Outputs
output "public_nacl_id" {
  description = "ID of the public network ACL"
  value       = aws_network_acl.public.id
}

output "public_nacl_associations" {
  description = "IDs of public NACL subnet associations"
  value       = aws_network_acl_association.public[*].id
}

output "private_nacl_id" {
  description = "ID of the private network ACL"
  value       = aws_network_acl.private.id
}

output "private_nacl_associations" {
  description = "IDs of private NACL subnet associations"
  value       = aws_network_acl_association.private[*].id
}

# Security Group Outputs
output "bastion_sg_id" {
  description = "ID of the bastion security group"
  value       = aws_security_group.bastion.id
}

output "web_sg_id" {
  description = "ID of the web security group"
  value       = aws_security_group.web.id
}

output "application_sg_id" {
  description = "ID of the application security group"
  value       = aws_security_group.application.id
}

output "database_sg_id" {
  description = "ID of the database security group"
  value       = aws_security_group.database.id
}

output "security_group_ids" {
  description = "Map of security group names to IDs for easy reference"
  value = {
    bastion     = aws_security_group.bastion.id
    web         = aws_security_group.web.id
    application = aws_security_group.application.id
    database    = aws_security_group.database.id
  }
}

output "default_security_group_id" {
  description = "ID of the default security group (restricted)"
  value       = aws_default_security_group.default.id
}
# Availability Zone Outputs
output "availability_zones" {
  description = "List of availability zones used"
  value       = local.availability_zones
}

output "az_count" {
  description = "Number of availability zones used"
  value       = local.az_count
}

# Subnet Outputs
output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "public_subnet_cidrs" {
  description = "CIDR blocks of public subnets"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "private_subnet_cidrs" {
  description = "CIDR blocks of private subnets"
  value       = aws_subnet.private[*].cidr_block
}

output "subnet_availability_zones" {
  description = "Map of subnet IDs to their availability zones"
  value = {
    public = zipmap(
      aws_subnet.public[*].id,
      aws_subnet.public[*].availability_zone
    )
    private = zipmap(
      aws_subnet.private[*].id,
      aws_subnet.private[*].availability_zone
    )
  }
}

# VPC Flow Logs Outputs
output "flow_logs_log_group_name" {
  description = "CloudWatch Log Group name for VPC Flow Logs"
  value       = var.enable_vpc_flow_logs ? aws_cloudwatch_log_group.flow_logs[0].name : null
}

output "flow_logs_log_group_arn" {
  description = "ARN of the CloudWatch Log Group for VPC Flow Logs"
  value       = var.enable_vpc_flow_logs ? aws_cloudwatch_log_group.flow_logs[0].arn : null
}

output "flow_logs_iam_role_arn" {
  description = "ARN of the IAM role used by VPC Flow Logs"
  value       = var.enable_vpc_flow_logs ? aws_iam_role.flow_logs[0].arn : null
}

output "flow_logs_id" {
  description = "ID of the VPC Flow Log"
  value       = var.enable_vpc_flow_logs ? aws_flow_log.main[0].id : null
}

# Deployment Information
output "deployment_info" {
  description = "Information about the deployment"
  value = {
    region               = data.aws_region.current.name
    account_id           = data.aws_caller_identity.current.account_id
    project              = var.project_name
    environment          = var.environment
    nat_gateway_strategy = var.nat_gateway_strategy
    flow_logs_enabled    = var.enable_vpc_flow_logs
  }
}
# Comprehensive Summary Output
# Useful for module consumption and documentation
output "vpc_summary" {
  description = "Comprehensive summary of VPC infrastructure for easy module consumption"
  value = {
    vpc = {
      id         = aws_vpc.main.id
      cidr       = aws_vpc.main.cidr_block
      arn        = aws_vpc.main.arn
      region     = data.aws_region.current.name
      account_id = data.aws_caller_identity.current.account_id
    }
    networking = {
      internet_gateway_id   = aws_internet_gateway.main.id
      nat_gateway_ids       = aws_nat_gateway.main[*].id
      nat_gateway_public_ips = aws_eip.nat[*].public_ip
      nat_strategy          = var.nat_gateway_strategy
    }
    subnets = {
      public_ids   = aws_subnet.public[*].id
      public_cidrs = aws_subnet.public[*].cidr_block
      private_ids  = aws_subnet.private[*].id
      private_cidrs = aws_subnet.private[*].cidr_block
    }
    availability_zones = {
      zones = local.availability_zones
      count = local.az_count
    }
    security_groups = {
      bastion     = aws_security_group.bastion.id
      web         = aws_security_group.web.id
      application = aws_security_group.application.id
      database    = aws_security_group.database.id
      default     = aws_default_security_group.default.id
    }
    route_tables = {
      public_id   = aws_route_table.public.id
      private_ids = aws_route_table.private[*].id
    }
    network_acls = {
      public_id  = aws_network_acl.public.id
      private_id = aws_network_acl.private.id
    }
    flow_logs = {
      enabled        = var.enable_vpc_flow_logs
      log_group_name = var.enable_vpc_flow_logs ? aws_cloudwatch_log_group.flow_logs[0].name : null
      log_group_arn  = var.enable_vpc_flow_logs ? aws_cloudwatch_log_group.flow_logs[0].arn : null
    }
  }
}