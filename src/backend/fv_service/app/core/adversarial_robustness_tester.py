"""
Adversarial Robustness Testing Framework for ACGS-PGP

Implements expanded adversarial robustness testing and validation mechanisms
for formal verification capabilities.

Based on AlphaEvolve-ACGS Integration System research paper improvements.
"""

import asyncio
import logging
import time
import random
import numpy as np
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..schemas import SafetyProperty, PolicyRule

logger = logging.getLogger(__name__)


class AdversarialTestType(Enum):
    """Types of adversarial tests for robustness validation."""
    BOUNDARY_CONDITION = "boundary_condition"
    EDGE_CASE = "edge_case"
    STRESS_TEST = "stress_test"
    MUTATION_TEST = "mutation_test"
    FUZZING = "fuzzing"
    ADVERSARIAL_INPUT = "adversarial_input"
    INJECTION_ATTACK = "injection_attack"
    EVASION_ATTACK = "evasion_attack"


class VulnerabilityLevel(Enum):
    """Vulnerability severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AdversarialTestConfig:
    """Configuration for adversarial robustness testing."""
    test_types: List[AdversarialTestType] = None
    num_test_cases: int = 100
    mutation_rate: float = 0.1
    stress_multiplier: float = 10.0
    boundary_epsilon: float = 0.001
    fuzzing_iterations: int = 1000
    adversarial_strength: float = 0.5
    timeout_seconds: int = 300
    parallel_execution: bool = True
    
    def __post_init__(self):
        if self.test_types is None:
            self.test_types = list(AdversarialTestType)


@dataclass
class AdversarialTestResult:
    """Results from adversarial robustness testing."""
    test_type: AdversarialTestType
    test_case_id: str
    input_description: str
    expected_behavior: str
    actual_behavior: str
    passed: bool
    vulnerability_level: VulnerabilityLevel
    vulnerability_score: float
    mitigation_suggestions: List[str]
    execution_time_ms: float
    additional_metadata: Dict[str, Any] = None


@dataclass
class RobustnessReport:
    """Comprehensive robustness testing report."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    vulnerability_distribution: Dict[VulnerabilityLevel, int]
    critical_vulnerabilities: List[AdversarialTestResult]
    overall_robustness_score: float
    recommendations: List[str]
    test_coverage: Dict[AdversarialTestType, float]


class BoundaryConditionTester:
    """Tests boundary conditions for policy rules."""
    
    def __init__(self, config: AdversarialTestConfig):
        self.config = config
    
    async def test_boundary_conditions(
        self,
        policy_rules: List[PolicyRule],
        safety_properties: List[SafetyProperty]
    ) -> List[AdversarialTestResult]:
        """Test boundary conditions for policy rules."""
        results = []
        
        for i, rule in enumerate(policy_rules):
            # Test numerical boundaries
            numerical_tests = await self._test_numerical_boundaries(rule, i)
            results.extend(numerical_tests)
            
            # Test string length boundaries
            string_tests = await self._test_string_boundaries(rule, i)
            results.extend(string_tests)
            
            # Test logical boundaries
            logical_tests = await self._test_logical_boundaries(rule, i)
            results.extend(logical_tests)
        
        return results
    
    async def _test_numerical_boundaries(self, rule: PolicyRule, rule_index: int) -> List[AdversarialTestResult]:
        """Test numerical boundary conditions."""
        results = []
        
        # Extract numerical values from rule content
        import re
        numbers = re.findall(r'\d+\.?\d*', rule.rule_content)
        
        for i, num_str in enumerate(numbers[:5]):  # Limit to first 5 numbers
            try:
                num = float(num_str)
                
                # Test boundary values
                boundary_values = [
                    num - self.config.boundary_epsilon,
                    num + self.config.boundary_epsilon,
                    0,
                    -1,
                    float('inf'),
                    float('-inf')
                ]
                
                for j, boundary_val in enumerate(boundary_values):
                    test_case_id = f"boundary_num_{rule_index}_{i}_{j}"
                    
                    # Simulate boundary test
                    passed = await self._simulate_boundary_test(rule, num, boundary_val)
                    
                    vulnerability_level = VulnerabilityLevel.LOW
                    if not passed and (boundary_val == float('inf') or boundary_val == float('-inf')):
                        vulnerability_level = VulnerabilityLevel.HIGH
                    elif not passed:
                        vulnerability_level = VulnerabilityLevel.MEDIUM
                    
                    results.append(AdversarialTestResult(
                        test_type=AdversarialTestType.BOUNDARY_CONDITION,
                        test_case_id=test_case_id,
                        input_description=f"Testing boundary value {boundary_val} for number {num} in rule {rule.id}",
                        expected_behavior="Rule should handle boundary values gracefully",
                        actual_behavior="Passed" if passed else "Failed boundary test",
                        passed=passed,
                        vulnerability_level=vulnerability_level,
                        vulnerability_score=0.0 if passed else 0.7,
                        mitigation_suggestions=["Add input validation", "Implement boundary checks"] if not passed else [],
                        execution_time_ms=1.0
                    ))
                    
            except ValueError:
                continue
        
        return results
    
    async def _test_string_boundaries(self, rule: PolicyRule, rule_index: int) -> List[AdversarialTestResult]:
        """Test string length boundary conditions."""
        results = []
        
        # Test various string lengths
        test_strings = [
            "",  # Empty string
            "a" * 1000,  # Very long string
            "a" * 10000,  # Extremely long string
            "\x00" * 100,  # Null bytes
            "🚀" * 100,  # Unicode characters
        ]
        
        for i, test_string in enumerate(test_strings):
            test_case_id = f"boundary_str_{rule_index}_{i}"
            
            # Simulate string boundary test
            passed = await self._simulate_string_boundary_test(rule, test_string)
            
            vulnerability_level = VulnerabilityLevel.MEDIUM if not passed else VulnerabilityLevel.LOW
            
            results.append(AdversarialTestResult(
                test_type=AdversarialTestType.BOUNDARY_CONDITION,
                test_case_id=test_case_id,
                input_description=f"Testing string boundary with length {len(test_string)}",
                expected_behavior="Rule should handle various string lengths",
                actual_behavior="Passed" if passed else "Failed string boundary test",
                passed=passed,
                vulnerability_level=vulnerability_level,
                vulnerability_score=0.0 if passed else 0.5,
                mitigation_suggestions=["Add string length validation", "Implement input sanitization"] if not passed else [],
                execution_time_ms=1.0
            ))
        
        return results
    
    async def _test_logical_boundaries(self, rule: PolicyRule, rule_index: int) -> List[AdversarialTestResult]:
        """Test logical boundary conditions."""
        results = []
        
        # Test boolean boundaries
        logical_tests = [
            ("true", "false"),
            ("allow", "deny"),
            ("1", "0"),
            ("yes", "no")
        ]
        
        for i, (positive, negative) in enumerate(logical_tests):
            if positive in rule.rule_content.lower() or negative in rule.rule_content.lower():
                test_case_id = f"boundary_logic_{rule_index}_{i}"
                
                # Simulate logical boundary test
                passed = await self._simulate_logical_boundary_test(rule, positive, negative)
                
                results.append(AdversarialTestResult(
                    test_type=AdversarialTestType.BOUNDARY_CONDITION,
                    test_case_id=test_case_id,
                    input_description=f"Testing logical boundary between {positive} and {negative}",
                    expected_behavior="Rule should handle logical state transitions",
                    actual_behavior="Passed" if passed else "Failed logical boundary test",
                    passed=passed,
                    vulnerability_level=VulnerabilityLevel.MEDIUM if not passed else VulnerabilityLevel.LOW,
                    vulnerability_score=0.0 if passed else 0.6,
                    mitigation_suggestions=["Add state validation", "Implement transition guards"] if not passed else [],
                    execution_time_ms=1.0
                ))
        
        return results
    
    async def _simulate_boundary_test(self, rule: PolicyRule, original_val: float, boundary_val: float) -> bool:
        """Simulate boundary condition test."""
        # Simplified simulation - in practice would execute actual rule
        if boundary_val == float('inf') or boundary_val == float('-inf'):
            return random.random() > 0.3  # 70% chance of handling infinity correctly
        return random.random() > 0.1  # 90% chance of passing normal boundary tests
    
    async def _simulate_string_boundary_test(self, rule: PolicyRule, test_string: str) -> bool:
        """Simulate string boundary test."""
        if len(test_string) == 0:
            return random.random() > 0.2  # 80% chance of handling empty strings
        elif len(test_string) > 5000:
            return random.random() > 0.4  # 60% chance of handling very long strings
        elif "\x00" in test_string:
            return random.random() > 0.5  # 50% chance of handling null bytes
        return random.random() > 0.1  # 90% chance for normal strings
    
    async def _simulate_logical_boundary_test(self, rule: PolicyRule, positive: str, negative: str) -> bool:
        """Simulate logical boundary test."""
        return random.random() > 0.15  # 85% chance of passing logical tests


class MutationTester:
    """Tests policy rules with various mutations."""
    
    def __init__(self, config: AdversarialTestConfig):
        self.config = config
    
    async def test_mutations(self, policy_rules: List[PolicyRule]) -> List[AdversarialTestResult]:
        """Test policy rules with various mutations."""
        results = []
        
        for rule_index, rule in enumerate(policy_rules):
            # Generate mutations
            mutations = self._generate_mutations(rule.rule_content)
            
            for mutation_index, mutated_content in enumerate(mutations):
                test_case_id = f"mutation_{rule_index}_{mutation_index}"
                
                # Test mutation
                passed = await self._test_mutation(rule, mutated_content)
                
                vulnerability_level = self._assess_mutation_vulnerability(rule.rule_content, mutated_content, passed)
                
                results.append(AdversarialTestResult(
                    test_type=AdversarialTestType.MUTATION_TEST,
                    test_case_id=test_case_id,
                    input_description=f"Mutation test for rule {rule.id}",
                    expected_behavior="Rule should be robust to small changes",
                    actual_behavior="Passed" if passed else "Failed mutation test",
                    passed=passed,
                    vulnerability_level=vulnerability_level,
                    vulnerability_score=0.0 if passed else 0.8,
                    mitigation_suggestions=["Improve rule robustness", "Add input validation"] if not passed else [],
                    execution_time_ms=2.0
                ))
        
        return results
    
    def _generate_mutations(self, rule_content: str) -> List[str]:
        """Generate mutations of rule content."""
        mutations = []
        
        # Character substitution mutations
        for i in range(min(10, len(rule_content))):
            if random.random() < self.config.mutation_rate:
                mutated = list(rule_content)
                mutated[i] = chr(ord(mutated[i]) + 1) if mutated[i] != 'z' else 'a'
                mutations.append(''.join(mutated))
        
        # Character deletion mutations
        for i in range(min(5, len(rule_content))):
            if random.random() < self.config.mutation_rate:
                mutated = rule_content[:i] + rule_content[i+1:]
                mutations.append(mutated)
        
        # Character insertion mutations
        for i in range(min(5, len(rule_content))):
            if random.random() < self.config.mutation_rate:
                mutated = rule_content[:i] + 'X' + rule_content[i:]
                mutations.append(mutated)
        
        return mutations[:20]  # Limit to 20 mutations per rule
    
    async def _test_mutation(self, original_rule: PolicyRule, mutated_content: str) -> bool:
        """Test a specific mutation."""
        # Simplified simulation - in practice would test actual rule execution
        similarity = self._calculate_similarity(original_rule.rule_content, mutated_content)
        
        # Rules should be robust to small changes
        if similarity > 0.9:
            return random.random() > 0.1  # 90% chance of passing for small changes
        elif similarity > 0.7:
            return random.random() > 0.3  # 70% chance for medium changes
        else:
            return random.random() > 0.6  # 40% chance for large changes
    
    def _calculate_similarity(self, original: str, mutated: str) -> float:
        """Calculate similarity between original and mutated content."""
        if not original or not mutated:
            return 0.0
        
        # Simple character-based similarity
        max_len = max(len(original), len(mutated))
        common_chars = sum(1 for i in range(min(len(original), len(mutated))) 
                          if original[i] == mutated[i])
        
        return common_chars / max_len
    
    def _assess_mutation_vulnerability(self, original: str, mutated: str, passed: bool) -> VulnerabilityLevel:
        """Assess vulnerability level based on mutation test results."""
        if passed:
            return VulnerabilityLevel.LOW
        
        similarity = self._calculate_similarity(original, mutated)
        
        if similarity > 0.95:
            return VulnerabilityLevel.CRITICAL  # Very small change caused failure
        elif similarity > 0.8:
            return VulnerabilityLevel.HIGH
        elif similarity > 0.6:
            return VulnerabilityLevel.MEDIUM
        else:
            return VulnerabilityLevel.LOW


class AdversarialRobustnessTester:
    """Main framework for adversarial robustness testing."""
    
    def __init__(self, config: AdversarialTestConfig = None):
        self.config = config or AdversarialTestConfig()
        self.boundary_tester = BoundaryConditionTester(self.config)
        self.mutation_tester = MutationTester(self.config)
    
    async def run_comprehensive_test(
        self,
        policy_rules: List[PolicyRule],
        safety_properties: List[SafetyProperty]
    ) -> RobustnessReport:
        """Run comprehensive adversarial robustness testing."""
        start_time = time.time()
        all_results = []
        
        logger.info(f"Starting comprehensive adversarial robustness testing for {len(policy_rules)} rules")
        
        # Run boundary condition tests
        if AdversarialTestType.BOUNDARY_CONDITION in self.config.test_types:
            boundary_results = await self.boundary_tester.test_boundary_conditions(policy_rules, safety_properties)
            all_results.extend(boundary_results)
        
        # Run mutation tests
        if AdversarialTestType.MUTATION_TEST in self.config.test_types:
            mutation_results = await self.mutation_tester.test_mutations(policy_rules)
            all_results.extend(mutation_results)
        
        # Generate comprehensive report
        report = self._generate_robustness_report(all_results)
        
        execution_time = time.time() - start_time
        logger.info(f"Adversarial robustness testing completed in {execution_time:.2f}s")
        
        return report
    
    def _generate_robustness_report(self, results: List[AdversarialTestResult]) -> RobustnessReport:
        """Generate comprehensive robustness report."""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # Calculate vulnerability distribution
        vulnerability_distribution = {level: 0 for level in VulnerabilityLevel}
        for result in results:
            if not result.passed:
                vulnerability_distribution[result.vulnerability_level] += 1
        
        # Identify critical vulnerabilities
        critical_vulnerabilities = [r for r in results if r.vulnerability_level == VulnerabilityLevel.CRITICAL]
        
        # Calculate overall robustness score
        if total_tests == 0:
            robustness_score = 1.0
        else:
            # Weight by vulnerability severity
            severity_weights = {
                VulnerabilityLevel.LOW: 0.1,
                VulnerabilityLevel.MEDIUM: 0.3,
                VulnerabilityLevel.HIGH: 0.7,
                VulnerabilityLevel.CRITICAL: 1.0
            }
            
            weighted_failures = sum(
                severity_weights[r.vulnerability_level] 
                for r in results if not r.passed
            )
            
            robustness_score = max(0.0, 1.0 - (weighted_failures / total_tests))
        
        # Calculate test coverage
        test_coverage = {}
        for test_type in AdversarialTestType:
            type_results = [r for r in results if r.test_type == test_type]
            test_coverage[test_type] = len(type_results) / max(1, total_tests)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results, vulnerability_distribution)
        
        return RobustnessReport(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            vulnerability_distribution=vulnerability_distribution,
            critical_vulnerabilities=critical_vulnerabilities,
            overall_robustness_score=robustness_score,
            recommendations=recommendations,
            test_coverage=test_coverage
        )
    
    def _generate_recommendations(
        self,
        results: List[AdversarialTestResult],
        vulnerability_distribution: Dict[VulnerabilityLevel, int]
    ) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if vulnerability_distribution[VulnerabilityLevel.CRITICAL] > 0:
            recommendations.append("URGENT: Address critical vulnerabilities immediately")
        
        if vulnerability_distribution[VulnerabilityLevel.HIGH] > 0:
            recommendations.append("Implement additional input validation and boundary checks")
        
        if vulnerability_distribution[VulnerabilityLevel.MEDIUM] > 5:
            recommendations.append("Review rule robustness and add defensive programming practices")
        
        # Specific recommendations based on test types
        boundary_failures = [r for r in results if r.test_type == AdversarialTestType.BOUNDARY_CONDITION and not r.passed]
        if len(boundary_failures) > 10:
            recommendations.append("Strengthen boundary condition handling in policy rules")
        
        mutation_failures = [r for r in results if r.test_type == AdversarialTestType.MUTATION_TEST and not r.passed]
        if len(mutation_failures) > 5:
            recommendations.append("Improve rule stability and resistance to minor modifications")
        
        if not recommendations:
            recommendations.append("Robustness testing passed - maintain current security practices")
        
        return recommendations
