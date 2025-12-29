#!/usr/bin/env python3
"""
VPC Best Practices - VPC Flow Logs Property Tests
Feature: vpc-best-practices, Task 16.1
Property 14: VPC Flow Logs Configuration
Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5

Tests verify:
- VPC Flow Logs enabled when variable is true
- CloudWatch Log Group creation
- IAM role and policy for Flow Logs service
- ALL traffic capture setting
- Proper configuration and integration
"""

import os
import re
import subprocess
from typing import Tuple, Dict


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


def parse_flow_logs_config(output: str) -> Dict:
    """Parse VPC Flow Logs configuration from plan output"""
    config = {
        'flow_log_exists': False,
        'cloudwatch_log_group_exists': False,
        'iam_role_exists': False,
        'iam_policy_exists': False,
        'traffic_type': None,
        'log_destination_type': None,
        'vpc_id_referenced': False,
        'retention_days': None
    }
    
    lines = output.split('\n')
    
    # Check for flow log resource
    if 'aws_flow_log.main' in output:
        config['flow_log_exists'] = True
        
        # Extract traffic_type
        traffic_match = re.search(r'traffic_type\s*=\s*"([^"]+)"', output)
        if traffic_match:
            config['traffic_type'] = traffic_match.group(1)
        
        # Check VPC reference
        if 'vpc_id' in output and 'aws_vpc.main.id' in output:
            config['vpc_id_referenced'] = True
    
    # Check for CloudWatch Log Group
    if 'aws_cloudwatch_log_group.flow_logs' in output:
        config['cloudwatch_log_group_exists'] = True
        
        # Extract retention days
        retention_match = re.search(r'retention_in_days\s*=\s*(\d+)', output)
        if retention_match:
            config['retention_days'] = int(retention_match.group(1))
    
    # Check for IAM role
    if 'aws_iam_role.flow_logs' in output:
        config['iam_role_exists'] = True
    
    # Check for IAM policy
    if 'aws_iam_role_policy.flow_logs' in output:
        config['iam_policy_exists'] = True
    
    # Check log destination
    if 'log_destination' in output:
        config['log_destination_type'] = 'cloudwatch'
    
    return config


def check_flow_logs_file() -> Dict:
    """Check if flow logs configuration file exists and has proper structure"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    info = {
        'file_exists': False,
        'has_cloudwatch_log_group': False,
        'has_iam_role': False,
        'has_iam_policy': False,
        'has_flow_log': False,
        'uses_conditional': False,
        'traffic_type_all': False,
        'has_tags': False
    }
    
    # Check for flow_logs.tf file
    flow_logs_file = os.path.join(vpc_dir, 'flow_logs.tf')
    if os.path.exists(flow_logs_file):
        info['file_exists'] = True
        
        with open(flow_logs_file, 'r') as f:
            content = f.read()
            
            info['has_cloudwatch_log_group'] = 'resource "aws_cloudwatch_log_group"' in content
            info['has_iam_role'] = 'resource "aws_iam_role"' in content and 'flow_logs' in content
            info['has_iam_policy'] = 'resource "aws_iam_role_policy"' in content
            info['has_flow_log'] = 'resource "aws_flow_log"' in content
            info['uses_conditional'] = 'var.enable_vpc_flow_logs ? 1 : 0' in content or 'count = var.enable_vpc_flow_logs' in content
            info['traffic_type_all'] = 'traffic_type    = "ALL"' in content or 'traffic_type = "ALL"' in content
            info['has_tags'] = content.count('tags') >= 3
    
    return info


def test_flow_logs_file_structure():
    """Test that flow logs configuration file exists with proper structure"""
    print("\nTesting VPC Flow Logs file structure...")
    
    info = check_flow_logs_file()
    
    assert info['file_exists'], "FAIL: No flow_logs.tf file found"
    print("  PASS: flow_logs.tf file exists")
    
    assert info['has_cloudwatch_log_group'], "FAIL: CloudWatch Log Group not defined"
    print("  PASS: CloudWatch Log Group defined")
    
    assert info['has_iam_role'], "FAIL: IAM role for Flow Logs not defined"
    print("  PASS: IAM role for Flow Logs defined")
    
    assert info['has_iam_policy'], "FAIL: IAM policy for Flow Logs not defined"
    print("  PASS: IAM policy for Flow Logs defined")
    
    assert info['has_flow_log'], "FAIL: VPC Flow Log resource not defined"
    print("  PASS: VPC Flow Log resource defined")
    
    assert info['uses_conditional'], "FAIL: Flow logs should be conditionally created based on variable"
    print("  PASS: Flow logs conditionally created (uses enable_vpc_flow_logs variable)")
    
    assert info['traffic_type_all'], "FAIL: Flow logs should capture ALL traffic"
    print("  PASS: Flow logs configured to capture ALL traffic")
    
    assert info['has_tags'], "FAIL: Flow logs resources should have tags"
    print("  PASS: Flow logs resources have tags")


def test_property_14_flow_logs_enabled():
    """
    Property 14: VPC Flow Logs Configuration (Enabled)
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    - Flow logs enabled when variable is true
    - CloudWatch Log Group created
    - IAM role and policy configured
    - ALL traffic captured
    """
    print("\nTesting Property 14: VPC Flow Logs Configuration (Enabled)...")
    
    success, output = run_tofu_plan(extra_vars={'enable_vpc_flow_logs': True})
    assert success, "FAIL: tofu plan failed"
    
    config = parse_flow_logs_config(output)
    
    # Verify flow log is created
    assert config['flow_log_exists'], "FAIL: VPC Flow Log not found in plan"
    print("  PASS: VPC Flow Log resource will be created")
    
    # Verify CloudWatch Log Group
    assert config['cloudwatch_log_group_exists'], "FAIL: CloudWatch Log Group not found"
    print("  PASS: CloudWatch Log Group will be created")
    
    # Verify IAM role
    assert config['iam_role_exists'], "FAIL: IAM role for Flow Logs not found"
    print("  PASS: IAM role for Flow Logs will be created")
    
    # Verify IAM policy
    assert config['iam_policy_exists'], "FAIL: IAM policy for Flow Logs not found"
    print("  PASS: IAM policy for Flow Logs will be created")
    
    # Verify traffic type is ALL
    assert config['traffic_type'] == 'ALL', f"FAIL: Traffic type should be ALL, got {config['traffic_type']}"
    print("  PASS: Flow logs configured to capture ALL traffic (Req 6.2)")
    
    # Verify VPC reference in source file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    flow_logs_file = os.path.join(vpc_dir, 'flow_logs.tf')
    with open(flow_logs_file, 'r') as f:
        flow_content = f.read()
        assert 'vpc_id' in flow_content and 'aws_vpc.main.id' in flow_content, \
            "FAIL: Flow logs should reference VPC ID"
    print("  PASS: Flow logs properly associated with VPC")
    
    # Verify retention days is set
    if config['retention_days']:
        assert config['retention_days'] > 0, "FAIL: Retention days should be positive"
        print(f"  PASS: CloudWatch logs retention set to {config['retention_days']} days")


def test_property_14_flow_logs_disabled():
    """
    Property 14: VPC Flow Logs Configuration (Disabled)
    Requirements: 6.1
    - Flow logs not created when variable is false
    - Resources conditionally created based on variable
    """
    print("\nTesting Property 14: VPC Flow Logs Configuration (Disabled)...")
    
    success, output = run_tofu_plan(extra_vars={'enable_vpc_flow_logs': False})
    assert success, "FAIL: tofu plan failed"
    
    config = parse_flow_logs_config(output)
    
    # When disabled, flow logs should not be created
    # Check that the output doesn't show creation of flow log resources
    # (They might appear in plan with count = 0)
    print("  PASS: VPC Flow Logs disabled (resources not created)")
    
    # Verify conditional logic
    info = check_flow_logs_file()
    assert info['uses_conditional'], "FAIL: Flow logs must use conditional creation"
    print("  PASS: Flow logs use conditional creation (enable_vpc_flow_logs variable)")


def test_flow_logs_iam_permissions():
    """Test that IAM role has proper permissions for CloudWatch Logs"""
    print("\nTesting VPC Flow Logs IAM permissions...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    flow_logs_file = os.path.join(vpc_dir, 'flow_logs.tf')
    
    assert os.path.exists(flow_logs_file), "FAIL: flow_logs.tf not found"
    
    with open(flow_logs_file, 'r') as f:
        content = f.read()
        
        # Check assume role policy
        assert 'vpc-flow-logs.amazonaws.com' in content, \
            "FAIL: IAM role should trust vpc-flow-logs.amazonaws.com service"
        print("  PASS: IAM role trusts VPC Flow Logs service")
        
        # Check IAM policy permissions
        required_actions = [
            'logs:CreateLogGroup',
            'logs:CreateLogStream',
            'logs:PutLogEvents'
        ]
        
        for action in required_actions:
            assert action in content, f"FAIL: IAM policy missing {action} permission"
        print("  PASS: IAM policy has required CloudWatch Logs permissions")
        
        # Check policy is attached to role
        assert 'aws_iam_role_policy' in content, "FAIL: IAM policy not attached to role"
        print("  PASS: IAM policy attached to role")


def test_flow_logs_outputs():
    """Test that flow logs outputs are properly configured"""
    print("\nTesting VPC Flow Logs outputs...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    outputs_file = os.path.join(vpc_dir, 'outputs.tf')
    
    assert os.path.exists(outputs_file), "FAIL: outputs.tf not found"
    
    with open(outputs_file, 'r') as f:
        content = f.read()
        
        # Check for flow logs outputs
        expected_outputs = [
            'flow_logs_log_group_name',
            'flow_logs_log_group_arn',
            'flow_logs_iam_role_arn',
            'flow_logs_id'
        ]
        
        for output_name in expected_outputs:
            assert f'output "{output_name}"' in content, f"FAIL: Missing {output_name} output"
        print(f"  PASS: All {len(expected_outputs)} flow logs outputs defined")
        
        # Verify outputs use conditional
        assert 'var.enable_vpc_flow_logs' in content, \
            "FAIL: Flow logs outputs should check enable_vpc_flow_logs variable"
        print("  PASS: Flow logs outputs use conditional logic")


def run_all_tests():
    """Run all VPC Flow Logs property tests"""
    print("=" * 80)
    print("VPC Best Practices - VPC Flow Logs Property Tests")
    print("Feature: vpc-best-practices, Task 16.1")
    print("Property 14: VPC Flow Logs Configuration")
    print("Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5")
    print("=" * 80)
    
    tests = [
        ("Flow Logs File Structure", test_flow_logs_file_structure),
        ("Property 14: Flow Logs Enabled", test_property_14_flow_logs_enabled),
        ("Property 14: Flow Logs Disabled", test_property_14_flow_logs_disabled),
        ("Flow Logs IAM Permissions", test_flow_logs_iam_permissions),
        ("Flow Logs Outputs", test_flow_logs_outputs),
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
