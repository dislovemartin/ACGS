"""
Security Hardening Recommendations for ACGS-PGP

This module generates security hardening recommendations based on vulnerability
assessment results and implements attack surface reduction measures.
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum

from .adversarial_framework import (
    VulnerabilityResult, AttackCategory, VulnerabilitySeverity, AdversarialTestReport
)

logger = logging.getLogger(__name__)


class HardeningPriority(Enum):
    """Priority levels for security hardening recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HardeningCategory(Enum):
    """Categories of security hardening measures."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    OUTPUT_ENCODING = "output_encoding"
    CRYPTOGRAPHY = "cryptography"
    NETWORK_SECURITY = "network_security"
    CONFIGURATION = "configuration"
    MONITORING = "monitoring"
    INCIDENT_RESPONSE = "incident_response"


@dataclass
class HardeningRecommendation:
    """Security hardening recommendation."""
    id: str
    title: str
    description: str
    category: HardeningCategory
    priority: HardeningPriority
    affected_services: List[str]
    vulnerability_types: List[AttackCategory]
    implementation_steps: List[str]
    verification_steps: List[str]
    estimated_effort: str  # e.g., "2-4 hours", "1-2 days"
    risk_reduction: float  # 0.0 to 1.0
    compliance_frameworks: List[str]
    references: List[str]


@dataclass
class SecurityHardeningReport:
    """Comprehensive security hardening report."""
    report_id: str
    generation_time: datetime
    total_recommendations: int
    critical_recommendations: int
    high_priority_recommendations: int
    estimated_attack_surface_reduction: float
    recommendations: List[HardeningRecommendation]
    implementation_roadmap: Dict[str, List[str]]
    compliance_mapping: Dict[str, List[str]]


class SecurityHardeningRecommendations:
    """
    Generator for security hardening recommendations.
    
    This component analyzes vulnerability assessment results and generates
    prioritized security hardening recommendations to reduce attack surface.
    """
    
    def __init__(self):
        self.hardening_templates = self._load_hardening_templates()
        self.compliance_frameworks = [
            "NIST Cybersecurity Framework",
            "ISO 27001",
            "SOC 2",
            "GDPR",
            "HIPAA",
            "PCI DSS"
        ]
    
    def generate_recommendations(
        self, 
        vulnerabilities: List[VulnerabilityResult],
        adversarial_report: AdversarialTestReport
    ) -> SecurityHardeningReport:
        """Generate security hardening recommendations based on vulnerability assessment."""
        
        logger.info("Generating security hardening recommendations")
        
        # Analyze vulnerabilities by category and severity
        vulnerability_analysis = self._analyze_vulnerabilities(vulnerabilities)
        
        # Generate recommendations based on analysis
        recommendations = self._generate_recommendations_from_analysis(vulnerability_analysis)
        
        # Prioritize recommendations
        prioritized_recommendations = self._prioritize_recommendations(recommendations, adversarial_report)
        
        # Create implementation roadmap
        implementation_roadmap = self._create_implementation_roadmap(prioritized_recommendations)
        
        # Map to compliance frameworks
        compliance_mapping = self._map_to_compliance_frameworks(prioritized_recommendations)
        
        # Calculate attack surface reduction
        attack_surface_reduction = self._calculate_attack_surface_reduction(prioritized_recommendations)
        
        # Count recommendations by priority
        critical_count = sum(1 for r in prioritized_recommendations if r.priority == HardeningPriority.CRITICAL)
        high_count = sum(1 for r in prioritized_recommendations if r.priority == HardeningPriority.HIGH)
        
        report = SecurityHardeningReport(
            report_id=f"hardening_report_{int(time.time())}",
            generation_time=datetime.now(timezone.utc),
            total_recommendations=len(prioritized_recommendations),
            critical_recommendations=critical_count,
            high_priority_recommendations=high_count,
            estimated_attack_surface_reduction=attack_surface_reduction,
            recommendations=prioritized_recommendations,
            implementation_roadmap=implementation_roadmap,
            compliance_mapping=compliance_mapping
        )
        
        logger.info(f"Generated {len(prioritized_recommendations)} security hardening recommendations")
        return report
    
    def _analyze_vulnerabilities(self, vulnerabilities: List[VulnerabilityResult]) -> Dict[str, Any]:
        """Analyze vulnerabilities to identify patterns and priorities."""
        analysis = {
            "by_category": {},
            "by_severity": {},
            "by_service": {},
            "attack_patterns": [],
            "common_weaknesses": []
        }
        
        # Analyze by category
        for vuln in vulnerabilities:
            category = vuln.attack_category.value
            if category not in analysis["by_category"]:
                analysis["by_category"][category] = []
            analysis["by_category"][category].append(vuln)
        
        # Analyze by severity
        for vuln in vulnerabilities:
            severity = vuln.severity.value
            if severity not in analysis["by_severity"]:
                analysis["by_severity"][severity] = []
            analysis["by_severity"][severity].append(vuln)
        
        # Analyze by service
        for vuln in vulnerabilities:
            service = vuln.service_target
            if service not in analysis["by_service"]:
                analysis["by_service"][service] = []
            analysis["by_service"][service].append(vuln)
        
        # Identify attack patterns
        analysis["attack_patterns"] = self._identify_attack_patterns(vulnerabilities)
        
        # Identify common weaknesses
        analysis["common_weaknesses"] = self._identify_common_weaknesses(vulnerabilities)
        
        return analysis
    
    def _generate_recommendations_from_analysis(self, analysis: Dict[str, Any]) -> List[HardeningRecommendation]:
        """Generate recommendations based on vulnerability analysis."""
        recommendations = []
        
        # Generate category-specific recommendations
        for category, vulns in analysis["by_category"].items():
            category_recommendations = self._generate_category_recommendations(category, vulns)
            recommendations.extend(category_recommendations)
        
        # Generate service-specific recommendations
        for service, vulns in analysis["by_service"].items():
            service_recommendations = self._generate_service_recommendations(service, vulns)
            recommendations.extend(service_recommendations)
        
        # Generate pattern-based recommendations
        pattern_recommendations = self._generate_pattern_recommendations(analysis["attack_patterns"])
        recommendations.extend(pattern_recommendations)
        
        # Generate weakness-based recommendations
        weakness_recommendations = self._generate_weakness_recommendations(analysis["common_weaknesses"])
        recommendations.extend(weakness_recommendations)
        
        # Remove duplicates
        unique_recommendations = self._deduplicate_recommendations(recommendations)
        
        return unique_recommendations
    
    def _generate_category_recommendations(self, category: str, vulnerabilities: List[VulnerabilityResult]) -> List[HardeningRecommendation]:
        """Generate recommendations for a specific vulnerability category."""
        recommendations = []
        
        if category == "constitutional_manipulation":
            recommendations.extend(self._get_constitutional_hardening_recommendations(vulnerabilities))
        elif category == "policy_synthesis_poisoning":
            recommendations.extend(self._get_policy_synthesis_hardening_recommendations(vulnerabilities))
        elif category == "z3_solver_bypass":
            recommendations.extend(self._get_z3_hardening_recommendations(vulnerabilities))
        elif category == "llm_prompt_injection":
            recommendations.extend(self._get_llm_hardening_recommendations(vulnerabilities))
        elif category == "cross_service_vulnerability":
            recommendations.extend(self._get_cross_service_hardening_recommendations(vulnerabilities))
        
        return recommendations
    
    def _get_constitutional_hardening_recommendations(self, vulnerabilities: List[VulnerabilityResult]) -> List[HardeningRecommendation]:
        """Generate constitutional manipulation hardening recommendations."""
        return [
            HardeningRecommendation(
                id="const_auth_001",
                title="Implement Multi-Factor Authentication for Constitutional Changes",
                description="Require multi-factor authentication for all constitutional principle modifications and amendments",
                category=HardeningCategory.AUTHENTICATION,
                priority=HardeningPriority.CRITICAL,
                affected_services=["ac_service"],
                vulnerability_types=[AttackCategory.CONSTITUTIONAL_MANIPULATION],
                implementation_steps=[
                    "Implement MFA for constitutional council members",
                    "Add hardware token support for critical operations",
                    "Implement time-based one-time passwords (TOTP)",
                    "Add biometric authentication for high-privilege operations"
                ],
                verification_steps=[
                    "Test MFA bypass attempts",
                    "Verify token validation logic",
                    "Test session management security"
                ],
                estimated_effort="1-2 days",
                risk_reduction=0.8,
                compliance_frameworks=["NIST Cybersecurity Framework", "ISO 27001"],
                references=["NIST SP 800-63B", "OWASP Authentication Cheat Sheet"]
            ),
            HardeningRecommendation(
                id="const_access_001",
                title="Implement Role-Based Access Control for Constitutional Operations",
                description="Enforce strict RBAC for constitutional principle management with principle of least privilege",
                category=HardeningCategory.AUTHORIZATION,
                priority=HardeningPriority.HIGH,
                affected_services=["ac_service"],
                vulnerability_types=[AttackCategory.CONSTITUTIONAL_MANIPULATION],
                implementation_steps=[
                    "Define granular permissions for constitutional operations",
                    "Implement role hierarchy with inheritance",
                    "Add permission validation middleware",
                    "Implement dynamic permission evaluation"
                ],
                verification_steps=[
                    "Test privilege escalation attempts",
                    "Verify permission inheritance logic",
                    "Test unauthorized access scenarios"
                ],
                estimated_effort="2-3 days",
                risk_reduction=0.7,
                compliance_frameworks=["NIST Cybersecurity Framework", "SOC 2"],
                references=["NIST SP 800-162", "OWASP Access Control Cheat Sheet"]
            )
        ]
    
    def _get_llm_hardening_recommendations(self, vulnerabilities: List[VulnerabilityResult]) -> List[HardeningRecommendation]:
        """Generate LLM security hardening recommendations."""
        return [
            HardeningRecommendation(
                id="llm_input_001",
                title="Implement Advanced Prompt Injection Detection",
                description="Deploy multi-layered prompt injection detection and prevention mechanisms",
                category=HardeningCategory.INPUT_VALIDATION,
                priority=HardeningPriority.CRITICAL,
                affected_services=["gs_service"],
                vulnerability_types=[AttackCategory.LLM_PROMPT_INJECTION],
                implementation_steps=[
                    "Implement prompt injection pattern detection",
                    "Add semantic analysis for malicious prompts",
                    "Implement prompt sanitization and encoding",
                    "Add constitutional prompt protection layers"
                ],
                verification_steps=[
                    "Test known prompt injection techniques",
                    "Verify sanitization effectiveness",
                    "Test bypass attempts"
                ],
                estimated_effort="3-5 days",
                risk_reduction=0.85,
                compliance_frameworks=["NIST AI Risk Management Framework"],
                references=["OWASP Top 10 for LLM Applications", "NIST AI 100-1"]
            )
        ]
    
    def _prioritize_recommendations(
        self, 
        recommendations: List[HardeningRecommendation],
        adversarial_report: AdversarialTestReport
    ) -> List[HardeningRecommendation]:
        """Prioritize recommendations based on risk and impact."""
        
        # Calculate priority scores
        for recommendation in recommendations:
            priority_score = self._calculate_priority_score(recommendation, adversarial_report)
            recommendation.priority = self._determine_priority_from_score(priority_score)
        
        # Sort by priority and risk reduction
        prioritized = sorted(
            recommendations,
            key=lambda r: (
                self._priority_to_numeric(r.priority),
                -r.risk_reduction  # Higher risk reduction first
            )
        )
        
        return prioritized
    
    def _calculate_attack_surface_reduction(self, recommendations: List[HardeningRecommendation]) -> float:
        """Calculate estimated attack surface reduction from implementing recommendations."""
        
        # Weight recommendations by priority and risk reduction
        total_reduction = 0.0
        total_weight = 0.0
        
        priority_weights = {
            HardeningPriority.CRITICAL: 1.0,
            HardeningPriority.HIGH: 0.8,
            HardeningPriority.MEDIUM: 0.6,
            HardeningPriority.LOW: 0.4
        }
        
        for recommendation in recommendations:
            weight = priority_weights[recommendation.priority]
            total_reduction += recommendation.risk_reduction * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        # Calculate weighted average and cap at 80% (realistic maximum)
        reduction = min(0.8, total_reduction / total_weight)
        return reduction
    
    def _create_implementation_roadmap(self, recommendations: List[HardeningRecommendation]) -> Dict[str, List[str]]:
        """Create implementation roadmap organized by phases."""
        roadmap = {
            "Phase 1 - Critical (0-2 weeks)": [],
            "Phase 2 - High Priority (2-6 weeks)": [],
            "Phase 3 - Medium Priority (6-12 weeks)": [],
            "Phase 4 - Low Priority (12+ weeks)": []
        }
        
        for recommendation in recommendations:
            if recommendation.priority == HardeningPriority.CRITICAL:
                roadmap["Phase 1 - Critical (0-2 weeks)"].append(recommendation.id)
            elif recommendation.priority == HardeningPriority.HIGH:
                roadmap["Phase 2 - High Priority (2-6 weeks)"].append(recommendation.id)
            elif recommendation.priority == HardeningPriority.MEDIUM:
                roadmap["Phase 3 - Medium Priority (6-12 weeks)"].append(recommendation.id)
            else:
                roadmap["Phase 4 - Low Priority (12+ weeks)"].append(recommendation.id)
        
        return roadmap
    
    def _map_to_compliance_frameworks(self, recommendations: List[HardeningRecommendation]) -> Dict[str, List[str]]:
        """Map recommendations to compliance frameworks."""
        mapping = {}
        
        for framework in self.compliance_frameworks:
            mapping[framework] = []
            for recommendation in recommendations:
                if framework in recommendation.compliance_frameworks:
                    mapping[framework].append(recommendation.id)
        
        return mapping
    
    def _load_hardening_templates(self) -> Dict[str, Any]:
        """Load hardening recommendation templates."""
        # This would typically load from a configuration file
        return {
            "authentication": [],
            "authorization": [],
            "input_validation": [],
            "cryptography": [],
            "monitoring": []
        }
    
    def _identify_attack_patterns(self, vulnerabilities: List[VulnerabilityResult]) -> List[str]:
        """Identify common attack patterns from vulnerabilities."""
        patterns = []
        
        # Analyze vulnerability descriptions for patterns
        injection_count = sum(1 for v in vulnerabilities if "injection" in v.vulnerability_description.lower())
        if injection_count > 3:
            patterns.append("injection_attacks")
        
        bypass_count = sum(1 for v in vulnerabilities if "bypass" in v.vulnerability_description.lower())
        if bypass_count > 2:
            patterns.append("bypass_attacks")
        
        return patterns
    
    def _identify_common_weaknesses(self, vulnerabilities: List[VulnerabilityResult]) -> List[str]:
        """Identify common security weaknesses."""
        weaknesses = []
        
        # Analyze for common weakness patterns
        auth_vulns = sum(1 for v in vulnerabilities if "auth" in v.vulnerability_description.lower())
        if auth_vulns > 2:
            weaknesses.append("authentication_weaknesses")
        
        validation_vulns = sum(1 for v in vulnerabilities if "validation" in v.vulnerability_description.lower())
        if validation_vulns > 2:
            weaknesses.append("input_validation_weaknesses")
        
        return weaknesses
    
    def _generate_service_recommendations(self, service: str, vulnerabilities: List[VulnerabilityResult]) -> List[HardeningRecommendation]:
        """Generate service-specific recommendations."""
        # Implementation for service-specific recommendations
        return []
    
    def _generate_pattern_recommendations(self, patterns: List[str]) -> List[HardeningRecommendation]:
        """Generate pattern-based recommendations."""
        # Implementation for pattern-based recommendations
        return []
    
    def _generate_weakness_recommendations(self, weaknesses: List[str]) -> List[HardeningRecommendation]:
        """Generate weakness-based recommendations."""
        # Implementation for weakness-based recommendations
        return []
    
    def _deduplicate_recommendations(self, recommendations: List[HardeningRecommendation]) -> List[HardeningRecommendation]:
        """Remove duplicate recommendations."""
        seen_ids = set()
        unique_recommendations = []
        
        for recommendation in recommendations:
            if recommendation.id not in seen_ids:
                seen_ids.add(recommendation.id)
                unique_recommendations.append(recommendation)
        
        return unique_recommendations
    
    def _calculate_priority_score(self, recommendation: HardeningRecommendation, report: AdversarialTestReport) -> float:
        """Calculate priority score for a recommendation."""
        # Base score from risk reduction
        score = recommendation.risk_reduction
        
        # Adjust based on affected vulnerability types
        for vuln_type in recommendation.vulnerability_types:
            if vuln_type in report.attack_success_rate:
                score += report.attack_success_rate[vuln_type] * 0.5
        
        return min(1.0, score)
    
    def _determine_priority_from_score(self, score: float) -> HardeningPriority:
        """Determine priority level from score."""
        if score >= 0.8:
            return HardeningPriority.CRITICAL
        elif score >= 0.6:
            return HardeningPriority.HIGH
        elif score >= 0.4:
            return HardeningPriority.MEDIUM
        else:
            return HardeningPriority.LOW
    
    def _priority_to_numeric(self, priority: HardeningPriority) -> int:
        """Convert priority to numeric value for sorting."""
        mapping = {
            HardeningPriority.CRITICAL: 0,
            HardeningPriority.HIGH: 1,
            HardeningPriority.MEDIUM: 2,
            HardeningPriority.LOW: 3
        }
        return mapping[priority]
    
    def export_report(self, report: SecurityHardeningReport, output_path: str = None) -> str:
        """Export security hardening report to JSON file."""
        if output_path is None:
            output_path = f"tests/adversarial/reports/hardening_report_{report.report_id}.json"
        
        # Convert report to dictionary for JSON serialization
        report_dict = asdict(report)
        
        # Handle datetime and enum serialization
        report_dict['generation_time'] = report.generation_time.isoformat()
        
        for recommendation in report_dict['recommendations']:
            recommendation['category'] = recommendation['category'].value if hasattr(recommendation['category'], 'value') else str(recommendation['category'])
            recommendation['priority'] = recommendation['priority'].value if hasattr(recommendation['priority'], 'value') else str(recommendation['priority'])
            recommendation['vulnerability_types'] = [
                vt.value if hasattr(vt, 'value') else str(vt) 
                for vt in recommendation['vulnerability_types']
            ]
        
        # Write report to file
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        logger.info(f"Security hardening report exported to: {output_path}")
        return output_path
