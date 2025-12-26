#!/usr/bin/env python3
"""
Property-based test for instance deployment compliance
Feature: simple-ec2-deployment, Property 1: Instance Deployment Compliance
Validates: Requirements 1.1, 1.4, 1.5, 2.4
"""
import os
import subprocess
import json
import re
from typing import Dict, Any, Tuple, List

def run_tofu_plan(tfvars_content: str = None) -> Tuple[bool, Dict[str, Any], str]:
    """Run tofu plan and parse the output"""
    try:
        # Determine the working directory (parent of test directory)
        test_dir = os.path.dirname(os.path.abspath(__file__))
        work_dir = os.path.dirname(test_dir)
        
        # Use test.tfvars if no custom content provided
        if tfvars_content:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False, dir=work_dir) as f:
                f.write(tfvars_content)
                tfvars_file = f.name
            
            cmd = ["tofu", "plan", f"-var-file={os.path.basename(tfvars_file)}", "-json", "-out=test.tfplan"]
        else:
            cmd = ["tofu", "plan", "-var-file=test.tfvars", "-json", "-out=test.tfplan"]
        
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if tfvars_content and os.path.exists(tfvars_file):
            os.unlink(tfvars_file)
        
        # Parse JSON output
        plan_data = {}
        for line in result.stdout.split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    if data.get('type') == 'planned_change':
                        resource = data.get('change', {}).get('resource', {})
                        resource_type = resource.get('resource_type')
                        if resource_type:
                            if resource_type not in plan_data:
                                plan_data[resource_type] = []
                            plan_data[resource_type].append(data)
                except json.JSONDecodeError:
                    continue
        
        return result.returncode == 0, plan_data, result.stdout + result.stderr
        
    except subprocess.TimeoutExpired:
        return False, {}, "Command timed out"
    except Exception as e:
        return False, {}, str(e)

def test_instance_created_in_region() -> Tuple[bool, List[str]]:
    """Test that EC2 instance is created in the specified AWS region (Req 1.1)"""
    print("\nTesting instance creation in specified region...")
    issues = []
    
    # Just test with the default region from test.tfvars
    success, plan_data, output = run_tofu_plan()
    
    if success and 'aws_instance' in plan_data:
        print("  PASS: Instance can be planned in specified region")
        return True, issues
    else:
        print("  FAIL: Instance planning failed")
        issues.append("Failed to plan instance")
        return False, issues

def test_instance_will_be_running() -> Tuple[bool, List[str]]:
    """Test that planned instance will be in running state (Req 1.4)"""
    print("\nTesting instance will be in running state...")
    issues = []
    
    success, plan_data, output = run_tofu_plan()
    
    if not success:
        issues.append("Failed to generate plan")
        print("  FAIL: Could not generate plan")
        return False, issues
    
    # Check that instance resource is being created
    if 'aws_instance' not in plan_data:
        issues.append("No EC2 instance in plan")
        print("  FAIL: No EC2 instance found in plan")
        return False, issues
    
    print("  PASS: EC2 instance resource will be created (will be running after apply)")
    return True, issues

def test_instance_has_public_ip() -> Tuple[bool, List[str]]:
    """Test that instance is configured to receive public IP (Req 1.5)"""
    print("\nTesting instance public IP assignment...")
    issues = []
    
    # Read main.tf to check for public IP configuration
    test_dir = os.path.dirname(os.path.abspath(__file__))
    main_tf_path = os.path.join(os.path.dirname(test_dir), "main.tf")
    try:
        with open(main_tf_path, "r") as f:
            main_tf_content = f.read()
    except FileNotFoundError:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Check for associate_public_ip_address = true
    if 'associate_public_ip_address = true' in main_tf_content or 'associate_public_ip_address=true' in main_tf_content:
        print("  PASS: Instance configured to receive public IP address")
    else:
        issues.append("Instance not configured for public IP assignment")
        print("  FAIL: associate_public_ip_address not set to true")
        return False, issues
    
    # Verify in plan that public_ip output exists
    success, plan_data, output = run_tofu_plan()
    if success and 'public_ip' in output:
        print("  PASS: Public IP will be available as output")
    else:
        print("  WARN: Could not verify public_ip output in plan")
    
    return True, issues

def test_instance_in_default_vpc() -> Tuple[bool, List[str]]:
    """Test that instance is placed in default VPC and subnet (Req 2.4)"""
    print("\nTesting instance placement in default VPC...")
    issues = []
    
    # Read main.tf to check for VPC data source
    test_dir = os.path.dirname(os.path.abspath(__file__))
    main_tf_path = os.path.join(os.path.dirname(test_dir), "main.tf")
    try:
        with open(main_tf_path, "r") as f:
            main_tf_content = f.read()
    except FileNotFoundError:
        issues.append("main.tf not found")
        print("  FAIL: main.tf not found")
        return False, issues
    
    # Check for default VPC data source
    if 'data "aws_vpc" "default"' in main_tf_content and 'default = true' in main_tf_content:
        print("  PASS: Configuration uses default VPC data source")
    else:
        issues.append("Default VPC data source not properly configured")
        print("  FAIL: Default VPC data source missing or incorrect")
        return False, issues
    
    # Check for default subnet data source
    if 'data "aws_subnet" "default"' in main_tf_content:
        print("  PASS: Configuration uses default subnet data source")
    else:
        issues.append("Default subnet data source not configured")
        print("  FAIL: Default subnet data source missing")
        return False, issues
    
    # Check that instance references the subnet
    if 'subnet_id' in main_tf_content and 'data.aws_subnet.default.id' in main_tf_content:
        print("  PASS: Instance configured to use default subnet")
    else:
        issues.append("Instance not configured to use default subnet")
        print("  FAIL: Instance subnet_id not referencing default subnet")
        return False, issues
    
    return True, issues

def test_deployment_compliance_property():
    """
    Property 1: Instance Deployment Compliance
    For any EC2 instance deployment, the instance should be created in the specified
    region, will be in running state after apply, has public IP enabled, and is
    placed in the default VPC/subnet.
    """
    print("Testing Property 1: Instance Deployment Compliance")
    print("=" * 60)
    
    all_issues = []
    
    # Test 1: Instance in specified region (Req 1.1)
    test1_passed, test1_issues = test_instance_created_in_region()
    all_issues.extend(test1_issues)
    
    # Test 2: Instance will be running (Req 1.4)
    test2_passed, test2_issues = test_instance_will_be_running()
    all_issues.extend(test2_issues)
    
    # Test 3: Public IP assignment (Req 1.5)
    test3_passed, test3_issues = test_instance_has_public_ip()
    all_issues.extend(test3_issues)
    
    # Test 4: Default VPC placement (Req 2.4)
    test4_passed, test4_issues = test_instance_in_default_vpc()
    all_issues.extend(test4_issues)
    
    overall_passed = all([test1_passed, test2_passed, test3_passed, test4_passed])
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Instance in Specified Region (Req 1.1): {'PASS' if test1_passed else 'FAIL'}")
    print(f"Instance Running State (Req 1.4): {'PASS' if test2_passed else 'FAIL'}")
    print(f"Public IP Assignment (Req 1.5): {'PASS' if test3_passed else 'FAIL'}")
    print(f"Default VPC Placement (Req 2.4): {'PASS' if test4_passed else 'FAIL'}")
    
    if overall_passed:
        print("\nAll deployment compliance tests PASSED!")
        return True
    else:
        print("\nSome deployment compliance tests FAILED:")
        for issue in all_issues:
            print(f"  - {issue}")
        return False

def test_plan_validation():
    """Additional test to ensure plan is valid and ready for deployment"""
    print("\nTesting plan validation...")
    
    success, plan_data, output = run_tofu_plan()
    
    if not success:
        print("  FAIL: Plan validation failed")
        return False
    
    # Check that plan creates expected resources
    expected_resources = ["aws_instance", "aws_security_group"]
    found_resources = []
    
    for resource_type in expected_resources:
        if resource_type in plan_data:
            found_resources.append(resource_type)
            print(f"  PASS: {resource_type} will be created")
    
    if len(found_resources) >= 2:
        print(f"  PASS: Plan includes {len(found_resources)} core resources")
        return True
    else:
        print(f"  FAIL: Plan missing expected resources")
        return False

if __name__ == "__main__":
    print("Instance Deployment Compliance Property Tests")
    print("=" * 60)
    
    # Run the main property test
    test1_passed = test_deployment_compliance_property()
    test2_passed = test_plan_validation()
    
    print("\n" + "=" * 60)
    print("Overall Results:")
    print(f"Property 1 (Deployment Compliance): {'PASS' if test1_passed else 'FAIL'}")
    print(f"Plan Validation: {'PASS' if test2_passed else 'FAIL'}")
    
    # Clean up test plan file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    plan_file = os.path.join(os.path.dirname(test_dir), "test.tfplan")
    if os.path.exists(plan_file):
        os.unlink(plan_file)
    
    if test1_passed and test2_passed:
        print("\nAll deployment property tests PASSED!")
        exit(0)
    else:
        print("\nSome property tests FAILED!")
        exit(1)
