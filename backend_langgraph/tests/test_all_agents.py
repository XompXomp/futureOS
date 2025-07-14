#!/usr/bin/env python3
"""Master test script to run all individual agent tests."""

import os
import sys
import subprocess
import time

def run_test(test_name, test_file):
    """Run a specific test file."""
    print(f"\n{'='*60}")
    print(f"RUNNING {test_name.upper()} TEST")
    print(f"{'='*60}")
    
    try:
        # Run the test file
        result = subprocess.run([
            sys.executable, 
            os.path.join(os.path.dirname(__file__), test_file)
        ], capture_output=True, text=True, timeout=60)
        
        print(f"Exit code: {result.returncode}")
        print(f"Output:\n{result.stdout}")
        
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"Test {test_name} timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"Error running {test_name}: {str(e)}")
        return False

def main():
    """Run all agent tests."""
    print("Starting all agent tests...")
    
    # Define all tests to run
    tests = [
        ("Patient Agent", "test_patient_agent.py"),
        ("Web Agent", "test_web_agent.py"),
        ("Text Agent", "test_text_agent.py"),
        ("File Agent", "test_file_agent.py"),
        ("JSON Agent", "test_json_agent.py")
    ]
    
    results = {}
    
    for test_name, test_file in tests:
        print(f"\nStarting {test_name} test...")
        success = run_test(test_name, test_file)
        results[test_name] = success
        
        # Small delay between tests
        time.sleep(1)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for test_name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(tests)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")

if __name__ == "__main__":
    main() 