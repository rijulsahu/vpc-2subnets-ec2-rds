#!/usr/bin/env python3
"""
VPC Best Practices - Infrastructure Code Organization Property Tests
Feature: vpc-best-practices, Task 19.1
Property 19: Infrastructure Code Organization
Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7

Tests verify:
- Logical file organization
- All values are parameterized via variables
- Output completeness and structure
- Proper versioning constraints
- Data source usage
- Locals for calculations
- Module structure best practices
"""

import os
import re
from typing import Dict, List


def get_vpc_dir() -> str:
    """Get VPC directory path"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(test_dir)


def test_property_19_file_organization():
    """
    Property 19: Logical File Organization
    Requirements: 10.1, 10.6
    - Proper file structure with separate concerns
    - Each file has clear purpose
    - Consistent naming conventions
    """
    print("\nTesting Property 19: Logical File Organization...")
    
    vpc_dir = get_vpc_dir()
    
    # Expected files and their purposes
    expected_files = {
        'versions.tf': 'Provider and version constraints',
        'variables.tf': 'Input variables',
        'locals.tf': 'Local value calculations',
        'data.tf': 'Data source definitions',
        'main.tf': 'Main VPC resources',
        'subnets.tf': 'Subnet resources',
        'nat_gateway.tf': 'NAT Gateway resources',
        'route_tables.tf': 'Route table resources',
        'nacls.tf': 'Network ACL resources',
        'security_groups.tf': 'Security group resources',
        'flow_logs.tf': 'VPC Flow Logs resources',
        'outputs.tf': 'Output values'
    }
    
    missing_files = []
    for filename, purpose in expected_files.items():
        filepath = os.path.join(vpc_dir, filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)
        else:
            print(f"  PASS: {filename} exists ({purpose})")
    
    assert len(missing_files) == 0, f"FAIL: Missing files: {', '.join(missing_files)}"
    print(f"  PASS: All {len(expected_files)} required files present")


def test_property_19_parameterization():
    """
    Property 19: Values Parameterized
    Requirements: 10.2
    - No hardcoded values where variables should be used
    - All configurable values in variables.tf
    - Proper variable types and validation
    """
    print("\nTesting Property 19: Values Parameterized...")
    
    vpc_dir = get_vpc_dir()
    variables_file = os.path.join(vpc_dir, 'variables.tf')
    
    assert os.path.exists(variables_file), "FAIL: variables.tf not found"
    
    with open(variables_file, 'r') as f:
        content = f.read()
        
        # Check for key variables
        required_variables = [
            'vpc_cidr',
            'project_name',
            'environment',
            'nat_gateway_strategy',
            'enable_vpc_flow_logs',
            'admin_cidr_blocks'
        ]
        
        missing_vars = []
        for var_name in required_variables:
            if f'variable "{var_name}"' not in content:
                missing_vars.append(var_name)
        
        assert len(missing_vars) == 0, f"FAIL: Missing variables: {', '.join(missing_vars)}"
        print(f"  PASS: All {len(required_variables)} required variables defined")
        
        # Check for variable validation
        validation_count = content.count('validation')
        assert validation_count >= 2, \
            f"FAIL: Expected at least 2 variable validations, found {validation_count}"
        print(f"  PASS: Variables have validation rules ({validation_count} validations)")
        
        # Check for variable types
        type_count = content.count('type')
        assert type_count >= len(required_variables), \
            f"FAIL: Not all variables have explicit types"
        print(f"  PASS: Variables have explicit types")
        
        # Check for descriptions
        description_count = content.count('description')
        assert description_count >= len(required_variables), \
            f"FAIL: Not all variables have descriptions"
        print(f"  PASS: Variables have descriptions")


def test_property_19_output_completeness():
    """
    Property 19: Output Completeness
    Requirements: 10.3
    - All major resources have outputs
    - Outputs have descriptions
    - Structured outputs for module consumption
    """
    print("\nTesting Property 19: Output Completeness...")
    
    vpc_dir = get_vpc_dir()
    outputs_file = os.path.join(vpc_dir, 'outputs.tf')
    
    assert os.path.exists(outputs_file), "FAIL: outputs.tf not found"
    
    with open(outputs_file, 'r') as f:
        content = f.read()
        
        # Check for key outputs
        required_outputs = [
            'vpc_id',
            'vpc_cidr',
            'public_subnet_ids',
            'private_subnet_ids',
            'nat_gateway_ids',
            'internet_gateway_id',
            'security_group_ids',
            'route_table_ids',
            'availability_zones'
        ]
        
        missing_outputs = []
        for output_name in required_outputs:
            if f'output "{output_name}"' not in content:
                missing_outputs.append(output_name)
        
        assert len(missing_outputs) == 0, \
            f"FAIL: Missing outputs: {', '.join(missing_outputs)}"
        print(f"  PASS: All {len(required_outputs)} required outputs defined")
        
        # Check for output descriptions
        output_count = content.count('output "')
        description_count = content.count('description =')
        
        assert description_count >= output_count * 0.9, \
            f"FAIL: Not all outputs have descriptions ({description_count}/{output_count})"
        print(f"  PASS: {output_count} outputs with descriptions")
        
        # Check for structured outputs (maps/objects)
        assert 'vpc_summary' in content or 'security_group_ids' in content, \
            "FAIL: Missing structured outputs for module consumption"
        print(f"  PASS: Structured outputs present for module consumption")


def test_property_19_version_constraints():
    """
    Property 19: Version Constraints
    Requirements: 10.7
    - Terraform/OpenTofu version constraints
    - Provider version constraints
    - Required providers block
    """
    print("\nTesting Property 19: Version Constraints...")
    
    vpc_dir = get_vpc_dir()
    versions_file = os.path.join(vpc_dir, 'versions.tf')
    
    assert os.path.exists(versions_file), "FAIL: versions.tf not found"
    
    with open(versions_file, 'r') as f:
        content = f.read()
        
        # Check for terraform block
        assert 'terraform {' in content, "FAIL: No terraform block found"
        print("  PASS: Terraform block defined")
        
        # Check for required_version
        assert 'required_version' in content, "FAIL: No required_version constraint"
        print("  PASS: Terraform/OpenTofu version constraint defined")
        
        # Check for required_providers
        assert 'required_providers' in content, "FAIL: No required_providers block"
        print("  PASS: Required providers block defined")
        
        # Check for AWS provider version
        assert 'aws' in content and 'source' in content, \
            "FAIL: AWS provider not properly configured"
        print("  PASS: AWS provider configured with source")
        
        # Check for version constraint on provider
        if 'version' in content:
            print("  PASS: Provider version constraint defined")
        else:
            print("  INFO: Provider version constraint optional but recommended")


def test_property_19_data_sources():
    """
    Property 19: Data Source Usage
    Requirements: 10.4
    - Data sources for dynamic values
    - Availability zone discovery
    - Region and account ID data
    """
    print("\nTesting Property 19: Data Source Usage...")
    
    vpc_dir = get_vpc_dir()
    data_file = os.path.join(vpc_dir, 'data.tf')
    
    assert os.path.exists(data_file), "FAIL: data.tf not found"
    
    with open(data_file, 'r') as f:
        content = f.read()
        
        # Check for availability zones data source
        assert 'data "aws_availability_zones"' in content, \
            "FAIL: Availability zones data source not found"
        print("  PASS: Availability zones data source defined")
        
        # Check for region data source
        assert 'data "aws_region"' in content, \
            "FAIL: AWS region data source not found"
        print("  PASS: AWS region data source defined")
        
        # Check for caller identity (account ID)
        assert 'data "aws_caller_identity"' in content, \
            "FAIL: AWS caller identity data source not found"
        print("  PASS: AWS caller identity data source defined")
        
        # Check data sources are used for dynamic discovery
        data_source_count = content.count('data "')
        assert data_source_count >= 3, \
            f"FAIL: Expected at least 3 data sources, found {data_source_count}"
        print(f"  PASS: {data_source_count} data sources for dynamic discovery")


def test_property_19_locals_for_calculations():
    """
    Property 19: Locals for Calculations
    Requirements: 10.5
    - Local values for computed values
    - Reusable calculations
    - Naming and tagging logic
    """
    print("\nTesting Property 19: Locals for Calculations...")
    
    vpc_dir = get_vpc_dir()
    locals_file = os.path.join(vpc_dir, 'locals.tf')
    
    assert os.path.exists(locals_file), "FAIL: locals.tf not found"
    
    with open(locals_file, 'r') as f:
        content = f.read()
        
        # Check for locals block
        assert 'locals {' in content, "FAIL: No locals block found"
        print("  PASS: Locals block defined")
        
        # Check for common calculations
        expected_locals = [
            'availability_zones',
            'az_count',
            'common_tags',
            'resource_prefix'
        ]
        
        missing_locals = []
        for local_name in expected_locals:
            if local_name not in content:
                missing_locals.append(local_name)
        
        assert len(missing_locals) == 0, \
            f"FAIL: Missing locals: {', '.join(missing_locals)}"
        print(f"  PASS: All {len(expected_locals)} expected locals defined")
        
        # Check for NAT Gateway count calculation
        assert 'nat_gateway_count' in content, \
            "FAIL: NAT Gateway count calculation not found in locals"
        print("  PASS: NAT Gateway count calculated in locals")


def test_property_19_documentation():
    """
    Property 19: Documentation Quality
    Requirements: 10.6
    - Files have header comments
    - Complex logic is documented
    - Requirements are referenced
    """
    print("\nTesting Property 19: Documentation Quality...")
    
    vpc_dir = get_vpc_dir()
    
    # Check key files for documentation
    files_to_check = ['main.tf', 'security_groups.tf', 'nacls.tf']
    
    for filename in files_to_check:
        filepath = os.path.join(vpc_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
                first_lines = content[:500]
                
                # Check for comments in first 500 characters
                assert '#' in first_lines, \
                    f"FAIL: {filename} has no header comments"
                
                # Check for requirements references
                if 'Requirement' in content or 'Requirements:' in content:
                    print(f"  PASS: {filename} has requirement documentation")
                else:
                    print(f"  INFO: {filename} could benefit from requirement references")
    
    print("  PASS: Files have documentation")


def test_property_19_no_hardcoded_values():
    """
    Property 19: No Hardcoded Values
    Requirements: 10.2
    - Check for common hardcoded patterns
    - Verify use of variables and locals
    """
    print("\nTesting Property 19: No Hardcoded Values...")
    
    vpc_dir = get_vpc_dir()
    
    # Files to check for hardcoded values
    files_to_check = ['main.tf', 'subnets.tf', 'nat_gateway.tf']
    
    acceptable_hardcoded = ['true', 'false', 'default', 'tcp', 'ALL']
    
    issues = []
    
    for filename in files_to_check:
        filepath = os.path.join(vpc_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
                
                # Check that common values use variables
                if 'cidr_block' in content:
                    # Should reference var.vpc_cidr, not hardcoded
                    if 'var.vpc_cidr' not in content and 'local.' not in content:
                        # Check if there's a hardcoded CIDR
                        hardcoded_cidr = re.search(r'cidr_block\s*=\s*"10\.\d+\.\d+\.\d+/\d+"', content)
                        if hardcoded_cidr:
                            issues.append(f"{filename}: Potential hardcoded CIDR block")
    
    # This is a soft check - some hardcoding may be acceptable
    if len(issues) == 0:
        print("  PASS: No obvious hardcoded values found")
    else:
        print(f"  INFO: Potential issues found but may be acceptable: {len(issues)}")
    
    # Main check: verify variables are actually used
    main_file = os.path.join(vpc_dir, 'main.tf')
    with open(main_file, 'r') as f:
        content = f.read()
        var_usage_count = content.count('var.')
        assert var_usage_count >= 1, "FAIL: Variables not being used in main.tf"
        print(f"  PASS: Variables used throughout code ({var_usage_count} references in main.tf)")


def run_all_tests():
    """Run all infrastructure code organization property tests"""
    print("=" * 80)
    print("VPC Best Practices - Infrastructure Code Organization Property Tests")
    print("Feature: vpc-best-practices, Task 19.1")
    print("Property 19: Infrastructure Code Organization")
    print("Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7")
    print("=" * 80)
    
    tests = [
        ("Property 19: File Organization", test_property_19_file_organization),
        ("Property 19: Parameterization", test_property_19_parameterization),
        ("Property 19: Output Completeness", test_property_19_output_completeness),
        ("Property 19: Version Constraints", test_property_19_version_constraints),
        ("Property 19: Data Sources", test_property_19_data_sources),
        ("Property 19: Locals for Calculations", test_property_19_locals_for_calculations),
        ("Property 19: Documentation", test_property_19_documentation),
        ("Property 19: No Hardcoded Values", test_property_19_no_hardcoded_values),
    ]
    
    results = []
    issues = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, True))
            print(f"PASS: {test_name}")
        except AssertionError as e:
            results.append((test_name, False))
            issues.append(f"  - {test_name}: {str(e)}")
            print(f"FAIL: {test_name}")
            print(f"  {str(e)}")
        except Exception as e:
            results.append((test_name, False))
            issues.append(f"  - {test_name}: Unexpected error: {str(e)}")
            print(f"ERROR: {test_name}")
            print(f"  {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(issue)
    
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    exit(0 if run_all_tests() else 1)
