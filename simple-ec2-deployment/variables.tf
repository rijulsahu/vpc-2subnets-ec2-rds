# AWS Region
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-south-1"
}

# Project name for resource naming
variable "project_name" {
  description = "Name of the project for resource naming and tagging"
  type        = string
  default     = "simple-ec2"
}

# EC2 Instance Type - restricted to free tier eligible types
variable "instance_type" {
  description = "EC2 instance type (must be free tier eligible)"
  type        = string
  default     = "t1.micro"

  validation {
    condition     = contains(["t1.micro", "t2.micro"], var.instance_type)
    error_message = "Instance type must be either t1.micro or t2.micro to stay within AWS free tier limits."
  }
}

# Key Pair Name
variable "key_pair_name" {
  description = "Name of the AWS key pair for SSH access"
  type        = string
  default     = null
}

# Create Key Pair Flag
variable "create_key_pair" {
  description = "Whether to create a new key pair or use an existing one"
  type        = bool
  default     = false
}

# Public Key for Key Pair Creation
variable "public_key" {
  description = "Public key content for creating new key pair (required if create_key_pair is true)"
  type        = string
  default     = null

  validation {
    condition     = var.create_key_pair == false || (var.create_key_pair == true && var.public_key != null)
    error_message = "public_key must be provided when create_key_pair is true."
  }
}

# SSH Access CIDR
variable "allowed_ssh_cidr" {
  description = "CIDR block allowed for SSH access"
  type        = string
  default     = "0.0.0.0/0"

  validation {
    condition     = can(cidrhost(var.allowed_ssh_cidr, 0))
    error_message = "The allowed_ssh_cidr must be a valid CIDR block."
  }
}

# Environment
variable "environment" {
  description = "Environment name for resource tagging"
  type        = string
  default     = "development"
}

# Root Volume Size
variable "root_volume_size" {
  description = "Size of the root EBS volume in GB (max 30GB for free tier)"
  type        = number
  default     = 30

  validation {
    condition     = var.root_volume_size >= 8 && var.root_volume_size <= 30
    error_message = "Root volume size must be between 8GB and 30GB to stay within free tier limits."
  }
}

# Root Volume Type
variable "root_volume_type" {
  description = "Type of the root EBS volume"
  type        = string
  default     = "gp3"

  validation {
    condition     = contains(["gp2", "gp3"], var.root_volume_type)
    error_message = "Root volume type must be either gp2 or gp3 for free tier eligibility."
  }
}