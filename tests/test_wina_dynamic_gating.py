"""
Tests for Enhanced WINA Dynamic Neuron Gating

This module tests the enhanced dynamic neuron gating functionality for Subtask 17.3,
including new gating strategies, constitutional compliance, and performance adaptation.
"""

import pytest
import numpy as np
import torch
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import WINA gating components
from src.backend.shared.wina.gating import (
    RuntimeGating,
    GatingStrategy,
    GatingDecision,
    NeuronGate,
    GatingPerformance
)
from src.backend.shared.wina.config import WINAConfig
from src.backend.shared.wina.exceptions import WINAGatingError


class TestEnhancedDynamicGating:
    """Test cases for enhanced dynamic neuron gating."""
    
    @pytest.fixture
    def wina_config(self):
        """Create WINA configuration for testing."""
        return WINAConfig(
            target_sparsity=0.6,
            gflops_reduction_target=0.5,
            accuracy_threshold=0.95,
            enable_runtime_gating=True,
            gating_threshold=0.1,
            layer_specific_sparsity={
                "attention_layer": 0.7,
                "feedforward_layer": 0.5
            }
        )
    
    @pytest.fixture
    def runtime_gating(self, wina_config):
        """Create runtime gating instance for testing."""
        return RuntimeGating(wina_config)
    
    @pytest.fixture
    def sample_wina_scores(self):
        """Generate sample WINA scores for testing."""
        np.random.seed(42)  # For reproducible tests
        return np.random.uniform(0.0, 1.0, 100)
    
    def test_enhanced_gating_strategies_available(self, runtime_gating):
        """Test that all enhanced gating strategies are available."""
        expected_strategies = {
            GatingStrategy.TOP_K,
            GatingStrategy.THRESHOLD_BASED,
            GatingStrategy.ADAPTIVE,
            GatingStrategy.PROBABILISTIC,
            GatingStrategy.CONSTITUTIONAL_AWARE,
            GatingStrategy.PERFORMANCE_ADAPTIVE,
            GatingStrategy.HYBRID_DYNAMIC
        }
        
        available_strategies = set(runtime_gating.strategies.keys())
        assert expected_strategies.issubset(available_strategies)
    
    def test_constitutional_aware_gating(self, runtime_gating, sample_wina_scores):
        """Test constitutional-aware gating strategy."""
        layer_name = "test_layer"
        
        # Test with no compliance history (should use base threshold)
        active_neurons, threshold = runtime_gating._constitutional_aware_gating(layer_name, sample_wina_scores)
        
        assert isinstance(active_neurons, np.ndarray)
        assert isinstance(threshold, float)
        assert len(active_neurons) > 0
        assert threshold > 0
        
        # Verify constitutional compliance constraints
        sparsity_achieved = 1.0 - (len(active_neurons) / len(sample_wina_scores))
        target_sparsity = runtime_gating.config.target_sparsity
        max_sparsity = min(target_sparsity + 0.1, 0.85)
        
        assert sparsity_achieved <= max_sparsity
    
    def test_performance_adaptive_gating(self, runtime_gating, sample_wina_scores):
        """Test performance-adaptive gating strategy."""
        layer_name = "test_layer"
        
        # Add some performance history
        runtime_gating.layer_performance_history[layer_name] = [0.92, 0.94, 0.93]
        
        active_neurons, threshold = runtime_gating._performance_adaptive_gating(layer_name, sample_wina_scores)
        
        assert isinstance(active_neurons, np.ndarray)
        assert isinstance(threshold, float)
        assert len(active_neurons) > 0
        
        # Test adaptation based on performance gap
        # Performance below target should result in more conservative gating
        runtime_gating.layer_performance_history[layer_name] = [0.90, 0.91, 0.92]  # Below 0.95 target
        active_neurons_conservative, threshold_conservative = runtime_gating._performance_adaptive_gating(layer_name, sample_wina_scores)
        
        # Conservative gating should activate more neurons (lower threshold)
        assert len(active_neurons_conservative) >= len(active_neurons)
    
    def test_hybrid_dynamic_gating(self, runtime_gating, sample_wina_scores):
        """Test hybrid dynamic gating strategy selection."""
        layer_name = "attention_layer"
        
        # Test with different contexts
        # Low variance should trigger probabilistic gating
        low_variance_scores = np.full(100, 0.5) + np.random.normal(0, 0.01, 100)
        active_neurons, threshold = runtime_gating._hybrid_dynamic_gating(layer_name, low_variance_scores)
        
        assert isinstance(active_neurons, np.ndarray)
        assert len(active_neurons) > 0
        
        # Attention layer should trigger top-k gating for normal variance
        active_neurons_attn, threshold_attn = runtime_gating._hybrid_dynamic_gating(layer_name, sample_wina_scores)
        assert isinstance(active_neurons_attn, np.ndarray)
    
    def test_enhanced_gating_decision_tracking(self, runtime_gating, sample_wina_scores):
        """Test enhanced gating decision with additional tracking fields."""
        layer_name = "test_layer"
        
        decision = runtime_gating.make_gating_decision(layer_name, sample_wina_scores)
        
        # Verify enhanced tracking fields
        assert decision.constitutional_compliance is not None
        assert 0.0 <= decision.constitutional_compliance <= 1.0
        
        assert decision.performance_impact is not None
        assert 0.0 <= decision.performance_impact <= 1.0
        
        assert decision.confidence_score is not None
        assert 0.0 <= decision.confidence_score <= 1.0
        
        assert decision.adaptation_factor is not None
        assert decision.fallback_applied is False
        
        assert decision.metadata is not None
        assert "layer_type" in decision.metadata
        assert "score_statistics" in decision.metadata
        assert "optimization_context" in decision.metadata
    
    def test_constitutional_compliance_calculation(self, runtime_gating, sample_wina_scores):
        """Test constitutional compliance score calculation."""
        layer_name = "test_layer"
        active_neurons = np.array([0, 1, 2, 3, 4])  # First 5 neurons
        
        compliance_score = runtime_gating._calculate_constitutional_compliance(
            layer_name, sample_wina_scores, active_neurons
        )
        
        assert isinstance(compliance_score, float)
        assert 0.0 <= compliance_score <= 1.0
        
        # Verify compliance history is updated
        assert layer_name in runtime_gating.constitutional_compliance_history
        assert len(runtime_gating.constitutional_compliance_history[layer_name]) == 1
    
    def test_performance_impact_estimation(self, runtime_gating):
        """Test performance impact estimation."""
        layer_name = "attention_layer"
        sparsity_achieved = 0.6
        
        performance_impact = runtime_gating._estimate_performance_impact(layer_name, sparsity_achieved)
        
        assert isinstance(performance_impact, float)
        assert 0.0 <= performance_impact <= 1.0
        
        # Attention layers should have higher impact multiplier
        feedforward_impact = runtime_gating._estimate_performance_impact("feedforward_layer", sparsity_achieved)
        assert performance_impact >= feedforward_impact  # Attention should have higher impact
    
    def test_confidence_score_calculation(self, runtime_gating, sample_wina_scores):
        """Test confidence score calculation for different strategies."""
        active_neurons = np.array([95, 96, 97, 98, 99])  # Top 5 neurons
        
        # Test different strategies
        strategies = [
            GatingStrategy.TOP_K,
            GatingStrategy.CONSTITUTIONAL_AWARE,
            GatingStrategy.PERFORMANCE_ADAPTIVE,
            GatingStrategy.HYBRID_DYNAMIC
        ]
        
        for strategy in strategies:
            confidence = runtime_gating._calculate_confidence_score(
                sample_wina_scores, active_neurons, strategy
            )
            
            assert isinstance(confidence, float)
            assert 0.0 <= confidence <= 1.0
    
    def test_layer_type_inference(self, runtime_gating):
        """Test layer type inference from layer names."""
        test_cases = [
            ("attention_layer", "attention"),
            ("self_attn", "attention"),
            ("feedforward_layer", "feedforward"),
            ("mlp_layer", "feedforward"),
            ("embedding_layer", "embedding"),
            ("layer_norm", "normalization"),
            ("unknown_layer", "other")
        ]
        
        for layer_name, expected_type in test_cases:
            inferred_type = runtime_gating._infer_layer_type(layer_name)
            assert inferred_type == expected_type
    
    def test_adaptive_learning_with_history(self, runtime_gating, sample_wina_scores):
        """Test adaptive learning with performance history."""
        layer_name = "adaptive_layer"
        
        # Simulate multiple gating decisions to build history
        for i in range(5):
            decision = runtime_gating.make_gating_decision(layer_name, sample_wina_scores)
            
            # Verify history is being maintained
            assert layer_name in runtime_gating.constitutional_compliance_history
            assert layer_name in runtime_gating.layer_performance_history
        
        # Verify history window size is respected
        max_history_length = runtime_gating.performance_window_size
        assert len(runtime_gating.constitutional_compliance_history[layer_name]) <= max_history_length
        assert len(runtime_gating.layer_performance_history[layer_name]) <= max_history_length
    
    def test_gating_mask_application(self, runtime_gating, sample_wina_scores):
        """Test gating mask application to layer inputs."""
        layer_name = "test_layer"
        
        # Create gating decision
        decision = runtime_gating.make_gating_decision(layer_name, sample_wina_scores)
        
        # Create mock layer input
        batch_size, seq_len, hidden_dim = 2, 10, len(sample_wina_scores)
        layer_input = torch.randn(batch_size, seq_len, hidden_dim)
        
        # Apply gating mask
        masked_input = runtime_gating.apply_gating_mask(layer_input, decision)
        
        assert masked_input.shape == layer_input.shape
        
        # Verify that inactive neurons are zeroed out
        for inactive_neuron in decision.inactive_neurons:
            assert torch.all(masked_input[:, :, inactive_neuron] == 0.0)
        
        # Verify that active neurons retain their values
        for active_neuron in decision.active_neurons:
            assert torch.allclose(masked_input[:, :, active_neuron], layer_input[:, :, active_neuron])
    
    def test_error_handling_and_fallbacks(self, runtime_gating):
        """Test error handling and fallback mechanisms."""
        layer_name = "error_layer"
        
        # Test with invalid WINA scores
        invalid_scores = np.array([])
        
        with pytest.raises(WINAGatingError):
            runtime_gating.make_gating_decision(layer_name, invalid_scores)
        
        # Test with NaN scores
        nan_scores = np.full(10, np.nan)
        
        with pytest.raises(WINAGatingError):
            runtime_gating.make_gating_decision(layer_name, nan_scores)
    
    def test_performance_metrics_tracking(self, runtime_gating, sample_wina_scores):
        """Test performance metrics tracking across multiple decisions."""
        layer_name = "metrics_layer"
        
        # Make multiple gating decisions
        for i in range(3):
            runtime_gating.make_gating_decision(layer_name, sample_wina_scores)
        
        # Get performance metrics
        metrics = runtime_gating.get_performance_metrics()
        
        assert isinstance(metrics, GatingPerformance)
        assert metrics.total_decisions == 3
        assert metrics.average_decision_time > 0
        assert metrics.average_sparsity > 0
        assert metrics.gflops_reduction > 0
    
    def test_layer_statistics_collection(self, runtime_gating, sample_wina_scores):
        """Test layer-specific statistics collection."""
        layer_name = "stats_layer"
        
        # Initialize layer and make decisions
        runtime_gating.initialize_layer_gates(layer_name, len(sample_wina_scores))
        runtime_gating.make_gating_decision(layer_name, sample_wina_scores)
        
        # Get layer statistics
        stats = runtime_gating.get_layer_statistics(layer_name)
        
        assert "num_neurons" in stats
        assert "average_activation_rate" in stats
        assert "total_decisions" in stats
        assert "average_sparsity" in stats
        assert "strategies_used" in stats
        
        assert stats["num_neurons"] == len(sample_wina_scores)
        assert stats["total_decisions"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
