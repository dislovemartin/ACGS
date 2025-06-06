"""
test_qec_enhancements.py

Comprehensive test suite for QEC-inspired enhancements to AlphaEvolve-ACGS.
Tests constitutional distance calculation, error prediction, recovery strategies,
and integration with existing GS service components.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

# Import QEC enhancement components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'alphaevolve_gs_engine', 'src'))

from alphaevolve_gs_engine.services.qec_enhancement import (
    ConstitutionalDistanceCalculator,
    ValidationDSLParser,
    ErrorPredictionModel,
    RecoveryStrategyDispatcher,
    FailureType,
    SynthesisAttemptLog,
    RecoveryStrategy
)
from alphaevolve_gs_engine.core.constitutional_principle import ConstitutionalPrinciple

# Mock GS service components for testing
class MockLLMInterpretationInput:
    def __init__(self, principle_text: str, context_information: Dict[str, Any], interpretation_type: str):
        self.principle_text = principle_text
        self.context_information = context_information
        self.interpretation_type = interpretation_type

    def dict(self):
        return {
            "principle_text": self.principle_text,
            "context_information": self.context_information,
            "interpretation_type": self.interpretation_type
        }

class MockQECSynthesisInput:
    def __init__(self, principle, context, llm_input, qec_metadata=None):
        self.principle = principle
        self.context = context
        self.llm_input = llm_input
        self.qec_metadata = qec_metadata


class TestConstitutionalDistanceCalculator:
    """Test suite for Constitutional Distance Calculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = ConstitutionalDistanceCalculator()
        
        # Create test principles with varying characteristics
        self.high_quality_principle = ConstitutionalPrinciple(
            principle_id="test_high_quality",
            name="High Quality Principle",
            description="AI systems must ensure data privacy through encryption and access controls with specific technical requirements.",
            category="Safety",
            policy_code="package test.high_quality\ndefault allow = false\nallow { input.encrypted == true }",
            validation_criteria_structured=[
                {
                    "id": "privacy_check",
                    "given": "user data is processed",
                    "when": "encryption is enabled",
                    "then": "data must be encrypted with AES-256",
                    "tags": ["privacy", "encryption"]
                }
            ]
        )
        
        self.low_quality_principle = ConstitutionalPrinciple(
            principle_id="test_low_quality",
            name="Vague Principle",
            description="AI should be appropriate and reasonable when possible.",
            category="General",
            policy_code="package test.low_quality\n" "default allow = false\n" "allow { input.valid }"
        )
    
    def test_calculate_score_high_quality(self):
        """Test distance calculation for high-quality principle."""
        score = self.calculator.calculate_score(self.high_quality_principle)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.7  # High-quality principle should have high score
        assert self.high_quality_principle.distance_score == score
        assert self.high_quality_principle.score_updated_at is not None
    
    def test_calculate_score_low_quality(self):
        """Test distance calculation for low-quality principle."""
        score = self.calculator.calculate_score(self.low_quality_principle)
        
        assert 0.0 <= score <= 1.0
        assert score < 0.5  # Low-quality principle should have low score
    
    def test_detailed_metrics(self):
        """Test detailed metrics calculation."""
        metrics = self.calculator.calculate_detailed_metrics(self.high_quality_principle)
        
        assert hasattr(metrics, 'language_ambiguity')
        assert hasattr(metrics, 'criteria_formality')
        assert hasattr(metrics, 'synthesis_reliability')
        assert hasattr(metrics, 'composite_score')
        
        # High-quality principle should have low ambiguity
        assert metrics.language_ambiguity < 0.5
        # Should have high formality due to structured criteria
        assert metrics.criteria_formality > 0.5


class TestValidationDSLParser:
    """Test suite for Validation DSL Parser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ValidationDSLParser()
        
        self.test_criteria = [
            {
                "id": "test_scenario_1",
                "given": "user submits personal data",
                "when": "data processing is initiated",
                "then": "data must be encrypted before storage",
                "tags": ["privacy", "encryption"],
                "priority": "high"
            },
            {
                "given": "AI system makes a decision",
                "when": "decision affects user rights",
                "then": "explanation must be provided",
                "tags": ["transparency"]
            }
        ]
    
    def test_parse_structured_criteria(self):
        """Test parsing of structured validation criteria."""
        scenarios, errors = self.parser.parse_structured_criteria(self.test_criteria)
        
        assert len(scenarios) == 2
        assert len(errors) == 0
        
        # Check first scenario
        scenario1 = scenarios[0]
        assert scenario1.id == "test_scenario_1"
        assert scenario1.given == "user submits personal data"
        assert scenario1.priority == "high"
        assert "privacy" in scenario1.tags
    
    def test_generate_test_outputs(self):
        """Test generation of multiple test output formats."""
        scenarios, _ = self.parser.parse_structured_criteria(self.test_criteria)
        outputs = self.parser.generate_test_outputs(scenarios)
        
        assert "natural_language" in outputs
        assert "rego_assertions" in outputs
        assert "smt_constraints" in outputs
        assert "metadata" in outputs
        
        # Check natural language tests
        nl_tests = outputs["natural_language"]
        assert len(nl_tests) == 2
        assert "Given user submits personal data" in nl_tests[0]
    
    def test_lint_criteria(self):
        """Test linting of validation criteria."""
        lint_report = self.parser.lint_criteria(self.test_criteria)
        
        assert "quality_score" in lint_report
        assert "total_criteria" in lint_report
        assert "issues" in lint_report
        assert "warnings" in lint_report
        assert "recommendations" in lint_report
        
        assert lint_report["total_criteria"] == 2
        assert 0.0 <= lint_report["quality_score"] <= 1.0


class TestErrorPredictionModel:
    """Test suite for Error Prediction Model."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.predictor = ErrorPredictionModel()
        
        self.test_principle = ConstitutionalPrinciple(
            principle_id="test_prediction",
            name="Test Principle",
            description="AI systems should be appropriate and reasonable when making decisions that might affect users.",
            category="Fairness",
            policy_code="# Complex policy logic here"
        )
    
    def test_predict_synthesis_challenges(self):
        """Test prediction of synthesis challenges."""
        result = self.predictor.predict_synthesis_challenges(self.test_principle)
        
        assert result.principle_id == "test_prediction"
        assert isinstance(result.predicted_failures, dict)
        assert 0.0 <= result.overall_risk_score <= 1.0
        assert result.recommended_strategy in ["standard_synthesis", "enhanced_validation", "multi_model_consensus", "human_review_required"]
        assert 0.0 <= result.confidence <= 1.0
    
    def test_log_synthesis_attempt(self):
        """Test logging of synthesis attempts."""
        log_entry = SynthesisAttemptLog(
            attempt_id="test_attempt_1",
            principle_id="test_prediction",
            timestamp=datetime.now(),
            llm_model="gpt-4",
            prompt_template="standard",
            failure_type=FailureType.SEMANTIC_CONFLICT,
            error_details={"error": "Ambiguous principle language"},
            recovery_strategy="explicit_disambiguation",
            final_outcome="success"
        )
        
        initial_count = len(self.predictor.attempt_logs)
        self.predictor.log_synthesis_attempt(log_entry)
        
        assert len(self.predictor.attempt_logs) == initial_count + 1
        assert self.predictor.attempt_logs[-1] == log_entry
    
    def test_diagnose_failure(self):
        """Test failure diagnosis functionality."""
        log_entry = SynthesisAttemptLog(
            attempt_id="test_failure",
            principle_id="test_prediction",
            timestamp=datetime.now(),
            llm_model="gpt-4",
            prompt_template="standard",
            failure_type=FailureType.AMBIGUOUS_PRINCIPLE,
            error_details={"error": "Principle contains vague terms"},
            recovery_strategy=None,
            final_outcome="failed"
        )
        
        diagnosis = self.predictor.diagnose_failure(log_entry)
        
        assert "failure_type" in diagnosis
        assert "likely_causes" in diagnosis
        assert "recommendations" in diagnosis
        assert "similar_failures" in diagnosis
        
        assert diagnosis["failure_type"] == "ambiguous_principle"
        assert isinstance(diagnosis["recommendations"], list)


class TestRecoveryStrategyDispatcher:
    """Test suite for Recovery Strategy Dispatcher."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.dispatcher = RecoveryStrategyDispatcher()
    
    def test_get_recovery_strategy(self):
        """Test recovery strategy selection."""
        failure_log = SynthesisAttemptLog(
            attempt_id="test_recovery",
            principle_id="test_principle",
            timestamp=datetime.now(),
            llm_model="gpt-4",
            prompt_template="standard",
            failure_type=FailureType.SYNTAX_ERROR,
            error_details={"error": "Invalid syntax in generated policy"},
            recovery_strategy=None,
            final_outcome="failed"
        )
        
        strategy = self.dispatcher.get_recovery_strategy(failure_log, "test_principle")
        
        assert isinstance(strategy, RecoveryStrategy)
        # For syntax errors, should recommend simplified syntax
        assert strategy == RecoveryStrategy.SIMPLIFIED_SYNTAX_PROMPT
    
    def test_execute_recovery_strategy(self):
        """Test recovery strategy execution."""
        result = self.dispatcher.execute_recovery_strategy(
            RecoveryStrategy.SIMPLIFIED_SYNTAX_PROMPT,
            "test_principle",
            {"principle_text": "Test principle"},
            {"error": "Syntax error"}
        )
        
        assert hasattr(result, 'strategy_used')
        assert hasattr(result, 'success')
        assert hasattr(result, 'attempts_made')
        assert hasattr(result, 'total_time_seconds')
        
        assert result.strategy_used == RecoveryStrategy.SIMPLIFIED_SYNTAX_PROMPT
    
    def test_strategy_performance_tracking(self):
        """Test performance tracking for recovery strategies."""
        # Execute a few strategies
        for i in range(3):
            self.dispatcher.execute_recovery_strategy(
                RecoveryStrategy.SIMPLIFIED_SYNTAX_PROMPT,
                f"test_principle_{i}",
                {"principle_text": f"Test principle {i}"},
                {"error": "Test error"}
            )
        
        performance = self.dispatcher.get_strategy_performance()
        
        assert "simplified_syntax_prompt" in performance
        strategy_perf = performance["simplified_syntax_prompt"]
        assert "attempts" in strategy_perf
        assert "successes" in strategy_perf
        assert "success_rate" in strategy_perf
        assert strategy_perf["attempts"] >= 3


@pytest.mark.asyncio
class TestQECEnhancedSynthesizer:
    """Test suite for QEC-Enhanced Synthesizer integration."""

    async def setup_method(self):
        """Set up test fixtures."""
        # Skip synthesizer tests for now since they require full GS service integration
        pytest.skip("QEC Enhanced Synthesizer tests require full GS service integration")

        self.test_principle = ConstitutionalPrinciple(
            principle_id="test_synthesis",
            name="Test Synthesis Principle",
            description="AI systems must ensure fairness in decision-making processes.",
            category="Fairness",
            policy_code="package test.fairness\ndefault allow = true"
        )

        self.synthesis_input = MockQECSynthesisInput(
            principle=self.test_principle,
            context={"domain": "healthcare", "risk_level": "high"},
            llm_input=MockLLMInterpretationInput(
                principle_text="AI systems must ensure fairness in decision-making processes.",
                context_information={"domain": "healthcare"},
                interpretation_type="policy_synthesis"
            )
        )
    
    async def test_synthesize_with_qec(self):
        """Test QEC-enhanced synthesis process."""
        result = await self.synthesizer.synthesize_with_qec(self.synthesis_input)
        
        assert hasattr(result, 'llm_output')
        assert hasattr(result, 'reliability_metrics')
        assert hasattr(result, 'constitutional_distance')
        assert hasattr(result, 'error_predictions')
        assert hasattr(result, 'qec_metadata')
        assert hasattr(result, 'synthesis_success')
        assert hasattr(result, 'total_attempts')
        
        # Check QEC metadata
        assert "synthesis_strategy" in result.qec_metadata
        assert "attempts_made" in result.qec_metadata
        assert "total_synthesis_time_ms" in result.qec_metadata
    
    async def test_synthesis_statistics(self):
        """Test synthesis statistics tracking."""
        # Perform a synthesis
        await self.synthesizer.synthesize_with_qec(self.synthesis_input)
        
        stats = self.synthesizer.get_synthesis_statistics()
        
        assert "total_attempts" in stats
        assert "successful_syntheses" in stats
        assert "success_rate" in stats
        assert "qec_interventions" in stats
        assert "recovery_successes" in stats
        assert "recovery_success_rate" in stats
        assert "improvement_from_qec" in stats
        
        assert stats["total_attempts"] >= 1


class TestQECIntegration:
    """Integration tests for QEC enhancements with existing ACGS-PGP components."""
    
    def test_constitutional_principle_qec_fields(self):
        """Test that ConstitutionalPrinciple supports QEC enhancement fields."""
        principle = ConstitutionalPrinciple(
            principle_id="integration_test",
            name="Integration Test Principle",
            description="Test principle for QEC integration",
            category="Testing",
            policy_code="package test",
            validation_criteria_structured=[
                {
                    "id": "test_criterion",
                    "given": "test condition",
                    "when": "test action",
                    "then": "test outcome"
                }
            ],
            distance_score=0.75,
            error_prediction_metadata={"test": "metadata"},
            recovery_strategies=["simplified_syntax_prompt"]
        )
        
        assert principle.validation_criteria_structured is not None
        assert len(principle.validation_criteria_structured) == 1
        assert principle.distance_score == 0.75
        assert "test" in principle.error_prediction_metadata
        assert "simplified_syntax_prompt" in principle.recovery_strategies
    
    def test_principle_serialization_with_qec_fields(self):
        """Test serialization/deserialization of principles with QEC fields."""
        original_principle = ConstitutionalPrinciple(
            principle_id="serialization_test",
            name="Serialization Test",
            description="Test principle serialization",
            category="Testing",
            policy_code="package test",
            validation_criteria_structured=[{"id": "test", "given": "a", "when": "b", "then": "c"}],
            distance_score=0.8,
            error_prediction_metadata={"prediction": "data"},
            recovery_strategies=["strategy1", "strategy2"]
        )
        
        # Serialize to dict
        principle_dict = original_principle.to_dict()
        
        # Check QEC fields are included
        assert "validation_criteria_structured" in principle_dict
        assert "distance_score" in principle_dict
        assert "error_prediction_metadata" in principle_dict
        assert "recovery_strategies" in principle_dict
        
        # Deserialize from dict
        restored_principle = ConstitutionalPrinciple.from_dict(principle_dict)
        
        # Check QEC fields are restored
        assert restored_principle.validation_criteria_structured == original_principle.validation_criteria_structured
        assert restored_principle.distance_score == original_principle.distance_score
        assert restored_principle.error_prediction_metadata == original_principle.error_prediction_metadata
        assert restored_principle.recovery_strategies == original_principle.recovery_strategies


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
