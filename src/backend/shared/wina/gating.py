"""
Runtime Gating Module for WINA

Implements dynamic neuron gating mechanism for runtime optimization
as part of the WINA (Weight Informed Neuron Activation) system.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Callable
import numpy as np
import torch
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .exceptions import WINAGatingError
from .config import WINAConfig, SparsityStrategy

logger = logging.getLogger(__name__)


class GatingStrategy(Enum):
    """Gating strategies for neuron activation."""
    TOP_K = "top_k"
    THRESHOLD_BASED = "threshold_based"
    ADAPTIVE = "adaptive"
    PROBABILISTIC = "probabilistic"
    CONSTITUTIONAL_AWARE = "constitutional_aware"
    PERFORMANCE_ADAPTIVE = "performance_adaptive"
    HYBRID_DYNAMIC = "hybrid_dynamic"


@dataclass
class GatingDecision:
    """
    Represents a gating decision for a layer.

    Attributes:
        layer_name: Name of the layer
        active_neurons: Indices of active neurons
        inactive_neurons: Indices of inactive neurons
        activation_scores: Scores used for gating decision
        gating_threshold: Threshold used for gating
        sparsity_achieved: Actual sparsity achieved
        decision_time: Time taken to make gating decision
        strategy_used: Gating strategy used
        constitutional_compliance: Constitutional compliance score
        performance_impact: Estimated performance impact
        adaptation_factor: Factor used for adaptive strategies
        confidence_score: Confidence in the gating decision
        fallback_applied: Whether fallback strategy was used
        metadata: Additional metadata for the decision
    """
    layer_name: str
    active_neurons: np.ndarray
    inactive_neurons: np.ndarray
    activation_scores: np.ndarray
    gating_threshold: float
    sparsity_achieved: float
    decision_time: float
    strategy_used: GatingStrategy

    # Enhanced tracking fields
    constitutional_compliance: Optional[float] = None
    performance_impact: Optional[float] = None
    adaptation_factor: Optional[float] = None
    confidence_score: Optional[float] = None
    fallback_applied: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GatingPerformance:
    """
    Performance metrics for gating operations.
    
    Attributes:
        total_decisions: Total number of gating decisions made
        average_decision_time: Average time per gating decision
        total_gating_time: Total time spent on gating
        average_sparsity: Average sparsity achieved
        gflops_reduction: Estimated GFLOPs reduction
        accuracy_impact: Estimated accuracy impact
    """
    total_decisions: int
    average_decision_time: float
    total_gating_time: float
    average_sparsity: float
    gflops_reduction: float
    accuracy_impact: float


class NeuronGate:
    """
    Individual neuron gate for controlling activation.
    
    This class represents a single neuron gate that can be opened or closed
    based on WINA scores and gating strategies.
    """
    
    def __init__(self, neuron_id: int, layer_name: str):
        """
        Initialize neuron gate.
        
        Args:
            neuron_id: Unique identifier for the neuron
            layer_name: Name of the layer this neuron belongs to
        """
        self.neuron_id = neuron_id
        self.layer_name = layer_name
        self.is_active = True
        self.activation_history: List[bool] = []
        self.score_history: List[float] = []
        self.last_activation_time = datetime.now(timezone.utc)
    
    def update_activation(self, is_active: bool, score: float) -> None:
        """
        Update neuron activation status.
        
        Args:
            is_active: Whether the neuron should be active
            score: Activation score for this decision
        """
        self.is_active = is_active
        self.activation_history.append(is_active)
        self.score_history.append(score)
        self.last_activation_time = datetime.now(timezone.utc)
        
        # Keep history limited to prevent memory growth
        if len(self.activation_history) > 1000:
            self.activation_history = self.activation_history[-500:]
            self.score_history = self.score_history[-500:]
    
    def get_activation_statistics(self) -> Dict[str, float]:
        """
        Get activation statistics for this neuron.
        
        Returns:
            Dictionary of activation statistics
        """
        if not self.activation_history:
            return {"activation_rate": 0.0, "average_score": 0.0}
        
        activation_rate = sum(self.activation_history) / len(self.activation_history)
        average_score = np.mean(self.score_history) if self.score_history else 0.0
        
        return {
            "activation_rate": activation_rate,
            "average_score": average_score,
            "total_activations": len(self.activation_history),
            "current_status": float(self.is_active)
        }


class RuntimeGating:
    """
    Runtime gating mechanism for WINA optimization.
    
    This class implements the dynamic neuron gating that controls which neurons
    are active during inference based on WINA scores and configured strategies.
    """
    
    def __init__(self, config: WINAConfig):
        """
        Initialize runtime gating with configuration.
        
        Args:
            config: WINA configuration
        """
        self.config = config
        self.gates: Dict[str, Dict[int, NeuronGate]] = {}
        self.gating_decisions: List[GatingDecision] = []
        self.performance_metrics = GatingPerformance(0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Gating strategies
        self.strategies = {
            GatingStrategy.TOP_K: self._top_k_gating,
            GatingStrategy.THRESHOLD_BASED: self._threshold_gating,
            GatingStrategy.ADAPTIVE: self._adaptive_gating,
            GatingStrategy.PROBABILISTIC: self._probabilistic_gating,
            GatingStrategy.CONSTITUTIONAL_AWARE: self._constitutional_aware_gating,
            GatingStrategy.PERFORMANCE_ADAPTIVE: self._performance_adaptive_gating,
            GatingStrategy.HYBRID_DYNAMIC: self._hybrid_dynamic_gating
        }

        # Enhanced tracking for adaptive strategies
        self.layer_performance_history: Dict[str, List[float]] = {}
        self.constitutional_compliance_history: Dict[str, List[float]] = {}
        self.adaptation_learning_rate = 0.1
        self.performance_window_size = 10
        
        logger.info(f"Initialized runtime gating with threshold: {config.gating_threshold}")
    
    def initialize_layer_gates(self, layer_name: str, num_neurons: int) -> None:
        """
        Initialize gates for a specific layer.
        
        Args:
            layer_name: Name of the layer
            num_neurons: Number of neurons in the layer
        """
        if layer_name not in self.gates:
            self.gates[layer_name] = {}
        
        for neuron_id in range(num_neurons):
            if neuron_id not in self.gates[layer_name]:
                self.gates[layer_name][neuron_id] = NeuronGate(neuron_id, layer_name)
        
        logger.debug(f"Initialized {num_neurons} gates for layer {layer_name}")
    
    def make_gating_decision(self, layer_name: str, wina_scores: np.ndarray, 
                           strategy: Optional[GatingStrategy] = None) -> GatingDecision:
        """
        Make gating decision for a layer based on WINA scores.
        
        Args:
            layer_name: Name of the layer
            wina_scores: WINA scores for each neuron
            strategy: Optional gating strategy to use
            
        Returns:
            GatingDecision containing the gating decision details
        """
        start_time = time.time()
        
        try:
            # Determine gating strategy
            if strategy is None:
                strategy = self._select_strategy(layer_name, wina_scores)
            
            # Apply gating strategy
            gating_function = self.strategies[strategy]
            active_neurons, gating_threshold = gating_function(layer_name, wina_scores)
            
            # Calculate inactive neurons
            all_neurons = np.arange(len(wina_scores))
            inactive_neurons = np.setdiff1d(all_neurons, active_neurons)
            
            # Calculate sparsity
            sparsity_achieved = len(inactive_neurons) / len(wina_scores)
            
            # Update neuron gates
            self._update_neuron_gates(layer_name, active_neurons, inactive_neurons, wina_scores)
            
            decision_time = time.time() - start_time

            # Calculate enhanced metrics
            constitutional_compliance = self._calculate_constitutional_compliance(layer_name, wina_scores, active_neurons)
            performance_impact = self._estimate_performance_impact(layer_name, sparsity_achieved)
            confidence_score = self._calculate_confidence_score(wina_scores, active_neurons, strategy)
            adaptation_factor = self._get_adaptation_factor(layer_name, strategy)

            decision = GatingDecision(
                layer_name=layer_name,
                active_neurons=active_neurons,
                inactive_neurons=inactive_neurons,
                activation_scores=wina_scores,
                gating_threshold=gating_threshold,
                sparsity_achieved=sparsity_achieved,
                decision_time=decision_time,
                strategy_used=strategy,
                constitutional_compliance=constitutional_compliance,
                performance_impact=performance_impact,
                adaptation_factor=adaptation_factor,
                confidence_score=confidence_score,
                fallback_applied=False,
                metadata={
                    "layer_type": self._infer_layer_type(layer_name),
                    "score_statistics": {
                        "mean": float(np.mean(wina_scores)),
                        "std": float(np.std(wina_scores)),
                        "min": float(np.min(wina_scores)),
                        "max": float(np.max(wina_scores))
                    },
                    "optimization_context": {
                        "target_sparsity": self.config.layer_specific_sparsity.get(layer_name, self.config.target_sparsity),
                        "gflops_reduction_target": self.config.gflops_reduction_target
                    }
                }
            )
            
            # Store decision
            self.gating_decisions.append(decision)
            
            # Update performance metrics
            self._update_performance_metrics(decision)
            
            logger.debug(f"Gating decision for {layer_name}: {len(active_neurons)}/{len(wina_scores)} neurons active "
                        f"(sparsity: {sparsity_achieved:.2%}, strategy: {strategy.value})")
            
            return decision
            
        except Exception as e:
            logger.error(f"Gating decision failed for {layer_name}: {e}")
            raise WINAGatingError(f"Gating decision failed: {e}")
    
    def apply_gating_mask(self, layer_input: torch.Tensor, gating_decision: GatingDecision) -> torch.Tensor:
        """
        Apply gating mask to layer input.
        
        Args:
            layer_input: Input tensor to the layer
            gating_decision: Gating decision to apply
            
        Returns:
            Masked input tensor
        """
        try:
            # Create mask
            mask = torch.zeros(layer_input.shape[-1], dtype=layer_input.dtype, device=layer_input.device)
            mask[gating_decision.active_neurons] = 1.0
            
            # Apply mask
            masked_input = layer_input * mask
            
            logger.debug(f"Applied gating mask to {gating_decision.layer_name}: "
                        f"{len(gating_decision.active_neurons)} active neurons")
            
            return masked_input
            
        except Exception as e:
            logger.error(f"Failed to apply gating mask for {gating_decision.layer_name}: {e}")
            raise WINAGatingError(f"Mask application failed: {e}")
    
    def _select_strategy(self, layer_name: str, wina_scores: np.ndarray) -> GatingStrategy:
        """
        Select appropriate gating strategy based on layer and scores.
        
        Args:
            layer_name: Name of the layer
            wina_scores: WINA scores
            
        Returns:
            Selected gating strategy
        """
        # Simple strategy selection based on configuration
        if self.config.sparsity_strategy == SparsityStrategy.ADAPTIVE_DYNAMIC:
            return GatingStrategy.ADAPTIVE
        elif "attention" in layer_name.lower():
            return GatingStrategy.TOP_K
        else:
            return GatingStrategy.THRESHOLD_BASED
    
    def _top_k_gating(self, layer_name: str, wina_scores: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Top-K gating strategy.
        
        Args:
            layer_name: Name of the layer
            wina_scores: WINA scores
            
        Returns:
            Tuple of (active_neuron_indices, gating_threshold)
        """
        # Get target sparsity for this layer
        target_sparsity = self.config.layer_specific_sparsity.get(layer_name, self.config.target_sparsity)
        k = int(len(wina_scores) * (1 - target_sparsity))
        k = max(1, k)  # Ensure at least one neuron is active
        
        # Get top-K indices
        top_k_indices = np.argpartition(wina_scores, -k)[-k:]
        
        # Threshold is the minimum score among top-K
        threshold = wina_scores[top_k_indices].min() if len(top_k_indices) > 0 else 0.0
        
        return top_k_indices, threshold
    
    def _threshold_gating(self, layer_name: str, wina_scores: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Threshold-based gating strategy.
        
        Args:
            layer_name: Name of the layer
            wina_scores: WINA scores
            
        Returns:
            Tuple of (active_neuron_indices, gating_threshold)
        """
        # Use configured gating threshold
        threshold = self.config.gating_threshold
        
        # Find neurons above threshold
        active_indices = np.where(wina_scores > threshold)[0]
        
        # Ensure minimum number of active neurons
        if len(active_indices) == 0:
            # Fallback to top-1 if no neurons meet threshold
            active_indices = np.array([np.argmax(wina_scores)])
            threshold = wina_scores[active_indices[0]]
        
        return active_indices, threshold
    
    def _adaptive_gating(self, layer_name: str, wina_scores: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Adaptive gating strategy that adjusts based on score distribution.
        
        Args:
            layer_name: Name of the layer
            wina_scores: WINA scores
            
        Returns:
            Tuple of (active_neuron_indices, gating_threshold)
        """
        # Calculate adaptive threshold based on score statistics
        mean_score = np.mean(wina_scores)
        std_score = np.std(wina_scores)
        
        # Adaptive threshold: mean + (std * factor)
        adaptive_factor = 0.5  # Can be made configurable
        threshold = mean_score + (std_score * adaptive_factor)
        
        # Find neurons above adaptive threshold
        active_indices = np.where(wina_scores > threshold)[0]
        
        # Ensure reasonable sparsity bounds
        target_sparsity = self.config.layer_specific_sparsity.get(layer_name, self.config.target_sparsity)
        min_active = int(len(wina_scores) * (1 - min(target_sparsity + 0.2, 0.9)))
        max_active = int(len(wina_scores) * (1 - max(target_sparsity - 0.2, 0.1)))
        
        if len(active_indices) < min_active:
            # Too sparse, use top-K
            active_indices = np.argpartition(wina_scores, -min_active)[-min_active:]
            threshold = wina_scores[active_indices].min()
        elif len(active_indices) > max_active:
            # Not sparse enough, use higher threshold
            active_indices = np.argpartition(wina_scores, -max_active)[-max_active:]
            threshold = wina_scores[active_indices].min()
        
        return active_indices, threshold
    
    def _probabilistic_gating(self, layer_name: str, wina_scores: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Probabilistic gating strategy based on score probabilities.
        
        Args:
            layer_name: Name of the layer
            wina_scores: WINA scores
            
        Returns:
            Tuple of (active_neuron_indices, gating_threshold)
        """
        # Normalize scores to probabilities
        scores_normalized = wina_scores - np.min(wina_scores)
        if np.max(scores_normalized) > 0:
            probabilities = scores_normalized / np.max(scores_normalized)
        else:
            probabilities = np.ones_like(scores_normalized) / len(scores_normalized)
        
        # Sample based on probabilities
        target_sparsity = self.config.layer_specific_sparsity.get(layer_name, self.config.target_sparsity)
        num_active = int(len(wina_scores) * (1 - target_sparsity))
        
        # Use weighted sampling without replacement
        active_indices = np.random.choice(
            len(wina_scores), 
            size=num_active, 
            replace=False, 
            p=probabilities / np.sum(probabilities)
        )
        
        threshold = wina_scores[active_indices].min() if len(active_indices) > 0 else 0.0
        
        return active_indices, threshold

    def _constitutional_aware_gating(self, layer_name: str, wina_scores: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Constitutional-aware gating strategy that considers constitutional compliance.

        Args:
            layer_name: Name of the layer
            wina_scores: WINA scores

        Returns:
            Tuple of (active_neuron_indices, gating_threshold)
        """
        # Get constitutional compliance history for this layer
        compliance_history = self.constitutional_compliance_history.get(layer_name, [])

        # Base threshold calculation
        base_threshold = np.mean(wina_scores) + 0.5 * np.std(wina_scores)

        # Adjust threshold based on constitutional compliance
        if compliance_history:
            avg_compliance = np.mean(compliance_history[-5:])  # Last 5 decisions
            if avg_compliance < 0.8:  # Low compliance, be more conservative
                threshold = base_threshold + 0.2 * np.std(wina_scores)
            elif avg_compliance > 0.95:  # High compliance, can be more aggressive
                threshold = base_threshold - 0.1 * np.std(wina_scores)
            else:
                threshold = base_threshold
        else:
            threshold = base_threshold

        # Find neurons above threshold
        active_indices = np.where(wina_scores > threshold)[0]

        # Ensure constitutional compliance constraints
        target_sparsity = self.config.layer_specific_sparsity.get(layer_name, self.config.target_sparsity)
        max_sparsity = min(target_sparsity + 0.1, 0.85)  # Constitutional safety margin
        min_active = int(len(wina_scores) * (1 - max_sparsity))

        if len(active_indices) < min_active:
            # Ensure minimum neurons for constitutional compliance
            top_indices = np.argpartition(wina_scores, -min_active)[-min_active:]
            active_indices = top_indices
            threshold = wina_scores[active_indices].min()

        return active_indices, threshold

    def _performance_adaptive_gating(self, layer_name: str, wina_scores: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Performance-adaptive gating strategy that learns from performance history.

        Args:
            layer_name: Name of the layer
            wina_scores: WINA scores

        Returns:
            Tuple of (active_neuron_indices, gating_threshold)
        """
        # Get performance history for this layer
        performance_history = self.layer_performance_history.get(layer_name, [])

        # Base threshold from adaptive strategy
        base_threshold = np.mean(wina_scores) + 0.5 * np.std(wina_scores)

        # Adapt based on performance history
        if len(performance_history) >= 3:
            recent_performance = np.mean(performance_history[-3:])
            target_performance = self.config.accuracy_threshold

            # Calculate performance gap
            performance_gap = target_performance - recent_performance

            # Adjust threshold based on performance gap
            if performance_gap > 0.02:  # Performance below target
                # Be more conservative (lower threshold = more neurons active)
                threshold = base_threshold - performance_gap * np.std(wina_scores)
            elif performance_gap < -0.01:  # Performance above target
                # Be more aggressive (higher threshold = fewer neurons active)
                threshold = base_threshold + abs(performance_gap) * np.std(wina_scores)
            else:
                threshold = base_threshold
        else:
            threshold = base_threshold

        # Find neurons above threshold
        active_indices = np.where(wina_scores > threshold)[0]

        # Ensure reasonable bounds
        target_sparsity = self.config.layer_specific_sparsity.get(layer_name, self.config.target_sparsity)
        min_active = max(1, int(len(wina_scores) * (1 - min(target_sparsity + 0.2, 0.9))))
        max_active = int(len(wina_scores) * (1 - max(target_sparsity - 0.2, 0.1)))

        if len(active_indices) < min_active:
            top_indices = np.argpartition(wina_scores, -min_active)[-min_active:]
            active_indices = top_indices
            threshold = wina_scores[active_indices].min()
        elif len(active_indices) > max_active:
            top_indices = np.argpartition(wina_scores, -max_active)[-max_active:]
            active_indices = top_indices
            threshold = wina_scores[active_indices].min()

        return active_indices, threshold

    def _hybrid_dynamic_gating(self, layer_name: str, wina_scores: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Hybrid dynamic gating that combines multiple strategies based on context.

        Args:
            layer_name: Name of the layer
            wina_scores: WINA scores

        Returns:
            Tuple of (active_neuron_indices, gating_threshold)
        """
        # Analyze context to select best strategy combination
        score_variance = np.var(wina_scores)

        # Get historical performance
        performance_history = self.layer_performance_history.get(layer_name, [])
        compliance_history = self.constitutional_compliance_history.get(layer_name, [])

        # Strategy selection based on context
        if score_variance < 0.01:  # Low variance - use probabilistic
            return self._probabilistic_gating(layer_name, wina_scores)
        elif len(compliance_history) > 0 and np.mean(compliance_history[-3:]) < 0.85:
            # Low compliance - use constitutional aware
            return self._constitutional_aware_gating(layer_name, wina_scores)
        elif len(performance_history) > 0 and np.mean(performance_history[-3:]) < self.config.accuracy_threshold:
            # Low performance - use performance adaptive
            return self._performance_adaptive_gating(layer_name, wina_scores)
        elif "attention" in layer_name.lower():
            # Attention layers - use top-k for stability
            return self._top_k_gating(layer_name, wina_scores)
        else:
            # Default to adaptive
            return self._adaptive_gating(layer_name, wina_scores)

    def _update_neuron_gates(self, layer_name: str, active_neurons: np.ndarray,
                           inactive_neurons: np.ndarray, wina_scores: np.ndarray) -> None:
        """
        Update neuron gates based on gating decision.
        
        Args:
            layer_name: Name of the layer
            active_neurons: Indices of active neurons
            inactive_neurons: Indices of inactive neurons
            wina_scores: WINA scores
        """
        if layer_name not in self.gates:
            self.initialize_layer_gates(layer_name, len(wina_scores))
        
        # Update active neurons
        for neuron_id in active_neurons:
            if neuron_id in self.gates[layer_name]:
                self.gates[layer_name][neuron_id].update_activation(True, wina_scores[neuron_id])
        
        # Update inactive neurons
        for neuron_id in inactive_neurons:
            if neuron_id in self.gates[layer_name]:
                self.gates[layer_name][neuron_id].update_activation(False, wina_scores[neuron_id])
    
    def _update_performance_metrics(self, decision: GatingDecision) -> None:
        """
        Update performance metrics based on gating decision.
        
        Args:
            decision: Gating decision to incorporate into metrics
        """
        # Update counters
        self.performance_metrics.total_decisions += 1
        self.performance_metrics.total_gating_time += decision.decision_time
        
        # Update averages
        total = self.performance_metrics.total_decisions
        self.performance_metrics.average_decision_time = (
            (self.performance_metrics.average_decision_time * (total - 1) + decision.decision_time) / total
        )
        self.performance_metrics.average_sparsity = (
            (self.performance_metrics.average_sparsity * (total - 1) + decision.sparsity_achieved) / total
        )
        
        # Estimate GFLOPs reduction (simplified)
        self.performance_metrics.gflops_reduction = self.performance_metrics.average_sparsity
    
    def get_layer_statistics(self, layer_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific layer.
        
        Args:
            layer_name: Name of the layer
            
        Returns:
            Dictionary of layer statistics
        """
        if layer_name not in self.gates:
            return {"error": "Layer not found"}
        
        gates = self.gates[layer_name]
        
        # Aggregate neuron statistics
        activation_rates = []
        average_scores = []
        
        for gate in gates.values():
            stats = gate.get_activation_statistics()
            activation_rates.append(stats["activation_rate"])
            average_scores.append(stats["average_score"])
        
        # Layer-specific decisions
        layer_decisions = [d for d in self.gating_decisions if d.layer_name == layer_name]
        
        return {
            "num_neurons": len(gates),
            "average_activation_rate": np.mean(activation_rates) if activation_rates else 0.0,
            "average_score": np.mean(average_scores) if average_scores else 0.0,
            "total_decisions": len(layer_decisions),
            "average_sparsity": np.mean([d.sparsity_achieved for d in layer_decisions]) if layer_decisions else 0.0,
            "strategies_used": list(set([d.strategy_used.value for d in layer_decisions]))
        }
    
    def get_performance_metrics(self) -> GatingPerformance:
        """
        Get current performance metrics.
        
        Returns:
            Current performance metrics
        """
        return self.performance_metrics
    
    def reset_statistics(self) -> None:
        """Reset all statistics and history."""
        self.gating_decisions.clear()
        self.performance_metrics = GatingPerformance(0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Reset neuron gate histories
        for layer_gates in self.gates.values():
            for gate in layer_gates.values():
                gate.activation_history.clear()
                gate.score_history.clear()
        
        logger.info("Runtime gating statistics reset")

    def _calculate_constitutional_compliance(self, layer_name: str, wina_scores: np.ndarray, active_neurons: np.ndarray) -> float:
        """Calculate constitutional compliance score for gating decision."""
        try:
            # Basic compliance based on sparsity constraints
            target_sparsity = self.config.layer_specific_sparsity.get(layer_name, self.config.target_sparsity)
            actual_sparsity = 1.0 - (len(active_neurons) / len(wina_scores))

            # Compliance score based on how close we are to target
            sparsity_compliance = 1.0 - abs(actual_sparsity - target_sparsity) / target_sparsity

            # Additional compliance factors
            score_distribution_compliance = self._assess_score_distribution_compliance(wina_scores, active_neurons)

            # Combined compliance score
            compliance_score = 0.7 * sparsity_compliance + 0.3 * score_distribution_compliance

            # Update compliance history
            if layer_name not in self.constitutional_compliance_history:
                self.constitutional_compliance_history[layer_name] = []

            self.constitutional_compliance_history[layer_name].append(compliance_score)

            # Keep only recent history
            if len(self.constitutional_compliance_history[layer_name]) > self.performance_window_size:
                self.constitutional_compliance_history[layer_name] = \
                    self.constitutional_compliance_history[layer_name][-self.performance_window_size:]

            return max(0.0, min(1.0, compliance_score))

        except Exception as e:
            logger.warning(f"Constitutional compliance calculation failed for {layer_name}: {e}")
            return 0.5  # Neutral score on error

    def _estimate_performance_impact(self, layer_name: str, sparsity_achieved: float) -> float:
        """Estimate performance impact of gating decision."""
        try:
            # Base performance impact from sparsity
            base_impact = sparsity_achieved * self.config.gflops_reduction_target

            # Layer-specific adjustments
            layer_type = self._infer_layer_type(layer_name)
            if layer_type == "attention":
                # Attention layers have higher impact
                impact_multiplier = 1.2
            elif layer_type == "feedforward":
                # Feedforward layers have standard impact
                impact_multiplier = 1.0
            else:
                # Other layers have lower impact
                impact_multiplier = 0.8

            performance_impact = base_impact * impact_multiplier

            # Update performance history
            if layer_name not in self.layer_performance_history:
                self.layer_performance_history[layer_name] = []

            self.layer_performance_history[layer_name].append(performance_impact)

            # Keep only recent history
            if len(self.layer_performance_history[layer_name]) > self.performance_window_size:
                self.layer_performance_history[layer_name] = \
                    self.layer_performance_history[layer_name][-self.performance_window_size:]

            return max(0.0, min(1.0, performance_impact))

        except Exception as e:
            logger.warning(f"Performance impact estimation failed for {layer_name}: {e}")
            return 0.5  # Neutral score on error

    def _calculate_confidence_score(self, wina_scores: np.ndarray, active_neurons: np.ndarray, strategy: GatingStrategy) -> float:
        """Calculate confidence score for gating decision."""
        try:
            # Score-based confidence
            if len(active_neurons) > 0:
                active_scores = wina_scores[active_neurons]
                score_confidence = np.mean(active_scores) / (np.max(wina_scores) + 1e-8)
            else:
                score_confidence = 0.0

            # Strategy-based confidence
            strategy_confidence_map = {
                GatingStrategy.TOP_K: 0.9,
                GatingStrategy.THRESHOLD_BASED: 0.8,
                GatingStrategy.ADAPTIVE: 0.7,
                GatingStrategy.PROBABILISTIC: 0.6,
                GatingStrategy.CONSTITUTIONAL_AWARE: 0.85,
                GatingStrategy.PERFORMANCE_ADAPTIVE: 0.75,
                GatingStrategy.HYBRID_DYNAMIC: 0.8
            }
            strategy_confidence = strategy_confidence_map.get(strategy, 0.5)

            # Combined confidence
            confidence = 0.6 * score_confidence + 0.4 * strategy_confidence

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.warning(f"Confidence score calculation failed: {e}")
            return 0.5  # Neutral score on error

    def _get_adaptation_factor(self, layer_name: str, strategy: GatingStrategy) -> float:
        """Get adaptation factor for the layer and strategy."""
        if strategy in [GatingStrategy.ADAPTIVE, GatingStrategy.PERFORMANCE_ADAPTIVE, GatingStrategy.HYBRID_DYNAMIC]:
            # Get recent performance for adaptive strategies
            performance_history = self.layer_performance_history.get(layer_name, [])
            if len(performance_history) >= 2:
                recent_trend = performance_history[-1] - performance_history[-2]
                return self.adaptation_learning_rate * recent_trend
            else:
                return 0.0
        else:
            return 0.0

    def _infer_layer_type(self, layer_name: str) -> str:
        """Infer layer type from layer name."""
        layer_name_lower = layer_name.lower()
        if "attention" in layer_name_lower or "attn" in layer_name_lower:
            return "attention"
        elif "feed" in layer_name_lower or "mlp" in layer_name_lower or "ffn" in layer_name_lower:
            return "feedforward"
        elif "embed" in layer_name_lower:
            return "embedding"
        elif "norm" in layer_name_lower or "layer_norm" in layer_name_lower:
            return "normalization"
        else:
            return "other"

    def _assess_score_distribution_compliance(self, wina_scores: np.ndarray, active_neurons: np.ndarray) -> float:
        """Assess compliance based on score distribution."""
        try:
            if len(active_neurons) == 0:
                return 0.0

            # Check if active neurons have higher scores than inactive ones
            active_scores = wina_scores[active_neurons]
            inactive_indices = np.setdiff1d(np.arange(len(wina_scores)), active_neurons)

            if len(inactive_indices) == 0:
                return 1.0

            inactive_scores = wina_scores[inactive_indices]

            # Calculate score separation
            active_mean = np.mean(active_scores)
            inactive_mean = np.mean(inactive_scores)

            if active_mean > inactive_mean:
                # Good separation - active neurons have higher scores
                separation_ratio = (active_mean - inactive_mean) / (np.max(wina_scores) - np.min(wina_scores) + 1e-8)
                return min(1.0, separation_ratio * 2)  # Scale to [0, 1]
            else:
                # Poor separation - active neurons don't have higher scores
                return 0.2

        except Exception as e:
            logger.warning(f"Score distribution compliance assessment failed: {e}")
            return 0.5
