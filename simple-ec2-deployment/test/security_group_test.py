#!/usr/bin/env python3
"""
Property-based test for Security Group Configuration
Feature: simple-ec2-deployment, Property 4: Security Group Configuration Compliance
Validates: Requirements 2.1, 2.2, 2.3, 2.5
"""

import os
import re
import sys

def read_main_tf() -> str:
    """Read the main.tf file content"""
    try:
        with open("main.tf", "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def validate_security_group_configuration(main_tf_content: str) -> tuple[bool, list]:
    """Validate security group configuration from main.tf content"""
    issues = []
    
    # Check if security group resource exists
    if 'resource "aws_security_group" "main"' not in main_tf_content:
        issues.append("Security group resource not found in main.tf")
        return False, issues
    
    # Extract security group block
    sg_match = re.search(r'resource "aws_security_group" "main" \{(.*?)\n\}', main_tf_content, re.DOTALL)
    if not sg_match:
        issues.append("Could not extract security group configuration")
        return False, issues
    
    sg_content = sg_match.group(1)
    
    # Check required ingress rules
    required_rules = [
        (22, "SSH", "var.allowed_ssh_cidr"),
        (80, "HTTP", "0.0.0.0/0"),
        (443, "HTTPS", "0.0.0.0/0")
    ]
    
    for port, description, expected_cidr in required_rules:
        # Look for ingress block with this port
        port_pattern = rf'ingress\s*\{{[^}}]*from_port\s*=\s*{port}[^}}]*to_port\s*=\s*{port}[^}}]*\}}'
        port_match = re.search(port_pattern, sg_content, re.DOTALL)
        
        if not port_match:
            issues.append(f"Missing {description} ingress rule for port {port}")
            continue
        
        port_block = port_match.group(0)
        
        # Check protocol
        if 'protocol    = "tcp"' not in port_block:
            issues.append(f"{description} rule should use TCP protocol")
        
        # Check CIDR blocks
        if port == 22:
            # SSH should use variable
            if "var.allowed_ssh_cidr" not in port_block:
                issues.append(f"SSH rule should use var.allowed_ssh_cidr")
        else:
            # HTTP/HTTPS should use 0.0.0.0/0
            if '"0.0.0.0/0"' not in port_block:
                issues.append(f"{description} rule should allow 0.0.0.0/0")
    
    # Check for unexpected ingress rules
    all_ingress_blocks = re.findall(r'ingress\s*\{(.*?)\}', sg_content, re.DOTALL)
    expected_ports = {22, 80, 443}
    
    for block in all_ingress_blocks:
        port_match = re.search(r'from_port\s*=\s*(\d+)', block)
        if port_match:
            port = int(port_match.group(1))
            if port not in expected_ports:
                issues.append(f"Unexpected ingress rule for port {port}")
    
    # Check egress rules
    egress_match = re.search(r'egress\s*\{(.*?)\}', sg_content, re.DOTALL)
    if egress_match:
        egress_content = egress_match.group(1)
        if 'from_port   = 0' not in egress_content:
            issues.append("Egress rule should allow all ports (from_port = 0)")
        if 'to_port     = 0' not in egress_content:
            issues.append("Egress rule should allow all ports (to_port = 0)")
        if 'protocol    = "-1"' not in egress_content:
            issues.append("Egress rule should allow all protocols (-1)")
        if '"0.0.0.0/0"' not in egress_content:
            issues.append("Egress rule should allow all destinations (0.0.0.0/0)")
    else:
        issues.append("No egress rules found")
    
    # Check naming and description
    if 'name_prefix = "${var.project_name}-sg"' not in sg_content:
        issues.append("Security group name_prefix should use project_name variable")
    
    if 'description = "Security group for ${var.project_name} EC2 instance"' not in sg_content:
        issues.append("Security group description should reference project_name")
    
    # Check VPC assignment
    if 'vpc_id      = data.aws_vpc.default.id' not in sg_content:
        issues.append("Security group should be assigned to default VPC")
    
    return len(issues) == 0, issues

def test_security_group_configuration_compliance():
    """
    Property 4: Security Group Configuration Compliance
    For any security group created by the configuration, it should allow SSH (port 22), 
    HTTP (port 80), and HTTPS (port 443), and should not allow any other inbound traffic.
    """
    print("Testing Property 4: Security Group Configuration Compliance")
    
    # Read the main.tf file
    main_tf_content = read_main_tf()
    
    if not main_tf_content:
        print("  FAIL: Could not read main.tf file")
        return False
    
    # Validate the security group configuration
    valid, issues = validate_security_group_configuration(main_tf_content)
    
    if valid:
        print("  PASS: Security group configuration is compliant")
        print("    - SSH (port 22) rule with configurable CIDR")
        print("    - HTTP (port 80) rule allowing 0.0.0.0/0")
        print("    - HTTPS (port 443) rule allowing 0.0.0.0/0")
        print("    - Egress rule allowing all outbound traffic")
        print("    - Proper naming and VPC assignment")
        return True
    else:
        print("  FAIL: Security group configuration issues:")
        for issue in issues:
            print(f"    - {issue}")
        return False

def test_variable_integration():
    """Test that security group properly uses the allowed_ssh_cidr variable"""
    print("\nTesting SSH CIDR variable integration...")
    
    main_tf_content = read_main_tf()
    
    if not main_tf_content:
        print("  FAIL: Could not read main.tf file")
        return False
    
    # Check that SSH rule uses the variable
    ssh_rule_pattern = r'ingress\s*\{[^}]*from_port\s*=\s*22[^}]*cidr_blocks\s*=\s*\[var\.allowed_ssh_cidr\][^}]*\}'
    
    if re.search(ssh_rule_pattern, main_tf_content, re.DOTALL):
        print("  PASS: SSH rule correctly uses var.allowed_ssh_cidr")
        return True
    else:
        print("  FAIL: SSH rule does not properly use var.allowed_ssh_cidr")
        return False

if __name__ == "__main__":
    print("Security Group Configuration Property Tests")
    print("=" * 50)
    
    # Run the property tests
    test1_passed = test_security_group_configuration_compliance()
    test2_passed = test_variable_integration()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Property 4 (Security Group Compliance): {'PASS' if test1_passed else 'FAIL'}")
    print(f"Variable Integration Test: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\nAll security group property tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome security group property tests FAILED!")
        sys.exit(1)