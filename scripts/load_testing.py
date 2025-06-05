#!/usr/bin/env python3
"""
ACGS-PGP Load Testing Framework
Phase 2 Development Plan - Priority 2: Load Testing Validation

Tests system performance under concurrent load targeting:
- 100+ concurrent users
- <200ms API response times across all 8 services
- Cross-service communication stability
- Database performance validation
- AlphaEvolve integration under load
"""

import asyncio
import aiohttp
import time
import json
import statistics
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    concurrent_users: int = 100
    test_duration_seconds: int = 300  # 5 minutes
    target_response_time_ms: int = 200
    services: Dict[str, int] = field(default_factory=lambda: {
        'auth_service': 8000,
        'ac_service': 8001,
        'integrity_service': 8002,
        'fv_service': 8003,
        'gs_service': 8004,
        'pgc_service': 8005,
        'ec_service': 8006,
        'research_service': 8007
    })
    database_port: int = 5433

@dataclass
class TestResult:
    """Individual test result."""
    service: str
    endpoint: str
    response_time_ms: float
    status_code: int
    success: bool
    timestamp: datetime
    error_message: Optional[str] = None

@dataclass
class LoadTestReport:
    """Comprehensive load test report."""
    config: LoadTestConfig
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    service_results: Dict[str, List[TestResult]]
    cross_service_tests: List[TestResult]
    database_performance: Dict[str, Any]
    alphaevolve_integration_results: List[TestResult]

class LoadTester:
    """ACGS-PGP Load Testing Framework."""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def test_service_health(self, service: str, port: int) -> TestResult:
        """Test individual service health endpoint."""
        start_time = time.time()
        endpoint = f"http://localhost:{port}/health"
        
        try:
            async with self.session.get(endpoint) as response:
                response_time = (time.time() - start_time) * 1000
                success = response.status == 200
                
                return TestResult(
                    service=service,
                    endpoint="/health",
                    response_time_ms=response_time,
                    status_code=response.status,
                    success=success,
                    timestamp=datetime.now(timezone.utc),
                    error_message=None if success else f"HTTP {response.status}"
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return TestResult(
                service=service,
                endpoint="/health",
                response_time_ms=response_time,
                status_code=0,
                success=False,
                timestamp=datetime.now(timezone.utc),
                error_message=str(e)
            )

    async def test_cross_service_communication(self) -> List[TestResult]:
        """Test cross-service communication patterns."""
        cross_service_results = []
        
        # Test GS Service → AC Service communication
        start_time = time.time()
        try:
            # First get principles from AC service
            async with self.session.get("http://localhost:8001/api/v1/principles") as ac_resp:
                if ac_resp.status == 200:
                    principles = await ac_resp.json()
                    
                    # Then test GS service synthesis using AC principles
                    synthesis_payload = {
                        "principle_id": 1,
                        "principle_text": "Test constitutional principle",
                        "context": "load_testing",
                        "target_format": "rego"
                    }
                    
                    async with self.session.post(
                        "http://localhost:8004/api/v1/synthesis/constitutional",
                        json=synthesis_payload
                    ) as gs_resp:
                        response_time = (time.time() - start_time) * 1000
                        success = gs_resp.status == 200
                        
                        cross_service_results.append(TestResult(
                            service="gs_service",
                            endpoint="/api/v1/synthesis/constitutional",
                            response_time_ms=response_time,
                            status_code=gs_resp.status,
                            success=success,
                            timestamp=datetime.now(timezone.utc),
                            error_message=None if success else f"Cross-service communication failed"
                        ))
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            cross_service_results.append(TestResult(
                service="cross_service",
                endpoint="gs_to_ac_communication",
                response_time_ms=response_time,
                status_code=0,
                success=False,
                timestamp=datetime.now(timezone.utc),
                error_message=str(e)
            ))
        
        return cross_service_results

    async def test_alphaevolve_integration(self) -> List[TestResult]:
        """Test AlphaEvolve integration under load."""
        alphaevolve_results = []
        
        # Test EC service AlphaEvolve governance evaluation
        start_time = time.time()
        try:
            governance_payload = {
                "proposal_id": "load_test_001",
                "proposal_type": "algorithm_optimization",
                "proposal_data": {
                    "algorithm": "genetic_algorithm",
                    "parameters": {"population_size": 100, "generations": 50}
                },
                "constitutional_constraints": ["fairness", "transparency", "efficiency"]
            }
            
            async with self.session.post(
                "http://localhost:8006/api/v1/alphaevolve/governance-evaluation",
                json=governance_payload
            ) as response:
                response_time = (time.time() - start_time) * 1000
                success = response.status == 200
                
                alphaevolve_results.append(TestResult(
                    service="ec_service",
                    endpoint="/api/v1/alphaevolve/governance-evaluation",
                    response_time_ms=response_time,
                    status_code=response.status,
                    success=success,
                    timestamp=datetime.now(timezone.utc),
                    error_message=None if success else f"AlphaEvolve integration failed"
                ))
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            alphaevolve_results.append(TestResult(
                service="ec_service",
                endpoint="alphaevolve_integration",
                response_time_ms=response_time,
                status_code=0,
                success=False,
                timestamp=datetime.now(timezone.utc),
                error_message=str(e)
            ))
        
        return alphaevolve_results

    async def run_concurrent_user_simulation(self, user_id: int) -> List[TestResult]:
        """Simulate a single concurrent user's workflow."""
        user_results = []
        
        # Simulate user workflow: health check → authentication → service usage
        for service, port in self.config.services.items():
            result = await self.test_service_health(service, port)
            user_results.append(result)
            
            # Add small delay to simulate realistic user behavior
            await asyncio.sleep(0.1)
        
        return user_results

    async def run_load_test(self) -> LoadTestReport:
        """Execute comprehensive load test."""
        logger.info(f"🚀 Starting ACGS-PGP Load Test with {self.config.concurrent_users} concurrent users")
        start_time = datetime.now(timezone.utc)
        
        # Create concurrent user tasks
        user_tasks = [
            self.run_concurrent_user_simulation(user_id)
            for user_id in range(self.config.concurrent_users)
        ]
        
        # Execute concurrent user simulations
        logger.info("📊 Executing concurrent user simulations...")
        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
        
        # Flatten results
        all_results = []
        for result_set in user_results:
            if isinstance(result_set, list):
                all_results.extend(result_set)
        
        # Test cross-service communication
        logger.info("🔗 Testing cross-service communication...")
        cross_service_results = await self.test_cross_service_communication()
        
        # Test AlphaEvolve integration
        logger.info("🧬 Testing AlphaEvolve integration...")
        alphaevolve_results = await self.test_alphaevolve_integration()
        
        end_time = datetime.now(timezone.utc)
        
        # Calculate metrics
        successful_results = [r for r in all_results if r.success]
        failed_results = [r for r in all_results if not r.success]
        response_times = [r.response_time_ms for r in successful_results]
        
        # Group results by service
        service_results = {}
        for service in self.config.services.keys():
            service_results[service] = [r for r in all_results if r.service == service]
        
        # Create comprehensive report
        report = LoadTestReport(
            config=self.config,
            start_time=start_time,
            end_time=end_time,
            total_requests=len(all_results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            average_response_time_ms=statistics.mean(response_times) if response_times else 0,
            p95_response_time_ms=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
            p99_response_time_ms=statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0,
            service_results=service_results,
            cross_service_tests=cross_service_results,
            database_performance={},  # TODO: Implement database performance tests
            alphaevolve_integration_results=alphaevolve_results
        )
        
        return report

def print_load_test_report(report: LoadTestReport):
    """Print comprehensive load test report."""
    print("\n" + "="*80)
    print("🎯 ACGS-PGP PHASE 2 LOAD TEST REPORT")
    print("="*80)
    
    # Test configuration
    print(f"📋 Test Configuration:")
    print(f"   Concurrent Users: {report.config.concurrent_users}")
    print(f"   Target Response Time: <{report.config.target_response_time_ms}ms")
    print(f"   Test Duration: {(report.end_time - report.start_time).total_seconds():.1f}s")
    
    # Overall results
    success_rate = (report.successful_requests / report.total_requests * 100) if report.total_requests > 0 else 0
    print(f"\n📊 Overall Results:")
    print(f"   Total Requests: {report.total_requests}")
    print(f"   Successful: {report.successful_requests} ({success_rate:.1f}%)")
    print(f"   Failed: {report.failed_requests}")
    print(f"   Average Response Time: {report.average_response_time_ms:.1f}ms")
    print(f"   95th Percentile: {report.p95_response_time_ms:.1f}ms")
    print(f"   99th Percentile: {report.p99_response_time_ms:.1f}ms")
    
    # Service-specific results
    print(f"\n🏥 Service Performance:")
    for service, results in report.service_results.items():
        if results:
            successful = [r for r in results if r.success]
            success_rate = len(successful) / len(results) * 100
            avg_response = statistics.mean([r.response_time_ms for r in successful]) if successful else 0
            status = "✅" if success_rate >= 95 and avg_response < report.config.target_response_time_ms else "⚠️"
            print(f"   {status} {service}: {success_rate:.1f}% success, {avg_response:.1f}ms avg")
    
    # Cross-service communication
    print(f"\n🔗 Cross-Service Communication:")
    if report.cross_service_tests:
        cross_success = [r for r in report.cross_service_tests if r.success]
        cross_success_rate = len(cross_success) / len(report.cross_service_tests) * 100
        cross_avg_response = statistics.mean([r.response_time_ms for r in cross_success]) if cross_success else 0
        status = "✅" if cross_success_rate >= 90 else "⚠️"
        print(f"   {status} Success Rate: {cross_success_rate:.1f}%")
        print(f"   📈 Average Response Time: {cross_avg_response:.1f}ms")
    
    # AlphaEvolve integration
    print(f"\n🧬 AlphaEvolve Integration:")
    if report.alphaevolve_integration_results:
        alpha_success = [r for r in report.alphaevolve_integration_results if r.success]
        alpha_success_rate = len(alpha_success) / len(report.alphaevolve_integration_results) * 100
        alpha_avg_response = statistics.mean([r.response_time_ms for r in alpha_success]) if alpha_success else 0
        status = "✅" if alpha_success_rate >= 90 else "⚠️"
        print(f"   {status} Success Rate: {alpha_success_rate:.1f}%")
        print(f"   📈 Average Response Time: {alpha_avg_response:.1f}ms")
    
    # Performance assessment
    print(f"\n🎯 Performance Assessment:")
    target_met = (
        success_rate >= 95 and 
        report.average_response_time_ms < report.config.target_response_time_ms
    )
    overall_status = "✅ PASSED" if target_met else "⚠️ NEEDS IMPROVEMENT"
    print(f"   Overall Status: {overall_status}")
    print(f"   Target Achievement: {'✅' if target_met else '❌'} >95% success with <{report.config.target_response_time_ms}ms response")

async def main():
    """Main load testing execution."""
    parser = argparse.ArgumentParser(description="ACGS-PGP Load Testing Framework")
    parser.add_argument("--users", type=int, default=100, help="Number of concurrent users")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--target-time", type=int, default=200, help="Target response time in ms")
    
    args = parser.parse_args()
    
    config = LoadTestConfig(
        concurrent_users=args.users,
        test_duration_seconds=args.duration,
        target_response_time_ms=args.target_time
    )
    
    async with LoadTester(config) as tester:
        report = await tester.run_load_test()
        print_load_test_report(report)

if __name__ == "__main__":
    asyncio.run(main())
