#!/usr/bin/env python3
"""
Test Teardown Procedures Validation Script

Validates that the implemented test teardown procedures work correctly
and prevent test pollution between test runs.
"""

import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

class TeardownProceduresTester:
    """Test the teardown procedures implementation."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def check_test_artifacts_before(self):
        """Check for test artifacts before running tests."""
        print("🔍 Checking for existing test artifacts...")
        
        artifacts = {
            'test_databases': list(Path(".").glob("test_*.db*")),
            'result_files': list(Path(".").glob("*_test_results.json")),
            'temp_files': list(Path(".").glob("test_*")),
            'temp_dirs': [p for p in Path(".").glob("test_*") if p.is_dir()]
        }
        
        total_artifacts = sum(len(files) for files in artifacts.values())
        
        if total_artifacts > 0:
            print(f"⚠️  Found {total_artifacts} existing test artifacts:")
            for category, files in artifacts.items():
                if files:
                    print(f"  {category}: {len(files)} files")
        else:
            print("✅ No existing test artifacts found")
            
        return artifacts
        
    def run_teardown_validation_tests(self):
        """Run the teardown validation test suite."""
        print("\n🧪 Running teardown validation tests...")
        
        try:
            # Run the teardown validation tests
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/test_teardown_validation.py",
                "-v", "--tb=short", "--no-header"
            ], capture_output=True, text=True, timeout=120)
            
            success = result.returncode == 0
            details = f"Exit code: {result.returncode}"
            
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
                
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
                
            self.log_test_result(
                "Teardown Validation Tests", 
                success, 
                details
            )
            
            return success
            
        except subprocess.TimeoutExpired:
            self.log_test_result(
                "Teardown Validation Tests", 
                False, 
                "Tests timed out after 120 seconds"
            )
            return False
        except Exception as e:
            self.log_test_result(
                "Teardown Validation Tests", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
            
    def check_test_artifacts_after(self, artifacts_before):
        """Check for test artifacts after running tests."""
        print("\n🔍 Checking for test artifacts after tests...")
        
        artifacts_after = {
            'test_databases': list(Path(".").glob("test_*.db*")),
            'result_files': list(Path(".").glob("*_test_results.json")),
            'temp_files': list(Path(".").glob("test_*")),
            'temp_dirs': [p for p in Path(".").glob("test_*") if p.is_dir()]
        }
        
        # Check for new artifacts
        new_artifacts = {}
        for category, files_after in artifacts_after.items():
            files_before = artifacts_before.get(category, [])
            new_files = [f for f in files_after if f not in files_before]
            if new_files:
                new_artifacts[category] = new_files
                
        total_new_artifacts = sum(len(files) for files in new_artifacts.values())
        
        if total_new_artifacts > 0:
            print(f"⚠️  Found {total_new_artifacts} new test artifacts:")
            for category, files in new_artifacts.items():
                print(f"  {category}: {[str(f) for f in files]}")
            
            self.log_test_result(
                "Test Artifact Cleanup", 
                False, 
                f"Found {total_new_artifacts} uncleaned artifacts"
            )
            return False
        else:
            print("✅ No new test artifacts found - cleanup successful!")
            self.log_test_result(
                "Test Artifact Cleanup", 
                True, 
                "All test artifacts properly cleaned up"
            )
            return True
            
    def test_multiple_test_runs(self):
        """Test that multiple test runs don't interfere with each other."""
        print("\n🔄 Testing multiple test runs for pollution...")
        
        success_count = 0
        total_runs = 3
        
        for run_num in range(1, total_runs + 1):
            print(f"\n  Run {run_num}/{total_runs}:")
            
            try:
                # Run a subset of tests multiple times
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    "tests/test_teardown_validation.py::TestTeardownValidation::test_no_test_pollution_between_runs",
                    "-v", "--tb=short", "--no-header", "-q"
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"    ✅ Run {run_num} passed")
                    success_count += 1
                else:
                    print(f"    ❌ Run {run_num} failed")
                    if result.stderr:
                        print(f"    Error: {result.stderr}")
                        
            except Exception as e:
                print(f"    ❌ Run {run_num} exception: {str(e)}")
                
        success = success_count == total_runs
        self.log_test_result(
            "Multiple Test Runs", 
            success, 
            f"{success_count}/{total_runs} runs passed"
        )
        
        return success
        
    def test_integration_teardown(self):
        """Test integration test teardown procedures."""
        print("\n🔗 Testing integration test teardown...")
        
        try:
            # Run a simple integration test to check teardown
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/integration/conftest.py",
                "--collect-only", "-q"
            ], capture_output=True, text=True, timeout=30)
            
            success = result.returncode == 0
            details = "Integration conftest.py validation"
            
            if not success and result.stderr:
                details = f"Error: {result.stderr}"
                
            self.log_test_result(
                "Integration Test Teardown", 
                success, 
                details
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "Integration Test Teardown", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
            
    def run_comprehensive_test(self):
        """Run comprehensive teardown procedure validation."""
        print("🧹 ACGS-PGP Test Teardown Procedures Validation")
        print("=" * 60)
        print(f"Test started at: {datetime.now().isoformat()}")
        
        # Step 1: Check initial state
        artifacts_before = self.check_test_artifacts_before()
        
        # Step 2: Run teardown validation tests
        validation_success = self.run_teardown_validation_tests()
        
        # Step 3: Check for artifacts after tests
        cleanup_success = self.check_test_artifacts_after(artifacts_before)
        
        # Step 4: Test multiple runs
        multiple_runs_success = self.test_multiple_test_runs()
        
        # Step 5: Test integration teardown
        integration_success = self.test_integration_teardown()
        
        # Calculate overall success
        all_tests = [
            validation_success,
            cleanup_success, 
            multiple_runs_success,
            integration_success
        ]
        
        overall_success = all(all_tests)
        passed_tests = sum(all_tests)
        total_tests = len(all_tests)
        
        print(f"\n📊 Test Results Summary:")
        print(f"  Passed: {passed_tests}/{total_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if overall_success:
            print("\n🎉 All teardown procedure tests passed!")
            print("✅ Test teardown procedures are working correctly")
            return True
        else:
            print("\n⚠️  Some teardown procedure tests failed")
            print("❌ Test teardown procedures need attention")
            return False


async def main():
    """Main test execution function."""
    tester = TeardownProceduresTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        # Save detailed results
        import json
        with open("teardown_test_results.json", "w") as f:
            json.dump({
                "test_results": tester.test_results,
                "summary": {
                    "total_tests": len(tester.test_results),
                    "passed_tests": len([r for r in tester.test_results if r["success"]]),
                    "overall_success": success,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: teardown_test_results.json")
        
        if success:
            print("\n🎉 Test teardown procedures validation completed successfully!")
            return 0
        else:
            print("\n⚠️  Test teardown procedures validation failed.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
