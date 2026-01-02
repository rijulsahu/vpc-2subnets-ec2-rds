# VPC Best Practices - Production-Ready AWS VPC Module

A comprehensive, production-ready OpenTofu/Terraform module for deploying highly available, secure AWS VPC infrastructure following AWS Well-Architected Framework principles.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Configuration Options](#configuration-options)
- [Cost Optimization](#cost-optimization)
- [Security Considerations](#security-considerations)
- [High Availability](#high-availability)
- [Outputs](#outputs)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Design Decisions](#design-decisions)
- [Requirements Traceability](#requirements-traceability)

## Overview

This module creates a production-ready VPC infrastructure with:
- Multi-AZ deployment for high availability
- Public and private subnets across availability zones
- NAT Gateway with flexible HA strategies
- Network Access Control Lists (NACLs) for subnet-level security
- Security Groups implementing defense-in-depth
- VPC Flow Logs for network monitoring (optional)
- Comprehensive tagging for cost tracking and resource management

**Key Benefits:**
- ✅ Production-ready out of the box
- ✅ Flexible NAT Gateway strategy (cost vs. availability trade-off)
- ✅ Defense-in-depth security architecture
- ✅ Multi-AZ high availability
- ✅ Comprehensive monitoring and logging
- ✅ Cost optimization options
- ✅ Extensively tested with property-based and integration tests

## Architecture

### Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS VPC (10.0.0.0/16)                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Internet Gateway                     │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                         │                                       │
│  ┌──────────────────────┴─────────────────────────────────┐     │
│  │                  Public Route Table                    │     │
│  │              0.0.0.0/0 -> Internet Gateway             │     │
│  └──────┬───────────────────────────┬─────────────────────┘     │
│         │                           │                           │
│  ┌──────▼──────────────┐    ┌──────▼──────────────┐             │
│  │  Public Subnet      │    │  Public Subnet      │             │
│  │  us-east-1a         │    │  us-east-1b         │             │
│  │  10.0.1.0/24        │    │  10.0.2.0/24        │             │
│  │  ┌────────────┐     │    │  ┌────────────┐     │             │
│  │  │ NAT Gateway│     │    │  │ NAT Gateway│     │             │
│  │  │ + EIP      │     │    │  │ + EIP      │     │             │
│  │  └──────┬─────┘     │    │  └──────┬─────┘     │             │
│  └─────────┼───────────┘    └─────────┼───────────┘             │
│            │                           │                        │
│  ┌─────────▼───────────┐    ┌─────────▼───────────┐             │
│  │ Private Route Table │    │ Private Route Table │             │
│  │ 0.0.0.0/0 -> NAT-1a │    │ 0.0.0.0/0 -> NAT-1b │             │
│  └─────────┬───────────┘    └─────────┬───────────┘             │
│            │                           │                        │
│  ┌─────────▼───────────┐    ┌─────────▼───────────┐             │
│  │ Private Subnet      │    │ Private Subnet      │             │
│  │ us-east-1a          │    │ us-east-1b          │             │
│  │ 10.0.11.0/24        │    │ 10.0.12.0/24        │             │
│  └─────────────────────┘    └─────────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Security Architecture (4-Tier Model)

```
Internet
   │
   │ HTTP/HTTPS (80, 443)
   ▼
┌──────────────────┐
│   Bastion SG     │ ← SSH from Admin CIDRs (22)
│   (Bastion Host) │
└────────┬─────────┘
         │ SSH (22)
         │
┌────────▼─────────┐
│     Web SG       │ ← HTTP/HTTPS from Internet (80, 443)
│  (Load Balancer) │
└────────┬─────────┘
         │ Custom Ports
         │
┌────────▼─────────┐
│  Application SG  │ ← From Web SG + Bastion SG
│  (App Servers)   │
└────────┬─────────┘
         │ DB Port (3306/5432)
         │
┌────────▼─────────┐
│   Database SG    │ ← From Application SG only
│   (RDS/EC2 DB)   │
└──────────────────┘
```

## Features

### Network Infrastructure
- **VPC**: IPv4 CIDR block (/16 recommended), DNS hostnames and DNS support enabled
- **Subnets**: Public and private subnets distributed across multiple AZs
- **Internet Gateway**: Single IGW attached to VPC for public subnet internet access
- **NAT Gateways**: Flexible strategy (per-AZ for HA or single for cost optimization)
- **Route Tables**: Separate route tables for public/private subnets with proper associations

### Security
- **NACLs**: Stateless firewall rules at subnet level
  - Public NACL: Allows HTTP (80), HTTPS (443), SSH (22), ephemeral ports
  - Private NACL: Allows VPC CIDR traffic and ephemeral ports
- **Security Groups**: Stateful firewall implementing 4-tier architecture
  - Bastion SG: SSH access point
  - Web SG: Internet-facing load balancers
  - Application SG: Internal application servers
  - Database SG: Database tier with strict access control
- **Default Security Group**: Hardened with no rules (deny all)
- **Flow Logs**: Optional VPC Flow Logs to CloudWatch for traffic analysis

### High Availability
- **Multi-AZ Deployment**: Resources distributed across 2+ availability zones
- **NAT Gateway HA**: Optional per-AZ NAT gateways eliminate single point of failure
- **Redundant Routing**: Each AZ has independent route to NAT Gateway
- **AZ Failure Tolerance**: Infrastructure continues operating if one AZ fails

### Operational Excellence
- **Comprehensive Tags**: Project, Environment, ManagedBy, CostCenter, Owner tags
- **Detailed Outputs**: All resource IDs exported for downstream modules
- **Parameterized Configuration**: Fully customizable via variables
- **Cost Visibility**: Tags enable cost tracking and allocation

## Prerequisites

### Required Tools
- **OpenTofu** >= 1.6.0 or **Terraform** >= 1.6.0
- **AWS CLI** >= 2.0 (for integration tests)
- **Python** >= 3.8 (for running tests)
- **uv** (Python package manager, for running tests)

### AWS Permissions
The AWS credentials used must have permissions to create:
- VPC, Subnets, Internet Gateway
- NAT Gateway, Elastic IPs
- Route Tables, Network ACLs
- Security Groups
- VPC Flow Logs (if enabled)
- CloudWatch Log Groups (if Flow Logs enabled)
- IAM Roles and Policies (if Flow Logs enabled)

### AWS Service Limits
Ensure your AWS account has sufficient limits for:
- VPCs per region (default: 5)
- NAT Gateways per AZ (default: 5)
- Elastic IPs per region (default: 5)
- Security Groups per VPC (default: 2500)

## Quick Start

### 1. Clone or Reference the Module

For local development:
```bash
cd vpc-best-practices
```

Or reference as a module:
```hcl
module "vpc" {
  source = "./vpc-best-practices"
  
  # Required variables
  project_name = "my-project"
  environment  = "production"
  vpc_cidr     = "10.0.0.0/16"
  
  # See configuration options below for more settings
}
```

### 2. Create terraform.tfvars

```hcl
project_name            = "my-project"
environment             = "production"
vpc_cidr                = "10.0.0.0/16"
availability_zones      = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs     = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs    = ["10.0.11.0/24", "10.0.12.0/24"]
nat_gateway_strategy    = "per_az"
enable_vpc_flow_logs    = true
admin_cidr_blocks       = ["203.0.113.0/24"]  # Your office/VPN IP
cost_center             = "engineering"
owner                   = "infrastructure-team"
```

### 3. Initialize and Apply

```bash
# Initialize OpenTofu/Terraform
tofu init

# Review the plan
tofu plan

# Apply the configuration
tofu apply
```

## Usage Examples

### Example 1: Production Environment (HA)

**Scenario**: Production workload requiring maximum availability

```hcl
# production.tfvars
project_name            = "my-app"
environment             = "production"
vpc_cidr                = "10.0.0.0/16"
availability_zones      = ["us-east-1a", "us-east-1b", "us-east-1c"]
public_subnet_cidrs     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnet_cidrs    = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
nat_gateway_strategy    = "per_az"           # HA: one NAT per AZ
enable_vpc_flow_logs    = true               # Enable monitoring
admin_cidr_blocks       = ["10.50.0.0/16"]   # Corporate VPN
cost_center             = "production-ops"
owner                   = "platform-team"
```

**Cost**: ~$96/month for NAT Gateways (3 AZs × $32/month)

### Example 2: Development Environment (Cost-Optimized)

**Scenario**: Development workload where cost is more important than HA

```hcl
# dev.tfvars
project_name            = "my-app"
environment             = "dev"
vpc_cidr                = "10.1.0.0/16"
availability_zones      = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs     = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnet_cidrs    = ["10.1.11.0/24", "10.1.12.0/24"]
nat_gateway_strategy    = "single"           # Cost-optimized: single NAT
enable_vpc_flow_logs    = false              # Disable to reduce costs
admin_cidr_blocks       = ["0.0.0.0/0"]      # Less restrictive for dev
cost_center             = "development"
owner                   = "dev-team"
```

**Cost**: ~$32/month for NAT Gateway (1 × $32/month)

### Example 3: Staging Environment (Balanced)

**Scenario**: Pre-production testing with moderate HA requirements

```hcl
# staging.tfvars
project_name            = "my-app"
environment             = "staging"
vpc_cidr                = "10.2.0.0/16"
availability_zones      = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs     = ["10.2.1.0/24", "10.2.2.0/24"]
private_subnet_cidrs    = ["10.2.11.0/24", "10.2.12.0/24"]
nat_gateway_strategy    = "per_az"           # HA for realistic testing
enable_vpc_flow_logs    = false              # Disable to reduce costs
admin_cidr_blocks       = ["10.50.0.0/16"]
cost_center             = "staging-ops"
owner                   = "qa-team"
```

**Cost**: ~$64/month for NAT Gateways (2 AZs × $32/month)

### Example 4: Using Module Outputs

```hcl
# main.tf
module "vpc" {
  source = "./vpc-best-practices"
  
  # ... configuration ...
}

# Deploy EC2 instance in private subnet
resource "aws_instance" "app_server" {
  ami                    = "ami-12345678"
  instance_type          = "t3.medium"
  subnet_id              = module.vpc.private_subnet_ids[0]
  vpc_security_group_ids = [module.vpc.security_group_ids["application"]]
  
  tags = {
    Name = "app-server"
  }
}

# Deploy RDS in private subnet
resource "aws_db_subnet_group" "database" {
  name       = "db-subnet-group"
  subnet_ids = module.vpc.private_subnet_ids
  
  tags = {
    Name = "database-subnet-group"
  }
}

resource "aws_db_instance" "database" {
  # ... other configuration ...
  db_subnet_group_name   = aws_db_subnet_group.database.name
  vpc_security_group_ids = [module.vpc.security_group_ids["database"]]
}
```

## Configuration Options

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `project_name` | string | Name of the project (used in resource naming and tags) |
| `environment` | string | Environment name (e.g., dev, staging, production) |
| `vpc_cidr` | string | CIDR block for VPC (must be /16) |
| `availability_zones` | list(string) | List of AZs to use (minimum 2) |
| `public_subnet_cidrs` | list(string) | CIDR blocks for public subnets (one per AZ) |
| `private_subnet_cidrs` | list(string) | CIDR blocks for private subnets (one per AZ) |
| `cost_center` | string | Cost center for billing/chargeback |
| `owner` | string | Team or individual responsible for resources |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `nat_gateway_strategy` | string | `"per_az"` | NAT strategy: `"per_az"` (HA) or `"single"` (cost-optimized) |
| `enable_vpc_flow_logs` | bool | `true` | Enable VPC Flow Logs to CloudWatch |
| `admin_cidr_blocks` | list(string) | `[]` | CIDR blocks allowed SSH access to bastion |

### Variable Validation

The module includes comprehensive validation:
- VPC CIDR must be /16
- Number of subnet CIDRs must match number of AZs
- NAT strategy must be "per_az" or "single"
- Minimum 2 availability zones required

## Cost Optimization

### Cost Comparison: NAT Gateway Strategies

| Strategy | Monthly Cost | Use Case | Availability |
|----------|--------------|----------|--------------|
| **Single NAT** | $32/month | Dev, Test, Non-Critical | Single AZ failure causes outage |
| **Per-AZ NAT (2 AZ)** | $64/month | Staging, Production | Survives single AZ failure |
| **Per-AZ NAT (3 AZ)** | $96/month | Critical Production | Survives loss of 2 AZs |

**Additional Costs:**
- Data processing: $0.045/GB
- Data transfer: $0.09/GB (internet out)
- VPC Flow Logs: ~$0.50/GB ingested to CloudWatch
- CloudWatch storage: $0.03/GB/month

### Cost Optimization Strategies

1. **Development Environments**
   - Use `nat_gateway_strategy = "single"`
   - Set `enable_vpc_flow_logs = false`
   - Use fewer availability zones (2 instead of 3)

2. **Staging Environments**
   - Consider single NAT if HA testing not required
   - Disable Flow Logs unless debugging networking issues
   - Use 2 AZs instead of 3

3. **Production Environments**
   - Use `nat_gateway_strategy = "per_az"` for HA
   - Enable Flow Logs for security monitoring
   - Use 2-3 AZs based on availability requirements

4. **General Tips**
   - Use VPC endpoints for AWS services (S3, DynamoDB) to avoid NAT charges
   - Monitor data transfer patterns
   - Use Cost Explorer tags to track VPC costs by environment
   - Consider AWS NAT instances for very low traffic workloads

### Monthly Cost Estimate

**Production (3 AZ, HA)**
- NAT Gateways: $96/month
- Data processing (100GB): $4.50/month
- Flow Logs (50GB): $25/month
- **Total: ~$125/month**

**Dev/Test (2 AZ, Single NAT)**
- NAT Gateway: $32/month
- Data processing (20GB): $0.90/month
- Flow Logs: $0 (disabled)
- **Total: ~$33/month**

## Security Considerations

### Network Access Control Lists (NACLs)

**Public NACL Rules:**
- Inbound: HTTP (80), HTTPS (443), SSH (22), Ephemeral (1024-65535)
- Outbound: All traffic allowed

**Private NACL Rules:**
- Inbound: VPC CIDR traffic, Ephemeral ports
- Outbound: VPC CIDR traffic, HTTP (80), HTTPS (443)

### Security Groups

**4-Tier Architecture:**

1. **Bastion Security Group**
   - Ingress: SSH (22) from admin CIDR blocks only
   - Egress: SSH (22) to application security group

2. **Web Security Group**
   - Ingress: HTTP (80), HTTPS (443) from 0.0.0.0/0
   - Egress: Custom ports to application security group

3. **Application Security Group**
   - Ingress: From web SG and bastion SG
   - Egress: Database ports to database SG, HTTPS to internet

4. **Database Security Group**
   - Ingress: Database ports from application SG only
   - Egress: Minimal (responses only)

### Security Best Practices

✅ **Implemented:**
- Default security group has no rules (deny all)
- Private subnets have no public IPs
- Security groups use references (not CIDR blocks) for inter-tier communication
- NACLs provide defense-in-depth
- Bastion is sole SSH entry point
- Database tier completely isolated from internet

⚠️ **Additional Recommendations:**
- Rotate bastion host keys regularly
- Use AWS Systems Manager Session Manager instead of SSH where possible
- Enable GuardDuty for threat detection
- Implement AWS Config rules for compliance monitoring
- Use AWS Security Hub for centralized security findings
- Consider AWS Network Firewall for advanced threat protection

## High Availability

### Multi-AZ Architecture

The module deploys resources across multiple availability zones:
- **Subnets**: One public and one private subnet per AZ
- **NAT Gateways**: One per AZ (with per_az strategy)
- **Route Tables**: Separate private route table per AZ

### Failure Scenarios

| Scenario | Impact (per_az) | Impact (single) |
|----------|-----------------|-----------------|
| **AZ Failure** | Affected AZ loses connectivity; other AZs continue | Affected AZ loses connectivity |
| **NAT Gateway Failure** | Only affected AZ loses internet; others continue | ALL private subnets lose internet |
| **IGW Failure** | All public subnet traffic affected (AWS manages IGW HA) | Same |
| **Route Table Issue** | Only affected AZ/subnet impacted | Dependent on issue scope |

### High Availability Features

✅ **Multi-AZ subnet distribution**: Resources deployed across 2+ AZs
✅ **Independent routing per AZ**: Each AZ has own route to NAT Gateway
✅ **NAT Gateway redundancy**: Optional per-AZ NAT eliminates SPOF
✅ **AZ failure tolerance**: Infrastructure continues if one AZ fails
✅ **Automatic failover**: Route tables automatically route to available NAT

### Recommendations

**Production Workloads:**
- Use minimum 2 availability zones (3 for critical workloads)
- Enable `nat_gateway_strategy = "per_az"`
- Deploy application instances across all AZs
- Use Application Load Balancer (ALB) for cross-AZ load balancing
- Enable Cross-Zone Load Balancing

**Monitoring:**
- Enable VPC Flow Logs
- Set CloudWatch alarms for NAT Gateway metrics
- Monitor AZ-specific metrics
- Implement health checks for critical resources

## Outputs

The module provides comprehensive outputs for downstream consumption:

### Network Outputs
```hcl
output "vpc_id"                    # VPC ID
output "vpc_cidr"                  # VPC CIDR block
output "public_subnet_ids"         # List of public subnet IDs
output "private_subnet_ids"        # List of private subnet IDs
output "internet_gateway_id"       # Internet Gateway ID
output "nat_gateway_ids"           # List of NAT Gateway IDs (or single ID)
output "nat_gateway_public_ips"    # List of Elastic IPs for NAT Gateways
```

### Security Outputs
```hcl
output "security_group_ids"        # Map of security group IDs by tier
                                   # { bastion, web, application, database }
output "public_nacl_id"            # Public NACL ID
output "private_nacl_id"           # Private NACL ID
```

### Routing Outputs
```hcl
output "route_table_ids"           # Map of route table IDs
                                   # { public, private-1a, private-1b, ... }
output "public_route_table_id"     # Public route table ID
output "private_route_table_ids"   # List of private route table IDs
```

### Monitoring Outputs
```hcl
output "flow_log_id"               # VPC Flow Log ID (if enabled)
output "flow_log_cloudwatch_group" # CloudWatch Log Group name (if enabled)
```

### Comprehensive Summary
```hcl
output "vpc_summary"               # Complete VPC configuration summary
# Includes: VPC ID, CIDR, AZs, subnet counts, NAT strategy, Flow Logs status
```

## Testing

The module includes comprehensive testing at multiple levels:

### Property-Based Tests

Located in `test/` directory. Run with:
```bash
cd test
uv run <test_file>.py
```

**Available Tests:**
- `vpc_cidr_test.py` - VPC CIDR configuration
- `subnet_distribution_test.py` - Multi-AZ subnet distribution
- `nat_gateway_ha_test.py` - NAT Gateway HA configuration
- `route_tables_test.py` - Route table associations
- `nacl_rules_test.py` - NACL rule compliance
- `security_groups_test.py` - Security group configuration
- `flow_logs_test.py` - VPC Flow Logs setup
- `ha_distribution_test.py` - HA resource distribution
- `security_best_practices_test.py` - Security hardening
- `code_organization_test.py` - Infrastructure organization
- `tagging_consistency_test.py` - Resource tagging

### Integration Tests

**⚠️ WARNING: Integration tests create real AWS resources and incur costs.**

Located in `test/` directory. Run with:
```bash
cd test
uv run <integration_test>.py
```

**Available Integration Tests:**
- `network_connectivity_integration_test.py` - End-to-end connectivity validation
- `ha_behavior_integration_test.py` - HA failure simulation
- `security_validation_integration_test.py` - Security controls validation

**Cost Estimates:**
- Network connectivity test: ~$0.10 (5 minutes)
- HA behavior test: ~$0.20 (10 minutes)
- Security validation test: ~$0.15 (7 minutes)

### Running All Tests

```bash
# Run all property tests
cd test
for test in *_test.py; do
    if [[ $test != *"integration"* ]]; then
        echo "Running $test"
        uv run $test
    fi
done

# Run integration tests (requires AWS credentials and incurs costs)
uv run network_connectivity_integration_test.py
uv run ha_behavior_integration_test.py
uv run security_validation_integration_test.py
```

## Troubleshooting

### Common Issues

#### Issue: NAT Gateway creation fails

**Symptoms:** Error creating NAT Gateway
```
Error: error creating EC2 NAT Gateway: NatGatewayLimitExceeded
```

**Solution:**
- Check NAT Gateway limits in your AWS account
- Request limit increase via AWS Support
- Consider using single NAT strategy for dev/test environments

#### Issue: Insufficient Elastic IPs

**Symptoms:** Error allocating Elastic IP
```
Error: error allocating EC2 EIP: AddressLimitExceeded
```

**Solution:**
- Release unused Elastic IPs in your account
- Request limit increase via AWS Support
- Each NAT Gateway requires one EIP

#### Issue: CIDR overlap with existing VPCs

**Symptoms:** Unable to peer VPCs
```
Error: CIDR block conflicts with existing VPC
```

**Solution:**
- Use non-overlapping CIDR blocks for different VPCs
- Plan your IP address space before deployment
- Common ranges: 10.0.0.0/16, 10.1.0.0/16, 10.2.0.0/16, etc.

#### Issue: Cannot SSH to instances in private subnet

**Symptoms:** SSH timeout when connecting to private instances

**Solution:**
- Use bastion host as jump server
- Verify bastion security group allows SSH from your IP
- Verify application security group allows SSH from bastion SG
- Check NACL rules allow ephemeral ports
- Verify route table has route to NAT Gateway

**SSH via bastion example:**
```bash
# Copy key to bastion
scp -i mykey.pem mykey.pem ec2-user@bastion-ip:/home/ec2-user/

# SSH to bastion
ssh -i mykey.pem ec2-user@bastion-ip

# From bastion, SSH to private instance
ssh -i mykey.pem ec2-user@private-instance-ip
```

#### Issue: VPC Flow Logs not working

**Symptoms:** No flow logs appearing in CloudWatch

**Solution:**
- Verify `enable_vpc_flow_logs = true`
- Check IAM role has correct permissions
- Verify CloudWatch Log Group exists
- Check VPC Flow Log resource is created
- Allow 10-15 minutes for first logs to appear

#### Issue: Terraform state lock errors

**Symptoms:** Error acquiring state lock

**Solution:**
- Ensure no other tofu/terraform processes running
- If using remote state, verify DynamoDB table access
- Force unlock if necessary (use with caution):
  ```bash
  tofu force-unlock <lock-id>
  ```

#### Issue: High NAT Gateway costs

**Symptoms:** Unexpected AWS bill for NAT Gateway data processing

**Solution:**
- Review data transfer patterns with VPC Flow Logs
- Implement VPC endpoints for AWS services (S3, DynamoDB)
- Consider using NAT instances for low-traffic workloads
- Use single NAT strategy for dev/test environments
- Monitor with AWS Cost Explorer and set billing alerts

### Debug Mode

Enable detailed logging:
```bash
# OpenTofu debug logging
export TF_LOG=DEBUG
export TF_LOG_PATH=./terraform-debug.log
tofu plan

# AWS CLI debug logging
aws ec2 describe-vpcs --debug
```

### Getting Help

1. **Check AWS Service Health Dashboard**: https://health.aws.amazon.com/
2. **Review CloudWatch Logs**: Check Flow Logs for traffic patterns
3. **AWS Support**: Open a support case for AWS-specific issues
4. **Community Forums**: AWS re:Post, HashiCorp Discuss

## Design Decisions

### Why /16 VPC CIDR?

**Decision:** Enforce /16 CIDR block for VPC

**Rationale:**
- Provides 65,536 IP addresses (sufficient for most use cases)
- Follows AWS best practices for VPC sizing
- Allows for future subnet expansion
- Standard size enables consistent network design

**Trade-offs:**
- May be oversized for very small deployments
- Consider /20 or /24 for lab environments

### Why Separate Route Tables per AZ?

**Decision:** Create separate private route table for each AZ

**Rationale:**
- Enables per-AZ NAT Gateway routing
- Isolates AZ failures (one AZ failure doesn't affect others)
- Required for true multi-AZ high availability
- Allows AZ-specific routing policies if needed

**Trade-offs:**
- More route tables to manage (minimal overhead)
- Slightly more complex than single route table

### Why Security Group References vs. CIDR Blocks?

**Decision:** Use security group references for inter-tier communication

**Rationale:**
- Automatic IP tracking (no need to update when IPs change)
- More maintainable and less error-prone
- Follows AWS best practices
- Better security posture (principle of least privilege)

**Trade-offs:**
- Slightly more complex to understand initially
- Requires proper SG planning

### Why Default Security Group Restriction?

**Decision:** Restrict default security group with no rules

**Rationale:**
- Prevents accidental use of default SG
- Forces explicit security group assignment
- Follows security best practices
- Reduces attack surface

**Trade-offs:**
- Resources without explicit SG assignment will have no connectivity
- Requires developers to specify SG explicitly

### Why Optional VPC Flow Logs?

**Decision:** Make Flow Logs optional via variable

**Rationale:**
- Cost optimization for dev/test environments
- Not all environments need detailed traffic logging
- Can add significant CloudWatch costs
- Easy to enable when needed

**Trade-offs:**
- Less visibility in environments with Flow Logs disabled
- May miss security incidents in dev/test

### Why Four-Tier Security Group Model?

**Decision:** Implement bastion, web, application, database security groups

**Rationale:**
- Defense-in-depth security architecture
- Clear separation of concerns
- Supports common application architectures
- Bastion provides secure access pattern

**Trade-offs:**
- May be over-engineered for simple applications
- Requires understanding of security group chains

## Requirements Traceability

This module implements all requirements from the VPC Best Practices specification:

### VPC Requirements (1.x)
- ✅ 1.1: VPC with /16 CIDR block
- ✅ 1.2: Multi-AZ deployment (2+ AZs)
- ✅ 1.3: DNS hostnames enabled
- ✅ 1.4: DNS support enabled

### Subnet Requirements (2.x)
- ✅ 2.1-2.3: Public and private subnets across multiple AZs
- ✅ 2.4-2.5: Proper public IP assignment configuration
- ✅ 2.6-2.8: Subnet-specific tagging and CIDR allocation

### Internet Connectivity (3.x)
- ✅ 3.1: Internet Gateway attached to VPC
- ✅ 3.2-3.3: Public and private subnet routing
- ✅ 3.4: NAT Gateway in each AZ (per_az strategy)
- ✅ 3.5-3.7: Route table configuration and associations

### Network ACLs (4.x)
- ✅ 4.1-4.7: Public and private NACL rules implemented

### Security Groups (5.x)
- ✅ 5.1-5.8: Four-tier security group architecture implemented

### Monitoring (6.x)
- ✅ 6.1-6.5: VPC Flow Logs with CloudWatch integration

### High Availability (7.x)
- ✅ 7.1-7.5: Multi-AZ resources with redundant NAT gateways

### Cost Optimization (8.x)
- ✅ 8.1: Configurable NAT strategy
- ✅ 8.3-8.5: Cost-effective options and documentation

### Security (9.x)
- ✅ 9.1-9.7: Security best practices implemented

### Infrastructure as Code (10.x)
- ✅ 10.1-10.8: Comprehensive IaC with outputs and documentation

### Testing (11.x)
- ✅ 11.1-11.8: Property-based and integration tests

---

## License

This module is provided as-is for educational and production use.

## Contributing

Improvements and suggestions welcome! Please ensure all tests pass before submitting changes.

## Maintainers

Maintained by [@rijulsahu](https://github.com/rijulsahu)

## Version History

- **v1.0.0** (2025-12-27): Initial production-ready release
  - Multi-AZ VPC with public/private subnets
  - Configurable NAT Gateway strategy
  - 4-tier security group architecture
  - Comprehensive testing suite
  - Full documentation

---

**Need Help?** Check the [Troubleshooting](#troubleshooting) section or open an issue.
