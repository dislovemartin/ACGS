#!/usr/bin/env python3
"""
Adversarial Testing Framework Validation Script

This script validates the adversarial testing framework implementation
and ensures all components are working correctly.
"""

import asyncio
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.adversarial.core.adversarial_framework import (
    AdversarialTestingFramework, AdversarialTestConfig, AttackCategory, VulnerabilitySeverity
)
from tests.adversarial.core.constitutional_attacks import ConstitutionalAttackTester
from tests.adversarial.core.policy_poisoning import PolicyPoisoningDetector
from tests.adversarial.core.z3_bypass import Z3BypassTester
from tests.adversarial.core.llm_security import LLMSecurityTester
from tests.adversarial.core.cross_service_vulnerabilities import CrossServiceVulnerabilityScanner
from tests.adversarial.core.vulnerability_scanner import AutomatedVulnerabilityScanner
from tests.adversarial.core.stress_testing import StressTestingProtocol
from tests.adversarial.core.security_hardening import SecurityHardeningRecommendations


class TestAdversarialFrameworkValidation:
    """Test suite for adversarial testing framework validation."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdversarialTestConfig(
            target_services=["auth_service", "ac_service", "gs_service"],
            attack_categories=[AttackCategory.CONSTITUTIONAL_MANIPULATION, AttackCategory.LLM_PROMPT_INJECTION],
            max_test_cases=10,  # Reduced for testing
            timeout_seconds=30,
            parallel_execution=False,  # Simplified for testing
            max_concurrent_tests=2
        )
    
    @pytest.fixture
    def framework(self, config):
        """Create adversarial testing framework instance."""
        return AdversarialTestingFramework(config)
    
    def test_framework_initialization(self, framework):
        """Test framework initialization."""
        assert framework.config is not None
        assert framework.session_id is not None
        assert framework.vulnerabilities == []
        assert framework.service_endpoints is not None
        assert len(framework.service_endpoints) == 6  # All 6 services
    
    def test_config_validation(self, config):
        """Test configuration validation."""
        assert config.target_services is not None
        assert len(config.target_services) > 0
        assert config.attack_categories is not None
        assert len(config.attack_categories) > 0
        assert config.max_test_cases > 0
        assert config.timeout_seconds > 0
    
    @pytest.mark.asyncio
    async def test_service_availability_check(self, framework):
        """Test service availability checking."""
        # Mock aiohttp session
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            available_services = await framework._check_service_availability()
            
            # Should return all services as available (mocked)
            assert isinstance(available_services, list)
    
    @pytest.mark.asyncio
    async def test_constitutional_attack_tester(self, config):
        """Test constitutional attack tester."""
        tester = ConstitutionalAttackTester(config)
        
        # Mock service endpoints and responses
        available_services = ["ac_service"]
        service_endpoints = {"ac_service": "http://localhost:8001"}
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 403  # Should be blocked
            mock_response.json.return_value = {"error": "Unauthorized"}
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            results = await tester.run_tests(available_services, service_endpoints)
            
            # Should return results (empty if properly blocked)
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_policy_poisoning_detector(self, config):
        """Test policy poisoning detector."""
        detector = PolicyPoisoningDetector(config)
        
        # Test payload validation
        assert "sql_injection" in detector.malicious_payloads
        assert "code_injection" in detector.malicious_payloads
        assert "prompt_injection" in detector.malicious_payloads
        
        # Mock service test
        available_services = ["gs_service"]
        service_endpoints = {"gs_service": "http://localhost:8004"}
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 400  # Should reject malicious input
            mock_response.json.return_value = {"error": "Invalid input"}
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            results = await detector.run_tests(available_services, service_endpoints)
            
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_z3_bypass_tester(self, config):
        """Test Z3 bypass tester."""
        tester = Z3BypassTester(config)
        
        # Test malicious formula validation
        assert "timeout_bombs" in tester.malicious_formulas
        assert "injection_attacks" in tester.malicious_formulas
        assert "complexity_exploits" in tester.malicious_formulas
        
        # Mock service test
        available_services = ["fv_service"]
        service_endpoints = {"fv_service": "http://localhost:8003"}
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 422  # Should reject malicious formulas
            mock_response.json.return_value = {"error": "Invalid formula"}
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            results = await tester.run_tests(available_services, service_endpoints)
            
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_llm_security_tester(self, config):
        """Test LLM security tester."""
        tester = LLMSecurityTester(config)
        
        # Test injection payload validation
        assert "direct_injection" in tester.injection_payloads
        assert "role_confusion" in tester.injection_payloads
        assert "instruction_hijacking" in tester.injection_payloads
        
        # Test jailbreak technique validation
        assert "dan_style" in tester.jailbreak_techniques
        assert "hypothetical_scenarios" in tester.jailbreak_techniques
        
        # Mock service test
        available_services = ["gs_service"]
        service_endpoints = {"gs_service": "http://localhost:8004"}
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"response": "Safe response without injection"}
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            results = await tester.run_tests(available_services, service_endpoints)
            
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_cross_service_vulnerability_scanner(self, config):
        """Test cross-service vulnerability scanner."""
        scanner = CrossServiceVulnerabilityScanner(config)
        
        # Test payload validation
        assert "authentication_bypass" in scanner.cross_service_payloads
        assert "data_injection" in scanner.cross_service_payloads
        assert "service_impersonation" in scanner.cross_service_payloads
        
        # Test service flow validation
        assert len(scanner.service_flows) > 0
        
        # Mock service test
        available_services = ["auth_service", "ac_service"]
        service_endpoints = {
            "auth_service": "http://localhost:8000",
            "ac_service": "http://localhost:8001"
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 401  # Should reject unauthorized requests
            mock_response.json.return_value = {"error": "Unauthorized"}
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            results = await scanner.run_tests(available_services, service_endpoints)
            
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_automated_vulnerability_scanner(self, config):
        """Test automated vulnerability scanner."""
        scanner = AutomatedVulnerabilityScanner(config)
        
        # Test scanning tools configuration
        assert "bandit" in scanner.scanning_tools
        assert "safety" in scanner.scanning_tools
        assert "semgrep" in scanner.scanning_tools
        assert "trivy" in scanner.scanning_tools
        
        # Mock security tool execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"results": []}'
            
            results = await scanner.run_tests([], {})
            
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_stress_testing_protocol(self, config):
        """Test stress testing protocol."""
        protocol = StressTestingProtocol(config)
        
        # Test stress parameters validation
        assert protocol.stress_parameters["concurrent_requests"] > 0
        assert protocol.stress_parameters["request_duration"] > 0
        assert protocol.stress_parameters["memory_stress_size"] > 0
        
        # Mock service test
        available_services = ["auth_service"]
        service_endpoints = {"auth_service": "http://localhost:8000"}
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            # Mock psutil for resource monitoring
            with patch('psutil.cpu_percent', return_value=50.0), \
                 patch('psutil.virtual_memory') as mock_memory:
                mock_memory.return_value.percent = 60.0
                
                results = await protocol.run_tests(available_services, service_endpoints)
                
                assert isinstance(results, list)
    
    def test_security_hardening_recommendations(self):
        """Test security hardening recommendations generator."""
        generator = SecurityHardeningRecommendations()
        
        # Test compliance frameworks
        assert len(generator.compliance_frameworks) > 0
        assert "NIST Cybersecurity Framework" in generator.compliance_frameworks
        assert "ISO 27001" in generator.compliance_frameworks
        
        # Create mock vulnerabilities and report
        mock_vulnerabilities = []
        mock_report = MagicMock()
        mock_report.attack_success_rate = {AttackCategory.CONSTITUTIONAL_MANIPULATION: 0.1}
        
        # Generate recommendations
        hardening_report = generator.generate_recommendations(mock_vulnerabilities, mock_report)
        
        assert hardening_report is not None
        assert hardening_report.total_recommendations >= 0
        assert hardening_report.estimated_attack_surface_reduction >= 0.0
        assert isinstance(hardening_report.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_framework_integration(self, framework):
        """Test complete framework integration."""
        # Mock all external dependencies
        with patch.object(framework, '_check_service_availability', return_value=["auth_service"]), \
             patch.object(framework, 'initialize_testers') as mock_init, \
             patch.object(framework, '_run_category_tests', return_value=[]):
            
            mock_init.return_value = None
            framework.testers = {AttackCategory.CONSTITUTIONAL_MANIPULATION: MagicMock()}
            
            # Run comprehensive assessment
            report = await framework.run_comprehensive_assessment()
            
            assert report is not None
            assert report.test_session_id is not None
            assert report.total_tests_executed >= 0
            assert report.vulnerabilities_found >= 0
            assert isinstance(report.recommendations, list)
    
    def test_vulnerability_severity_assessment(self):
        """Test vulnerability severity assessment logic."""
        # Test severity mapping
        severities = [
            VulnerabilitySeverity.CRITICAL,
            VulnerabilitySeverity.HIGH,
            VulnerabilitySeverity.MEDIUM,
            VulnerabilitySeverity.LOW,
            VulnerabilitySeverity.INFO
        ]
        
        for severity in severities:
            assert severity.value in ["critical", "high", "medium", "low", "info"]
    
    def test_attack_category_coverage(self):
        """Test attack category coverage."""
        # Ensure all attack categories are covered
        expected_categories = [
            AttackCategory.CONSTITUTIONAL_MANIPULATION,
            AttackCategory.POLICY_SYNTHESIS_POISONING,
            AttackCategory.Z3_SOLVER_BYPASS,
            AttackCategory.LLM_PROMPT_INJECTION,
            AttackCategory.CROSS_SERVICE_VULNERABILITY,
            AttackCategory.AUTHENTICATION_BYPASS,
            AttackCategory.CRYPTOGRAPHIC_ATTACK,
            AttackCategory.STRESS_OVERLOAD
        ]
        
        for category in expected_categories:
            assert category.value is not None
            assert len(category.value) > 0


@pytest.mark.asyncio
async def test_adversarial_framework_end_to_end():
    """End-to-end test of adversarial testing framework."""
    
    # Create minimal configuration for testing
    config = AdversarialTestConfig(
        target_services=["auth_service"],
        attack_categories=[AttackCategory.CONSTITUTIONAL_MANIPULATION],
        max_test_cases=5,
        timeout_seconds=10,
        parallel_execution=False
    )
    
    framework = AdversarialTestingFramework(config)
    
    # Mock all external dependencies
    with patch.object(framework, '_check_service_availability', return_value=["auth_service"]), \
         patch.object(framework, 'initialize_testers'), \
         patch.object(framework, '_run_category_tests', return_value=[]):
        
        # Initialize mock testers
        framework.testers = {AttackCategory.CONSTITUTIONAL_MANIPULATION: MagicMock()}
        
        # Run assessment
        report = await framework.run_comprehensive_assessment()
        
        # Validate report structure
        assert report.test_session_id is not None
        assert report.start_time is not None
        assert report.end_time is not None
        assert report.total_tests_executed >= 0
        assert report.vulnerabilities_found >= 0
        assert report.overall_security_score >= 0.0
        assert report.overall_security_score <= 1.0
        assert isinstance(report.recommendations, list)
        assert isinstance(report.test_coverage, dict)


if __name__ == "__main__":
    # Run validation tests
    pytest.main([__file__, "-v", "--tb=short"])
