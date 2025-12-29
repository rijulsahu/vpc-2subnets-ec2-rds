#!/usr/bin/env python3
"""
VPC Best Practices - NAT Gateway Property Tests
Feature: vpc-best-practices, Tasks 7.1, 7.2
Property 5: NAT Gateway High Availability Compliance
Property 16: Cost Optimization Options
Validates: Requirements 3.3, 3.4, 3.6, 7.2, 8.1, 8.3

Tests verify:
- NAT Gateway HA strategy (per_az vs single)
- Elastic IP allocation for each NAT Gateway
- NAT Gateway placement in public subnets
- Cost optimization with single NAT strategy
"""

import os
import re
import subprocess
from typing import Tuple, Dict, List


def run_tofu_plan(var_file: str = None) -> Tuple[bool, Dict]:
    """Run OpenTofu plan and parse NAT Gateway information"""
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
        
        # Parse NAT Gateway and EIP information
        nat_info = {
            'nat_gateways': [],
            'eips': [],
            'strategy': None,
            'total_resources': 0
        }
        
        # Extract strategy from output
        strategy_match = re.search(r'nat_gateway_strategy\s*=\s*"(\w+)"', output)
        if strategy_match:
            nat_info['strategy'] = strategy_match.group(1)
        
        # Count resources in plan
        plan_match = re.search(r'Plan:\s+(\d+)\s+to\s+add', output, re.IGNORECASE)
        if plan_match:
            nat_info['total_resources'] = int(plan_match.group(1))
        else:
            # Try alternate pattern
            plan_match2 = re.search(r'(\d+)\s+to\s+add', output, re.IGNORECASE)
            if plan_match2:
                nat_info['total_resources'] = int(plan_match2.group(1))
        
        lines = output.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for NAT Gateway resources
            nat_match = re.search(r'# aws_nat_gateway\.main\[(\d+)\]', line)
            if nat_match:
                nat_idx = int(nat_match.group(1))
                
                # Collect NAT Gateway block
                block_lines = []
                j = i
                while j < len(lines) and j < i + 40:
                    block_lines.append(lines[j])
                    j += 1
                    if lines[j].strip().startswith('# aws_') and 'aws_nat_gateway' not in lines[j]:
                        break
                
                block_text = '\n'.join(block_lines)
                
                nat_data = {
                    'index': nat_idx,
                    'subnet_id': None,
                    'allocation_id': None,
                    'connectivity_type': None,
                    'az': None,
                    'strategy_tag': None
                }
                
                # Extract connectivity_type
                conn_match = re.search(r'connectivity_type\s*=\s*"([^"]+)"', block_text)
                if conn_match:
                    nat_data['connectivity_type'] = conn_match.group(1)
                
                # Extract AZ from tags
                az_match = re.search(r'"AZ"\s*=\s*"([^"]+)"', block_text)
                if az_match:
                    nat_data['az'] = az_match.group(1)
                
                # Extract Strategy from tags
                strat_match = re.search(r'"Strategy"\s*=\s*"([^"]+)"', block_text)
                if strat_match:
                    nat_data['strategy_tag'] = strat_match.group(1)
                
                # Check for subnet reference
                if 'subnet_id' in block_text:
                    nat_data['subnet_id'] = 'referenced'
                
                # Check for allocation reference
                if 'allocation_id' in block_text:
                    nat_data['allocation_id'] = 'referenced'
                
                nat_info['nat_gateways'].append(nat_data)
            
            # Look for EIP resources
            eip_match = re.search(r'# aws_eip\.nat\[(\d+)\]', line)
            if eip_match:
                eip_idx = int(eip_match.group(1))
                
                # Collect EIP block
                block_lines = []
                j = i
                while j < len(lines) and j < i + 30:
                    block_lines.append(lines[j])
                    j += 1
                    if lines[j].strip().startswith('# aws_') and 'aws_eip' not in lines[j]:
                        break
                
                block_text = '\n'.join(block_lines)
                
                eip_data = {
                    'index': eip_idx,
                    'domain': None,
                    'az': None
                }
                
                # Extract domain
                domain_match = re.search(r'domain\s*=\s*"([^"]+)"', block_text)
                if domain_match:
                    eip_data['domain'] = domain_match.group(1)
                
                # Extract AZ from tags
                az_match = re.search(r'"AZ"\s*=\s*"([^"]+)"', block_text)
                if az_match:
                    eip_data['az'] = az_match.group(1)
                
                nat_info['eips'].append(eip_data)
            
            i += 1
        
        return result.returncode == 0, nat_info
        
    except Exception as e:
        print(f"  ERROR running tofu plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}


def check_nat_config() -> Dict:
    """Check NAT Gateway configuration in source files"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    
    config_info = {
        'nat_resource_exists': False,
        'eip_resource_exists': False,
        'uses_nat_count': False,
        'has_connectivity_type': False,
        'has_depends_on_igw': False,
        'uses_public_subnet': False,
        'strategy_in_tags': False
    }
    
    # Check nat_gateway.tf
    nat_file = os.path.join(vpc_dir, 'nat_gateway.tf')
    if os.path.exists(nat_file):
        with open(nat_file, 'r') as f:
            content = f.read()
            
            config_info['nat_resource_exists'] = 'resource "aws_nat_gateway"' in content
            config_info['eip_resource_exists'] = 'resource "aws_eip"' in content
            config_info['uses_nat_count'] = 'count = local.nat_gateway_count' in content
            config_info['has_connectivity_type'] = 'connectivity_type = "public"' in content
            config_info['has_depends_on_igw'] = 'depends_on = [aws_internet_gateway.main]' in content
            config_info['uses_public_subnet'] = 'subnet_id         = aws_subnet.public[count.index].id' in content
            config_info['strategy_in_tags'] = 'Strategy' in content
    
    return config_info


def test_nat_gateway_resource_definition():
    """Test that NAT Gateway and EIP resources are properly defined"""
    print("\nTesting NAT Gateway resource definitions...")
    
    config = check_nat_config()
    
    assert config['nat_resource_exists'], "FAIL: No NAT Gateway resource defined"
    print("  PASS: NAT Gateway resource defined")
    
    assert config['eip_resource_exists'], "FAIL: No Elastic IP resource defined"
    print("  PASS: Elastic IP resource defined")
    
    assert config['uses_nat_count'], "FAIL: NAT Gateway doesn't use local.nat_gateway_count"
    print("  PASS: NAT Gateway uses count = local.nat_gateway_count")
    
    assert config['has_connectivity_type'], "FAIL: connectivity_type not set to 'public'"
    print("  PASS: connectivity_type = 'public'")
    
    assert config['uses_public_subnet'], "FAIL: NAT Gateway not placed in public subnet"
    print("  PASS: NAT Gateway deployed in public subnets")
    
    assert config['has_depends_on_igw'], "FAIL: NAT Gateway missing dependency on IGW"
    print("  PASS: NAT Gateway has depends_on = [aws_internet_gateway.main]")
    
    assert config['strategy_in_tags'], "FAIL: NAT Gateway tags don't include Strategy"
    print("  PASS: NAT Gateway tags include Strategy")


def test_property_5_nat_ha_per_az():
    """
    Property 5: NAT Gateway High Availability (per_az strategy)
    Requirements: 3.3, 3.4, 3.6, 7.2
    - per_az strategy creates one NAT Gateway per AZ
    - Each NAT Gateway in different public subnet
    - Each NAT Gateway has its own Elastic IP
    """
    print("\nTesting Property 5: NAT Gateway HA (per_az strategy)...")
    
    # Test with default (per_az) strategy
    success, nat_info = run_tofu_plan()
    assert success, "FAIL: tofu plan failed"
    
    # Verify strategy
    assert nat_info['strategy'] == 'per_az', f"FAIL: Expected per_az strategy, got {nat_info['strategy']}"
    print(f"  PASS: Strategy is 'per_az'")
    
    # Verify NAT Gateway count (should be 2 for 2 AZs)
    nat_count = len(nat_info['nat_gateways'])
    assert nat_count == 2, f"FAIL: Expected 2 NAT Gateways for HA, found {nat_count}"
    print(f"  PASS: Created {nat_count} NAT Gateways (one per AZ)")
    
    # Verify EIP count matches NAT count
    eip_count = len(nat_info['eips'])
    assert eip_count == nat_count, f"FAIL: EIP count ({eip_count}) doesn't match NAT count ({nat_count})"
    print(f"  PASS: {eip_count} Elastic IPs created (one per NAT Gateway)")
    
    # Verify each NAT is in a different AZ
    nat_azs = [nat['az'] for nat in nat_info['nat_gateways'] if nat['az']]
    assert len(nat_azs) == len(set(nat_azs)), "FAIL: NAT Gateways not distributed across different AZs"
    print(f"  PASS: NAT Gateways distributed across {len(set(nat_azs))} different AZs")
    
    # Verify connectivity type
    for nat in nat_info['nat_gateways']:
        assert nat['connectivity_type'] == 'public', f"FAIL: NAT Gateway has wrong connectivity_type"
    print(f"  PASS: All NAT Gateways have connectivity_type = 'public'")
    
    # Verify subnet references
    for nat in nat_info['nat_gateways']:
        assert nat['subnet_id'] == 'referenced', f"FAIL: NAT Gateway {nat['index']} missing subnet_id"
    print(f"  PASS: All NAT Gateways have subnet_id references")
    
    # Verify allocation references
    for nat in nat_info['nat_gateways']:
        assert nat['allocation_id'] == 'referenced', f"FAIL: NAT Gateway {nat['index']} missing allocation_id"
    print(f"  PASS: All NAT Gateways have allocation_id (EIP) references")


def test_property_5_nat_single():
    """
    Property 5: NAT Gateway High Availability (single strategy)
    Requirements: 3.3, 8.1
    - single strategy creates only one NAT Gateway
    - Single NAT Gateway in first public subnet
    - One Elastic IP for the NAT Gateway
    """
    print("\nTesting Property 5: NAT Gateway (single strategy)...")
    
    # Test with single strategy
    success, nat_info = run_tofu_plan("dev.tfvars.example")
    assert success, "FAIL: tofu plan with single strategy failed"
    
    # Verify strategy
    assert nat_info['strategy'] == 'single', f"FAIL: Expected single strategy, got {nat_info['strategy']}"
    print(f"  PASS: Strategy is 'single'")
    
    # Verify NAT Gateway count (should be 1 for cost optimization)
    nat_count = len(nat_info['nat_gateways'])
    assert nat_count == 1, f"FAIL: Expected 1 NAT Gateway for single strategy, found {nat_count}"
    print(f"  PASS: Created {nat_count} NAT Gateway (cost-optimized)")
    
    # Verify EIP count matches NAT count
    eip_count = len(nat_info['eips'])
    assert eip_count == 1, f"FAIL: Expected 1 EIP for single strategy, found {eip_count}"
    print(f"  PASS: {eip_count} Elastic IP created")
    
    # Verify NAT is index 0 (first AZ)
    nat = nat_info['nat_gateways'][0]
    assert nat['index'] == 0, f"FAIL: Single NAT should be at index 0, found {nat['index']}"
    print(f"  PASS: NAT Gateway deployed in first availability zone")
    
    # Verify strategy tag matches
    assert nat['strategy_tag'] == 'single', f"FAIL: NAT Gateway Strategy tag is '{nat['strategy_tag']}', expected 'single'"
    print(f"  PASS: NAT Gateway tagged with Strategy = 'single'")


def test_property_16_cost_optimization():
    """
    Property 16: Cost Optimization Options
    Requirements: 8.1, 8.3
    - single strategy minimizes NAT Gateway resources
    - Reduced resource count compared to per_az
    - Single NAT configuration saves costs
    """
    print("\nTesting Property 16: Cost Optimization...")
    
    # Get resource count for per_az strategy
    success_per_az, nat_info_per_az = run_tofu_plan()
    assert success_per_az, "FAIL: tofu plan with per_az strategy failed"
    
    # Get resource count for single strategy
    success_single, nat_info_single = run_tofu_plan("dev.tfvars.example")
    assert success_single, "FAIL: tofu plan with single strategy failed"
    
    # Compare resource counts
    per_az_count = nat_info_per_az['total_resources']
    single_count = nat_info_single['total_resources']
    
    print(f"  INFO: per_az strategy creates {per_az_count} resources")
    print(f"  INFO: single strategy creates {single_count} resources")
    
    # If resource count parsing failed, use NAT+EIP count instead
    if per_az_count == 0 or single_count == 0:
        per_az_count = len(nat_info_per_az['nat_gateways']) + len(nat_info_per_az['eips'])
        single_count = len(nat_info_single['nat_gateways']) + len(nat_info_single['eips'])
        print(f"  INFO: Using NAT+EIP count instead: per_az={per_az_count}, single={single_count}")
    
    assert single_count < per_az_count, f"FAIL: single strategy ({single_count}) should use fewer resources than per_az ({per_az_count})"
    print(f"  PASS: single strategy reduces resource count by {per_az_count - single_count}")
    
    # Verify NAT Gateway count reduction
    per_az_nats = len(nat_info_per_az['nat_gateways'])
    single_nats = len(nat_info_single['nat_gateways'])
    
    assert single_nats < per_az_nats, f"FAIL: single strategy should use fewer NAT Gateways"
    print(f"  PASS: NAT Gateways reduced from {per_az_nats} (per_az) to {single_nats} (single)")
    
    # Verify EIP count reduction
    per_az_eips = len(nat_info_per_az['eips'])
    single_eips = len(nat_info_single['eips'])
    
    assert single_eips < per_az_eips, f"FAIL: single strategy should use fewer EIPs"
    print(f"  PASS: Elastic IPs reduced from {per_az_eips} (per_az) to {single_eips} (single)")
    
    # Calculate cost savings (NAT Gateway + EIP reduction)
    nat_savings = per_az_nats - single_nats
    eip_savings = per_az_eips - single_eips
    
    print(f"  PASS: Cost optimization achieves {nat_savings} NAT Gateway + {eip_savings} EIP savings")


def test_nat_gateway_outputs():
    """Test that NAT Gateway outputs are properly configured"""
    print("\nTesting NAT Gateway outputs...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    vpc_dir = os.path.dirname(test_dir)
    outputs_file = os.path.join(vpc_dir, 'outputs.tf')
    
    assert os.path.exists(outputs_file), "FAIL: outputs.tf not found"
    
    with open(outputs_file, 'r') as f:
        content = f.read()
        
        # Check for NAT Gateway outputs
        assert 'output "nat_gateway_ids"' in content, "FAIL: Missing nat_gateway_ids output"
        print("  PASS: nat_gateway_ids output defined")
        
        assert 'output "nat_gateway_public_ips"' in content, "FAIL: Missing nat_gateway_public_ips output"
        print("  PASS: nat_gateway_public_ips output defined")
        
        assert 'output "nat_gateway_strategy"' in content, "FAIL: Missing nat_gateway_strategy output"
        print("  PASS: nat_gateway_strategy output defined")
        
        assert 'output "nat_gateway_count"' in content, "FAIL: Missing nat_gateway_count output"
        print("  PASS: nat_gateway_count output defined")
        
        # Verify outputs reference correct resources
        assert 'aws_nat_gateway.main' in content, "FAIL: Outputs don't reference NAT Gateway resource"
        print("  PASS: Outputs reference aws_nat_gateway.main")
        
        assert 'aws_eip.nat' in content, "FAIL: Outputs don't reference EIP resource"
        print("  PASS: Outputs reference aws_eip.nat")


def run_all_tests():
    """Run all NAT Gateway property tests"""
    print("=" * 80)
    print("VPC Best Practices - NAT Gateway Property Tests")
    print("Feature: vpc-best-practices, Tasks 7.1, 7.2")
    print("Property 5: NAT Gateway High Availability Compliance")
    print("Property 16: Cost Optimization Options")
    print("Validates: Requirements 3.3, 3.4, 3.6, 7.2, 8.1, 8.3")
    print("=" * 80)
    
    tests = [
        ("NAT Gateway Resource Definition", test_nat_gateway_resource_definition),
        ("Property 5: NAT HA (per_az)", test_property_5_nat_ha_per_az),
        ("Property 5: NAT (single)", test_property_5_nat_single),
        ("Property 16: Cost Optimization", test_property_16_cost_optimization),
        ("NAT Gateway Outputs", test_nat_gateway_outputs),
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
