"""
Performance Benchmark Tests for Governance Synthesis

Tests performance requirements for the enhanced governance synthesis system
with OPA/Rego integration, targeting <50ms policy decision latency.

Phase 3: Performance Optimization and Security Compliance
Enhanced with advanced caching, performance monitoring, and security testing.
"""

import pytest
import asyncio
import time
import statistics
import concurrent.futures
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import redis.asyncio as redis

from src.backend.gs_service.app.services.policy_validator import (
    PolicyValidationEngine,
    PolicyValidationRequest,
    ValidationLevel,
    PolicyType
)
from src.backend.gs_service.app.core.opa_integration import (
    OPAClient,
    PolicyDecisionRequest,
    PolicyDecisionResponse
)

# Phase 3: Performance optimization imports
from src.backend.gs_service.app.services.performance_monitor import (
    PerformanceMonitor,
    PerformanceProfiler,
    SystemResourceMonitor
)
from src.backend.gs_service.app.services.advanced_cache import (
    MultiTierCache,
    LRUCache,
    RedisCache
)
from src.backend.gs_service.app.services.security_compliance import (
    SecurityComplianceService,
    RateLimiter,
    InputValidator
)


@pytest.fixture
def performance_test_config():
    """Configuration for performance tests."""
    return {
        "target_latency_ms": 50,
        "batch_sizes": [1, 10, 50, 100],
        "concurrent_requests": [1, 5, 10, 20],
        "test_iterations": 100,
        "warmup_iterations": 10
    }


@pytest.fixture
def mock_fast_opa_client():
    """Mock OPA client optimized for fast responses."""
    client = AsyncMock()
    
    async def fast_validate_policy(policy_content, policy_path):
        await asyncio.sleep(0.001)  # 1ms simulated processing
        return MagicMock(
            is_valid=True,
            policy_path=policy_path,
            validation_time_ms=1.0,
            errors=[],
            warnings=[],
            syntax_errors=[],
            semantic_errors=[]
        )
    
    async def fast_evaluate_policy(request):
        await asyncio.sleep(0.002)  # 2ms simulated processing
        return PolicyDecisionResponse(
            result={"allowed": True, "compliance_score": 0.9},
            decision_id=f"decision_{int(time.time() * 1000)}",
            decision_time_ms=2.0
        )
    
    client.validate_policy = fast_validate_policy
    client.evaluate_policy = fast_evaluate_policy
    return client


@pytest.fixture
def performance_policy_validator(mock_fast_opa_client):
    """Policy validator configured for performance testing."""
    validator = PolicyValidationEngine()
    validator.opa_client = mock_fast_opa_client
    validator._initialized = True
    return validator


@pytest.fixture
def sample_performance_requests():
    """Generate sample policy validation requests for performance testing."""
    requests = []
    for i in range(100):
        request = PolicyValidationRequest(
            policy_content=f"""
            package acgs.performance.test{i}
            
            default allow := false
            
            allow if {{
                input.user.role == "admin"
                input.resource.type == "governance"
                input.context.test_id == {i}
            }}
            """,
            policy_type=PolicyType.GOVERNANCE_RULE,
            constitutional_principles=[
                {
                    "description": f"Test principle {i}",
                    "type": "fairness",
                    "category": "access_control"
                }
            ],
            existing_policies=[],
            context_data={
                "target_system": "acgs",
                "governance_type": "operational",
                "risk_level": "medium",
                "test_id": i
            },
            validation_level=ValidationLevel.STANDARD
        )
        requests.append(request)
    return requests


class TestSingleRequestLatency:
    """Test latency for single policy validation requests."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_request_latency_target(self, performance_policy_validator, 
                                                sample_performance_requests, performance_test_config):
        """Test that single requests meet the <50ms latency target."""
        latencies = []
        
        # Warmup
        for i in range(performance_test_config["warmup_iterations"]):
            request = sample_performance_requests[i % len(sample_performance_requests)]
            await performance_policy_validator.validate_policy(request)
        
        # Actual test
        for i in range(performance_test_config["test_iterations"]):
            request = sample_performance_requests[i % len(sample_performance_requests)]
            
            start_time = time.time()
            response = await performance_policy_validator.validate_policy(request)
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            
            # Each individual request should meet target
            assert latency_ms < performance_test_config["target_latency_ms"], \
                f"Request latency {latency_ms:.2f}ms exceeded target {performance_test_config['target_latency_ms']}ms"
        
        # Statistical analysis
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        max_latency = max(latencies)
        
        print(f"\nSingle Request Latency Statistics:")
        print(f"Average: {avg_latency:.2f}ms")
        print(f"95th percentile: {p95_latency:.2f}ms")
        print(f"99th percentile: {p99_latency:.2f}ms")
        print(f"Maximum: {max_latency:.2f}ms")
        
        # Performance assertions
        assert avg_latency < performance_test_config["target_latency_ms"] * 0.5, \
            f"Average latency {avg_latency:.2f}ms should be well below target"
        assert p95_latency < performance_test_config["target_latency_ms"], \
            f"95th percentile latency {p95_latency:.2f}ms exceeded target"
        assert p99_latency < performance_test_config["target_latency_ms"] * 1.5, \
            f"99th percentile latency {p99_latency:.2f}ms significantly exceeded target"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_validation_level_performance_impact(self, performance_policy_validator, 
                                                      sample_performance_requests):
        """Test performance impact of different validation levels."""
        request = sample_performance_requests[0]
        validation_levels = [ValidationLevel.BASIC, ValidationLevel.STANDARD, ValidationLevel.COMPREHENSIVE]
        
        results = {}
        
        for level in validation_levels:
            request.validation_level = level
            latencies = []
            
            for _ in range(20):
                start_time = time.time()
                await performance_policy_validator.validate_policy(request)
                end_time = time.time()
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
            
            avg_latency = statistics.mean(latencies)
            results[level.value] = avg_latency
            
            print(f"{level.value} validation average latency: {avg_latency:.2f}ms")
        
        # Basic should be fastest, comprehensive should still meet target
        assert results["basic"] <= results["standard"] <= results["comprehensive"]
        assert results["comprehensive"] < 50, "Even comprehensive validation should meet 50ms target"


class TestBatchProcessingPerformance:
    """Test performance of batch policy validation."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_processing_scaling(self, performance_policy_validator, 
                                          sample_performance_requests, performance_test_config):
        """Test that batch processing scales efficiently."""
        batch_results = {}
        
        for batch_size in performance_test_config["batch_sizes"]:
            batch_requests = sample_performance_requests[:batch_size]
            latencies = []
            
            # Test multiple batches
            for _ in range(5):
                start_time = time.time()
                responses = await performance_policy_validator.batch_validate(batch_requests)
                end_time = time.time()
                
                batch_latency_ms = (end_time - start_time) * 1000
                avg_latency_per_request = batch_latency_ms / batch_size
                
                latencies.append(avg_latency_per_request)
                
                assert len(responses) == batch_size
            
            avg_per_request_latency = statistics.mean(latencies)
            batch_results[batch_size] = avg_per_request_latency
            
            print(f"Batch size {batch_size}: {avg_per_request_latency:.2f}ms per request")
            
            # Per-request latency should remain low even in batches
            assert avg_per_request_latency < performance_test_config["target_latency_ms"], \
                f"Batch processing latency {avg_per_request_latency:.2f}ms exceeded target"
        
        # Batch processing should show efficiency gains
        assert batch_results[100] <= batch_results[1] * 1.5, \
            "Batch processing should not significantly degrade per-request performance"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_batch_processing(self, performance_policy_validator, 
                                             sample_performance_requests, performance_test_config):
        """Test concurrent batch processing performance."""
        batch_size = 10
        
        for concurrent_batches in performance_test_config["concurrent_requests"]:
            # Create concurrent batch tasks
            tasks = []
            for i in range(concurrent_batches):
                start_idx = (i * batch_size) % len(sample_performance_requests)
                end_idx = start_idx + batch_size
                batch_requests = sample_performance_requests[start_idx:end_idx]
                
                task = performance_policy_validator.batch_validate(batch_requests)
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_latency_ms = (end_time - start_time) * 1000
            total_requests = concurrent_batches * batch_size
            avg_latency_per_request = total_latency_ms / total_requests
            
            print(f"Concurrent batches {concurrent_batches}: {avg_latency_per_request:.2f}ms per request")
            
            # Verify all batches completed successfully
            for batch_result in results:
                assert len(batch_result) == batch_size
            
            # Concurrent processing should maintain reasonable performance
            assert avg_latency_per_request < performance_test_config["target_latency_ms"] * 2, \
                f"Concurrent processing latency {avg_latency_per_request:.2f}ms too high"


class TestOPAIntegrationPerformance:
    """Test performance of OPA integration components."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_opa_client_decision_latency(self, mock_fast_opa_client, performance_test_config):
        """Test OPA client policy decision latency."""
        latencies = []
        
        for i in range(performance_test_config["test_iterations"]):
            request = PolicyDecisionRequest(
                input_data={
                    "policy_content": f"package test{i}\ndefault allow := true",
                    "policy_type": "governance_rule",
                    "context": {"test_id": i}
                },
                policy_path="acgs/test/policy",
                explain=False  # Disable explanation for performance
            )
            
            start_time = time.time()
            response = await mock_fast_opa_client.evaluate_policy(request)
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            
            assert latency_ms < performance_test_config["target_latency_ms"]
        
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]
        
        print(f"\nOPA Decision Latency Statistics:")
        print(f"Average: {avg_latency:.2f}ms")
        print(f"95th percentile: {p95_latency:.2f}ms")
        
        assert avg_latency < 10, "OPA decisions should be very fast"
        assert p95_latency < 20, "95th percentile should be well below target"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_policy_validation_latency(self, mock_fast_opa_client, performance_test_config):
        """Test policy validation latency."""
        latencies = []
        
        for i in range(performance_test_config["test_iterations"]):
            policy_content = f"""
            package acgs.performance.test{i}
            default allow := false
            allow if {{ input.user.role == "admin" }}
            """
            
            start_time = time.time()
            result = await mock_fast_opa_client.validate_policy(policy_content, f"test_policy_{i}")
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            
            assert latency_ms < performance_test_config["target_latency_ms"]
        
        avg_latency = statistics.mean(latencies)
        print(f"Policy validation average latency: {avg_latency:.2f}ms")
        
        assert avg_latency < 5, "Policy validation should be very fast"


class TestMemoryAndResourceUsage:
    """Test memory and resource usage during performance tests."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, performance_policy_validator, 
                                         sample_performance_requests):
        """Test memory usage during high-load validation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large batch multiple times
        for _ in range(10):
            batch_requests = sample_performance_requests[:50]
            await performance_policy_validator.batch_validate(batch_requests)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        # Memory increase should be reasonable
        assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB too high"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_performance_impact(self, performance_test_config):
        """Test performance impact of caching."""
        from src.backend.gs_service.app.core.opa_integration import PolicyDecisionCache
        
        cache = PolicyDecisionCache(max_size=1000, ttl_seconds=300)
        
        # Test cache hit performance
        request = PolicyDecisionRequest(
            input_data={"test": "data"},
            policy_path="test/policy"
        )
        
        # Mock response
        response = PolicyDecisionResponse(
            result={"allowed": True},
            decision_id="test_decision",
            decision_time_ms=5.0
        )
        
        # Cache the response
        await cache.put(request, response)

        # Measure cache hit latency
        cache_hit_latencies = []
        for _ in range(1000):
            start_time = time.time()
            cached_response = await cache.get(request)
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            cache_hit_latencies.append(latency_ms)
            
            assert cached_response is not None
        
        avg_cache_latency = statistics.mean(cache_hit_latencies)
        print(f"Cache hit average latency: {avg_cache_latency:.4f}ms")
        
        # Cache hits should be extremely fast
        assert avg_cache_latency < 0.1, "Cache hits should be sub-millisecond"


class TestThroughputMeasurement:
    """Test system throughput under various conditions."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_maximum_throughput(self, performance_policy_validator, 
                                    sample_performance_requests, performance_test_config):
        """Measure maximum system throughput."""
        test_duration_seconds = 10
        completed_requests = 0
        
        async def validation_worker():
            nonlocal completed_requests
            request_idx = 0
            while True:
                request = sample_performance_requests[request_idx % len(sample_performance_requests)]
                await performance_policy_validator.validate_policy(request)
                completed_requests += 1
                request_idx += 1
        
        # Start multiple workers
        workers = [asyncio.create_task(validation_worker()) for _ in range(10)]
        
        # Run for specified duration
        await asyncio.sleep(test_duration_seconds)
        
        # Stop workers
        for worker in workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*workers, return_exceptions=True)
        
        throughput_per_second = completed_requests / test_duration_seconds
        
        print(f"Maximum throughput: {throughput_per_second:.1f} requests/second")
        print(f"Total requests completed: {completed_requests}")
        
        # Should achieve reasonable throughput
        assert throughput_per_second > 100, f"Throughput {throughput_per_second:.1f} req/s too low"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, performance_policy_validator, 
                                            sample_performance_requests):
        """Test performance under sustained load."""
        sustained_duration_seconds = 30
        batch_size = 20
        batches_completed = 0
        total_latency = 0
        
        start_time = time.time()
        
        while (time.time() - start_time) < sustained_duration_seconds:
            batch_requests = sample_performance_requests[:batch_size]
            
            batch_start = time.time()
            await performance_policy_validator.batch_validate(batch_requests)
            batch_end = time.time()
            
            batch_latency = (batch_end - batch_start) * 1000
            total_latency += batch_latency
            batches_completed += 1
            
            # Brief pause to simulate realistic load
            await asyncio.sleep(0.1)
        
        avg_batch_latency = total_latency / batches_completed
        avg_per_request_latency = avg_batch_latency / batch_size
        total_requests = batches_completed * batch_size
        
        print(f"Sustained load test results:")
        print(f"Duration: {sustained_duration_seconds}s")
        print(f"Total requests: {total_requests}")
        print(f"Average per-request latency: {avg_per_request_latency:.2f}ms")
        print(f"Requests per second: {total_requests / sustained_duration_seconds:.1f}")
        
        # Performance should remain stable under sustained load
        assert avg_per_request_latency < 50, "Performance degraded under sustained load"
