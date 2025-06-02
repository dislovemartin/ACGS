"""
WINA Continuous Learning Feedback Loops System

This module implements adaptive learning mechanisms for the WINA (Weight Informed Neuron Activation) system,
creating intelligent feedback loops that continuously improve optimization strategies based on performance data.

Key Features:
- Centralized feedback processing system collecting data from all WINA components
- Adaptive learning algorithms adjusting WINA parameters based on operational outcomes
- Component-specific feedback loops for Neuron Activation, SVD Transformation, Dynamic Gating
- Constitutional compliance monitoring and learning
- Performance-based learning with reinforcement mechanisms
- Real-time strategy optimization and threshold adjustment
- Integration with performance monitoring system from Task 17.10

Target Performance:
- 40-70% GFLOPs reduction while maintaining >95% synthesis accuracy retention
- Adaptive intelligence that learns from operational patterns
- Constitutional compliance optimization through continuous feedback
- Real-time parameter adjustment based on performance metrics
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict
import numpy as np
from abc import ABC, abstractmethod

# WINA imports
try:
    from .config import WINAConfig, WINAIntegrationConfig
    from .metrics import WINAMetrics
    from .performance_monitoring import (
        WINAPerformanceCollector,
        WINAMonitoringLevel,
        WINANeuronActivationMetrics,
        WINASVDTransformationMetrics,
        WINADynamicGatingMetrics,
        WINAConstitutionalComplianceMetrics,
        WINALearningFeedbackMetrics,
        WINAIntegrationPerformanceMetrics,
        WINASystemHealthMetrics,
        WINAComponentType
    )
    WINA_AVAILABLE = True
except ImportError as e:
    WINA_AVAILABLE = False
    logging.getLogger(__name__).warning(f"WINA modules not available: {e}")

logger = logging.getLogger(__name__)


class LearningStrategy(Enum):
    """Learning strategy types for WINA continuous learning."""
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    PATTERN_RECOGNITION = "pattern_recognition"
    ADAPTIVE_THRESHOLD = "adaptive_threshold"
    GRADIENT_OPTIMIZATION = "gradient_optimization"
    CONSTITUTIONAL_ALIGNMENT = "constitutional_alignment"
    HYBRID_MULTIMODAL = "hybrid_multimodal"


class FeedbackType(Enum):
    """Types of feedback for learning system."""
    PERFORMANCE_METRIC = "performance_metric"
    ACCURACY_RETENTION = "accuracy_retention"
    EFFICIENCY_GAIN = "efficiency_gain"
    CONSTITUTIONAL_COMPLIANCE = "constitutional_compliance"
    USER_FEEDBACK = "user_feedback"
    SYSTEM_ERROR = "system_error"
    OPTIMIZATION_SUCCESS = "optimization_success"


class LearningPhase(Enum):
    """Learning phases for adaptive optimization."""
    EXPLORATION = "exploration"  # Exploring new parameter spaces
    EXPLOITATION = "exploitation"  # Using known good parameters
    CONVERGENCE = "convergence"  # Fine-tuning converged parameters
    ADAPTATION = "adaptation"  # Adapting to new conditions


@dataclass
class FeedbackSignal:
    """Individual feedback signal for learning system."""
    component_type: WINAComponentType
    feedback_type: FeedbackType
    value: float
    context: Dict[str, Any]
    timestamp: datetime
    confidence: float = 1.0
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningAction:
    """Action taken by learning system."""
    action_type: str
    component_target: WINAComponentType
    parameter_adjustments: Dict[str, float]
    expected_impact: float
    confidence: float
    rationale: str
    timestamp: datetime


@dataclass
class LearningState:
    """Current state of learning system."""
    current_phase: LearningPhase
    strategy_in_use: LearningStrategy
    exploration_rate: float
    learning_rate: float
    convergence_threshold: float
    performance_trend: List[float]
    last_significant_change: datetime
    component_states: Dict[WINAComponentType, Dict[str, Any]]


@dataclass
class ComponentLearningProfile:
    """Learning profile for specific WINA component."""
    component_type: WINAComponentType
    optimal_parameters: Dict[str, float]
    parameter_bounds: Dict[str, Tuple[float, float]]
    learning_history: List[Tuple[Dict[str, float], float]]  # (params, performance)
    adaptation_rate: float
    stability_score: float
    last_update: datetime
    performance_baseline: float


class LearningAlgorithm(ABC):
    """Abstract base class for learning algorithms."""
    
    @abstractmethod
    async def process_feedback(self, feedback: List[FeedbackSignal]) -> List[LearningAction]:
        """Process feedback signals and generate learning actions."""
        pass
    
    @abstractmethod
    async def update_parameters(self, component_type: WINAComponentType, 
                               current_params: Dict[str, float]) -> Dict[str, float]:
        """Update parameters for specific component."""
        pass


class ReinforcementLearningAlgorithm(LearningAlgorithm):
    """Reinforcement learning algorithm for WINA optimization."""
    
    def __init__(self, learning_rate: float = 0.01, exploration_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.experience_replay: deque = deque(maxlen=10000)
        
    async def process_feedback(self, feedback: List[FeedbackSignal]) -> List[LearningAction]:
        """Process feedback using reinforcement learning."""
        actions = []
        
        for signal in feedback:
            # Convert feedback to reward signal
            reward = self._calculate_reward(signal)
            
            # Update Q-values
            state_key = self._get_state_key(signal.context)
            action_key = f"{signal.component_type.value}_{signal.feedback_type.value}"
            
            # Q-learning update
            current_q = self.q_table[state_key][action_key]
            max_future_q = max(self.q_table[state_key].values()) if self.q_table[state_key] else 0
            new_q = current_q + self.learning_rate * (reward + 0.9 * max_future_q - current_q)
            self.q_table[state_key][action_key] = new_q
            
            # Generate learning action if improvement opportunity detected
            if reward > 0.1:  # Threshold for significant improvement
                action = await self._generate_learning_action(signal, reward)
                if action:
                    actions.append(action)
        
        return actions
    
    def _calculate_reward(self, signal: FeedbackSignal) -> float:
        """Calculate reward signal from feedback."""
        if signal.feedback_type == FeedbackType.EFFICIENCY_GAIN:
            return signal.value  # Direct efficiency gain as reward
        elif signal.feedback_type == FeedbackType.ACCURACY_RETENTION:
            return signal.value - 0.95  # Reward above 95% accuracy target
        elif signal.feedback_type == FeedbackType.CONSTITUTIONAL_COMPLIANCE:
            return signal.value  # Direct compliance score as reward
        elif signal.feedback_type == FeedbackType.SYSTEM_ERROR:
            return -signal.value  # Negative reward for errors
        else:
            return signal.value * signal.confidence
    
    def _get_state_key(self, context: Dict[str, Any]) -> str:
        """Generate state key from context."""
        key_elements = []
        for key in sorted(context.keys()):
            if isinstance(context[key], (int, float, str, bool)):
                key_elements.append(f"{key}:{context[key]}")
        return "_".join(key_elements)
    
    async def _generate_learning_action(self, signal: FeedbackSignal, reward: float) -> Optional[LearningAction]:
        """Generate learning action based on feedback signal."""
        try:
            # Determine parameter adjustments based on feedback
            adjustments = {}
            
            if signal.component_type == WINAComponentType.NEURON_ACTIVATION:
                if signal.feedback_type == FeedbackType.EFFICIENCY_GAIN and reward > 0:
                    adjustments["activation_threshold"] = 0.05 * reward
                elif signal.feedback_type == FeedbackType.ACCURACY_RETENTION and reward < 0:
                    adjustments["activation_threshold"] = -0.02 * abs(reward)
            
            elif signal.component_type == WINAComponentType.DYNAMIC_GATING:
                if signal.feedback_type == FeedbackType.EFFICIENCY_GAIN and reward > 0:
                    adjustments["gating_threshold"] = 0.03 * reward
                    adjustments["adaptive_rate"] = 0.01 * reward
            
            elif signal.component_type == WINAComponentType.SVD_TRANSFORMATION:
                if signal.feedback_type == FeedbackType.ACCURACY_RETENTION and reward > 0:
                    adjustments["rank_threshold"] = 0.02 * reward
            
            if adjustments:
                return LearningAction(
                    action_type="parameter_adjustment",
                    component_target=signal.component_type,
                    parameter_adjustments=adjustments,
                    expected_impact=reward,
                    confidence=signal.confidence,
                    rationale=f"Reinforcement learning based on {signal.feedback_type.value}",
                    timestamp=datetime.now()
                )
        except Exception as e:
            logger.warning(f"Failed to generate learning action: {e}")
        
        return None
    
    async def update_parameters(self, component_type: WINAComponentType, 
                               current_params: Dict[str, float]) -> Dict[str, float]:
        """Update parameters using reinforcement learning insights."""
        updated_params = current_params.copy()
        
        # Apply exploration vs exploitation strategy
        if np.random.random() < self.exploration_rate:
            # Exploration: add random noise
            for param, value in updated_params.items():
                noise = np.random.normal(0, 0.01)
                updated_params[param] = max(0, min(1, value + noise))
        else:
            # Exploitation: use learned Q-values to guide updates
            # This would use the Q-table to determine best actions
            pass
        
        return updated_params


class PatternRecognitionAlgorithm(LearningAlgorithm):
    """Pattern recognition algorithm for identifying optimization opportunities."""
    
    def __init__(self, window_size: int = 100, similarity_threshold: float = 0.8):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.pattern_database: List[Dict[str, Any]] = []
        self.feedback_history: deque = deque(maxlen=window_size)
        
    async def process_feedback(self, feedback: List[FeedbackSignal]) -> List[LearningAction]:
        """Process feedback using pattern recognition."""
        actions = []
        
        # Add feedback to history
        self.feedback_history.extend(feedback)
        
        # Look for patterns in recent feedback
        patterns = await self._identify_patterns()
        
        for pattern in patterns:
            action = await self._pattern_to_action(pattern)
            if action:
                actions.append(action)
        
        return actions
    
    async def _identify_patterns(self) -> List[Dict[str, Any]]:
        """Identify patterns in feedback history."""
        patterns = []
        
        if len(self.feedback_history) < 10:
            return patterns
        
        try:
            # Group feedback by component type
            component_feedback = defaultdict(list)
            for signal in self.feedback_history:
                component_feedback[signal.component_type].append(signal)
            
            for component, signals in component_feedback.items():
                # Look for performance trends
                if len(signals) >= 5:
                    values = [s.value for s in signals[-5:]]
                    
                    # Identify trends
                    if self._is_increasing_trend(values):
                        patterns.append({
                            "type": "increasing_performance",
                            "component": component,
                            "strength": self._calculate_trend_strength(values),
                            "signals": signals[-5:]
                        })
                    elif self._is_decreasing_trend(values):
                        patterns.append({
                            "type": "decreasing_performance",
                            "component": component,
                            "strength": self._calculate_trend_strength(values),
                            "signals": signals[-5:]
                        })
        
        except Exception as e:
            logger.warning(f"Pattern identification failed: {e}")
        
        return patterns
    
    def _is_increasing_trend(self, values: List[float]) -> bool:
        """Check if values show increasing trend."""
        if len(values) < 3:
            return False
        
        increases = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
        return increases >= len(values) * 0.6
    
    def _is_decreasing_trend(self, values: List[float]) -> bool:
        """Check if values show decreasing trend."""
        if len(values) < 3:
            return False
        
        decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i-1])
        return decreases >= len(values) * 0.6
    
    def _calculate_trend_strength(self, values: List[float]) -> float:
        """Calculate strength of trend."""
        if len(values) < 2:
            return 0.0
        
        return abs((values[-1] - values[0]) / len(values))
    
    async def _pattern_to_action(self, pattern: Dict[str, Any]) -> Optional[LearningAction]:
        """Convert identified pattern to learning action."""
        try:
            if pattern["type"] == "increasing_performance":
                # Reinforce current approach
                return LearningAction(
                    action_type="reinforce_current",
                    component_target=pattern["component"],
                    parameter_adjustments={"stability_boost": 0.1},
                    expected_impact=pattern["strength"],
                    confidence=0.7,
                    rationale="Reinforcing successful performance pattern",
                    timestamp=datetime.now()
                )
            elif pattern["type"] == "decreasing_performance":
                # Adjust parameters to reverse trend
                return LearningAction(
                    action_type="reverse_trend",
                    component_target=pattern["component"],
                    parameter_adjustments={"correction_factor": -0.1 * pattern["strength"]},
                    expected_impact=pattern["strength"],
                    confidence=0.6,
                    rationale="Correcting declining performance pattern",
                    timestamp=datetime.now()
                )
        except Exception as e:
            logger.warning(f"Pattern to action conversion failed: {e}")
        
        return None
    
    async def update_parameters(self, component_type: WINAComponentType, 
                               current_params: Dict[str, float]) -> Dict[str, float]:
        """Update parameters based on recognized patterns."""
        return current_params  # Pattern recognition primarily generates actions


class WINAContinuousLearningSystem:
    """
    Centralized continuous learning system for WINA optimization.
    
    Coordinates learning across all WINA components, processes feedback signals,
    and implements adaptive optimization strategies.
    """
    
    def __init__(self, config: Optional[WINAConfig] = None):
        """Initialize continuous learning system."""
        self.config = config
        self.learning_state = LearningState(
            current_phase=LearningPhase.EXPLORATION,
            strategy_in_use=LearningStrategy.HYBRID_MULTIMODAL,
            exploration_rate=0.1,
            learning_rate=0.01,
            convergence_threshold=0.01,
            performance_trend=[],
            last_significant_change=datetime.now(),
            component_states={}
        )
        
        # Learning algorithms
        self.algorithms: Dict[LearningStrategy, LearningAlgorithm] = {
            LearningStrategy.REINFORCEMENT_LEARNING: ReinforcementLearningAlgorithm(),
            LearningStrategy.PATTERN_RECOGNITION: PatternRecognitionAlgorithm()
        }
        
        # Component profiles
        self.component_profiles: Dict[WINAComponentType, ComponentLearningProfile] = {}
        
        # Feedback processing
        self.feedback_queue: asyncio.Queue = asyncio.Queue()
        self.feedback_history: deque = deque(maxlen=10000)
        self.learning_actions_history: deque = deque(maxlen=1000)
        
        # Performance tracking
        self.performance_collector: Optional[WINAPerformanceCollector] = None
        
        # Learning metrics
        self.learning_metrics = {
            "total_feedback_processed": 0,
            "learning_actions_generated": 0,
            "successful_adaptations": 0,
            "failed_adaptations": 0,
            "average_performance_improvement": 0.0,
            "convergence_events": 0
        }
        
        # Initialize component profiles
        self._initialize_component_profiles()
        
        logger.info("WINA Continuous Learning System initialized")
    
    def _initialize_component_profiles(self):
        """Initialize learning profiles for all WINA components."""
        for component_type in WINAComponentType:
            if component_type in [WINAComponentType.NEURON_ACTIVATION, 
                                WINAComponentType.SVD_TRANSFORMATION,
                                WINAComponentType.DYNAMIC_GATING,
                                WINAComponentType.CONSTITUTIONAL_VERIFICATION]:
                
                # Component-specific parameter bounds
                if component_type == WINAComponentType.NEURON_ACTIVATION:
                    bounds = {
                        "activation_threshold": (0.1, 0.9),
                        "importance_threshold": (0.0, 1.0),
                        "efficiency_target": (0.4, 0.7)
                    }
                    optimal = {
                        "activation_threshold": 0.5,
                        "importance_threshold": 0.3,
                        "efficiency_target": 0.55
                    }
                elif component_type == WINAComponentType.SVD_TRANSFORMATION:
                    bounds = {
                        "rank_threshold": (0.1, 0.95),
                        "compression_ratio": (0.2, 0.8),
                        "accuracy_preservation": (0.95, 1.0)
                    }
                    optimal = {
                        "rank_threshold": 0.7,
                        "compression_ratio": 0.5,
                        "accuracy_preservation": 0.97
                    }
                elif component_type == WINAComponentType.DYNAMIC_GATING:
                    bounds = {
                        "gating_threshold": (0.2, 0.8),
                        "adaptive_rate": (0.01, 0.1),
                        "response_time": (1.0, 100.0)
                    }
                    optimal = {
                        "gating_threshold": 0.5,
                        "adaptive_rate": 0.05,
                        "response_time": 10.0
                    }
                else:  # Constitutional verification
                    bounds = {
                        "compliance_threshold": (0.8, 1.0),
                        "verification_depth": (0.5, 1.0),
                        "update_frequency": (0.1, 1.0)
                    }
                    optimal = {
                        "compliance_threshold": 0.9,
                        "verification_depth": 0.8,
                        "update_frequency": 0.5
                    }
                
                self.component_profiles[component_type] = ComponentLearningProfile(
                    component_type=component_type,
                    optimal_parameters=optimal,
                    parameter_bounds=bounds,
                    learning_history=[],
                    adaptation_rate=0.1,
                    stability_score=1.0,
                    last_update=datetime.now(),
                    performance_baseline=0.5
                )
    
    async def start_learning_loop(self):
        """Start the continuous learning loop."""
        logger.info("Starting WINA continuous learning loop")
        
        # Start feedback processing task
        asyncio.create_task(self._feedback_processing_loop())
        
        # Start periodic learning adaptation
        asyncio.create_task(self._adaptation_loop())
        
        # Start performance monitoring integration
        asyncio.create_task(self._performance_monitoring_loop())
    
    async def process_feedback_signal(self, feedback: FeedbackSignal):
        """Process a single feedback signal."""
        try:
            await self.feedback_queue.put(feedback)
            self.learning_metrics["total_feedback_processed"] += 1
            logger.debug(f"Feedback signal queued: {feedback.feedback_type.value} for {feedback.component_type.value}")
        except Exception as e:
            logger.error(f"Failed to process feedback signal: {e}")
    
    async def _feedback_processing_loop(self):
        """Main feedback processing loop."""
        batch_size = 10
        batch_timeout = 1.0  # seconds
        
        while True:
            try:
                feedback_batch = []
                
                # Collect batch of feedback signals
                try:
                    # Get first signal with timeout
                    first_signal = await asyncio.wait_for(
                        self.feedback_queue.get(), timeout=batch_timeout
                    )
                    feedback_batch.append(first_signal)
                    
                    # Collect additional signals without blocking
                    for _ in range(batch_size - 1):
                        try:
                            signal = self.feedback_queue.get_nowait()
                            feedback_batch.append(signal)
                        except asyncio.QueueEmpty:
                            break
                
                except asyncio.TimeoutError:
                    continue  # No feedback to process
                
                if feedback_batch:
                    # Process batch with all algorithms
                    await self._process_feedback_batch(feedback_batch)
                    
                    # Store in history
                    self.feedback_history.extend(feedback_batch)
            
            except Exception as e:
                logger.error(f"Feedback processing loop error: {e}")
                await asyncio.sleep(1)  # Prevent tight error loop
    
    async def _process_feedback_batch(self, feedback_batch: List[FeedbackSignal]):
        """Process a batch of feedback signals."""
        try:
            all_actions = []
            
            # Process with each learning algorithm
            for strategy, algorithm in self.algorithms.items():
                try:
                    actions = await algorithm.process_feedback(feedback_batch)
                    all_actions.extend(actions)
                except Exception as e:
                    logger.warning(f"Algorithm {strategy.value} failed: {e}")
            
            # Execute learning actions
            for action in all_actions:
                await self._execute_learning_action(action)
                self.learning_actions_history.append(action)
                self.learning_metrics["learning_actions_generated"] += 1
            
            # Update learning state
            await self._update_learning_state(feedback_batch, all_actions)
            
        except Exception as e:
            logger.error(f"Feedback batch processing failed: {e}")
    
    async def _execute_learning_action(self, action: LearningAction):
        """Execute a learning action."""
        try:
            component_profile = self.component_profiles.get(action.component_target)
            if not component_profile:
                logger.warning(f"No profile found for component {action.component_target}")
                return
            
            # Apply parameter adjustments within bounds
            updated_params = component_profile.optimal_parameters.copy()
            
            for param, adjustment in action.parameter_adjustments.items():
                if param in updated_params:
                    current_value = updated_params[param]
                    new_value = current_value + adjustment
                    
                    # Apply bounds
                    if param in component_profile.parameter_bounds:
                        min_val, max_val = component_profile.parameter_bounds[param]
                        new_value = max(min_val, min(max_val, new_value))
                    
                    updated_params[param] = new_value
            
            # Update component profile
            component_profile.optimal_parameters = updated_params
            component_profile.last_update = datetime.now()
            
            # Record in learning history
            performance_estimate = action.expected_impact
            component_profile.learning_history.append((updated_params.copy(), performance_estimate))
            
            # Keep history manageable
            if len(component_profile.learning_history) > 100:
                component_profile.learning_history = component_profile.learning_history[-50:]
            
            logger.debug(f"Learning action executed for {action.component_target.value}: {action.rationale}")
            
            # Record metrics if performance monitoring available
            if self.performance_collector:
                learning_metrics = WINALearningFeedbackMetrics(
                    component_type=action.component_target,
                    feedback_processed=1,
                    learning_actions_taken=1,
                    parameter_updates=len(action.parameter_adjustments),
                    performance_improvement=action.expected_impact,
                    adaptation_success_rate=action.confidence,
                    learning_convergence=0.5,  # Placeholder
                    strategy_effectiveness=action.confidence,
                    feedback_quality=0.8  # Placeholder
                )
                await self.performance_collector.record_learning_feedback_metrics(learning_metrics)
            
            self.learning_metrics["successful_adaptations"] += 1
            
        except Exception as e:
            logger.error(f"Failed to execute learning action: {e}")
            self.learning_metrics["failed_adaptations"] += 1
    
    async def _update_learning_state(self, feedback_batch: List[FeedbackSignal], actions: List[LearningAction]):
        """Update the overall learning state."""
        try:
            # Calculate current performance trend
            recent_performance = [signal.value for signal in feedback_batch 
                                if signal.feedback_type in [FeedbackType.EFFICIENCY_GAIN, 
                                                           FeedbackType.ACCURACY_RETENTION]]
            
            if recent_performance:
                avg_performance = sum(recent_performance) / len(recent_performance)
                self.learning_state.performance_trend.append(avg_performance)
                
                # Keep trend history manageable
                if len(self.learning_state.performance_trend) > 100:
                    self.learning_state.performance_trend = self.learning_state.performance_trend[-50:]
                
                # Update average performance improvement metric
                if len(self.learning_state.performance_trend) > 1:
                    improvement = (self.learning_state.performance_trend[-1] - 
                                 self.learning_state.performance_trend[0]) / len(self.learning_state.performance_trend)
                    self.learning_metrics["average_performance_improvement"] = improvement
            
            # Determine learning phase
            await self._update_learning_phase()
            
            # Adjust learning parameters
            await self._adjust_learning_parameters()
            
        except Exception as e:
            logger.warning(f"Learning state update failed: {e}")
    
    async def _update_learning_phase(self):
        """Update the current learning phase."""
        try:
            trend = self.learning_state.performance_trend
            
            if len(trend) < 10:
                self.learning_state.current_phase = LearningPhase.EXPLORATION
                return
            
            recent_trend = trend[-10:]
            variance = np.var(recent_trend) if len(recent_trend) > 1 else 1.0
            
            if variance < self.learning_state.convergence_threshold:
                if self.learning_state.current_phase != LearningPhase.CONVERGENCE:
                    self.learning_state.current_phase = LearningPhase.CONVERGENCE
                    self.learning_metrics["convergence_events"] += 1
            elif variance > 0.1:
                self.learning_state.current_phase = LearningPhase.EXPLORATION
            else:
                self.learning_state.current_phase = LearningPhase.EXPLOITATION
            
        except Exception as e:
            logger.warning(f"Learning phase update failed: {e}")
    
    async def _adjust_learning_parameters(self):
        """Adjust learning parameters based on current phase."""
        try:
            if self.learning_state.current_phase == LearningPhase.EXPLORATION:
                self.learning_state.exploration_rate = min(0.3, self.learning_state.exploration_rate + 0.01)
                self.learning_state.learning_rate = min(0.05, self.learning_state.learning_rate + 0.001)
            elif self.learning_state.current_phase == LearningPhase.EXPLOITATION:
                self.learning_state.exploration_rate = max(0.05, self.learning_state.exploration_rate - 0.01)
                self.learning_state.learning_rate = max(0.001, self.learning_state.learning_rate - 0.001)
            elif self.learning_state.current_phase == LearningPhase.CONVERGENCE:
                self.learning_state.exploration_rate = max(0.01, self.learning_state.exploration_rate - 0.02)
                self.learning_state.learning_rate = max(0.0001, self.learning_state.learning_rate - 0.002)
            
        except Exception as e:
            logger.warning(f"Learning parameter adjustment failed: {e}")
    
    async def _adaptation_loop(self):
        """Periodic adaptation and optimization loop."""
        adaptation_interval = 300  # 5 minutes
        
        while True:
            try:
                await asyncio.sleep(adaptation_interval)
                await self._perform_periodic_adaptation()
            except Exception as e:
                logger.error(f"Adaptation loop error: {e}")
    
    async def _perform_periodic_adaptation(self):
        """Perform periodic adaptation and optimization."""
        try:
            logger.info("Performing periodic WINA learning adaptation")
            
            # Analyze component performance
            for component_type, profile in self.component_profiles.items():
                await self._analyze_component_performance(component_type, profile)
            
            # Optimize learning strategy
            await self._optimize_learning_strategy()
            
            # Clean up old data
            await self._cleanup_learning_data()
            
        except Exception as e:
            logger.error(f"Periodic adaptation failed: {e}")
    
    async def _analyze_component_performance(self, component_type: WINAComponentType, 
                                           profile: ComponentLearningProfile):
        """Analyze performance of specific component."""
        try:
            if len(profile.learning_history) < 5:
                return
            
            # Calculate performance trend
            recent_performance = [perf for _, perf in profile.learning_history[-10:]]
            
            if len(recent_performance) > 1:
                trend = (recent_performance[-1] - recent_performance[0]) / len(recent_performance)
                
                # Update stability score
                variance = np.var(recent_performance)
                profile.stability_score = max(0.1, 1.0 - variance)
                
                # Adjust adaptation rate based on stability
                if profile.stability_score > 0.8:
                    profile.adaptation_rate = max(0.01, profile.adaptation_rate - 0.01)
                elif profile.stability_score < 0.5:
                    profile.adaptation_rate = min(0.2, profile.adaptation_rate + 0.02)
            
        except Exception as e:
            logger.warning(f"Component performance analysis failed for {component_type}: {e}")
    
    async def _optimize_learning_strategy(self):
        """Optimize the overall learning strategy."""
        try:
            # Analyze effectiveness of different strategies
            strategy_performance = {}
            
            for action in list(self.learning_actions_history)[-100:]:  # Recent actions
                strategy = "unknown"
                if "reinforcement" in action.rationale.lower():
                    strategy = LearningStrategy.REINFORCEMENT_LEARNING
                elif "pattern" in action.rationale.lower():
                    strategy = LearningStrategy.PATTERN_RECOGNITION
                
                if strategy != "unknown":
                    if strategy not in strategy_performance:
                        strategy_performance[strategy] = []
                    strategy_performance[strategy].append(action.expected_impact)
            
            # Select best performing strategy
            best_strategy = None
            best_performance = -float('inf')
            
            for strategy, performances in strategy_performance.items():
                avg_performance = sum(performances) / len(performances)
                if avg_performance > best_performance:
                    best_performance = avg_performance
                    best_strategy = strategy
            
            if best_strategy and best_strategy != self.learning_state.strategy_in_use:
                self.learning_state.strategy_in_use = best_strategy
                logger.info(f"Learning strategy optimized to: {best_strategy.value}")
            
        except Exception as e:
            logger.warning(f"Learning strategy optimization failed: {e}")
    
    async def _cleanup_learning_data(self):
        """Clean up old learning data to prevent memory issues."""
        try:
            # Clean up feedback history
            while len(self.feedback_history) > 5000:
                self.feedback_history.popleft()
            
            # Clean up action history
            while len(self.learning_actions_history) > 500:
                self.learning_actions_history.popleft()
            
            # Clean up component learning histories
            for profile in self.component_profiles.values():
                if len(profile.learning_history) > 50:
                    profile.learning_history = profile.learning_history[-25:]
            
        except Exception as e:
            logger.warning(f"Learning data cleanup failed: {e}")
    
    async def _performance_monitoring_loop(self):
        """Integration loop with performance monitoring system."""
        monitoring_interval = 60  # 1 minute
        
        while True:
            try:
                await asyncio.sleep(monitoring_interval)
                
                if self.performance_collector:
                    # Generate synthetic feedback from performance data
                    await self._generate_performance_feedback()
                
            except Exception as e:
                logger.error(f"Performance monitoring loop error: {e}")
    
    async def _generate_performance_feedback(self):
        """Generate feedback signals from performance monitoring data."""
        try:
            # This would integrate with actual performance monitoring
            # For now, generating representative feedback signals
            
            for component_type in [WINAComponentType.NEURON_ACTIVATION,
                                 WINAComponentType.SVD_TRANSFORMATION,
                                 WINAComponentType.DYNAMIC_GATING]:
                
                # Simulate performance metrics
                efficiency = np.random.normal(0.55, 0.1)  # Target 40-70% range
                accuracy = np.random.normal(0.96, 0.02)   # Target >95%
                
                # Create feedback signals
                efficiency_feedback = FeedbackSignal(
                    component_type=component_type,
                    feedback_type=FeedbackType.EFFICIENCY_GAIN,
                    value=efficiency,
                    context={"source": "performance_monitoring", "synthetic": True},
                    timestamp=datetime.now(),
                    confidence=0.8,
                    source="performance_monitor"
                )
                
                accuracy_feedback = FeedbackSignal(
                    component_type=component_type,
                    feedback_type=FeedbackType.ACCURACY_RETENTION,
                    value=accuracy,
                    context={"source": "performance_monitoring", "synthetic": True},
                    timestamp=datetime.now(),
                    confidence=0.9,
                    source="performance_monitor"
                )
                
                await self.process_feedback_signal(efficiency_feedback)
                await self.process_feedback_signal(accuracy_feedback)
        
        except Exception as e:
            logger.warning(f"Performance feedback generation failed: {e}")
    
    async def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning system status."""
        try:
            status = {
                "learning_state": {
                    "current_phase": self.learning_state.current_phase.value,
                    "strategy_in_use": self.learning_state.strategy_in_use.value,
                    "exploration_rate": self.learning_state.exploration_rate,
                    "learning_rate": self.learning_state.learning_rate
                },
                "metrics": self.learning_metrics.copy(),
                "component_profiles": {},
                "recent_actions": len(self.learning_actions_history),
                "feedback_queue_size": self.feedback_queue.qsize()
            }
            
            # Add component profile summaries
            for component_type, profile in self.component_profiles.items():
                status["component_profiles"][component_type.value] = {
                    "optimal_parameters": profile.optimal_parameters,
                    "stability_score": profile.stability_score,
                    "adaptation_rate": profile.adaptation_rate,
                    "last_update": profile.last_update.isoformat(),
                    "learning_history_size": len(profile.learning_history)
                }
            
            return status
        
        except Exception as e:
            logger.error(f"Failed to get learning status: {e}")
            return {"error": str(e)}
    
    async def get_component_recommendations(self, component_type: WINAComponentType) -> Dict[str, Any]:
        """Get optimization recommendations for specific component."""
        try:
            profile = self.component_profiles.get(component_type)
            if not profile:
                return {"error": "Component profile not found"}
            
            recommendations = {
                "component_type": component_type.value,
                "current_parameters": profile.optimal_parameters,
                "parameter_bounds": profile.parameter_bounds,
                "stability_score": profile.stability_score,
                "adaptation_rate": profile.adaptation_rate,
                "recommendations": []
            }
            
            # Generate recommendations based on learning history
            if len(profile.learning_history) > 5:
                recent_performance = [perf for _, perf in profile.learning_history[-5:]]
                avg_performance = sum(recent_performance) / len(recent_performance)
                
                if avg_performance < profile.performance_baseline:
                    recommendations["recommendations"].append({
                        "type": "performance_improvement",
                        "priority": "high",
                        "description": "Recent performance below baseline - consider parameter adjustment",
                        "suggested_action": "Increase adaptation rate or adjust thresholds"
                    })
                
                if profile.stability_score < 0.6:
                    recommendations["recommendations"].append({
                        "type": "stability_improvement",
                        "priority": "medium", 
                        "description": "Low stability detected - reduce learning volatility",
                        "suggested_action": "Decrease adaptation rate and exploration"
                    })
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Failed to get component recommendations: {e}")
            return {"error": str(e)}
    
    def set_performance_collector(self, collector: WINAPerformanceCollector):
        """Set the performance collector for integration."""
        self.performance_collector = collector
        logger.info("Performance collector integrated with learning system")


# Global learning system instance
_wina_learning_system: Optional[WINAContinuousLearningSystem] = None


async def get_wina_learning_system(config: Optional[WINAConfig] = None) -> WINAContinuousLearningSystem:
    """Get or create the global WINA learning system instance."""
    global _wina_learning_system
    
    if _wina_learning_system is None:
        _wina_learning_system = WINAContinuousLearningSystem(config)
        await _wina_learning_system.start_learning_loop()
        logger.info("WINA Continuous Learning System instance created and started")
    
    return _wina_learning_system


async def close_wina_learning_system():
    """Close the global WINA learning system."""
    global _wina_learning_system
    if _wina_learning_system:
        # Perform cleanup if needed
        _wina_learning_system = None
        logger.info("WINA Continuous Learning System instance closed")


# Utility functions for easy integration

async def process_efficiency_feedback(component_type: WINAComponentType, efficiency_value: float, 
                                    context: Optional[Dict[str, Any]] = None):
    """Convenience function to process efficiency feedback."""
    learning_system = await get_wina_learning_system()
    
    feedback = FeedbackSignal(
        component_type=component_type,
        feedback_type=FeedbackType.EFFICIENCY_GAIN,
        value=efficiency_value,
        context=context or {},
        timestamp=datetime.now()
    )
    
    await learning_system.process_feedback_signal(feedback)


async def process_accuracy_feedback(component_type: WINAComponentType, accuracy_value: float,
                                  context: Optional[Dict[str, Any]] = None):
    """Convenience function to process accuracy retention feedback."""
    learning_system = await get_wina_learning_system()
    
    feedback = FeedbackSignal(
        component_type=component_type,
        feedback_type=FeedbackType.ACCURACY_RETENTION,
        value=accuracy_value,
        context=context or {},
        timestamp=datetime.now()
    )
    
    await learning_system.process_feedback_signal(feedback)


async def process_constitutional_feedback(compliance_score: float, 
                                        context: Optional[Dict[str, Any]] = None):
    """Convenience function to process constitutional compliance feedback."""
    learning_system = await get_wina_learning_system()
    
    feedback = FeedbackSignal(
        component_type=WINAComponentType.CONSTITUTIONAL_VERIFICATION,
        feedback_type=FeedbackType.CONSTITUTIONAL_COMPLIANCE,
        value=compliance_score,
        context=context or {},
        timestamp=datetime.now()
    )
    
    await learning_system.process_feedback_signal(feedback)
