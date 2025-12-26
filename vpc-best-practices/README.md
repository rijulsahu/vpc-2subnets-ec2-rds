# VPC Best Practices Deployment

Production-ready AWS VPC deployment following best practices for network architecture, security, high availability, and cost optimization.

## Features

- ✅ **Multi-AZ Architecture**: Resources distributed across 2+ availability zones
- ✅ **Network Segmentation**: Separate public and private subnets
- ✅ **High Availability**: Redundant NAT Gateways (configurable)
- ✅ **Layered Security**: NACLs + multi-tier security groups
- ✅ **Monitoring**: VPC Flow Logs with CloudWatch integration
- ✅ **Cost Optimization**: Configurable NAT Gateway strategy
- ✅ **Best Practices**: Following AWS Well-Architected Framework

## Architecture

```
Internet → Internet Gateway → Public Subnets (Multi-AZ)
                                      ↓
                               NAT Gateways (Multi-AZ)
                                      ↓
                            Private Subnets (Multi-AZ)
                                      ↓
                            Application Resources
```

## Prerequisites

- [OpenTofu](https://opentofu.org/) >= 1.6.0 or Terraform >= 1.6.0
- AWS CLI configured with appropriate credentials
- AWS account with permissions to create VPC resources

## Quick Start

1. **Clone and navigate to the directory**:
   ```bash
   cd vpc-best-practices
   ```

2. **Copy example configuration**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit variables** (optional):
   ```bash
   # Edit terraform.tfvars with your preferences
   ```

4. **Initialize OpenTofu**:
   ```bash
   tofu init
   ```

5. **Review the plan**:
   ```bash
   tofu plan
   ```

6. **Apply the configuration**:
   ```bash
   tofu apply
   ```

## Project Structure

```
vpc-best-practices/
├── versions.tf          # Provider version constraints
├── data.tf             # Data sources (AZs, account info)
├── locals.tf           # Local values and calculations
├── variables.tf        # Input variables
├── outputs.tf          # Output values
├── main.tf             # VPC resource
├── subnets.tf          # Subnet resources (to be created)
├── nat_gateway.tf      # NAT Gateway resources (to be created)
├── route_tables.tf     # Route tables (to be created)
├── security_groups.tf  # Security groups (to be created)
├── nacls.tf            # Network ACLs (to be created)
├── flow_logs.tf        # VPC Flow Logs (to be created)
└── README.md           # This file
```

## Configuration

### Key Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `vpc_cidr` | `10.0.0.0/16` | VPC CIDR block |
| `az_count` | `2` | Number of availability zones |
| `nat_gateway_strategy` | `per_az` | NAT strategy: `per_az` or `single` |
| `enable_vpc_flow_logs` | `true` | Enable VPC Flow Logs |
| `environment` | `development` | Environment name |

### Deployment Scenarios

**Production (High Availability)**:
- NAT Gateway per AZ: `nat_gateway_strategy = "per_az"`
- VPC Flow Logs enabled
- Cost: ~$65/month (for 2 NAT Gateways)

**Development (Cost Optimized)**:
- Single NAT Gateway: `nat_gateway_strategy = "single"`
- VPC Flow Logs optional
- Cost: ~$32/month

## Outputs

After deployment, you'll see:
- VPC ID and CIDR
- Subnet IDs (public and private)
- NAT Gateway IDs
- Security Group IDs
- Availability zones used

## Cost Estimation

| Resource | Quantity | Monthly Cost |
|----------|----------|--------------|
| VPC | 1 | $0 |
| Subnets | 4 | $0 |
| Internet Gateway | 1 | $0 |
| NAT Gateway (HA) | 2 | ~$64.80 |
| NAT Gateway (Single) | 1 | ~$32.40 |
| VPC Flow Logs | 1 | ~$0.50-2.00 |

## Next Steps

This is Task 1 (Foundation Setup). Next tasks will add:
- Subnet creation (public and private)
- Internet Gateway
- NAT Gateways with HA
- Route tables
- Network ACLs
- Security groups (layered)
- VPC Flow Logs

## Documentation

For complete documentation, see:
- [Requirements](../.kiro/specs/vpc-best-practices/requirements.md)
- [Design](../.kiro/specs/vpc-best-practices/design.md)
- [Tasks](../.kiro/specs/vpc-best-practices/tasks.md)
- [Comparison with Simple EC2](../.kiro/specs/vpc-best-practices/COMPARISON.md)

## Status

✅ Task 1: Project structure and provider configuration - **COMPLETE**

## License

This is part of a learning and demonstration project.
