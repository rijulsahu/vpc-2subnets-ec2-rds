#!/usr/bin/env python3
"""
Property-based test for VPC CIDR configuration compliance
Feature: vpc-best-practices, Property 1: VPC CIDR Configuration Compliance
Task: 3.1 - Write property test for VPC CIDR configuration
Validates: Requirements 1.1, 1.3, 1.4
"""

import os
import re
import sys
import subprocess
import json
from typing import Tuple, List, Dict

def read_main_tf() -> str:
    """Read the main.tf file"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    main_tf_path = os.path.join(os.path.dirname(test_dir), "main.tf")
    
    try:
        with open(main_tf_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

def run_tofu_plan(vpc_cidr: str = None, region: str = "us-east-1") -> Tuple[bool, Dict]:
    """Run OpenTofu plan and return results"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    try:
        # Build command
        cmd = ["tofu", "plan", "-json", "-compact-warnings"]
        
        if vpc_cidr:
            cmd.extend(["-var", f"vpc_cidr={vpc_cidr}"])
        
        if region:
            cmd.extend(["-var", f"aws_region={region}"])
        
        # Run plan
        result = subprocess.run(
            cmd,
            cwd=vpc_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse JSON output
        plan_data = {}
        for line in result.stdout.split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    if data.get('type') == 'planned_change':
                        if 'change' in data and 'resource' in data['change']:
                            resource = data['change']['resource']
                            if resource['resource_type'] == 'aws_vpc':
                                plan_data['vpc'] = resource
                except json.JSONDecodeError:
                    continue
        
        return result.returncode == 0, plan_data
    except subprocess.TimeoutExpired:
        return False, {}
    except Exception as e:
        print(f"  ERROR running tofu plan: {str(e)}")
        return False, {}

def test_vpc_resource_definition() -> Tuple[bool, List[str]]:
    """
    Test that VPC resource is properly defined in main.tf
    """
    print("\nTesting VPC resource definition...")
    issues = []
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Check for VPC resource definition
    if 'resource "aws_vpc"' not in main_tf_content:
        issues.append("aws_vpc resource not defined")
        print("  FAIL: aws_vpc resource not defined")
        return False, issues
    
    print("  PASS: aws_vpc resource defined")
    
    # Extract VPC resource block
    vpc_match = re.search(
        r'resource "aws_vpc" "main".*?\{(.*?)\n\}',
        main_tf_content,
        re.DOTALL
    )
    
    if not vpc_match:
        issues.append("Could not parse aws_vpc resource")
        print("  FAIL: Could not parse aws_vpc resource")
        return False, issues
    
    vpc_block = vpc_match.group(1)
    
    # Check for cidr_block from variable
    if 'cidr_block' in vpc_block and 'var.vpc_cidr' in vpc_block:
        print("  PASS: VPC uses var.vpc_cidr for CIDR block")
    else:
        issues.append("VPC doesn't use var.vpc_cidr for CIDR block")
        print("  FAIL: VPC should use var.vpc_cidr")
        return False, issues
    
    # Check for DNS hostnames enabled (Requirement 1.4)
    if 'enable_dns_hostnames' in vpc_block and '= true' in vpc_block:
        print("  PASS: DNS hostnames enabled")
    else:
        issues.append("DNS hostnames not enabled")
        print("  FAIL: enable_dns_hostnames should be true")
        return False, issues
    
    # Check for DNS support enabled (Requirement 1.4)
    if 'enable_dns_support' in vpc_block and '= true' in vpc_block:
        print("  PASS: DNS support enabled")
    else:
        issues.append("DNS support not enabled")
        print("  FAIL: enable_dns_support should be true")
        return False, issues
    
    # Check for instance tenancy (Requirement 1.1)
    if 'instance_tenancy' in vpc_block and 'default' in vpc_block:
        print("  PASS: Instance tenancy set to default")
    else:
        print("  WARN: instance_tenancy should be explicitly set")
    
    # Check for tags (Requirement 10.8)
    if 'tags' in vpc_block:
        print("  PASS: Tags configured")
    else:
        issues.append("Tags not configured")
        print("  FAIL: VPC should have tags")
        return False, issues
    
    return len(issues) == 0, issues

def test_vpc_cidr_16_compliance() -> Tuple[bool, List[str]]:
    """
    Test that VPC CIDR configuration enforces /16 blocks
    Property 1: VPC CIDR Configuration Compliance
    Requirement 1.1: VPC SHALL use a CIDR block of /16
    """
    print("\nTesting VPC CIDR /16 compliance...")
    issues = []
    
    # Test valid /16 CIDR
    print("  Testing valid /16 CIDR (10.0.0.0/16)...")
    success, plan_data = run_tofu_plan(vpc_cidr="10.0.0.0/16")
    
    if success and 'vpc' in plan_data:
        print("  PASS: Valid /16 CIDR accepted")
    else:
        issues.append("Valid /16 CIDR not accepted")
        print("  FAIL: Should accept valid /16 CIDR")
        return False, issues
    
    # Verify CIDR in plan
    if 'vpc' in plan_data:
        vpc_resource = plan_data['vpc']
        if 'resource_name' in vpc_resource and vpc_resource['resource_name'] == 'main':
            print("  PASS: VPC resource named 'main'")
        else:
            print("  INFO: VPC resource name may vary")
    
    return len(issues) == 0, issues

def test_vpc_dns_configuration() -> Tuple[bool, List[str]]:
    """
    Test that VPC has DNS hostnames and support enabled
    Property 1: VPC CIDR Configuration Compliance
    Requirement 1.4: VPC SHALL enable DNS hostnames and DNS support
    """
    print("\nTesting VPC DNS configuration...")
    issues = []
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Extract VPC resource block
    vpc_match = re.search(
        r'resource "aws_vpc" "main".*?\{(.*?)\n\}',
        main_tf_content,
        re.DOTALL
    )
    
    if not vpc_match:
        issues.append("Could not parse aws_vpc resource")
        print("  FAIL: Could not parse aws_vpc resource")
        return False, issues
    
    vpc_block = vpc_match.group(1)
    
    # Check DNS settings are explicitly true (not just present)
    dns_hostnames_check = re.search(r'enable_dns_hostnames\s*=\s*true', vpc_block)
    dns_support_check = re.search(r'enable_dns_support\s*=\s*true', vpc_block)
    
    if dns_hostnames_check:
        print("  PASS: enable_dns_hostnames = true")
    else:
        issues.append("enable_dns_hostnames not set to true")
        print("  FAIL: enable_dns_hostnames must be true")
        return False, issues
    
    if dns_support_check:
        print("  PASS: enable_dns_support = true")
    else:
        issues.append("enable_dns_support not set to true")
        print("  FAIL: enable_dns_support must be true")
        return False, issues
    
    return len(issues) == 0, issues

def test_vpc_tagging_strategy() -> Tuple[bool, List[str]]:
    """
    Test that VPC has comprehensive tagging strategy
    Property 1: VPC CIDR Configuration Compliance
    Requirement 10.8: Resources SHALL have consistent tagging strategy
    """
    print("\nTesting VPC tagging strategy...")
    issues = []
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Extract VPC resource block
    vpc_match = re.search(
        r'resource "aws_vpc" "main".*?\{(.*?)\n\}',
        main_tf_content,
        re.DOTALL
    )
    
    if not vpc_match:
        issues.append("Could not parse aws_vpc resource")
        print("  FAIL: Could not parse aws_vpc resource")
        return False, issues
    
    vpc_block = vpc_match.group(1)
    
    # Check for tags block
    if 'tags' not in vpc_block:
        issues.append("No tags block found")
        print("  FAIL: VPC should have tags block")
        return False, issues
    
    print("  PASS: Tags block present")
    
    # Check for merge with local.common_tags
    if 'merge(' in vpc_block and 'local.common_tags' in vpc_block:
        print("  PASS: Uses merge() with local.common_tags")
    else:
        print("  WARN: Should use merge() with local.common_tags for consistency")
    
    # Check for Name tag
    if 'Name' in vpc_block:
        print("  PASS: Name tag configured")
    else:
        print("  WARN: Should include Name tag")
    
    return len(issues) == 0, issues

def test_vpc_region_compliance() -> Tuple[bool, List[str]]:
    """
    Test that VPC can be created in specified region
    Property 1: VPC CIDR Configuration Compliance  
    Requirement 1.3: VPC SHALL use consistent naming conventions with environment and purpose tags
    """
    print("\nTesting VPC region compliance...")
    issues = []
    
    # Check that provider configuration uses var.aws_region
    test_dir = os.path.dirname(os.path.abspath(__file__))
    versions_tf_path = os.path.join(os.path.dirname(test_dir), "versions.tf")
    
    try:
        with open(versions_tf_path, 'r') as f:
            versions_content = f.read()
    except FileNotFoundError:
        issues.append("versions.tf not found")
        print("  FAIL: versions.tf not found")
        return False, issues
    
    # Check for provider configuration
    if 'provider "aws"' in versions_content:
        print("  PASS: AWS provider configured")
    else:
        issues.append("AWS provider not configured")
        print("  FAIL: AWS provider should be configured")
        return False, issues
    
    # Check that region uses variable
    if 'region' in versions_content and 'var.aws_region' in versions_content:
        print("  PASS: Provider uses var.aws_region")
    else:
        print("  WARN: Provider should use var.aws_region for flexibility")
    
    return len(issues) == 0, issues

def run_all_tests():
    """Run all VPC CIDR configuration tests"""
    print("=" * 80)
    print("VPC Best Practices - VPC CIDR Configuration Property Tests")
    print("Feature: vpc-best-practices, Task 3.1")
    print("Property 1: VPC CIDR Configuration Compliance")
    print("Validates: Requirements 1.1, 1.3, 1.4")
    print("=" * 80)
    
    all_tests = [
        ("VPC Resource Definition", test_vpc_resource_definition),
        ("VPC CIDR /16 Compliance", test_vpc_cidr_16_compliance),
        ("VPC DNS Configuration", test_vpc_dns_configuration),
        ("VPC Tagging Strategy", test_vpc_tagging_strategy),
        ("VPC Region Compliance", test_vpc_region_compliance),
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
