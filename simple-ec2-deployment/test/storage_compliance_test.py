#!/usr/bin/env python3
"""
Property-based test for storage configuration compliance (optimized version)
Feature: simple-ec2-deployment, Property 6: Storage Configuration Compliance
Validates: Requirements 4.3

This test validates storage configuration correctness by analyzing the configuration
structure rather than attempting AWS deployment.
"""

import os
import sys
import re

def read_variables_tf() -> str:
    """Read variables.tf file content"""
    variables_tf_path = "variables.tf"
    if not os.path.exists(variables_tf_path):
        return ""
    with open(variables_tf_path, 'r') as f:
        return f.read()

def read_main_tf() -> str:
    """Read main.tf file content"""
    main_tf_path = "main.tf"
    if not os.path.exists(main_tf_path):
        return ""
    with open(main_tf_path, 'r') as f:
        return f.read()

def validate_storage_constraints(variables_content: str) -> tuple[bool, str]:
    """Validate that storage variables have correct constraints"""
    # Check root_volume_size validation
    size_validation_pattern = r'var\.root_volume_size\s*>=\s*8\s*&&\s*var\.root_volume_size\s*<=\s*30'
    if not re.search(size_validation_pattern, variables_content):
        return False, "root_volume_size validation (8-30GB) not found or incorrect"
    
    # Check root_volume_type validation
    type_validation_pattern = r'contains\(\["gp2",\s*"gp3"\],\s*var\.root_volume_type\)'
    if not re.search(type_validation_pattern, variables_content):
        return False, "root_volume_type validation (gp2/gp3) not found or incorrect"
    
    return True, "Storage constraints validated"

def test_storage_configuration_compliance():
    """
    Property 6: Storage Configuration Compliance
    Validates that storage configuration has proper constraints for free tier compliance:
    - Volume size: 8-30GB
    - Volume type: gp2 or gp3 only
    - Encryption enabled
    """
    print("Testing Property 6: Storage Configuration Compliance")
    
    variables_content = read_variables_tf()
    main_content = read_main_tf()
    
    if not variables_content:
        print("  FAIL: variables.tf not found")
        return False
    
    if not main_content:
        print("  FAIL: main.tf not found")
        return False
    
    checks_passed = 0
    total_checks = 5
    
    # Check 1: root_volume_size variable exists
    print("\nChecking storage variable definitions...")
    if 'variable "root_volume_size"' in variables_content:
        print("  PASS: root_volume_size variable defined")
        checks_passed += 1
    else:
        print("  FAIL: root_volume_size variable not found")
    
    # Check 2: root_volume_type variable exists
    if 'variable "root_volume_type"' in variables_content:
        print("  PASS: root_volume_type variable defined")
        checks_passed += 1
    else:
        print("  FAIL: root_volume_type variable not found")
    
    # Check 3: Storage constraints are correct
    print("\nChecking storage constraints...")
    valid, message = validate_storage_constraints(variables_content)
    if valid:
        print(f"  PASS: {message}")
        checks_passed += 1
    else:
        print(f"  FAIL: {message}")
    
    # Check 4: root_block_device configuration exists in main.tf
    print("\nChecking storage configuration in main.tf...")
    if 'root_block_device' in main_content:
        print("  PASS: root_block_device configuration found")
        checks_passed += 1
    else:
        print("  FAIL: root_block_device configuration not found")
    
    # Check 5: Encryption is enabled
    if re.search(r'encrypted\s*=\s*true', main_content):
        print("  PASS: Storage encryption enabled")
        checks_passed += 1
    else:
        print("  FAIL: Storage encryption not enabled")
    
    # Validate that volume_type and volume_size reference the variables
    print("\nChecking variable references in main.tf...")
    if 'var.root_volume_type' in main_content:
        print("  PASS: root_volume_type variable referenced")
    else:
        print("  WARN: root_volume_type variable not referenced")
    
    if 'var.root_volume_size' in main_content:
        print("  PASS: root_volume_size variable referenced")
    else:
        print("  WARN: root_volume_size variable not referenced")
    
    print(f"\nStorage configuration compliance: {checks_passed}/{total_checks} checks passed")
    
    return checks_passed == total_checks

if __name__ == "__main__":
    print("Storage Configuration Compliance Property Tests")
    print("=" * 60)
    
    # Run the comprehensive property test
    test_passed = test_storage_configuration_compliance()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Property 6 (Storage Configuration Compliance): {'PASS' if test_passed else 'FAIL'}")
    
    if test_passed:
        print("\nAll storage compliance property tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome storage compliance tests FAILED!")
        sys.exit(1)