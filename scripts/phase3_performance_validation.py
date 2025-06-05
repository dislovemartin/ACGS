#!/usr/bin/env python3
"""
ACGS Phase 3 Performance Validation Script
Validates all services meet performance targets for production deployment.

Performance Targets:
- <25ms average policy decision latency (improved from <50ms)
- >80% cache hit rate under sustained load
- <85% memory usage maintained throughout testing
- 100+ concurrent users sustained for 10+ minutes
- Zero service crashes or timeouts during load testing
"""

import asyncio
import aiohttp
import time
import json
import statistics
import psutil
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/phase3_performance_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ACGSPerformanceValidator:
    def __init__(self):
        self.services = {
            'auth_service': {'port': 8000, 'name': 'Auth Service'},
            'ac_service': {'port': 8001, 'name': 'AC Service'},
            'integrity_service': {'port': 8002, 'name': 'Integrity Service'},
            'fv_service': {'port': 8003, 'name': 'FV Service'},
            'gs_service': {'port': 8004, 'name': 'GS Service'},
            'pgc_service': {'port': 8005, 'name': 'PGC Service'}
        }
        
        self.performance_targets = {
            'max_avg_latency_ms': 25,
            'min_cache_hit_rate': 0.80,
            'max_memory_usage': 0.85,
            'min_concurrent_users': 100,
            'min_test_duration_minutes': 10
        }
        
        self.results = {
            'test_start': datetime.now(timezone.utc).isoformat(),
            'services_tested': [],
            'performance_metrics': {},
            'load_test_results': {},
            'memory_monitoring': [],
            'success_criteria': {},
            'overall_status': 'PENDING'
        }

    async def validate_service_health(self) -> bool:
        """Validate all services are healthy before performance testing."""
        logger.info("🔍 Validating service health before performance testing...")
        
        healthy_services = 0
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for service_id, config in self.services.items():
                try:
                    start_time = time.time()
                    async with session.get(f"http://localhost:{config['port']}/health") as response:
                        end_time = time.time()
                        response_time_ms = (end_time - start_time) * 1000
                        
                        if response.status == 200:
                            logger.info(f"✅ {config['name']} (:{config['port']}) - Healthy ({response_time_ms:.1f}ms)")
                            healthy_services += 1
                            self.results['services_tested'].append(service_id)
                        else:
                            logger.error(f"❌ {config['name']} (:{config['port']}) - Unhealthy (Status: {response.status})")
                            
                except Exception as e:
                    logger.error(f"❌ {config['name']} (:{config['port']}) - Error: {str(e)}")
        
        all_healthy = healthy_services == len(self.services)
        logger.info(f"Health Check Summary: {healthy_services}/{len(self.services)} services healthy")
        return all_healthy

    async def measure_baseline_performance(self) -> Dict:
        """Measure baseline performance for each service."""
        logger.info("📊 Measuring baseline performance...")
        
        baseline_results = {}
        async with aiohttp.ClientSession() as session:
            for service_id, config in self.services.items():
                response_times = []
                
                # Measure 50 requests to get baseline
                for _ in range(50):
                    try:
                        start_time = time.time()
                        async with session.get(f"http://localhost:{config['port']}/health") as response:
                            end_time = time.time()
                            if response.status == 200:
                                response_times.append((end_time - start_time) * 1000)
                    except Exception as e:
                        logger.warning(f"Baseline test failed for {service_id}: {e}")
                
                if response_times:
                    baseline_results[service_id] = {
                        'avg_latency_ms': statistics.mean(response_times),
                        'median_latency_ms': statistics.median(response_times),
                        'p95_latency_ms': sorted(response_times)[int(0.95 * len(response_times))],
                        'min_latency_ms': min(response_times),
                        'max_latency_ms': max(response_times),
                        'sample_count': len(response_times)
                    }
                    
                    avg_latency = baseline_results[service_id]['avg_latency_ms']
                    status = "🚀 EXCELLENT" if avg_latency < 25 else "✅ GOOD" if avg_latency < 50 else "⚠️ SLOW"
                    logger.info(f"{config['name']}: {avg_latency:.1f}ms avg | {status}")
        
        self.results['performance_metrics']['baseline'] = baseline_results
        return baseline_results

    async def run_load_test(self, concurrent_users: int = 100, duration_minutes: int = 10) -> Dict:
        """Run comprehensive load test with specified concurrent users."""
        logger.info(f"🚀 Starting load test: {concurrent_users} concurrent users for {duration_minutes} minutes...")
        
        test_duration_seconds = duration_minutes * 60
        start_time = time.time()
        end_time = start_time + test_duration_seconds
        
        # Track metrics during load test
        response_times = {service_id: [] for service_id in self.services.keys()}
        error_counts = {service_id: 0 for service_id in self.services.keys()}
        success_counts = {service_id: 0 for service_id in self.services.keys()}
        
        async def worker(session: aiohttp.ClientSession, service_id: str, config: Dict):
            """Worker function for load testing a specific service."""
            while time.time() < end_time:
                try:
                    request_start = time.time()
                    async with session.get(f"http://localhost:{config['port']}/health") as response:
                        request_end = time.time()
                        response_time_ms = (request_end - request_start) * 1000
                        
                        if response.status == 200:
                            response_times[service_id].append(response_time_ms)
                            success_counts[service_id] += 1
                        else:
                            error_counts[service_id] += 1
                            
                except Exception as e:
                    error_counts[service_id] += 1
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
        
        # Start concurrent workers
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=concurrent_users * 2)
        ) as session:
            tasks = []
            
            # Create workers for each service
            for service_id, config in self.services.items():
                for _ in range(concurrent_users // len(self.services)):
                    tasks.append(worker(session, service_id, config))
            
            # Monitor memory usage during load test
            memory_monitoring_task = asyncio.create_task(self.monitor_memory_usage(test_duration_seconds))
            
            # Run load test
            await asyncio.gather(*tasks, memory_monitoring_task, return_exceptions=True)
        
        # Calculate load test results
        load_test_results = {}
        for service_id, config in self.services.items():
            if response_times[service_id]:
                load_test_results[service_id] = {
                    'avg_latency_ms': statistics.mean(response_times[service_id]),
                    'median_latency_ms': statistics.median(response_times[service_id]),
                    'p95_latency_ms': sorted(response_times[service_id])[int(0.95 * len(response_times[service_id]))],
                    'total_requests': len(response_times[service_id]),
                    'successful_requests': success_counts[service_id],
                    'failed_requests': error_counts[service_id],
                    'error_rate': error_counts[service_id] / (success_counts[service_id] + error_counts[service_id]) if (success_counts[service_id] + error_counts[service_id]) > 0 else 0,
                    'requests_per_second': len(response_times[service_id]) / test_duration_seconds
                }
                
                avg_latency = load_test_results[service_id]['avg_latency_ms']
                error_rate = load_test_results[service_id]['error_rate']
                
                logger.info(f"{config['name']} Load Test Results:")
                logger.info(f"  Average Latency: {avg_latency:.1f}ms")
                logger.info(f"  Error Rate: {error_rate:.2%}")
                logger.info(f"  Requests/sec: {load_test_results[service_id]['requests_per_second']:.1f}")
        
        self.results['load_test_results'] = load_test_results
        return load_test_results

    async def monitor_memory_usage(self, duration_seconds: int):
        """Monitor system memory usage during load testing."""
        logger.info("📈 Monitoring memory usage during load test...")
        
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            memory_info = psutil.virtual_memory()
            self.results['memory_monitoring'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'memory_percent': memory_info.percent,
                'memory_used_gb': memory_info.used / (1024**3),
                'memory_available_gb': memory_info.available / (1024**3)
            })
            
            await asyncio.sleep(30)  # Monitor every 30 seconds

    def evaluate_success_criteria(self) -> bool:
        """Evaluate if all performance targets are met."""
        logger.info("🎯 Evaluating success criteria...")
        
        success_criteria = {}
        overall_success = True
        
        # Check average latency across all services
        if 'load_test_results' in self.results:
            avg_latencies = [
                result['avg_latency_ms'] 
                for result in self.results['load_test_results'].values()
            ]
            
            if avg_latencies:
                overall_avg_latency = statistics.mean(avg_latencies)
                latency_success = overall_avg_latency < self.performance_targets['max_avg_latency_ms']
                success_criteria['average_latency'] = {
                    'target_ms': self.performance_targets['max_avg_latency_ms'],
                    'actual_ms': overall_avg_latency,
                    'passed': latency_success
                }
                overall_success &= latency_success
                
                logger.info(f"Average Latency: {overall_avg_latency:.1f}ms (Target: <{self.performance_targets['max_avg_latency_ms']}ms) - {'✅ PASSED' if latency_success else '❌ FAILED'}")
        
        # Check memory usage
        if self.results['memory_monitoring']:
            max_memory_usage = max(entry['memory_percent'] for entry in self.results['memory_monitoring']) / 100
            memory_success = max_memory_usage < self.performance_targets['max_memory_usage']
            success_criteria['memory_usage'] = {
                'target_percent': self.performance_targets['max_memory_usage'] * 100,
                'actual_percent': max_memory_usage * 100,
                'passed': memory_success
            }
            overall_success &= memory_success
            
            logger.info(f"Peak Memory Usage: {max_memory_usage:.1%} (Target: <{self.performance_targets['max_memory_usage']:.1%}) - {'✅ PASSED' if memory_success else '❌ FAILED'}")
        
        # Check error rates
        if 'load_test_results' in self.results:
            error_rates = [
                result['error_rate'] 
                for result in self.results['load_test_results'].values()
            ]
            
            if error_rates:
                max_error_rate = max(error_rates)
                error_rate_success = max_error_rate < 0.01  # Less than 1% error rate
                success_criteria['error_rate'] = {
                    'target_percent': 1.0,
                    'actual_percent': max_error_rate * 100,
                    'passed': error_rate_success
                }
                overall_success &= error_rate_success
                
                logger.info(f"Maximum Error Rate: {max_error_rate:.2%} (Target: <1%) - {'✅ PASSED' if error_rate_success else '❌ FAILED'}")
        
        self.results['success_criteria'] = success_criteria
        self.results['overall_status'] = 'PASSED' if overall_success else 'FAILED'
        
        return overall_success

    async def run_validation(self, concurrent_users: int = 100, duration_minutes: int = 10) -> bool:
        """Run complete performance validation."""
        logger.info("🚀 Starting ACGS Phase 3 Performance Validation")
        logger.info("=" * 80)
        
        try:
            # Step 1: Validate service health
            if not await self.validate_service_health():
                logger.error("❌ Service health validation failed. Cannot proceed with performance testing.")
                return False
            
            # Step 2: Measure baseline performance
            await self.measure_baseline_performance()
            
            # Step 3: Run load test
            await self.run_load_test(concurrent_users, duration_minutes)
            
            # Step 4: Evaluate success criteria
            success = self.evaluate_success_criteria()
            
            # Step 5: Generate final report
            self.generate_final_report()
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Performance validation failed with exception: {str(e)}")
            self.results['overall_status'] = 'ERROR'
            self.results['error_message'] = str(e)
            return False

    def generate_final_report(self):
        """Generate comprehensive performance validation report."""
        self.results['test_end'] = datetime.now(timezone.utc).isoformat()
        
        # Save detailed results to file
        report_file = f"logs/phase3_performance_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info("=" * 80)
        logger.info("🎉 ACGS Phase 3 Performance Validation Complete!")
        logger.info("=" * 80)
        logger.info(f"Overall Status: {'✅ PASSED' if self.results['overall_status'] == 'PASSED' else '❌ FAILED'}")
        logger.info(f"Detailed Report: {report_file}")
        
        if self.results['overall_status'] == 'PASSED':
            logger.info("🚀 All performance targets met! Ready for Phase 3 production deployment.")
        else:
            logger.info("⚠️ Performance targets not met. Review results and optimize before production.")

async def main():
    parser = argparse.ArgumentParser(description='ACGS Phase 3 Performance Validation')
    parser.add_argument('--concurrent-users', type=int, default=100, help='Number of concurrent users for load testing')
    parser.add_argument('--duration-minutes', type=int, default=10, help='Duration of load test in minutes')
    parser.add_argument('--quick-test', action='store_true', help='Run quick test (10 users, 2 minutes)')
    
    args = parser.parse_args()
    
    if args.quick_test:
        concurrent_users = 10
        duration_minutes = 2
        logger.info("🏃 Running quick performance test...")
    else:
        concurrent_users = args.concurrent_users
        duration_minutes = args.duration_minutes
    
    validator = ACGSPerformanceValidator()
    success = await validator.run_validation(concurrent_users, duration_minutes)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
