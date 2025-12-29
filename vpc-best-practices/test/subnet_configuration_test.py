#!/usr/bin/env python3
"""
Property-based tests for subnet distribution and configuration
Feature: vpc-best-practices
Property 2: Multi-AZ Subnet Distribution
Property 3: Public Subnet Configuration Compliance
Property 4: Private Subnet Configuration Compliance
Tasks: 5.1, 5.2, 5.3
Validates: Requirements 1.2, 2.1-2.8
"""

import os
import re
import sys
import subprocess
import json
from typing import Tuple, List, Dict
import ipaddress

def parse_subnet_block(block: str, index: int) -> Dict:
    """Parse a subnet block from tofu plan output"""
    cidr_match = re.search(r'cidr_block\s*=\s*"([^"]+)"', block)
    az_match = re.search(r'availability_zone\s*=\s*"([^"]+)"', block)
    map_public_match = re.search(r'map_public_ip_on_launch\s*=\s*(true|false)', block)
    
    return {
        'index': index,
        'cidr': cidr_match.group(1) if cidr_match else None,
        'az': az_match.group(1) if az_match else None,
        'map_public_ip': map_public_match.group(1) == 'true' if map_public_match else None
    }

def read_subnets_tf() -> str:
    """Read the subnets.tf file"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    subnets_tf_path = os.path.join(os.path.dirname(test_dir), "subnets.tf")
    
    try:
        with open(subnets_tf_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

def run_tofu_plan() -> Tuple[bool, Dict]:
    """Run OpenTofu plan and parse subnet information"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    try:
        result = subprocess.run(
            ["tofu", "plan", "-compact-warnings"],
            cwd=vpc_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse output for subnet information
        output = result.stdout
        
        public_subnets = []
        private_subnets = []
        
        # Split output into lines and look for subnet declarations
        lines = output.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for subnet resource declaration
            match = re.search(r'# aws_subnet\.(public|private)\[(\d+)\]', line)
            if match:
                subnet_type = match.group(1)
                subnet_index = int(match.group(2))
                
                # Collect the next ~30 lines that contain subnet configuration
                block_lines = [line]  # Start with the declaration line
                j = i + 1
                lines_collected = 1
                while j < len(lines) and lines_collected < 30:
                    current_line = lines[j]
                    # Stop if we hit another resource declaration (but not within tags block)
                    if current_line.strip().startswith('# aws_') and not 'aws_subnet' in current_line:
                        break
                    block_lines.append(current_line)
                    j += 1
                    lines_collected += 1
                
                subnet_block = '\n'.join(block_lines)
                subnet_info = parse_subnet_block(subnet_block, subnet_index)
                
                if subnet_type == 'public':
                    public_subnets.append(subnet_info)
                else:
                    private_subnets.append(subnet_info)
            
            i += 1  # Always increment by 1 to check every line
        
        return result.returncode == 0, {
            'public': sorted(public_subnets, key=lambda x: x['index']),
            'private': sorted(private_subnets, key=lambda x: x['index'])
        }
    except Exception as e:
        print(f"  ERROR running tofu plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}

def test_subnet_resource_definition() -> Tuple[bool, List[str]]:
    """
    Test that subnet resources are properly defined
    """
    print("\nTesting subnet resource definitions...")
    issues = []
    
    subnets_content = read_subnets_tf()
    if not subnets_content:
        issues.append("subnets.tf not found")
        print("  FAIL: subnets.tf not found")
        return False, issues
    
    # Check for public subnet resource
    if 'resource "aws_subnet" "public"' not in subnets_content:
        issues.append("Public subnet resource not defined")
        print("  FAIL: Public subnet resource not defined")
        return False, issues
    
    print("  PASS: Public subnet resource defined")
    
    # Check for private subnet resource
    if 'resource "aws_subnet" "private"' not in subnets_content:
        issues.append("Private subnet resource not defined")
        print("  FAIL: Private subnet resource not defined")
        return False, issues
    
    print("  PASS: Private subnet resource defined")
    
    # Check for count meta-argument
    if 'count = local.az_count' in subnets_content:
        print("  PASS: Subnets use count = local.az_count for multi-AZ")
    else:
        issues.append("Subnets don't use count = local.az_count")
        print("  FAIL: Subnets should use count = local.az_count")
        return False, issues
    
    return len(issues) == 0, issues

def test_multi_az_subnet_distribution() -> Tuple[bool, List[str]]:
    """
    Property 2: Multi-AZ Subnet Distribution
    For any VPC deployment with N availability zones, there should be exactly
    N public subnets and N private subnets, with each subnet in a different AZ
    """
    print("\nTesting Property 2: Multi-AZ Subnet Distribution...")
    issues = []
    
    success, subnets = run_tofu_plan()
    if not success:
        issues.append("Failed to run tofu plan")
        print("  FAIL: Could not run tofu plan")
        return False, issues
    
    if not subnets or 'public' not in subnets or 'private' not in subnets:
        issues.append("Could not parse subnet information")
        print("  FAIL: Could not parse subnet information")
        return False, issues
    
    public_count = len(subnets['public'])
    private_count = len(subnets['private'])
    
    print(f"  Found {public_count} public subnets")
    print(f"  Found {private_count} private subnets")
    
    # Verify equal number of public and private subnets
    if public_count != private_count:
        issues.append(f"Unequal subnet counts: {public_count} public, {private_count} private")
        print(f"  FAIL: Should have equal number of public and private subnets")
        return False, issues
    
    print(f"  PASS: Equal number of public and private subnets ({public_count})")
    
    # Verify minimum 2 AZs for HA (Requirement 1.2)
    if public_count < 2:
        issues.append(f"Insufficient AZs: only {public_count} subnets")
        print(f"  FAIL: Should have at least 2 subnets per type for HA")
        return False, issues
    
    print(f"  PASS: Minimum 2 AZs requirement met")
    
    # Verify each subnet is in a different AZ
    public_azs = [s['az'] for s in subnets['public']]
    private_azs = [s['az'] for s in subnets['private']]
    
    if len(public_azs) != len(set(public_azs)):
        issues.append("Public subnets have duplicate AZs")
        print("  FAIL: Each public subnet should be in a different AZ")
        return False, issues
    
    print("  PASS: Each public subnet in different AZ")
    
    if len(private_azs) != len(set(private_azs)):
        issues.append("Private subnets have duplicate AZs")
        print("  FAIL: Each private subnet should be in a different AZ")
        return False, issues
    
    print("  PASS: Each private subnet in different AZ")
    
    # Verify public and private subnets share the same AZs
    if set(public_azs) != set(private_azs):
        issues.append("Public and private subnets not in matching AZs")
        print("  FAIL: Public and private subnets should be in the same AZs")
        return False, issues
    
    print("  PASS: Public and private subnets in matching AZs")
    
    return len(issues) == 0, issues

def test_subnet_cidr_no_overlap() -> Tuple[bool, List[str]]:
    """
    Verify subnet CIDRs don't overlap
    Property 2: Multi-AZ Subnet Distribution
    """
    print("\nTesting subnet CIDR non-overlap...")
    issues = []
    
    success, subnets = run_tofu_plan()
    if not success or not subnets:
        issues.append("Could not get subnet information")
        print("  FAIL: Could not get subnet information")
        return False, issues
    
    # Collect all CIDRs
    all_cidrs = []
    for subnet in subnets.get('public', []):
        if subnet['cidr']:
            all_cidrs.append(subnet['cidr'])
    
    for subnet in subnets.get('private', []):
        if subnet['cidr']:
            all_cidrs.append(subnet['cidr'])
    
    # Check for duplicates
    if len(all_cidrs) != len(set(all_cidrs)):
        issues.append("Duplicate CIDR blocks found")
        print("  FAIL: All subnet CIDRs should be unique")
        return False, issues
    
    print(f"  PASS: All {len(all_cidrs)} subnet CIDRs are unique")
    
    # Check for overlaps using ipaddress module
    networks = [ipaddress.ip_network(cidr) for cidr in all_cidrs]
    
    for i, net1 in enumerate(networks):
        for j, net2 in enumerate(networks):
            if i != j and net1.overlaps(net2):
                issues.append(f"CIDR overlap: {all_cidrs[i]} and {all_cidrs[j]}")
                print(f"  FAIL: CIDR blocks overlap: {all_cidrs[i]} and {all_cidrs[j]}")
                return False, issues
    
    print("  PASS: No CIDR overlaps detected")
    
    return len(issues) == 0, issues

def test_public_subnet_configuration() -> Tuple[bool, List[str]]:
    """
    Property 3: Public Subnet Configuration Compliance
    For any public subnet, it should have map_public_ip_on_launch enabled
    Requirements: 2.4, 2.6
    """
    print("\nTesting Property 3: Public Subnet Configuration Compliance...")
    issues = []
    
    subnets_content = read_subnets_tf()
    if not subnets_content:
        issues.append("subnets.tf not found")
        print("  FAIL: subnets.tf not found")
        return False, issues
    
    # Extract public subnet block
    public_match = re.search(
        r'resource "aws_subnet" "public".*?\{(.*?)^\}',
        subnets_content,
        re.MULTILINE | re.DOTALL
    )
    
    if not public_match:
        issues.append("Could not parse public subnet resource")
        print("  FAIL: Could not parse public subnet resource")
        return False, issues
    
    public_block = public_match.group(1)
    
    # Check map_public_ip_on_launch = true (Requirement 2.6)
    if 'map_public_ip_on_launch = true' in public_block:
        print("  PASS: map_public_ip_on_launch = true for public subnets")
    else:
        issues.append("Public subnets don't have map_public_ip_on_launch = true")
        print("  FAIL: Public subnets must have map_public_ip_on_launch = true")
        return False, issues
    
    # Check CIDR from variable
    if 'cidr_block' in public_block and 'var.public_subnet_cidrs' in public_block:
        print("  PASS: Public subnets use var.public_subnet_cidrs")
    else:
        issues.append("Public subnets don't use var.public_subnet_cidrs")
        print("  FAIL: Should use var.public_subnet_cidrs")
        return False, issues
    
    # Check availability zone assignment
    if 'availability_zone' in public_block and 'local.availability_zones' in public_block:
        print("  PASS: Public subnets distributed across AZs")
    else:
        print("  WARN: Should use local.availability_zones for AZ distribution")
    
    # Check for tags (Requirement 2.8)
    if 'tags' in public_block:
        print("  PASS: Public subnets have tags")
    else:
        issues.append("Public subnets missing tags")
        print("  FAIL: Public subnets should have tags")
        return False, issues
    
    # Check for public subnet specific tags
    if 'local.public_subnet_tags' in public_block:
        print("  PASS: Uses local.public_subnet_tags")
    else:
        print("  WARN: Should use local.public_subnet_tags")
    
    # Verify actual configuration from plan
    success, subnets = run_tofu_plan()
    if success and 'public' in subnets:
        all_public_correct = all(s['map_public_ip'] == True for s in subnets['public'] if s['map_public_ip'] is not None)
        if all_public_correct:
            print("  PASS: All public subnets have map_public_ip_on_launch enabled")
        else:
            issues.append("Not all public subnets have map_public_ip_on_launch enabled")
            print("  FAIL: All public subnets must have map_public_ip_on_launch enabled")
            return False, issues
    
    return len(issues) == 0, issues

def test_private_subnet_configuration() -> Tuple[bool, List[str]]:
    """
    Property 4: Private Subnet Configuration Compliance
    For any private subnet, it should NOT have map_public_ip_on_launch enabled
    Requirements: 2.5, 2.7
    """
    print("\nTesting Property 4: Private Subnet Configuration Compliance...")
    issues = []
    
    subnets_content = read_subnets_tf()
    if not subnets_content:
        issues.append("subnets.tf not found")
        print("  FAIL: subnets.tf not found")
        return False, issues
    
    # Extract private subnet block
    private_match = re.search(
        r'resource "aws_subnet" "private".*?\{(.*?)^\}',
        subnets_content,
        re.MULTILINE | re.DOTALL
    )
    
    if not private_match:
        issues.append("Could not parse private subnet resource")
        print("  FAIL: Could not parse private subnet resource")
        return False, issues
    
    private_block = private_match.group(1)
    
    # Check map_public_ip_on_launch = false (Requirement 2.7)
    if 'map_public_ip_on_launch = false' in private_block:
        print("  PASS: map_public_ip_on_launch = false for private subnets")
    else:
        issues.append("Private subnets don't have map_public_ip_on_launch = false")
        print("  FAIL: Private subnets must have map_public_ip_on_launch = false")
        return False, issues
    
    # Check CIDR from variable
    if 'cidr_block' in private_block and 'var.private_subnet_cidrs' in private_block:
        print("  PASS: Private subnets use var.private_subnet_cidrs")
    else:
        issues.append("Private subnets don't use var.private_subnet_cidrs")
        print("  FAIL: Should use var.private_subnet_cidrs")
        return False, issues
    
    # Check availability zone assignment
    if 'availability_zone' in private_block and 'local.availability_zones' in private_block:
        print("  PASS: Private subnets distributed across AZs")
    else:
        print("  WARN: Should use local.availability_zones for AZ distribution")
    
    # Check for tags (Requirement 2.8)
    if 'tags' in private_block:
        print("  PASS: Private subnets have tags")
    else:
        issues.append("Private subnets missing tags")
        print("  FAIL: Private subnets should have tags")
        return False, issues
    
    # Check for private subnet specific tags
    if 'local.private_subnet_tags' in private_block:
        print("  PASS: Uses local.private_subnet_tags")
    else:
        print("  WARN: Should use local.private_subnet_tags")
    
    # Verify actual configuration from plan
    success, subnets = run_tofu_plan()
    if success and 'private' in subnets:
        all_private_correct = all(s['map_public_ip'] == False for s in subnets['private'] if s['map_public_ip'] is not None)
        if all_private_correct:
            print("  PASS: All private subnets have map_public_ip_on_launch disabled")
        else:
            issues.append("Not all private subnets have map_public_ip_on_launch disabled")
            print("  FAIL: All private subnets must have map_public_ip_on_launch disabled")
            return False, issues
    
    return len(issues) == 0, issues

def test_subnet_cidr_sizing() -> Tuple[bool, List[str]]:
    """
    Test that subnets use /24 CIDR blocks as per best practices
    Requirement 2.3: Each subnet SHALL use a /24 CIDR block
    """
    print("\nTesting subnet CIDR sizing (Requirement 2.3)...")
    issues = []
    
    success, subnets = run_tofu_plan()
    if not success or not subnets:
        issues.append("Could not get subnet information")
        print("  FAIL: Could not get subnet information")
        return False, issues
    
    all_subnets = subnets.get('public', []) + subnets.get('private', [])
    
    for subnet in all_subnets:
        if subnet['cidr']:
            network = ipaddress.ip_network(subnet['cidr'])
            if network.prefixlen != 24:
                issues.append(f"Subnet {subnet['cidr']} is not /24 (it's /{network.prefixlen})")
                print(f"  FAIL: Subnet {subnet['cidr']} should be /24")
                return False, issues
    
    print(f"  PASS: All {len(all_subnets)} subnets use /24 CIDR blocks")
    
    return len(issues) == 0, issues

def run_all_tests():
    """Run all subnet configuration tests"""
    print("=" * 80)
    print("VPC Best Practices - Subnet Configuration Property Tests")
    print("Feature: vpc-best-practices, Tasks 5.1, 5.2, 5.3")
    print("Property 2: Multi-AZ Subnet Distribution")
    print("Property 3: Public Subnet Configuration Compliance")
    print("Property 4: Private Subnet Configuration Compliance")
    print("Validates: Requirements 1.2, 2.1-2.8")
    print("=" * 80)
    
    all_tests = [
        ("Subnet Resource Definition", test_subnet_resource_definition),
        ("Property 2: Multi-AZ Subnet Distribution", test_multi_az_subnet_distribution),
        ("Subnet CIDR Non-Overlap", test_subnet_cidr_no_overlap),
        ("Subnet CIDR Sizing (/24)", test_subnet_cidr_sizing),
        ("Property 3: Public Subnet Configuration", test_public_subnet_configuration),
        ("Property 4: Private Subnet Configuration", test_private_subnet_configuration),
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
            import traceback
            traceback.print_exc()
    
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
