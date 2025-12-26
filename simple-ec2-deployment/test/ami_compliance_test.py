#!/usr/bin/env python3
"""
Property-based test for AMI compliance
Feature: simple-ec2-deployment, Property 3: Amazon Linux 2023 AMI Usage
Validates: Requirements 1.3, 4.2
"""

import os
import sys

def test_ami_data_source_exists():
    """Test that AMI data source is defined in main.tf"""
    print("Testing AMI data source configuration...")
    
    main_tf_path = "main.tf"  # Current directory
    if not os.path.exists(main_tf_path):
        print("  FAIL: main.tf file not found")
        return False
    
    with open(main_tf_path, 'r') as f:
        content = f.read()
    
    # Check for AMI data source
    if 'data "aws_ami" "amazon_linux"' in content:
        print("  PASS: AMI data source 'amazon_linux' found")
    else:
        print("  FAIL: AMI data source 'amazon_linux' not found")
        return False
    
    # Check for Amazon Linux 2023 filter
    if 'al2023-ami-*-x86_64' in content:
        print("  PASS: Amazon Linux 2023 AMI filter found")
    else:
        print("  FAIL: Amazon Linux 2023 AMI filter not found")
        return False
    
    # Check for most_recent = true
    if 'most_recent = true' in content:
        print("  PASS: most_recent = true configuration found")
    else:
        print("  FAIL: most_recent = true configuration not found")
        return False
    
    # Check for owners = ["amazon"]
    if 'owners      = ["amazon"]' in content:
        print("  PASS: Amazon owners configuration found")
    else:
        print("  FAIL: Amazon owners configuration not found")
        return False
    
    return True

def test_ec2_instance_uses_ami():
    """Test that EC2 instance uses the AMI data source"""
    print("\nTesting EC2 instance AMI configuration...")
    
    main_tf_path = "main.tf"  # Current directory
    if not os.path.exists(main_tf_path):
        print("  FAIL: main.tf file not found")
        return False
    
    with open(main_tf_path, 'r') as f:
        content = f.read()
    
    # Check for EC2 instance resource
    if 'resource "aws_instance" "main"' in content:
        print("  PASS: EC2 instance resource 'main' found")
    else:
        print("  FAIL: EC2 instance resource 'main' not found")
        return False
    
    # Check that instance uses AMI data source
    if 'ami                    = data.aws_ami.amazon_linux.id' in content:
        print("  PASS: EC2 instance uses AMI data source")
    else:
        print("  FAIL: EC2 instance does not use AMI data source")
        return False
    
    return True

def test_storage_configuration():
    """Test that storage is configured correctly for free tier"""
    print("\nTesting storage configuration...")
    
    main_tf_path = "main.tf"  # Current directory
    if not os.path.exists(main_tf_path):
        print("  FAIL: main.tf file not found")
        return False
    
    with open(main_tf_path, 'r') as f:
        content = f.read()
    
    # Check for root_block_device configuration
    if 'root_block_device {' in content:
        print("  PASS: root_block_device configuration found")
    else:
        print("  FAIL: root_block_device configuration not found")
        return False
    
    # Check for volume type variable usage
    if 'volume_type = var.root_volume_type' in content:
        print("  PASS: Volume type uses variable")
    else:
        print("  FAIL: Volume type does not use variable")
        return False
    
    # Check for volume size variable usage
    if 'volume_size = var.root_volume_size' in content:
        print("  PASS: Volume size uses variable")
    else:
        print("  FAIL: Volume size does not use variable")
        return False
    
    return True

if __name__ == "__main__":
    print("AMI Compliance Property Tests")
    print("=" * 50)
    
    # Run the property tests
    test1_passed = test_ami_data_source_exists()
    test2_passed = test_ec2_instance_uses_ami()
    test3_passed = test_storage_configuration()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"AMI Data Source Configuration: {'PASS' if test1_passed else 'FAIL'}")
    print(f"EC2 Instance AMI Usage: {'PASS' if test2_passed else 'FAIL'}")
    print(f"Storage Configuration: {'PASS' if test3_passed else 'FAIL'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\nAll AMI compliance tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome AMI compliance tests FAILED!")
        sys.exit(1)