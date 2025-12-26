#!/usr/bin/env python3
"""
Property-based test for OpenTofu variable validation
Feature: simple-ec2-deployment, Property 2: Free Tier Instance Type Compliance
Validates: Requirements 1.2, 4.1
"""

import os
import re
import sys
from typing import Tuple, List

def read_variables_tf() -> str:
    """Read the variables.tf file"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    variables_path = os.path.join(os.path.dirname(test_dir), "variables.tf")
    
    try:
        with open(variables_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

def test_free_tier_instance_type_compliance() -> Tuple[bool, List[str]]:
    """
    Property 2: Free Tier Instance Type Compliance
    For any EC2 instance created by the configuration, the instance type should be 
    either t2.micro or t3.micro to ensure free tier eligibility.
    """
    print("\nTesting instance_type variable validation...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for instance_type variable definition
    if 'variable "instance_type"' not in variables_content:
        issues.append("instance_type variable not defined")
        print("  FAIL: instance_type variable not defined")
        return False, issues
    
    print("  PASS: instance_type variable defined")
    
    # Check for validation block
    instance_type_match = re.search(
        r'variable "instance_type".*?\{(.*?)\n\}',
        variables_content,
        re.DOTALL
    )
    
    if not instance_type_match:
        issues.append("Could not parse instance_type variable")
        print("  FAIL: Could not parse instance_type variable")
        return False, issues
    
    instance_type_block = instance_type_match.group(1)
    
    # Check for validation block
    if 'validation {' not in instance_type_block:
        issues.append("instance_type missing validation block")
        print("  FAIL: instance_type missing validation block")
        return False, issues
    
    print("  PASS: instance_type has validation block")
    
    # Check that validation includes t2.micro and t3.micro
    if 't2.micro' in instance_type_block and 't3.micro' in instance_type_block:
        print("  PASS: Validation includes t2.micro and t3.micro")
    else:
        issues.append("Validation doesn't include both t2.micro and t3.micro")
        print("  FAIL: Validation should include t2.micro and t3.micro")
        return False, issues
    
    # Check for "free tier" in error message
    if 'free tier' in instance_type_block.lower():
        print("  PASS: Validation error message mentions free tier")
    else:
        print("  WARN: Validation error message should mention free tier")
    
    # Check for contains() function in validation
    if 'contains(' in instance_type_block:
        print("  PASS: Uses contains() for validation")
    else:
        print("  WARN: Should use contains() function for validation")
    
    return len(issues) == 0, issues

def test_volume_size_validation() -> Tuple[bool, List[str]]:
    """Additional validation test for volume size compliance"""
    print("\nTesting root_volume_size variable validation...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for root_volume_size variable definition
    if 'variable "root_volume_size"' not in variables_content:
        issues.append("root_volume_size variable not defined")
        print("  FAIL: root_volume_size variable not defined")
        return False, issues
    
    print("  PASS: root_volume_size variable defined")
    
    # Extract root_volume_size variable block
    volume_size_match = re.search(
        r'variable "root_volume_size".*?\{(.*?)\n\}',
        variables_content,
        re.DOTALL
    )
    
    if not volume_size_match:
        issues.append("Could not parse root_volume_size variable")
        print("  FAIL: Could not parse root_volume_size variable")
        return False, issues
    
    volume_size_block = volume_size_match.group(1)
    
    # Check for validation block
    if 'validation {' not in volume_size_block:
        issues.append("root_volume_size missing validation block")
        print("  FAIL: root_volume_size missing validation block")
        return False, issues
    
    print("  PASS: root_volume_size has validation block")
    
    # Check for 8GB minimum and 30GB maximum in validation
    if '8' in volume_size_block and '30' in volume_size_block:
        print("  PASS: Validation includes 8GB min and 30GB max limits")
    else:
        issues.append("Validation doesn't include proper size limits (8-30GB)")
        print("  FAIL: Validation should enforce 8-30GB limits")
        return False, issues
    
    # Check for "free tier" in error message
    if 'free tier' in volume_size_block.lower():
        print("  PASS: Validation error message mentions free tier")
    else:
        print("  WARN: Validation error message should mention free tier")
    
    return len(issues) == 0, issues

def test_volume_type_validation() -> Tuple[bool, List[str]]:
    """Test root_volume_type variable validation"""
    print("\nTesting root_volume_type variable validation...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for root_volume_type variable
    if 'variable "root_volume_type"' not in variables_content:
        issues.append("root_volume_type variable not defined")
        print("  FAIL: root_volume_type variable not defined")
        return False, issues
    
    print("  PASS: root_volume_type variable defined")
    
    # Extract variable block
    volume_type_match = re.search(
        r'variable "root_volume_type".*?\{(.*?)\n\}',
        variables_content,
        re.DOTALL
    )
    
    if not volume_type_match:
        issues.append("Could not parse root_volume_type variable")
        print("  FAIL: Could not parse root_volume_type variable")
        return False, issues
    
    volume_type_block = volume_type_match.group(1)
    
    # Check for validation block
    if 'validation {' not in volume_type_block:
        issues.append("root_volume_type missing validation block")
        print("  FAIL: root_volume_type missing validation block")
        return False, issues
    
    print("  PASS: root_volume_type has validation block")
    
    # Check that validation includes gp2 and gp3
    if 'gp2' in volume_type_block and 'gp3' in volume_type_block:
        print("  PASS: Validation includes gp2 and gp3")
    else:
        issues.append("Validation doesn't include both gp2 and gp3")
        print("  FAIL: Validation should include gp2 and gp3")
        return False, issues
    
    return len(issues) == 0, issues

if __name__ == "__main__":
    print("OpenTofu Variable Validation Property Tests")
    print("=" * 60)
    
    all_issues = []
    
    # Run the property tests
    test1_passed, test1_issues = test_free_tier_instance_type_compliance()
    all_issues.extend(test1_issues)
    
    test2_passed, test2_issues = test_volume_size_validation()
    all_issues.extend(test2_issues)
    
    test3_passed, test3_issues = test_volume_type_validation()
    all_issues.extend(test3_issues)
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Property 2 (Instance Type Validation): {'PASS' if test1_passed else 'FAIL'}")
    print(f"Volume Size Validation: {'PASS' if test2_passed else 'FAIL'}")
    print(f"Volume Type Validation: {'PASS' if test3_passed else 'FAIL'}")
    
    overall_passed = test1_passed and test2_passed and test3_passed
    
    if overall_passed:
        print("\nAll variable validation property tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome property tests FAILED:")
        for issue in all_issues:
            print(f"  - {issue}")
        sys.exit(1)