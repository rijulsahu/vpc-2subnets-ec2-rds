#!/usr/bin/env python3
"""
VPC Best Practices - Internet Gateway Property Tests
Feature: vpc-best-practices, Task 6.1
Property 6: Internet Gateway Attachment Compliance
Validates: Requirements 3.1, 3.7

Tests verify:
- Exactly one Internet Gateway per VPC
- Internet Gateway is properly attached to VPC
- Internet Gateway has proper naming and tagging
- IGW configuration follows best practices
"""

import os
import re
import subprocess
from typing import Tuple, Dict, Optional


def run_tofu_plan() -> Tuple[bool, Dict]:
    """Run OpenTofu plan and parse Internet Gateway information"""
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
        
        output = result.stdout
        
        # Extract Internet Gateway information
        igw_info = {
            'exists': False,
            'vpc_id_reference': None,
            'has_tags': False,
            'has_name_tag': False,
            'count': 0
        }
        
        # Look for Internet Gateway resource
        lines = output.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if '# aws_internet_gateway.' in line and 'will be created' in line:
                igw_info['exists'] = True
                igw_info['count'] += 1
                
                # Collect the IGW block (next 30 lines)
                block_lines = []
                j = i
                while j < len(lines) and j < i + 30:
                    block_lines.append(lines[j])
                    j += 1
                    if lines[j].strip().startswith('# aws_') and 'aws_internet_gateway' not in lines[j]:
                        break
                
                block_text = '\n'.join(block_lines)
                
                # Check for VPC ID reference
                vpc_id_match = re.search(r'vpc_id\s*=\s*aws_vpc\.(\w+)\.id', block_text)
                if vpc_id_match:
                    igw_info['vpc_id_reference'] = vpc_id_match.group(1)
                
                # Check for tags
                if 'tags' in block_text:
                    igw_info['has_tags'] = True
                if '"Name"' in block_text or '+ "Name"' in block_text:
                    igw_info['has_name_tag'] = True
            
            i += 1
        
        return result.returncode == 0, igw_info
        
    except Exception as e:
        print(f"  ERROR running tofu plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}


def check_igw_in_config() -> Dict:
    """Check Internet Gateway configuration in source files"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    config_info = {
        'igw_resource_exists': False,
        'attached_to_vpc': False,
        'has_tags': False,
        'uses_common_tags': False,
        'igw_count': 0
    }
    
    # Check main.tf for IGW resource
    main_tf = os.path.join(vpc_dir, 'main.tf')
    if os.path.exists(main_tf):
        with open(main_tf, 'r') as f:
            content = f.read()
            
            # Count IGW resources
            igw_matches = re.findall(r'resource\s+"aws_internet_gateway"\s+"(\w+)"', content)
            config_info['igw_count'] = len(igw_matches)
            config_info['igw_resource_exists'] = len(igw_matches) > 0
            
            # Check for VPC attachment
            if 'vpc_id = aws_vpc.' in content:
                config_info['attached_to_vpc'] = True
            
            # Check for tagging
            if 'tags' in content and 'aws_internet_gateway' in content:
                config_info['has_tags'] = True
            
            if 'merge(' in content and 'local.common_tags' in content and 'aws_internet_gateway' in content:
                config_info['uses_common_tags'] = True
    
    return config_info


def test_igw_resource_definition():
    """Test that Internet Gateway resource is properly defined"""
    print("\nTesting Internet Gateway resource definition...")
    
    config = check_igw_in_config()
    
    assert config['igw_resource_exists'], "FAIL: No Internet Gateway resource defined"
    print("  PASS: Internet Gateway resource defined")
    
    assert config['igw_count'] == 1, f"FAIL: Expected exactly 1 IGW, found {config['igw_count']}"
    print("  PASS: Exactly one Internet Gateway defined")
    
    assert config['attached_to_vpc'], "FAIL: Internet Gateway not attached to VPC"
    print("  PASS: Internet Gateway attached to VPC (vpc_id = aws_vpc.*.id)")
    
    assert config['has_tags'], "FAIL: Internet Gateway has no tags"
    print("  PASS: Internet Gateway has tags configured")
    
    assert config['uses_common_tags'], "FAIL: Internet Gateway doesn't use common tags"
    print("  PASS: Internet Gateway uses merge() with local.common_tags")


def test_property_6_igw_attachment():
    """
    Property 6: Internet Gateway Attachment Compliance
    Requirements: 3.1, 3.7
    - Exactly one Internet Gateway per VPC
    - IGW is attached to VPC
    - Proper naming and tagging
    """
    print("\nTesting Property 6: Internet Gateway Attachment...")
    
    # Check configuration first (more reliable than plan output for references)
    config = check_igw_in_config()
    
    assert config['igw_resource_exists'], "FAIL: No Internet Gateway defined"
    print(f"  PASS: Internet Gateway resource exists")
    
    assert config['igw_count'] == 1, f"FAIL: Expected 1 IGW, found {config['igw_count']}"
    print(f"  PASS: Exactly one Internet Gateway defined")
    
    assert config['attached_to_vpc'], "FAIL: IGW not attached to VPC in configuration"
    print(f"  PASS: IGW attached to VPC (vpc_id = aws_vpc.*.id)")
    
    # Now check plan output
    success, igw_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    assert igw_info['exists'], "FAIL: No Internet Gateway found in plan"
    print(f"  PASS: Internet Gateway exists in plan")
    
    assert igw_info['count'] == 1, f"FAIL: Expected 1 IGW in plan, found {igw_info['count']}"
    print(f"  PASS: Plan shows exactly one Internet Gateway")
    
    # Test: Proper tagging
    assert igw_info['has_tags'], "FAIL: IGW has no tags"
    print("  PASS: IGW has tags configured")
    
    assert igw_info['has_name_tag'], "FAIL: IGW missing Name tag"
    print("  PASS: IGW has Name tag for identification")


def test_igw_outputs():
    """Test that IGW outputs are properly configured"""
    print("\nTesting Internet Gateway outputs...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    outputs_file = os.path.join(vpc_dir, 'outputs.tf')
    
    assert os.path.exists(outputs_file), "FAIL: outputs.tf not found"
    
    with open(outputs_file, 'r') as f:
        content = f.read()
        
        # Check for IGW ID output
        assert 'output "internet_gateway_id"' in content, "FAIL: Missing internet_gateway_id output"
        print("  PASS: internet_gateway_id output defined")
        
        # Check output references IGW resource
        assert 'aws_internet_gateway.main.id' in content, "FAIL: Output doesn't reference IGW resource"
        print("  PASS: Output references aws_internet_gateway.main.id")


def run_all_tests():
    """Run all Internet Gateway property tests"""
    print("=" * 80)
    print("VPC Best Practices - Internet Gateway Property Tests")
    print("Feature: vpc-best-practices, Task 6.1")
    print("Property 6: Internet Gateway Attachment Compliance")
    print("Validates: Requirements 3.1, 3.7")
    print("=" * 80)
    
    tests = [
        ("IGW Resource Definition", test_igw_resource_definition),
        ("Property 6: IGW Attachment", test_property_6_igw_attachment),
        ("IGW Outputs", test_igw_outputs),
    ]
    
    results = []
    issues = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, True))
            print(f"✓ PASS: {test_name}")
        except AssertionError as e:
            results.append((test_name, False))
            issues.append(f"  - {test_name}: {str(e)}")
            print(f"✗ FAIL: {test_name}")
            print(f"  {str(e)}")
        except Exception as e:
            results.append((test_name, False))
            issues.append(f"  - {test_name}: Unexpected error: {str(e)}")
            print(f"✗ ERROR: {test_name}")
            print(f"  {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
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
