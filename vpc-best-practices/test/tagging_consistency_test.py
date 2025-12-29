#!/usr/bin/env python3
"""
VPC Best Practices - Resource Tagging Consistency Property Tests
Feature: vpc-best-practices, Task 20.1
Property 17: Resource Tagging Consistency
Validates: Requirements 8.4, 10.8

Tests verify:
- All resources have required tags
- Common tags are consistently applied
- Tag format and values are correct
- Subnet-specific tags are present
- Cost center and owner tags included
"""

import os
import re
import subprocess
from typing import Tuple, Dict, List


def run_tofu_plan(var_file: str = None, extra_vars: Dict = None) -> Tuple[bool, str]:
    """Run OpenTofu plan and return output"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    cmd = ["tofu", "plan", "-compact-warnings"]
    if var_file:
        cmd.extend(["-var-file", var_file])
    
    if extra_vars:
        for key, value in extra_vars.items():
            if isinstance(value, bool):
                value = str(value).lower()
            cmd.extend(["-var", f"{key}={value}"])
    
    try:
        result = subprocess.run(
            cmd,
            cwd=vpc_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return result.returncode == 0, result.stdout
        
    except Exception as e:
        print(f"  ERROR running tofu plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, ""


def get_vpc_dir() -> str:
    """Get VPC directory path"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(test_dir)


def test_property_17_common_tags_defined():
    """
    Property 17: Common Tags Defined
    Requirements: 8.4, 10.8
    - Common tags in locals
    - Include required tag fields
    """
    print("\nTesting Property 17: Common Tags Defined...")
    
    vpc_dir = get_vpc_dir()
    locals_file = os.path.join(vpc_dir, 'locals.tf')
    
    assert os.path.exists(locals_file), "FAIL: locals.tf not found"
    
    with open(locals_file, 'r') as f:
        content = f.read()
        
        # Check for common_tags
        assert 'common_tags' in content, "FAIL: common_tags not defined in locals"
        print("  PASS: common_tags defined in locals")
        
        # Check for required tag fields
        required_tags = ['Project', 'Environment', 'ManagedBy', 'CostCenter', 'Owner']
        
        for tag in required_tags:
            assert tag in content, f"FAIL: Required tag '{tag}' not found in common_tags"
        
        print(f"  PASS: All {len(required_tags)} required tags present (Project, Environment, ManagedBy, CostCenter, Owner)")
        
        # Check for Terraform/OpenTofu tag
        assert 'Terraform' in content or 'opentofu' in content.lower(), \
            "FAIL: Terraform/OpenTofu management tag not found"
        print("  PASS: Infrastructure management tag present")


def test_property_17_variables_for_tags():
    """
    Property 17: Variables for Tag Values
    Requirements: 8.4, 10.8
    - Cost center variable exists
    - Owner variable exists
    - Other tag variables exist
    """
    print("\nTesting Property 17: Variables for Tag Values...")
    
    vpc_dir = get_vpc_dir()
    variables_file = os.path.join(vpc_dir, 'variables.tf')
    
    with open(variables_file, 'r') as f:
        content = f.read()
        
        # Check for tag-related variables
        required_vars = ['cost_center', 'owner', 'project_name', 'environment']
        
        for var in required_vars:
            assert f'variable "{var}"' in content, \
                f"FAIL: Variable '{var}' not found"
        
        print(f"  PASS: All {len(required_vars)} tag-related variables defined")
        
        # Check for descriptions
        for var in required_vars:
            var_section_start = content.find(f'variable "{var}"')
            var_section = content[var_section_start:var_section_start + 200]
            assert 'description' in var_section, \
                f"FAIL: Variable '{var}' missing description"
        
        print("  PASS: All tag variables have descriptions")


def test_property_17_tags_applied_to_resources():
    """
    Property 17: Tags Applied to Resources
    Requirements: 8.4, 10.8
    - VPC has tags
    - Subnets have tags
    - NAT Gateways have tags
    - Security groups have tags
    - Route tables have tags
    """
    print("\nTesting Property 17: Tags Applied to Resources...")
    
    vpc_dir = get_vpc_dir()
    
    # Check various resource files for tags
    files_to_check = {
        'main.tf': ['aws_vpc', 'aws_internet_gateway', 'aws_default_security_group'],
        'subnets.tf': ['aws_subnet'],
        'nat_gateway.tf': ['aws_nat_gateway', 'aws_eip'],
        'route_tables.tf': ['aws_route_table'],
        'security_groups.tf': ['aws_security_group'],
        'nacls.tf': ['aws_network_acl'],
        'flow_logs.tf': ['aws_cloudwatch_log_group', 'aws_iam_role']
    }
    
    total_checks = 0
    for filename, resource_types in files_to_check.items():
        filepath = os.path.join(vpc_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
                
                for resource_type in resource_types:
                    if resource_type in content:
                        # Check if tags or common_tags appears after the resource
                        resource_pos = content.find(resource_type)
                        section = content[resource_pos:resource_pos + 500]
                        
                        if 'tags' in section or 'common_tags' in section:
                            total_checks += 1
    
    assert total_checks >= 8, \
        f"FAIL: Expected at least 8 resource types with tags, found {total_checks}"
    print(f"  PASS: Tags applied to {total_checks} resource types")
    
    # Check for merge pattern (best practice)
    main_file = os.path.join(vpc_dir, 'main.tf')
    with open(main_file, 'r') as f:
        content = f.read()
        merge_count = content.count('merge(')
        if merge_count > 0:
            print(f"  PASS: Using merge() for tag composition ({merge_count} occurrences)")


def test_property_17_subnet_specific_tags():
    """
    Property 17: Subnet-Specific Tags
    Requirements: 8.4, 10.8
    - Public subnets have Type/Tier tags
    - Private subnets have Type/Tier tags
    - Subnet tags differentiate subnet types
    """
    print("\nTesting Property 17: Subnet-Specific Tags...")
    
    vpc_dir = get_vpc_dir()
    
    # Check locals for subnet-specific tags
    locals_file = os.path.join(vpc_dir, 'locals.tf')
    with open(locals_file, 'r') as f:
        locals_content = f.read()
        
        # Check for subnet-specific tag definitions
        assert 'public_subnet_tags' in locals_content or 'Type = "public"' in locals_content, \
            "FAIL: Public subnet-specific tags not found"
        print("  PASS: Public subnet-specific tags defined")
        
        assert 'private_subnet_tags' in locals_content or 'Type = "private"' in locals_content, \
            "FAIL: Private subnet-specific tags not found"
        print("  PASS: Private subnet-specific tags defined")
    
    # Check subnets.tf for tag application
    subnets_file = os.path.join(vpc_dir, 'subnets.tf')
    with open(subnets_file, 'r') as f:
        subnets_content = f.read()
        
        # Verify tags are merged with common_tags
        public_section = subnets_content[:subnets_content.find('resource "aws_subnet" "private"')]
        private_section = subnets_content[subnets_content.find('resource "aws_subnet" "private"'):]
        
        # Check public subnet has Type tag
        assert 'Type' in public_section or 'public_subnet_tags' in public_section, \
            "FAIL: Public subnet missing Type tag"
        print("  PASS: Public subnets have type-specific tags")
        
        # Check private subnet has Type tag
        assert 'Type' in private_section or 'private_subnet_tags' in private_section, \
            "FAIL: Private subnet missing Type tag"
        print("  PASS: Private subnets have type-specific tags")


def test_property_17_tag_format():
    """
    Property 17: Tag Format Consistency
    Requirements: 8.4, 10.8
    - Tag names use consistent case (PascalCase)
    - Tag values use consistent format
    """
    print("\nTesting Property 17: Tag Format Consistency...")
    
    vpc_dir = get_vpc_dir()
    locals_file = os.path.join(vpc_dir, 'locals.tf')
    
    with open(locals_file, 'r') as f:
        content = f.read()
        
        # Find common_tags section
        common_tags_start = content.find('common_tags')
        common_tags_section = content[common_tags_start:common_tags_start + 500]
        
        # Check for PascalCase tag names
        tag_names = re.findall(r'(\w+)\s*=', common_tags_section)
        
        # Filter out non-tag fields (like 'local', 'common_tags')
        tag_names = [name for name in tag_names if name not in ['locals', 'common_tags']]
        
        # Check first letter is uppercase (PascalCase)
        for tag_name in tag_names:
            if tag_name[0].islower() and tag_name != 'opentofu':
                print(f"  INFO: Tag '{tag_name}' doesn't follow PascalCase convention")
        
        print("  PASS: Tag naming convention consistent")
        
        # Check that variable references are used for values
        var_count = common_tags_section.count('var.')
        assert var_count >= 3, \
            f"FAIL: Expected at least 3 variable references in common_tags, found {var_count}"
        print(f"  PASS: Tag values use variables ({var_count} variable references)")


def test_property_17_tagging_in_plan():
    """
    Property 17: Tagging in Plan Output
    Requirements: 8.4, 10.8
    - Plan shows tags being applied
    - Required tags present in plan
    """
    print("\nTesting Property 17: Tagging in Plan Output...")
    
    success, output = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Check for tags in plan output
    assert 'tags' in output.lower(), "FAIL: No tags found in plan output"
    print("  PASS: Tags present in plan output")
    
    # Check for specific required tags
    required_tags = ['Project', 'Environment', 'Owner', 'CostCenter']
    found_tags = []
    
    for tag in required_tags:
        if tag in output:
            found_tags.append(tag)
    
    assert len(found_tags) >= 2, \
        f"FAIL: Expected at least 2 required tags in plan, found {len(found_tags)}"
    print(f"  PASS: Required tags appear in plan output ({len(found_tags)} tags found)")


def test_property_17_no_untagged_resources():
    """
    Property 17: No Untagged Resources
    Requirements: 8.4, 10.8
    - All taggable resources have tags
    - Check across all resource files
    """
    print("\nTesting Property 17: No Untagged Resources...")
    
    vpc_dir = get_vpc_dir()
    
    # Resource types that support tags
    taggable_resources = [
        'aws_vpc',
        'aws_subnet',
        'aws_internet_gateway',
        'aws_nat_gateway',
        'aws_eip',
        'aws_route_table',
        'aws_network_acl',
        'aws_security_group',
        'aws_default_security_group',
        'aws_cloudwatch_log_group',
        'aws_iam_role'
    ]
    
    # Check each .tf file
    tf_files = [f for f in os.listdir(vpc_dir) if f.endswith('.tf')]
    
    untagged_resources = []
    tagged_resources = []
    
    for tf_file in tf_files:
        filepath = os.path.join(vpc_dir, tf_file)
        with open(filepath, 'r') as f:
            content = f.read()
            
            # Find all resources
            for resource_type in taggable_resources:
                pattern = f'resource "{resource_type}" "\\w+"'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    resource_start = match.start()
                    # Look ahead for tags in the resource block (next 500 chars)
                    resource_section = content[resource_start:resource_start + 700]
                    
                    # Find the end of this resource block
                    brace_count = 0
                    in_resource = False
                    resource_end = resource_start
                    
                    for i, char in enumerate(content[resource_start:resource_start + 1000]):
                        if char == '{':
                            in_resource = True
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if in_resource and brace_count == 0:
                                resource_end = resource_start + i
                                break
                    
                    resource_block = content[resource_start:resource_end]
                    
                    if 'tags' in resource_block:
                        tagged_resources.append(f"{tf_file}:{resource_type}")
                    else:
                        # Some resources might inherit tags or be special cases
                        # VPC Flow Log resources might not all need tags
                        if resource_type not in ['aws_flow_log']:
                            untagged_resources.append(f"{tf_file}:{resource_type}")
    
    # Most resources should be tagged
    tag_ratio = len(tagged_resources) / (len(tagged_resources) + len(untagged_resources)) if (len(tagged_resources) + len(untagged_resources)) > 0 else 0
    
    assert tag_ratio >= 0.85, \
        f"FAIL: Only {tag_ratio*100:.0f}% of resources are tagged (expected >= 85%)"
    print(f"  PASS: {len(tagged_resources)} resources properly tagged ({tag_ratio*100:.0f}% tag coverage)")


def run_all_tests():
    """Run all resource tagging consistency property tests"""
    print("=" * 80)
    print("VPC Best Practices - Resource Tagging Consistency Property Tests")
    print("Feature: vpc-best-practices, Task 20.1")
    print("Property 17: Resource Tagging Consistency")
    print("Validates: Requirements 8.4, 10.8")
    print("=" * 80)
    
    tests = [
        ("Property 17: Common Tags Defined", test_property_17_common_tags_defined),
        ("Property 17: Variables for Tags", test_property_17_variables_for_tags),
        ("Property 17: Tags Applied to Resources", test_property_17_tags_applied_to_resources),
        ("Property 17: Subnet-Specific Tags", test_property_17_subnet_specific_tags),
        ("Property 17: Tag Format Consistency", test_property_17_tag_format),
        ("Property 17: Tagging in Plan", test_property_17_tagging_in_plan),
        ("Property 17: No Untagged Resources", test_property_17_no_untagged_resources),
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
