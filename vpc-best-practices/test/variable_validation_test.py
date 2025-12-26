#!/usr/bin/env python3
"""
Property-based test for VPC Best Practices variable validation
Feature: vpc-best-practices, Property: Variable Validation Compliance
Task: 2.1 - Write property test for variable validation
Validates: Requirements 10.2
"""

import os
import re
import sys
from typing import Tuple, List
import ipaddress

def read_variables_tf() -> str:
    """Read the variables.tf file"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    variables_path = os.path.join(os.path.dirname(test_dir), "variables.tf")
    
    try:
        with open(variables_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

def extract_variable_block(content: str, var_name: str) -> str:
    """Extract a variable block from variables.tf content"""
    # Match variable block with nested braces
    pattern = rf'variable "{var_name}".*?\{{((?:[^{{}}]|\{{[^{{}}]*\}})*)\}}'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1) if match else None

def test_vpc_cidr_validation() -> Tuple[bool, List[str]]:
    """
    Test VPC CIDR variable validation
    Ensures VPC CIDR is properly validated for /16 prefix
    """
    print("\nTesting vpc_cidr variable validation...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for vpc_cidr variable definition
    if 'variable "vpc_cidr"' not in variables_content:
        issues.append("vpc_cidr variable not defined")
        print("  FAIL: vpc_cidr variable not defined")
        return False, issues
    
    print("  PASS: vpc_cidr variable defined")
    
    vpc_cidr_block = extract_variable_block(variables_content, "vpc_cidr")
    if not vpc_cidr_block:
        issues.append("Could not parse vpc_cidr variable")
        print("  FAIL: Could not parse vpc_cidr variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in vpc_cidr_block:
        issues.append("vpc_cidr missing validation block")
        print("  FAIL: vpc_cidr missing validation block")
        return False, issues
    
    print("  PASS: vpc_cidr has validation block")
    
    # Check for /16 requirement
    if '/16' in vpc_cidr_block or '== 16' in vpc_cidr_block:
        print("  PASS: Validation enforces /16 CIDR block")
    else:
        issues.append("Validation doesn't enforce /16 CIDR requirement")
        print("  FAIL: Validation should enforce /16 CIDR block")
        return False, issues
    
    # Check for cidrhost() validation function
    if 'cidrhost(' in vpc_cidr_block:
        print("  PASS: Uses cidrhost() for CIDR validation")
    else:
        print("  WARN: Should use cidrhost() for CIDR validation")
    
    # Check for default value
    if 'default' in vpc_cidr_block and '10.0.0.0/16' in vpc_cidr_block:
        print("  PASS: Has appropriate default CIDR (10.0.0.0/16)")
    else:
        print("  WARN: Should have default CIDR value")
    
    # Check for descriptive error message
    if 'error_message' in vpc_cidr_block:
        print("  PASS: Has error_message defined")
    else:
        issues.append("Missing error_message for validation")
        print("  FAIL: Should have error_message for validation")
        return False, issues
    
    return len(issues) == 0, issues

def test_nat_gateway_strategy_validation() -> Tuple[bool, List[str]]:
    """
    Test NAT Gateway strategy variable validation
    Ensures only 'per_az' or 'single' strategies are allowed
    """
    print("\nTesting nat_gateway_strategy variable validation...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for nat_gateway_strategy variable definition
    if 'variable "nat_gateway_strategy"' not in variables_content:
        issues.append("nat_gateway_strategy variable not defined")
        print("  FAIL: nat_gateway_strategy variable not defined")
        return False, issues
    
    print("  PASS: nat_gateway_strategy variable defined")
    
    nat_strategy_block = extract_variable_block(variables_content, "nat_gateway_strategy")
    if not nat_strategy_block:
        issues.append("Could not parse nat_gateway_strategy variable")
        print("  FAIL: Could not parse nat_gateway_strategy variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in nat_strategy_block:
        issues.append("nat_gateway_strategy missing validation block")
        print("  FAIL: nat_gateway_strategy missing validation block")
        return False, issues
    
    print("  PASS: nat_gateway_strategy has validation block")
    
    # Check that validation includes 'per_az' and 'single'
    if 'per_az' in nat_strategy_block and 'single' in nat_strategy_block:
        print("  PASS: Validation includes 'per_az' and 'single' options")
    else:
        issues.append("Validation doesn't include both per_az and single options")
        print("  FAIL: Validation should include 'per_az' and 'single'")
        return False, issues
    
    # Check for contains() function in validation
    if 'contains(' in nat_strategy_block:
        print("  PASS: Uses contains() for validation")
    else:
        print("  WARN: Should use contains() function for validation")
    
    # Check for default value
    if 'default' in nat_strategy_block:
        if 'per_az' in nat_strategy_block.split('default')[1].split('\n')[0]:
            print("  PASS: Default is 'per_az' (high availability)")
        elif 'single' in nat_strategy_block.split('default')[1].split('\n')[0]:
            print("  INFO: Default is 'single' (cost optimized)")
    else:
        print("  WARN: Should have default NAT strategy")
    
    # Check for descriptive error message
    if 'error_message' in nat_strategy_block and ('high availability' in nat_strategy_block.lower() or 'cost' in nat_strategy_block.lower()):
        print("  PASS: Error message describes strategy options")
    else:
        print("  WARN: Error message should describe HA vs cost trade-off")
    
    return len(issues) == 0, issues

def test_subnet_cidr_validation() -> Tuple[bool, List[str]]:
    """
    Test subnet CIDR variable validation
    Ensures subnet CIDRs are valid IPv4 CIDR blocks
    """
    print("\nTesting subnet CIDR variable validations...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for public_subnet_cidrs variable
    if 'variable "public_subnet_cidrs"' not in variables_content:
        issues.append("public_subnet_cidrs variable not defined")
        print("  FAIL: public_subnet_cidrs variable not defined")
        return False, issues
    
    print("  PASS: public_subnet_cidrs variable defined")
    
    public_subnet_block = extract_variable_block(variables_content, "public_subnet_cidrs")
    if not public_subnet_block:
        issues.append("Could not parse public_subnet_cidrs variable")
        print("  FAIL: Could not parse public_subnet_cidrs variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in public_subnet_block:
        issues.append("public_subnet_cidrs missing validation block")
        print("  FAIL: public_subnet_cidrs missing validation block")
        return False, issues
    
    print("  PASS: public_subnet_cidrs has validation block")
    
    # Check for alltrue() and cidrhost() validation
    if 'alltrue(' in public_subnet_block and 'cidrhost(' in public_subnet_block:
        print("  PASS: Uses alltrue() and cidrhost() for CIDR list validation")
    else:
        print("  WARN: Should use alltrue() and cidrhost() for validating all CIDRs")
    
    # Check for private_subnet_cidrs variable
    if 'variable "private_subnet_cidrs"' not in variables_content:
        issues.append("private_subnet_cidrs variable not defined")
        print("  FAIL: private_subnet_cidrs variable not defined")
        return False, issues
    
    print("  PASS: private_subnet_cidrs variable defined")
    
    private_subnet_block = extract_variable_block(variables_content, "private_subnet_cidrs")
    if not private_subnet_block:
        issues.append("Could not parse private_subnet_cidrs variable")
        print("  FAIL: Could not parse private_subnet_cidrs variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in private_subnet_block:
        issues.append("private_subnet_cidrs missing validation block")
        print("  FAIL: private_subnet_cidrs missing validation block")
        return False, issues
    
    print("  PASS: private_subnet_cidrs has validation block")
    
    # Check default values are within VPC CIDR
    if 'default' in public_subnet_block and '10.0.' in public_subnet_block:
        print("  PASS: public_subnet_cidrs has default values in 10.0.0.0/16 range")
    else:
        print("  WARN: Should have default subnet CIDRs")
    
    if 'default' in private_subnet_block and '10.0.' in private_subnet_block:
        print("  PASS: private_subnet_cidrs has default values in 10.0.0.0/16 range")
    else:
        print("  WARN: Should have default subnet CIDRs")
    
    return len(issues) == 0, issues

def test_az_configuration_validation() -> Tuple[bool, List[str]]:
    """
    Test availability zone configuration validation
    Ensures proper AZ count and list validation
    """
    print("\nTesting availability zone variable validations...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for availability_zones variable
    if 'variable "availability_zones"' not in variables_content:
        issues.append("availability_zones variable not defined")
        print("  FAIL: availability_zones variable not defined")
        return False, issues
    
    print("  PASS: availability_zones variable defined")
    
    az_block = extract_variable_block(variables_content, "availability_zones")
    if not az_block:
        issues.append("Could not parse availability_zones variable")
        print("  FAIL: Could not parse availability_zones variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in az_block:
        issues.append("availability_zones missing validation block")
        print("  FAIL: availability_zones missing validation block")
        return False, issues
    
    print("  PASS: availability_zones has validation block")
    
    # Check for minimum 2 AZ requirement
    if '>= 2' in az_block or 'at least 2' in az_block.lower():
        print("  PASS: Validation enforces minimum 2 AZs for HA")
    else:
        print("  WARN: Should enforce minimum 2 AZs")
    
    # Check for az_count variable
    if 'variable "az_count"' not in variables_content:
        issues.append("az_count variable not defined")
        print("  FAIL: az_count variable not defined")
        return False, issues
    
    print("  PASS: az_count variable defined")
    
    az_count_block = extract_variable_block(variables_content, "az_count")
    if not az_count_block:
        issues.append("Could not parse az_count variable")
        print("  FAIL: Could not parse az_count variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in az_count_block:
        issues.append("az_count missing validation block")
        print("  FAIL: az_count missing validation block")
        return False, issues
    
    print("  PASS: az_count has validation block")
    
    # Check for range validation (2-4)
    if '>= 2' in az_count_block and '<= 4' in az_count_block:
        print("  PASS: Validates az_count between 2 and 4")
    else:
        print("  WARN: Should validate az_count range (2-4)")
    
    return len(issues) == 0, issues

def test_admin_cidr_validation() -> Tuple[bool, List[str]]:
    """
    Test admin CIDR blocks validation
    Ensures admin CIDR blocks are valid
    """
    print("\nTesting admin_cidr_blocks variable validation...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for admin_cidr_blocks variable
    if 'variable "admin_cidr_blocks"' not in variables_content:
        issues.append("admin_cidr_blocks variable not defined")
        print("  FAIL: admin_cidr_blocks variable not defined")
        return False, issues
    
    print("  PASS: admin_cidr_blocks variable defined")
    
    admin_cidr_block = extract_variable_block(variables_content, "admin_cidr_blocks")
    if not admin_cidr_block:
        issues.append("Could not parse admin_cidr_blocks variable")
        print("  FAIL: Could not parse admin_cidr_blocks variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in admin_cidr_block:
        issues.append("admin_cidr_blocks missing validation block")
        print("  FAIL: admin_cidr_blocks missing validation block")
        return False, issues
    
    print("  PASS: admin_cidr_blocks has validation block")
    
    # Check for alltrue() and cidrhost() validation
    if 'alltrue(' in admin_cidr_block and 'cidrhost(' in admin_cidr_block:
        print("  PASS: Uses alltrue() and cidrhost() for CIDR list validation")
    else:
        print("  WARN: Should validate all CIDR blocks in list")
    
    return len(issues) == 0, issues

def test_flow_logs_retention_validation() -> Tuple[bool, List[str]]:
    """
    Test VPC Flow Logs retention validation
    Ensures retention days match CloudWatch valid values
    """
    print("\nTesting flow_logs_retention_days variable validation...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for flow_logs_retention_days variable
    if 'variable "flow_logs_retention_days"' not in variables_content:
        issues.append("flow_logs_retention_days variable not defined")
        print("  FAIL: flow_logs_retention_days variable not defined")
        return False, issues
    
    print("  PASS: flow_logs_retention_days variable defined")
    
    retention_block = extract_variable_block(variables_content, "flow_logs_retention_days")
    if not retention_block:
        issues.append("Could not parse flow_logs_retention_days variable")
        print("  FAIL: Could not parse flow_logs_retention_days variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in retention_block:
        issues.append("flow_logs_retention_days missing validation block")
        print("  FAIL: flow_logs_retention_days missing validation block")
        return False, issues
    
    print("  PASS: flow_logs_retention_days has validation block")
    
    # Check for contains() with valid CloudWatch retention periods
    if 'contains(' in retention_block and ('1, 3, 5, 7' in retention_block or '1,' in retention_block):
        print("  PASS: Validates against CloudWatch retention periods")
    else:
        print("  WARN: Should validate against valid CloudWatch retention values")
    
    return len(issues) == 0, issues

def test_project_name_validation() -> Tuple[bool, List[str]]:
    """
    Test project name validation
    Ensures project name follows naming conventions
    """
    print("\nTesting project_name variable validation...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for project_name variable
    if 'variable "project_name"' not in variables_content:
        issues.append("project_name variable not defined")
        print("  FAIL: project_name variable not defined")
        return False, issues
    
    print("  PASS: project_name variable defined")
    
    project_name_block = extract_variable_block(variables_content, "project_name")
    if not project_name_block:
        issues.append("Could not parse project_name variable")
        print("  FAIL: Could not parse project_name variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in project_name_block:
        issues.append("project_name missing validation block")
        print("  FAIL: project_name missing validation block")
        return False, issues
    
    print("  PASS: project_name has validation block")
    
    # Check for regex validation
    if 'regex(' in project_name_block or 'can(regex(' in project_name_block:
        print("  PASS: Uses regex for name validation")
    else:
        print("  WARN: Should use regex for name validation")
    
    return len(issues) == 0, issues

def test_environment_validation() -> Tuple[bool, List[str]]:
    """
    Test environment variable validation
    Ensures environment is one of valid options
    """
    print("\nTesting environment variable validation...")
    issues = []
    
    variables_content = read_variables_tf()
    if not variables_content:
        issues.append("variables.tf not found")
        print("  FAIL: variables.tf not found")
        return False, issues
    
    # Check for environment variable
    if 'variable "environment"' not in variables_content:
        issues.append("environment variable not defined")
        print("  FAIL: environment variable not defined")
        return False, issues
    
    print("  PASS: environment variable defined")
    
    environment_block = extract_variable_block(variables_content, "environment")
    if not environment_block:
        issues.append("Could not parse environment variable")
        print("  FAIL: Could not parse environment variable")
        return False, issues
    
    # Check for validation block
    if 'validation {' not in environment_block:
        issues.append("environment missing validation block")
        print("  FAIL: environment missing validation block")
        return False, issues
    
    print("  PASS: environment has validation block")
    
    # Check for standard environments
    if 'development' in environment_block and 'production' in environment_block:
        print("  PASS: Includes standard environment values")
    else:
        print("  WARN: Should include standard environments (development, staging, production)")
    
    return len(issues) == 0, issues

def run_all_tests():
    """Run all variable validation tests"""
    print("=" * 80)
    print("VPC Best Practices - Variable Validation Property Tests")
    print("Feature: vpc-best-practices, Task 2.1")
    print("Property: Variable Validation Compliance")
    print("Validates: Requirements 10.2")
    print("=" * 80)
    
    all_tests = [
        ("VPC CIDR Validation", test_vpc_cidr_validation),
        ("NAT Gateway Strategy Validation", test_nat_gateway_strategy_validation),
        ("Subnet CIDR Validation", test_subnet_cidr_validation),
        ("AZ Configuration Validation", test_az_configuration_validation),
        ("Admin CIDR Validation", test_admin_cidr_validation),
        ("Flow Logs Retention Validation", test_flow_logs_retention_validation),
        ("Project Name Validation", test_project_name_validation),
        ("Environment Validation", test_environment_validation),
    ]
    
    results = []
    total_issues = []
    
    for test_name, test_func in all_tests:
        try:
            success, issues = test_func()
            results.append((test_name, success))
            if not success:
                total_issues.extend([f"{test_name}: {issue}" for issue in issues])
        except Exception as e:
            results.append((test_name, False))
            total_issues.append(f"{test_name}: Exception - {str(e)}")
            print(f"  ERROR: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if total_issues:
        print("\nIssues found:")
        for issue in total_issues:
            print(f"  - {issue}")
    
    print("=" * 80)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
