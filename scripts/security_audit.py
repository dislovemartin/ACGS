#!/usr/bin/env python3
"""
ACGS-PGP Security Audit Framework
Phase 2 Development Plan - Priority 3: Security Audit Implementation

Comprehensive security assessment targeting ≥85% security score:
- CSRF protection validation
- JWT validation improvements
- RBAC testing across all microservices
- Authentication workflow security
- Cryptographic integrity components audit
- Cross-service API communication security
- Vulnerability scanning and hardening recommendations
"""

import asyncio
import aiohttp
import json
import logging
import time
import hashlib
import jwt
import base64
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security assessment levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class SecurityFinding:
    """Individual security finding."""
    category: str
    level: SecurityLevel
    title: str
    description: str
    service: str
    endpoint: Optional[str] = None
    recommendation: Optional[str] = None
    cve_reference: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class SecurityAuditConfig:
    """Security audit configuration."""
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
    target_security_score: float = 85.0
    test_timeout: int = 30

@dataclass
class SecurityAuditReport:
    """Comprehensive security audit report."""
    config: SecurityAuditConfig
    start_time: datetime
    end_time: datetime
    findings: List[SecurityFinding]
    security_score: float
    services_tested: int
    vulnerabilities_found: int
    recommendations: List[str]

class SecurityAuditor:
    """ACGS-PGP Security Audit Framework."""
    
    def __init__(self, config: SecurityAuditConfig):
        self.config = config
        self.findings: List[SecurityFinding] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=50)
        timeout = aiohttp.ClientTimeout(total=self.config.test_timeout)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def test_csrf_protection(self, service: str, port: int) -> List[SecurityFinding]:
        """Test CSRF protection implementation."""
        findings = []
        
        try:
            # Test if service accepts requests without CSRF tokens
            test_payload = {"test": "csrf_validation"}
            async with self.session.post(
                f"http://localhost:{port}/api/v1/test",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 403:  # Should reject without CSRF token
                    findings.append(SecurityFinding(
                        category="CSRF Protection",
                        level=SecurityLevel.HIGH,
                        title="Missing CSRF Protection",
                        description=f"Service {service} accepts POST requests without CSRF validation",
                        service=service,
                        endpoint="/api/v1/test",
                        recommendation="Implement CSRF token validation for state-changing operations"
                    ))
        except Exception as e:
            # If endpoint doesn't exist, that's actually good for this test
            if "404" not in str(e):
                findings.append(SecurityFinding(
                    category="CSRF Protection",
                    level=SecurityLevel.MEDIUM,
                    title="CSRF Test Inconclusive",
                    description=f"Could not test CSRF protection on {service}: {str(e)}",
                    service=service,
                    recommendation="Verify CSRF protection implementation manually"
                ))
        
        return findings

    async def test_jwt_validation(self, service: str, port: int) -> List[SecurityFinding]:
        """Test JWT token validation security."""
        findings = []
        
        try:
            # Test with invalid JWT token
            invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
            headers = {"Authorization": f"Bearer {invalid_token}"}
            
            async with self.session.get(
                f"http://localhost:{port}/api/v1/protected",
                headers=headers
            ) as response:
                if response.status == 200:  # Should reject invalid token
                    findings.append(SecurityFinding(
                        category="JWT Validation",
                        level=SecurityLevel.CRITICAL,
                        title="Weak JWT Validation",
                        description=f"Service {service} accepts invalid JWT tokens",
                        service=service,
                        endpoint="/api/v1/protected",
                        recommendation="Implement proper JWT signature validation and expiration checks"
                    ))
                elif response.status == 401:
                    # Good - properly rejecting invalid tokens
                    pass
                    
            # Test with expired token (if we can generate one)
            try:
                expired_payload = {
                    "sub": "test_user",
                    "exp": int(time.time()) - 3600,  # Expired 1 hour ago
                    "iat": int(time.time()) - 7200   # Issued 2 hours ago
                }
                expired_token = jwt.encode(expired_payload, "test_secret", algorithm="HS256")
                headers = {"Authorization": f"Bearer {expired_token}"}
                
                async with self.session.get(
                    f"http://localhost:{port}/api/v1/protected",
                    headers=headers
                ) as response:
                    if response.status == 200:  # Should reject expired token
                        findings.append(SecurityFinding(
                            category="JWT Validation",
                            level=SecurityLevel.HIGH,
                            title="Expired Token Acceptance",
                            description=f"Service {service} accepts expired JWT tokens",
                            service=service,
                            endpoint="/api/v1/protected",
                            recommendation="Implement JWT expiration validation"
                        ))
            except Exception:
                # JWT library issues are not security findings
                pass
                
        except Exception as e:
            if "404" not in str(e):
                findings.append(SecurityFinding(
                    category="JWT Validation",
                    level=SecurityLevel.MEDIUM,
                    title="JWT Test Inconclusive",
                    description=f"Could not test JWT validation on {service}: {str(e)}",
                    service=service,
                    recommendation="Verify JWT validation implementation manually"
                ))
        
        return findings

    async def test_rbac_implementation(self, service: str, port: int) -> List[SecurityFinding]:
        """Test Role-Based Access Control implementation."""
        findings = []
        
        try:
            # Test admin-only endpoints without proper role
            admin_endpoints = [
                "/api/v1/admin/users",
                "/api/v1/admin/config",
                "/api/v1/admin/system"
            ]
            
            # Create a regular user token (mock)
            user_payload = {
                "sub": "regular_user",
                "role": "user",
                "exp": int(time.time()) + 3600
            }
            user_token = jwt.encode(user_payload, "test_secret", algorithm="HS256")
            headers = {"Authorization": f"Bearer {user_token}"}
            
            for endpoint in admin_endpoints:
                try:
                    async with self.session.get(
                        f"http://localhost:{port}{endpoint}",
                        headers=headers
                    ) as response:
                        if response.status == 200:  # Should reject non-admin access
                            findings.append(SecurityFinding(
                                category="RBAC",
                                level=SecurityLevel.HIGH,
                                title="Insufficient Access Control",
                                description=f"Service {service} allows non-admin access to {endpoint}",
                                service=service,
                                endpoint=endpoint,
                                recommendation="Implement proper role-based access control"
                            ))
                except Exception:
                    # Endpoint might not exist, which is fine
                    pass
                    
        except Exception as e:
            findings.append(SecurityFinding(
                category="RBAC",
                level=SecurityLevel.MEDIUM,
                title="RBAC Test Inconclusive",
                description=f"Could not test RBAC on {service}: {str(e)}",
                service=service,
                recommendation="Verify RBAC implementation manually"
            ))
        
        return findings

    async def test_authentication_workflow(self) -> List[SecurityFinding]:
        """Test authentication workflow security."""
        findings = []
        
        try:
            # Test auth service specifically
            auth_port = self.config.services.get('auth_service', 8000)
            
            # Test registration with weak passwords
            weak_passwords = ["123", "password", "admin", ""]
            for weak_password in weak_passwords:
                try:
                    register_payload = {
                        "username": f"test_user_{weak_password}",
                        "email": f"test_{weak_password}@example.com",
                        "password": weak_password
                    }
                    
                    async with self.session.post(
                        f"http://localhost:{auth_port}/api/v1/auth/register",
                        json=register_payload
                    ) as response:
                        if response.status == 200:  # Should reject weak passwords
                            findings.append(SecurityFinding(
                                category="Authentication",
                                level=SecurityLevel.MEDIUM,
                                title="Weak Password Policy",
                                description=f"Auth service accepts weak password: '{weak_password}'",
                                service="auth_service",
                                endpoint="/api/v1/auth/register",
                                recommendation="Implement strong password policy (min 8 chars, complexity requirements)"
                            ))
                except Exception:
                    # Registration might not be available, which is fine
                    pass
            
            # Test login brute force protection
            login_attempts = []
            for i in range(10):  # Try 10 failed logins
                try:
                    login_payload = {
                        "username": "nonexistent_user",
                        "password": f"wrong_password_{i}"
                    }
                    
                    start_time = time.time()
                    async with self.session.post(
                        f"http://localhost:{auth_port}/api/v1/auth/login",
                        json=login_payload
                    ) as response:
                        response_time = time.time() - start_time
                        login_attempts.append(response_time)
                except Exception:
                    pass
            
            # Check if there's rate limiting (response times should increase)
            if len(login_attempts) >= 5:
                avg_early = sum(login_attempts[:3]) / 3
                avg_late = sum(login_attempts[-3:]) / 3
                if avg_late <= avg_early * 1.5:  # No significant slowdown
                    findings.append(SecurityFinding(
                        category="Authentication",
                        level=SecurityLevel.MEDIUM,
                        title="Missing Brute Force Protection",
                        description="Auth service lacks rate limiting for failed login attempts",
                        service="auth_service",
                        endpoint="/api/v1/auth/login",
                        recommendation="Implement progressive delays or account lockout for failed login attempts"
                    ))
                    
        except Exception as e:
            findings.append(SecurityFinding(
                category="Authentication",
                level=SecurityLevel.MEDIUM,
                title="Authentication Test Inconclusive",
                description=f"Could not test authentication workflow: {str(e)}",
                service="auth_service",
                recommendation="Verify authentication security manually"
            ))
        
        return findings

    async def test_cryptographic_integrity(self) -> List[SecurityFinding]:
        """Test cryptographic integrity components."""
        findings = []
        
        try:
            # Test integrity service
            integrity_port = self.config.services.get('integrity_service', 8002)
            
            # Test hash verification
            test_data = "test_data_for_integrity_check"
            test_hash = hashlib.sha256(test_data.encode()).hexdigest()
            
            verify_payload = {
                "data": test_data,
                "expected_hash": test_hash,
                "algorithm": "sha256"
            }
            
            async with self.session.post(
                f"http://localhost:{integrity_port}/api/v1/verify",
                json=verify_payload
            ) as response:
                if response.status != 200:
                    findings.append(SecurityFinding(
                        category="Cryptographic Integrity",
                        level=SecurityLevel.MEDIUM,
                        title="Hash Verification Issues",
                        description="Integrity service hash verification not working properly",
                        service="integrity_service",
                        endpoint="/api/v1/verify",
                        recommendation="Verify cryptographic hash implementation"
                    ))
                    
            # Test with tampered data
            tampered_payload = {
                "data": "tampered_data",
                "expected_hash": test_hash,
                "algorithm": "sha256"
            }
            
            async with self.session.post(
                f"http://localhost:{integrity_port}/api/v1/verify",
                json=tampered_payload
            ) as response:
                if response.status == 200:  # Should detect tampering
                    response_data = await response.json()
                    if response_data.get("verified", True):  # Should be False
                        findings.append(SecurityFinding(
                            category="Cryptographic Integrity",
                            level=SecurityLevel.HIGH,
                            title="Tampering Detection Failure",
                            description="Integrity service fails to detect data tampering",
                            service="integrity_service",
                            endpoint="/api/v1/verify",
                            recommendation="Fix hash verification logic to properly detect tampering"
                        ))
                        
        except Exception as e:
            findings.append(SecurityFinding(
                category="Cryptographic Integrity",
                level=SecurityLevel.MEDIUM,
                title="Cryptographic Test Inconclusive",
                description=f"Could not test cryptographic integrity: {str(e)}",
                service="integrity_service",
                recommendation="Verify cryptographic implementation manually"
            ))
        
        return findings

    async def test_cross_service_security(self) -> List[SecurityFinding]:
        """Test cross-service API communication security."""
        findings = []
        
        try:
            # Test if services validate requests from other services
            # This is a simplified test - in production, services should use mutual TLS or API keys
            
            # Test GS service calling AC service
            gs_port = self.config.services.get('gs_service', 8004)
            
            # Try to access internal endpoints that should be service-to-service only
            internal_endpoints = [
                "/api/v1/internal/principles",
                "/api/v1/internal/config",
                "/api/v1/internal/metrics"
            ]
            
            for endpoint in internal_endpoints:
                try:
                    async with self.session.get(f"http://localhost:{gs_port}{endpoint}") as response:
                        if response.status == 200:  # Should require service authentication
                            findings.append(SecurityFinding(
                                category="Cross-Service Security",
                                level=SecurityLevel.MEDIUM,
                                title="Unprotected Internal Endpoint",
                                description=f"Internal endpoint {endpoint} accessible without service authentication",
                                service="gs_service",
                                endpoint=endpoint,
                                recommendation="Implement service-to-service authentication (mutual TLS, API keys)"
                            ))
                except Exception:
                    # Endpoint might not exist, which is fine
                    pass
                    
        except Exception as e:
            findings.append(SecurityFinding(
                category="Cross-Service Security",
                level=SecurityLevel.MEDIUM,
                title="Cross-Service Security Test Inconclusive",
                description=f"Could not test cross-service security: {str(e)}",
                service="multiple",
                recommendation="Verify service-to-service authentication manually"
            ))
        
        return findings

    def calculate_security_score(self) -> float:
        """Calculate overall security score based on findings."""
        if not self.findings:
            return 100.0
        
        # Weight findings by severity
        severity_weights = {
            SecurityLevel.CRITICAL: 25,
            SecurityLevel.HIGH: 15,
            SecurityLevel.MEDIUM: 8,
            SecurityLevel.LOW: 3,
            SecurityLevel.INFO: 1
        }
        
        total_deductions = sum(severity_weights.get(finding.level, 0) for finding in self.findings)
        
        # Start with 100 and deduct points
        score = max(0, 100 - total_deductions)
        return score

    async def run_security_audit(self) -> SecurityAuditReport:
        """Execute comprehensive security audit."""
        logger.info("🔒 Starting ACGS-PGP Security Audit")
        start_time = datetime.now(timezone.utc)
        
        # Test each service
        for service, port in self.config.services.items():
            logger.info(f"🔍 Auditing {service} on port {port}")
            
            # CSRF protection tests
            csrf_findings = await self.test_csrf_protection(service, port)
            self.findings.extend(csrf_findings)
            
            # JWT validation tests
            jwt_findings = await self.test_jwt_validation(service, port)
            self.findings.extend(jwt_findings)
            
            # RBAC tests
            rbac_findings = await self.test_rbac_implementation(service, port)
            self.findings.extend(rbac_findings)
        
        # Authentication workflow tests
        logger.info("🔐 Testing authentication workflow")
        auth_findings = await self.test_authentication_workflow()
        self.findings.extend(auth_findings)
        
        # Cryptographic integrity tests
        logger.info("🔐 Testing cryptographic integrity")
        crypto_findings = await self.test_cryptographic_integrity()
        self.findings.extend(crypto_findings)
        
        # Cross-service security tests
        logger.info("🔗 Testing cross-service security")
        cross_service_findings = await self.test_cross_service_security()
        self.findings.extend(cross_service_findings)
        
        end_time = datetime.now(timezone.utc)
        
        # Calculate security score
        security_score = self.calculate_security_score()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        return SecurityAuditReport(
            config=self.config,
            start_time=start_time,
            end_time=end_time,
            findings=self.findings,
            security_score=security_score,
            services_tested=len(self.config.services),
            vulnerabilities_found=len([f for f in self.findings if f.level in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]]),
            recommendations=recommendations
        )

    def _generate_recommendations(self) -> List[str]:
        """Generate security hardening recommendations."""
        recommendations = []
        
        # Group findings by category
        categories = {}
        for finding in self.findings:
            if finding.category not in categories:
                categories[finding.category] = []
            categories[finding.category].append(finding)
        
        # Generate category-specific recommendations
        if "CSRF Protection" in categories:
            recommendations.append("Implement CSRF token validation for all state-changing operations")
        
        if "JWT Validation" in categories:
            recommendations.append("Strengthen JWT validation with proper signature verification and expiration checks")
        
        if "RBAC" in categories:
            recommendations.append("Implement comprehensive role-based access control across all services")
        
        if "Authentication" in categories:
            recommendations.append("Enhance authentication security with strong password policies and brute force protection")
        
        if "Cryptographic Integrity" in categories:
            recommendations.append("Verify and strengthen cryptographic implementations")
        
        if "Cross-Service Security" in categories:
            recommendations.append("Implement service-to-service authentication (mutual TLS or API keys)")
        
        # General recommendations
        recommendations.extend([
            "Implement comprehensive logging and monitoring for security events",
            "Regular security audits and penetration testing",
            "Keep all dependencies updated to latest secure versions",
            "Implement rate limiting and DDoS protection",
            "Use HTTPS/TLS for all communications"
        ])
        
        return recommendations

def print_security_audit_report(report: SecurityAuditReport):
    """Print comprehensive security audit report."""
    print("\n" + "="*80)
    print("🔒 ACGS-PGP PHASE 2 SECURITY AUDIT REPORT")
    print("="*80)
    
    # Audit summary
    print(f"📋 Audit Summary:")
    print(f"   Services Tested: {report.services_tested}")
    print(f"   Audit Duration: {(report.end_time - report.start_time).total_seconds():.1f}s")
    print(f"   Security Score: {report.security_score:.1f}/100")
    print(f"   Target Score: ≥{report.config.target_security_score}")
    
    # Security score assessment
    if report.security_score >= report.config.target_security_score:
        score_status = "✅ PASSED"
    else:
        score_status = "⚠️ NEEDS IMPROVEMENT"
    print(f"   Overall Status: {score_status}")
    
    # Findings summary
    print(f"\n🔍 Security Findings:")
    print(f"   Total Findings: {len(report.findings)}")
    print(f"   Critical Vulnerabilities: {len([f for f in report.findings if f.level == SecurityLevel.CRITICAL])}")
    print(f"   High Risk Issues: {len([f for f in report.findings if f.level == SecurityLevel.HIGH])}")
    print(f"   Medium Risk Issues: {len([f for f in report.findings if f.level == SecurityLevel.MEDIUM])}")
    print(f"   Low Risk Issues: {len([f for f in report.findings if f.level == SecurityLevel.LOW])}")
    
    # Detailed findings
    if report.findings:
        print(f"\n📝 Detailed Findings:")
        for finding in sorted(report.findings, key=lambda x: x.level.value):
            level_icon = {
                SecurityLevel.CRITICAL: "🚨",
                SecurityLevel.HIGH: "⚠️",
                SecurityLevel.MEDIUM: "⚡",
                SecurityLevel.LOW: "ℹ️",
                SecurityLevel.INFO: "📋"
            }.get(finding.level, "❓")
            
            print(f"   {level_icon} [{finding.level.value.upper()}] {finding.title}")
            print(f"      Service: {finding.service}")
            if finding.endpoint:
                print(f"      Endpoint: {finding.endpoint}")
            print(f"      Description: {finding.description}")
            if finding.recommendation:
                print(f"      Recommendation: {finding.recommendation}")
            print()
    
    # Recommendations
    print(f"🛡️ Security Hardening Recommendations:")
    for i, recommendation in enumerate(report.recommendations, 1):
        print(f"   {i}. {recommendation}")

async def main():
    """Main security audit execution."""
    parser = argparse.ArgumentParser(description="ACGS-PGP Security Audit Framework")
    parser.add_argument("--target-score", type=float, default=85.0, help="Target security score")
    parser.add_argument("--timeout", type=int, default=30, help="Test timeout in seconds")
    
    args = parser.parse_args()
    
    config = SecurityAuditConfig(
        target_security_score=args.target_score,
        test_timeout=args.timeout
    )
    
    async with SecurityAuditor(config) as auditor:
        report = await auditor.run_security_audit()
        print_security_audit_report(report)

if __name__ == "__main__":
    asyncio.run(main())
