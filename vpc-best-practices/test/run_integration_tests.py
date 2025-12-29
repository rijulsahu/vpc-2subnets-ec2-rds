#!/usr/bin/env python3
"""
Integration Test Runner for VPC Best Practices

⚠️  WARNING: This script runs integration tests that create REAL AWS resources
             and INCUR COSTS. These tests should be run with explicit intent.

Integration tests validate end-to-end functionality by:
- Deploying actual VPC infrastructure
- Creating EC2 instances for testing
- Testing real network connectivity
- Simulating failure scenarios
- Cleaning up all resources afterward

COST ESTIMATES (per test run):
- Network Connectivity Test: ~$0.10 (5 minutes)
- HA Behavior Test: ~$0.20 (10 minutes)  
- Security Validation Test: ~$0.15 (7 minutes)
- TOTAL: ~$0.45 for all tests

PREREQUISITES:
1. AWS CLI configured with valid credentials
2. Sufficient AWS permissions (VPC, EC2, NAT Gateway, etc.)
3. Adequate AWS service limits (NAT Gateways, Elastic IPs, etc.)
4. Cost awareness and approval

USAGE:
    # Run all integration tests
    uv run run_integration_tests.py

    # Run individual tests
    uv run network_connectivity_integration_test.py
    uv run ha_behavior_integration_test.py
    uv run security_validation_integration_test.py
"""

import os
import sys
import subprocess
import time

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_warning(text):
    print(f"{Colors.YELLOW}{Colors.BOLD}{text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}{text}{Colors.END}")

def print_pass(text):
    print(f"{Colors.GREEN}{text}{Colors.END}")

def print_fail(text):
    print(f"{Colors.RED}{text}{Colors.END}")

def run_integration_test(test_file):
    """Run a single integration test and return success status"""
    test_name = os.path.basename(test_file).replace('_integration_test.py', '').replace('_', ' ').title()
    
    print_header(f"Running: {test_name} Integration Test")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,  # Let output stream to console
            text=True
        )
        
        success = result.returncode == 0
        
        if success:
            print_pass(f"\n✓ {test_name} Integration Test PASSED")
        else:
            print_fail(f"\n✗ {test_name} Integration Test FAILED")
        
        return test_name, success
        
    except Exception as e:
        print_fail(f"\n✗ Error running {test_name}: {str(e)}")
        return test_name, False

def main():
    """Run all integration tests with warnings and confirmations"""
    
    print_header("VPC BEST PRACTICES - INTEGRATION TEST SUITE")
    
    # Display cost warning
    print_warning("⚠️  WARNING: INTEGRATION TESTS CREATE REAL AWS RESOURCES")
    print_warning("⚠️  These tests will incur AWS charges (~$0.45 total)")
    print()
    print_info("What these tests do:")
    print_info("  • Deploy VPC infrastructure using OpenTofu")
    print_info("  • Create EC2 instances for connectivity testing")
    print_info("  • Create NAT Gateways and Elastic IPs")
    print_info("  • Test real network connectivity scenarios")
    print_info("  • Simulate failure conditions")
    print_info("  • Clean up all resources after completion")
    print()
    print_info("Cost breakdown:")
    print_info("  • Network Connectivity: ~$0.10 (5 min)")
    print_info("  • HA Behavior: ~$0.20 (10 min)")
    print_info("  • Security Validation: ~$0.15 (7 min)")
    print_info("  • TOTAL ESTIMATED TIME: ~22 minutes")
    print_info("  • TOTAL ESTIMATED COST: ~$0.45")
    print()
    print_warning("⚠️  Make sure you have:")
    print_warning("    1. AWS credentials configured")
    print_warning("    2. Sufficient AWS permissions")
    print_warning("    3. Adequate service limits")
    print_warning("    4. Cost awareness and approval")
    print()
    
    # Confirmation prompt
    print_warning("Press Ctrl+C within 15 seconds to cancel...")
    try:
        time.sleep(15)
    except KeyboardInterrupt:
        print()
        print_info("Integration tests cancelled by user")
        return 0
    
    print()
    print_info("Starting integration tests...")
    
    # List of integration test files
    test_dir = os.path.dirname(os.path.abspath(__file__))
    integration_tests = [
        'network_connectivity_integration_test.py',
        'ha_behavior_integration_test.py',
        'security_validation_integration_test.py',
    ]
    
    results = []
    start_time = time.time()
    
    for test_file in integration_tests:
        test_path = os.path.join(test_dir, test_file)
        if os.path.exists(test_path):
            test_name, success = run_integration_test(test_path)
            results.append((test_name, success))
            
            # Brief pause between tests
            if test_file != integration_tests[-1]:
                print_info("\nPausing 10 seconds before next test...")
                time.sleep(10)
        else:
            print_fail(f"\n✗ Test file not found: {test_file}")
            results.append((test_file, False))
    
    elapsed_time = time.time() - start_time
    
    # Print final summary
    print_header("INTEGRATION TEST SUMMARY")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        if success:
            print_pass(f"  ✓ PASS: {test_name}")
        else:
            print_fail(f"  ✗ FAIL: {test_name}")
    
    print()
    print_info(f"Results: {passed}/{total} integration tests passed")
    print_info(f"Total Time: {elapsed_time/60:.1f} minutes")
    print()
    
    if passed == total:
        print_pass("✓ All integration tests passed!")
    else:
        print_fail("✗ Some integration tests failed")
        print_info("\nCheck AWS Console to verify all resources were cleaned up:")
        print_info("  • VPCs")
        print_info("  • NAT Gateways")
        print_info("  • Elastic IPs")
        print_info("  • EC2 Instances")
        print_info("  • Security Groups")
    
    print()
    print("=" * 80)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print_warning("\nIntegration tests interrupted by user")
        print_info("Check AWS Console to verify resources were cleaned up")
        sys.exit(1)
    except Exception as e:
        print_fail(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
