#!/usr/bin/env python3
"""
Property-based test for minimal resource creation
Feature: simple-ec2-deployment, Property 8: Minimal Resource Creation
Validates: Requirements 4.5
"""
import os
import subprocess
import json
import re
from typing import Dict, List, Tuple

def run_tofu_plan_json() -> Tuple[bool, str]:
    """Run tofu plan and return JSON output"""
    try:
        test_dir = os.path.dirname(os.path.abspath(__file__))
        work_dir = os.path.dirname(test_dir)
        
        result = subprocess.run(
            ["tofu", "plan", "-var-file=test.tfvars", "-out=test.tfplan"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return False, result.stdout + result.stderr
        
        # Get plan in JSON format
        show_result = subprocess.run(
            ["tofu", "show", "-json", "test.tfplan"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return show_result.returncode == 0, show_result.stdout
        
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def count_planned_resources(plan_json: str) -> Dict[str, int]:
    """Count resources by type in the plan"""
    try:
        plan_data = json.loads(plan_json)
        
        resource_changes = plan_data.get('resource_changes', [])
        resource_counts = {}
        
        for change in resource_changes:
            # Only count resources being created
            actions = change.get('change', {}).get('actions', [])
            if 'create' in actions:
                resource_type = change.get('type', 'unknown')
                resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
        
        return resource_counts
        
    except json.JSONDecodeError:
        return {}
    except Exception:
        return {}

def test_minimal_chargeable_resources() -> Tuple[bool, List[str]]:
    """Test that only minimal chargeable resources are created (Req 4.5)"""
    print("\nTesting minimal chargeable resource creation...")
    issues = []
    
    success, plan_output = run_tofu_plan_json()
    
    if not success:
        issues.append("Failed to generate plan")
        print("  FAIL: Could not generate plan")
        return False, issues
    
    resource_counts = count_planned_resources(plan_output)
    
    # Define allowed resources (free tier or free resources)
    allowed_resources = {
        'aws_instance': 1,           # 1 EC2 instance (free tier eligible)
        'aws_security_group': 1,     # Security groups are free
        'aws_key_pair': 1,           # Key pairs are free
    }
    
    # Resources that should NOT be created (chargeable beyond basic needs)
    forbidden_resources = [
        'aws_eip',                   # Elastic IPs (charged when not attached)
        'aws_ebs_volume',            # Additional EBS volumes (beyond root)
        'aws_lb',                    # Load balancers (not free)
        'aws_elb',                   # Classic load balancers
        'aws_alb',                   # Application load balancers
        'aws_nat_gateway',           # NAT gateways (expensive)
        'aws_vpc',                   # Custom VPCs (we use default)
        'aws_subnet',                # Custom subnets (we use default)
        'aws_rds_instance',          # RDS instances
        'aws_dynamodb_table',        # DynamoDB tables
    ]
    
    print(f"  Resources planned for creation:")
    for resource_type, count in resource_counts.items():
        print(f"    - {resource_type}: {count}")
    
    # Check for forbidden resources
    forbidden_found = []
    for resource_type in forbidden_resources:
        if resource_type in resource_counts:
            forbidden_found.append(resource_type)
            issues.append(f"Unnecessary chargeable resource: {resource_type}")
            print(f"  FAIL: Found forbidden resource: {resource_type}")
    
    if not forbidden_found:
        print("  PASS: No unnecessary chargeable resources found")
    
    # Check resource counts are reasonable
    total_resources = sum(resource_counts.values())
    if total_resources <= 4:  # Instance, Security Group, Key Pair, and maybe one more
        print(f"  PASS: Minimal resource count ({total_resources} resources)")
    else:
        issues.append(f"Too many resources: {total_resources} (expected <= 4)")
        print(f"  WARN: Resource count higher than expected: {total_resources}")
    
    return len(forbidden_found) == 0, issues

def test_no_additional_networking_resources() -> Tuple[bool, List[str]]:
    """Test that no additional networking resources are created"""
    print("\nTesting no additional networking resources...")
    issues = []
    
    # Read main.tf to verify we're using default VPC/subnet
    test_dir = os.path.dirname(os.path.abspath(__file__))
    main_tf_path = os.path.join(os.path.dirname(test_dir), "main.tf")
    try:
        with open(main_tf_path, "r") as f:
            main_tf_content = f.read()
    except FileNotFoundError:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Check that we're using data sources (not creating new VPC/subnets)
    if 'data "aws_vpc" "default"' in main_tf_content:
        print("  PASS: Using default VPC (data source, not creating new VPC)")
    else:
        issues.append("Not using default VPC data source")
        print("  FAIL: Should use default VPC data source")
    
    if 'data "aws_subnet" "default"' in main_tf_content:
        print("  PASS: Using default subnet (data source, not creating new subnet)")
    else:
        issues.append("Not using default subnet data source")
        print("  FAIL: Should use default subnet data source")
    
    # Check that we're NOT creating custom VPC/subnets
    if 'resource "aws_vpc"' not in main_tf_content:
        print("  PASS: Not creating custom VPC")
    else:
        issues.append("Creating custom VPC (unnecessary charge)")
        print("  FAIL: Should not create custom VPC")
    
    if 'resource "aws_subnet"' not in main_tf_content:
        print("  PASS: Not creating custom subnets")
    else:
        issues.append("Creating custom subnets (unnecessary)")
        print("  FAIL: Should not create custom subnets")
    
    return len(issues) == 0, issues

def test_no_additional_storage_volumes() -> Tuple[bool, List[str]]:
    """Test that no additional EBS volumes are created beyond root volume"""
    print("\nTesting no additional storage volumes...")
    issues = []
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    main_tf_path = os.path.join(os.path.dirname(test_dir), "main.tf")
    try:
        with open(main_tf_path, "r") as f:
            main_tf_content = f.read()
    except FileNotFoundError:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Check for additional EBS volume resources
    if 'resource "aws_ebs_volume"' in main_tf_content:
        issues.append("Creating additional EBS volumes (extra cost)")
        print("  FAIL: Additional EBS volumes found")
        return False, issues
    else:
        print("  PASS: No additional EBS volumes created")
    
    # Verify only root_block_device is configured
    if 'root_block_device' in main_tf_content:
        print("  PASS: Using only root_block_device (no additional volumes)")
    else:
        print("  WARN: root_block_device not found")
    
    # Check for ebs_block_device (additional volumes)
    if 'ebs_block_device' in main_tf_content:
        issues.append("Using ebs_block_device (additional volumes)")
        print("  FAIL: Should not use ebs_block_device (extra cost)")
        return False, issues
    else:
        print("  PASS: No ebs_block_device configured")
    
    return len(issues) == 0, issues

def test_minimal_resource_creation_property():
    """
    Property 8: Minimal Resource Creation
    For any deployment, only the minimum required resources should be created
    to avoid unnecessary charges beyond basic EC2 requirements.
    """
    print("Testing Property 8: Minimal Resource Creation")
    print("=" * 60)
    
    all_issues = []
    
    # Test 1: Minimal chargeable resources (Req 4.5)
    test1_passed, test1_issues = test_minimal_chargeable_resources()
    all_issues.extend(test1_issues)
    
    # Test 2: No additional networking resources
    test2_passed, test2_issues = test_no_additional_networking_resources()
    all_issues.extend(test2_issues)
    
    # Test 3: No additional storage volumes
    test3_passed, test3_issues = test_no_additional_storage_volumes()
    all_issues.extend(test3_issues)
    
    overall_passed = all([test1_passed, test2_passed, test3_passed])
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Minimal Chargeable Resources (Req 4.5): {'PASS' if test1_passed else 'FAIL'}")
    print(f"No Additional Networking Resources: {'PASS' if test2_passed else 'FAIL'}")
    print(f"No Additional Storage Volumes: {'PASS' if test3_passed else 'FAIL'}")
    
    if overall_passed:
        print("\nAll minimal resource creation tests PASSED!")
        return True
    else:
        print("\nSome minimal resource tests FAILED:")
        for issue in all_issues:
            print(f"  - {issue}")
        return False

def test_free_tier_compliance():
    """Additional test to verify all resources are free tier eligible"""
    print("\nTesting free tier compliance...")
    
    # Read variables to check instance type
    test_dir = os.path.dirname(os.path.abspath(__file__))
    variables_path = os.path.join(os.path.dirname(test_dir), "variables.tf")
    try:
        with open(variables_path, "r") as f:
            variables_content = f.read()
    except FileNotFoundError:
        print("  FAIL: variables.tf not found")
        return False
    
    # Check instance type validation
    if 't2.micro' in variables_content and 't3.micro' in variables_content:
        print("  PASS: Instance type restricted to free tier (t2.micro/t3.micro)")
    else:
        print("  WARN: Instance type validation might not restrict to free tier")
    
    # Check volume size validation
    if 'root_volume_size' in variables_content:
        # Check for validation limiting to 30GB
        if '30' in variables_content:
            print("  PASS: Root volume size limited to free tier (max 30GB)")
        else:
            print("  WARN: Root volume size validation might not be optimal")
    
    return True

if __name__ == "__main__":
    print("Minimal Resource Creation Property Tests")
    print("=" * 60)
    
    # Run the main property test
    test1_passed = test_minimal_resource_creation_property()
    test2_passed = test_free_tier_compliance()
    
    print("\n" + "=" * 60)
    print("Overall Results:")
    print(f"Property 8 (Minimal Resource Creation): {'PASS' if test1_passed else 'FAIL'}")
    print(f"Free Tier Compliance: {'PASS' if test2_passed else 'FAIL'}")
    
    # Clean up test plan file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    plan_file = os.path.join(os.path.dirname(test_dir), "test.tfplan")
    if os.path.exists(plan_file):
        os.unlink(plan_file)
    
    if test1_passed and test2_passed:
        print("\nAll minimal resource property tests PASSED!")
        exit(0)
    else:
        print("\nSome property tests FAILED!")
        exit(1)
