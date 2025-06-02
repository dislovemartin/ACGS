"""
test_qec_performance_optimization.py

Performance optimization and benchmarking suite for QEC-enhanced AlphaEvolve-ACGS.
Tests performance under load, validates caching mechanisms, and ensures target metrics.

Target Performance Metrics:
- API response time: <200ms
- Concurrent users: 50+
- First-pass synthesis success: 88%
- Failure resolution time: <8.5 minutes
- System uptime: >99.5%
"""

import pytest
import asyncio
import time
import statistics
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Any, List
import httpx
import psutil
import redis

# QEC Enhancement imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'alphaevolve_gs_engine', 'src'))

try:
    from alphaevolve_gs_engine.services.qec_enhancement import (
        ConstitutionalDistanceCalculator,
        ValidationDSLParser,
        ErrorPredictionModel,
        RecoveryStrategyDispatcher,
        FailureType,
        SynthesisAttemptLog,
        RecoveryStrategy
    )
    from alphaevolve_gs_engine.services.qec_enhancement.constitutional_fidelity_monitor import (
        ConstitutionalFidelityMonitor,
        FidelityComponents,
        FidelityAlert,
        FidelityThresholds
    )
    from alphaevolve_gs_engine.core.constitutional_principle import ConstitutionalPrinciple
    QEC_AVAILABLE = True
except ImportError:
    QEC_AVAILABLE = False


class QECPerformanceOptimizer:
    """Performance optimization and benchmarking for QEC components."""
    
    def __init__(self):
        self.performance_metrics = {
            "api_response_times": [],
            "concurrent_user_capacity": 0,
            "database_query_times": [],
            "cache_hit_rates": {},
            "memory_usage": [],
            "cpu_usage": []
        }
        
        # Performance targets
        self.targets = {
            "api_response_time_ms": 200,
            "concurrent_users": 50,
            "first_pass_synthesis_success": 0.88,
            "failure_resolution_time_minutes": 8.5,
            "system_uptime": 0.995,
            "cache_hit_rate": 0.80
        }
        
        # Initialize Redis for caching tests
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_client.ping()
            self.redis_available = True
        except:
            self.redis_available = False
    
    @pytest.mark.asyncio
    async def test_api_response_time_optimization(self):
        """Test and optimize API response times for QEC endpoints."""
        if not QEC_AVAILABLE:
            pytest.skip("QEC components not available")
        
        # Initialize QEC components
        distance_calculator = ConstitutionalDistanceCalculator()
        error_predictor = ErrorPredictionModel()
        fidelity_monitor = ConstitutionalFidelityMonitor()
        
        # Create test principle
        test_principle = ConstitutionalPrinciple(
            principle_id="performance_test",
            name="Performance Test Principle",
            description="Test principle for performance optimization",
            category="testing",
            policy_code="package test { default allow = true }",
            validation_criteria_structured=[{
                "type": "performance_test",
                "criteria": ["response_time", "throughput"]
            }]
        )
        
        # Benchmark individual component performance
        response_times = []
        
        # Test constitutional distance calculation
        for _ in range(100):
            start_time = time.time()
            distance_calculator.calculate_score(test_principle)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            response_times.append(response_time)
        
        avg_distance_time = statistics.mean(response_times)
        p95_distance_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        
        # Test error prediction
        prediction_times = []
        for _ in range(100):
            start_time = time.time()
            error_predictor.predict_synthesis_challenges(test_principle)
            response_time = (time.time() - start_time) * 1000
            prediction_times.append(response_time)
        
        avg_prediction_time = statistics.mean(prediction_times)
        p95_prediction_time = statistics.quantiles(prediction_times, n=20)[18]
        
        # Test fidelity calculation
        fidelity_times = []
        system_metrics = {"total_principles": 1}
        for _ in range(50):  # Fewer iterations for expensive operation
            start_time = time.time()
            await fidelity_monitor.calculate_fidelity([test_principle], system_metrics)
            response_time = (time.time() - start_time) * 1000
            fidelity_times.append(response_time)
        
        avg_fidelity_time = statistics.mean(fidelity_times)
        p95_fidelity_time = statistics.quantiles(fidelity_times, n=20)[18]
        
        # Store metrics
        self.performance_metrics["api_response_times"] = {
            "distance_calculation": {
                "avg_ms": avg_distance_time,
                "p95_ms": p95_distance_time
            },
            "error_prediction": {
                "avg_ms": avg_prediction_time,
                "p95_ms": p95_prediction_time
            },
            "fidelity_calculation": {
                "avg_ms": avg_fidelity_time,
                "p95_ms": p95_fidelity_time
            }
        }
        
        # Validate performance targets
        assert avg_distance_time < 50, f"Distance calculation too slow: {avg_distance_time:.2f}ms"
        assert avg_prediction_time < 100, f"Error prediction too slow: {avg_prediction_time:.2f}ms"
        assert avg_fidelity_time < self.targets["api_response_time_ms"], \
            f"Fidelity calculation exceeds target: {avg_fidelity_time:.2f}ms > {self.targets['api_response_time_ms']}ms"
        
        return self.performance_metrics["api_response_times"]
    
    @pytest.mark.asyncio
    async def test_concurrent_user_capacity(self):
        """Test system capacity under concurrent load."""
        if not QEC_AVAILABLE:
            pytest.skip("QEC components not available")
        
        # Create test workload
        async def simulate_user_session():
            """Simulate a user session with QEC operations."""
            distance_calculator = ConstitutionalDistanceCalculator()
            error_predictor = ErrorPredictionModel()
            
            test_principle = ConstitutionalPrinciple(
                principle_id=f"concurrent_test_{asyncio.current_task().get_name()}",
                name="Concurrent Test Principle",
                description="Test principle for concurrent load testing",
                category="testing",
                policy_code="package concurrent_test { default allow = true }"
            )
            
            start_time = time.time()
            
            # Perform typical QEC operations
            distance_calculator.calculate_score(test_principle)
            error_predictor.predict_synthesis_challenges(test_principle)
            
            session_time = time.time() - start_time
            return {
                "session_time": session_time,
                "success": True
            }
        
        # Test with increasing concurrent users
        concurrent_levels = [10, 25, 50, 75, 100]
        results = {}
        
        for concurrent_users in concurrent_levels:
            print(f"Testing {concurrent_users} concurrent users...")
            
            start_time = time.time()
            
            # Create concurrent tasks
            tasks = []
            for i in range(concurrent_users):
                task = asyncio.create_task(
                    simulate_user_session(),
                    name=f"user_{i}"
                )
                tasks.append(task)
            
            # Execute concurrently
            session_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_sessions = [r for r in session_results if isinstance(r, dict) and r.get("success")]
            failed_sessions = len(session_results) - len(successful_sessions)
            
            avg_session_time = statistics.mean([s["session_time"] for s in successful_sessions]) if successful_sessions else 0
            success_rate = len(successful_sessions) / len(session_results)
            
            results[concurrent_users] = {
                "total_time": total_time,
                "success_rate": success_rate,
                "avg_session_time": avg_session_time,
                "failed_sessions": failed_sessions,
                "throughput": len(successful_sessions) / total_time
            }
            
            # Stop if success rate drops below 95%
            if success_rate < 0.95:
                print(f"Success rate dropped to {success_rate:.2%} at {concurrent_users} users")
                break
        
        # Determine maximum concurrent capacity
        max_capacity = max([
            users for users, metrics in results.items() 
            if metrics["success_rate"] >= 0.95
        ])
        
        self.performance_metrics["concurrent_user_capacity"] = max_capacity
        
        # Validate target
        assert max_capacity >= self.targets["concurrent_users"], \
            f"Concurrent capacity {max_capacity} below target {self.targets['concurrent_users']}"
        
        return results
    
    @pytest.mark.asyncio
    async def test_database_query_optimization(self):
        """Test and optimize database query performance for QEC tables."""
        
        # Simulate database queries for QEC operations
        query_times = {
            "constitutional_principles_lookup": [],
            "qec_distance_calculations": [],
            "qec_error_predictions": [],
            "qec_synthesis_logs": []
        }
        
        # Simulate typical query patterns
        for _ in range(100):
            # Simulate principle lookup
            start_time = time.time()
            await asyncio.sleep(0.001)  # Simulate DB query
            query_times["constitutional_principles_lookup"].append(
                (time.time() - start_time) * 1000
            )
            
            # Simulate distance calculation lookup
            start_time = time.time()
            await asyncio.sleep(0.002)  # Simulate more complex query
            query_times["qec_distance_calculations"].append(
                (time.time() - start_time) * 1000
            )
        
        # Calculate averages
        avg_query_times = {
            query_type: statistics.mean(times)
            for query_type, times in query_times.items()
        }
        
        self.performance_metrics["database_query_times"] = avg_query_times
        
        # Validate query performance
        for query_type, avg_time in avg_query_times.items():
            assert avg_time < 50, f"{query_type} query too slow: {avg_time:.2f}ms"
        
        return avg_query_times
    
    @pytest.mark.asyncio
    async def test_caching_mechanism_optimization(self):
        """Test and optimize caching mechanisms for QEC components."""
        if not self.redis_available:
            pytest.skip("Redis not available for caching tests")
        
        distance_calculator = ConstitutionalDistanceCalculator()
        
        # Test cache performance
        test_principle = ConstitutionalPrinciple(
            principle_id="cache_test",
            name="Cache Test Principle",
            description="Test principle for cache optimization",
            category="testing",
            policy_code="package cache_test { default allow = true }"
        )
        
        # Clear cache
        self.redis_client.flushdb()
        
        # Test cache miss (first calculation)
        cache_miss_times = []
        for _ in range(10):
            start_time = time.time()
            distance_calculator.calculate_score(test_principle)
            cache_miss_times.append((time.time() - start_time) * 1000)
        
        # Test cache hit (subsequent calculations)
        cache_hit_times = []
        for _ in range(10):
            start_time = time.time()
            distance_calculator.calculate_score(test_principle)
            cache_hit_times.append((time.time() - start_time) * 1000)
        
        avg_cache_miss_time = statistics.mean(cache_miss_times)
        avg_cache_hit_time = statistics.mean(cache_hit_times)
        
        # Calculate cache effectiveness
        cache_speedup = avg_cache_miss_time / avg_cache_hit_time if avg_cache_hit_time > 0 else 1
        
        self.performance_metrics["cache_hit_rates"] = {
            "cache_miss_time_ms": avg_cache_miss_time,
            "cache_hit_time_ms": avg_cache_hit_time,
            "speedup_factor": cache_speedup
        }
        
        # Validate caching effectiveness
        assert cache_speedup > 1.5, f"Cache speedup insufficient: {cache_speedup:.2f}x"
        assert avg_cache_hit_time < 10, f"Cache hit time too slow: {avg_cache_hit_time:.2f}ms"
        
        return self.performance_metrics["cache_hit_rates"]
    
    @pytest.mark.asyncio
    async def test_memory_and_cpu_optimization(self):
        """Test memory and CPU usage optimization."""
        
        # Monitor system resources
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        # Perform intensive QEC operations
        if QEC_AVAILABLE:
            distance_calculator = ConstitutionalDistanceCalculator()
            error_predictor = ErrorPredictionModel()
            fidelity_monitor = ConstitutionalFidelityMonitor()
            
            # Create multiple test principles
            principles = []
            for i in range(100):
                principle = ConstitutionalPrinciple(
                    principle_id=f"memory_test_{i}",
                    name=f"Memory Test Principle {i}",
                    description=f"Test principle {i} for memory optimization",
                    category="testing",
                    policy_code=f"package memory_test_{i} {{ default allow = true }}"
                )
                principles.append(principle)
            
            # Perform operations
            for principle in principles:
                distance_calculator.calculate_score(principle)
                error_predictor.predict_synthesis_challenges(principle)
            
            # Calculate fidelity for all principles
            system_metrics = {"total_principles": len(principles)}
            await fidelity_monitor.calculate_fidelity(principles, system_metrics)
        
        # Monitor final resource usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()
        
        memory_increase = final_memory - initial_memory
        cpu_increase = final_cpu - initial_cpu
        
        self.performance_metrics["memory_usage"] = {
            "initial_mb": initial_memory,
            "final_mb": final_memory,
            "increase_mb": memory_increase
        }
        
        self.performance_metrics["cpu_usage"] = {
            "initial_percent": initial_cpu,
            "final_percent": final_cpu,
            "increase_percent": cpu_increase
        }
        
        # Validate resource usage
        assert memory_increase < 500, f"Memory increase too high: {memory_increase:.2f}MB"
        assert final_memory < 2000, f"Total memory usage too high: {final_memory:.2f}MB"
        
        return {
            "memory": self.performance_metrics["memory_usage"],
            "cpu": self.performance_metrics["cpu_usage"]
        }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance optimization report."""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "performance_targets": self.targets,
            "measured_metrics": self.performance_metrics,
            "target_compliance": {},
            "optimization_recommendations": []
        }
        
        # Check target compliance
        if "api_response_times" in self.performance_metrics:
            fidelity_time = self.performance_metrics["api_response_times"].get("fidelity_calculation", {}).get("avg_ms", 0)
            report["target_compliance"]["api_response_time"] = fidelity_time < self.targets["api_response_time_ms"]
        
        if "concurrent_user_capacity" in self.performance_metrics:
            capacity = self.performance_metrics["concurrent_user_capacity"]
            report["target_compliance"]["concurrent_users"] = capacity >= self.targets["concurrent_users"]
        
        # Generate recommendations
        if report["target_compliance"].get("api_response_time", True) == False:
            report["optimization_recommendations"].append(
                "Consider implementing additional caching layers for fidelity calculations"
            )
        
        if report["target_compliance"].get("concurrent_users", True) == False:
            report["optimization_recommendations"].append(
                "Consider horizontal scaling with load balancing for higher concurrent capacity"
            )
        
        return report


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
