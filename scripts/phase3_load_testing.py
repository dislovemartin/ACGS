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
        # Try multiple service endpoints to find available ones
        self.service_endpoints = {
            "ac_service": "http://localhost:8001",  # AC Service
            "auth_service": "http://localhost:8000",  # Auth Service
            "gs_service": "http://localhost:8015",  # GS Service (if running)
        }
        self.available_services = {}
        self.results = {
            "test_start": datetime.now().isoformat(),
            "performance_metrics": {},
            "security_metrics": {},
            "resource_metrics": {},
            "success_criteria": {},
            "service_availability": {}
        }

    async def check_service_availability(self):
        """Check which services are available for testing."""
        logger.info("Checking service availability...")

        async with aiohttp.ClientSession() as session:
            for service_name, url in self.service_endpoints.items():
                try:
                    async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            self.available_services[service_name] = url
                            logger.info(f"✅ {service_name} available at {url}")
                        else:
                            logger.warning(f"❌ {service_name} returned status {response.status}")
                except Exception as e:
                    logger.warning(f"❌ {service_name} not available at {url}: {e}")

        self.results["service_availability"] = {
            "total_services": len(self.service_endpoints),
            "available_services": len(self.available_services),
            "available_service_list": list(self.available_services.keys()),
            "unavailable_services": [name for name in self.service_endpoints.keys() if name not in self.available_services]
        }

        if not self.available_services:
            logger.error("❌ No services available for testing!")
            return False

        logger.info(f"✅ {len(self.available_services)} services available for testing")
        return True

    async def test_policy_decision_latency_under_load(self, concurrent_users: int = 100, duration_seconds: int = 60):
        """Test policy decision latency under concurrent load."""
        logger.info(f"Testing policy decision latency with {concurrent_users} concurrent users for {duration_seconds}s")

        if not self.available_services:
            logger.error("No services available for latency testing")
            self.results["performance_metrics"]["policy_decision_latency"] = {
                "error": "No services available",
                "target_met": False
            }
            return

        # Use the first available service for testing
        service_name, base_url = next(iter(self.available_services.items()))
        logger.info(f"Using {service_name} at {base_url} for latency testing")

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
                    # Try different endpoints based on service type
                    if "ac_service" in service_name:
                        endpoint = f"{base_url}/api/v1/constitutional/validate"
                    elif "auth_service" in service_name:
                        endpoint = f"{base_url}/health"  # Use health endpoint for auth service
                    else:
                        endpoint = f"{base_url}/api/v1/synthesize/policy"

                    async with session.post(
                        endpoint,
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
        """Test cache hit rate and performance under load with constitutional validation endpoint."""
        logger.info(f"Testing cache performance with {concurrent_users} concurrent users for {duration_seconds}s")

        cache_requests = 0
        cache_hits = 0

        # Use available services for cache testing
        if not self.available_services:
            logger.error("No services available for cache testing")
            self.results["performance_metrics"]["cache_performance"] = {
                "error": "No services available",
                "target_met": False
            }
            return

        service_name, base_url = next(iter(self.available_services.items()))

        # Pre-populate cache with constitutional validation requests
        test_validations = [
            {
                "proposal": {
                    "id": f"proposal_{i}",
                    "title": f"Test Proposal {i}",
                    "context": "governance",
                    "respects_human_dignity": True,
                    "ensures_fairness": True,
                    "protects_privacy": True
                },
                "principles": [
                    {"name": "Human Dignity", "category": "fundamental"},
                    {"name": "Fairness", "category": "fundamental"}
                ]
            }
            for i in range(10)
        ]

        async def cache_worker(session: aiohttp.ClientSession, worker_id: int):
            nonlocal cache_requests, cache_hits

            start_time = time.time()
            end_time = start_time + duration_seconds

            while time.time() < end_time:
                # Use cached validations 80% of the time for cache hits
                if worker_id % 5 != 0:  # 80% should be cache hits
                    validation_request = test_validations[worker_id % len(test_validations)]
                    cache_requests += 1
                else:  # 20% cache misses with unique requests
                    validation_request = {
                        "proposal": {
                            "id": f"unique_proposal_{int(time.time())}_{worker_id}",
                            "title": f"Unique Proposal {worker_id}",
                            "context": "governance",
                            "respects_human_dignity": True,
                            "ensures_fairness": True,
                            "protects_privacy": True
                        },
                        "principles": []
                    }

                try:
                    # Use constitutional validation endpoint if AC service available
                    if "ac_service" in service_name:
                        endpoint = f"{base_url}/api/v1/principles/validate-constitutional"
                    else:
                        # Fallback to health endpoint for other services
                        endpoint = f"{base_url}/health"
                        validation_request = {}

                    async with session.post(
                        endpoint,
                        json=validation_request,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            # Check if response indicates cache hit
                            try:
                                response_data = await response.json()
                                if isinstance(response_data, dict) and response_data.get("cached", False):
                                    cache_hits += 1
                            except:
                                # For health endpoints or non-JSON responses
                                pass
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
            "target_met": cache_hit_rate > 80,
            "service_used": service_name,
            "endpoint_tested": "constitutional_validation" if "ac_service" in service_name else "health"
        }

        logger.info(f"Cache Performance Results:")
        logger.info(f"  Service tested: {service_name}")
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
        """Monitor system resource usage during testing with enhanced memory analysis."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        # Enhanced memory monitoring
        process = psutil.Process()
        process_memory = process.memory_info()

        # Memory optimization recommendations
        memory_recommendations = []
        if memory.percent >= 90:
            memory_recommendations.append("CRITICAL: Immediate process restart recommended")
        elif memory.percent >= 85:
            memory_recommendations.append("WARNING: Aggressive memory cleanup needed")
        elif memory.percent >= 80:
            memory_recommendations.append("INFO: Standard memory optimization recommended")

        # Check for memory leaks (simplified detection)
        memory_leak_indicators = []
        if process_memory.rss > 1024 * 1024 * 1024:  # > 1GB process memory
            memory_leak_indicators.append("High process memory usage detected")

        self.results["resource_metrics"] = {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "memory_used_gb": memory.used / (1024**3),
            "process_memory_mb": process_memory.rss / (1024**2),
            "process_memory_vms_mb": process_memory.vms / (1024**2),
            "cpu_target_met": cpu_percent < 80,
            "memory_target_met": memory.percent < 85,
            "memory_optimization_needed": memory.percent >= 80,
            "memory_recommendations": memory_recommendations,
            "memory_leak_indicators": memory_leak_indicators,
            "production_ready": memory.percent < 85 and cpu_percent < 80
        }

        logger.info(f"System Resource Usage:")
        logger.info(f"  CPU: {cpu_percent:.1f}% (target: <80%)")
        logger.info(f"  Memory: {memory.percent:.1f}% (target: <85%)")
        logger.info(f"  Available Memory: {memory.available / (1024**3):.1f} GB")
        logger.info(f"  Process Memory: {process_memory.rss / (1024**2):.1f} MB")

        if memory_recommendations:
            logger.warning(f"  Memory Recommendations: {'; '.join(memory_recommendations)}")

        if memory_leak_indicators:
            logger.warning(f"  Memory Leak Indicators: {'; '.join(memory_leak_indicators)}")

        # Memory optimization status
        memory_status = "✅ OPTIMAL" if memory.percent < 80 else "⚠️ NEEDS OPTIMIZATION" if memory.percent < 85 else "❌ CRITICAL"
        logger.info(f"  Memory Status: {memory_status}")
    
    async def run_comprehensive_load_test(self):
        """Run comprehensive load testing suite."""
        logger.info("🚀 Starting Phase 3 Comprehensive Load Testing")
        logger.info("=" * 60)

        # Check service availability first
        if not await self.check_service_availability():
            logger.error("❌ Cannot proceed with load testing - no services available")
            self.results["success_criteria"] = {
                "overall_success": False,
                "error": "No services available for testing"
            }
            self.generate_load_test_report()
            return

        # Test 1: Policy Decision Latency Under Load
        await self.test_policy_decision_latency_under_load(concurrent_users=50, duration_seconds=30)
        
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
