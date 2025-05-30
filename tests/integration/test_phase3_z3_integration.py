#!/usr/bin/env python3
"""
Phase 3 Z3 Integration Test Script for ACGS-PGP
Tests the Z3 SMT solver integration, tiered validation pipeline, and safety/conflict checking
"""

import asyncio
import json
import sys
import time
from typing import Dict, List, Any
import httpx

# Test configuration
BASE_URL = "http://localhost:8003"  # Direct FV service port
ADMIN_TOKEN = "admin_token"  # Replace with actual admin token
TEST_TIMEOUT = 30

class Phase3TestRunner:
    """Test runner for Phase 3 Z3 integration features."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        self.headers = {
            "Authorization": f"Bearer {ADMIN_TOKEN}",
            "Content-Type": "application/json"
        }
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test_result(self, test_name: str, success: bool, message: str = "", details: Dict = None):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        if not success and details:
            print(f"    Details: {details}")
    
    async def test_z3_solver_basic(self):
        """Test basic Z3 SMT solver functionality."""
        test_name = "Z3 Solver Basic Functionality"
        
        try:
            # Test data from our test file
            test_data = {
                "policy_rule_refs": [{"id": 1}],
                "ac_principle_refs": [{"id": 1}]
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/verify/",
                headers=self.headers,
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if "results" in result and len(result["results"]) > 0:
                    self.log_test_result(test_name, True, "Z3 solver integration working")
                else:
                    self.log_test_result(test_name, False, "No verification results returned")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_tiered_validation_automated(self):
        """Test automated tier validation."""
        test_name = "Tiered Validation - Automated Tier"
        
        try:
            test_data = {
                "policy_rule_refs": [{"id": 1}, {"id": 2}],
                "validation_tier": "automated",
                "validation_level": "baseline",
                "timeout_seconds": 300
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/verify/tiered",
                headers=self.headers,
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if "results" in result and "overall_confidence" in result:
                    confidence = result["overall_confidence"]
                    self.log_test_result(
                        test_name, True, 
                        f"Automated validation completed with confidence: {confidence:.2f}",
                        {"confidence": confidence, "results_count": len(result["results"])}
                    )
                else:
                    self.log_test_result(test_name, False, "Invalid response format")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_tiered_validation_hitl(self):
        """Test human-in-the-loop tier validation."""
        test_name = "Tiered Validation - HITL Tier"
        
        try:
            test_data = {
                "policy_rule_refs": [{"id": 3}],
                "validation_tier": "human_in_the_loop",
                "validation_level": "standard",
                "human_reviewer_id": "test_reviewer",
                "timeout_seconds": 300
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/verify/tiered",
                headers=self.headers,
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if "results" in result:
                    # Check if human review notes are present
                    has_human_review = any(
                        r.get("human_review_notes") for r in result["results"]
                    )
                    self.log_test_result(
                        test_name, True,
                        f"HITL validation completed, human review: {has_human_review}",
                        {"human_review_present": has_human_review}
                    )
                else:
                    self.log_test_result(test_name, False, "Invalid response format")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_tiered_validation_rigorous(self):
        """Test rigorous tier validation."""
        test_name = "Tiered Validation - Rigorous Tier"
        
        try:
            test_data = {
                "policy_rule_refs": [{"id": 1}],
                "validation_tier": "rigorous",
                "validation_level": "critical",
                "safety_properties": [
                    {
                        "property_id": "SP001",
                        "property_type": "safety",
                        "property_description": "Test safety property",
                        "formal_specification": "test_safety_spec",
                        "criticality_level": "critical"
                    }
                ],
                "require_proof": True,
                "timeout_seconds": 600
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/verify/tiered",
                headers=self.headers,
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if "results" in result:
                    # Check for proof traces
                    has_proof_trace = any(
                        r.get("proof_trace") for r in result["results"]
                    )
                    self.log_test_result(
                        test_name, True,
                        f"Rigorous validation completed, proof trace: {has_proof_trace}",
                        {"proof_trace_present": has_proof_trace}
                    )
                else:
                    self.log_test_result(test_name, False, "Invalid response format")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_safety_property_checking(self):
        """Test safety property verification."""
        test_name = "Safety Property Checking"
        
        try:
            test_data = {
                "system_model": "test_access_control_model",
                "safety_properties": [
                    {
                        "property_id": "SP001",
                        "property_type": "safety",
                        "property_description": "No unauthorized access to sensitive data",
                        "formal_specification": "unauthorized_access_prevention",
                        "criticality_level": "critical"
                    },
                    {
                        "property_id": "SP002",
                        "property_type": "security",
                        "property_description": "All transmissions encrypted",
                        "formal_specification": "encryption_mandatory",
                        "criticality_level": "high"
                    }
                ],
                "verification_method": "bounded_model_checking",
                "depth_limit": 50,
                "time_limit_seconds": 300
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/verify/safety-check",
                headers=self.headers,
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if "results" in result and "overall_safety_status" in result:
                    safety_status = result["overall_safety_status"]
                    critical_violations = result.get("critical_violations", [])
                    self.log_test_result(
                        test_name, True,
                        f"Safety check completed: {safety_status}, critical violations: {len(critical_violations)}",
                        {"safety_status": safety_status, "critical_violations_count": len(critical_violations)}
                    )
                else:
                    self.log_test_result(test_name, False, "Invalid response format")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_conflict_detection(self):
        """Test conflict detection between rule sets."""
        test_name = "Conflict Detection"
        
        try:
            test_data = {
                "rule_sets": ["access_control_rules", "security_rules"],
                "conflict_types": ["logical_contradiction", "practical_incompatibility"],
                "resolution_strategy": "principle_priority_based",
                "include_suggestions": True
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/verify/conflict-check",
                headers=self.headers,
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if "conflicts" in result and "total_conflicts" in result:
                    total_conflicts = result["total_conflicts"]
                    critical_conflicts = result.get("critical_conflicts", 0)
                    self.log_test_result(
                        test_name, True,
                        f"Conflict detection completed: {total_conflicts} total, {critical_conflicts} critical",
                        {"total_conflicts": total_conflicts, "critical_conflicts": critical_conflicts}
                    )
                else:
                    self.log_test_result(test_name, False, "Invalid response format")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_validation_status_endpoint(self):
        """Test validation status retrieval."""
        test_name = "Validation Status Endpoint"
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/verify/validation-status/1",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if "rule_id" in result and "available_validation_tiers" in result:
                    tiers = result["available_validation_tiers"]
                    self.log_test_result(
                        test_name, True,
                        f"Validation status retrieved, available tiers: {len(tiers)}",
                        {"available_tiers": tiers}
                    )
                else:
                    self.log_test_result(test_name, False, "Invalid response format")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_performance_benchmarks(self):
        """Test performance of Z3 integration."""
        test_name = "Performance Benchmarks"
        
        try:
            start_time = time.time()
            
            # Run a simple verification test
            test_data = {
                "policy_rule_refs": [{"id": 1}],
                "validation_tier": "automated",
                "validation_level": "baseline"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/verify/tiered",
                headers=self.headers,
                json=test_data
            )
            
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            if response.status_code == 200:
                # Check if response time is reasonable (< 5 seconds for basic test)
                if duration_ms < 5000:
                    self.log_test_result(
                        test_name, True,
                        f"Performance test passed: {duration_ms}ms",
                        {"duration_ms": duration_ms}
                    )
                else:
                    self.log_test_result(
                        test_name, False,
                        f"Performance test failed: {duration_ms}ms (too slow)",
                        {"duration_ms": duration_ms}
                    )
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all Phase 3 tests."""
        print("🚀 Starting Phase 3 Z3 Integration Tests")
        print("=" * 50)
        
        # Test sequence
        tests = [
            self.test_z3_solver_basic,
            self.test_tiered_validation_automated,
            self.test_tiered_validation_hitl,
            self.test_tiered_validation_rigorous,
            self.test_safety_property_checking,
            self.test_conflict_detection,
            self.test_validation_status_endpoint,
            self.test_performance_benchmarks
        ]
        
        for test in tests:
            await test()
            await asyncio.sleep(0.5)  # Brief pause between tests
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        return failed_tests == 0


async def main():
    """Main test execution."""
    print("Phase 3 Z3 Integration Test Suite")
    print("Testing Z3 SMT solver, tiered validation, and safety/conflict checking")
    print()
    
    async with Phase3TestRunner() as test_runner:
        success = await test_runner.run_all_tests()
        
        if success:
            print("\n🎉 All Phase 3 tests passed!")
            sys.exit(0)
        else:
            print("\n💥 Some Phase 3 tests failed!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
