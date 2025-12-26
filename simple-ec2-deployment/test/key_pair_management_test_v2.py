#!/usr/bin/env python3
"""
Property-based test for OpenTofu key pair management
Feature: simple-ec2-deployment, Property 5: Key Pair Management
Validates: Requirements 3.1, 3.4
"""
import os
import re
import sys
from typing import Tuple, List

def read_main_tf() -> str:
    """Read the main.tf file"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    main_tf_path = os.path.join(os.path.dirname(test_dir), "main.tf")
    
    try:
        with open(main_tf_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

def read_variables_tf() -> str:
    """Read the variables.tf file"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    variables_path = os.path.join(os.path.dirname(test_dir), "variables.tf")
    
    try:
        with open(variables_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

def read_outputs_tf() -> str:
    """Read the outputs.tf file"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    outputs_path = os.path.join(os.path.dirname(test_dir), "outputs.tf")
    
    try:
        with open(outputs_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

def test_key_pair_resource_exists() -> Tuple[bool, List[str]]:
    """Test that key pair resource is properly defined"""
    print("\nTesting key pair resource configuration...")
    issues = []
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Check for key pair resource
    if 'resource "aws_key_pair" "main"' in main_tf_content:
        print("  PASS: aws_key_pair resource defined")
    else:
        issues.append("aws_key_pair resource not found")
        print("  FAIL: aws_key_pair resource not found")
        return False, issues
    
    # Extract key pair resource block
    key_pair_match = re.search(
        r'resource "aws_key_pair" "main".*?\{(.*?)\n\}',
        main_tf_content,
        re.DOTALL
    )
    
    if not key_pair_match:
        issues.append("Could not parse key pair resource")
        print("  FAIL: Could not parse key pair resource")
        return False, issues
    
    key_pair_block = key_pair_match.group(1)
    
    # Check for conditional creation with count
    if 'count' in key_pair_block and 'var.create_key_pair' in key_pair_block:
        print("  PASS: Key pair has conditional creation (count based on var.create_key_pair)")
    else:
        issues.append("Key pair missing conditional creation logic")
        print("  FAIL: Key pair should use count with var.create_key_pair")
        return False, issues
    
    # Check for key_name
    if 'key_name' in key_pair_block:
        print("  PASS: key_name attribute configured")
    else:
        issues.append("key_name attribute missing")
        print("  FAIL: key_name attribute missing")
    
    # Check for public_key
    if 'public_key' in key_pair_block and 'var.public_key' in key_pair_block:
        print("  PASS: public_key references var.public_key")
    else:
        issues.append("public_key not properly configured")
        print("  FAIL: public_key should reference var.public_key")
    
    # Check for naming logic (either custom or generated)
    if 'var.key_pair_name' in key_pair_block or 'var.project_name' in key_pair_block:
        print("  PASS: Key pair naming logic includes variables")
    else:
        print("  WARN: Key pair naming should use variables")
    
    return len(issues) == 0, issues

def test_existing_key_pair_data_source() -> Tuple[bool, List[str]]:
    """Test that data source for existing key pair is configured"""
    print("\nTesting existing key pair data source...")
    issues = []
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Check for key pair data source
    if 'data "aws_key_pair" "existing"' in main_tf_content:
        print("  PASS: aws_key_pair data source defined for existing key pairs")
    else:
        issues.append("aws_key_pair data source not found")
        print("  FAIL: aws_key_pair data source for existing keys not found")
        return False, issues
    
    # Extract data source block
    data_source_match = re.search(
        r'data "aws_key_pair" "existing".*?\{(.*?)\n\}',
        main_tf_content,
        re.DOTALL
    )
    
    if not data_source_match:
        issues.append("Could not parse key pair data source")
        print("  FAIL: Could not parse key pair data source")
        return False, issues
    
    data_source_block = data_source_match.group(1)
    
    # Check for conditional with count
    if 'count' in data_source_block:
        print("  PASS: Data source has conditional logic (count)")
    else:
        issues.append("Data source missing conditional logic")
        print("  FAIL: Data source should use count for conditional")
    
    # Check for key_name reference
    if 'key_name' in data_source_block and 'var.key_pair_name' in data_source_block:
        print("  PASS: Data source references var.key_pair_name")
    else:
        issues.append("Data source doesn't reference var.key_pair_name")
        print("  FAIL: Data source should reference var.key_pair_name")
    
    return len(issues) == 0, issues

def test_ec2_key_pair_association() -> Tuple[bool, List[str]]:
    """Test that EC2 instance is associated with key pair"""
    print("\nTesting EC2 instance key pair association...")
    issues = []
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Check for EC2 instance resource
    if 'resource "aws_instance" "main"' not in main_tf_content:
        issues.append("EC2 instance resource not found")
        print("  FAIL: EC2 instance resource not found")
        return False, issues
    
    # Extract EC2 instance block
    instance_match = re.search(
        r'resource "aws_instance" "main".*?\{(.*?)\n\}',
        main_tf_content,
        re.DOTALL
    )
    
    if not instance_match:
        issues.append("Could not parse EC2 instance")
        print("  FAIL: Could not parse EC2 instance")
        return False, issues
    
    instance_block = instance_match.group(1)
    
    # Check for key_name attribute
    if 'key_name' not in instance_block:
        issues.append("EC2 instance missing key_name attribute")
        print("  FAIL: EC2 instance missing key_name attribute")
        return False, issues
    
    print("  PASS: EC2 instance has key_name attribute")
    
    # Check for conditional logic (references both resource and data source)
    if 'aws_key_pair.main' in instance_block and 'data.aws_key_pair.existing' in instance_block:
        print("  PASS: EC2 key_name uses conditional logic (resource or data source)")
    else:
        issues.append("EC2 key_name missing conditional logic")
        print("  FAIL: EC2 should conditionally use aws_key_pair.main or data.aws_key_pair.existing")
        return False, issues
    
    # Check for ternary operator or similar
    if '?' in instance_block or 'var.create_key_pair' in instance_block:
        print("  PASS: Conditional logic includes var.create_key_pair")
    else:
        print("  WARN: Should use var.create_key_pair in conditional")
    
    return len(issues) == 0, issues

def test_key_pair_variables() -> Tuple[bool, List[str]]:
    """Test that required variables for key pair management are defined"""
    print("\nTesting key pair variables configuration...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for create_key_pair variable
    if 'variable "create_key_pair"' in variables_content:
        print("  PASS: create_key_pair variable defined")
    else:
        issues.append("create_key_pair variable not found")
        print("  FAIL: create_key_pair variable not found")
    
    # Check for key_pair_name variable
    if 'variable "key_pair_name"' in variables_content:
        print("  PASS: key_pair_name variable defined")
    else:
        issues.append("key_pair_name variable not found")
        print("  FAIL: key_pair_name variable not found")
    
    # Check for public_key variable
    if 'variable "public_key"' in variables_content:
        print("  PASS: public_key variable defined")
    else:
        issues.append("public_key variable not found")
        print("  FAIL: public_key variable not found")
    
    # Check for public_key validation
    public_key_match = re.search(
        r'variable "public_key".*?\{(.*?)\n\}',
        variables_content,
        re.DOTALL
    )
    
    if public_key_match:
        public_key_block = public_key_match.group(1)
        if 'validation {' in public_key_block:
            print("  PASS: public_key has validation block")
            if 'var.create_key_pair' in public_key_block:
                print("  PASS: Validation checks create_key_pair dependency")
        else:
            print("  WARN: public_key should have validation")
    
    return len(issues) == 0, issues

def test_key_pair_output() -> Tuple[bool, List[str]]:
    """Test that key pair name is available as output"""
    print("\nTesting key pair output configuration...")
    issues = []
    
    outputs_content = read_outputs_tf()
    if not outputs_content:
        issues.append("outputs.tf not found")
        print("  FAIL: outputs.tf not found")
        return False, issues
    
    # Check for key_pair_name output
    if 'output "key_pair_name"' in outputs_content:
        print("  PASS: key_pair_name output defined")
    else:
        issues.append("key_pair_name output not found")
        print("  FAIL: key_pair_name output not found")
        return False, issues
    
    # Extract output block
    output_match = re.search(
        r'output "key_pair_name".*?\{(.*?)\}',
        outputs_content,
        re.DOTALL
    )
    
    if output_match:
        output_block = output_match.group(1)
        
        # Check for conditional logic in output
        if '?' in output_block or 'var.create_key_pair' in output_block:
            print("  PASS: Output uses conditional logic")
        else:
            print("  WARN: Output should handle both create and existing scenarios")
        
        # Check references to both resource and data source
        if 'aws_key_pair.main' in output_block or 'data.aws_key_pair.existing' in output_block:
            print("  PASS: Output references key pair resources")
    
    return len(issues) == 0, issues

def test_key_pair_management_property():
    """
    Property 5: Key Pair Management
    For any deployment, key pair resources should be properly configured with:
    1. Conditional creation (resource) or usage (data source)
    2. Proper association with EC2 instance
    3. Required variables and validation
    4. Output availability
    """
    print("Testing Property 5: Key Pair Management")
    print("=" * 60)
    
    all_issues = []
    
    # Test 1: Key pair resource configuration
    test1_passed, test1_issues = test_key_pair_resource_exists()
    all_issues.extend(test1_issues)
    
    # Test 2: Existing key pair data source
    test2_passed, test2_issues = test_existing_key_pair_data_source()
    all_issues.extend(test2_issues)
    
    # Test 3: EC2 instance association
    test3_passed, test3_issues = test_ec2_key_pair_association()
    all_issues.extend(test3_issues)
    
    # Test 4: Key pair variables
    test4_passed, test4_issues = test_key_pair_variables()
    all_issues.extend(test4_issues)
    
    # Test 5: Key pair output
    test5_passed, test5_issues = test_key_pair_output()
    all_issues.extend(test5_issues)
    
    overall_passed = all([test1_passed, test2_passed, test3_passed, test4_passed, test5_passed])
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Key Pair Resource Configuration: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Existing Key Pair Data Source: {'PASS' if test2_passed else 'FAIL'}")
    print(f"EC2 Instance Association: {'PASS' if test3_passed else 'FAIL'}")
    print(f"Key Pair Variables: {'PASS' if test4_passed else 'FAIL'}")
    print(f"Key Pair Output: {'PASS' if test5_passed else 'FAIL'}")
    
    if overall_passed:
        print("\nAll key pair management tests PASSED!")
        return True
    else:
        print("\nSome key pair management tests FAILED:")
        for issue in all_issues:
            print(f"  - {issue}")
        return False

if __name__ == "__main__":
    print("OpenTofu Key Pair Management Property Tests")
    print("=" * 60)
    
    # Run the main property test
    test_passed = test_key_pair_management_property()
    
    print("\n" + "=" * 60)
    print("Overall Results:")
    print(f"Property 5 (Key Pair Management): {'PASS' if test_passed else 'FAIL'}")
    
    if test_passed:
        print("\nAll key pair management property tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome property tests FAILED!")
        sys.exit(1)
