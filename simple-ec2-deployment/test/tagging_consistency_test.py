#!/usr/bin/env python3
"""
Property-based test for resource tagging and naming consistency
Feature: simple-ec2-deployment, Property 7: Resource Tagging and Naming Consistency
Validates: Requirements 4.4, 5.4
"""
import os
import re
from typing import Dict, List, Tuple

def read_main_tf() -> str:
    """Read the main.tf file content"""
    try:
        with open("main.tf", "r") as f:
            return f.read()
    except FileNotFoundError:
        return None

def test_default_tags_configuration() -> Tuple[bool, List[str]]:
    """Test that provider has default_tags configured with required tags"""
    print("\nTesting default tags configuration in provider...")
    issues = []
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        return False, ["main.tf file not found"]
    
    # Check for default_tags block
    if 'default_tags {' not in main_tf_content:
        issues.append("Provider missing default_tags block")
        return False, issues
    
    print("  PASS: default_tags block found in provider")
    
    # Extract default_tags block
    default_tags_match = re.search(r'default_tags\s*\{(.*?)\}', main_tf_content, re.DOTALL)
    if not default_tags_match:
        issues.append("Could not parse default_tags block")
        return False, issues
    
    default_tags_content = default_tags_match.group(1)
    
    # Check for required tags
    required_tags = {
        "Project": r'Project\s*=\s*var\.project_name',
        "Environment": r'Environment\s*=',
        "ManagedBy": r'ManagedBy\s*=\s*"opentofu"',
        "Purpose": r'Purpose\s*='
    }
    
    for tag_name, pattern in required_tags.items():
        if re.search(pattern, default_tags_content):
            print(f"  PASS: {tag_name} tag found in default_tags")
        else:
            issues.append(f"Missing or incorrect {tag_name} tag in default_tags")
            print(f"  FAIL: {tag_name} tag not found in default_tags")
    
    return len(issues) == 0, issues

def test_resource_name_tags() -> Tuple[bool, List[str]]:
    """Test that all resources have Name tags following naming convention"""
    print("\nTesting Name tags on resources...")
    issues = []
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        return False, ["main.tf file not found"]
    
    # Define resources that should have Name tags
    resources_to_check = {
        "aws_key_pair": r'${var.project_name}-keypair',
        "aws_security_group": r'${var.project_name}-security-group',
        "aws_instance": r'${var.project_name}-instance',
    }
    
    for resource_type, expected_pattern in resources_to_check.items():
        # Find resource block
        resource_pattern = rf'resource "{resource_type}" "main".*?\{{(.*?)\n\}}'
        resource_match = re.search(resource_pattern, main_tf_content, re.DOTALL)
        
        if not resource_match:
            # Key pair might be conditional
            if resource_type == "aws_key_pair":
                continue
            issues.append(f"Resource {resource_type}.main not found")
            print(f"  FAIL: {resource_type}.main not found")
            continue
        
        resource_content = resource_match.group(1)
        
        # Check for Name tag
        if re.search(r'Name\s*=\s*.*' + re.escape(expected_pattern.replace('${var.project_name}', '')), resource_content):
            print(f"  PASS: {resource_type}.main has Name tag with correct pattern")
        elif 'Name =' in resource_content or 'Name=' in resource_content:
            print(f"  PASS: {resource_type}.main has Name tag")
        else:
            issues.append(f"{resource_type}.main missing Name tag")
            print(f"  FAIL: {resource_type}.main missing Name tag")
    
    # Check root_block_device Name tag
    if 'root_block_device {' in main_tf_content:
        root_block_match = re.search(r'root_block_device\s*\{(.*?)\}', main_tf_content, re.DOTALL)
        if root_block_match and 'Name =' in root_block_match.group(1):
            print("  PASS: root_block_device has Name tag")
        else:
            issues.append("root_block_device missing Name tag")
            print("  FAIL: root_block_device missing Name tag")
    
    return len(issues) == 0, issues

def test_naming_convention_consistency() -> Tuple[bool, List[str]]:
    """Test that all resource names follow the convention: ${var.project_name}-{resource-type}"""
    print("\nTesting naming convention consistency...")
    issues = []
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        return False, ["main.tf file not found"]
    
    # Check naming patterns
    naming_patterns = [
        (r'name_prefix\s*=\s*"\${var\.project_name}-sg"', "Security group name_prefix"),
        (r'Name\s*=\s*"\${var\.project_name}-security-group"', "Security group Name tag"),
        (r'Name\s*=\s*"\${var\.project_name}-instance"', "EC2 instance Name tag"),
        (r'Name\s*=\s*"\${var\.project_name}-root-volume"', "Root volume Name tag"),
    ]
    
    for pattern, description in naming_patterns:
        if re.search(pattern, main_tf_content):
            print(f"  PASS: {description} follows naming convention")
        else:
            issues.append(f"{description} does not follow naming convention")
            print(f"  FAIL: {description} does not follow naming convention")
    
    return len(issues) == 0, issues

def test_tagging_strategy_compliance() -> Tuple[bool, List[str]]:
    """
    Property 7: Resource Tagging and Naming Consistency
    For any infrastructure deployment, all resources should follow a consistent tagging
    strategy and naming convention for proper resource management and cost tracking.
    """
    print("Testing Property 7: Resource Tagging and Naming Consistency")
    print("=" * 60)
    
    all_issues = []
    
    # Test 1: Default tags configuration
    test1_passed, test1_issues = test_default_tags_configuration()
    all_issues.extend(test1_issues)
    
    # Test 2: Resource Name tags
    test2_passed, test2_issues = test_resource_name_tags()
    all_issues.extend(test2_issues)
    
    # Test 3: Naming convention consistency
    test3_passed, test3_issues = test_naming_convention_consistency()
    all_issues.extend(test3_issues)
    
    overall_passed = test1_passed and test2_passed and test3_passed
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Default Tags Configuration: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Resource Name Tags: {'PASS' if test2_passed else 'FAIL'}")
    print(f"Naming Convention Consistency: {'PASS' if test3_passed else 'FAIL'}")
    
    if overall_passed:
        print("\nAll tagging and naming consistency tests PASSED!")
        return True
    else:
        print("\nSome tagging and naming tests FAILED:")
        for issue in all_issues:
            print(f"  - {issue}")
        return False

def test_project_name_variable_usage() -> bool:
    """Test that var.project_name is used consistently across resources"""
    print("\nTesting var.project_name usage consistency...")
    
    main_tf_content = read_main_tf()
    if not main_tf_content:
        print("  FAIL: main.tf file not found")
        return False
    
    # Count occurrences of var.project_name
    project_name_count = len(re.findall(r'var\.project_name', main_tf_content))
    
    if project_name_count >= 5:  # Should appear in multiple places
        print(f"  PASS: var.project_name used {project_name_count} times across resources")
        return True
    else:
        print(f"  FAIL: var.project_name only used {project_name_count} times (expected >= 5)")
        return False

if __name__ == "__main__":
    print("Resource Tagging and Naming Consistency Property Tests")
    print("=" * 60)
    
    # Run the main property test
    test1_passed = test_tagging_strategy_compliance()
    test2_passed = test_project_name_variable_usage()
    
    print("\n" + "=" * 60)
    print("Overall Results:")
    print(f"Property 7 (Tagging Strategy Compliance): {'PASS' if test1_passed else 'FAIL'}")
    print(f"Variable Usage Consistency: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\nAll tagging and naming property tests PASSED!")
        exit(0)
    else:
        print("\nSome property tests FAILED!")
        exit(1)
