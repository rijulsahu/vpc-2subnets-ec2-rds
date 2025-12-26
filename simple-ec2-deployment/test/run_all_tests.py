#!/usr/bin/env python3
"""
Run all property-based tests for simple-ec2-deployment
Final checkpoint validation
"""
import subprocess
import sys
import os

# Define all tests to run
TESTS = [
    ("Property 2: Variable Validation", "test/variable_validation_test.py"),
    ("Property 3: AMI Compliance", "test/ami_compliance_test.py"),
    ("Property 4: Security Group", "test/security_group_test.py"),
    ("Property 6: Storage Configuration", "test/storage_compliance_test.py"),
    ("Property 5: Key Pair Management", "test/key_pair_management_test_v2.py"),
    ("Property 7: Tagging Consistency", "test/tagging_consistency_test.py"),
    ("Property 9: Output Availability", "test/output_availability_test.py"),
    ("Property 1: Deployment Compliance", "test/deployment_compliance_test.py"),
    ("Property 8: Minimal Resources", "test/minimal_resource_test.py"),
]

def run_test(test_name, test_path):
    """Run a single test and return result"""
    print(f"\n{'='*70}")
    print(f"Running: {test_name}")
    print(f"{'='*70}")
    
    try:
        # Get the parent directory (simple-ec2-deployment)
        test_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(test_dir)
        
        result = subprocess.run(
            ["python", test_path],
            cwd=parent_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {test_name} took too long")
        return False
    except Exception as e:
        print(f"ERROR: {test_name} failed with {e}")
        return False

def main():
    print("\n" + "="*70)
    print("SIMPLE EC2 DEPLOYMENT - FINAL CHECKPOINT")
    print("Running Full Test Suite")
    print("="*70)
    
    results = {}
    
    for test_name, test_path in TESTS:
        passed = run_test(test_name, test_path)
        results[test_name] = passed
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUITE SUMMARY")
    print("="*70)
    
    passed_count = 0
    failed_count = 0
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        color = "\033[92m" if passed else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{status}{reset} - {test_name}")
        
        if passed:
            passed_count += 1
        else:
            failed_count += 1
    
    print("\n" + "="*70)
    total_tests = len(results)
    success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Success Rate: {success_rate:.1f}%")
    print("="*70)
    
    if failed_count == 0:
        print("\nALL TESTS PASSED! Configuration is ready for deployment.")
        return 0
    else:
        print(f"\n{failed_count} test(s) failed. Please review and fix issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
