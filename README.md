# AWS Infrastructure as Code - VPC & EC2 Deployments

A collection of Terraform/OpenTofu configurations for deploying secure and scalable AWS infrastructure. This repository demonstrates best practices in Infrastructure as Code, including proper VPC design, security hardening, and automated testing.

## 📁 Projects

### 1. Simple EC2 Deployment
Located in [`simple-ec2-deployment/`](simple-ec2-deployment/)

A straightforward, free-tier optimized EC2 deployment for learning and development purposes.

**Features:**
- ✅ AWS Free Tier compatible (t2.micro/t3.micro)
- ✅ Secure SSH, HTTP, and HTTPS access
- ✅ Flexible key pair management
- ✅ Uses default VPC for simplicity
- ✅ Comprehensive testing suite

**Use Cases:**
- Development and testing environments
- Learning AWS and IaC
- Quick prototype deployments
- Personal projects

[Read more →](simple-ec2-deployment/README.md)

### 2. VPC Best Practices
Located in [`vpc-best-practices/`](vpc-best-practices/)

A production-ready VPC configuration following AWS best practices with proper network segmentation.

**Features:**
- ✅ Custom VPC with public and private subnets
- ✅ NAT Gateway for private subnet internet access
- ✅ Internet Gateway for public subnet
- ✅ Proper routing and security groups
- ✅ Multi-AZ support for high availability

**Use Cases:**
- Production workloads
- Multi-tier applications
- Secure network architectures
- Learning VPC fundamentals

[Read more →](vpc-best-practices/README.md)

## 🚀 Quick Start

### Prerequisites

1. **Terraform/OpenTofu** (v1.6+)
   ```bash
   # Install OpenTofu (recommended)
   brew install opentofu  # macOS
   # Or see: https://opentofu.org/docs/intro/install/
   ```

2. **AWS CLI** configured with credentials
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and default region
   ```

3. **Python 3.x** (for running tests)
   ```bash
   python --version  # Should be 3.7+
   ```

### Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vpc-2subnets-ec2-rds
   ```

2. **Choose a project**
   ```bash
   cd simple-ec2-deployment  # or vpc-best-practices
   ```

3. **Copy and configure variables**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

4. **Initialize Terraform**
   ```bash
   terraform init
   ```

5. **Plan and deploy**
   ```bash
   terraform plan
   terraform apply
   ```

## 🧪 Testing

Each project includes comprehensive tests written in Python. To run tests:

```bash
cd simple-ec2-deployment/test  # or vpc-best-practices/test
python run_all_tests.py
```

**Test Coverage Includes:**
- ✅ AMI compliance verification
- ✅ Security group configuration validation
- ✅ Storage compliance checks
- ✅ Output availability testing
- ✅ Key pair management validation
- ✅ Resource deployment compliance

## 📊 Architecture

### Simple EC2 Deployment
```
┌─────────────────────────────────────┐
│         Default VPC                 │
│  ┌───────────────────────────────┐  │
│  │    Public Subnet              │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  EC2 Instance           │  │  │
│  │  │  - t2.micro/t3.micro    │  │  │
│  │  │  - Security Group       │  │  │
│  │  │    - SSH (22)           │  │  │
│  │  │    - HTTP (80)          │  │  │
│  │  │    - HTTPS (443)        │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### VPC Best Practices
```
┌────────────────────────────────────────────────────────┐
│                     Custom VPC                         │
│  ┌──────────────────────┐  ┌──────────────────────┐    │
│  │  Public Subnet       │  │  Private Subnet      │    │
│  │  - NAT Gateway       │  │  - EC2 Instances     │    │
│  │  - Bastion Host      │  │  - RDS Database      │    │
│  │  - Internet Gateway  │  │  - App Servers       │    │
│  └──────────────────────┘  └──────────────────────┘    │
└────────────────────────────────────────────────────────┘
```

## 🔒 Security Best Practices

- ✅ **No hardcoded credentials** - Use AWS credentials or IAM roles
- ✅ **Sensitive data excluded** - `.gitignore` prevents committing `.tfvars` and state files
- ✅ **Security groups** - Least privilege access rules
- ✅ **SSH key management** - Use existing or create new key pairs
- ✅ **State file security** - Store remotely with encryption (recommended for production)

## 💰 Cost Optimization

- **Simple EC2 Deployment**: ~$0 (within free tier with t2.micro/t3.micro)
- **VPC Best Practices**: Minimal costs
  - VPC, Subnets, Route Tables: Free
  - NAT Gateway: ~$0.045/hour (~$32/month)
  - EC2 instances: Varies by type
  - RDS: Varies by configuration

**Cost Reduction Tips:**
1. Use free tier eligible resources (t2.micro, t3.micro)
2. Stop instances when not in use
3. Consider VPC endpoints instead of NAT Gateway for AWS services
4. Set up AWS Budgets for alerts

## 📝 Project Structure

```
vpc-2subnets-ec2-rds/
├── .gitignore                      # Excludes sensitive files
├── README.md                       # This file
├── simple-ec2-deployment/          # Free tier EC2 deployment
│   ├── main.tf                    # Main infrastructure code
│   ├── variables.tf               # Input variables
│   ├── outputs.tf                 # Output values
│   ├── versions.tf                # Provider versions
│   ├── terraform.tfvars.example   # Example configuration
│   ├── README.md                  # Detailed documentation
│   └── test/                      # Python test suite
└── vpc-best-practices/            # Production VPC setup
    ├── main.tf
    ├── data.tf
    ├── locals.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    ├── dev.tfvars.example
    ├── README.md
    └── test/
```

## 🛠️ Common Commands

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Plan changes
terraform plan

# Apply changes
terraform apply

# Destroy infrastructure
terraform destroy

# Show current state
terraform show

# List resources
terraform state list
```

## 🐛 Troubleshooting

### Common Issues

1. **AWS Authentication Failed**
   ```bash
   aws configure list
   aws sts get-caller-identity
   ```

2. **Terraform State Locked**
   ```bash
   terraform force-unlock <lock-id>
   ```

3. **Resource Already Exists**
   - Import existing resource: `terraform import <resource> <id>`
   - Or rename in AWS and retry

4. **Permission Denied**
   - Verify IAM permissions for EC2, VPC, and related services

## 📚 Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [OpenTofu Documentation](https://opentofu.org/docs/)
- [AWS VPC Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html)
- [AWS Free Tier](https://aws.amazon.com/free/)

## 👤 Author

**Rijul Sahu**  
Lead Data Engineer & Cloud Solutions Architect

- Portfolio: [rijul.cloud](https://rijul.cloud)
- LinkedIn: [linkedin.com/in/rijulsahu](https://www.linkedin.com/in/rijul-sahu-242b59129)
- Certifications: AWS Solutions Architect, Databricks Data Engineer Associate

## 📄 License

This project is provided as-is for educational and demonstration purposes.

## 🤝 Contributing

Feel free to fork, modify, and use these configurations for your own projects. If you find issues or have improvements, please open an issue or submit a pull request.

## ⚠️ Disclaimer

These configurations are for demonstration and learning purposes. Always review and customize them for your specific use case, especially for production environments. Ensure you understand the costs associated with AWS resources before deployment.
