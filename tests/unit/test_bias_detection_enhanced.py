"""
Enhanced Bias Detection Tests for ACGS-PGP Phase 3
Tests the improved bias detection implementation with HuggingFace Fairness Indicators
"""

import pytest
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Import the enhanced bias detector
import sys
sys.path.append('src/backend/fv_service')

from src.backend.fv_service.app.core.bias_detector import BiasDetector, FAIRLEARN_AVAILABLE
from src.backend.fv_service.app.schemas import (
    BiasDetectionRequest, BiasDetectionResult, BiasMetric, PolicyRule
)


class TestEnhancedBiasDetection:
    """Test suite for enhanced bias detection with fairlearn integration."""
    
    @pytest.fixture
    def bias_detector(self):
        """Create a BiasDetector instance for testing."""
        return BiasDetector()
    
    @pytest.fixture
    def test_fixtures(self):
        """Load test fixtures with known bias characteristics."""
        fixtures_path = Path("data/test_bias_detection_fixtures.json")
        if fixtures_path.exists():
            with open(fixtures_path, 'r') as f:
                return json.load(f)
        else:
            # Fallback minimal fixtures if file doesn't exist
            return {
                "test_bias_detection_scenarios": [
                    {
                        "scenario_id": "simple_bias_test",
                        "policy_rule": {
                            "id": "test_rule_1",
                            "rule_content": "allow { input.user.gender == \"male\" }",
                            "rule_type": "access_control"
                        },
                        "protected_attributes": ["gender"],
                        "dataset": [
                            {"user_id": 1, "gender": "male", "score": 85},
                            {"user_id": 2, "gender": "female", "score": 87}
                        ],
                        "expected_bias_detected": True,
                        "bias_type": "gender_discrimination"
                    }
                ],
                "bias_metrics": [
                    {
                        "metric_id": "demographic_parity",
                        "metric_type": "statistical",
                        "threshold": 0.1
                    }
                ]
            }
    
    @pytest.mark.asyncio
    async def test_fairlearn_integration_available(self, bias_detector):
        """Test that fairlearn integration is properly detected."""
        # This test checks if fairlearn is available and properly imported
        assert isinstance(FAIRLEARN_AVAILABLE, bool)
        if FAIRLEARN_AVAILABLE:
            print("✅ Fairlearn is available - using real bias detection")
        else:
            print("⚠️  Fairlearn not available - using heuristic fallback")
    
    @pytest.mark.asyncio
    async def test_demographic_parity_violation(self, bias_detector, test_fixtures):
        """Test detection of demographic parity violations."""
        scenario = next(
            s for s in test_fixtures["test_bias_detection_scenarios"] 
            if s["scenario_id"] == "demographic_parity_violation"
        )
        
        # Create policy rule from test fixture
        policy_rule = PolicyRule(
            id=scenario["policy_rule"]["id"],
            rule_content=scenario["policy_rule"]["rule_content"],
            rule_type=scenario["policy_rule"]["rule_type"]
        )
        
        # Create bias metric
        bias_metric = BiasMetric(
            metric_id="demographic_parity",
            metric_type="statistical",
            threshold=0.1
        )
        
        # Create bias detection request
        request = BiasDetectionRequest(
            policy_rule_ids=[policy_rule.id],
            bias_metrics=[bias_metric],
            protected_attributes=scenario["protected_attributes"],
            dataset=scenario["dataset"]
        )
        
        # Run bias detection
        response = await bias_detector.detect_bias(request, [policy_rule])
        
        # Validate results
        assert len(response.results) > 0
        result = response.results[0]
        
        # Check if bias was detected as expected
        if scenario["expected_bias_detected"]:
            assert result.bias_detected, f"Expected bias to be detected for scenario {scenario['scenario_id']}"
            assert result.bias_score > 0.1, f"Expected bias score > 0.1, got {result.bias_score}"
        
        # Check bias score is within expected range
        expected_range = scenario.get("expected_bias_score_range", [0.0, 1.0])
        assert expected_range[0] <= result.bias_score <= expected_range[1], \
            f"Bias score {result.bias_score} not in expected range {expected_range}"
        
        print(f"✅ Demographic parity test passed: bias_detected={result.bias_detected}, score={result.bias_score:.3f}")
    
    @pytest.mark.asyncio
    async def test_fair_policy_rule(self, bias_detector, test_fixtures):
        """Test that fair policy rules are correctly identified as unbiased."""
        scenario = next(
            s for s in test_fixtures["test_bias_detection_scenarios"] 
            if s["scenario_id"] == "fair_policy_rule"
        )
        
        policy_rule = PolicyRule(
            id=scenario["policy_rule"]["id"],
            rule_content=scenario["policy_rule"]["rule_content"],
            rule_type=scenario["policy_rule"]["rule_type"]
        )
        
        bias_metric = BiasMetric(
            metric_id="demographic_parity",
            metric_type="statistical",
            threshold=0.1
        )
        
        request = BiasDetectionRequest(
            policy_rule_ids=[policy_rule.id],
            bias_metrics=[bias_metric],
            protected_attributes=scenario["protected_attributes"],
            dataset=scenario["dataset"]
        )
        
        response = await bias_detector.detect_bias(request, [policy_rule])
        result = response.results[0]
        
        # Fair rule should have low bias score
        assert result.bias_score <= 0.2, f"Fair rule should have low bias score, got {result.bias_score}"
        
        print(f"✅ Fair policy test passed: bias_detected={result.bias_detected}, score={result.bias_score:.3f}")
    
    @pytest.mark.asyncio
    async def test_heuristic_fallback(self, bias_detector):
        """Test heuristic bias detection when fairlearn is not available or dataset is small."""
        policy_rule = PolicyRule(
            id="heuristic_test",
            rule_content="deny { input.user.race == \"minority\"; input.action == \"hire\" }",
            rule_type="discriminatory_rule"
        )
        
        bias_metric = BiasMetric(
            metric_id="heuristic_bias",
            metric_type="statistical",
            threshold=0.1
        )
        
        # Use small dataset to force heuristic fallback
        small_dataset = [
            {"user_id": 1, "race": "minority", "qualifications": "high"},
            {"user_id": 2, "race": "majority", "qualifications": "medium"}
        ]
        
        request = BiasDetectionRequest(
            policy_rule_ids=[policy_rule.id],
            bias_metrics=[bias_metric],
            protected_attributes=["race"],
            dataset=small_dataset
        )
        
        response = await bias_detector.detect_bias(request, [policy_rule])
        result = response.results[0]
        
        # Should detect bias due to explicit discriminatory language
        assert result.bias_detected, "Heuristic method should detect obvious bias"
        assert result.bias_score > 0.2, f"Expected high bias score for discriminatory rule, got {result.bias_score}"
        assert "race" in result.explanation.lower() or "minority" in result.explanation.lower()
        
        print(f"✅ Heuristic fallback test passed: bias_detected={result.bias_detected}, score={result.bias_score:.3f}")
    
    @pytest.mark.asyncio
    async def test_multiple_metrics(self, bias_detector):
        """Test bias detection with multiple metrics."""
        policy_rule = PolicyRule(
            id="multi_metric_test",
            rule_content="exclude { input.user.gender == \"female\"; input.user.age > 40 }",
            rule_type="multi_bias_rule"
        )
        
        metrics = [
            BiasMetric(metric_id="statistical", metric_type="statistical", threshold=0.1),
            BiasMetric(metric_id="embedding", metric_type="embedding", threshold=0.15),
            BiasMetric(metric_id="llm_review", metric_type="llm_review", threshold=0.2)
        ]
        
        dataset = [
            {"user_id": i, "gender": "female" if i % 2 == 0 else "male", "age": 30 + i}
            for i in range(20)
        ]
        
        request = BiasDetectionRequest(
            policy_rule_ids=[policy_rule.id],
            bias_metrics=metrics,
            protected_attributes=["gender", "age"],
            dataset=dataset
        )
        
        response = await bias_detector.detect_bias(request, [policy_rule])
        
        # Should have results for all metrics
        assert len(response.results) == len(metrics)
        
        # At least one metric should detect bias
        bias_detected_count = sum(1 for r in response.results if r.bias_detected)
        assert bias_detected_count > 0, "At least one metric should detect bias"
        
        print(f"✅ Multiple metrics test passed: {bias_detected_count}/{len(metrics)} metrics detected bias")
    
    @pytest.mark.asyncio
    async def test_bias_recommendations(self, bias_detector):
        """Test that appropriate recommendations are generated for biased rules."""
        policy_rule = PolicyRule(
            id="recommendation_test",
            rule_content="prefer { input.applicant.ethnicity == \"majority_group\" }",
            rule_type="preference_rule"
        )
        
        bias_metric = BiasMetric(
            metric_id="recommendation_test",
            metric_type="statistical",
            threshold=0.1
        )
        
        dataset = [{"applicant_id": i, "ethnicity": "majority_group" if i < 15 else "minority_group"} for i in range(20)]
        
        request = BiasDetectionRequest(
            policy_rule_ids=[policy_rule.id],
            bias_metrics=[bias_metric],
            protected_attributes=["ethnicity"],
            dataset=dataset
        )
        
        response = await bias_detector.detect_bias(request, [policy_rule])
        
        # Check that recommendations are provided
        assert len(response.recommendations) > 0, "Recommendations should be provided for biased rules"
        assert response.human_review_required, "Human review should be required for biased rules"
        
        # Check for specific recommendation types
        recommendations_text = " ".join(response.recommendations).lower()
        assert any(keyword in recommendations_text for keyword in ["review", "rewrite", "monitor", "test"])
        
        print(f"✅ Recommendations test passed: {len(response.recommendations)} recommendations generated")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
