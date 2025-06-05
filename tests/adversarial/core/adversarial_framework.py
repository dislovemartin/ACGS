"""
Comprehensive Adversarial Testing Framework for ACGS-PGP

This module implements the main adversarial testing framework that coordinates
all adversarial testing components and provides comprehensive vulnerability assessment.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
import aiohttp
import numpy as np

logger = logging.getLogger(__name__)


class AttackCategory(Enum):
    """Categories of adversarial attacks."""
    CONSTITUTIONAL_MANIPULATION = "constitutional_manipulation"
    POLICY_SYNTHESIS_POISONING = "policy_synthesis_poisoning"
    Z3_SOLVER_BYPASS = "z3_solver_bypass"
    LLM_PROMPT_INJECTION = "llm_prompt_injection"
    CROSS_SERVICE_VULNERABILITY = "cross_service_vulnerability"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    CRYPTOGRAPHIC_ATTACK = "cryptographic_attack"
    STRESS_OVERLOAD = "stress_overload"


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AdversarialTestConfig:
    """Configuration for adversarial testing framework."""
    target_services: List[str] = None
    attack_categories: List[AttackCategory] = None
    max_test_cases: int = 1000
    timeout_seconds: int = 600
    parallel_execution: bool = True
    max_concurrent_tests: int = 10
    vulnerability_threshold: float = 0.95
    stress_multiplier: float = 100.0
    enable_monitoring: bool = True
    generate_reports: bool = True
    
    def __post_init__(self):
        if self.target_services is None:
            self.target_services = [
                "auth_service", "ac_service", "gs_service", 
                "fv_service", "integrity_service", "pgc_service"
            ]
        if self.attack_categories is None:
            self.attack_categories = list(AttackCategory)


@dataclass
class VulnerabilityResult:
    """Result of a vulnerability test."""
    test_id: str
    attack_category: AttackCategory
    severity: VulnerabilitySeverity
    service_target: str
    vulnerability_description: str
    attack_vector: str
    impact_assessment: str
    proof_of_concept: str
    mitigation_recommendations: List[str]
    cvss_score: float
    execution_time_ms: float
    timestamp: datetime
    additional_metadata: Dict[str, Any] = None


@dataclass
class AdversarialTestReport:
    """Comprehensive adversarial testing report."""
    test_session_id: str
    start_time: datetime
    end_time: datetime
    total_tests_executed: int
    vulnerabilities_found: int
    vulnerability_distribution: Dict[VulnerabilitySeverity, int]
    attack_success_rate: Dict[AttackCategory, float]
    overall_security_score: float
    critical_vulnerabilities: List[VulnerabilityResult]
    recommendations: List[str]
    test_coverage: Dict[str, float]
    performance_impact: Dict[str, float]


class AdversarialTestingFramework:
    """
    Main adversarial testing framework that coordinates all testing components.
    
    This framework implements comprehensive adversarial testing targeting:
    - 95% vulnerability detection rate
    - 1000+ test case resilience
    - 80% attack surface reduction recommendations
    """
    
    def __init__(self, config: AdversarialTestConfig = None):
        self.config = config or AdversarialTestConfig()
        self.session_id = f"adversarial_test_{int(time.time())}"
        self.vulnerabilities: List[VulnerabilityResult] = []
        self.test_results: Dict[str, Any] = {}
        
        # Service endpoints
        self.service_endpoints = {
            "auth_service": "http://localhost:8000",
            "ac_service": "http://localhost:8001", 
            "integrity_service": "http://localhost:8002",
            "fv_service": "http://localhost:8003",
            "gs_service": "http://localhost:8004",
            "pgc_service": "http://localhost:8005"
        }
        
        # Initialize testing components (will be imported dynamically)
        self.testers = {}
        
    async def initialize_testers(self):
        """Initialize all adversarial testing components."""
        try:
            from .constitutional_attacks import ConstitutionalAttackTester
            from .policy_poisoning import PolicyPoisoningDetector
            from .z3_bypass import Z3BypassTester
            from .llm_security import LLMSecurityTester
            from .cross_service_vulnerabilities import CrossServiceVulnerabilityScanner
            from .stress_testing import StressTestingProtocol
            
            self.testers = {
                AttackCategory.CONSTITUTIONAL_MANIPULATION: ConstitutionalAttackTester(self.config),
                AttackCategory.POLICY_SYNTHESIS_POISONING: PolicyPoisoningDetector(self.config),
                AttackCategory.Z3_SOLVER_BYPASS: Z3BypassTester(self.config),
                AttackCategory.LLM_PROMPT_INJECTION: LLMSecurityTester(self.config),
                AttackCategory.CROSS_SERVICE_VULNERABILITY: CrossServiceVulnerabilityScanner(self.config),
                AttackCategory.STRESS_OVERLOAD: StressTestingProtocol(self.config)
            }
            
            logger.info(f"Initialized {len(self.testers)} adversarial testing components")
            
        except ImportError as e:
            logger.warning(f"Some testing components not available: {e}")
    
    async def run_comprehensive_assessment(self) -> AdversarialTestReport:
        """
        Run comprehensive adversarial testing assessment.
        
        Returns:
            AdversarialTestReport: Comprehensive test results and recommendations
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting comprehensive adversarial assessment - Session: {self.session_id}")
        
        # Initialize testing components
        await self.initialize_testers()
        
        # Check service availability
        available_services = await self._check_service_availability()
        logger.info(f"Available services: {available_services}")
        
        # Run adversarial tests by category
        total_tests = 0
        for category in self.config.attack_categories:
            if category in self.testers:
                logger.info(f"Running {category.value} tests...")
                category_results = await self._run_category_tests(category, available_services)
                self.vulnerabilities.extend(category_results)
                total_tests += len(category_results)
        
        # Generate comprehensive report
        end_time = datetime.now(timezone.utc)
        report = self._generate_comprehensive_report(start_time, end_time, total_tests)
        
        logger.info(f"Adversarial assessment completed - Found {len(self.vulnerabilities)} vulnerabilities")
        return report
    
    async def _check_service_availability(self) -> List[str]:
        """Check which services are available for testing."""
        available_services = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for service_name, endpoint in self.service_endpoints.items():
                try:
                    async with session.get(f"{endpoint}/health") as response:
                        if response.status == 200:
                            available_services.append(service_name)
                            logger.debug(f"Service {service_name} is available")
                except Exception as e:
                    logger.warning(f"Service {service_name} not available: {e}")
        
        return available_services
    
    async def _run_category_tests(
        self, 
        category: AttackCategory, 
        available_services: List[str]
    ) -> List[VulnerabilityResult]:
        """Run tests for a specific attack category."""
        if category not in self.testers:
            logger.warning(f"No tester available for category: {category}")
            return []
        
        tester = self.testers[category]
        
        try:
            # Run category-specific tests
            results = await tester.run_tests(available_services, self.service_endpoints)
            logger.info(f"Category {category.value}: {len(results)} tests completed")
            return results
            
        except Exception as e:
            logger.error(f"Error running {category.value} tests: {e}")
            return []
    
    def _generate_comprehensive_report(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        total_tests: int
    ) -> AdversarialTestReport:
        """Generate comprehensive adversarial testing report."""
        
        # Calculate vulnerability distribution
        vulnerability_distribution = {severity: 0 for severity in VulnerabilitySeverity}
        for vuln in self.vulnerabilities:
            vulnerability_distribution[vuln.severity] += 1
        
        # Calculate attack success rates
        attack_success_rate = {}
        for category in AttackCategory:
            category_vulns = [v for v in self.vulnerabilities if v.attack_category == category]
            category_tests = max(1, len([v for v in self.vulnerabilities if v.attack_category == category]))
            attack_success_rate[category] = len(category_vulns) / category_tests
        
        # Calculate overall security score
        security_score = self._calculate_security_score()
        
        # Get critical vulnerabilities
        critical_vulnerabilities = [
            v for v in self.vulnerabilities 
            if v.severity == VulnerabilitySeverity.CRITICAL
        ]
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations()
        
        # Calculate test coverage
        test_coverage = self._calculate_test_coverage()
        
        # Calculate performance impact
        performance_impact = self._calculate_performance_impact()
        
        return AdversarialTestReport(
            test_session_id=self.session_id,
            start_time=start_time,
            end_time=end_time,
            total_tests_executed=total_tests,
            vulnerabilities_found=len(self.vulnerabilities),
            vulnerability_distribution=vulnerability_distribution,
            attack_success_rate=attack_success_rate,
            overall_security_score=security_score,
            critical_vulnerabilities=critical_vulnerabilities,
            recommendations=recommendations,
            test_coverage=test_coverage,
            performance_impact=performance_impact
        )
    
    def _calculate_security_score(self) -> float:
        """Calculate overall security score (0.0 to 1.0)."""
        if not self.vulnerabilities:
            return 1.0
        
        # Weight vulnerabilities by severity
        severity_weights = {
            VulnerabilitySeverity.CRITICAL: 1.0,
            VulnerabilitySeverity.HIGH: 0.7,
            VulnerabilitySeverity.MEDIUM: 0.4,
            VulnerabilitySeverity.LOW: 0.2,
            VulnerabilitySeverity.INFO: 0.1
        }
        
        total_weight = sum(severity_weights[v.severity] for v in self.vulnerabilities)
        max_possible_weight = len(self.vulnerabilities) * severity_weights[VulnerabilitySeverity.CRITICAL]
        
        return max(0.0, 1.0 - (total_weight / max_possible_weight))
    
    def _generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []
        
        # Critical vulnerability recommendations
        critical_count = len([v for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL])
        if critical_count > 0:
            recommendations.append(f"URGENT: Address {critical_count} critical vulnerabilities immediately")
        
        # Category-specific recommendations
        category_counts = {}
        for vuln in self.vulnerabilities:
            category_counts[vuln.attack_category] = category_counts.get(vuln.attack_category, 0) + 1
        
        if category_counts.get(AttackCategory.CONSTITUTIONAL_MANIPULATION, 0) > 0:
            recommendations.append("Strengthen constitutional principle validation and access controls")
        
        if category_counts.get(AttackCategory.LLM_PROMPT_INJECTION, 0) > 0:
            recommendations.append("Implement advanced prompt injection detection and sanitization")
        
        if category_counts.get(AttackCategory.CROSS_SERVICE_VULNERABILITY, 0) > 0:
            recommendations.append("Review and harden cross-service communication protocols")
        
        # General recommendations
        if len(self.vulnerabilities) > 50:
            recommendations.append("Conduct comprehensive security architecture review")
        
        if not recommendations:
            recommendations.append("Security posture is strong - maintain current practices")
        
        return recommendations
    
    def _calculate_test_coverage(self) -> Dict[str, float]:
        """Calculate test coverage by service and category."""
        coverage = {}
        
        # Service coverage
        for service in self.config.target_services:
            service_tests = len([v for v in self.vulnerabilities if v.service_target == service])
            coverage[f"service_{service}"] = min(1.0, service_tests / 100)  # Normalize to 100 tests per service
        
        # Category coverage
        for category in AttackCategory:
            category_tests = len([v for v in self.vulnerabilities if v.attack_category == category])
            coverage[f"category_{category.value}"] = min(1.0, category_tests / 50)  # Normalize to 50 tests per category
        
        return coverage
    
    def _calculate_performance_impact(self) -> Dict[str, float]:
        """Calculate performance impact of adversarial tests."""
        if not self.vulnerabilities:
            return {}
        
        # Calculate average execution times by category
        impact = {}
        for category in AttackCategory:
            category_vulns = [v for v in self.vulnerabilities if v.attack_category == category]
            if category_vulns:
                avg_time = np.mean([v.execution_time_ms for v in category_vulns])
                impact[f"{category.value}_avg_time_ms"] = avg_time
        
        return impact
    
    async def export_report(self, report: AdversarialTestReport, output_path: str = None) -> str:
        """Export adversarial testing report to JSON file."""
        if output_path is None:
            output_path = f"tests/adversarial/reports/adversarial_report_{self.session_id}.json"
        
        # Convert report to dictionary for JSON serialization
        report_dict = asdict(report)
        
        # Handle datetime serialization
        report_dict['start_time'] = report.start_time.isoformat()
        report_dict['end_time'] = report.end_time.isoformat()
        
        # Handle enum serialization
        for vuln in report_dict['critical_vulnerabilities']:
            vuln['attack_category'] = vuln['attack_category'].value if hasattr(vuln['attack_category'], 'value') else str(vuln['attack_category'])
            vuln['severity'] = vuln['severity'].value if hasattr(vuln['severity'], 'value') else str(vuln['severity'])
            vuln['timestamp'] = vuln['timestamp'].isoformat() if hasattr(vuln['timestamp'], 'isoformat') else str(vuln['timestamp'])
        
        # Write report to file
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        logger.info(f"Adversarial testing report exported to: {output_path}")
        return output_path
