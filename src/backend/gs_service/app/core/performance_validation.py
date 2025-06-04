"""
Performance Validation System for MAB Prompt Optimization

Validates 25% quality improvement target and convergence within 100 iterations.
Provides real-time monitoring and benchmarking capabilities.
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ConvergenceStatus(Enum):
    """Convergence status for MAB optimization."""
    NOT_STARTED = "not_started"
    CONVERGING = "converging"
    CONVERGED = "converged"
    DIVERGING = "diverging"
    STALLED = "stalled"


class PerformanceTarget(Enum):
    """Performance improvement targets."""
    QUALITY_IMPROVEMENT_25_PERCENT = 0.25
    CONVERGENCE_100_ITERATIONS = 100
    RELIABILITY_99_9_PERCENT = 0.999


@dataclass
class PerformanceBaseline:
    """Baseline performance metrics for comparison."""
    baseline_id: str
    baseline_name: str
    created_at: datetime
    
    # Baseline metrics
    average_reward: float
    success_rate: float
    response_time_ms: float
    reliability_score: float
    
    # Sample information
    sample_count: int
    measurement_period_hours: float
    
    # Context
    context_category: str
    measurement_conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a specific point in time."""
    timestamp: datetime
    iteration: int
    
    # Current metrics
    average_reward: float
    success_rate: float
    response_time_ms: float
    reliability_score: float
    
    # Improvement metrics
    improvement_percentage: float
    improvement_from_baseline: float
    
    # Convergence indicators
    reward_variance: float
    selection_entropy: float  # Diversity of template selection
    convergence_score: float  # 0-1 score indicating convergence


@dataclass
class ConvergenceAnalysis:
    """Analysis of convergence behavior."""
    status: ConvergenceStatus
    convergence_iteration: Optional[int]
    convergence_confidence: float  # 0-1 confidence in convergence
    
    # Convergence metrics
    reward_stability: float  # How stable rewards are
    selection_stability: float  # How stable template selection is
    improvement_rate: float  # Rate of improvement per iteration
    
    # Trend analysis
    trend_direction: str  # "improving", "stable", "declining"
    trend_strength: float  # 0-1 strength of trend
    
    # Predictions
    predicted_convergence_iteration: Optional[int]
    predicted_final_performance: float


class PerformanceValidator:
    """Performance validation system for MAB optimization."""
    
    def __init__(self, target_improvement: float = 0.25, target_iterations: int = 100):
        self.target_improvement = target_improvement
        self.target_iterations = target_iterations
        
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.performance_history: List[PerformanceSnapshot] = []
        self.convergence_analysis: Optional[ConvergenceAnalysis] = None
        
        # Tracking variables
        self.current_iteration = 0
        self.start_time = datetime.now(timezone.utc)
        self.last_analysis_iteration = 0
        
        logger.info(f"Initialized Performance Validator: target_improvement={target_improvement:.1%}, "
                   f"target_iterations={target_iterations}")
    
    def set_baseline(
        self,
        baseline_id: str,
        baseline_name: str,
        average_reward: float,
        success_rate: float,
        response_time_ms: float,
        reliability_score: float,
        sample_count: int,
        context_category: str = "general",
        measurement_conditions: Dict[str, Any] = None
    ):
        """Set performance baseline for comparison."""
        baseline = PerformanceBaseline(
            baseline_id=baseline_id,
            baseline_name=baseline_name,
            created_at=datetime.now(timezone.utc),
            average_reward=average_reward,
            success_rate=success_rate,
            response_time_ms=response_time_ms,
            reliability_score=reliability_score,
            sample_count=sample_count,
            measurement_period_hours=0.0,  # Will be calculated
            context_category=context_category,
            measurement_conditions=measurement_conditions or {}
        )
        
        self.baselines[baseline_id] = baseline
        logger.info(f"Set baseline '{baseline_name}': avg_reward={average_reward:.3f}, "
                   f"success_rate={success_rate:.3f}")
    
    async def record_performance(
        self,
        average_reward: float,
        success_rate: float,
        response_time_ms: float,
        reliability_score: float,
        template_selection_counts: Dict[str, int],
        baseline_id: str = None
    ):
        """Record current performance metrics."""
        self.current_iteration += 1
        
        # Calculate improvement metrics
        improvement_percentage = 0.0
        improvement_from_baseline = 0.0
        
        if baseline_id and baseline_id in self.baselines:
            baseline = self.baselines[baseline_id]
            if baseline.average_reward > 0:
                improvement_from_baseline = (
                    (average_reward - baseline.average_reward) / baseline.average_reward
                )
                improvement_percentage = improvement_from_baseline * 100
        
        # Calculate convergence indicators
        reward_variance = self._calculate_reward_variance()
        selection_entropy = self._calculate_selection_entropy(template_selection_counts)
        convergence_score = self._calculate_convergence_score(
            reward_variance, selection_entropy
        )
        
        # Create performance snapshot
        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(timezone.utc),
            iteration=self.current_iteration,
            average_reward=average_reward,
            success_rate=success_rate,
            response_time_ms=response_time_ms,
            reliability_score=reliability_score,
            improvement_percentage=improvement_percentage,
            improvement_from_baseline=improvement_from_baseline,
            reward_variance=reward_variance,
            selection_entropy=selection_entropy,
            convergence_score=convergence_score
        )
        
        self.performance_history.append(snapshot)
        
        # Perform convergence analysis every 10 iterations
        if self.current_iteration % 10 == 0:
            await self._analyze_convergence()
        
        logger.debug(f"Recorded performance iteration {self.current_iteration}: "
                    f"reward={average_reward:.3f}, improvement={improvement_percentage:.1f}%")
    
    def _calculate_reward_variance(self, window_size: int = 20) -> float:
        """Calculate variance in recent rewards."""
        if len(self.performance_history) < 2:
            return 1.0  # High variance initially
        
        recent_rewards = [
            snapshot.average_reward 
            for snapshot in self.performance_history[-window_size:]
        ]
        
        return float(np.var(recent_rewards))
    
    def _calculate_selection_entropy(self, selection_counts: Dict[str, int]) -> float:
        """Calculate entropy of template selection (diversity measure)."""
        if not selection_counts:
            return 0.0
        
        total_selections = sum(selection_counts.values())
        if total_selections == 0:
            return 0.0
        
        # Calculate Shannon entropy
        entropy = 0.0
        for count in selection_counts.values():
            if count > 0:
                probability = count / total_selections
                entropy -= probability * np.log2(probability)
        
        # Normalize by maximum possible entropy
        max_entropy = np.log2(len(selection_counts))
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _calculate_convergence_score(
        self, 
        reward_variance: float, 
        selection_entropy: float
    ) -> float:
        """Calculate overall convergence score (0-1, higher = more converged)."""
        # Low variance and low entropy indicate convergence
        variance_score = max(0.0, 1.0 - reward_variance * 10)  # Scale variance
        entropy_score = 1.0 - selection_entropy  # Low entropy = high convergence
        
        # Weighted combination
        convergence_score = 0.7 * variance_score + 0.3 * entropy_score
        return max(0.0, min(1.0, convergence_score))
    
    async def _analyze_convergence(self):
        """Analyze convergence behavior and update convergence analysis."""
        if len(self.performance_history) < 10:
            return
        
        # Get recent performance data
        recent_snapshots = self.performance_history[-20:]  # Last 20 iterations
        
        # Calculate stability metrics
        reward_stability = self._calculate_stability([s.average_reward for s in recent_snapshots])
        selection_stability = self._calculate_stability([s.selection_entropy for s in recent_snapshots])
        
        # Calculate improvement rate
        improvement_rate = self._calculate_improvement_rate(recent_snapshots)
        
        # Determine convergence status
        convergence_status = self._determine_convergence_status(
            reward_stability, selection_stability, improvement_rate
        )
        
        # Find convergence iteration if converged
        convergence_iteration = None
        convergence_confidence = 0.0
        
        if convergence_status == ConvergenceStatus.CONVERGED:
            convergence_iteration, convergence_confidence = self._find_convergence_point()
        
        # Trend analysis
        trend_direction, trend_strength = self._analyze_trend(recent_snapshots)
        
        # Predictions
        predicted_convergence_iteration = self._predict_convergence_iteration()
        predicted_final_performance = self._predict_final_performance()
        
        # Update convergence analysis
        self.convergence_analysis = ConvergenceAnalysis(
            status=convergence_status,
            convergence_iteration=convergence_iteration,
            convergence_confidence=convergence_confidence,
            reward_stability=reward_stability,
            selection_stability=selection_stability,
            improvement_rate=improvement_rate,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            predicted_convergence_iteration=predicted_convergence_iteration,
            predicted_final_performance=predicted_final_performance
        )
        
        self.last_analysis_iteration = self.current_iteration
        
        logger.info(f"Convergence analysis (iteration {self.current_iteration}): "
                   f"status={convergence_status.value}, "
                   f"reward_stability={reward_stability:.3f}, "
                   f"improvement_rate={improvement_rate:.3f}")
    
    def _calculate_stability(self, values: List[float]) -> float:
        """Calculate stability score (0-1, higher = more stable)."""
        if len(values) < 2:
            return 0.0
        
        # Use coefficient of variation (CV) as stability measure
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if mean_val == 0:
            return 0.0
        
        cv = std_val / abs(mean_val)
        # Convert to stability score (lower CV = higher stability)
        stability = max(0.0, 1.0 - cv)
        return min(1.0, stability)
    
    def _calculate_improvement_rate(self, snapshots: List[PerformanceSnapshot]) -> float:
        """Calculate rate of improvement per iteration."""
        if len(snapshots) < 2:
            return 0.0
        
        # Linear regression on rewards over iterations
        iterations = [s.iteration for s in snapshots]
        rewards = [s.average_reward for s in snapshots]
        
        # Calculate slope (improvement rate)
        n = len(iterations)
        sum_x = sum(iterations)
        sum_y = sum(rewards)
        sum_xy = sum(x * y for x, y in zip(iterations, rewards))
        sum_x2 = sum(x * x for x in iterations)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    def _determine_convergence_status(
        self, 
        reward_stability: float, 
        selection_stability: float, 
        improvement_rate: float
    ) -> ConvergenceStatus:
        """Determine convergence status based on stability metrics."""
        # Thresholds for convergence
        stability_threshold = 0.8
        improvement_threshold = 0.001  # Very small improvement rate
        
        if reward_stability > stability_threshold and selection_stability > stability_threshold:
            if abs(improvement_rate) < improvement_threshold:
                return ConvergenceStatus.CONVERGED
            elif improvement_rate > 0:
                return ConvergenceStatus.CONVERGING
            else:
                return ConvergenceStatus.STALLED
        elif improvement_rate < -0.01:  # Significant decline
            return ConvergenceStatus.DIVERGING
        else:
            return ConvergenceStatus.CONVERGING
    
    def _find_convergence_point(self) -> Tuple[Optional[int], float]:
        """Find the iteration where convergence occurred."""
        if len(self.performance_history) < 20:
            return None, 0.0
        
        # Look for point where variance becomes consistently low
        window_size = 10
        variance_threshold = 0.01
        
        for i in range(window_size, len(self.performance_history)):
            window_rewards = [
                s.average_reward 
                for s in self.performance_history[i-window_size:i]
            ]
            variance = np.var(window_rewards)
            
            if variance < variance_threshold:
                confidence = min(1.0, (len(self.performance_history) - i) / 20)
                return self.performance_history[i].iteration, confidence
        
        return None, 0.0
    
    def _analyze_trend(self, snapshots: List[PerformanceSnapshot]) -> Tuple[str, float]:
        """Analyze performance trend."""
        if len(snapshots) < 3:
            return "stable", 0.0
        
        # Calculate trend using linear regression
        rewards = [s.average_reward for s in snapshots]
        slope = self._calculate_improvement_rate(snapshots)
        
        # Determine trend direction and strength
        if slope > 0.01:
            direction = "improving"
            strength = min(1.0, slope * 100)
        elif slope < -0.01:
            direction = "declining"
            strength = min(1.0, abs(slope) * 100)
        else:
            direction = "stable"
            strength = 1.0 - abs(slope) * 100
        
        return direction, max(0.0, strength)
    
    def _predict_convergence_iteration(self) -> Optional[int]:
        """Predict when convergence will occur."""
        if not self.convergence_analysis or len(self.performance_history) < 10:
            return None
        
        if self.convergence_analysis.status == ConvergenceStatus.CONVERGED:
            return self.convergence_analysis.convergence_iteration
        
        # Simple prediction based on improvement rate
        improvement_rate = self.convergence_analysis.improvement_rate
        if improvement_rate <= 0:
            return None
        
        # Estimate iterations needed to reach stability
        current_variance = self.performance_history[-1].reward_variance
        target_variance = 0.01
        
        if current_variance <= target_variance:
            return self.current_iteration
        
        # Rough estimate
        iterations_needed = int((current_variance - target_variance) / max(improvement_rate, 0.001))
        predicted_iteration = self.current_iteration + iterations_needed
        
        return min(predicted_iteration, self.target_iterations)
    
    def _predict_final_performance(self) -> float:
        """Predict final performance level."""
        if len(self.performance_history) < 5:
            return 0.0
        
        # Use trend to predict final performance
        recent_snapshots = self.performance_history[-10:]
        improvement_rate = self._calculate_improvement_rate(recent_snapshots)
        current_performance = self.performance_history[-1].average_reward
        
        # Predict performance at target iterations
        remaining_iterations = max(0, self.target_iterations - self.current_iteration)
        predicted_improvement = improvement_rate * remaining_iterations
        
        # Apply diminishing returns
        diminishing_factor = 0.8  # Improvement rate decreases over time
        adjusted_improvement = predicted_improvement * diminishing_factor
        
        predicted_performance = current_performance + adjusted_improvement
        return max(0.0, min(1.0, predicted_performance))
    
    def check_performance_targets(self, baseline_id: str = None) -> Dict[str, Any]:
        """Check if performance targets are being met."""
        if not self.performance_history:
            return {"status": "no_data"}
        
        current_snapshot = self.performance_history[-1]
        
        # Check 25% improvement target
        improvement_target_met = False
        improvement_progress = 0.0
        
        if baseline_id and baseline_id in self.baselines:
            improvement_progress = current_snapshot.improvement_from_baseline
            improvement_target_met = improvement_progress >= self.target_improvement
        
        # Check 100 iteration convergence target
        convergence_target_met = False
        convergence_progress = 0.0
        
        if self.convergence_analysis:
            if self.convergence_analysis.status == ConvergenceStatus.CONVERGED:
                convergence_target_met = (
                    self.convergence_analysis.convergence_iteration and
                    self.convergence_analysis.convergence_iteration <= self.target_iterations
                )
            convergence_progress = min(1.0, self.current_iteration / self.target_iterations)
        
        return {
            "status": "active",
            "current_iteration": self.current_iteration,
            "targets": {
                "improvement_25_percent": {
                    "target": self.target_improvement,
                    "current": improvement_progress,
                    "met": improvement_target_met,
                    "progress_percentage": min(100.0, improvement_progress / self.target_improvement * 100)
                },
                "convergence_100_iterations": {
                    "target": self.target_iterations,
                    "current": self.current_iteration,
                    "met": convergence_target_met,
                    "progress_percentage": convergence_progress * 100
                }
            },
            "convergence_analysis": {
                "status": self.convergence_analysis.status.value if self.convergence_analysis else "not_analyzed",
                "confidence": self.convergence_analysis.convergence_confidence if self.convergence_analysis else 0.0,
                "predicted_convergence": self.convergence_analysis.predicted_convergence_iteration if self.convergence_analysis else None,
                "predicted_performance": self.convergence_analysis.predicted_final_performance if self.convergence_analysis else 0.0
            },
            "current_performance": {
                "average_reward": current_snapshot.average_reward,
                "success_rate": current_snapshot.success_rate,
                "improvement_percentage": current_snapshot.improvement_percentage
            }
        }
    
    def export_performance_report(self) -> Dict[str, Any]:
        """Export comprehensive performance report."""
        if not self.performance_history:
            return {"error": "No performance data available"}
        
        # Calculate summary statistics
        rewards = [s.average_reward for s in self.performance_history]
        success_rates = [s.success_rate for s in self.performance_history]
        
        summary_stats = {
            "total_iterations": len(self.performance_history),
            "average_reward": {
                "mean": float(np.mean(rewards)),
                "std": float(np.std(rewards)),
                "min": float(np.min(rewards)),
                "max": float(np.max(rewards))
            },
            "success_rate": {
                "mean": float(np.mean(success_rates)),
                "std": float(np.std(success_rates)),
                "min": float(np.min(success_rates)),
                "max": float(np.max(success_rates))
            }
        }
        
        return {
            "report_generated": datetime.now(timezone.utc).isoformat(),
            "validation_period": {
                "start_time": self.start_time.isoformat(),
                "duration_hours": (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600
            },
            "summary_statistics": summary_stats,
            "performance_targets": self.check_performance_targets(),
            "convergence_analysis": self.convergence_analysis.__dict__ if self.convergence_analysis else None,
            "baselines": {
                baseline_id: {
                    "name": baseline.baseline_name,
                    "average_reward": baseline.average_reward,
                    "success_rate": baseline.success_rate,
                    "sample_count": baseline.sample_count
                }
                for baseline_id, baseline in self.baselines.items()
            },
            "performance_history": [
                {
                    "iteration": s.iteration,
                    "timestamp": s.timestamp.isoformat(),
                    "average_reward": s.average_reward,
                    "success_rate": s.success_rate,
                    "improvement_percentage": s.improvement_percentage,
                    "convergence_score": s.convergence_score
                }
                for s in self.performance_history[-50:]  # Last 50 iterations
            ]
        }
