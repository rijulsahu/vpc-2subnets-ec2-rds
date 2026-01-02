# Simple EC2 Deployment

A straightforward OpenTofu (Terraform-compatible) configuration for deploying a single EC2 instance within AWS free tier limits. This project emphasizes simplicity, cost-effectiveness, and security best practices while maintaining infrastructure as code principles.

## 🎯 Overview

This deployment creates a minimal but functional cloud server suitable for:
- Development and testing environments
- Learning AWS and Infrastructure as Code
- Quick prototype deployments
- Personal projects within free tier limits

**Key Features:**
- ✅ Free tier optimized (t2.micro/t3.micro instances)
- ✅ Secure by default (security group with SSH, HTTP, HTTPS)
- ✅ Flexible key pair management (create new or use existing)
- ✅ Default VPC usage (minimal networking complexity)
- ✅ Comprehensive tagging for cost tracking
- ✅ Property-based testing for validation

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Outputs](#outputs)
- [Testing](#testing)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Security Considerations](#security-considerations)

## 🔧 Prerequisites

Before you begin, ensure you have the following installed:

1. **OpenTofu** (v1.6+) or **Terraform** (v1.6+)
   ```bash
   # Install OpenTofu (recommended)
   # See: https://opentofu.org/docs/intro/install/
   
   # Or install Terraform
   # See: https://developer.hashicorp.com/terraform/install
   ```

2. **AWS CLI** configured with credentials
   ```bash
   aws configure
   ```
   You'll need:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., `ap-south-1`)

3. **SSH Key Pair** (if creating new key pair)
   ```bash
   # Generate SSH key pair if you don't have one
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/ec2-keypair
   ```

## 🚀 Quick Start

### 1. Clone or Navigate to This Directory

```bash
cd simple-ec2-deployment
```

### 2. Create Configuration File

Copy the example configuration:

```bash
cp terraform.tfvars.example terraform.tfvars
```

### 3. Edit Configuration

Edit `terraform.tfvars` with your settings:

```hcl
# AWS Region
aws_region = "ap-south-1"

# Project name (used for resource naming)
project_name = "my-ec2"

# Instance type (must be free tier: t2.micro or t3.micro)
instance_type = "t2.micro"

# Key pair configuration - Option 1: Create new key pair
create_key_pair = true
key_pair_name = "my-ec2-keypair"
public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... your-public-key"

# SSH access CIDR (restrict to your IP for security)
allowed_ssh_cidr = "0.0.0.0/0"  # Change this to your IP/CIDR

# Storage configuration
root_volume_size = 10  # GB (8-30 for free tier)
root_volume_type = "gp3"
```

### 4. Initialize OpenTofu

```bash
tofu init
```

### 5. Review the Plan

```bash
tofu plan
```

### 6. Deploy

```bash
tofu apply
```

Type `yes` when prompted to confirm.

### 7. Connect to Your Instance

After deployment completes, use the SSH connection command from the outputs:

```bash
# Get the connection command
tofu output ssh_connection

# Or manually connect
ssh -i ~/.ssh/ec2-keypair ec2-user@<public-ip>
```

## ⚙️ Configuration

### Required Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `aws_region` | string | `ap-south-1` | AWS region for deployment |
| `project_name` | string | `simple-ec2` | Project name for resource naming |
| `instance_type` | string | `t2.micro` | EC2 instance type (t2.micro or t3.micro) |

### Key Pair Configuration

**Option 1: Create New Key Pair**
```hcl
create_key_pair = true
key_pair_name = "my-keypair"
public_key = "ssh-rsa AAAAB3NzaC1yc2E... your-public-key"
```

**Option 2: Use Existing Key Pair**
```hcl
create_key_pair = false
key_pair_name = "existing-keypair-name"
```

### Security Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `allowed_ssh_cidr` | string | `0.0.0.0/0` | CIDR block for SSH access |

⚠️ **Security Best Practice:** Restrict SSH access to your IP address:
```hcl
allowed_ssh_cidr = "203.0.113.45/32"  # Your IP address
```

### Storage Configuration

| Variable | Type | Default | Constraints | Description |
|----------|------|---------|-------------|-------------|
| `root_volume_size` | number | `10` | 8-30 GB | Root EBS volume size |
| `root_volume_type` | string | `gp3` | gp2, gp3 | EBS volume type |

## 📤 Outputs

After successful deployment, the following outputs are available:

```bash
# View all outputs
tofu output

# View specific output
tofu output public_ip
```

| Output | Description |
|--------|-------------|
| `instance_id` | EC2 instance ID |
| `public_ip` | Public IP address for SSH connection |
| `key_pair_name` | Name of the key pair used |
| `security_group_id` | ID of the security group |
| `ami_id` | ID of the Amazon Linux 2023 AMI used |
| `instance_state` | Current state of the instance |
| `ssh_connection` | Ready-to-use SSH connection command |

## 🧪 Testing

This project includes comprehensive property-based tests to validate the configuration:

### Run All Tests

```bash
# Navigate to the project directory
cd simple-ec2-deployment

# Run individual test suites
uv run test/variable_validation_test.py
uv run test/ami_compliance_test.py
uv run test/security_group_test.py
uv run test/storage_compliance_test.py
uv run test/key_pair_management_test_v2.py
uv run test/tagging_consistency_test.py
uv run test/output_availability_test.py
uv run test/deployment_compliance_test.py
uv run test/minimal_resource_test.py
```

### Test Coverage

- ✅ **Property 1:** Instance Deployment Compliance
- ✅ **Property 2:** Free Tier Instance Type Compliance
- ✅ **Property 3:** Amazon Linux 2023 AMI Usage
- ✅ **Property 4:** Security Group Configuration
- ✅ **Property 5:** Key Pair Management
- ✅ **Property 6:** Storage Configuration
- ✅ **Property 7:** Resource Tagging and Naming
- ✅ **Property 8:** Minimal Resource Creation
- ✅ **Property 9:** Required Output Availability

## 💰 Cost Optimization

This configuration is designed to stay within AWS free tier limits:

### Free Tier Includes:
- **EC2:** 750 hours/month of t2.micro or t3.micro instances
- **EBS:** 30 GB of General Purpose (SSD) storage
- **Data Transfer:** 15 GB of bandwidth out per month

### Cost-Saving Features:
1. ✅ Uses free tier eligible instance types (validated)
2. ✅ Leverages default VPC (no additional networking costs)
3. ✅ No Elastic IP (uses dynamic public IP)
4. ✅ No additional EBS volumes
5. ✅ No load balancers or NAT gateways
6. ✅ Security groups are free

### Estimated Monthly Cost:
**$0.00** within free tier limits (first 12 months)

After free tier expires:
- t2.micro in ap-south-1: ~$8.50/month
- 10 GB gp3 storage: ~$0.80/month
- **Total: ~$9.30/month**

⚠️ **Important:** Always monitor your AWS billing dashboard and set up billing alerts!

## 🔍 Troubleshooting

### Common Issues

#### 1. "No default VPC available"

**Problem:** Your AWS account doesn't have a default VPC in the selected region.

**Solution:**
```bash
# Create a default VPC using AWS CLI
aws ec2 create-default-vpc --region ap-south-1
```

#### 2. "Key pair already exists"

**Problem:** A key pair with the same name already exists.

**Solution:**
```hcl
# Option 1: Use the existing key pair
create_key_pair = false
key_pair_name = "existing-keypair-name"

# Option 2: Choose a different name
key_pair_name = "my-new-keypair-name"
```

#### 3. "AuthFailure: Not authorized"

**Problem:** AWS credentials not configured or insufficient permissions.

**Solution:**
```bash
# Reconfigure AWS CLI
aws configure

# Verify credentials
aws sts get-caller-identity
```

#### 4. "Instance type not available in AZ"

**Problem:** The selected instance type (t2.micro/t3.micro) isn't available in the default availability zone.

**Solution:**
```hcl
# Try a different region or instance type
aws_region = "us-east-1"
instance_type = "t3.micro"  # Try t3 if t2 unavailable
```

#### 5. SSH Connection Refused

**Problem:** Cannot connect via SSH after deployment.

**Solutions:**
1. **Check security group:** Ensure your IP is allowed in `allowed_ssh_cidr`
2. **Wait for initialization:** Instance may still be starting up (wait 2-3 minutes)
3. **Verify key permissions:**
   ```bash
   chmod 400 ~/.ssh/ec2-keypair
   ```
4. **Check correct username:** For Amazon Linux 2023, use `ec2-user`
   ```bash
   ssh -i ~/.ssh/ec2-keypair ec2-user@<public-ip>
   ```

### Validation Commands

```bash
# Validate configuration syntax
tofu validate

# Format configuration files
tofu fmt

# Show current state
tofu show

# Check for configuration drift
tofu plan

# View current outputs
tofu output
```

### Cleanup

To destroy all resources and avoid charges:

```bash
tofu destroy
```

Type `yes` when prompted. This will remove:
- EC2 instance
- Security group
- Key pair (if created by this configuration)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              Internet                       │
└───────────────────┬─────────────────────────┘
                    │
            ┌───────▼────────┐
            │ Security Group │
            │  - SSH (22)    │
            │  - HTTP (80)   │
            │  - HTTPS (443) │
            └───────┬────────┘
                    │
            ┌───────▼────────┐
            │  EC2 Instance  │
            │  - t2.micro    │
            │  - AL2023      │
            │  - Public IP   │
            └───────┬────────┘
                    │
            ┌───────▼────────┐
            │  EBS Volume    │
            │  - 10GB gp3    │
            │  - Encrypted   │
            └────────────────┘
```

### Components

1. **EC2 Instance**
   - Type: t2.micro (default) or t3.micro
   - AMI: Latest Amazon Linux 2023 (auto-resolved)
   - Network: Default VPC and subnet
   - Public IP: Automatically assigned

2. **Security Group**
   - SSH (port 22): Configurable CIDR
   - HTTP (port 80): Open to internet
   - HTTPS (port 443): Open to internet
   - Egress: All traffic allowed

3. **Key Pair**
   - Option to create new or use existing
   - Required for SSH access

4. **EBS Storage**
   - 10GB root volume (configurable 8-30GB)
   - gp3 type (or gp2)
   - Encrypted by default

## 🔒 Security Considerations

### Implemented Security Features

1. ✅ **Encrypted EBS volumes** - Root volume encrypted at rest
2. ✅ **Configurable SSH access** - Restrict by CIDR block
3. ✅ **Minimal ingress rules** - Only SSH, HTTP, HTTPS
4. ✅ **Default deny** - All other inbound traffic blocked
5. ✅ **Resource tagging** - Clear identification and tracking

### Security Best Practices

1. **Restrict SSH Access**
   ```hcl
   allowed_ssh_cidr = "YOUR.IP.ADDRESS/32"
   ```

2. **Use Strong SSH Keys**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/ec2-keypair
   ```

3. **Keep Software Updated**
   ```bash
   sudo dnf update -y  # On Amazon Linux 2023
   ```

4. **Enable AWS CloudTrail** - Monitor API calls and changes

5. **Set up Billing Alerts** - Avoid unexpected charges

6. **Regular Security Audits** - Review security group rules periodically

### Additional Security Recommendations

- Consider using AWS Systems Manager Session Manager instead of SSH
- Implement Multi-Factor Authentication (MFA) on your AWS account
- Use IAM roles with least privilege principle
- Enable AWS GuardDuty for threat detection
- Regularly review AWS Trusted Advisor recommendations

## 📝 File Structure

```
simple-ec2-deployment/
├── main.tf                    # Core resource definitions
├── variables.tf               # Input variables with validation
├── outputs.tf                 # Output definitions
├── versions.tf                # Provider version constraints
├── terraform.tfvars.example   # Example configuration
├── test.tfvars                # Test configuration
├── README.md                  # This file
└── test/                      # Property-based tests
    ├── ami_compliance_test.py
    ├── deployment_compliance_test.py
    ├── key_pair_management_test_v2.py
    ├── minimal_resource_test.py
    ├── output_availability_test.py
    ├── run_all_tests.py
    ├── security_group_test.py
    ├── storage_compliance_test.py
    ├── tagging_consistency_test.py
    └── variable_validation_test.py
```

## 🤝 Contributing

Contributions are welcome! Please ensure:
1. All property tests pass
2. Code follows existing patterns
3. Documentation is updated
4. Configuration stays within free tier limits

## 📄 License

This project is provided as-is for educational and development purposes.

## 🙏 Acknowledgments

- Built with [OpenTofu](https://opentofu.org/) - Open-source Terraform alternative
- Designed for AWS Free Tier eligibility
- Property-based testing approach for infrastructure validation

## 📞 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [AWS Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/)
3. Consult [OpenTofu Documentation](https://opentofu.org/docs/)

---

**⚠️ Disclaimer:** Always monitor your AWS billing dashboard. While this configuration is designed for free tier usage, costs may occur if you exceed free tier limits or deploy in regions with different pricing.

**Happy Deploying! 🚀**
