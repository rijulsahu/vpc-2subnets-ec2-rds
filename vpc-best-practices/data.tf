# Data source for availability zones
# Automatically discovers available AZs in the selected region
data "aws_availability_zones" "available" {
  state = "available"

  # Exclude local zones and wavelength zones
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# Data source for current AWS account information
data "aws_caller_identity" "current" {}

# Data source for current AWS region
data "aws_region" "current" {}
