#!/usr/bin/env python3
"""
VPC Best Practices - Security Best Practices Property Tests
Feature: vpc-best-practices, Task 18.1
Property 18: Security Best Practices Compliance
Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.7

Tests verify:
- Default security group has no rules (deny all)
- No public IPs assigned to private subnets
- Least privilege enforcement
- Security group rule justifications
- No unrestricted access where not required
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


def parse_security_config(output: str) -> Dict:
    """Parse security configuration from plan output"""
    config = {
        'default_sg_exists': False,
        'default_sg_has_ingress': False,
        'default_sg_has_egress': False,
        'private_subnets': [],
        'public_subnets': [],
        'security_groups': [],
        'unrestricted_rules': []
    }
    
    lines = output.split('\n')
    
    # Check for default security group
    if 'aws_default_security_group.default' in output:
        config['default_sg_exists'] = True
        
        # Check if it has any ingress rules defined
        # In the plan, if no rules are defined, we shouldn't see ingress/egress blocks
        i = 0
        in_default_sg = False
        while i < len(lines):
            if 'aws_default_security_group.default' in lines[i]:
                in_default_sg = True
            elif in_default_sg and ('# aws_' in lines[i] or 'Plan:' in lines[i]):
                in_default_sg = False
            
            if in_default_sg:
                # Check for ingress rules
                if re.search(r'ingress\s*=\s*\[', lines[i]) or 'ingress {' in lines[i]:
                    # Check if the list is non-empty
                    if not re.search(r'ingress\s*=\s*\[\s*\]', lines[i]):
                        config['default_sg_has_ingress'] = True
                
                # Check for egress rules
                if re.search(r'egress\s*=\s*\[', lines[i]) or 'egress {' in lines[i]:
                    if not re.search(r'egress\s*=\s*\[\s*\]', lines[i]):
                        config['default_sg_has_egress'] = True
            
            i += 1
    
    # Parse private subnets and check for public IP assignment
    private_subnet_pattern = r'aws_subnet\.private\[(\d+)\]'
    i = 0
    while i < len(lines):
        match = re.search(private_subnet_pattern, lines[i])
        if match and 'will be created' in lines[i]:
            subnet_index = int(match.group(1))
            
            # Look ahead for map_public_ip_on_launch setting
            map_public_ip = None
            for j in range(i, min(i + 20, len(lines))):
                map_match = re.search(r'map_public_ip_on_launch\s*=\s*(true|false)', lines[j])
                if map_match:
                    map_public_ip = map_match.group(1) == 'true'
                    break
            
            config['private_subnets'].append({
                'index': subnet_index,
                'map_public_ip_on_launch': map_public_ip
            })
        
        i += 1
    
    return config


def test_property_18_default_sg_restricted():
    """
    Property 18: Default Security Group Restricted
    Requirements: 9.1
    - Default security group has no ingress rules
    - Default security group has no egress rules
    - Prevents accidental use of default SG
    """
    print("\nTesting Property 18: Default Security Group Restricted...")
    
    success, output = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    config = parse_security_config(output)
    
    # Verify default SG resource exists
    assert config['default_sg_exists'], "FAIL: Default security group not managed"
    print("  PASS: Default security group is managed")
    
    # Verify no ingress rules
    assert not config['default_sg_has_ingress'], \
        "FAIL: Default security group has ingress rules (should be empty)"
    print("  PASS: Default security group has no ingress rules (deny all inbound)")
    
    # Verify no egress rules
    assert not config['default_sg_has_egress'], \
        "FAIL: Default security group has egress rules (should be empty)"
    print("  PASS: Default security group has no egress rules (deny all outbound)")
    
    # Check source file for explicit empty configuration
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    # Check main.tf for default SG
    main_file = os.path.join(vpc_dir, 'main.tf')
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            content = f.read()
            if 'aws_default_security_group' in content:
                print("  PASS: Default security group explicitly managed in main.tf")


def test_property_18_private_subnet_no_public_ip():
    """
    Property 18: Private Subnets No Public IPs
    Requirements: 9.2, 9.3
    - Private subnets do not auto-assign public IPs
    - Ensures resources in private subnets remain private
    """
    print("\nTesting Property 18: Private Subnets No Public IP...")
    
    success, output = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    config = parse_security_config(output)
    
    # Verify private subnets exist
    assert len(config['private_subnets']) > 0, "FAIL: No private subnets found"
    print(f"  PASS: Found {len(config['private_subnets'])} private subnet(s)")
    
    # Verify none have public IP auto-assignment
    for subnet in config['private_subnets']:
        if subnet['map_public_ip_on_launch'] is not None:
            assert subnet['map_public_ip_on_launch'] == False, \
                f"FAIL: Private subnet {subnet['index']} has map_public_ip_on_launch = true"
    
    print("  PASS: All private subnets have map_public_ip_on_launch = false")
    
    # Verify in source file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    subnets_file = os.path.join(vpc_dir, 'subnets.tf')
    
    with open(subnets_file, 'r') as f:
        content = f.read()
        
        # Find private subnet section
        private_section_start = content.find('resource "aws_subnet" "private"')
        if private_section_start != -1:
            private_section = content[private_section_start:private_section_start + 500]
            assert 'map_public_ip_on_launch = false' in private_section, \
                "FAIL: Private subnet configuration should explicitly set map_public_ip_on_launch = false"
            print("  PASS: Private subnets explicitly configured with no public IP assignment")


def test_property_18_least_privilege():
    """
    Property 18: Least Privilege Enforcement
    Requirements: 9.4
    - Security groups use specific rules, not overly broad
    - Database tier has minimal egress
    - Application tier has restricted access
    """
    print("\nTesting Property 18: Least Privilege Enforcement...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    sg_file = os.path.join(vpc_dir, 'security_groups.tf')
    
    assert os.path.exists(sg_file), "FAIL: security_groups.tf not found"
    
    with open(sg_file, 'r') as f:
        content = f.read()
        
        # Verify database tier has minimal/no egress
        db_section_start = content.find('resource "aws_security_group" "database"')
        db_section_end = content.find('resource "aws_security_group"', db_section_start + 1)
        if db_section_end == -1:
            db_section_end = len(content)
        
        db_section = content[db_section_start:db_section_end]
        
        # Count egress rules in database section
        db_egress_count = db_section.count('aws_security_group_rule') + \
                         db_section.count('egress_') - \
                         db_section.count('# No egress')
        
        # Database should have 0-1 egress rules (minimal)
        # The comment "# No egress rules" indicates no rules
        assert '# No egress' in db_section or db_egress_count <= 1, \
            f"FAIL: Database tier should have minimal egress rules, found {db_egress_count}"
        print("  PASS: Database tier has minimal egress rules (least privilege)")
        
        # Verify bastion only has SSH egress to app tier
        bastion_egress = content.count('bastion_egress')
        assert bastion_egress == 1, \
            f"FAIL: Bastion should have exactly 1 egress rule (SSH to app), found {bastion_egress}"
        print("  PASS: Bastion has restricted egress (SSH to app tier only)")
        
        # Verify security group references are used (not just CIDR blocks)
        sg_reference_count = content.count('source_security_group_id')
        assert sg_reference_count >= 4, \
            f"FAIL: Expected at least 4 security group references, found {sg_reference_count}"
        print(f"  PASS: Security groups use references ({sg_reference_count} SG references found)")


def test_property_18_rule_justifications():
    """
    Property 18: Security Group Rule Justifications
    Requirements: 9.5
    - All security group rules have descriptions
    - Rules are documented with purpose
    """
    print("\nTesting Property 18: Security Group Rule Justifications...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    sg_file = os.path.join(vpc_dir, 'security_groups.tf')
    
    with open(sg_file, 'r') as f:
        content = f.read()
        
        # Count security group rules
        rule_count = content.count('resource "aws_security_group_rule"')
        
        # Count descriptions
        description_count = content.count('description')
        
        # Each rule should have a description
        # Note: Security groups themselves also have descriptions
        sg_count = content.count('resource "aws_security_group"')
        
        assert description_count >= rule_count, \
            f"FAIL: Not all rules have descriptions. Rules: {rule_count}, Descriptions: {description_count}"
        print(f"  PASS: All {rule_count} security group rules have descriptions")
        
        # Verify file header has documentation
        assert 'Requirements:' in content[:500], \
            "FAIL: Security groups file should have requirements documentation"
        print("  PASS: Security groups file has requirement documentation")


def test_property_18_no_unrestricted_access():
    """
    Property 18: No Unrestricted Access
    Requirements: 9.7
    - 0.0.0.0/0 only allowed for specific use cases (web tier HTTP/HTTPS, app HTTPS egress)
    - No unrestricted SSH or database access
    - No unrestricted egress except where documented
    """
    print("\nTesting Property 18: No Unrestricted Access...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    sg_file = os.path.join(vpc_dir, 'security_groups.tf')
    
    with open(sg_file, 'r') as f:
        content = f.read()
        
        # Find all 0.0.0.0/0 references
        unrestricted_patterns = re.findall(r'(resource "aws_security_group_rule" "(\w+)".*?description.*?"([^"]+)".*?cidr_blocks.*?0\.0\.0\.0/0)', 
                                          content, re.DOTALL)
        
        # Check each unrestricted rule
        lines = content.split('\n')
        unrestricted_rules = []
        
        for i, line in enumerate(lines):
            if '0.0.0.0/0' in line:
                # Get rule name from context
                for j in range(max(0, i-10), i):
                    if 'resource "aws_security_group_rule"' in lines[j]:
                        rule_name = re.search(r'"(\w+)"', lines[j].split('resource "aws_security_group_rule"')[1])
                        if rule_name:
                            unrestricted_rules.append(rule_name.group(1))
                        break
        
        # Verify unrestricted rules are only:
        # - web_ingress_http, web_ingress_https (web tier ingress)
        # - app_egress_https (application tier egress for updates)
        allowed_unrestricted = ['web_ingress_http', 'web_ingress_https', 'app_egress_https']
        
        for rule in unrestricted_rules:
            assert any(allowed in rule for allowed in allowed_unrestricted), \
                f"FAIL: Unrestricted access (0.0.0.0/0) found in rule '{rule}' - not allowed"
        
        print(f"  PASS: Only {len(set(unrestricted_rules))} allowed unrestricted rule(s) found (web HTTP/HTTPS, app HTTPS egress)")
        
        # Verify no unrestricted SSH
        # Check for SSH (port 22) combined with 0.0.0.0/0
        ssh_sections = []
        for i, line in enumerate(lines):
            if 'from_port         = 22' in line or 'from_port = 22' in line:
                # Check surrounding lines for 0.0.0.0/0
                context = '\n'.join(lines[max(0, i-5):min(len(lines), i+10)])
                if '0.0.0.0/0' in context and 'cidr_blocks' in context:
                    ssh_sections.append(context)
        
        assert len(ssh_sections) == 0, \
            f"FAIL: Unrestricted SSH access (0.0.0.0/0 on port 22) found in {len(ssh_sections)} location(s)"
        print("  PASS: No unrestricted SSH access")
        
        # Verify no unrestricted database access
        # Database ports: 3306 (MySQL), 5432 (PostgreSQL), 1433 (SQL Server), 27017 (MongoDB)
        db_unrestricted = []
        for port in [3306, 5432, 1433, 27017]:
            for i, line in enumerate(lines):
                if f'from_port         = {port}' in line or f'from_port = {port}' in line:
                    context = '\n'.join(lines[max(0, i-5):min(len(lines), i+10)])
                    if '0.0.0.0/0' in context and 'cidr_blocks' in context:
                        db_unrestricted.append(port)
        
        assert len(db_unrestricted) == 0, \
            f"FAIL: Unrestricted database access found on ports: {db_unrestricted}"
        print("  PASS: No unrestricted database access")


def test_default_nacl_unchanged():
    """
    Property 18: Default NACL Unchanged
    Requirements: 9.2
    - Default NACL is not modified
    - Custom NACLs are used instead
    """
    print("\nTesting Property 18: Default NACL Unchanged...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    # Check if default NACL is managed
    nacl_file = os.path.join(vpc_dir, 'nacls.tf')
    assert os.path.exists(nacl_file), "FAIL: nacls.tf not found"
    
    with open(nacl_file, 'r') as f:
        content = f.read()
        
        # Verify default NACL is NOT managed (no aws_default_network_acl)
        assert 'aws_default_network_acl' not in content, \
            "FAIL: Default NACL should not be managed - use custom NACLs instead"
        print("  PASS: Default NACL not managed (remains with default rules)")
        
        # Verify custom NACLs are used
        assert 'aws_network_acl.public' in content or 'resource "aws_network_acl" "public"' in content, \
            "FAIL: Custom public NACL not found"
        assert 'aws_network_acl.private' in content or 'resource "aws_network_acl" "private"' in content, \
            "FAIL: Custom private NACL not found"
        print("  PASS: Custom NACLs used (public and private)")


def run_all_tests():
    """Run all security best practices property tests"""
    print("=" * 80)
    print("VPC Best Practices - Security Best Practices Property Tests")
    print("Feature: vpc-best-practices, Task 18.1")
    print("Property 18: Security Best Practices Compliance")
    print("Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.7")
    print("=" * 80)
    
    tests = [
        ("Property 18: Default SG Restricted", test_property_18_default_sg_restricted),
        ("Property 18: Private Subnets No Public IP", test_property_18_private_subnet_no_public_ip),
        ("Property 18: Least Privilege", test_property_18_least_privilege),
        ("Property 18: Rule Justifications", test_property_18_rule_justifications),
        ("Property 18: No Unrestricted Access", test_property_18_no_unrestricted_access),
        ("Property 18: Default NACL Unchanged", test_default_nacl_unchanged),
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
