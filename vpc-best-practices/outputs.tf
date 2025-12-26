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

# Availability Zone Outputs
output "availability_zones" {
  description = "List of availability zones used"
  value       = local.availability_zones
}

output "az_count" {
  description = "Number of availability zones used"
  value       = local.az_count
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
