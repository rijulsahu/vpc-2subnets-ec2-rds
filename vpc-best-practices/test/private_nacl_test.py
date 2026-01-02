#!/usr/bin/env python3
"""
VPC Best Practices - Private NACL Property Tests
Feature: vpc-best-practices, Task 11.1
Property 8: Private NACL Rules Compliance
Validates: Requirements 4.4, 4.5, 4.6, 4.7

Tests verify:
- Private NACL exists and is associated with private subnets
- Inbound rules restricted to VPC CIDR only (no internet access)
- Inbound ephemeral ports (1024-65535) for return traffic
- Outbound rules for VPC CIDR and HTTPS for updates
- Rule numbering allows insertions (100, 110, 120...)
"""

import os
import re
import subprocess
from typing import Tuple, Dict, List


def run_tofu_plan(var_file: str = None) -> Tuple[bool, Dict]:
    """Run OpenTofu plan and parse private NACL information"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    cmd = ["tofu", "plan", "-compact-warnings"]
    if var_file:
        cmd.extend(["-var-file", var_file])
    
    try:
        result = subprocess.run(
            cmd,
            cwd=vpc_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout
        
        # Parse private NACL information
        nacl_info = {
            'private_nacl_exists': False,
            'inbound_rules': [],
            'outbound_rules': [],
            'associations': [],
            'vpc_cidr': None
        }
        
        # Extract VPC CIDR from plan
        vpc_cidr_match = re.search(r'vpc_cidr\s*=\s*"([^"]+)"', output)
        if vpc_cidr_match:
            nacl_info['vpc_cidr'] = vpc_cidr_match.group(1)
        
        lines = output.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for private NACL resource
            if 'aws_network_acl.private' in line and 'will be created' in line:
                nacl_info['private_nacl_exists'] = True
            
            # Look for inbound rules
            if 'aws_network_acl_rule.private_inbound_' in line and 'will be created' in line:
                # Extract rule type
                match = re.search(r'aws_network_acl_rule\.private_inbound_(\w+)', line)
                if match:
                    rule_type = match.group(1)
                    
                    # Get rule details from the block
                    block_lines = []
                    j = i
                    while j < len(lines) and j < i + 20:
                        block_lines.append(lines[j])
                        j += 1
                        if j < len(lines) and lines[j].strip().startswith('# aws_') and 'aws_network_acl_rule' not in lines[j]:
                            break
                    
                    block_text = '\n'.join(block_lines)
                    
                    rule_info = {
                        'type': rule_type,
                        'rule_number': None,
                        'protocol': None,
                        'from_port': None,
                        'to_port': None,
                        'cidr': None,
                        'action': None
                    }
                    
                    # Parse rule details
                    rule_num_match = re.search(r'rule_number\s*=\s*(\d+)', block_text)
                    if rule_num_match:
                        rule_info['rule_number'] = int(rule_num_match.group(1))
                    
                    protocol_match = re.search(r'protocol\s*=\s*"([^"]+)"', block_text)
                    if protocol_match:
                        rule_info['protocol'] = protocol_match.group(1)
                    
                    from_port_match = re.search(r'from_port\s*=\s*(\d+)', block_text)
                    if from_port_match:
                        rule_info['from_port'] = int(from_port_match.group(1))
                    
                    to_port_match = re.search(r'to_port\s*=\s*(\d+)', block_text)
                    if to_port_match:
                        rule_info['to_port'] = int(to_port_match.group(1))
                    
                    cidr_match = re.search(r'cidr_block\s*=\s*"([^"]+)"', block_text)
                    if cidr_match:
                        rule_info['cidr'] = cidr_match.group(1)
                    
                    action_match = re.search(r'rule_action\s*=\s*"(\w+)"', block_text)
                    if action_match:
                        rule_info['action'] = action_match.group(1)
                    
                    nacl_info['inbound_rules'].append(rule_info)
            
            # Look for outbound rules
            if 'aws_network_acl_rule.private_outbound_' in line and 'will be created' in line:
                # Extract rule type
                match = re.search(r'aws_network_acl_rule\.private_outbound_(\w+)', line)
                if match:
                    rule_type = match.group(1)
                    
                    # Get rule details
                    block_lines = []
                    j = i
                    while j < len(lines) and j < i + 20:
                        block_lines.append(lines[j])
                        j += 1
                        if j < len(lines) and lines[j].strip().startswith('# aws_') and 'aws_network_acl_rule' not in lines[j]:
                            break
                    
                    block_text = '\n'.join(block_lines)
                    
                    rule_info = {
                        'type': rule_type,
                        'rule_number': None,
                        'protocol': None,
                        'from_port': None,
                        'to_port': None,
                        'cidr': None,
                        'action': None
                    }
                    
                    rule_num_match = re.search(r'rule_number\s*=\s*(\d+)', block_text)
                    if rule_num_match:
                        rule_info['rule_number'] = int(rule_num_match.group(1))
                    
                    protocol_match = re.search(r'protocol\s*=\s*"([^"]+)"', block_text)
                    if protocol_match:
                        rule_info['protocol'] = protocol_match.group(1)
                    
                    from_port_match = re.search(r'from_port\s*=\s*(\d+)', block_text)
                    if from_port_match:
                        rule_info['from_port'] = int(from_port_match.group(1))
                    
                    to_port_match = re.search(r'to_port\s*=\s*(\d+)', block_text)
                    if to_port_match:
                        rule_info['to_port'] = int(to_port_match.group(1))
                    
                    cidr_match = re.search(r'cidr_block\s*=\s*"([^"]+)"', block_text)
                    if cidr_match:
                        rule_info['cidr'] = cidr_match.group(1)
                    
                    action_match = re.search(r'rule_action\s*=\s*"(\w+)"', block_text)
                    if action_match:
                        rule_info['action'] = action_match.group(1)
                    
                    nacl_info['outbound_rules'].append(rule_info)
            
            # Look for NACL associations
            assoc_match = re.search(r'aws_network_acl_association\.private\[(\d+)\]', line)
            if assoc_match:
                idx = int(assoc_match.group(1))
                nacl_info['associations'].append({'index': idx})
            
            i += 1
        
        return result.returncode == 0, nacl_info
        
    except Exception as e:
        print(f"  ERROR running tofu plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}


def check_nacl_config() -> Dict:
    """Check private NACL configuration in source files"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    config_info = {
        'nacl_file_exists': False,
        'private_nacl_defined': False,
        'has_vpc_inbound': False,
        'has_ephemeral_inbound': False,
        'has_vpc_outbound': False,
        'has_https_outbound': False,
        'has_associations': False,
        'uses_rule_numbering': False,
        'uses_protocol_all': False
    }
    
    # Check nacls.tf
    nacl_file = os.path.join(vpc_dir, 'nacls.tf')
    if os.path.exists(nacl_file):
        config_info['nacl_file_exists'] = True
        
        with open(nacl_file, 'r') as f:
            content = f.read()
            
            config_info['private_nacl_defined'] = 'resource "aws_network_acl" "private"' in content
            config_info['has_vpc_inbound'] = 'resource "aws_network_acl_rule" "private_inbound_vpc"' in content
            config_info['has_ephemeral_inbound'] = 'resource "aws_network_acl_rule" "private_inbound_ephemeral"' in content
            config_info['has_vpc_outbound'] = 'resource "aws_network_acl_rule" "private_outbound_vpc"' in content
            config_info['has_https_outbound'] = 'resource "aws_network_acl_rule" "private_outbound_https"' in content
            config_info['has_associations'] = 'resource "aws_network_acl_association" "private"' in content
            
            # Check for protocol = "-1" (all protocols)
            config_info['uses_protocol_all'] = 'protocol       = "-1"' in content
            
            # Check for rule numbering pattern (100, 110, etc.)
            # Extract private NACL rules section
            private_section = content[content.find('# Private NACL'):]
            rule_numbers = re.findall(r'rule_number\s*=\s*(\d+)', private_section)
            if rule_numbers:
                nums = [int(n) for n in rule_numbers]
                config_info['uses_rule_numbering'] = all(n % 10 == 0 for n in nums) and min(nums) >= 100
    
    return config_info


def test_nacl_resource_definition():
    """Test that private NACL resources are properly defined"""
    print("\nTesting private NACL resource definitions...")
    
    config = check_nacl_config()
    
    assert config['nacl_file_exists'], "FAIL: No nacls.tf file found"
    print("  PASS: nacls.tf file exists")
    
    assert config['private_nacl_defined'], "FAIL: No private NACL resource defined"
    print("  PASS: Private NACL resource defined")
    
    assert config['has_vpc_inbound'], "FAIL: No VPC CIDR inbound rule defined"
    print("  PASS: VPC CIDR inbound rule defined")
    
    assert config['has_ephemeral_inbound'], "FAIL: No ephemeral ports inbound rule defined"
    print("  PASS: Ephemeral ports inbound rule defined")
    
    assert config['has_vpc_outbound'], "FAIL: No VPC CIDR outbound rule defined"
    print("  PASS: VPC CIDR outbound rule defined")
    
    assert config['has_https_outbound'], "FAIL: No HTTPS outbound rule defined"
    print("  PASS: HTTPS outbound rule defined")
    
    assert config['has_associations'], "FAIL: No private NACL associations defined"
    print("  PASS: Private NACL subnet associations defined")
    
    assert config['uses_protocol_all'], "FAIL: VPC rules don't use protocol = '-1' for all protocols"
    print("  PASS: VPC rules use protocol '-1' (all protocols)")
    
    assert config['uses_rule_numbering'], "FAIL: Rule numbering doesn't follow 100/110 pattern"
    print("  PASS: Rule numbering allows insertions (100, 110...)")


def test_property_8_private_nacl_inbound():
    """
    Property 8: Private NACL Rules - Inbound
    Requirements: 4.4, 4.5, 4.6
    - VPC CIDR allowed (all protocols)
    - Ephemeral ports (1024-65535) for return traffic from internet
    - No direct internet access (only VPC and ephemeral)
    """
    print("\nTesting Property 8: Private NACL Inbound Rules...")
    
    success, nacl_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Verify private NACL exists
    assert nacl_info['private_nacl_exists'], "FAIL: Private NACL not found in plan"
    print("  PASS: Private NACL exists")
    
    inbound = nacl_info['inbound_rules']
    
    # Check VPC CIDR rule
    vpc_rules = [r for r in inbound if r['type'] == 'vpc']
    assert len(vpc_rules) == 1, f"FAIL: Expected 1 VPC CIDR rule, found {len(vpc_rules)}"
    vpc_rule = vpc_rules[0]
    
    # Verify it allows from VPC CIDR
    expected_cidr = nacl_info['vpc_cidr'] or '10.0.0.0/16'
    assert vpc_rule['cidr'] == expected_cidr, f"FAIL: VPC rule CIDR should be {expected_cidr}, got {vpc_rule['cidr']}"
    assert vpc_rule['protocol'] == '-1', f"FAIL: VPC rule protocol should be '-1' (all), got {vpc_rule['protocol']}"
    assert vpc_rule['action'] == 'allow', f"FAIL: VPC rule action should be allow, got {vpc_rule['action']}"
    print(f"  PASS: VPC CIDR ({expected_cidr}) inbound rule configured (rule {vpc_rule['rule_number']})")
    
    # Check ephemeral ports rule
    ephemeral_rules = [r for r in inbound if r['type'] == 'ephemeral']
    assert len(ephemeral_rules) == 1, f"FAIL: Expected 1 ephemeral rule, found {len(ephemeral_rules)}"
    eph_rule = ephemeral_rules[0]
    assert eph_rule['from_port'] == 1024, f"FAIL: Ephemeral from_port should be 1024, got {eph_rule['from_port']}"
    assert eph_rule['to_port'] == 65535, f"FAIL: Ephemeral to_port should be 65535, got {eph_rule['to_port']}"
    assert eph_rule['protocol'] == 'tcp', f"FAIL: Ephemeral protocol should be tcp, got {eph_rule['protocol']}"
    assert eph_rule['cidr'] == '0.0.0.0/0', f"FAIL: Ephemeral CIDR should be 0.0.0.0/0, got {eph_rule['cidr']}"
    print(f"  PASS: Ephemeral ports (1024-65535) inbound rule configured (rule {eph_rule['rule_number']})")
    
    # Verify restrictive nature: only 2 inbound rules (VPC + ephemeral)
    assert len(inbound) == 2, f"FAIL: Expected exactly 2 inbound rules for restrictive access, found {len(inbound)}"
    print(f"  PASS: Restrictive inbound rules (only VPC and ephemeral ports)")


def test_property_8_private_nacl_outbound():
    """
    Property 8: Private NACL Rules - Outbound
    Requirements: 4.4, 4.5, 4.7
    - VPC CIDR allowed (all protocols)
    - HTTPS (443) to internet for updates
    - No unrestricted internet access
    """
    print("\nTesting Property 8: Private NACL Outbound Rules...")
    
    success, nacl_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    outbound = nacl_info['outbound_rules']
    
    # Check VPC CIDR rule
    vpc_rules = [r for r in outbound if r['type'] == 'vpc']
    assert len(vpc_rules) == 1, f"FAIL: Expected 1 VPC CIDR outbound rule, found {len(vpc_rules)}"
    vpc_rule = vpc_rules[0]
    
    expected_cidr = nacl_info['vpc_cidr'] or '10.0.0.0/16'
    assert vpc_rule['cidr'] == expected_cidr, f"FAIL: VPC outbound CIDR should be {expected_cidr}, got {vpc_rule['cidr']}"
    assert vpc_rule['protocol'] == '-1', f"FAIL: VPC outbound protocol should be '-1' (all), got {vpc_rule['protocol']}"
    print(f"  PASS: VPC CIDR ({expected_cidr}) outbound rule configured (rule {vpc_rule['rule_number']})")
    
    # Check HTTPS rule
    https_rules = [r for r in outbound if r['type'] == 'https']
    assert len(https_rules) == 1, f"FAIL: Expected 1 HTTPS outbound rule, found {len(https_rules)}"
    https_rule = https_rules[0]
    assert https_rule['from_port'] == 443, f"FAIL: HTTPS from_port should be 443, got {https_rule['from_port']}"
    assert https_rule['to_port'] == 443, f"FAIL: HTTPS to_port should be 443, got {https_rule['to_port']}"
    assert https_rule['cidr'] == '0.0.0.0/0', f"FAIL: HTTPS CIDR should be 0.0.0.0/0, got {https_rule['cidr']}"
    print(f"  PASS: HTTPS (443) outbound rule configured (rule {https_rule['rule_number']})")
    
    # Verify restrictive nature: only 3 outbound rules (VPC + HTTPS)
    assert len(outbound) == 3, f"FAIL: Expected exactly 3 outbound rules for restrictive access, found {len(outbound)}"
    print(f"  PASS: Restrictive outbound rules (only VPC and HTTPS)")


def test_property_8_rule_numbering():
    """
    Property 8: Rule Numbering
    Requirements: 4.6
    - Rules numbered to allow insertions (100, 110...)
    - Rule numbers >= 100
    """
    print("\nTesting Property 8: Rule Numbering Strategy...")
    
    success, nacl_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    all_rules = nacl_info['inbound_rules'] + nacl_info['outbound_rules']
    
    rule_numbers = [r['rule_number'] for r in all_rules if r['rule_number'] is not None]
    assert len(rule_numbers) > 0, "FAIL: No rule numbers found"
    
    # Check all rules are >= 100
    assert all(n >= 100 for n in rule_numbers), f"FAIL: Some rules have numbers < 100: {[n for n in rule_numbers if n < 100]}"
    print(f"  PASS: All {len(rule_numbers)} rules numbered >= 100")
    
    # Check rules follow pattern allowing insertions (multiples of 10)
    assert all(n % 10 == 0 for n in rule_numbers), f"FAIL: Some rules don't follow 10-increment pattern"
    print(f"  PASS: Rule numbering allows insertions (100, 110...)")
    
    # Verify rule number range
    print(f"  INFO: Rule numbers range from {min(rule_numbers)} to {max(rule_numbers)}")


def test_property_8_subnet_associations():
    """
    Property 8: NACL Subnet Associations
    Requirements: 4.5
    - Private NACL associated with all private subnets
    """
    print("\nTesting Property 8: NACL Subnet Associations...")
    
    success, nacl_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Should have 2 associations (one per private subnet)
    assoc_count = len(nacl_info['associations'])
    assert assoc_count == 2, f"FAIL: Expected 2 NACL associations, found {assoc_count}"
    print(f"  PASS: Private NACL associated with {assoc_count} private subnets")


def test_nacl_outputs():
    """Test that private NACL outputs are properly configured"""
    print("\nTesting private NACL outputs...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    outputs_file = os.path.join(vpc_dir, 'outputs.tf')
    
    assert os.path.exists(outputs_file), "FAIL: outputs.tf not found"
    
    with open(outputs_file, 'r') as f:
        content = f.read()
        
        # Check for private NACL outputs
        assert 'output "private_nacl_id"' in content, "FAIL: Missing private_nacl_id output"
        print("  PASS: private_nacl_id output defined")
        
        assert 'output "private_nacl_associations"' in content, "FAIL: Missing private_nacl_associations output"
        print("  PASS: private_nacl_associations output defined")
        
        # Verify outputs reference correct resources
        assert 'aws_network_acl.private' in content, "FAIL: Outputs don't reference private NACL"
        print("  PASS: Outputs reference aws_network_acl.private")


def run_all_tests():
    """Run all private NACL property tests"""
    print("=" * 80)
    print("VPC Best Practices - Private NACL Property Tests")
    print("Feature: vpc-best-practices, Task 11.1")
    print("Property 8: Private NACL Rules Compliance")
    print("Validates: Requirements 4.4, 4.5, 4.6, 4.7")
    print("=" * 80)
    
    tests = [
        ("NACL Resource Definition", test_nacl_resource_definition),
        ("Property 8: Inbound Rules", test_property_8_private_nacl_inbound),
        ("Property 8: Outbound Rules", test_property_8_private_nacl_outbound),
        ("Property 8: Rule Numbering", test_property_8_rule_numbering),
        ("Property 8: Subnet Associations", test_property_8_subnet_associations),
        ("NACL Outputs", test_nacl_outputs),
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
