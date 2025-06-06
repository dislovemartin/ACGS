import os, pytest
if not os.environ.get("ACGS_INTEGRATION"):
    pytest.skip("integration test requires running services", allow_module_level=True)

#!/usr/bin/env python3
"""
ACGS-PGP Authentication Service Performance Testing Script
Tests authentication endpoints under load and measures performance metrics.
"""

import asyncio
import aiohttp
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor
import threading

BASE_URL = "http://localhost:8000/api/auth"

class PerformanceMetrics:
    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.errors = []
        self.lock = threading.Lock()
    
    def add_result(self, response_time, success, error_msg=None):
        with self.lock:
            self.response_times.append(response_time)
            if success:
                self.success_count += 1
            else:
                self.error_count += 1
                if error_msg:
                    self.errors.append(error_msg)
    
    def get_stats(self):
        if not self.response_times:
            return {}
        
        return {
            "total_requests": len(self.response_times),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (self.success_count / len(self.response_times)) * 100,
            "avg_response_time": statistics.mean(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "p95_response_time": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times),
            "errors": self.errors[:5]  # Show first 5 errors
        }

async def test_registration_performance(session, user_id, metrics):
    """Test user registration performance."""
    start_time = time.time()
    
    user_data = {
        "username": f"perftest_{user_id}_{int(time.time())}",
        "email": f"perftest_{user_id}_{int(time.time())}@example.com",
        "password": "testpassword123"
    }
    
    try:
        async with session.post(f"{BASE_URL}/register", json=user_data) as response:
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            success = response.status in [200, 201, 400]  # 400 might be "user exists"
            
            if not success:
                error_msg = f"Registration failed: HTTP {response.status}"
                metrics.add_result(response_time, False, error_msg)
            else:
                metrics.add_result(response_time, True)
                
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        metrics.add_result(response_time, False, f"Registration exception: {str(e)}")

async def test_login_performance(session, user_id, metrics):
    """Test user login performance."""
    start_time = time.time()
    
    # Use a known existing user
    login_data = {
        "username": "testworkflow001",
        "password": "testpassword123"
    }
    
    try:
        async with session.post(
            f"{BASE_URL}/token", 
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        ) as response:
            response_time = (time.time() - start_time) * 1000
            success = response.status == 200
            
            if not success:
                error_msg = f"Login failed: HTTP {response.status}"
                metrics.add_result(response_time, False, error_msg)
            else:
                metrics.add_result(response_time, True)
                
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        metrics.add_result(response_time, False, f"Login exception: {str(e)}")

async def test_health_check_performance(session, user_id, metrics):
    """Test health check endpoint performance."""
    start_time = time.time()
    
    try:
        async with session.get(f"{BASE_URL}/health") as response:
            response_time = (time.time() - start_time) * 1000
            success = response.status == 200
            
            if not success:
                error_msg = f"Health check failed: HTTP {response.status}"
                metrics.add_result(response_time, False, error_msg)
            else:
                metrics.add_result(response_time, True)
                
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        metrics.add_result(response_time, False, f"Health check exception: {str(e)}")

async def run_concurrent_test(test_func, num_requests, concurrency, test_name):
    """Run a test function with specified concurrency."""
    print(f"🔍 Running {test_name} - {num_requests} requests with {concurrency} concurrent users")
    
    metrics = PerformanceMetrics()
    
    # Create connector with connection pooling
    connector = aiohttp.TCPConnector(limit=concurrency * 2, limit_per_host=concurrency * 2)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def limited_test(user_id):
            async with semaphore:
                await test_func(session, user_id, metrics)
        
        # Run all requests
        start_time = time.time()
        tasks = [limited_test(i) for i in range(num_requests)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
    
    # Calculate and display results
    stats = metrics.get_stats()
    
    print(f"   📊 {test_name} Results:")
    print(f"      Total Time: {total_time:.2f}s")
    print(f"      Requests/sec: {num_requests/total_time:.2f}")
    print(f"      Success Rate: {stats.get('success_rate', 0):.1f}%")
    print(f"      Avg Response Time: {stats.get('avg_response_time', 0):.2f}ms")
    print(f"      Min/Max Response Time: {stats.get('min_response_time', 0):.2f}ms / {stats.get('max_response_time', 0):.2f}ms")
    print(f"      P95 Response Time: {stats.get('p95_response_time', 0):.2f}ms")
    
    if stats.get('errors'):
        print(f"      Sample Errors: {stats['errors'][:3]}")
    
    # Performance targets
    target_response_time = 200  # ms
    target_success_rate = 95    # %
    
    meets_targets = (
        stats.get('avg_response_time', float('inf')) <= target_response_time and
        stats.get('success_rate', 0) >= target_success_rate
    )
    
    status = "✅ PASS" if meets_targets else "❌ FAIL"
    print(f"      Performance Target: {status}")
    
    return meets_targets, stats

async def main():
    """Run comprehensive performance tests."""
    print("🚀 ACGS-PGP Authentication Service Performance Test")
    print("=" * 70)
    
    # Test configurations
    tests = [
        (test_health_check_performance, 100, 10, "Health Check Load Test"),
        (test_login_performance, 50, 5, "Login Performance Test"),
        (test_registration_performance, 20, 3, "Registration Performance Test"),
    ]
    
    results = []
    
    for test_func, num_requests, concurrency, test_name in tests:
        try:
            meets_targets, stats = await run_concurrent_test(
                test_func, num_requests, concurrency, test_name
            )
            results.append((test_name, meets_targets, stats))
            print()
        except Exception as e:
            print(f"   ❌ {test_name} failed with error: {str(e)}")
            results.append((test_name, False, {}))
            print()
    
    # Summary
    print("=" * 70)
    print("📈 Performance Test Summary:")
    
    passed_tests = sum(1 for _, passed, _ in results if passed)
    total_tests = len(results)
    
    for test_name, passed, stats in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        avg_time = stats.get('avg_response_time', 0)
        success_rate = stats.get('success_rate', 0)
        print(f"   {status} {test_name}: {avg_time:.1f}ms avg, {success_rate:.1f}% success")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All performance tests passed! Authentication service is production-ready.")
    else:
        print("⚠️  Some performance tests failed. Review and optimize before production.")

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import pytest

@pytest.mark.skipif(not os.environ.get("ACGS_INTEGRATION"), reason="Integration test requires running services")
def test_main_wrapper():
    if 'main' in globals():
        if asyncio.iscoroutinefunction(main):
            asyncio.run(main())
        else:
            main()
