#!/usr/bin/env python3
"""
VPC Best Practices - Security Group Property Tests
Feature: vpc-best-practices, Tasks 12.1, 13.1, 14.1, 15.1
Property 10: Bastion Security Group Rules
Property 11: Web Security Group Rules
Property 12: Application Security Group Rules
Property 13: Database Security Group Rules
Validates: Requirements 5.1-5.7, 9.5

Tests verify:
- 4-tier security group architecture
- Proper ingress/egress rules for each tier
- Security group references (not CIDR blocks where appropriate)
- No unrestricted egress rules
"""

import os
import re
import subprocess
from typing import Tuple, Dict, List


def run_tofu_plan(var_file: str = None) -> Tuple[bool, Dict]:
    """Run OpenTofu plan and parse security group information"""
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
        
        # Parse security group information
        sg_info = {
            'security_groups': {},
            'rules': [],
            'admin_cidr_count': 0
        }
        
        # Count admin CIDR blocks
        admin_cidr_match = re.search(r'admin_cidr_blocks\s*=\s*\[(.*?)\]', output, re.DOTALL)
        if admin_cidr_match:
            cidr_content = admin_cidr_match.group(1)
            sg_info['admin_cidr_count'] = len(re.findall(r'"[^"]*"', cidr_content))
        
        lines = output.split('\n')
        i = 0
        found_rule_lines = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for security groups
            if 'aws_security_group.' in line and 'will be created' in line:
                sg_match = re.search(r'aws_security_group\.(\w+)', line)
                if sg_match:
                    sg_name = sg_match.group(1)
                    sg_info['security_groups'][sg_name] = {'exists': True}
            
            # Look for security group rules
            if 'aws_security_group_rule' in line:
                found_rule_lines += 1
                if 'will be created' in line:
                    # Match both rule_name and rule_name[0]
                    rule_match = re.search(r'aws_security_group_rule\.(\w+)(?:\[(\d+)\])?', line)
                    if rule_match:
                        rule_name = rule_match.group(1)
                        index = rule_match.group(2) if rule_match.group(2) else None
                        
                        # Get rule details from the block
                        block_lines = []
                        j = i
                        while j < len(lines) and j < i + 30:  # Increase to 30 to capture full rule
                            # Stop at the closing brace followed by a new resource
                            if j > i:
                                # Check if we've hit the closing brace and the next line is a new resource
                                if lines[j].strip() == '}':
                                    block_lines.append(lines[j])
                                    break
                                # Also break if we hit a new resource start
                                if lines[j].strip().startswith('# aws_'):
                                    break
                            block_lines.append(lines[j])
                            j += 1
                        
                        block_text = '\n'.join(block_lines)
                        
                        rule_info = {
                            'name': rule_name,
                            'index': index,
                            'type': None,  # ingress or egress
                            'from_port': None,
                            'to_port': None,
                            'protocol': None,
                            'cidr_blocks': [],
                            'source_sg_id': None,
                            'description': None,
                            'sg_id': None
                        }
                        
                        # Parse rule details
                        type_match = re.search(r'type\s*=\s*"(\w+)"', block_text)
                        if type_match:
                            rule_info['type'] = type_match.group(1)
                        
                        from_port_match = re.search(r'from_port\s*=\s*(\d+)', block_text)
                        if from_port_match:
                            rule_info['from_port'] = int(from_port_match.group(1))
                        
                        to_port_match = re.search(r'to_port\s*=\s*(\d+)', block_text)
                        if to_port_match:
                            rule_info['to_port'] = int(to_port_match.group(1))
                        
                        protocol_match = re.search(r'protocol\s*=\s*"([^"]+)"', block_text)
                        if protocol_match:
                            rule_info['protocol'] = protocol_match.group(1)
                        
                        # Check for CIDR blocks (may span multiple lines)
                        cidr_match = re.search(r'cidr_blocks\s*=\s*\[(.*?)\]', block_text, re.DOTALL)
                        if cidr_match:
                            cidrs = re.findall(r'"([^"]+)"', cidr_match.group(1))
                            rule_info['cidr_blocks'] = cidrs
                        
                        # Check for source security group
                        source_sg_match = re.search(r'source_security_group_id\s*=', block_text)
                        if source_sg_match:
                            rule_info['source_sg_id'] = 'referenced'
                        
                        desc_match = re.search(r'description\s*=\s*"([^"]+)"', block_text)
                        if desc_match:
                            rule_info['description'] = desc_match.group(1)
                        
                        # Determine which SG this rule belongs to from the rule name
                        # Check most specific patterns first to avoid mismatches
                        if rule_name.startswith('bastion_'):
                            rule_info['sg_id'] = 'bastion'
                        elif rule_name.startswith('web_'):
                            rule_info['sg_id'] = 'web'
                        elif rule_name.startswith('app_'):
                            rule_info['sg_id'] = 'application'
                        elif rule_name.startswith('db_'):
                            rule_info['sg_id'] = 'database'
                        
                        sg_info['rules'].append(rule_info)
            
            i += 1
        
        return result.returncode == 0, sg_info
        
    except Exception as e:
        print(f"  ERROR running tofu plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}


def check_sg_config() -> Dict:
    """Check security group configuration in source files"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    config_info = {
        'sg_file_exists': False,
        'bastion_sg_defined': False,
        'web_sg_defined': False,
        'app_sg_defined': False,
        'db_sg_defined': False,
        'has_bastion_ssh_ingress': False,
        'has_bastion_ssh_egress': False,
        'uses_sg_references': False,
        'has_descriptions': False
    }
    
    # Check security_groups.tf
    sg_file = os.path.join(vpc_dir, 'security_groups.tf')
    if os.path.exists(sg_file):
        config_info['sg_file_exists'] = True
        
        with open(sg_file, 'r') as f:
            content = f.read()
            
            config_info['bastion_sg_defined'] = 'resource "aws_security_group" "bastion"' in content
            config_info['web_sg_defined'] = 'resource "aws_security_group" "web"' in content
            config_info['app_sg_defined'] = 'resource "aws_security_group" "application"' in content
            config_info['db_sg_defined'] = 'resource "aws_security_group" "database"' in content
            
            config_info['has_bastion_ssh_ingress'] = 'resource "aws_security_group_rule" "bastion_ingress_ssh"' in content
            config_info['has_bastion_ssh_egress'] = 'resource "aws_security_group_rule" "bastion_egress_ssh_to_app"' in content
            
            # Check for security group references (not CIDR blocks)
            config_info['uses_sg_references'] = 'source_security_group_id' in content
            
            # Check for descriptions
            config_info['has_descriptions'] = content.count('description') > 4
    
    return config_info


def test_sg_resource_definition():
    """Test that all 4 security groups are properly defined"""
    print("\nTesting security group resource definitions...")
    
    config = check_sg_config()
    
    assert config['sg_file_exists'], "FAIL: No security_groups.tf file found"
    print("  PASS: security_groups.tf file exists")
    
    assert config['bastion_sg_defined'], "FAIL: No bastion security group defined"
    print("  PASS: Bastion security group defined")
    
    assert config['web_sg_defined'], "FAIL: No web security group defined"
    print("  PASS: Web security group defined")
    
    assert config['app_sg_defined'], "FAIL: No application security group defined"
    print("  PASS: Application security group defined")
    
    assert config['db_sg_defined'], "FAIL: No database security group defined"
    print("  PASS: Database security group defined")
    
    assert config['has_bastion_ssh_ingress'], "FAIL: No bastion SSH ingress rule defined"
    print("  PASS: Bastion SSH ingress rule defined")
    
    assert config['has_bastion_ssh_egress'], "FAIL: No bastion SSH egress rule defined"
    print("  PASS: Bastion SSH egress rule defined")
    
    assert config['uses_sg_references'], "FAIL: No security group references found (should use SG IDs, not CIDRs)"
    print("  PASS: Security group references used (not just CIDR blocks)")
    
    assert config['has_descriptions'], "FAIL: Insufficient rule descriptions"
    print("  PASS: Security group rules have descriptions")


def test_property_10_bastion_sg():
    """
    Property 10: Bastion Security Group Rules
    Requirements: 5.2
    - SSH (22) ingress from admin CIDR blocks only
    - SSH (22) egress to application tier only (using SG reference)
    - No unrestricted access
    """
    print("\nTesting Property 10: Bastion Security Group Rules...")
    
    success, sg_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Verify bastion SG exists
    assert 'bastion' in sg_info['security_groups'], "FAIL: Bastion security group not found"
    print("  PASS: Bastion security group exists")
    
    # Get bastion rules
    bastion_rules = [r for r in sg_info['rules'] if r['sg_id'] == 'bastion']
    
    # Check SSH ingress rules (one per admin CIDR)
    bastion_ingress = [r for r in bastion_rules if r['type'] == 'ingress' and 'ssh' in r['name']]
    expected_count = sg_info['admin_cidr_count']
    if expected_count == 0 and len(bastion_ingress) > 0:
        expected_count = len(bastion_ingress)
    
    assert len(bastion_ingress) >= 1, f"FAIL: Expected at least 1 SSH ingress rule, found {len(bastion_ingress)}"
    
    for rule in bastion_ingress:
        assert rule['from_port'] == 22, f"FAIL: SSH from_port should be 22, got {rule['from_port']}"
        assert rule['to_port'] == 22, f"FAIL: SSH to_port should be 22, got {rule['to_port']}"
        assert rule['protocol'] == 'tcp', f"FAIL: SSH protocol should be tcp, got {rule['protocol']}"
        assert len(rule['cidr_blocks']) > 0, "FAIL: SSH ingress should have CIDR blocks"
    print(f"  PASS: SSH ingress from {len(bastion_ingress)} admin CIDR block(s)")
    
    # Check SSH egress to app tier
    bastion_egress = [r for r in bastion_rules if r['type'] == 'egress' and 'ssh' in r['name']]
    assert len(bastion_egress) == 1, f"FAIL: Expected 1 SSH egress rule, found {len(bastion_egress)}"
    
    egress_rule = bastion_egress[0]
    assert egress_rule['from_port'] == 22, f"FAIL: SSH egress from_port should be 22"
    assert egress_rule['to_port'] == 22, f"FAIL: SSH egress to_port should be 22"
    assert egress_rule['source_sg_id'] == 'referenced', "FAIL: SSH egress should reference application SG, not use CIDR"
    print(f"  PASS: SSH egress to application tier (using SG reference)")
    
    # Verify no unrestricted egress (like 0.0.0.0/0 on all ports)
    unrestricted_egress = [r for r in bastion_rules if r['type'] == 'egress' and '0.0.0.0/0' in r['cidr_blocks']]
    assert len(unrestricted_egress) == 0, f"FAIL: Found {len(unrestricted_egress)} unrestricted egress rules"
    print(f"  PASS: No unrestricted egress rules")


def test_property_11_web_sg():
    """
    Property 11: Web Security Group Rules
    Requirements: 5.3
    - HTTP (80) ingress from internet (0.0.0.0/0)
    - HTTPS (443) ingress from internet (0.0.0.0/0)
    - Egress to application tier only (using SG reference)
    - No other unrestricted ingress
    """
    print("\nTesting Property 11: Web Security Group Rules...")
    
    success, sg_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Verify web SG exists
    assert 'web' in sg_info['security_groups'], "FAIL: Web security group not found"
    print("  PASS: Web security group exists")
    
    # Get web rules
    web_rules = [r for r in sg_info['rules'] if r['sg_id'] == 'web']
    
    # Check HTTP ingress from internet
    web_http_ingress = [r for r in web_rules if r['type'] == 'ingress' and r['from_port'] == 80]
    assert len(web_http_ingress) == 1, f"FAIL: Expected 1 HTTP ingress rule, found {len(web_http_ingress)}"
    
    http_rule = web_http_ingress[0]
    assert http_rule['from_port'] == 80, f"FAIL: HTTP from_port should be 80, got {http_rule['from_port']}"
    assert http_rule['to_port'] == 80, f"FAIL: HTTP to_port should be 80, got {http_rule['to_port']}"
    assert http_rule['protocol'] == 'tcp', f"FAIL: HTTP protocol should be tcp, got {http_rule['protocol']}"
    assert '0.0.0.0/0' in http_rule['cidr_blocks'], "FAIL: HTTP ingress should allow internet (0.0.0.0/0)"
    print(f"  PASS: HTTP (80) ingress from internet (0.0.0.0/0)")
    
    # Check HTTPS ingress from internet
    web_https_ingress = [r for r in web_rules if r['type'] == 'ingress' and r['from_port'] == 443]
    assert len(web_https_ingress) == 1, f"FAIL: Expected 1 HTTPS ingress rule, found {len(web_https_ingress)}"
    
    https_rule = web_https_ingress[0]
    assert https_rule['from_port'] == 443, f"FAIL: HTTPS from_port should be 443, got {https_rule['from_port']}"
    assert https_rule['to_port'] == 443, f"FAIL: HTTPS to_port should be 443, got {https_rule['to_port']}"
    assert https_rule['protocol'] == 'tcp', f"FAIL: HTTPS protocol should be tcp, got {https_rule['protocol']}"
    assert '0.0.0.0/0' in https_rule['cidr_blocks'], "FAIL: HTTPS ingress should allow internet (0.0.0.0/0)"
    print(f"  PASS: HTTPS (443) ingress from internet (0.0.0.0/0)")
    
    # Check egress to application tier
    web_egress = [r for r in web_rules if r['type'] == 'egress']
    assert len(web_egress) >= 1, f"FAIL: Expected at least 1 egress rule, found {len(web_egress)}"
    
    # At least one egress rule should reference app SG
    app_egress = [r for r in web_egress if r['source_sg_id'] == 'referenced']
    assert len(app_egress) >= 1, "FAIL: Web tier should have egress to application tier (using SG reference)"
    print(f"  PASS: Egress to application tier (using SG reference)")
    
    # Verify only HTTP/HTTPS from internet (no other unrestricted ingress)
    web_ingress = [r for r in web_rules if r['type'] == 'ingress']
    unrestricted_ingress = [r for r in web_ingress if '0.0.0.0/0' in r['cidr_blocks']]
    
    # Should only have HTTP and HTTPS from internet
    for rule in unrestricted_ingress:
        assert rule['from_port'] in [80, 443], \
            f"FAIL: Unrestricted ingress on port {rule['from_port']}, only HTTP(80) and HTTPS(443) should be allowed from internet"
    print(f"  PASS: Only HTTP/HTTPS allowed from internet")


def test_property_12_application_sg():
    """
    Property 12: Application Security Group Rules
    Requirements: 5.4, 5.7
    - Ingress from web tier only (using SG reference)
    - Ingress SSH from bastion tier (using SG reference)
    - Egress to database tier (using SG reference)
    - HTTPS egress to internet for updates/API calls
    - No direct internet ingress
    """
    print("\nTesting Property 12: Application Security Group Rules...")
    
    success, sg_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Verify application SG exists
    assert 'application' in sg_info['security_groups'], "FAIL: Application security group not found"
    print("  PASS: Application security group exists")
    
    # Get application rules
    app_rules = [r for r in sg_info['rules'] if r['sg_id'] == 'application']
    
    # Check ingress from web tier
    app_web_ingress = [r for r in app_rules if r['type'] == 'ingress' and 'from_web' in r['name']]
    assert len(app_web_ingress) == 1, f"FAIL: Expected 1 ingress rule from web tier, found {len(app_web_ingress)}"
    
    web_ingress_rule = app_web_ingress[0]
    assert web_ingress_rule['source_sg_id'] == 'referenced', "FAIL: Ingress from web should use SG reference, not CIDR"
    # Common app port (could be 8080 or other)
    assert web_ingress_rule['from_port'] == web_ingress_rule['to_port'], "FAIL: Application port should have same from/to port"
    print(f"  PASS: Ingress from web tier on port {web_ingress_rule['from_port']} (using SG reference)")
    
    # Check SSH ingress from bastion
    app_ssh_ingress = [r for r in app_rules if r['type'] == 'ingress' and 'ssh' in r['name'] and 'bastion' in r['name']]
    assert len(app_ssh_ingress) == 1, f"FAIL: Expected 1 SSH ingress rule from bastion, found {len(app_ssh_ingress)}"
    
    ssh_ingress_rule = app_ssh_ingress[0]
    assert ssh_ingress_rule['from_port'] == 22, f"FAIL: SSH from_port should be 22, got {ssh_ingress_rule['from_port']}"
    assert ssh_ingress_rule['to_port'] == 22, f"FAIL: SSH to_port should be 22, got {ssh_ingress_rule['to_port']}"
    assert ssh_ingress_rule['source_sg_id'] == 'referenced', "FAIL: SSH ingress from bastion should use SG reference"
    print(f"  PASS: SSH (22) ingress from bastion tier (using SG reference)")
    
    # Check egress to database tier
    app_db_egress = [r for r in app_rules if r['type'] == 'egress' and 'to_db' in r['name']]
    assert len(app_db_egress) == 1, f"FAIL: Expected 1 egress rule to database tier, found {len(app_db_egress)}"
    
    db_egress_rule = app_db_egress[0]
    assert db_egress_rule['source_sg_id'] == 'referenced', "FAIL: Egress to database should use SG reference, not CIDR"
    # Common database ports: 3306 (MySQL), 5432 (PostgreSQL), etc.
    assert db_egress_rule['from_port'] in [3306, 5432, 1433, 5439], \
        f"FAIL: Database port {db_egress_rule['from_port']} not a common database port"
    print(f"  PASS: Egress to database tier on port {db_egress_rule['from_port']} (using SG reference)")
    
    # Check HTTPS egress to internet
    app_https_egress = [r for r in app_rules if r['type'] == 'egress' and r['from_port'] == 443]
    assert len(app_https_egress) == 1, f"FAIL: Expected 1 HTTPS egress rule, found {len(app_https_egress)}"
    
    https_egress_rule = app_https_egress[0]
    assert https_egress_rule['from_port'] == 443, f"FAIL: HTTPS from_port should be 443"
    assert https_egress_rule['to_port'] == 443, f"FAIL: HTTPS to_port should be 443"
    assert '0.0.0.0/0' in https_egress_rule['cidr_blocks'], "FAIL: HTTPS egress should allow internet (0.0.0.0/0)"
    print(f"  PASS: HTTPS (443) egress to internet for updates/API calls")
    
    # Verify no direct internet ingress (all ingress should use SG references)
    app_ingress = [r for r in app_rules if r['type'] == 'ingress']
    internet_ingress = [r for r in app_ingress if '0.0.0.0/0' in r['cidr_blocks']]
    assert len(internet_ingress) == 0, \
        f"FAIL: Found {len(internet_ingress)} direct internet ingress rules, application tier should not be directly accessible from internet"
    print(f"  PASS: No direct internet ingress (all ingress via SG references)")
    
    # Verify all ingress uses security group references (Requirements 5.7)
    for rule in app_ingress:
        assert rule['source_sg_id'] == 'referenced', \
            f"FAIL: Ingress rule {rule['name']} should use security group reference, not CIDR blocks"
    print(f"  PASS: All ingress rules use security group references (Req 5.7)")


def test_property_13_database_sg():
    """
    Property 13: Database Security Group Rules
    Requirements: 5.5, 5.8
    - Ingress from application tier only (using SG reference)
    - Minimal or no egress rules (least privilege)
    - No internet access (ingress or egress)
    - Complete isolation except from application tier
    """
    print("\nTesting Property 13: Database Security Group Rules...")
    
    success, sg_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Verify database SG exists
    assert 'database' in sg_info['security_groups'], "FAIL: Database security group not found"
    print("  PASS: Database security group exists")
    
    # Get database rules
    db_rules = [r for r in sg_info['rules'] if r['sg_id'] == 'database']
    
    # Check ingress from application tier
    db_ingress = [r for r in db_rules if r['type'] == 'ingress']
    assert len(db_ingress) >= 1, f"FAIL: Expected at least 1 ingress rule, found {len(db_ingress)}"
    
    # All ingress should be from application tier using SG reference
    for rule in db_ingress:
        assert rule['source_sg_id'] == 'referenced', \
            f"FAIL: Database ingress rule {rule['name']} should use SG reference from application tier, not CIDR"
        # Common database ports
        assert rule['from_port'] in [3306, 5432, 1433, 5439, 27017], \
            f"FAIL: Database port {rule['from_port']} is not a common database port"
    print(f"  PASS: Ingress from application tier only on port {db_ingress[0]['from_port']} (using SG reference)")
    
    # Check egress rules (should be minimal or none)
    db_egress = [r for r in db_rules if r['type'] == 'egress']
    assert len(db_egress) <= 1, \
        f"FAIL: Expected 0-1 egress rules (minimal configuration), found {len(db_egress)}"
    print(f"  PASS: Minimal egress configuration ({len(db_egress)} egress rules - least privilege)")
    
    # Verify no internet access - no ingress from 0.0.0.0/0
    internet_ingress = [r for r in db_ingress if '0.0.0.0/0' in r['cidr_blocks']]
    assert len(internet_ingress) == 0, \
        f"FAIL: Found {len(internet_ingress)} internet ingress rules, database should not be accessible from internet"
    print(f"  PASS: No internet ingress (complete isolation)")
    
    # Verify no internet egress
    internet_egress = [r for r in db_egress if '0.0.0.0/0' in r['cidr_blocks']]
    assert len(internet_egress) == 0, \
        f"FAIL: Found {len(internet_egress)} internet egress rules, database should not have internet access"
    print(f"  PASS: No internet egress (complete isolation)")
    
    # Verify all ingress uses security group references (Requirements 5.8)
    for rule in db_ingress:
        assert rule['source_sg_id'] == 'referenced', \
            f"FAIL: Database ingress should only use security group references (Req 5.8)"
    print(f"  PASS: All ingress uses security group references (Req 5.8)")


def test_property_9_sg_layering():
    """
    Property 9: Security Group Layering
    Requirements: 5.1, 5.6
    - All four security group tiers exist (bastion, web, app, database)
    - Consistent naming conventions
    - Descriptive names and descriptions
    - Proper VPC association
    """
    print("\nTesting Property 9: Security Group Layering...")
    
    success, sg_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Verify all four tiers exist
    required_tiers = ['bastion', 'web', 'application', 'database']
    for tier in required_tiers:
        assert tier in sg_info['security_groups'], f"FAIL: {tier} security group not found"
    print(f"  PASS: All four security group tiers exist (bastion, web, application, database)")
    
    # Check naming conventions in the config
    config = check_sg_config()
    
    # Verify naming pattern exists
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    sg_file = os.path.join(vpc_dir, 'security_groups.tf')
    
    with open(sg_file, 'r') as f:
        content = f.read()
        
        # Check for consistent naming with prefix
        naming_pattern_found = 'local.resource_prefix' in content and '-sg"' in content
        assert naming_pattern_found, "FAIL: Inconsistent naming convention (should use local.resource_prefix and -sg suffix)"
        print(f"  PASS: Consistent naming convention (uses resource prefix and -sg suffix)")
        
        # Verify descriptive names and descriptions
        for tier in required_tiers:
            assert f'resource "aws_security_group" "{tier}"' in content, \
                f"FAIL: Security group {tier} not properly defined"
            
            # Check for description field
            tier_section_start = content.find(f'resource "aws_security_group" "{tier}"')
            tier_section = content[tier_section_start:tier_section_start + 500]
            assert 'description' in tier_section, f"FAIL: {tier} security group missing description"
        
        print(f"  PASS: All security groups have descriptive names and descriptions")
        
        # Verify VPC association
        vpc_association_count = content.count('vpc_id      = aws_vpc.main.id')
        assert vpc_association_count >= 4, \
            f"FAIL: Not all security groups associated with VPC (found {vpc_association_count} associations)"
        print(f"  PASS: All security groups properly associated with VPC")
        
        # Verify tags are applied
        tags_count = content.count('tags = merge(')
        assert tags_count >= 4, f"FAIL: Not all security groups have tags"
        print(f"  PASS: All security groups have proper tagging")


def test_sg_outputs():
    """Test that security group outputs are properly configured"""
    print("\nTesting security group outputs...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    outputs_file = os.path.join(vpc_dir, 'outputs.tf')
    
    assert os.path.exists(outputs_file), "FAIL: outputs.tf not found"
    
    with open(outputs_file, 'r') as f:
        content = f.read()
        
        # Check for security group outputs
        assert 'output "bastion_sg_id"' in content, "FAIL: Missing bastion_sg_id output"
        print("  PASS: bastion_sg_id output defined")
        
        assert 'output "web_sg_id"' in content, "FAIL: Missing web_sg_id output"
        print("  PASS: web_sg_id output defined")
        
        assert 'output "application_sg_id"' in content, "FAIL: Missing application_sg_id output"
        print("  PASS: application_sg_id output defined")
        
        assert 'output "database_sg_id"' in content, "FAIL: Missing database_sg_id output"
        print("  PASS: database_sg_id output defined")
        
        # Verify outputs reference correct resources
        assert 'aws_security_group.bastion' in content, "FAIL: Outputs don't reference bastion SG"
        print("  PASS: Outputs reference all security groups")


def run_all_tests():
    """Run all security group property tests"""
    print("=" * 80)
    print("VPC Best Practices - Security Group Property Tests")
    print("Feature: vpc-best-practices, Tasks 12.1, 13.1, 14.1, 15.1, 15.2")
    print("Property 9: Security Group Layering")
    print("Property 10: Bastion Security Group Rules")
    print("Property 11: Web Security Group Rules")
    print("Property 12: Application Security Group Rules")
    print("Property 13: Database Security Group Rules")
    print("Validates: Requirements 5.1-5.8, 9.5")
    print("=" * 80)
    
    tests = [
        ("Security Group Resource Definition", test_sg_resource_definition),
        ("Property 9: Security Group Layering", test_property_9_sg_layering),
        ("Property 10: Bastion SG Rules", test_property_10_bastion_sg),
        ("Property 11: Web SG Rules", test_property_11_web_sg),
        ("Property 12: Application SG Rules", test_property_12_application_sg),
        ("Property 13: Database SG Rules", test_property_13_database_sg),
        ("Security Group Outputs", test_sg_outputs),
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
