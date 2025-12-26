#!/usr/bin/env python3
"""
Property-based test for required output availability
Feature: simple-ec2-deployment, Property 9: Required Output Availability
Validates: Requirements 3.2, 3.5, 5.3
"""
import os
import re
from typing import Dict, List, Tuple

def read_outputs_tf() -> str:
    """Read the outputs.tf file content"""
    try:
        with open("outputs.tf", "r") as f:
            return f.read()
    except FileNotFoundError:
        return None

def test_required_outputs_exist() -> Tuple[bool, List[str]]:
    """Test that all required outputs are defined"""
    print("\nTesting required outputs existence...")
    issues = []
    
    outputs_content = read_outputs_tf()
    if not outputs_content:
        return False, ["outputs.tf file not found"]
    
    # Define required outputs per requirements
    required_outputs = {
        "instance_id": "EC2 instance ID (Req 5.3)",
        "public_ip": "Public IP address for SSH (Req 3.5)",
        "key_pair_name": "Key pair name for reference (Req 3.2)",
    }
    
    for output_name, description in required_outputs.items():
        pattern = rf'output "{output_name}"'
        if re.search(pattern, outputs_content):
            print(f"  PASS: Required output '{output_name}' found - {description}")
        else:
            issues.append(f"Missing required output: {output_name} - {description}")
            print(f"  FAIL: Required output '{output_name}' not found - {description}")
    
    return len(issues) == 0, issues

def test_output_descriptions() -> Tuple[bool, List[str]]:
    """Test that all outputs have descriptions"""
    print("\nTesting output descriptions...")
    issues = []
    
    outputs_content = read_outputs_tf()
    if not outputs_content:
        return False, ["outputs.tf file not found"]
    
    # Find all output blocks
    output_blocks = re.findall(r'output "([^"]+)" \{([^}]*(?:\{[^}]*\}[^}]*)*)\}', outputs_content, re.DOTALL)
    
    if not output_blocks:
        return False, ["No output blocks found"]
    
    for output_name, output_content in output_blocks:
        if 'description' in output_content:
            print(f"  PASS: Output '{output_name}' has description")
        else:
            issues.append(f"Output '{output_name}' missing description")
            print(f"  FAIL: Output '{output_name}' missing description")
    
    return len(issues) == 0, issues

def test_ssh_connection_output() -> Tuple[bool, List[str]]:
    """Test that SSH connection output is properly formatted"""
    print("\nTesting SSH connection output format...")
    issues = []
    
    outputs_content = read_outputs_tf()
    if not outputs_content:
        return False, ["outputs.tf file not found"]
    
    # Check for ssh_connection output
    if 'output "ssh_connection"' not in outputs_content:
        issues.append("SSH connection output not found")
        print("  FAIL: ssh_connection output not found")
        return False, issues
    
    print("  PASS: ssh_connection output exists")
    
    # Check that it references the public_ip
    ssh_output_match = re.search(r'output "ssh_connection".*?\{(.*?)\}', outputs_content, re.DOTALL)
    if ssh_output_match:
        ssh_content = ssh_output_match.group(1)
        if 'public_ip' in ssh_content or 'aws_instance.main.public_ip' in ssh_content:
            print("  PASS: ssh_connection references public IP")
        else:
            issues.append("ssh_connection output doesn't reference public IP")
            print("  FAIL: ssh_connection doesn't reference public IP")
        
        # Check for ec2-user (Amazon Linux default user)
        if 'ec2-user' in ssh_content:
            print("  PASS: ssh_connection uses correct username (ec2-user)")
        else:
            issues.append("ssh_connection doesn't specify ec2-user")
            print("  WARN: ssh_connection should use ec2-user for Amazon Linux")
    
    return len(issues) == 0, issues

def test_key_pair_output_conditional_logic() -> Tuple[bool, List[str]]:
    """Test that key_pair_name output handles both create and existing scenarios"""
    print("\nTesting key_pair_name conditional logic...")
    issues = []
    
    outputs_content = read_outputs_tf()
    if not outputs_content:
        return False, ["outputs.tf file not found"]
    
    key_pair_output = re.search(r'output "key_pair_name".*?\{(.*?)\}', outputs_content, re.DOTALL)
    if not key_pair_output:
        issues.append("key_pair_name output not found")
        print("  FAIL: key_pair_name output not found")
        return False, issues
    
    key_pair_content = key_pair_output.group(1)
    
    # Check for conditional logic
    if 'var.create_key_pair' in key_pair_content or '?' in key_pair_content:
        print("  PASS: key_pair_name uses conditional logic for create/existing scenarios")
    else:
        issues.append("key_pair_name missing conditional logic")
        print("  FAIL: key_pair_name should handle both create and existing key pair scenarios")
    
    # Check references to both scenarios
    if 'aws_key_pair.main' in key_pair_content or 'data.aws_key_pair.existing' in key_pair_content:
        print("  PASS: key_pair_name references appropriate key pair resources")
    else:
        issues.append("key_pair_name doesn't properly reference key pair resources")
        print("  FAIL: key_pair_name should reference key pair resources")
    
    return len(issues) == 0, issues

def test_essential_connection_information() -> Tuple[bool, List[str]]:
    """Test that all essential connection information is available as outputs"""
    print("\nTesting essential connection information availability...")
    issues = []
    
    outputs_content = read_outputs_tf()
    if not outputs_content:
        return False, ["outputs.tf file not found"]
    
    # Essential information for connecting to the instance
    essential_outputs = [
        ("public_ip", "Public IP for connection"),
        ("key_pair_name", "Key pair for authentication"),
        ("instance_id", "Instance identifier"),
    ]
    
    for output_name, purpose in essential_outputs:
        if f'output "{output_name}"' in outputs_content:
            print(f"  PASS: {output_name} available - {purpose}")
        else:
            issues.append(f"Missing essential output: {output_name} - {purpose}")
            print(f"  FAIL: Missing {output_name} - {purpose}")
    
    return len(issues) == 0, issues

def test_output_availability_property():
    """
    Property 9: Required Output Availability
    For any EC2 deployment, all essential connection information should be available
    as outputs including instance ID, public IP, and key pair name.
    """
    print("Testing Property 9: Required Output Availability")
    print("=" * 60)
    
    all_issues = []
    
    # Test 1: Required outputs exist
    test1_passed, test1_issues = test_required_outputs_exist()
    all_issues.extend(test1_issues)
    
    # Test 2: Output descriptions
    test2_passed, test2_issues = test_output_descriptions()
    all_issues.extend(test2_issues)
    
    # Test 3: SSH connection output
    test3_passed, test3_issues = test_ssh_connection_output()
    all_issues.extend(test3_issues)
    
    # Test 4: Key pair conditional logic
    test4_passed, test4_issues = test_key_pair_output_conditional_logic()
    all_issues.extend(test4_issues)
    
    # Test 5: Essential connection information
    test5_passed, test5_issues = test_essential_connection_information()
    all_issues.extend(test5_issues)
    
    overall_passed = all([test1_passed, test2_passed, test3_passed, test4_passed, test5_passed])
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Required Outputs Exist: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Output Descriptions: {'PASS' if test2_passed else 'FAIL'}")
    print(f"SSH Connection Output: {'PASS' if test3_passed else 'FAIL'}")
    print(f"Key Pair Conditional Logic: {'PASS' if test4_passed else 'FAIL'}")
    print(f"Essential Connection Info: {'PASS' if test5_passed else 'FAIL'}")
    
    if overall_passed:
        print("\nAll output availability tests PASSED!")
        return True
    else:
        print("\nSome output tests FAILED:")
        for issue in all_issues:
            print(f"  - {issue}")
        return False

def test_additional_useful_outputs() -> bool:
    """Test for additional useful outputs beyond requirements"""
    print("\nTesting additional useful outputs...")
    
    outputs_content = read_outputs_tf()
    if not outputs_content:
        print("  FAIL: outputs.tf file not found")
        return False
    
    additional_outputs = {
        "security_group_id": "Helpful for security group management",
        "ami_id": "Useful for tracking AMI version",
        "instance_state": "Helpful for monitoring instance status",
    }
    
    found_count = 0
    for output_name, purpose in additional_outputs.items():
        if f'output "{output_name}"' in outputs_content:
            print(f"  PASS: Additional output '{output_name}' found - {purpose}")
            found_count += 1
    
    if found_count > 0:
        print(f"  INFO: {found_count} additional helpful outputs provided")
        return True
    else:
        print("  INFO: Only required outputs provided")
        return True  # Not a failure

if __name__ == "__main__":
    print("Required Output Availability Property Tests")
    print("=" * 60)
    
    # Run the main property test
    test1_passed = test_output_availability_property()
    test2_passed = test_additional_useful_outputs()
    
    print("\n" + "=" * 60)
    print("Overall Results:")
    print(f"Property 9 (Output Availability): {'PASS' if test1_passed else 'FAIL'}")
    print(f"Additional Outputs Check: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\nAll output property tests PASSED!")
        exit(0)
    else:
        print("\nSome property tests FAILED!")
        exit(1)
