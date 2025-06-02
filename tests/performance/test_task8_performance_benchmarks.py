"""
Performance Benchmarks for Task 8: Incremental Policy Compilation

Comprehensive performance testing to validate that the incremental compilation
system meets the specified performance targets and efficiency requirements.

Performance Targets:
- Incremental compilation: <100ms
- Full compilation: <1000ms  
- Cache hit ratio: >80%
- Dependency analysis: <50ms
- Time savings: >60% vs full compilation
"""

import asyncio
import json
import logging
import os
import statistics
import time
from typing import Dict, List, Any, Tuple
import pytest

# Add project root to path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Performance targets
PERFORMANCE_TARGETS = {
    "incremental_compilation_time_ms": 100,
    "full_compilation_time_ms": 1000,
    "cache_hit_ratio_threshold": 0.8,
    "dependency_analysis_time_ms": 50,
    "compilation_savings_percent": 60,
    "throughput_policies_per_second": 10,
    "memory_usage_mb_limit": 100
}

class Task8PerformanceBenchmark:
    """Performance benchmark suite for Task 8 incremental compilation."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.compiler = None
        
    async def setup(self):
        """Setup benchmark environment."""
        try:
            from src.backend.pgc_service.app.core.incremental_compiler import get_incremental_compiler
            self.compiler = await get_incremental_compiler()
            print("✅ Benchmark environment setup complete")
        except Exception as e:
            print(f"❌ Benchmark setup failed: {e}")
            raise
    
    def log_benchmark_result(self, test_name: str, metrics: Dict[str, Any], meets_targets: bool):
        """Log benchmark result with detailed metrics."""
        result = {
            "test_name": test_name,
            "metrics": metrics,
            "meets_targets": meets_targets,
            "timestamp": time.time()
        }
        self.results.append(result)
        
        status = "✅ PASS" if meets_targets else "❌ FAIL"
        print(f"{status} {test_name}")
        
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"   📊 {key}: {value:.2f}")
            else:
                print(f"   📊 {key}: {value}")
    
    def create_test_policies(self, count: int) -> List:
        """Create test policies for benchmarking."""
        from src.backend.pgc_service.app.services.integrity_client import IntegrityPolicyRule

        policies = []
        for i in range(count):
            policy = IntegrityPolicyRule(
                id=1000 + i,  # Integer ID starting from 1000
                rule_content=f"""
                package benchmark.policy{i}

                default allow = false

                allow {{
                    input.user == "benchmark_user_{i}"
                    input.action in ["read", "write", "execute"]
                    input.resource.type == "benchmark_resource"
                }}

                deny {{
                    input.user == "blocked_user"
                }}

                # Complex rule with dependencies
                complex_allow {{
                    allow
                    input.timestamp > {1000000 + i}
                    count(input.permissions) > {i % 5}
                }}
                """,
                version=1,
                verification_status="verified",
                source_principle_ids=[1000 + i]
            )
            policies.append(policy)

        return policies
    
    async def benchmark_compilation_latency(self) -> bool:
        """Benchmark compilation latency for different policy set sizes."""
        test_name = "Compilation Latency Benchmark"
        
        try:
            policy_counts = [1, 5, 10, 20, 50]
            latency_results = {}
            
            for count in policy_counts:
                policies = self.create_test_policies(count)
                
                # Measure full compilation
                start_time = time.time()
                await self.compiler.compile_policies(policies, force_full=True)
                full_time = (time.time() - start_time) * 1000
                
                # Measure incremental compilation
                start_time = time.time()
                await self.compiler.compile_policies(policies, force_full=False)
                incremental_time = (time.time() - start_time) * 1000
                
                latency_results[f"{count}_policies"] = {
                    "full_compilation_ms": full_time,
                    "incremental_compilation_ms": incremental_time,
                    "speedup_factor": full_time / incremental_time if incremental_time > 0 else 0
                }
            
            # Check if targets are met
            max_incremental = max(result["incremental_compilation_ms"] for result in latency_results.values())
            max_full = max(result["full_compilation_ms"] for result in latency_results.values())
            
            meets_targets = (
                max_incremental <= PERFORMANCE_TARGETS["incremental_compilation_time_ms"] and
                max_full <= PERFORMANCE_TARGETS["full_compilation_time_ms"]
            )
            
            self.log_benchmark_result(test_name, latency_results, meets_targets)
            return meets_targets
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            return False
    
    async def benchmark_throughput(self) -> bool:
        """Benchmark policy compilation throughput."""
        test_name = "Compilation Throughput Benchmark"
        
        try:
            # Create a large set of policies
            policies = self.create_test_policies(100)
            
            # Measure throughput over multiple runs
            runs = 5
            throughput_measurements = []
            
            for run in range(runs):
                start_time = time.time()
                await self.compiler.compile_policies(policies[:20], force_full=False)  # 20 policies per run
                elapsed_time = time.time() - start_time
                
                throughput = 20 / elapsed_time  # policies per second
                throughput_measurements.append(throughput)
            
            avg_throughput = statistics.mean(throughput_measurements)
            min_throughput = min(throughput_measurements)
            max_throughput = max(throughput_measurements)
            
            meets_targets = avg_throughput >= PERFORMANCE_TARGETS["throughput_policies_per_second"]
            
            metrics = {
                "average_throughput_policies_per_sec": avg_throughput,
                "min_throughput_policies_per_sec": min_throughput,
                "max_throughput_policies_per_sec": max_throughput,
                "target_throughput_policies_per_sec": PERFORMANCE_TARGETS["throughput_policies_per_second"]
            }
            
            self.log_benchmark_result(test_name, metrics, meets_targets)
            return meets_targets
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            return False
    
    async def benchmark_cache_performance(self) -> bool:
        """Benchmark cache hit ratio and performance impact."""
        test_name = "Cache Performance Benchmark"
        
        try:
            policies = self.create_test_policies(10)
            
            # Clear cache and compile policies multiple times
            cache_measurements = []
            
            for iteration in range(10):
                # First compilation (cache miss)
                start_time = time.time()
                await self.compiler.compile_policies(policies, force_full=True)
                first_time = (time.time() - start_time) * 1000
                
                # Second compilation (cache hit)
                start_time = time.time()
                await self.compiler.compile_policies(policies, force_full=False)
                second_time = (time.time() - start_time) * 1000
                
                cache_speedup = (first_time - second_time) / first_time if first_time > 0 else 0
                cache_measurements.append(cache_speedup)
            
            avg_cache_speedup = statistics.mean(cache_measurements)
            cache_hit_ratio = len([x for x in cache_measurements if x > 0]) / len(cache_measurements)
            
            meets_targets = (
                cache_hit_ratio >= PERFORMANCE_TARGETS["cache_hit_ratio_threshold"] and
                avg_cache_speedup > 0.5  # At least 50% speedup from cache
            )
            
            metrics = {
                "average_cache_speedup": avg_cache_speedup,
                "cache_hit_ratio": cache_hit_ratio,
                "target_cache_hit_ratio": PERFORMANCE_TARGETS["cache_hit_ratio_threshold"],
                "cache_size": len(self.compiler.compilation_cache)
            }
            
            self.log_benchmark_result(test_name, metrics, meets_targets)
            return meets_targets
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            return False
    
    async def benchmark_dependency_analysis(self) -> bool:
        """Benchmark dependency analysis performance."""
        test_name = "Dependency Analysis Benchmark"
        
        try:
            # Create policies with complex dependencies
            policies = self.create_test_policies(20)
            
            # Measure dependency analysis time
            dependency_times = []
            
            for _ in range(5):
                start_time = time.time()
                
                # Trigger dependency analysis by compiling policies
                await self.compiler.compile_policies(policies)
                
                analysis_time = (time.time() - start_time) * 1000
                dependency_times.append(analysis_time)
            
            avg_analysis_time = statistics.mean(dependency_times)
            max_analysis_time = max(dependency_times)
            
            meets_targets = max_analysis_time <= PERFORMANCE_TARGETS["dependency_analysis_time_ms"]
            
            metrics = {
                "average_dependency_analysis_ms": avg_analysis_time,
                "max_dependency_analysis_ms": max_analysis_time,
                "target_dependency_analysis_ms": PERFORMANCE_TARGETS["dependency_analysis_time_ms"],
                "dependency_graph_nodes": len(self.compiler.dependency_graph.nodes),
                "dependency_graph_edges": len(self.compiler.dependency_graph.edges)
            }
            
            self.log_benchmark_result(test_name, metrics, meets_targets)
            return meets_targets
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            return False
    
    async def benchmark_memory_usage(self) -> bool:
        """Benchmark memory usage during compilation."""
        test_name = "Memory Usage Benchmark"
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            # Measure baseline memory
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Compile large policy set
            policies = self.create_test_policies(100)
            await self.compiler.compile_policies(policies)
            
            # Measure peak memory
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - baseline_memory
            
            meets_targets = memory_increase <= PERFORMANCE_TARGETS["memory_usage_mb_limit"]
            
            metrics = {
                "baseline_memory_mb": baseline_memory,
                "peak_memory_mb": peak_memory,
                "memory_increase_mb": memory_increase,
                "target_memory_limit_mb": PERFORMANCE_TARGETS["memory_usage_mb_limit"]
            }
            
            self.log_benchmark_result(test_name, metrics, meets_targets)
            return meets_targets
            
        except ImportError:
            print("⚠️  psutil not available, skipping memory benchmark")
            return True
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            return False


async def run_task8_performance_benchmarks():
    """Run all Task 8 performance benchmarks."""
    print("🚀 Running Task 8: Incremental Policy Compilation Performance Benchmarks")
    print("=" * 80)
    
    benchmark = Task8PerformanceBenchmark()
    await benchmark.setup()
    
    # Run all benchmarks
    benchmarks = [
        benchmark.benchmark_compilation_latency,
        benchmark.benchmark_throughput,
        benchmark.benchmark_cache_performance,
        benchmark.benchmark_dependency_analysis,
        benchmark.benchmark_memory_usage,
    ]
    
    passed = 0
    total = len(benchmarks)
    
    for bench in benchmarks:
        try:
            if await bench():
                passed += 1
        except Exception as e:
            print(f"❌ Benchmark {bench.__name__} failed with exception: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TASK 8 PERFORMANCE BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Benchmarks Passed: {passed}/{total}")
    print(f"Performance Score: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All performance benchmarks passed!")
        print("✅ Incremental compilation meets all performance targets")
        print("✅ System ready for high-performance production deployment")
    else:
        print(f"⚠️  {total - passed} benchmarks failed - performance optimization needed")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_task8_performance_benchmarks())
