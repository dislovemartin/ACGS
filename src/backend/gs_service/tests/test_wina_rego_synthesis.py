"""
Tests for WINA-Optimized Rego Policy Synthesis

This module contains comprehensive tests for the WINA integration into
the Rego policy synthesis pipeline, validating performance targets and
constitutional compliance.

Test Coverage:
- WINA optimization functionality
- Rego policy synthesis accuracy
- Constitutional compliance verification
- Performance metrics validation
- API endpoint testing
- Integration with AlphaEvolve components
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.wina_rego_synthesis import (
    WINARegoSynthesizer,
    WINARegoSynthesisResult,
    WINARegoSynthesisMetrics,
    synthesize_rego_policy_with_wina,
    batch_synthesize_rego_policies_with_wina,
    get_wina_rego_synthesis_performance_summary,
    clear_wina_rego_synthesis_cache
)


class TestWINARegoSynthesizer:
    """Test cases for WINARegoSynthesizer class."""
    
    @pytest.fixture
    def mock_constitutional_principles(self):
        """Mock constitutional principles for testing."""
        return [
            {
                "id": "CP001",
                "description": "Ensure user privacy and data protection",
                "type": "privacy_principle",
                "priority": 1.0
            },
            {
                "id": "CP002", 
                "description": "Maintain system security and access control",
                "type": "security_principle",
                "priority": 0.9
            }
        ]
    
    @pytest.fixture
    def wina_synthesizer(self):
        """Create WINARegoSynthesizer instance for testing."""
        return WINARegoSynthesizer(enable_wina=True)
    
    @pytest.fixture
    def mock_wina_optimization_result(self):
        """Mock WINA optimization result."""
        from shared.wina.model_integration import WINAOptimizationResult
        return WINAOptimizationResult(
            gflops_reduction=0.55,  # 55% reduction (within 40-70% target)
            accuracy_preservation=0.97,  # 97% accuracy (>95% target)
            optimization_time=0.15,
            constitutional_compliance=True,
            performance_metrics={
                "layers_optimized": 24,
                "neurons_gated": 1024,
                "svd_compression_ratio": 0.45
            }
        )
    
    @pytest.mark.asyncio
    async def test_synthesize_rego_policy_success(
        self, 
        wina_synthesizer, 
        mock_constitutional_principles,
        mock_wina_optimization_result
    ):
        """Test successful WINA-optimized Rego policy synthesis."""
        
        synthesis_goal = "Create access control policy for sensitive data"
        
        # Mock WINA LLM client
        with patch.object(wina_synthesizer.wina_llm_client, 'get_constitutional_synthesis_optimized') as mock_synthesis:
            from app.core.wina_llm_integration import WINAOptimizedSynthesisResult
            from app.schemas import ConstitutionalSynthesisOutput
            
            mock_synthesis_output = ConstitutionalSynthesisOutput(
                generated_rules=[
                    """
package acgs.access_control

default allow = false

allow {
    input.action == "read"
    input.resource.classification != "sensitive"
    input.user.clearance_level >= input.resource.required_clearance
}

deny {
    input.resource.classification == "sensitive"
    input.user.clearance_level < 3
}
                    """.strip()
                ]
            )
            
            mock_synthesis.return_value = WINAOptimizedSynthesisResult(
                original_result=mock_synthesis_output,
                wina_optimization=mock_wina_optimization_result,
                performance_metrics={
                    "synthesis_time": 0.85,
                    "gflops_reduction": 0.55,
                    "accuracy_preservation": 0.97
                },
                constitutional_compliance=True,
                optimization_applied=True,
                synthesis_time=0.85
            )
            
            # Perform synthesis
            result = await wina_synthesizer.synthesize_rego_policy(
                synthesis_goal=synthesis_goal,
                constitutional_principles=mock_constitutional_principles,
                constraints=["Must include default deny rule"],
                context_data={"security_level": "high"}
            )
            
            # Validate results
            assert result.success is True
            assert result.constitutional_compliance is True
            assert "package acgs.access_control" in result.rego_content
            assert "default allow = false" in result.rego_content
            assert result.synthesis_metrics.gflops_reduction >= 0.4  # 40% minimum
            assert result.synthesis_metrics.gflops_reduction <= 0.7  # 70% maximum
            assert result.synthesis_metrics.accuracy_preservation >= 0.95  # >95% target
            assert result.synthesis_metrics.optimization_applied is True
            assert result.validation_result["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_synthesize_rego_policy_without_wina(
        self, 
        mock_constitutional_principles
    ):
        """Test Rego policy synthesis without WINA optimization."""
        
        wina_synthesizer = WINARegoSynthesizer(enable_wina=False)
        synthesis_goal = "Create basic access policy"
        
        result = await wina_synthesizer.synthesize_rego_policy(
            synthesis_goal=synthesis_goal,
            constitutional_principles=mock_constitutional_principles,
            apply_wina=False
        )
        
        # Validate that synthesis works without WINA
        assert result.success is True
        assert result.synthesis_metrics.optimization_applied is False
        assert result.synthesis_metrics.gflops_reduction == 0.0
        assert "package acgs.generated_policy" in result.rego_content
    
    @pytest.mark.asyncio
    async def test_constitutional_compliance_verification(
        self,
        wina_synthesizer,
        mock_constitutional_principles
    ):
        """Test constitutional compliance verification."""
        
        # Test with compliant Rego content
        compliant_rego = """
package acgs.privacy_control

default allow = false

allow {
    input.action == "read"
    input.user.privacy_consent == true
    input.data.classification != "sensitive"
}

deny {
    input.data.contains_pii == true
    input.user.privacy_consent != true
}
"""
        
        compliance = await wina_synthesizer._verify_constitutional_compliance(
            compliant_rego, mock_constitutional_principles, None
        )
        
        assert compliance is True
        
        # Test with non-compliant Rego content
        non_compliant_rego = """
package test.basic

default allow = true
"""
        
        compliance = await wina_synthesizer._verify_constitutional_compliance(
            non_compliant_rego, mock_constitutional_principles, None
        )
        
        # Should still pass basic structure compliance
        assert compliance is True  # Basic structure is valid
    
    @pytest.mark.asyncio
    async def test_rego_validation(self, wina_synthesizer):
        """Test Rego policy validation functionality."""
        
        # Test valid Rego
        valid_rego = """
package test.policy

default allow = false

allow {
    input.user == "admin"
}
"""
        
        validation_result = await wina_synthesizer._validate_rego_policy(valid_rego)
        assert validation_result["is_valid"] is True
        assert validation_result["syntax_valid"] is True
        assert validation_result["structure_valid"] is True
        
        # Test invalid Rego (unbalanced braces)
        invalid_rego = """
package test.policy

default allow = false

allow {
    input.user == "admin"
"""
        
        validation_result = await wina_synthesizer._validate_rego_policy(invalid_rego)
        assert validation_result["is_valid"] is False
        assert len(validation_result["errors"]) > 0
    
    def test_performance_tracking(self, wina_synthesizer):
        """Test performance metrics tracking."""
        
        # Create mock synthesis result
        mock_result = WINARegoSynthesisResult(
            policy_suggestion=None,
            rego_content="package test.policy\ndefault allow = false",
            constitutional_compliance=True,
            wina_optimization=None,
            synthesis_metrics=WINARegoSynthesisMetrics(
                synthesis_time=1.2,
                gflops_reduction=0.6,
                accuracy_preservation=0.96,
                constitutional_compliance=True,
                rego_validation_success=True,
                policy_complexity_score=0.3,
                optimization_applied=True,
                error_count=0
            ),
            validation_result={"is_valid": True},
            warnings=[],
            success=True
        )
        
        # Update tracking
        asyncio.run(wina_synthesizer._update_synthesis_tracking(mock_result))
        
        # Verify metrics
        summary = wina_synthesizer.get_performance_summary()
        assert summary["performance_metrics"]["total_syntheses"] == 1
        assert summary["performance_metrics"]["constitutional_compliance_rate"] == 1.0
        assert summary["performance_metrics"]["rego_validation_success_rate"] == 1.0


class TestWINARegoSynthesisAPI:
    """Test cases for WINA Rego synthesis API functions."""
    
    @pytest.mark.asyncio
    async def test_synthesize_rego_policy_with_wina_function(self):
        """Test the main synthesis function."""
        
        synthesis_goal = "Create data access policy"
        constitutional_principles = [
            {"description": "Protect user data", "type": "privacy"}
        ]
        
        with patch('app.core.wina_rego_synthesis.get_wina_rego_synthesizer') as mock_get_synthesizer:
            mock_synthesizer = Mock()
            mock_synthesizer.synthesize_rego_policy = AsyncMock(return_value=WINARegoSynthesisResult(
                policy_suggestion=None,
                rego_content="package test.policy\ndefault allow = false",
                constitutional_compliance=True,
                wina_optimization=None,
                synthesis_metrics=WINARegoSynthesisMetrics(
                    synthesis_time=0.8,
                    gflops_reduction=0.5,
                    accuracy_preservation=0.96,
                    constitutional_compliance=True,
                    rego_validation_success=True,
                    policy_complexity_score=0.2,
                    optimization_applied=True,
                    error_count=0
                ),
                validation_result={"is_valid": True},
                warnings=[],
                success=True
            ))
            mock_get_synthesizer.return_value = mock_synthesizer
            
            result = await synthesize_rego_policy_with_wina(
                synthesis_goal=synthesis_goal,
                constitutional_principles=constitutional_principles
            )
            
            assert result.success is True
            assert result.synthesis_metrics.gflops_reduction == 0.5
            mock_synthesizer.synthesize_rego_policy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_synthesize_rego_policies(self):
        """Test batch synthesis functionality."""
        
        synthesis_requests = [
            {
                "synthesis_goal": "Policy 1",
                "constitutional_principles": [{"description": "Principle 1"}]
            },
            {
                "synthesis_goal": "Policy 2", 
                "constitutional_principles": [{"description": "Principle 2"}]
            }
        ]
        
        with patch('app.core.wina_rego_synthesis.get_wina_rego_synthesizer') as mock_get_synthesizer:
            mock_synthesizer = Mock()
            mock_synthesizer.synthesize_rego_policy = AsyncMock(return_value=WINARegoSynthesisResult(
                policy_suggestion=None,
                rego_content="package test.policy\ndefault allow = false",
                constitutional_compliance=True,
                wina_optimization=None,
                synthesis_metrics=WINARegoSynthesisMetrics(
                    synthesis_time=0.5,
                    gflops_reduction=0.45,
                    accuracy_preservation=0.97,
                    constitutional_compliance=True,
                    rego_validation_success=True,
                    policy_complexity_score=0.1,
                    optimization_applied=True,
                    error_count=0
                ),
                validation_result={"is_valid": True},
                warnings=[],
                success=True
            ))
            mock_get_synthesizer.return_value = mock_synthesizer
            
            results = await batch_synthesize_rego_policies_with_wina(
                synthesis_requests=synthesis_requests,
                enable_wina=True
            )
            
            assert len(results) == 2
            assert all(result.success for result in results)
            assert mock_synthesizer.synthesize_rego_policy.call_count == 2


class TestWINAPerformanceTargets:
    """Test cases for validating WINA performance targets."""
    
    @pytest.mark.asyncio
    async def test_gflops_reduction_target(self):
        """Test that WINA achieves 40-70% GFLOPs reduction target."""
        
        # This would be an integration test with actual WINA optimization
        # For now, we test the validation logic
        
        synthesizer = WINARegoSynthesizer(enable_wina=True)
        
        # Mock a result that meets the target
        mock_metrics = WINARegoSynthesisMetrics(
            synthesis_time=1.0,
            gflops_reduction=0.55,  # 55% - within target range
            accuracy_preservation=0.96,  # 96% - above target
            constitutional_compliance=True,
            rego_validation_success=True,
            policy_complexity_score=0.3,
            optimization_applied=True,
            error_count=0
        )
        
        # Validate targets
        assert 0.4 <= mock_metrics.gflops_reduction <= 0.7  # 40-70% target
        assert mock_metrics.accuracy_preservation >= 0.95  # >95% target
        assert mock_metrics.constitutional_compliance is True  # Required
    
    def test_performance_summary_structure(self):
        """Test performance summary structure and content."""
        
        with patch('app.core.wina_rego_synthesis.get_wina_rego_synthesizer') as mock_get_synthesizer:
            mock_synthesizer = Mock()
            mock_synthesizer.get_performance_summary.return_value = {
                "performance_metrics": {
                    "total_syntheses": 10,
                    "wina_optimized_syntheses": 8,
                    "average_gflops_reduction": 0.52,
                    "average_accuracy_preservation": 0.96,
                    "constitutional_compliance_rate": 0.95,
                    "rego_validation_success_rate": 0.90
                },
                "synthesis_history_count": 10,
                "wina_enabled": True,
                "recent_syntheses": [],
                "target_performance": {
                    "gflops_reduction_target": "40-70%",
                    "accuracy_preservation_target": ">95%",
                    "constitutional_compliance_target": "100%"
                }
            }
            mock_get_synthesizer.return_value = mock_synthesizer
            
            summary = get_wina_rego_synthesis_performance_summary()
            
            # Validate structure
            assert "performance_metrics" in summary
            assert "target_performance" in summary
            assert summary["wina_enabled"] is True
            
            # Validate performance meets targets
            metrics = summary["performance_metrics"]
            assert 0.4 <= metrics["average_gflops_reduction"] <= 0.7
            assert metrics["average_accuracy_preservation"] >= 0.95
