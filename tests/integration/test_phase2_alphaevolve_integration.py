#!/usr/bin/env python3
"""
Phase 2 AlphaEvolve Integration Test Suite

This script tests the integration between AlphaEvolve governance engine
and the main ACGS-PGP services for evolutionary computation governance.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any

import httpx
import pytest

# Test configuration
BASE_URL = "http://localhost:8000"
GS_SERVICE_URL = "http://localhost:8004"  # Direct GS service port
PGC_SERVICE_URL = "http://localhost:8005"  # Direct PGC service port
AC_SERVICE_URL = "http://localhost:8001"   # Direct AC service port

# Test data
SAMPLE_EC_PROPOSALS = [
    {
        "proposal_id": "ec_001",
        "solution_code": "def safe_function(): return 'safe solution'",
        "generation": 1,
        "parent_ids": [],
        "fitness_context": {"objective": "maximize_safety", "domain": "healthcare"},
        "metadata": {"complexity": "low", "safety_score": 0.9}
    },
    {
        "proposal_id": "ec_002", 
        "solution_code": "def unsafe_function(): return 'potentially harmful code'",
        "generation": 2,
        "parent_ids": ["ec_001"],
        "fitness_context": {"objective": "maximize_efficiency", "domain": "healthcare"},
        "metadata": {"complexity": "medium", "safety_score": 0.3}
    },
    {
        "proposal_id": "ec_003",
        "solution_code": "def complex_function(): " + "x = 1; " * 1000 + "return x",
        "generation": 3,
        "parent_ids": ["ec_001", "ec_002"],
        "fitness_context": {"objective": "maximize_performance", "domain": "finance"},
        "metadata": {"complexity": "high", "safety_score": 0.7}
    }
]

SAMPLE_EC_CONTEXT = "healthcare_ai_optimization"
SAMPLE_OPTIMIZATION_OBJECTIVE = "Optimize AI decision-making for patient safety and treatment efficacy"
SAMPLE_CONSTITUTIONAL_CONSTRAINTS = [
    "Ensure patient privacy protection",
    "Maintain treatment safety standards", 
    "Preserve healthcare equity and fairness",
    "Comply with medical ethics guidelines"
]


class Phase2TestSuite:
    """Test suite for Phase 2 AlphaEvolve integration."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        
    async def cleanup(self):
        """Cleanup test resources."""
        await self.client.aclose()
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", latency_ms: float = 0):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if latency_ms > 0:
            print(f"    Latency: {latency_ms:.2f}ms")
    
    async def test_gs_service_health(self):
        """Test GS service health and availability."""
        test_name = "GS Service Health Check"
        try:
            start_time = time.time()
            response = await self.client.get(f"{GS_SERVICE_URL}/")
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                self.log_test_result(test_name, True, "GS service is healthy", latency_ms)
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Connection error: {str(e)}")
            return False
    
    async def test_pgc_service_health(self):
        """Test PGC service health and availability."""
        test_name = "PGC Service Health Check"
        try:
            start_time = time.time()
            response = await self.client.get(f"{PGC_SERVICE_URL}/")
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                self.log_test_result(test_name, True, "PGC service is healthy", latency_ms)
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_test_result(test_name, False, f"Connection error: {str(e)}")
            return False
    
    async def test_ec_constitutional_prompting(self):
        """Test EC constitutional prompting endpoint."""
        test_name = "EC Constitutional Prompting"
        try:
            start_time = time.time()
            
            request_data = {
                "ec_context": SAMPLE_EC_CONTEXT,
                "current_population": SAMPLE_EC_PROPOSALS,
                "optimization_objective": SAMPLE_OPTIMIZATION_OBJECTIVE,
                "constitutional_constraints": SAMPLE_CONSTITUTIONAL_CONSTRAINTS,
                "generation_guidance": True
            }
            
            response = await self.client.post(
                f"{GS_SERVICE_URL}/api/v1/alphaevolve/constitutional-prompting",
                json=request_data
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["prompting_id", "constitutional_guidance", "fitness_modifications", 
                                 "operator_constraints", "population_filters", "synthesis_metadata"]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_test_result(test_name, False, f"Missing fields: {missing_fields}", latency_ms)
                    return False
                
                self.log_test_result(test_name, True, 
                    f"Generated guidance with {len(data['operator_constraints'])} constraints", latency_ms)
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}", latency_ms)
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {str(e)}")
            return False
    
    async def test_ec_governance_evaluation(self):
        """Test EC governance evaluation endpoint."""
        test_name = "EC Governance Evaluation"
        try:
            start_time = time.time()
            
            request_data = {
                "proposals": SAMPLE_EC_PROPOSALS,
                "context": SAMPLE_EC_CONTEXT,
                "real_time": True,
                "priority": "high"
            }
            
            response = await self.client.post(
                f"{GS_SERVICE_URL}/api/v1/alphaevolve/governance-evaluation",
                json=request_data
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["evaluation_id", "decisions", "batch_summary", 
                                 "processing_time_ms", "constitutional_compliance_rate"]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_test_result(test_name, False, f"Missing fields: {missing_fields}", latency_ms)
                    return False
                
                # Validate decisions
                if len(data["decisions"]) != len(SAMPLE_EC_PROPOSALS):
                    self.log_test_result(test_name, False, 
                        f"Expected {len(SAMPLE_EC_PROPOSALS)} decisions, got {len(data['decisions'])}", latency_ms)
                    return False
                
                compliance_rate = data["constitutional_compliance_rate"]
                self.log_test_result(test_name, True, 
                    f"Evaluated {len(data['decisions'])} proposals, compliance rate: {compliance_rate:.2f}", latency_ms)
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}", latency_ms)
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {str(e)}")
            return False
    
    async def test_pgc_batch_evaluation(self):
        """Test PGC batch evaluation for EC proposals."""
        test_name = "PGC Batch Evaluation"
        try:
            start_time = time.time()
            
            request_data = {
                "proposals": SAMPLE_EC_PROPOSALS,
                "context": SAMPLE_EC_CONTEXT,
                "real_time": True
            }
            
            response = await self.client.post(
                f"{PGC_SERVICE_URL}/api/v1/alphaevolve/evaluate-batch",
                json=request_data
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check performance requirements
                avg_latency = data.get("batch_summary", {}).get("average_latency_ms", 0)
                target_latency = 50  # Sub-50ms requirement
                
                performance_ok = avg_latency <= target_latency
                performance_details = f"Avg latency: {avg_latency:.2f}ms (target: {target_latency}ms)"
                
                if performance_ok:
                    self.log_test_result(test_name, True, 
                        f"Batch processed successfully. {performance_details}", latency_ms)
                else:
                    self.log_test_result(test_name, False, 
                        f"Performance target missed. {performance_details}", latency_ms)
                
                return performance_ok
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}", latency_ms)
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {str(e)}")
            return False
    
    async def test_pgc_single_evaluation(self):
        """Test PGC single proposal evaluation for maximum performance."""
        test_name = "PGC Single Evaluation"
        try:
            start_time = time.time()
            
            request_data = {
                "proposal": SAMPLE_EC_PROPOSALS[0],
                "context": SAMPLE_EC_CONTEXT
            }
            
            response = await self.client.post(
                f"{PGC_SERVICE_URL}/api/v1/alphaevolve/evaluate-single",
                json=request_data
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check performance requirements
                achieved_latency = data.get("latency_ms", 0)
                target_latency = 20  # Sub-20ms requirement for single evaluation
                
                performance_ok = achieved_latency <= target_latency
                performance_details = f"Latency: {achieved_latency:.2f}ms (target: {target_latency}ms)"
                
                if performance_ok:
                    self.log_test_result(test_name, True, 
                        f"Single evaluation successful. {performance_details}", latency_ms)
                else:
                    self.log_test_result(test_name, False, 
                        f"Performance target missed. {performance_details}", latency_ms)
                
                return performance_ok
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}", latency_ms)
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {str(e)}")
            return False
    
    async def test_cache_functionality(self):
        """Test PGC enforcement cache functionality."""
        test_name = "PGC Cache Functionality"
        try:
            # Clear cache first
            await self.client.post(f"{PGC_SERVICE_URL}/api/v1/alphaevolve/cache/clear")
            
            # Get initial cache stats
            response = await self.client.get(f"{PGC_SERVICE_URL}/api/v1/alphaevolve/cache/stats")
            if response.status_code != 200:
                self.log_test_result(test_name, False, "Cache stats endpoint not available")
                return False
            
            initial_stats = response.json()
            initial_size = initial_stats.get("cache_size", 0)
            
            # Perform evaluation to populate cache
            request_data = {
                "proposal": SAMPLE_EC_PROPOSALS[0],
                "context": SAMPLE_EC_CONTEXT
            }
            
            await self.client.post(
                f"{PGC_SERVICE_URL}/api/v1/alphaevolve/evaluate-single",
                json=request_data
            )
            
            # Check cache stats after evaluation
            response = await self.client.get(f"{PGC_SERVICE_URL}/api/v1/alphaevolve/cache/stats")
            final_stats = response.json()
            final_size = final_stats.get("cache_size", 0)
            
            if final_size > initial_size:
                self.log_test_result(test_name, True, 
                    f"Cache populated: {initial_size} -> {final_size} entries")
                return True
            else:
                self.log_test_result(test_name, False, 
                    f"Cache not populated: {initial_size} -> {final_size} entries")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all Phase 2 integration tests."""
        print("🚀 Starting Phase 2 AlphaEvolve Integration Tests")
        print("=" * 60)
        
        # Service health checks
        gs_healthy = await self.test_gs_service_health()
        pgc_healthy = await self.test_pgc_service_health()
        
        if not (gs_healthy and pgc_healthy):
            print("\n❌ Service health checks failed. Aborting tests.")
            return False
        
        # Core functionality tests
        tests = [
            self.test_ec_constitutional_prompting,
            self.test_ec_governance_evaluation,
            self.test_pgc_batch_evaluation,
            self.test_pgc_single_evaluation,
            self.test_cache_functionality
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Phase 2 Integration Test Summary")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Performance summary
        latencies = [r["latency_ms"] for r in self.test_results if r["latency_ms"] > 0]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            print(f"Average Latency: {avg_latency:.2f}ms")
            print(f"Maximum Latency: {max_latency:.2f}ms")
        
        return passed_tests == total_tests


async def main():
    """Main test execution function."""
    test_suite = Phase2TestSuite()
    
    try:
        success = await test_suite.run_all_tests()
        
        # Save detailed results
        with open("phase2_test_results.json", "w") as f:
            json.dump({
                "test_results": test_suite.test_results,
                "summary": {
                    "total_tests": len(test_suite.test_results),
                    "passed_tests": len([r for r in test_suite.test_results if r["success"]]),
                    "overall_success": success,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: phase2_test_results.json")
        
        if success:
            print("\n🎉 All Phase 2 AlphaEvolve integration tests passed!")
            return 0
        else:
            print("\n⚠️  Some Phase 2 tests failed. Check the results above.")
            return 1
            
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
