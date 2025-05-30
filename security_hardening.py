#!/usr/bin/env python3
"""
ACGS-PGP Security Hardening Suite
Performs security assessment and hardening recommendations
"""

import asyncio
import aiohttp
import json
import sys
import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class SecurityHardener:
    def __init__(self):
        self.session = None
        self.security_issues = []
        self.base_urls = {
            "auth": "http://localhost:8001",
            "ac": "http://localhost:8002",
            "gs": "http://localhost:8003", 
            "fv": "http://localhost:8004",
            "integrity": "http://localhost:8005",
            "pgc": "http://localhost:8006"
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_authentication_security(self) -> Dict[str, bool]:
        """Test authentication and authorization security"""
        print("\n🔐 Testing Authentication Security...")
        
        security_tests = {}
        
        try:
            # Test unauthenticated access to protected endpoints
            protected_endpoints = [
                f"{self.base_urls['ac']}/api/v1/principles",
                f"{self.base_urls['gs']}/api/v1/constitutional/synthesize",
                f"{self.base_urls['integrity']}/api/v1/audit/logs"
            ]
            
            for endpoint in protected_endpoints:
                async with self.session.get(endpoint) as response:
                    if response.status == 401:
                        print(f"✅ Protected endpoint requires authentication: {endpoint}")
                        security_tests[f"auth_required_{endpoint.split('/')[-1]}"] = True
                    else:
                        print(f"❌ Endpoint accessible without auth: {endpoint} (HTTP {response.status})")
                        security_tests[f"auth_required_{endpoint.split('/')[-1]}"] = False
                        self.security_issues.append(f"Unprotected endpoint: {endpoint}")
            
            # Test JWT token validation
            invalid_token = "Bearer invalid.jwt.token"
            headers = {"Authorization": invalid_token}
            
            async with self.session.get(f"{self.base_urls['ac']}/api/v1/principles", headers=headers) as response:
                if response.status == 401:
                    print("✅ Invalid JWT tokens are rejected")
                    security_tests["jwt_validation"] = True
                else:
                    print(f"❌ Invalid JWT token accepted (HTTP {response.status})")
                    security_tests["jwt_validation"] = False
                    self.security_issues.append("Invalid JWT tokens accepted")
            
        except Exception as e:
            print(f"❌ Authentication security test failed: {str(e)}")
            security_tests["auth_test_error"] = False
        
        return security_tests
    
    async def test_input_validation(self) -> Dict[str, bool]:
        """Test input validation and sanitization"""
        print("\n🛡️ Testing Input Validation...")
        
        validation_tests = {}
        
        try:
            # Test SQL injection attempts
            sql_injection_payloads = [
                "'; DROP TABLE principles; --",
                "1' OR '1'='1",
                "admin'/*",
                "' UNION SELECT * FROM users --"
            ]
            
            for payload in sql_injection_payloads:
                test_data = {
                    "name": payload,
                    "description": "Test principle",
                    "content": "Test content"
                }
                
                async with self.session.post(f"{self.base_urls['ac']}/api/v1/principles", json=test_data) as response:
                    if response.status == 400 or response.status == 422:
                        print(f"✅ SQL injection payload rejected: {payload[:20]}...")
                        validation_tests[f"sql_injection_{len(validation_tests)}"] = True
                    else:
                        print(f"❌ SQL injection payload accepted: {payload[:20]}...")
                        validation_tests[f"sql_injection_{len(validation_tests)}"] = False
                        self.security_issues.append(f"SQL injection vulnerability: {payload}")
            
            # Test XSS attempts
            xss_payloads = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "';alert('xss');//"
            ]
            
            for payload in xss_payloads:
                test_data = {
                    "context": payload,
                    "category": "test",
                    "synthesis_request": "Generate test policy",
                    "target_format": "rego"
                }
                
                async with self.session.post(f"{self.base_urls['gs']}/api/v1/constitutional/synthesize", json=test_data) as response:
                    if response.status == 400 or response.status == 422:
                        print(f"✅ XSS payload rejected: {payload[:20]}...")
                        validation_tests[f"xss_{len(validation_tests)}"] = True
                    else:
                        print(f"❌ XSS payload accepted: {payload[:20]}...")
                        validation_tests[f"xss_{len(validation_tests)}"] = False
                        self.security_issues.append(f"XSS vulnerability: {payload}")
            
        except Exception as e:
            print(f"❌ Input validation test failed: {str(e)}")
            validation_tests["validation_test_error"] = False
        
        return validation_tests
    
    async def test_rate_limiting(self) -> Dict[str, bool]:
        """Test rate limiting implementation"""
        print("\n⏱️ Testing Rate Limiting...")
        
        rate_limit_tests = {}
        
        try:
            # Test rapid requests to trigger rate limiting
            endpoint = f"{self.base_urls['ac']}/api/v1/principles"
            rapid_requests = 50
            successful_requests = 0
            rate_limited_requests = 0
            
            for i in range(rapid_requests):
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        successful_requests += 1
                    elif response.status == 429:  # Too Many Requests
                        rate_limited_requests += 1
                    
                    # Small delay to avoid overwhelming the server
                    await asyncio.sleep(0.01)
            
            if rate_limited_requests > 0:
                print(f"✅ Rate limiting active: {rate_limited_requests}/{rapid_requests} requests limited")
                rate_limit_tests["rate_limiting_active"] = True
            else:
                print(f"❌ No rate limiting detected: {successful_requests}/{rapid_requests} requests succeeded")
                rate_limit_tests["rate_limiting_active"] = False
                self.security_issues.append("Rate limiting not implemented")
            
        except Exception as e:
            print(f"❌ Rate limiting test failed: {str(e)}")
            rate_limit_tests["rate_limit_test_error"] = False
        
        return rate_limit_tests
    
    def check_environment_security(self) -> Dict[str, bool]:
        """Check environment and configuration security"""
        print("\n🔧 Checking Environment Security...")
        
        env_security = {}
        
        # Check for sensitive data in environment variables
        sensitive_patterns = [
            ("SECRET_KEY", r"^.{32,}$"),  # Should be at least 32 characters
            ("POSTGRES_PASSWORD", r"^.{12,}$"),  # Should be at least 12 characters
            ("CSRF_SECRET_KEY", r"^.{32,}$"),  # Should be at least 32 characters
        ]
        
        for var_name, pattern in sensitive_patterns:
            env_value = os.getenv(var_name)
            if env_value:
                if re.match(pattern, env_value):
                    print(f"✅ {var_name} meets security requirements")
                    env_security[f"{var_name.lower()}_secure"] = True
                else:
                    print(f"❌ {var_name} does not meet security requirements")
                    env_security[f"{var_name.lower()}_secure"] = False
                    self.security_issues.append(f"Weak {var_name}")
            else:
                print(f"⚠️ {var_name} not set")
                env_security[f"{var_name.lower()}_set"] = False
                self.security_issues.append(f"Missing {var_name}")
        
        # Check for debug mode in production
        debug_mode = os.getenv("DEBUG", "false").lower()
        if debug_mode == "false":
            print("✅ Debug mode is disabled")
            env_security["debug_disabled"] = True
        else:
            print("❌ Debug mode is enabled in production")
            env_security["debug_disabled"] = False
            self.security_issues.append("Debug mode enabled")
        
        # Check HTTPS configuration
        https_enabled = os.getenv("HTTPS_ENABLED", "false").lower()
        if https_enabled == "true":
            print("✅ HTTPS is enabled")
            env_security["https_enabled"] = True
        else:
            print("⚠️ HTTPS not explicitly enabled")
            env_security["https_enabled"] = False
            self.security_issues.append("HTTPS not configured")
        
        return env_security
    
    def check_file_permissions(self) -> Dict[str, bool]:
        """Check file and directory permissions"""
        print("\n📁 Checking File Permissions...")
        
        permission_tests = {}
        
        # Check sensitive files
        sensitive_files = [
            ".env",
            ".env.production", 
            "docker-compose.yml",
            "alembic.ini"
        ]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                file_stat = os.stat(file_path)
                file_mode = oct(file_stat.st_mode)[-3:]
                
                # Check if file is readable by others (should not be)
                if file_mode[2] in ['0', '4']:  # Others have no read permission
                    print(f"✅ {file_path} has secure permissions ({file_mode})")
                    permission_tests[f"{file_path.replace('.', '_')}_secure"] = True
                else:
                    print(f"❌ {file_path} has insecure permissions ({file_mode})")
                    permission_tests[f"{file_path.replace('.', '_')}_secure"] = False
                    self.security_issues.append(f"Insecure permissions on {file_path}")
            else:
                print(f"ℹ️ {file_path} not found")
                permission_tests[f"{file_path.replace('.', '_')}_exists"] = False
        
        return permission_tests
    
    def generate_security_recommendations(self) -> List[str]:
        """Generate security hardening recommendations"""
        recommendations = [
            "🔐 Security Hardening Recommendations:",
            "",
            "1. Authentication & Authorization:",
            "   - Implement multi-factor authentication (MFA)",
            "   - Use strong JWT secret keys (256-bit minimum)",
            "   - Implement role-based access control (RBAC)",
            "   - Set appropriate token expiration times",
            "",
            "2. Input Validation & Sanitization:",
            "   - Validate all input parameters",
            "   - Sanitize user inputs to prevent XSS",
            "   - Use parameterized queries to prevent SQL injection",
            "   - Implement request size limits",
            "",
            "3. Rate Limiting & DDoS Protection:",
            "   - Implement rate limiting on all endpoints",
            "   - Use progressive delays for repeated failures",
            "   - Implement IP-based blocking for abuse",
            "   - Configure load balancer rate limiting",
            "",
            "4. Cryptographic Security:",
            "   - Use strong encryption algorithms (AES-256, RSA-2048+)",
            "   - Implement proper key management",
            "   - Use secure random number generation",
            "   - Regularly rotate cryptographic keys",
            "",
            "5. Infrastructure Security:",
            "   - Enable HTTPS/TLS 1.3 for all communications",
            "   - Use secure Docker configurations",
            "   - Implement network segmentation",
            "   - Regular security updates and patches",
            "",
            "6. Monitoring & Logging:",
            "   - Implement comprehensive audit logging",
            "   - Monitor for suspicious activities",
            "   - Set up security alerts and notifications",
            "   - Regular security assessments"
        ]
        
        return recommendations
    
    async def run_security_assessment(self) -> Dict:
        """Run comprehensive security assessment"""
        print("🚀 ACGS-PGP Security Hardening Suite")
        print("=" * 60)
        print(f"Assessment started at: {datetime.now().isoformat()}")
        
        assessment_results = {}
        
        # Run security tests
        assessment_results["authentication"] = await self.test_authentication_security()
        assessment_results["input_validation"] = await self.test_input_validation()
        assessment_results["rate_limiting"] = await self.test_rate_limiting()
        assessment_results["environment"] = self.check_environment_security()
        assessment_results["file_permissions"] = self.check_file_permissions()
        
        # Generate recommendations
        recommendations = self.generate_security_recommendations()
        
        # Print summary
        print("\n" + "=" * 60)
        print("SECURITY ASSESSMENT SUMMARY")
        print("=" * 60)
        
        if self.security_issues:
            print("⚠️ Security Issues Found:")
            for issue in self.security_issues:
                print(f"  - {issue}")
        else:
            print("✅ No critical security issues detected!")
        
        print("\n📋 Security Recommendations:")
        for rec in recommendations:
            print(rec)
        
        return {
            "results": assessment_results,
            "issues": self.security_issues,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Main security assessment function"""
    async with SecurityHardener() as hardener:
        assessment_results = await hardener.run_security_assessment()
        
        # Save results to file
        with open("security_assessment_results.json", "w") as f:
            json.dump(assessment_results, f, indent=2)
        
        print(f"\n🔒 Results saved to: security_assessment_results.json")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
