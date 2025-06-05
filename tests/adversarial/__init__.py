"""
Adversarial Testing Framework for ACGS-PGP

This module provides comprehensive adversarial testing capabilities for the
AI Compliance Governance System - Policy Generation Platform.

Components:
- Constitutional principle manipulation attacks
- Policy synthesis poisoning detection
- Z3 solver constraint bypass testing
- LLM prompt injection and jailbreaking
- Cross-service communication vulnerabilities
- Automated vulnerability scanning
- Security hardening recommendations
"""

from .core.adversarial_framework import AdversarialTestingFramework
from .core.constitutional_attacks import ConstitutionalAttackTester
from .core.policy_poisoning import PolicyPoisoningDetector
from .core.z3_bypass import Z3BypassTester
from .core.llm_security import LLMSecurityTester
from .core.cross_service_vulnerabilities import CrossServiceVulnerabilityScanner
from .core.vulnerability_scanner import AutomatedVulnerabilityScanner
from .core.stress_testing import StressTestingProtocol
from .core.security_hardening import SecurityHardeningRecommendations

__all__ = [
    "AdversarialTestingFramework",
    "ConstitutionalAttackTester", 
    "PolicyPoisoningDetector",
    "Z3BypassTester",
    "LLMSecurityTester",
    "CrossServiceVulnerabilityScanner",
    "AutomatedVulnerabilityScanner",
    "StressTestingProtocol",
    "SecurityHardeningRecommendations"
]
