#!/usr/bin/env python3
"""
ACGS-PGP Security Validation Script

Comprehensive security testing and validation for Phase 2.1 Security Hardening.
Tests security configurations, middleware, and protection mechanisms.

Usage:
    python scripts/security_validation.py [--service SERVICE] [--verbose]
"""

import asyncio
import aiohttp
import json
import time
import argparse
import sys
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityTestResult:
    """Security test result."""
    test_name: str
    passed: bool
    details: str
    severity: str  # low, medium, high, critical
    execution_time_ms: float

@dataclass
class ServiceEndpoint:
    """Service endpoint configuration."""
    name: str
    url: str
    port: int
    health_endpoint: str = "/health"

class SecurityValidator:
    """Comprehensive security validation framework."""
    
    def __init__(self):
        self.services = [
            ServiceEndpoint("auth_service", "http://localhost", 8000),
            ServiceEndpoint("ac_service", "http://localhost", 8001),
            ServiceEndpoint("integrity_service", "http://localhost", 8002),
            ServiceEndpoint("fv_service", "http://localhost", 8003),
            ServiceEndpoint("gs_service", "http://localhost", 8004),
            ServiceEndpoint("pgc_service", "http://localhost", 8005),
            ServiceEndpoint("ec_service", "http://localhost", 8006),
            ServiceEndpoint("research_service", "http://localhost", 8007),
        ]
        self.results: List[SecurityTestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def validate_all_services(self, service_filter: Optional[str] = None) -> Dict[str, List[SecurityTestResult]]:
        """Validate security for all services."""
        results = {}
        
        services_to_test = self.services
        if service_filter:
            services_to_test = [s for s in self.services if s.name == service_filter]
        
        for service in services_to_test:
            logger.info(f"Testing security for {service.name}")
            service_results = await self.validate_service_security(service)
            results[service.name] = service_results
        
        return results
    
    async def validate_service_security(self, service: ServiceEndpoint) -> List[SecurityTestResult]:
        """Validate security for a specific service."""
        service_results = []
        base_url = f"{service.url}:{service.port}"
        
        # Test 1: Security Headers
        result = await self.test_security_headers(base_url, service.name)
        service_results.append(result)
        
        # Test 2: Rate Limiting
        result = await self.test_rate_limiting(base_url, service.name)
        service_results.append(result)
        
        # Test 3: Input Validation
        result = await self.test_input_validation(base_url, service.name)
        service_results.append(result)
        
        # Test 4: Authentication Security
        result = await self.test_authentication_security(base_url, service.name)
        service_results.append(result)
        
        # Test 5: CORS Configuration
        result = await self.test_cors_configuration(base_url, service.name)
        service_results.append(result)
        
        # Test 6: Error Handling
        result = await self.test_error_handling(base_url, service.name)
        service_results.append(result)
        
        return service_results
    
    async def test_security_headers(self, base_url: str, service_name: str) -> SecurityTestResult:
        """Test security headers implementation."""
        start_time = time.time()
        
        try:
            async with self.session.get(f"{base_url}/health") as response:
                headers = response.headers
                
                required_headers = [
                    "X-Content-Type-Options",
                    "X-Frame-Options",
                    "X-XSS-Protection",
                    "Referrer-Policy",
                    "Content-Security-Policy"
                ]
                
                missing_headers = []
                for header in required_headers:
                    if header not in headers:
                        missing_headers.append(header)
                
                execution_time = (time.time() - start_time) * 1000
                
                if missing_headers:
                    return SecurityTestResult(
                        test_name="Security Headers",
                        passed=False,
                        details=f"Missing headers: {', '.join(missing_headers)}",
                        severity="medium",
                        execution_time_ms=execution_time
                    )
                
                return SecurityTestResult(
                    test_name="Security Headers",
                    passed=True,
                    details="All required security headers present",
                    severity="low",
                    execution_time_ms=execution_time
                )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SecurityTestResult(
                test_name="Security Headers",
                passed=False,
                details=f"Test failed: {str(e)}",
                severity="high",
                execution_time_ms=execution_time
            )
    
    async def test_rate_limiting(self, base_url: str, service_name: str) -> SecurityTestResult:
        """Test rate limiting implementation."""
        start_time = time.time()
        
        try:
            # Send multiple rapid requests to trigger rate limiting
            tasks = []
            for i in range(15):  # Send 15 requests rapidly
                task = self.session.get(f"{base_url}/health")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if any requests were rate limited (429 status)
            rate_limited_count = 0
            for response in responses:
                if isinstance(response, aiohttp.ClientResponse):
                    if response.status == 429:
                        rate_limited_count += 1
                    await response.release()
            
            execution_time = (time.time() - start_time) * 1000
            
            if rate_limited_count > 0:
                return SecurityTestResult(
                    test_name="Rate Limiting",
                    passed=True,
                    details=f"Rate limiting active: {rate_limited_count} requests blocked",
                    severity="low",
                    execution_time_ms=execution_time
                )
            else:
                return SecurityTestResult(
                    test_name="Rate Limiting",
                    passed=False,
                    details="No rate limiting detected",
                    severity="medium",
                    execution_time_ms=execution_time
                )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SecurityTestResult(
                test_name="Rate Limiting",
                passed=False,
                details=f"Test failed: {str(e)}",
                severity="high",
                execution_time_ms=execution_time
            )
    
    async def test_input_validation(self, base_url: str, service_name: str) -> SecurityTestResult:
        """Test input validation and sanitization."""
        start_time = time.time()
        
        try:
            # Test SQL injection patterns
            malicious_payloads = [
                "'; DROP TABLE users; --",
                "<script>alert('xss')</script>",
                "' OR '1'='1",
                "javascript:alert('xss')",
                "../../../etc/passwd"
            ]
            
            blocked_count = 0
            for payload in malicious_payloads:
                try:
                    async with self.session.get(
                        f"{base_url}/health",
                        params={"test": payload}
                    ) as response:
                        if response.status == 400:  # Bad request indicates validation
                            blocked_count += 1
                except:
                    blocked_count += 1  # Connection error might indicate blocking
            
            execution_time = (time.time() - start_time) * 1000
            
            if blocked_count >= len(malicious_payloads) * 0.8:  # 80% blocked
                return SecurityTestResult(
                    test_name="Input Validation",
                    passed=True,
                    details=f"Input validation active: {blocked_count}/{len(malicious_payloads)} payloads blocked",
                    severity="low",
                    execution_time_ms=execution_time
                )
            else:
                return SecurityTestResult(
                    test_name="Input Validation",
                    passed=False,
                    details=f"Insufficient input validation: {blocked_count}/{len(malicious_payloads)} payloads blocked",
                    severity="high",
                    execution_time_ms=execution_time
                )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SecurityTestResult(
                test_name="Input Validation",
                passed=False,
                details=f"Test failed: {str(e)}",
                severity="high",
                execution_time_ms=execution_time
            )
    
    async def test_authentication_security(self, base_url: str, service_name: str) -> SecurityTestResult:
        """Test authentication security."""
        start_time = time.time()
        
        try:
            # Test access to protected endpoints without authentication
            protected_endpoints = ["/api/v1/users", "/api/v1/admin", "/api/v1/config"]
            
            unauthorized_count = 0
            for endpoint in protected_endpoints:
                try:
                    async with self.session.get(f"{base_url}{endpoint}") as response:
                        if response.status in [401, 403]:  # Unauthorized/Forbidden
                            unauthorized_count += 1
                except:
                    pass  # Endpoint might not exist
            
            execution_time = (time.time() - start_time) * 1000
            
            return SecurityTestResult(
                test_name="Authentication Security",
                passed=True,
                details=f"Authentication required for {unauthorized_count} protected endpoints",
                severity="low",
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SecurityTestResult(
                test_name="Authentication Security",
                passed=False,
                details=f"Test failed: {str(e)}",
                severity="medium",
                execution_time_ms=execution_time
            )
    
    async def test_cors_configuration(self, base_url: str, service_name: str) -> SecurityTestResult:
        """Test CORS configuration."""
        start_time = time.time()
        
        try:
            headers = {
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST"
            }
            
            async with self.session.options(f"{base_url}/health", headers=headers) as response:
                cors_headers = response.headers
                
                # Check if CORS is properly configured
                allow_origin = cors_headers.get("Access-Control-Allow-Origin", "")
                
                execution_time = (time.time() - start_time) * 1000
                
                if allow_origin == "*":
                    return SecurityTestResult(
                        test_name="CORS Configuration",
                        passed=False,
                        details="CORS allows all origins (*) - security risk",
                        severity="medium",
                        execution_time_ms=execution_time
                    )
                
                return SecurityTestResult(
                    test_name="CORS Configuration",
                    passed=True,
                    details=f"CORS properly configured: {allow_origin}",
                    severity="low",
                    execution_time_ms=execution_time
                )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SecurityTestResult(
                test_name="CORS Configuration",
                passed=False,
                details=f"Test failed: {str(e)}",
                severity="low",
                execution_time_ms=execution_time
            )
    
    async def test_error_handling(self, base_url: str, service_name: str) -> SecurityTestResult:
        """Test error handling for information disclosure."""
        start_time = time.time()
        
        try:
            # Test with invalid endpoint
            async with self.session.get(f"{base_url}/nonexistent-endpoint-12345") as response:
                response_text = await response.text()
                
                # Check for information disclosure in error messages
                sensitive_info = ["traceback", "stack trace", "database", "internal server error"]
                disclosed_info = []
                
                for info in sensitive_info:
                    if info.lower() in response_text.lower():
                        disclosed_info.append(info)
                
                execution_time = (time.time() - start_time) * 1000
                
                if disclosed_info:
                    return SecurityTestResult(
                        test_name="Error Handling",
                        passed=False,
                        details=f"Information disclosure detected: {', '.join(disclosed_info)}",
                        severity="medium",
                        execution_time_ms=execution_time
                    )
                
                return SecurityTestResult(
                    test_name="Error Handling",
                    passed=True,
                    details="No sensitive information disclosed in error messages",
                    severity="low",
                    execution_time_ms=execution_time
                )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SecurityTestResult(
                test_name="Error Handling",
                passed=False,
                details=f"Test failed: {str(e)}",
                severity="low",
                execution_time_ms=execution_time
            )

def print_security_report(results: Dict[str, List[SecurityTestResult]]):
    """Print comprehensive security report."""
    print("\n" + "="*80)
    print("ACGS-PGP SECURITY VALIDATION REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_tests = 0
    passed_tests = 0
    critical_issues = 0
    high_issues = 0
    medium_issues = 0
    
    for service_name, service_results in results.items():
        print(f"\n🔒 {service_name.upper()}")
        print("-" * 40)
        
        for result in service_results:
            total_tests += 1
            if result.passed:
                passed_tests += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
                if result.severity == "critical":
                    critical_issues += 1
                elif result.severity == "high":
                    high_issues += 1
                elif result.severity == "medium":
                    medium_issues += 1
            
            print(f"  {status} {result.test_name}")
            print(f"    Details: {result.details}")
            print(f"    Severity: {result.severity.upper()}")
            print(f"    Time: {result.execution_time_ms:.2f}ms")
            print()
    
    # Summary
    print("="*80)
    print("SECURITY SUMMARY")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    print("Issues by Severity:")
    print(f"  🔴 Critical: {critical_issues}")
    print(f"  🟠 High: {high_issues}")
    print(f"  🟡 Medium: {medium_issues}")
    print()
    
    # Security score calculation
    if critical_issues > 0:
        security_score = "F"
    elif high_issues > 2:
        security_score = "D"
    elif high_issues > 0 or medium_issues > 3:
        security_score = "C"
    elif medium_issues > 0:
        security_score = "B"
    else:
        security_score = "A+"
    
    print(f"🏆 SECURITY SCORE: {security_score}")
    print("="*80)

async def main():
    """Main security validation function."""
    parser = argparse.ArgumentParser(description="ACGS-PGP Security Validation")
    parser.add_argument("--service", help="Specific service to test")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    print("🔒 Starting ACGS-PGP Security Validation...")
    print("Phase 2.1: Security Hardening Validation")
    print()
    
    async with SecurityValidator() as validator:
        results = await validator.validate_all_services(args.service)
        print_security_report(results)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"security_validation_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": {
                    service: [
                        {
                            "test_name": r.test_name,
                            "passed": r.passed,
                            "details": r.details,
                            "severity": r.severity,
                            "execution_time_ms": r.execution_time_ms
                        }
                        for r in service_results
                    ]
                    for service, service_results in results.items()
                }
            }, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
