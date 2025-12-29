# Local values for common calculations and configurations

locals {
  # Common tags applied to all resources
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "opentofu"
    CostCenter  = var.cost_center
    Owner       = var.owner
    Terraform   = "true"
  }

  # Determine availability zones to use
  # If user provides specific AZs, use those; otherwise use first N available AZs
  availability_zones = length(var.availability_zones) > 0 ? var.availability_zones : slice(
    data.aws_availability_zones.available.names,
    0,
    var.az_count
  )

  # Number of AZs being used
  az_count = length(local.availability_zones)

  # Subnet-specific tags
  public_subnet_tags = {
    Type = "public"
    Tier = "dmz"
  }

  private_subnet_tags = {
    Type = "private"
    Tier = "application"
  }

  # NAT Gateway configuration
  # For 'per_az' strategy, create one NAT per AZ
  # For 'single' strategy, create only one NAT
  nat_gateway_count = var.nat_gateway_strategy == "per_az" ? local.az_count : 1

  # Calculate VPC name
  vpc_name = "${var.project_name}-vpc-${var.environment}"

  # Common resource prefix for consistent naming
  resource_prefix = "${var.project_name}-${var.environment}"

  # Generate subnet names dynamically
  public_subnet_names = [
    for idx, az in local.availability_zones :
    "${var.project_name}-public-subnet-${var.environment}-${substr(az, -1, 1)}"
  ]

  private_subnet_names = [
    for idx, az in local.availability_zones :
    "${var.project_name}-private-subnet-${var.environment}-${substr(az, -1, 1)}"
  ]
}
