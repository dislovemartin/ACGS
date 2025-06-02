"""
Integration Tests for WINA Rego Synthesis

This module contains integration tests to validate the WINA Rego synthesis
functionality works correctly with the existing ACGS-PGP infrastructure.
"""

import pytest
import asyncio
import sys
import os

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import Mock, patch, AsyncMock


class TestWINARegoIntegration:
    """Integration tests for WINA Rego synthesis."""
    
    @pytest.mark.asyncio
    async def test_wina_rego_synthesis_basic_functionality(self):
        """Test basic WINA Rego synthesis functionality."""
        
        # Mock the WINA components to avoid dependency issues
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', True):
            with patch('app.core.wina_rego_synthesis.load_wina_config_from_env') as mock_config:
                # Mock WINA configuration
                mock_wina_config = Mock()
                mock_wina_integration_config = Mock()
                mock_config.return_value = (mock_wina_config, mock_wina_integration_config)
                
                # Import after mocking
                from app.core.wina_rego_synthesis import WINARegoSynthesizer
                
                # Create synthesizer
                synthesizer = WINARegoSynthesizer(enable_wina=True)
                
                # Verify initialization
                assert synthesizer.enable_wina is True
                assert synthesizer.wina_config is not None
                assert synthesizer.wina_integration_config is not None
    
    @pytest.mark.asyncio
    async def test_wina_rego_synthesis_without_dependencies(self):
        """Test WINA Rego synthesis gracefully handles missing dependencies."""
        
        # Test with WINA not available
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', False):
            from app.core.wina_rego_synthesis import WINARegoSynthesizer
            
            # Create synthesizer without WINA
            synthesizer = WINARegoSynthesizer(enable_wina=True)
            
            # Should gracefully disable WINA
            assert synthesizer.enable_wina is False
    
    @pytest.mark.asyncio
    async def test_rego_policy_validation_basic(self):
        """Test basic Rego policy validation functionality."""
        
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', False):
            from app.core.wina_rego_synthesis import WINARegoSynthesizer
            
            synthesizer = WINARegoSynthesizer(enable_wina=False)
            
            # Test valid Rego policy
            valid_rego = """
package test.policy

default allow = false

allow {
    input.user == "admin"
    input.action == "read"
}
"""
            
            validation_result = await synthesizer._validate_rego_policy(valid_rego)
            
            # Should pass basic validation
            assert validation_result["syntax_valid"] is True
            assert validation_result["structure_valid"] is True
            assert validation_result["is_valid"] is True
            assert len(validation_result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_constitutional_compliance_verification(self):
        """Test constitutional compliance verification."""
        
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', False):
            from app.core.wina_rego_synthesis import WINARegoSynthesizer
            
            synthesizer = WINARegoSynthesizer(enable_wina=False)
            
            # Test with constitutional principles
            constitutional_principles = [
                {
                    "description": "Ensure user privacy and data protection",
                    "type": "privacy_principle"
                }
            ]
            
            # Test Rego policy that references privacy
            privacy_rego = """
package acgs.privacy_control

default allow = false

allow {
    input.action == "read"
    input.user.privacy_consent == true
    input.data.classification != "sensitive"
}
"""
            
            compliance = await synthesizer._verify_constitutional_compliance(
                privacy_rego, constitutional_principles, None
            )
            
            # Should pass compliance check
            assert compliance is True
    
    @pytest.mark.asyncio
    async def test_fallback_rego_generation(self):
        """Test fallback Rego policy generation."""
        
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', False):
            from app.core.wina_rego_synthesis import WINARegoSynthesizer
            
            synthesizer = WINARegoSynthesizer(enable_wina=False)
            
            synthesis_goal = "Create access control policy"
            
            # Generate fallback policy
            fallback_rego = synthesizer._generate_fallback_rego_policy(synthesis_goal)
            
            # Verify fallback policy structure
            assert "package acgs.generated_policy" in fallback_rego
            assert "default allow = false" in fallback_rego
            assert "default deny = false" in fallback_rego
            assert synthesis_goal in fallback_rego
    
    @pytest.mark.asyncio
    async def test_rego_format_enforcement(self):
        """Test Rego format enforcement functionality."""
        
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', False):
            from app.core.wina_rego_synthesis import WINARegoSynthesizer
            
            synthesizer = WINARegoSynthesizer(enable_wina=False)
            
            # Test content without package declaration
            content_without_package = """
allow {
    input.user == "admin"
}
"""
            
            formatted_content = synthesizer._ensure_rego_format(
                content_without_package, "test policy"
            )
            
            # Should add package declaration
            assert formatted_content.startswith("package acgs.generated_policy")
            assert "default allow = false" in formatted_content
            assert "default deny = false" in formatted_content
    
    @pytest.mark.asyncio
    async def test_performance_metrics_calculation(self):
        """Test performance metrics calculation."""
        
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', False):
            from app.core.wina_rego_synthesis import (
                WINARegoSynthesizer, 
                WINARegoSynthesisMetrics
            )
            
            synthesizer = WINARegoSynthesizer(enable_wina=False)
            
            # Mock synthesis result
            mock_wina_synthesis_result = Mock()
            mock_wina_synthesis_result.wina_optimization = None
            mock_wina_synthesis_result.original_result = Mock()
            mock_wina_synthesis_result.original_result.generated_rules = ["rule1", "rule2"]
            
            validation_result = {"is_valid": True, "errors": []}
            constitutional_compliance = True
            synthesis_time = 1.5
            
            # Calculate metrics
            metrics = synthesizer._calculate_synthesis_metrics(
                mock_wina_synthesis_result,
                synthesis_time,
                validation_result,
                constitutional_compliance
            )
            
            # Verify metrics structure
            assert isinstance(metrics, WINARegoSynthesisMetrics)
            assert metrics.synthesis_time == 1.5
            assert metrics.constitutional_compliance is True
            assert metrics.rego_validation_success is True
            assert metrics.error_count == 0
            assert metrics.optimization_applied is False
    
    def test_performance_summary_structure(self):
        """Test performance summary structure."""
        
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', False):
            from app.core.wina_rego_synthesis import WINARegoSynthesizer
            
            synthesizer = WINARegoSynthesizer(enable_wina=False)
            
            # Get performance summary
            summary = synthesizer.get_performance_summary()
            
            # Verify summary structure
            assert "performance_metrics" in summary
            assert "synthesis_history_count" in summary
            assert "wina_enabled" in summary
            assert "recent_syntheses" in summary
            assert "target_performance" in summary
            
            # Verify target performance values
            targets = summary["target_performance"]
            assert targets["gflops_reduction_target"] == "40-70%"
            assert targets["accuracy_preservation_target"] == ">95%"
            assert targets["constitutional_compliance_target"] == "100%"
    
    @pytest.mark.asyncio
    async def test_global_function_interfaces(self):
        """Test global function interfaces work correctly."""
        
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', False):
            # Test get_wina_rego_synthesizer function
            from app.core.wina_rego_synthesis import get_wina_rego_synthesizer
            
            synthesizer1 = get_wina_rego_synthesizer(enable_wina=False)
            synthesizer2 = get_wina_rego_synthesizer(enable_wina=False)
            
            # Should return the same instance (singleton pattern)
            assert synthesizer1 is synthesizer2
            
            # Test clear cache function
            from app.core.wina_rego_synthesis import clear_wina_rego_synthesis_cache
            
            # Should not raise an exception
            clear_wina_rego_synthesis_cache()
    
    @pytest.mark.asyncio
    async def test_api_integration_readiness(self):
        """Test that the implementation is ready for API integration."""
        
        with patch('app.core.wina_rego_synthesis.WINA_AVAILABLE', False):
            from app.core.wina_rego_synthesis import synthesize_rego_policy_with_wina
            
            # Mock the synthesizer to avoid complex dependencies
            with patch('app.core.wina_rego_synthesis.get_wina_rego_synthesizer') as mock_get_synthesizer:
                mock_synthesizer = Mock()
                mock_synthesizer.synthesize_rego_policy = AsyncMock()
                
                # Mock a successful result
                from app.core.wina_rego_synthesis import (
                    WINARegoSynthesisResult, 
                    WINARegoSynthesisMetrics
                )
                
                mock_result = WINARegoSynthesisResult(
                    policy_suggestion=None,
                    rego_content="package test.policy\ndefault allow = false",
                    constitutional_compliance=True,
                    wina_optimization=None,
                    synthesis_metrics=WINARegoSynthesisMetrics(
                        synthesis_time=1.0,
                        gflops_reduction=0.0,
                        accuracy_preservation=1.0,
                        constitutional_compliance=True,
                        rego_validation_success=True,
                        policy_complexity_score=0.1,
                        optimization_applied=False,
                        error_count=0
                    ),
                    validation_result={"is_valid": True},
                    warnings=[],
                    success=True
                )
                
                mock_synthesizer.synthesize_rego_policy.return_value = mock_result
                mock_get_synthesizer.return_value = mock_synthesizer
                
                # Test the main API function
                result = await synthesize_rego_policy_with_wina(
                    synthesis_goal="Test policy",
                    constitutional_principles=[{"description": "Test principle"}]
                )
                
                # Verify result structure
                assert result.success is True
                assert result.rego_content is not None
                assert result.constitutional_compliance is True
                assert result.synthesis_metrics is not None
                
                # Verify the synthesizer was called correctly
                mock_synthesizer.synthesize_rego_policy.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
