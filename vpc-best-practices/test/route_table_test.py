#!/usr/bin/env python3
"""
VPC Best Practices - Route Table Property Tests
Feature: vpc-best-practices, Task 9.1
Property 20: Route Table Associations
Validates: Requirements 3.7, 3.2, 3.5

Tests verify:
- All subnets have explicit route table associations
- Public subnets route to Internet Gateway
- Private subnets route to NAT Gateway
- Routing configuration works across NAT strategies
"""

import os
import re
import subprocess
from typing import Tuple, Dict, List


def run_tofu_plan(var_file: str = None) -> Tuple[bool, Dict]:
    """Run OpenTofu plan and parse route table information"""
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
        
        # Parse route table information
        route_info = {
            'public_route_tables': [],
            'private_route_tables': [],
            'public_routes': [],
            'private_routes': [],
            'public_associations': [],
            'private_associations': [],
            'strategy': None
        }
        
        # Extract strategy
        strategy_match = re.search(r'nat_gateway_strategy\s*=\s*"(\w+)"', output)
        if strategy_match:
            route_info['strategy'] = strategy_match.group(1)
        
        lines = output.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for public route table (no index since it's singular)
            if 'aws_route_table.public' in line and 'will be created' in line:
                route_info['public_route_tables'].append({'exists': True})
            
            # Look for private route tables
            priv_rt_match = re.search(r'# aws_route_table\.private\[(\d+)\]', line)
            if priv_rt_match:
                idx = int(priv_rt_match.group(1))
                
                # Get block to extract tags
                block_lines = []
                j = i
                while j < len(lines) and j < i + 30:
                    block_lines.append(lines[j])
                    j += 1
                    if lines[j].strip().startswith('# aws_') and 'aws_route_table' not in lines[j]:
                        break
                
                block_text = '\n'.join(block_lines)
                az_match = re.search(r'"AZ"\s*=\s*"([^"]+)"', block_text)
                
                route_info['private_route_tables'].append({
                    'index': idx,
                    'az': az_match.group(1) if az_match else None
                })
            
            # Look for public internet route (no index since it's singular)
            if 'aws_route.public_internet' in line and 'will be created' in line:
                # Get next few lines to extract details
                block_lines = []
                j = i
                while j < len(lines) and j < i + 15:
                    block_lines.append(lines[j])
                    j += 1
                
                block_text = '\n'.join(block_lines)
                
                route_info['public_routes'].append({
                    'destination': '0.0.0.0/0' if 'destination_cidr_block = "0.0.0.0/0"' in block_text else None,
                    'target': 'igw' if 'gateway_id' in block_text else None
                })
            
            # Look for private NAT routes
            priv_route_match = re.search(r'# aws_route\.private_nat\[(\d+)\]', line)
            if priv_route_match:
                idx = int(priv_route_match.group(1))
                
                # Get block
                block_lines = []
                j = i
                while j < len(lines) and j < i + 15:
                    block_lines.append(lines[j])
                    j += 1
                
                block_text = '\n'.join(block_lines)
                
                route_info['private_routes'].append({
                    'index': idx,
                    'destination': '0.0.0.0/0' if 'destination_cidr_block = "0.0.0.0/0"' in block_text else None,
                    'target': 'nat' if 'nat_gateway_id' in block_text else None
                })
            
            # Look for public route table associations
            pub_assoc_match = re.search(r'# aws_route_table_association\.public\[(\d+)\]', line)
            if pub_assoc_match:
                idx = int(pub_assoc_match.group(1))
                route_info['public_associations'].append({'index': idx})
            
            # Look for private route table associations
            priv_assoc_match = re.search(r'# aws_route_table_association\.private\[(\d+)\]', line)
            if priv_assoc_match:
                idx = int(priv_assoc_match.group(1))
                route_info['private_associations'].append({'index': idx})
            
            i += 1
        
        return result.returncode == 0, route_info
        
    except Exception as e:
        print(f"  ERROR running tofu plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}


def check_route_table_config() -> Dict:
    """Check route table configuration in source files"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    config_info = {
        'public_rt_exists': False,
        'private_rt_exists': False,
        'public_route_to_igw': False,
        'private_route_to_nat': False,
        'public_associations_exist': False,
        'private_associations_exist': False,
        'uses_count_for_associations': False
    }
    
    # Check route_tables.tf
    rt_file = os.path.join(vpc_dir, 'route_tables.tf')
    if os.path.exists(rt_file):
        with open(rt_file, 'r') as f:
            content = f.read()
            
            config_info['public_rt_exists'] = 'resource "aws_route_table" "public"' in content
            config_info['private_rt_exists'] = 'resource "aws_route_table" "private"' in content
            config_info['public_route_to_igw'] = 'gateway_id             = aws_internet_gateway.main.id' in content
            config_info['private_route_to_nat'] = 'nat_gateway_id         = aws_nat_gateway.main[count.index].id' in content
            config_info['public_associations_exist'] = 'resource "aws_route_table_association" "public"' in content
            config_info['private_associations_exist'] = 'resource "aws_route_table_association" "private"' in content
            config_info['uses_count_for_associations'] = 'count = local.az_count' in content
    
    return config_info


def test_route_table_resource_definition():
    """Test that route table resources are properly defined"""
    print("\nTesting route table resource definitions...")
    
    config = check_route_table_config()
    
    assert config['public_rt_exists'], "FAIL: No public route table resource defined"
    print("  PASS: Public route table resource defined")
    
    assert config['private_rt_exists'], "FAIL: No private route table resource defined"
    print("  PASS: Private route table resource defined")
    
    assert config['public_route_to_igw'], "FAIL: Public route doesn't point to IGW"
    print("  PASS: Public route configured to Internet Gateway")
    
    assert config['private_route_to_nat'], "FAIL: Private route doesn't point to NAT Gateway"
    print("  PASS: Private route configured to NAT Gateway")
    
    assert config['public_associations_exist'], "FAIL: No public subnet associations defined"
    print("  PASS: Public route table associations defined")
    
    assert config['private_associations_exist'], "FAIL: No private subnet associations defined"
    print("  PASS: Private route table associations defined")
    
    assert config['uses_count_for_associations'], "FAIL: Associations don't use count = local.az_count"
    print("  PASS: Route table associations use count for multi-AZ")


def test_property_20_public_routing():
    """
    Property 20: Route Table Associations - Public Routing
    Requirements: 3.2, 3.7
    - Public route table exists
    - Route to IGW (0.0.0.0/0 -> IGW)
    - All public subnets associated
    """
    print("\nTesting Property 20: Public Routing Configuration...")
    
    success, route_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Verify public route table exists
    assert len(route_info['public_route_tables']) == 1, f"FAIL: Expected 1 public route table, found {len(route_info['public_route_tables'])}"
    print(f"  PASS: Public route table exists")
    
    # Verify public route to IGW
    assert len(route_info['public_routes']) >= 1, "FAIL: No public route to IGW found"
    pub_route = route_info['public_routes'][0]
    assert pub_route['destination'] == '0.0.0.0/0', "FAIL: Public route destination is not 0.0.0.0/0"
    assert pub_route['target'] == 'igw', "FAIL: Public route target is not IGW"
    print(f"  PASS: Public route configured (0.0.0.0/0 -> IGW)")
    
    # Verify public subnet associations (should be 2 for 2 AZs)
    pub_assoc_count = len(route_info['public_associations'])
    assert pub_assoc_count == 2, f"FAIL: Expected 2 public associations, found {pub_assoc_count}"
    print(f"  PASS: All {pub_assoc_count} public subnets associated with route table")


def test_property_20_private_routing_per_az():
    """
    Property 20: Route Table Associations - Private Routing (per_az)
    Requirements: 3.5, 3.7, 7.5
    - Private route tables per AZ
    - Routes to NAT Gateways (0.0.0.0/0 -> NAT)
    - Each private subnet associated with its AZ's route table
    """
    print("\nTesting Property 20: Private Routing (per_az strategy)...")
    
    success, route_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Verify strategy
    assert route_info['strategy'] == 'per_az', f"FAIL: Expected per_az strategy, got {route_info['strategy']}"
    print(f"  PASS: Strategy is 'per_az'")
    
    # Verify private route tables (should be 2 for per_az with 2 AZs)
    priv_rt_count = len(route_info['private_route_tables'])
    assert priv_rt_count == 2, f"FAIL: Expected 2 private route tables for per_az, found {priv_rt_count}"
    print(f"  PASS: {priv_rt_count} private route tables (one per AZ)")
    
    # Verify each route table has AZ tag
    azs = [rt['az'] for rt in route_info['private_route_tables']]
    assert all(az for az in azs), "FAIL: Not all private route tables have AZ tags"
    assert len(set(azs)) == len(azs), "FAIL: Duplicate AZ tags found"
    print(f"  PASS: Each private route table tagged with unique AZ")
    
    # Verify private routes to NAT Gateways
    priv_route_count = len(route_info['private_routes'])
    assert priv_route_count == 2, f"FAIL: Expected 2 private routes, found {priv_route_count}"
    
    for route in route_info['private_routes']:
        assert route['destination'] == '0.0.0.0/0', f"FAIL: Private route destination is not 0.0.0.0/0"
        assert route['target'] == 'nat', f"FAIL: Private route target is not NAT Gateway"
    print(f"  PASS: {priv_route_count} private routes configured (0.0.0.0/0 -> NAT)")
    
    # Verify private subnet associations
    priv_assoc_count = len(route_info['private_associations'])
    assert priv_assoc_count == 2, f"FAIL: Expected 2 private associations, found {priv_assoc_count}"
    print(f"  PASS: All {priv_assoc_count} private subnets associated with route tables")


def test_property_20_private_routing_single():
    """
    Property 20: Route Table Associations - Private Routing (single)
    Requirements: 3.5, 3.7, 8.1
    - Single private route table
    - Route to NAT Gateway (0.0.0.0/0 -> NAT)
    - All private subnets share the route table
    """
    print("\nTesting Property 20: Private Routing (single strategy)...")
    
    success, route_info = run_tofu_plan("dev.tfvars.example")
    assert success, "FAIL: tofu plan with single strategy failed"
    
    # Verify strategy
    assert route_info['strategy'] == 'single', f"FAIL: Expected single strategy, got {route_info['strategy']}"
    print(f"  PASS: Strategy is 'single'")
    
    # Verify single private route table
    priv_rt_count = len(route_info['private_route_tables'])
    assert priv_rt_count == 1, f"FAIL: Expected 1 private route table for single, found {priv_rt_count}"
    print(f"  PASS: {priv_rt_count} private route table (shared)")
    
    # Verify AZ tag is "shared" for single strategy
    rt = route_info['private_route_tables'][0]
    assert rt['az'] == 'shared', f"FAIL: Expected 'shared' AZ tag, got '{rt['az']}'"
    print(f"  PASS: Private route table tagged with AZ = 'shared'")
    
    # Verify single private route to NAT Gateway
    priv_route_count = len(route_info['private_routes'])
    assert priv_route_count == 1, f"FAIL: Expected 1 private route, found {priv_route_count}"
    
    route = route_info['private_routes'][0]
    assert route['destination'] == '0.0.0.0/0', f"FAIL: Private route destination is not 0.0.0.0/0"
    assert route['target'] == 'nat', f"FAIL: Private route target is not NAT Gateway"
    print(f"  PASS: Private route configured (0.0.0.0/0 -> NAT)")
    
    # Verify both private subnets still get associations
    priv_assoc_count = len(route_info['private_associations'])
    assert priv_assoc_count == 2, f"FAIL: Expected 2 private associations, found {priv_assoc_count}"
    print(f"  PASS: All {priv_assoc_count} private subnets associated with shared route table")


def test_route_table_outputs():
    """Test that route table outputs are properly configured"""
    print("\nTesting route table outputs...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    outputs_file = os.path.join(vpc_dir, 'outputs.tf')
    
    assert os.path.exists(outputs_file), "FAIL: outputs.tf not found"
    
    with open(outputs_file, 'r') as f:
        content = f.read()
        
        # Check for public route table outputs
        assert 'output "public_route_table_id"' in content, "FAIL: Missing public_route_table_id output"
        print("  PASS: public_route_table_id output defined")
        
        assert 'output "public_route_table_associations"' in content, "FAIL: Missing public_route_table_associations output"
        print("  PASS: public_route_table_associations output defined")
        
        # Check for private route table outputs
        assert 'output "private_route_table_ids"' in content, "FAIL: Missing private_route_table_ids output"
        print("  PASS: private_route_table_ids output defined")
        
        assert 'output "private_route_table_associations"' in content, "FAIL: Missing private_route_table_associations output"
        print("  PASS: private_route_table_associations output defined")
        
        # Verify outputs reference correct resources
        assert 'aws_route_table.public' in content, "FAIL: Outputs don't reference public route table"
        print("  PASS: Outputs reference aws_route_table.public")
        
        assert 'aws_route_table.private' in content, "FAIL: Outputs don't reference private route tables"
        print("  PASS: Outputs reference aws_route_table.private")


def run_all_tests():
    """Run all route table property tests"""
    print("=" * 80)
    print("VPC Best Practices - Route Table Property Tests")
    print("Feature: vpc-best-practices, Task 9.1")
    print("Property 20: Route Table Associations")
    print("Validates: Requirements 3.7, 3.2, 3.5")
    print("=" * 80)
    
    tests = [
        ("Route Table Resource Definition", test_route_table_resource_definition),
        ("Property 20: Public Routing", test_property_20_public_routing),
        ("Property 20: Private Routing (per_az)", test_property_20_private_routing_per_az),
        ("Property 20: Private Routing (single)", test_property_20_private_routing_single),
        ("Route Table Outputs", test_route_table_outputs),
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
