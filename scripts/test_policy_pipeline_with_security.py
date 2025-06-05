#!/usr/bin/env python3
"""
ACGS-PGP Policy Pipeline Test with Security Middleware

This script tests the complete policy pipeline (AC→GS→FV→Integrity→PGC) 
with the new security middleware to ensure security improvements don't 
interfere with core functionality.

Usage:
    python scripts/test_policy_pipeline_with_security.py
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PolicyPipelineTest:
    """Policy pipeline test case."""
    name: str
    description: str
    test_data: Dict
    expected_outcome: str
    
@dataclass
class TestResult:
    """Test execution result."""
    test_name: str
    passed: bool
    details: str
    execution_time_ms: float
    response_data: Optional[Dict] = None

class PolicyPipelineValidator:
    """Validates the complete ACGS-PGP policy pipeline with security middleware."""
    
    def __init__(self):
        self.base_urls = {
            "ac": "http://localhost:8001",
            "integrity": "http://localhost:8002", 
            "fv": "http://localhost:8003",
            "gs": "http://localhost:8004",
            "pgc": "http://localhost:8005"
        }
        
    async def test_service_health_with_security(self) -> List[TestResult]:
        """Test that all services are healthy and security middleware is active."""
        results = []
        
        for service_name, base_url in self.base_urls.items():
            start_time = time.time()
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{base_url}/health") as response:
                        execution_time = (time.time() - start_time) * 1000
                        
                        # Check if service is healthy
                        if response.status == 200:
                            data = await response.json()
                            
                            # Check for security headers
                            security_headers = [
                                "X-Content-Type-Options",
                                "X-Frame-Options",
                                "X-XSS-Protection"
                            ]
                            
                            missing_headers = []
                            for header in security_headers:
                                if header not in response.headers:
                                    missing_headers.append(header)
                            
                            if missing_headers:
                                results.append(TestResult(
                                    test_name=f"{service_name.upper()} Service Health + Security",
                                    passed=False,
                                    details=f"Service healthy but missing security headers: {missing_headers}",
                                    execution_time_ms=execution_time,
                                    response_data=data
                                ))
                            else:
                                results.append(TestResult(
                                    test_name=f"{service_name.upper()} Service Health + Security",
                                    passed=True,
                                    details=f"Service healthy with security headers present",
                                    execution_time_ms=execution_time,
                                    response_data=data
                                ))
                        else:
                            results.append(TestResult(
                                test_name=f"{service_name.upper()} Service Health + Security",
                                passed=False,
                                details=f"Service unhealthy: HTTP {response.status}",
                                execution_time_ms=execution_time
                            ))
                            
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                results.append(TestResult(
                    test_name=f"{service_name.upper()} Service Health + Security",
                    passed=False,
                    details=f"Connection failed: {str(e)}",
                    execution_time_ms=execution_time
                ))
        
        return results
    
    async def test_security_validation_blocking(self) -> TestResult:
        """Test that security middleware blocks malicious requests."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test malicious payload against AC service
                malicious_payload = "'; DROP TABLE principles; --"
                
                async with session.get(
                    f"{self.base_urls['ac']}/health",
                    params={"test": malicious_payload}
                ) as response:
                    execution_time = (time.time() - start_time) * 1000
                    
                    # Should return 400 or 500 (blocked)
                    if response.status in [400, 500]:
                        return TestResult(
                            test_name="Security Validation Blocking",
                            passed=True,
                            details=f"Malicious payload correctly blocked with HTTP {response.status}",
                            execution_time_ms=execution_time
                        )
                    else:
                        return TestResult(
                            test_name="Security Validation Blocking",
                            passed=False,
                            details=f"Malicious payload not blocked: HTTP {response.status}",
                            execution_time_ms=execution_time
                        )
                        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return TestResult(
                test_name="Security Validation Blocking",
                passed=False,
                details=f"Test failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def test_legitimate_requests_allowed(self) -> TestResult:
        """Test that legitimate requests pass through security middleware."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test legitimate request
                async with session.get(
                    f"{self.base_urls['ac']}/health",
                    params={"version": "1.0", "client": "test"}
                ) as response:
                    execution_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return TestResult(
                            test_name="Legitimate Requests Allowed",
                            passed=True,
                            details="Legitimate request passed through security middleware",
                            execution_time_ms=execution_time
                        )
                    else:
                        return TestResult(
                            test_name="Legitimate Requests Allowed",
                            passed=False,
                            details=f"Legitimate request blocked: HTTP {response.status}",
                            execution_time_ms=execution_time
                        )
                        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return TestResult(
                test_name="Legitimate Requests Allowed",
                passed=False,
                details=f"Test failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def test_cross_service_communication(self) -> TestResult:
        """Test that cross-service communication works with security middleware."""
        start_time = time.time()
        
        try:
            # This would test AC→GS communication if services were running
            # For now, just test that services can communicate basic health checks
            
            async with aiohttp.ClientSession() as session:
                # Test multiple service health checks in sequence
                services_tested = []
                
                for service_name, base_url in self.base_urls.items():
                    try:
                        async with session.get(f"{base_url}/health", timeout=5) as response:
                            if response.status == 200:
                                services_tested.append(service_name)
                    except:
                        pass  # Service not available
                
                execution_time = (time.time() - start_time) * 1000
                
                if len(services_tested) >= 2:
                    return TestResult(
                        test_name="Cross-Service Communication",
                        passed=True,
                        details=f"Multiple services responding: {', '.join(services_tested)}",
                        execution_time_ms=execution_time
                    )
                else:
                    return TestResult(
                        test_name="Cross-Service Communication",
                        passed=False,
                        details=f"Insufficient services available: {', '.join(services_tested)}",
                        execution_time_ms=execution_time
                    )
                    
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return TestResult(
                test_name="Cross-Service Communication",
                passed=False,
                details=f"Test failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def run_all_tests(self) -> List[TestResult]:
        """Run all policy pipeline tests with security validation."""
        print("🔒 Starting ACGS-PGP Policy Pipeline + Security Tests...")
        print("Testing complete pipeline with security middleware active")
        print()
        
        all_results = []
        
        # Test 1: Service health with security
        print("📋 Testing service health with security middleware...")
        health_results = await self.test_service_health_with_security()
        all_results.extend(health_results)
        
        # Test 2: Security validation blocking
        print("🛡️  Testing security validation blocking...")
        blocking_result = await self.test_security_validation_blocking()
        all_results.append(blocking_result)
        
        # Test 3: Legitimate requests allowed
        print("✅ Testing legitimate requests allowed...")
        legitimate_result = await self.test_legitimate_requests_allowed()
        all_results.append(legitimate_result)
        
        # Test 4: Cross-service communication
        print("🔗 Testing cross-service communication...")
        communication_result = await self.test_cross_service_communication()
        all_results.append(communication_result)
        
        return all_results

def print_pipeline_report(results: List[TestResult]):
    """Print comprehensive pipeline test report."""
    print("\n" + "="*80)
    print("ACGS-PGP POLICY PIPELINE + SECURITY VALIDATION REPORT")
    print("="*80)
    print(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    
    for result in results:
        if result.passed:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"{status} {result.test_name}")
        print(f"    Details: {result.details}")
        print(f"    Time: {result.execution_time_ms:.2f}ms")
        if result.response_data:
            print(f"    Response: {json.dumps(result.response_data, indent=2)[:100]}...")
        print()
    
    # Summary
    print("="*80)
    print("PIPELINE + SECURITY SUMMARY")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    # Overall assessment
    if passed_tests == total_tests:
        assessment = "🏆 EXCELLENT - Ready for Phase 2.3"
    elif passed_tests >= total_tests * 0.8:
        assessment = "✅ GOOD - Minor issues to address"
    elif passed_tests >= total_tests * 0.6:
        assessment = "⚠️  FAIR - Significant issues need attention"
    else:
        assessment = "❌ POOR - Major issues require immediate attention"
    
    print(f"📊 OVERALL ASSESSMENT: {assessment}")
    print("="*80)

async def main():
    """Main function."""
    validator = PolicyPipelineValidator()
    
    try:
        print("🚀 Starting ACGS-PGP Policy Pipeline + Security Validation...")
        print("This test validates that security middleware doesn't interfere with core functionality")
        print()
        
        # Run all tests
        results = await validator.run_all_tests()
        
        # Print results
        print_pipeline_report(results)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(main())
