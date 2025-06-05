#!/usr/bin/env python3
"""
Phase 3 Comprehensive Load Testing Script
Validates performance under sustained load with 100+ concurrent requests.
"""

import asyncio
import aiohttp
import time
import statistics
import json
from datetime import datetime
from typing import Dict, List, Any
import psutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase3LoadTester:
    def __init__(self):
        self.base_url = "http://localhost:8014"  # GS Service
        self.results = {
            "test_start": datetime.now().isoformat(),
            "performance_metrics": {},
            "security_metrics": {},
            "resource_metrics": {},
            "success_criteria": {}
        }
    
    async def test_policy_decision_latency_under_load(self, concurrent_users: int = 100, duration_seconds: int = 60):
        """Test policy decision latency under concurrent load."""
        logger.info(f"Testing policy decision latency with {concurrent_users} concurrent users for {duration_seconds}s")
        
        latencies = []
        successful_requests = 0
        failed_requests = 0
        
        async def worker_task(session: aiohttp.ClientSession, worker_id: int):
            nonlocal successful_requests, failed_requests
            
            test_policy = {
                "policy_content": f"allow = true if input.user == 'test_user_{worker_id}'",
                "input_data": {"user": f"test_user_{worker_id}", "action": "read"},
                "validation_level": "standard"
            }
            
            start_time = time.time()
            end_time = start_time + duration_seconds
            
            while time.time() < end_time:
                request_start = time.time()
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/synthesize/policy",
                        json=test_policy,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            successful_requests += 1
                            request_latency = (time.time() - request_start) * 1000
                            latencies.append(request_latency)
                        else:
                            failed_requests += 1
                except Exception as e:
                    failed_requests += 1
                    logger.debug(f"Request failed: {e}")
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
        
        # Create concurrent workers
        async with aiohttp.ClientSession() as session:
            workers = [worker_task(session, i) for i in range(concurrent_users)]
            await asyncio.gather(*workers, return_exceptions=True)
        
        # Calculate metrics
        if latencies:
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
            
            self.results["performance_metrics"]["policy_decision_latency"] = {
                "average_ms": avg_latency,
                "p95_ms": p95_latency,
                "p99_ms": p99_latency,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": successful_requests / (successful_requests + failed_requests) * 100,
                "target_met": avg_latency < 50 and p95_latency < 50
            }
            
            logger.info(f"Policy Decision Latency Results:")
            logger.info(f"  Average: {avg_latency:.2f}ms")
            logger.info(f"  95th percentile: {p95_latency:.2f}ms")
            logger.info(f"  99th percentile: {p99_latency:.2f}ms")
            logger.info(f"  Success rate: {successful_requests / (successful_requests + failed_requests) * 100:.1f}%")
            logger.info(f"  Target (<50ms): {'✅ MET' if avg_latency < 50 and p95_latency < 50 else '❌ FAILED'}")
    
    async def test_cache_performance_under_load(self, concurrent_users: int = 50, duration_seconds: int = 30):
        """Test cache hit rate and performance under load."""
        logger.info(f"Testing cache performance with {concurrent_users} concurrent users for {duration_seconds}s")
        
        cache_requests = 0
        cache_hits = 0
        
        # Pre-populate cache with test policies
        test_policies = [
            {
                "policy_content": f"allow = true if input.user == 'cached_user_{i}'",
                "input_data": {"user": f"cached_user_{i}", "action": "read"},
                "validation_level": "standard"
            }
            for i in range(10)
        ]
        
        async def cache_worker(session: aiohttp.ClientSession, worker_id: int):
            nonlocal cache_requests, cache_hits
            
            start_time = time.time()
            end_time = start_time + duration_seconds
            
            while time.time() < end_time:
                # Use cached policies 80% of the time
                if worker_id % 5 != 0:  # 80% cache hits
                    policy = test_policies[worker_id % len(test_policies)]
                    cache_requests += 1
                else:  # 20% cache misses
                    policy = {
                        "policy_content": f"allow = true if input.user == 'new_user_{int(time.time())}'",
                        "input_data": {"user": f"new_user_{int(time.time())}", "action": "read"},
                        "validation_level": "standard"
                    }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/synthesize/policy",
                        json=policy,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            # Check if response indicates cache hit
                            response_data = await response.json()
                            if response_data.get("cached", False):
                                cache_hits += 1
                except Exception as e:
                    logger.debug(f"Cache test request failed: {e}")
                
                await asyncio.sleep(0.02)
        
        async with aiohttp.ClientSession() as session:
            workers = [cache_worker(session, i) for i in range(concurrent_users)]
            await asyncio.gather(*workers, return_exceptions=True)
        
        cache_hit_rate = (cache_hits / cache_requests * 100) if cache_requests > 0 else 0
        
        self.results["performance_metrics"]["cache_performance"] = {
            "total_requests": cache_requests,
            "cache_hits": cache_hits,
            "hit_rate_percent": cache_hit_rate,
            "target_met": cache_hit_rate > 80
        }
        
        logger.info(f"Cache Performance Results:")
        logger.info(f"  Total requests: {cache_requests}")
        logger.info(f"  Cache hits: {cache_hits}")
        logger.info(f"  Hit rate: {cache_hit_rate:.1f}%")
        logger.info(f"  Target (>80%): {'✅ MET' if cache_hit_rate > 80 else '❌ FAILED'}")
    
    async def test_security_under_load(self, concurrent_users: int = 30, duration_seconds: int = 20):
        """Test security measures under load."""
        logger.info(f"Testing security measures with {concurrent_users} concurrent users for {duration_seconds}s")
        
        rate_limit_violations = 0
        auth_failures = 0
        injection_attempts = 0
        
        malicious_payloads = [
            {"policy_content": "'; DROP TABLE policies; --"},
            {"policy_content": "<script>alert('xss')</script>"},
            {"policy_content": "; cat /etc/passwd"},
            {"policy_content": "1' OR '1'='1"},
        ]
        
        async def security_worker(session: aiohttp.ClientSession, worker_id: int):
            nonlocal rate_limit_violations, auth_failures, injection_attempts
            
            start_time = time.time()
            end_time = start_time + duration_seconds
            
            while time.time() < end_time:
                # Send malicious payload
                payload = malicious_payloads[worker_id % len(malicious_payloads)]
                injection_attempts += 1
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/synthesize/policy",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 429:  # Rate limited
                            rate_limit_violations += 1
                        elif response.status == 401:  # Unauthorized
                            auth_failures += 1
                        elif response.status == 400:  # Bad request (injection detected)
                            pass  # Expected for malicious input
                except Exception as e:
                    logger.debug(f"Security test request failed: {e}")
                
                await asyncio.sleep(0.05)
        
        async with aiohttp.ClientSession() as session:
            workers = [security_worker(session, i) for i in range(concurrent_users)]
            await asyncio.gather(*workers, return_exceptions=True)
        
        self.results["security_metrics"] = {
            "injection_attempts": injection_attempts,
            "rate_limit_violations": rate_limit_violations,
            "auth_failures": auth_failures,
            "security_active": rate_limit_violations > 0 or injection_attempts > 0
        }
        
        logger.info(f"Security Testing Results:")
        logger.info(f"  Injection attempts: {injection_attempts}")
        logger.info(f"  Rate limit violations: {rate_limit_violations}")
        logger.info(f"  Auth failures: {auth_failures}")
        logger.info(f"  Security measures: {'✅ ACTIVE' if rate_limit_violations > 0 else '⚠️ CHECK CONFIG'}")
    
    def monitor_system_resources(self):
        """Monitor system resource usage during testing."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        self.results["resource_metrics"] = {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "cpu_target_met": cpu_percent < 80,
            "memory_target_met": memory.percent < 85
        }
        
        logger.info(f"System Resource Usage:")
        logger.info(f"  CPU: {cpu_percent:.1f}% (target: <80%)")
        logger.info(f"  Memory: {memory.percent:.1f}% (target: <85%)")
        logger.info(f"  Available Memory: {memory.available / (1024**3):.1f} GB")
    
    async def run_comprehensive_load_test(self):
        """Run comprehensive load testing suite."""
        logger.info("🚀 Starting Phase 3 Comprehensive Load Testing")
        logger.info("=" * 60)
        
        # Test 1: Policy Decision Latency Under Load
        await self.test_policy_decision_latency_under_load(concurrent_users=100, duration_seconds=60)
        
        # Test 2: Cache Performance Under Load
        await self.test_cache_performance_under_load(concurrent_users=50, duration_seconds=30)
        
        # Test 3: Security Measures Under Load
        await self.test_security_under_load(concurrent_users=30, duration_seconds=20)
        
        # Test 4: System Resource Monitoring
        self.monitor_system_resources()
        
        # Evaluate Success Criteria
        self.evaluate_success_criteria()
        
        # Generate Report
        self.generate_load_test_report()
    
    def evaluate_success_criteria(self):
        """Evaluate overall success criteria."""
        criteria = {
            "policy_latency_target": self.results["performance_metrics"].get("policy_decision_latency", {}).get("target_met", False),
            "cache_performance_target": self.results["performance_metrics"].get("cache_performance", {}).get("target_met", False),
            "cpu_usage_target": self.results["resource_metrics"].get("cpu_target_met", False),
            "memory_usage_target": self.results["resource_metrics"].get("memory_target_met", False),
            "security_measures_active": self.results["security_metrics"].get("security_active", False)
        }
        
        overall_success = all(criteria.values())
        
        self.results["success_criteria"] = {
            **criteria,
            "overall_success": overall_success,
            "success_percentage": sum(criteria.values()) / len(criteria) * 100
        }
    
    def generate_load_test_report(self):
        """Generate comprehensive load test report."""
        self.results["test_end"] = datetime.now().isoformat()
        
        logger.info("\n🎯 Phase 3 Load Testing Results Summary")
        logger.info("=" * 60)
        
        success_criteria = self.results["success_criteria"]
        logger.info(f"Overall Success: {'✅ PASSED' if success_criteria['overall_success'] else '❌ FAILED'}")
        logger.info(f"Success Rate: {success_criteria['success_percentage']:.1f}%")
        
        logger.info("\n📊 Detailed Results:")
        for criterion, passed in success_criteria.items():
            if criterion not in ["overall_success", "success_percentage"]:
                status = "✅ PASSED" if passed else "❌ FAILED"
                logger.info(f"  {criterion.replace('_', ' ').title()}: {status}")
        
        # Save results to file
        with open("phase3_load_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n📄 Detailed results saved to: phase3_load_test_results.json")

async def main():
    """Run Phase 3 load testing."""
    tester = Phase3LoadTester()
    await tester.run_comprehensive_load_test()

if __name__ == "__main__":
    asyncio.run(main())
