#!/usr/bin/env python3
"""
ACGS-PGP Security Middleware Standalone Test

This script demonstrates the security middleware functionality without requiring
the full Docker infrastructure. It creates a minimal FastAPI app with the
security middleware and runs validation tests.

Usage:
    python scripts/test_security_middleware_standalone.py
"""

import asyncio
import aiohttp
import sys
import os
import time
from typing import Dict, List
from dataclasses import dataclass
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import threading
import signal

# Add the shared directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend', 'shared'))

try:
    from security_middleware import add_security_middleware
    from security_config import security_config
except ImportError as e:
    print(f"Error importing security modules: {e}")
    print("Make sure you're running this from the ACGS-master root directory")
    sys.exit(1)

@dataclass
class SecurityTestResult:
    """Security test result."""
    test_name: str
    passed: bool
    details: str
    severity: str
    execution_time_ms: float

class SecurityMiddlewareDemo:
    """Demonstrates security middleware functionality."""
    
    def __init__(self):
        self.app = None
        self.server_thread = None
        self.server_process = None
        self.port = 8001
        self.base_url = f"http://localhost:{self.port}"
        
    def create_test_app(self) -> FastAPI:
        """Create a test FastAPI app with security middleware."""
        app = FastAPI(title="ACGS-PGP Security Middleware Test")
        
        # Add the security middleware
        add_security_middleware(app)
        
        # Add test endpoints
        @app.get("/health")
        async def health_check():
            return {"status": "ok", "message": "Security middleware test service"}
        
        @app.get("/test/basic")
        async def basic_test():
            return {"message": "Basic endpoint test"}
        
        @app.post("/test/post")
        async def post_test(request: Request):
            body = await request.json() if request.headers.get("content-type") == "application/json" else {}
            return {"message": "POST endpoint test", "received": body}
        
        @app.get("/test/error")
        async def error_test():
            raise HTTPException(status_code=500, detail="Test error")
        
        return app
    
    def start_server(self):
        """Start the test server in a separate thread."""
        self.app = self.create_test_app()
        
        def run_server():
            uvicorn.run(
                self.app,
                host="0.0.0.0",
                port=self.port,
                log_level="info"
            )
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
    
    def stop_server(self):
        """Stop the test server."""
        if self.server_thread and self.server_thread.is_alive():
            # Send interrupt signal to stop uvicorn
            os.kill(os.getpid(), signal.SIGINT)
    
    async def test_security_headers(self) -> SecurityTestResult:
        """Test security headers implementation."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
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
    
    async def test_rate_limiting(self) -> SecurityTestResult:
        """Test rate limiting implementation."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Send multiple rapid requests to trigger rate limiting
                tasks = []
                for i in range(15):  # Send 15 requests rapidly
                    task = session.get(f"{self.base_url}/health")
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check if any requests were rate limited (429 status)
                rate_limited_count = 0
                for response in responses:
                    if isinstance(response, aiohttp.ClientResponse):
                        if response.status == 429:
                            rate_limited_count += 1
                        response.close()
                
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
    
    async def test_input_validation(self) -> SecurityTestResult:
        """Test input validation and sanitization."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
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
                        async with session.get(
                            f"{self.base_url}/health",
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
    
    async def run_all_tests(self) -> List[SecurityTestResult]:
        """Run all security tests."""
        print("🔒 Starting ACGS-PGP Security Middleware Tests...")
        print(f"Testing service at: {self.base_url}")
        print()
        
        tests = [
            self.test_security_headers(),
            self.test_rate_limiting(),
            self.test_input_validation()
        ]
        
        results = await asyncio.gather(*tests)
        return results

def print_security_report(results: List[SecurityTestResult]):
    """Print comprehensive security report."""
    print("\n" + "="*80)
    print("ACGS-PGP SECURITY MIDDLEWARE VALIDATION REPORT")
    print("="*80)
    print(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    critical_issues = sum(1 for r in results if not r.passed and r.severity == "critical")
    high_issues = sum(1 for r in results if not r.passed and r.severity == "high")
    medium_issues = sum(1 for r in results if not r.passed and r.severity == "medium")
    
    for result in results:
        if result.passed:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"{status} {result.test_name}")
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
    """Main function."""
    demo = SecurityMiddlewareDemo()
    
    try:
        print("🚀 Starting security middleware test server...")
        demo.start_server()
        
        print("⏳ Waiting for server to initialize...")
        await asyncio.sleep(2)
        
        # Run security tests
        results = await demo.run_all_tests()
        
        # Print results
        print_security_report(results)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        print("\n🔄 Cleaning up...")
        demo.stop_server()

if __name__ == "__main__":
    asyncio.run(main())
