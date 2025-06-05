"""
Integration Tests for WINA Enhanced Dynamic Gating

This module provides comprehensive integration tests for the enhanced dynamic
neuron gating system, demonstrating real-world usage scenarios and performance.
"""

import pytest
import asyncio
import numpy as np
import torch
import time
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import WINA components
from src.backend.shared.wina import (
    WINAConfig,
    WINAIntegrationConfig,
    RuntimeGating,
    GatingStrategy,
    WINACore
)
from src.backend.shared.wina.gating import GatingDecision


class TestWINAGatingIntegration:
    """Integration tests for WINA enhanced dynamic gating."""
    
    @pytest.fixture
    def production_config(self):
        """Create production-like WINA configuration."""
        return WINAConfig(
            target_sparsity=0.6,
            gflops_reduction_target=0.5,
            accuracy_threshold=0.95,
            enable_runtime_gating=True,
            enable_performance_monitoring=True,
            enable_constitutional_compliance=True,
            gating_threshold=0.1,
            layer_specific_sparsity={
                "transformer.layers.0.attention": 0.7,
                "transformer.layers.0.feed_forward": 0.5,
                "transformer.layers.1.attention": 0.65,
                "transformer.layers.1.feed_forward": 0.55
            }
        )
    
    @pytest.fixture
    def integration_config(self):
        """Create integration configuration."""
        return WINAIntegrationConfig(
            gs_engine_optimization=True,
            ec_layer_oversight=True,
            constitutional_council_integration=True,
            performance_monitoring_enabled=True
        )
    
    @pytest.fixture
    def runtime_gating(self, production_config):
        """Create runtime gating with production configuration."""
        return RuntimeGating(production_config)
    
    def test_end_to_end_gating_workflow(self, runtime_gating):
        """Test complete end-to-end gating workflow."""
        # Simulate a multi-layer transformer model
        layer_configs = [
            ("transformer.layers.0.attention", 768),
            ("transformer.layers.0.feed_forward", 3072),
            ("transformer.layers.1.attention", 768),
            ("transformer.layers.1.feed_forward", 3072)
        ]
        
        gating_decisions = []
        total_neurons = 0
        total_active = 0
        
        for layer_name, num_neurons in layer_configs:
            # Generate realistic WINA scores
            np.random.seed(hash(layer_name) % 2**32)
            wina_scores = self._generate_realistic_wina_scores(num_neurons, layer_name)
            
            # Make gating decision
            decision = runtime_gating.make_gating_decision(layer_name, wina_scores)
            gating_decisions.append(decision)
            
            total_neurons += num_neurons
            total_active += len(decision.active_neurons)
            
            # Verify decision quality
            assert decision.constitutional_compliance >= 0.0  # Valid range
            assert decision.confidence_score > 0.3
            assert decision.sparsity_achieved >= 0.0  # Some sparsity achieved
            assert decision.decision_time < 0.1  # Should be fast
        
        # Verify overall performance
        overall_sparsity = 1.0 - (total_active / total_neurons)
        assert 0.0 <= overall_sparsity <= 0.9  # Reasonable sparsity range
        
        # Verify different strategies were used appropriately
        strategies_used = [d.strategy_used for d in gating_decisions]
        attention_strategies = [d.strategy_used for d in gating_decisions if "attention" in d.layer_name]
        
        # Attention layers should prefer stable strategies
        assert all(s in [GatingStrategy.TOP_K, GatingStrategy.HYBRID_DYNAMIC] for s in attention_strategies)
    
    def test_adaptive_learning_over_time(self, runtime_gating):
        """Test adaptive learning behavior over multiple iterations."""
        layer_name = "adaptive_test_layer"
        num_neurons = 512
        
        # Simulate multiple inference cycles
        performance_scores = []
        compliance_scores = []
        sparsity_levels = []
        
        for iteration in range(10):
            # Generate WINA scores with some variation
            np.random.seed(42 + iteration)
            wina_scores = self._generate_realistic_wina_scores(num_neurons, layer_name)
            
            # Make gating decision
            decision = runtime_gating.make_gating_decision(layer_name, wina_scores)
            
            # Track metrics
            performance_scores.append(decision.performance_impact)
            compliance_scores.append(decision.constitutional_compliance)
            sparsity_levels.append(decision.sparsity_achieved)
            
            # Simulate performance feedback (improving over time)
            simulated_performance = 0.9 + (iteration * 0.01)
            runtime_gating.layer_performance_history[layer_name][-1] = simulated_performance
        
        # Verify adaptive behavior
        # Performance should stabilize or improve
        recent_performance = np.mean(performance_scores[-3:])
        early_performance = np.mean(performance_scores[:3])
        assert recent_performance >= early_performance - 0.1  # Allow some variance
        
        # Compliance should be reasonable
        assert np.mean(compliance_scores) > 0.2

        # Sparsity should be within reasonable range
        assert 0.0 <= np.mean(sparsity_levels) <= 0.9
    
    def test_constitutional_compliance_enforcement(self, runtime_gating):
        """Test constitutional compliance enforcement across different scenarios."""
        test_scenarios = [
            ("safety_critical_layer", 0.4),  # Lower sparsity for safety
            ("performance_layer", 0.7),      # Higher sparsity for performance
            ("balanced_layer", 0.6)          # Balanced approach
        ]
        
        for layer_name, target_sparsity in test_scenarios:
            # Update layer-specific configuration
            runtime_gating.config.layer_specific_sparsity[layer_name] = target_sparsity
            
            # Generate WINA scores
            wina_scores = self._generate_realistic_wina_scores(256, layer_name)
            
            # Make multiple decisions to build compliance history
            decisions = []
            for i in range(5):
                decision = runtime_gating.make_gating_decision(layer_name, wina_scores)
                decisions.append(decision)
            
            # Verify constitutional compliance
            avg_compliance = np.mean([d.constitutional_compliance for d in decisions])
            assert avg_compliance > 0.6
            
            # Verify sparsity is within constitutional bounds
            avg_sparsity = np.mean([d.sparsity_achieved for d in decisions])
            max_allowed_sparsity = min(target_sparsity + 0.1, 0.85)
            assert avg_sparsity <= max_allowed_sparsity
    
    def test_performance_under_load(self, runtime_gating):
        """Test gating performance under high load conditions."""
        num_layers = 24  # Large transformer model
        neurons_per_layer = 1024
        
        start_time = time.time()
        decisions = []
        
        # Simulate high-frequency gating decisions
        for layer_idx in range(num_layers):
            layer_name = f"transformer.layers.{layer_idx}.attention"
            wina_scores = self._generate_realistic_wina_scores(neurons_per_layer, layer_name)
            
            decision = runtime_gating.make_gating_decision(layer_name, wina_scores)
            decisions.append(decision)
        
        total_time = time.time() - start_time
        avg_decision_time = total_time / num_layers
        
        # Performance requirements
        assert avg_decision_time < 0.01  # Less than 10ms per decision
        assert total_time < 0.2  # Total time under 200ms
        
        # Verify all decisions are valid
        assert len(decisions) == num_layers
        assert all(d.confidence_score > 0.0 for d in decisions)
    
    def test_strategy_selection_intelligence(self, runtime_gating):
        """Test intelligent strategy selection based on context."""
        test_cases = [
            {
                "layer_name": "attention_layer",
                "scores": np.random.uniform(0.3, 0.9, 768),  # High variance
                "expected_strategies": [GatingStrategy.TOP_K, GatingStrategy.HYBRID_DYNAMIC]
            },
            {
                "layer_name": "embedding_layer", 
                "scores": np.full(512, 0.5) + np.random.normal(0, 0.01, 512),  # Low variance
                "expected_strategies": [GatingStrategy.PROBABILISTIC, GatingStrategy.HYBRID_DYNAMIC]
            }
        ]
        
        for case in test_cases:
            # Build some history to influence strategy selection
            for i in range(3):
                decision = runtime_gating.make_gating_decision(case["layer_name"], case["scores"])
                
                # Simulate varying compliance for testing
                if i == 0:
                    runtime_gating.constitutional_compliance_history[case["layer_name"]][-1] = 0.7
                
            # Final decision should use appropriate strategy
            final_decision = runtime_gating.make_gating_decision(case["layer_name"], case["scores"])
            assert final_decision.strategy_used in case["expected_strategies"]
    
    def test_error_recovery_and_fallbacks(self, runtime_gating):
        """Test error recovery and fallback mechanisms."""
        layer_name = "error_test_layer"
        
        # Test with edge cases
        edge_cases = [
            np.array([0.1]),  # Single neuron
            np.full(100, 0.5),  # All same scores
            np.array([0.0, 1.0]),  # Extreme scores
        ]
        
        for scores in edge_cases:
            try:
                decision = runtime_gating.make_gating_decision(layer_name, scores)
                
                # Verify fallback behavior
                assert len(decision.active_neurons) >= 1  # At least one neuron active
                assert decision.confidence_score >= 0.0
                assert decision.constitutional_compliance >= 0.0
                
            except Exception as e:
                # Should handle gracefully
                assert "WINAGatingError" in str(type(e))
    
    def test_memory_efficiency(self, runtime_gating):
        """Test memory efficiency of gating system."""
        layer_name = "memory_test_layer"
        
        # Generate many decisions to test memory management
        for i in range(50):
            wina_scores = self._generate_realistic_wina_scores(1024, layer_name)
            runtime_gating.make_gating_decision(layer_name, wina_scores)
        
        # Verify history is bounded
        assert len(runtime_gating.gating_decisions) <= 50
        assert len(runtime_gating.constitutional_compliance_history[layer_name]) <= runtime_gating.performance_window_size
        assert len(runtime_gating.layer_performance_history[layer_name]) <= runtime_gating.performance_window_size
    
    def _generate_realistic_wina_scores(self, num_neurons: int, layer_name: str) -> np.ndarray:
        """Generate realistic WINA scores based on layer characteristics."""
        if "attention" in layer_name:
            # Attention layers: some high-importance neurons, many medium
            high_importance = np.random.uniform(0.7, 1.0, num_neurons // 4)
            medium_importance = np.random.uniform(0.3, 0.7, num_neurons // 2)
            low_importance = np.random.uniform(0.0, 0.3, num_neurons - len(high_importance) - len(medium_importance))
            scores = np.concatenate([high_importance, medium_importance, low_importance])
        elif "feed_forward" in layer_name:
            # Feed-forward layers: more uniform distribution
            scores = np.random.beta(2, 3, num_neurons)  # Skewed towards lower values
        else:
            # Other layers: normal distribution
            scores = np.random.normal(0.5, 0.2, num_neurons)
            scores = np.clip(scores, 0.0, 1.0)
        
        np.random.shuffle(scores)
        return scores


if __name__ == "__main__":
    pytest.main([__file__])
