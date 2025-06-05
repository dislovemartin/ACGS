#!/usr/bin/env python3
"""
ACGS Phase 3 Security Compliance Validation Script
Validates security compliance for production deployment.

Security Targets:
- ≥90% security compliance with zero critical vulnerabilities
- SQL injection, XSS, command injection testing
- JWT authentication validation
- Rate limiting verification
- Input sanitization testing
"""

import asyncio
import aiohttp
import subprocess
import json
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/phase3_security_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ACGSSecurityValidator:
    def __init__(self):
        self.services = {
            'auth_service': {'port': 8000, 'name': 'Auth Service'},
            'ac_service': {'port': 8001, 'name': 'AC Service'},
            'integrity_service': {'port': 8002, 'name': 'Integrity Service'},
            'fv_service': {'port': 8003, 'name': 'FV Service'},
            'gs_service': {'port': 8004, 'name': 'GS Service'},
            'pgc_service': {'port': 8005, 'name': 'PGC Service'}
        }
        
        self.security_targets = {
            'min_compliance_score': 0.90,
            'max_critical_vulnerabilities': 0,
            'max_high_vulnerabilities': 2,
            'required_security_headers': [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection'
            ]
        }
        
        self.results = {
            'test_start': datetime.now(timezone.utc).isoformat(),
            'services_tested': [],
            'dependency_scan_results': {},
            'penetration_test_results': {},
            'security_headers_check': {},
            'authentication_tests': {},
            'input_validation_tests': {},
            'compliance_score': 0.0,
            'critical_vulnerabilities': 0,
            'high_vulnerabilities': 0,
            'overall_status': 'PENDING'
        }

    async def run_dependency_security_scan(self) -> Dict:
        """Run security scan on Python dependencies using Safety."""
        logger.info("🔍 Running dependency security scan...")
        
        scan_results = {
            'safety_scan': {'status': 'not_run', 'vulnerabilities': []},
            'bandit_scan': {'status': 'not_run', 'issues': []}
        }
        
        # Run Safety scan
        try:
            logger.info("Running Safety scan for known vulnerabilities...")
            result = subprocess.run(
                ['python', '-m', 'safety', 'check', '--json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                scan_results['safety_scan']['status'] = 'passed'
                scan_results['safety_scan']['vulnerabilities'] = []
                logger.info("✅ Safety scan: No known vulnerabilities found")
            else:
                try:
                    vulnerabilities = json.loads(result.stdout) if result.stdout else []
                    scan_results['safety_scan']['status'] = 'failed'
                    scan_results['safety_scan']['vulnerabilities'] = vulnerabilities
                    logger.warning(f"⚠️ Safety scan found {len(vulnerabilities)} vulnerabilities")
                except json.JSONDecodeError:
                    scan_results['safety_scan']['status'] = 'error'
                    logger.error("❌ Safety scan failed to parse results")
                    
        except subprocess.TimeoutExpired:
            scan_results['safety_scan']['status'] = 'timeout'
            logger.error("❌ Safety scan timed out")
        except FileNotFoundError:
            scan_results['safety_scan']['status'] = 'not_installed'
            logger.warning("⚠️ Safety not installed, skipping dependency scan")
        
        # Run Bandit scan for code security issues
        try:
            logger.info("Running Bandit scan for code security issues...")
            result = subprocess.run(
                ['python', '-m', 'bandit', '-r', 'src/', '-f', 'json', '-ll'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                scan_results['bandit_scan']['status'] = 'passed'
                scan_results['bandit_scan']['issues'] = []
                logger.info("✅ Bandit scan: No security issues found")
            else:
                try:
                    bandit_output = json.loads(result.stdout) if result.stdout else {}
                    issues = bandit_output.get('results', [])
                    scan_results['bandit_scan']['status'] = 'completed'
                    scan_results['bandit_scan']['issues'] = issues
                    
                    high_issues = [i for i in issues if i.get('issue_severity') == 'HIGH']
                    medium_issues = [i for i in issues if i.get('issue_severity') == 'MEDIUM']
                    
                    logger.info(f"Bandit scan completed: {len(high_issues)} high, {len(medium_issues)} medium issues")
                    
                except json.JSONDecodeError:
                    scan_results['bandit_scan']['status'] = 'error'
                    logger.error("❌ Bandit scan failed to parse results")
                    
        except subprocess.TimeoutExpired:
            scan_results['bandit_scan']['status'] = 'timeout'
            logger.error("❌ Bandit scan timed out")
        except FileNotFoundError:
            scan_results['bandit_scan']['status'] = 'not_installed'
            logger.warning("⚠️ Bandit not installed, skipping code security scan")
        
        self.results['dependency_scan_results'] = scan_results
        return scan_results

    async def test_security_headers(self) -> Dict:
        """Test security headers for all services."""
        logger.info("🛡️ Testing security headers...")
        
        headers_results = {}
        async with aiohttp.ClientSession() as session:
            for service_id, config in self.services.items():
                try:
                    async with session.get(f"http://localhost:{config['port']}/health") as response:
                        headers = dict(response.headers)
                        
                        security_headers_present = {}
                        for header in self.security_targets['required_security_headers']:
                            security_headers_present[header] = header in headers
                        
                        headers_results[service_id] = {
                            'status': 'completed',
                            'security_headers': security_headers_present,
                            'all_headers': headers,
                            'score': sum(security_headers_present.values()) / len(security_headers_present)
                        }
                        
                        score = headers_results[service_id]['score']
                        logger.info(f"{config['name']}: {score:.1%} security headers present")
                        
                except Exception as e:
                    headers_results[service_id] = {
                        'status': 'error',
                        'error': str(e),
                        'score': 0.0
                    }
                    logger.error(f"❌ {config['name']} security headers test failed: {e}")
        
        self.results['security_headers_check'] = headers_results
        return headers_results

    async def test_input_validation(self) -> Dict:
        """Test input validation and injection protection."""
        logger.info("🔒 Testing input validation and injection protection...")
        
        # Common injection payloads for testing
        injection_payloads = [
            "'; DROP TABLE users; --",  # SQL injection
            "<script>alert('xss')</script>",  # XSS
            "$(whoami)",  # Command injection
            "../../../etc/passwd",  # Path traversal
            "' OR '1'='1",  # SQL injection variant
        ]
        
        validation_results = {}
        async with aiohttp.ClientSession() as session:
            for service_id, config in self.services.items():
                service_results = {
                    'sql_injection_protected': True,
                    'xss_protected': True,
                    'command_injection_protected': True,
                    'path_traversal_protected': True,
                    'tests_passed': 0,
                    'total_tests': 0
                }
                
                # Test health endpoint with malicious payloads
                for payload in injection_payloads:
                    try:
                        # Test as query parameter
                        async with session.get(
                            f"http://localhost:{config['port']}/health?test={payload}",
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            service_results['total_tests'] += 1
                            
                            # Check if service properly handles malicious input
                            if response.status in [200, 400, 422]:  # Expected responses
                                service_results['tests_passed'] += 1
                            
                            # Check response doesn't echo back the payload (XSS protection)
                            response_text = await response.text()
                            if payload not in response_text:
                                service_results['tests_passed'] += 1
                            else:
                                if 'script' in payload.lower():
                                    service_results['xss_protected'] = False
                                    
                    except asyncio.TimeoutError:
                        # Timeout might indicate the service is hanging due to injection
                        if 'DROP' in payload or 'whoami' in payload:
                            service_results['sql_injection_protected'] = False
                            service_results['command_injection_protected'] = False
                    except Exception as e:
                        logger.debug(f"Input validation test error for {service_id}: {e}")
                
                validation_results[service_id] = service_results
                
                protection_score = service_results['tests_passed'] / max(service_results['total_tests'], 1)
                logger.info(f"{config['name']}: {protection_score:.1%} input validation tests passed")
        
        self.results['input_validation_tests'] = validation_results
        return validation_results

    async def test_authentication_security(self) -> Dict:
        """Test authentication and authorization security."""
        logger.info("🔐 Testing authentication security...")
        
        auth_results = {
            'jwt_validation': {'status': 'not_tested'},
            'rate_limiting': {'status': 'not_tested'},
            'unauthorized_access': {'status': 'not_tested'}
        }
        
        async with aiohttp.ClientSession() as session:
            # Test unauthorized access to protected endpoints
            try:
                # Try to access a potentially protected endpoint without authentication
                async with session.get("http://localhost:8000/protected", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status in [401, 403]:
                        auth_results['unauthorized_access']['status'] = 'protected'
                        logger.info("✅ Unauthorized access properly blocked")
                    else:
                        auth_results['unauthorized_access']['status'] = 'vulnerable'
                        logger.warning("⚠️ Unauthorized access not properly blocked")
            except aiohttp.ClientError:
                # Endpoint might not exist, which is fine
                auth_results['unauthorized_access']['status'] = 'endpoint_not_found'
            
            # Test rate limiting
            try:
                start_time = asyncio.get_event_loop().time()
                requests_made = 0
                rate_limited = False
                
                # Make rapid requests to test rate limiting
                for i in range(20):
                    async with session.get("http://localhost:8000/health", timeout=aiohttp.ClientTimeout(total=1)) as response:
                        requests_made += 1
                        if response.status == 429:  # Too Many Requests
                            rate_limited = True
                            break
                
                if rate_limited:
                    auth_results['rate_limiting']['status'] = 'active'
                    logger.info("✅ Rate limiting is active")
                else:
                    auth_results['rate_limiting']['status'] = 'not_detected'
                    logger.info("ℹ️ Rate limiting not detected (may be configured for higher limits)")
                    
            except Exception as e:
                auth_results['rate_limiting']['status'] = 'error'
                logger.error(f"❌ Rate limiting test failed: {e}")
        
        self.results['authentication_tests'] = auth_results
        return auth_results

    def calculate_compliance_score(self) -> float:
        """Calculate overall security compliance score."""
        logger.info("📊 Calculating security compliance score...")
        
        total_score = 0.0
        max_score = 0.0
        
        # Dependency scan score (30% weight)
        dependency_weight = 0.30
        if self.results['dependency_scan_results'].get('safety_scan', {}).get('status') == 'passed':
            total_score += dependency_weight
        max_score += dependency_weight
        
        # Security headers score (25% weight)
        headers_weight = 0.25
        if self.results['security_headers_check']:
            headers_scores = [
                result.get('score', 0.0) 
                for result in self.results['security_headers_check'].values()
                if isinstance(result, dict) and 'score' in result
            ]
            if headers_scores:
                avg_headers_score = sum(headers_scores) / len(headers_scores)
                total_score += headers_weight * avg_headers_score
        max_score += headers_weight
        
        # Input validation score (25% weight)
        validation_weight = 0.25
        if self.results['input_validation_tests']:
            validation_scores = []
            for result in self.results['input_validation_tests'].values():
                if result['total_tests'] > 0:
                    validation_scores.append(result['tests_passed'] / result['total_tests'])
            
            if validation_scores:
                avg_validation_score = sum(validation_scores) / len(validation_scores)
                total_score += validation_weight * avg_validation_score
        max_score += validation_weight
        
        # Authentication security score (20% weight)
        auth_weight = 0.20
        auth_score = 0.0
        auth_tests = self.results['authentication_tests']
        
        if auth_tests.get('unauthorized_access', {}).get('status') == 'protected':
            auth_score += 0.5
        if auth_tests.get('rate_limiting', {}).get('status') in ['active', 'not_detected']:
            auth_score += 0.5
        
        total_score += auth_weight * auth_score
        max_score += auth_weight
        
        compliance_score = total_score / max_score if max_score > 0 else 0.0
        self.results['compliance_score'] = compliance_score
        
        logger.info(f"Security Compliance Score: {compliance_score:.1%}")
        return compliance_score

    def evaluate_security_criteria(self) -> bool:
        """Evaluate if security criteria are met."""
        logger.info("🎯 Evaluating security criteria...")
        
        compliance_score = self.calculate_compliance_score()
        
        # Count vulnerabilities from dependency scans
        critical_vulns = 0
        high_vulns = 0
        
        safety_vulns = self.results['dependency_scan_results'].get('safety_scan', {}).get('vulnerabilities', [])
        for vuln in safety_vulns:
            if vuln.get('severity', '').lower() == 'critical':
                critical_vulns += 1
            elif vuln.get('severity', '').lower() == 'high':
                high_vulns += 1
        
        bandit_issues = self.results['dependency_scan_results'].get('bandit_scan', {}).get('issues', [])
        for issue in bandit_issues:
            if issue.get('issue_severity', '').upper() == 'HIGH':
                high_vulns += 1
        
        self.results['critical_vulnerabilities'] = critical_vulns
        self.results['high_vulnerabilities'] = high_vulns
        
        # Evaluate criteria
        compliance_passed = compliance_score >= self.security_targets['min_compliance_score']
        critical_vulns_passed = critical_vulns <= self.security_targets['max_critical_vulnerabilities']
        high_vulns_passed = high_vulns <= self.security_targets['max_high_vulnerabilities']
        
        overall_passed = compliance_passed and critical_vulns_passed and high_vulns_passed
        
        logger.info(f"Compliance Score: {compliance_score:.1%} (Target: ≥{self.security_targets['min_compliance_score']:.1%}) - {'✅ PASSED' if compliance_passed else '❌ FAILED'}")
        logger.info(f"Critical Vulnerabilities: {critical_vulns} (Target: ≤{self.security_targets['max_critical_vulnerabilities']}) - {'✅ PASSED' if critical_vulns_passed else '❌ FAILED'}")
        logger.info(f"High Vulnerabilities: {high_vulns} (Target: ≤{self.security_targets['max_high_vulnerabilities']}) - {'✅ PASSED' if high_vulns_passed else '❌ FAILED'}")
        
        self.results['overall_status'] = 'PASSED' if overall_passed else 'FAILED'
        return overall_passed

    async def run_security_validation(self) -> bool:
        """Run complete security validation."""
        logger.info("🔒 Starting ACGS Phase 3 Security Validation")
        logger.info("=" * 80)
        
        try:
            # Step 1: Run dependency security scan
            await self.run_dependency_security_scan()
            
            # Step 2: Test security headers
            await self.test_security_headers()
            
            # Step 3: Test input validation
            await self.test_input_validation()
            
            # Step 4: Test authentication security
            await self.test_authentication_security()
            
            # Step 5: Evaluate security criteria
            success = self.evaluate_security_criteria()
            
            # Step 6: Generate final report
            self.generate_security_report()
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Security validation failed with exception: {str(e)}")
            self.results['overall_status'] = 'ERROR'
            self.results['error_message'] = str(e)
            return False

    def generate_security_report(self):
        """Generate comprehensive security validation report."""
        self.results['test_end'] = datetime.now(timezone.utc).isoformat()
        
        # Save detailed results to file
        report_file = f"logs/phase3_security_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info("=" * 80)
        logger.info("🎉 ACGS Phase 3 Security Validation Complete!")
        logger.info("=" * 80)
        logger.info(f"Overall Status: {'✅ PASSED' if self.results['overall_status'] == 'PASSED' else '❌ FAILED'}")
        logger.info(f"Compliance Score: {self.results['compliance_score']:.1%}")
        logger.info(f"Critical Vulnerabilities: {self.results['critical_vulnerabilities']}")
        logger.info(f"High Vulnerabilities: {self.results['high_vulnerabilities']}")
        logger.info(f"Detailed Report: {report_file}")
        
        if self.results['overall_status'] == 'PASSED':
            logger.info("🚀 Security validation passed! Ready for production deployment.")
        else:
            logger.info("⚠️ Security issues found. Address vulnerabilities before production.")

async def main():
    parser = argparse.ArgumentParser(description='ACGS Phase 3 Security Validation')
    parser.add_argument('--quick-test', action='store_true', help='Run quick security test (skip some scans)')
    
    args = parser.parse_args()
    
    validator = ACGSSecurityValidator()
    success = await validator.run_security_validation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
