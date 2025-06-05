"""
validation_dsl_parser.py

QEC-inspired Validation DSL Parser for transforming natural language validation
criteria into machine-actionable test specifications.

Classes:
    ValidationDSLParser: Main parser for structured validation criteria
    ValidationScenario: Data structure for validation test cases
    ValidationLinter: Linter for validation criteria quality
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationScenario:
    """Data structure for a validation test scenario."""
    id: str
    given: str  # Context/precondition
    when: str   # Action/input
    then: str   # Expected outcome
    tags: List[str]  # Categories for filtering
    priority: str = "medium"  # low, medium, high, critical
    metadata: Optional[Dict[str, Any]] = None


class ValidationDSLParser:
    """
    QEC-inspired Validation DSL Parser.
    
    Transforms ambiguous natural language validation criteria into machine-actionable
    test specifications, enabling automated validation and reducing interpretation errors.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the validation DSL parser.
        
        Args:
            config: Configuration dictionary for parser settings
        """
        self.config = config or self._get_default_config()
        self.linter = ValidationLinter()
        
        # Pattern matching for scenario extraction
        self._scenario_patterns = self._load_scenario_patterns()
        
        logger.info("Validation DSL Parser initialized")
    
    def parse_structured_criteria(
        self, 
        criteria: List[Dict[str, Any]]
    ) -> Tuple[List[ValidationScenario], List[str]]:
        """
        Parse structured validation criteria into test scenarios.
        
        Args:
            criteria: List of structured validation criteria
            
        Returns:
            Tuple of (parsed scenarios, validation errors)
        """
        scenarios = []
        errors = []
        
        for i, criterion in enumerate(criteria):
            try:
                scenario = self._parse_single_criterion(criterion, i)
                if scenario:
                    scenarios.append(scenario)
            except Exception as e:
                error_msg = f"Error parsing criterion {i}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        return scenarios, errors
    
    def generate_test_outputs(
        self, 
        scenarios: List[ValidationScenario]
    ) -> Dict[str, Any]:
        """
        Generate multiple test output formats from validation scenarios.
        
        Args:
            scenarios: List of validation scenarios
            
        Returns:
            Dictionary with different test format outputs
        """
        outputs = {
            "natural_language": self._generate_natural_language_tests(scenarios),
            "rego_assertions": self._generate_rego_tests(scenarios),
            "smt_constraints": self._generate_smt_tests(scenarios),
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "total_scenarios": len(scenarios),
                "parser_version": "1.0.0"
            }
        }
        
        return outputs
    
    def lint_criteria(self, criteria: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Lint validation criteria for quality and completeness.
        
        Args:
            criteria: List of validation criteria to lint
            
        Returns:
            Linting report with issues and recommendations
        """
        return self.linter.lint_criteria(criteria)
    
    def _parse_single_criterion(self, criterion: Dict[str, Any], index: int) -> Optional[ValidationScenario]:
        """
        Parse a single validation criterion into a scenario.
        
        Args:
            criterion: Single validation criterion dictionary
            index: Index for generating unique IDs
            
        Returns:
            ValidationScenario or None if parsing fails
        """
        # Validate required fields
        required_fields = ['given', 'when', 'then']
        if not all(field in criterion for field in required_fields):
            raise ValueError(f"Missing required fields. Required: {required_fields}")
        
        # Generate scenario ID
        scenario_id = criterion.get('id', f"scenario_{index:03d}")
        
        # Extract and clean fields
        given = self._clean_text(criterion['given'])
        when = self._clean_text(criterion['when'])
        then = self._clean_text(criterion['then'])
        
        # Extract tags
        tags = criterion.get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        
        # Determine priority
        priority = criterion.get('priority', 'medium').lower()
        if priority not in ['low', 'medium', 'high', 'critical']:
            priority = 'medium'
        
        return ValidationScenario(
            id=scenario_id,
            given=given,
            when=when,
            then=then,
            tags=tags,
            priority=priority,
            metadata=criterion.get('metadata', {})
        )
    
    def _generate_natural_language_tests(self, scenarios: List[ValidationScenario]) -> List[str]:
        """Generate natural language test descriptions."""
        tests = []
        
        for scenario in scenarios:
            test_description = (
                f"Test {scenario.id}: "
                f"Given {scenario.given}, "
                f"when {scenario.when}, "
                f"then {scenario.then}."
            )
            tests.append(test_description)
        
        return tests
    
    def _generate_rego_tests(self, scenarios: List[ValidationScenario]) -> List[str]:
        """Generate Rego test assertions."""
        rego_tests = []
        
        for scenario in scenarios:
            # Simple Rego test template
            rego_test = f"""
# Test: {scenario.id}
# {scenario.given}
test_{scenario.id.replace('-', '_')} {{
    # Given: {scenario.given}
    # When: {scenario.when}
    # Then: {scenario.then}
    
    # TODO: Implement specific Rego logic for this scenario
    # This is a template that needs to be customized
    true  # Placeholder
}}
""".strip()
            rego_tests.append(rego_test)
        
        return rego_tests
    
    def _generate_smt_tests(self, scenarios: List[ValidationScenario]) -> List[str]:
        """Generate SMT-LIB constraint templates."""
        smt_tests = []
        
        for scenario in scenarios:
            # Simple SMT-LIB template
            smt_test = f"""
; Test: {scenario.id}
; Given: {scenario.given}
; When: {scenario.when}
; Then: {scenario.then}

; TODO: Define specific SMT constraints for this scenario
; This is a template that needs to be customized
(assert true)  ; Placeholder
""".strip()
            smt_tests.append(smt_test)
        
        return smt_tests
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common artifacts
        text = re.sub(r'[^\w\s\-.,;:()[\]{}]', '', text)
        
        return text
    
    def _load_scenario_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for scenario extraction."""
        return {
            'given_patterns': [
                r'given\s+(.+?)(?:\s+when|\s+,|$)',
                r'assuming\s+(.+?)(?:\s+when|\s+,|$)',
                r'if\s+(.+?)(?:\s+then|\s+,|$)'
            ],
            'when_patterns': [
                r'when\s+(.+?)(?:\s+then|\s+,|$)',
                r'if\s+(.+?)(?:\s+then|\s+,|$)',
                r'upon\s+(.+?)(?:\s+then|\s+,|$)'
            ],
            'then_patterns': [
                r'then\s+(.+?)(?:\s+and|\s+,|$)',
                r'should\s+(.+?)(?:\s+and|\s+,|$)',
                r'must\s+(.+?)(?:\s+and|\s+,|$)'
            ]
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the parser."""
        return {
            "max_scenarios_per_principle": 10,
            "default_priority": "medium",
            "enable_linting": True,
            "output_formats": ["natural_language", "rego_assertions", "smt_constraints"]
        }


class ValidationLinter:
    """Linter for validation criteria quality assessment."""
    
    def __init__(self):
        """Initialize the validation linter."""
        self.rules = self._load_linting_rules()
    
    def lint_criteria(self, criteria: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Lint validation criteria for quality and completeness.
        
        Args:
            criteria: List of validation criteria to lint
            
        Returns:
            Linting report with issues and recommendations
        """
        issues = []
        warnings = []
        recommendations = []
        
        for i, criterion in enumerate(criteria):
            criterion_issues = self._lint_single_criterion(criterion, i)
            issues.extend(criterion_issues['errors'])
            warnings.extend(criterion_issues['warnings'])
            recommendations.extend(criterion_issues['recommendations'])
        
        # Calculate quality score
        total_checks = len(criteria) * len(self.rules)
        total_issues = len(issues) + len(warnings)
        quality_score = max(0.0, 1.0 - (total_issues / max(total_checks, 1)))
        
        return {
            "quality_score": quality_score,
            "total_criteria": len(criteria),
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "lint_timestamp": datetime.now().isoformat()
        }
    
    def _lint_single_criterion(self, criterion: Dict[str, Any], index: int) -> Dict[str, List[str]]:
        """Lint a single validation criterion."""
        issues = {"errors": [], "warnings": [], "recommendations": []}
        
        # Check required fields
        required_fields = ['given', 'when', 'then']
        for field in required_fields:
            if field not in criterion or not criterion[field]:
                issues["errors"].append(f"Criterion {index}: Missing required field '{field}'")
        
        # Check field quality
        for field in required_fields:
            if field in criterion:
                text = criterion[field]
                if len(text) < 10:
                    issues["warnings"].append(f"Criterion {index}: Field '{field}' is very short")
                if len(text) > 200:
                    issues["warnings"].append(f"Criterion {index}: Field '{field}' is very long")
        
        # Check for vague language
        vague_terms = ['appropriate', 'reasonable', 'sufficient', 'proper']
        for field in required_fields:
            if field in criterion:
                text = criterion[field].lower()
                for term in vague_terms:
                    if term in text:
                        issues["recommendations"].append(
                            f"Criterion {index}: Consider replacing vague term '{term}' in '{field}'"
                        )
        
        return issues
    
    def _load_linting_rules(self) -> List[Dict[str, Any]]:
        """Load linting rules for validation criteria."""
        return [
            {"name": "required_fields", "severity": "error"},
            {"name": "field_length", "severity": "warning"},
            {"name": "vague_language", "severity": "recommendation"},
            {"name": "completeness", "severity": "warning"},
            {"name": "clarity", "severity": "recommendation"}
        ]
