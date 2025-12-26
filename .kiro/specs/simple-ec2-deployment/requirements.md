# Requirements Document

## Introduction

This feature provides a simple, cost-effective EC2 instance deployment using OpenTofu (Terraform) for basic cloud computing needs within AWS free tier limits.

## Glossary

- **EC2_Instance**: Amazon Elastic Compute Cloud virtual server instance
- **OpenTofu**: Open-source infrastructure as code tool (Terraform fork)
- **Free_Tier**: AWS offering that provides limited free usage of services for eligible accounts
- **Security_Group**: Virtual firewall that controls inbound and outbound traffic for EC2 instances
- **Key_Pair**: Public-private key pair used for secure SSH access to EC2 instances
- **VPC**: Virtual Private Cloud - isolated network environment in AWS
- **Subnet**: Network segment within a VPC where resources are deployed

## Requirements

### Requirement 1: EC2 Instance Provisioning

**User Story:** As a developer, I want to deploy a simple EC2 instance using OpenTofu, so that I can have a basic cloud server for development and testing.

#### Acceptance Criteria

1. WHEN OpenTofu configuration is applied, THE EC2_Instance SHALL be created in the specified AWS region
2. WHEN selecting instance type, THE EC2_Instance SHALL use t2.micro or t3.micro to stay within free tier limits
3. WHEN the instance is created, THE EC2_Instance SHALL use the latest Amazon Linux 2023 AMI
4. WHEN the deployment completes, THE EC2_Instance SHALL be in a running state
5. WHEN the instance is deployed, THE EC2_Instance SHALL be assigned a public IP address for external access

### Requirement 2: Network Security Configuration

**User Story:** As a system administrator, I want proper network security controls, so that the EC2 instance is accessible but secure.

#### Acceptance Criteria

1. WHEN creating network resources, THE Security_Group SHALL allow SSH access on port 22 from any IP address
2. WHEN creating network resources, THE Security_Group SHALL allow HTTP access on port 80 from any IP address
3. WHEN creating network resources, THE Security_Group SHALL allow HTTPS access on port 443 from any IP address
4. WHEN the instance is deployed, THE EC2_Instance SHALL be placed in the default VPC and subnet
5. WHEN security rules are applied, THE Security_Group SHALL deny all other inbound traffic by default

### Requirement 3: SSH Access Management

**User Story:** As a developer, I want secure SSH access to the EC2 instance, so that I can manage and configure the server remotely.

#### Acceptance Criteria

1. WHEN deploying the instance, THE Key_Pair SHALL be created or referenced for SSH authentication
2. WHEN the key pair is created, THE OpenTofu SHALL output the key pair name for reference
3. WHEN SSH access is configured, THE EC2_Instance SHALL accept connections using the specified key pair
4. IF a key pair already exists with the same name, THEN THE OpenTofu SHALL use the existing key pair
5. WHEN the deployment completes, THE OpenTofu SHALL output the public IP address for SSH connection

### Requirement 4: Cost Optimization

**User Story:** As a cost-conscious user, I want the deployment to stay within AWS free tier limits, so that I don't incur unexpected charges.

#### Acceptance Criteria

1. THE EC2_Instance SHALL use only free tier eligible instance types (t2.micro or t3.micro)
2. THE EC2_Instance SHALL use free tier eligible AMI (Amazon Linux 2023)
3. WHEN storage is configured, THE EC2_Instance SHALL use general purpose SSD (gp3) with maximum 30GB to stay within free tier
4. THE OpenTofu SHALL include tags to identify resources for cost tracking
5. THE OpenTofu SHALL not create additional chargeable resources beyond basic EC2 requirements

### Requirement 5: Infrastructure as Code Best Practices

**User Story:** As a DevOps engineer, I want well-structured OpenTofu configuration, so that the infrastructure is maintainable and reusable.

#### Acceptance Criteria

1. WHEN organizing the code, THE OpenTofu SHALL separate resources into logical files (main.tf, variables.tf, outputs.tf)
2. WHEN defining resources, THE OpenTofu SHALL use variables for configurable values like region and instance type
3. WHEN the deployment completes, THE OpenTofu SHALL output essential information like instance ID and public IP
4. WHEN resources are created, THE OpenTofu SHALL apply consistent naming conventions and tags
5. WHEN configuration is written, THE OpenTofu SHALL include provider version constraints for reproducibility