#!/usr/bin/env python3
"""
Test runner for VPC Best Practices property-based tests
Runs all property tests and provides a summary
"""

import os
import sys
import importlib.util

def run_test_file(test_file_path):
    """Run a single test file and return results"""
    test_name = os.path.basename(test_file_path).replace('.py', '').replace('_', ' ').title()
    
    print(f"\n{'=' * 80}")
    print(f"Running: {test_name}")
    print('=' * 80)
    
    try:
        spec = importlib.util.spec_from_file_location("test_module", test_file_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        if hasattr(test_module, 'run_all_tests'):
            success = test_module.run_all_tests()
            return test_name, success
        else:
            print(f"  WARNING: {test_file_path} does not have run_all_tests() function")
            return test_name, False
    except Exception as e:
        print(f"  ERROR running {test_file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return test_name, False

def main():
    """Run all property-based tests"""
    print("=" * 80)
    print("VPC BEST PRACTICES - PROPERTY-BASED TEST SUITE")
    print("=" * 80)
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of test files to run (in order)
    test_files = [
        'variable_validation_test.py',
        'vpc_cidr_configuration_test.py',
        # More tests will be added as we implement them
    ]
    
    results = []
    
    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        if os.path.exists(test_path):
            test_name, success = run_test_file(test_path)
            results.append((test_name, success))
        else:
            print(f"\n  WARNING: Test file not found: {test_file}")
            results.append((test_file, False))
    
    # Print final summary
    print("\n" + "=" * 80)
    print("FINAL TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall Results: {passed}/{total} test suites passed")
    print("=" * 80)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
