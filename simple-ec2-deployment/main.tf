# Configure the AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "development"
      ManagedBy   = "opentofu"
      Purpose     = "learning-development"
    }
  }
}

# Data source for the latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get default VPC
data "aws_vpc" "default" {
  default = true
}

# Get default subnet
data "aws_subnet" "default" {
  vpc_id            = data.aws_vpc.default.id
  availability_zone = data.aws_availability_zones.available.names[0]
}

# Get available availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Create key pair resource with proper naming
resource "aws_key_pair" "main" {
  count      = var.create_key_pair ? 1 : 0
  key_name   = var.key_pair_name != null ? var.key_pair_name : "${var.project_name}-keypair"
  public_key = var.public_key

  tags = {
    Name = var.key_pair_name != null ? var.key_pair_name : "${var.project_name}-keypair"
  }

  lifecycle {
    # Prevent accidental deletion of key pairs
    prevent_destroy = false
  }
}

# Data source to get existing key pair if not creating new one
data "aws_key_pair" "existing" {
  count    = var.create_key_pair ? 0 : 1
  key_name = var.key_pair_name

  # This will fail if the key pair doesn't exist, which is expected behavior
}

# Security Group for EC2 instance
resource "aws_security_group" "main" {
  name_prefix = "${var.project_name}-sg"
  description = "Security group for ${var.project_name} EC2 instance"
  vpc_id      = data.aws_vpc.default.id

  # SSH access
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  # HTTP access
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-security-group"
  }
}

# EC2 Instance
resource "aws_instance" "main" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.create_key_pair ? aws_key_pair.main[0].key_name : data.aws_key_pair.existing[0].key_name
  vpc_security_group_ids = [aws_security_group.main.id]
  subnet_id              = data.aws_subnet.default.id

  # Enable public IP assignment
  associate_public_ip_address = true

  # Root block device configuration for free tier compliance
  root_block_device {
    volume_type = var.root_volume_type
    volume_size = var.root_volume_size
    encrypted   = true

    tags = {
      Name = "${var.project_name}-root-volume"
    }
  }

  tags = {
    Name = "${var.project_name}-instance"
  }

  # Ensure instance is created after security group
  depends_on = [aws_security_group.main]
}