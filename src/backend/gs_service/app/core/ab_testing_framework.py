"""
A/B Testing Framework for MAB Prompt Optimization

Implements statistical significance testing, performance comparison,
and A/B test result tracking for prompt template optimization.
"""

import asyncio
import logging
import numpy as np
import scipy.stats as stats
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ABTestStatus(Enum):
    """A/B test status."""
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


class StatisticalSignificance(Enum):
    """Statistical significance levels."""
    NOT_SIGNIFICANT = "not_significant"
    MARGINALLY_SIGNIFICANT = "marginally_significant"  # p < 0.1
    SIGNIFICANT = "significant"  # p < 0.05
    HIGHLY_SIGNIFICANT = "highly_significant"  # p < 0.01


@dataclass
class ABTestConfig:
    """Configuration for A/B testing."""
    significance_level: float = 0.05  # Alpha level for statistical tests
    minimum_sample_size: int = 30  # Minimum samples per variant
    maximum_duration_hours: int = 24  # Maximum test duration
    effect_size_threshold: float = 0.1  # Minimum meaningful effect size
    power: float = 0.8  # Statistical power
    early_stopping_enabled: bool = True
    confidence_level: float = 0.95


@dataclass
class ABTestVariant:
    """A/B test variant (prompt template)."""
    variant_id: str
    template_id: str
    template_name: str
    allocation_percentage: float  # Percentage of traffic
    
    # Performance metrics
    sample_count: int = 0
    total_reward: float = 0.0
    rewards: List[float] = field(default_factory=list)
    success_count: int = 0
    
    # Calculated metrics
    mean_reward: float = 0.0
    std_reward: float = 0.0
    success_rate: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 1.0)


@dataclass
class ABTestResult:
    """A/B test statistical results."""
    test_id: str
    status: ABTestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Statistical results
    p_value: float = 1.0
    effect_size: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    significance: StatisticalSignificance = StatisticalSignificance.NOT_SIGNIFICANT
    
    # Winner information
    winning_variant_id: Optional[str] = None
    improvement_percentage: float = 0.0
    
    # Test metadata
    total_samples: int = 0
    test_duration_hours: float = 0.0
    early_stopped: bool = False
    
    # Detailed results
    variants: Dict[str, ABTestVariant] = field(default_factory=dict)
    statistical_details: Dict[str, Any] = field(default_factory=dict)


class ABTestingFramework:
    """A/B Testing Framework for prompt optimization."""
    
    def __init__(self, config: ABTestConfig = None):
        self.config = config or ABTestConfig()
        self.active_tests: Dict[str, ABTestResult] = {}
        self.completed_tests: Dict[str, ABTestResult] = {}
        
        logger.info("Initialized A/B Testing Framework")
    
    def create_ab_test(
        self,
        test_id: str,
        template_variants: List[Tuple[str, str, float]],  # (template_id, name, allocation)
        test_config: ABTestConfig = None
    ) -> ABTestResult:
        """Create a new A/B test."""
        config = test_config or self.config
        
        # Validate allocations sum to 1.0
        total_allocation = sum(allocation for _, _, allocation in template_variants)
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError(f"Allocation percentages must sum to 1.0, got {total_allocation}")
        
        # Create test result
        test_result = ABTestResult(
            test_id=test_id,
            status=ABTestStatus.RUNNING,
            start_time=datetime.now(timezone.utc)
        )
        
        # Create variants
        for i, (template_id, template_name, allocation) in enumerate(template_variants):
            variant = ABTestVariant(
                variant_id=f"{test_id}_variant_{i}",
                template_id=template_id,
                template_name=template_name,
                allocation_percentage=allocation
            )
            test_result.variants[variant.variant_id] = variant
        
        self.active_tests[test_id] = test_result
        
        logger.info(f"Created A/B test '{test_id}' with {len(template_variants)} variants")
        return test_result
    
    def select_variant(self, test_id: str) -> Optional[str]:
        """Select a variant for the A/B test based on allocation."""
        if test_id not in self.active_tests:
            return None
        
        test_result = self.active_tests[test_id]
        if test_result.status != ABTestStatus.RUNNING:
            return None
        
        # Random selection based on allocation percentages
        rand_val = np.random.random()
        cumulative_allocation = 0.0
        
        for variant in test_result.variants.values():
            cumulative_allocation += variant.allocation_percentage
            if rand_val <= cumulative_allocation:
                return variant.template_id
        
        # Fallback to first variant
        return list(test_result.variants.values())[0].template_id
    
    async def record_result(
        self,
        test_id: str,
        template_id: str,
        reward: float,
        success: bool,
        context: Dict[str, Any] = None
    ):
        """Record a result for the A/B test."""
        if test_id not in self.active_tests:
            logger.warning(f"Test {test_id} not found")
            return
        
        test_result = self.active_tests[test_id]
        if test_result.status != ABTestStatus.RUNNING:
            return
        
        # Find the variant for this template
        variant = None
        for v in test_result.variants.values():
            if v.template_id == template_id:
                variant = v
                break
        
        if not variant:
            logger.warning(f"Variant for template {template_id} not found in test {test_id}")
            return
        
        # Update variant metrics
        variant.sample_count += 1
        variant.total_reward += reward
        variant.rewards.append(reward)
        if success:
            variant.success_count += 1
        
        # Recalculate metrics
        variant.mean_reward = variant.total_reward / variant.sample_count
        variant.std_reward = np.std(variant.rewards) if len(variant.rewards) > 1 else 0.0
        variant.success_rate = variant.success_count / variant.sample_count
        
        # Calculate confidence interval
        if variant.sample_count >= 2:
            sem = variant.std_reward / np.sqrt(variant.sample_count)
            margin = stats.t.ppf((1 + self.config.confidence_level) / 2, variant.sample_count - 1) * sem
            variant.confidence_interval = (
                max(0.0, variant.mean_reward - margin),
                min(1.0, variant.mean_reward + margin)
            )
        
        # Check if test should be analyzed
        await self._check_test_completion(test_id)
    
    async def _check_test_completion(self, test_id: str):
        """Check if A/B test should be completed."""
        test_result = self.active_tests[test_id]
        
        # Check minimum sample size
        min_samples_met = all(
            variant.sample_count >= self.config.minimum_sample_size
            for variant in test_result.variants.values()
        )
        
        if not min_samples_met:
            return
        
        # Check maximum duration
        duration_hours = (datetime.now(timezone.utc) - test_result.start_time).total_seconds() / 3600
        max_duration_reached = duration_hours >= self.config.maximum_duration_hours
        
        # Perform statistical analysis
        analysis_result = await self._perform_statistical_analysis(test_id)
        
        # Check for early stopping
        should_stop = False
        if self.config.early_stopping_enabled:
            should_stop = (
                analysis_result['significance'] == StatisticalSignificance.HIGHLY_SIGNIFICANT and
                analysis_result['effect_size'] >= self.config.effect_size_threshold
            )
        
        # Complete test if conditions are met
        if max_duration_reached or should_stop:
            await self._complete_test(test_id, early_stopped=should_stop)
    
    async def _perform_statistical_analysis(self, test_id: str) -> Dict[str, Any]:
        """Perform statistical analysis of A/B test results."""
        test_result = self.active_tests[test_id]
        variants = list(test_result.variants.values())
        
        if len(variants) != 2:
            # For now, only support two-variant tests
            return {
                'significance': StatisticalSignificance.NOT_SIGNIFICANT,
                'effect_size': 0.0,
                'p_value': 1.0
            }
        
        variant_a, variant_b = variants[0], variants[1]
        
        # Perform two-sample t-test
        if len(variant_a.rewards) < 2 or len(variant_b.rewards) < 2:
            return {
                'significance': StatisticalSignificance.NOT_SIGNIFICANT,
                'effect_size': 0.0,
                'p_value': 1.0
            }
        
        # Two-sample t-test
        t_stat, p_value = stats.ttest_ind(variant_a.rewards, variant_b.rewards)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(
            ((len(variant_a.rewards) - 1) * variant_a.std_reward ** 2 +
             (len(variant_b.rewards) - 1) * variant_b.std_reward ** 2) /
            (len(variant_a.rewards) + len(variant_b.rewards) - 2)
        )
        
        effect_size = abs(variant_a.mean_reward - variant_b.mean_reward) / pooled_std if pooled_std > 0 else 0.0
        
        # Determine significance level
        if p_value < 0.01:
            significance = StatisticalSignificance.HIGHLY_SIGNIFICANT
        elif p_value < 0.05:
            significance = StatisticalSignificance.SIGNIFICANT
        elif p_value < 0.1:
            significance = StatisticalSignificance.MARGINALLY_SIGNIFICANT
        else:
            significance = StatisticalSignificance.NOT_SIGNIFICANT
        
        return {
            'significance': significance,
            'effect_size': effect_size,
            'p_value': p_value,
            't_statistic': t_stat,
            'pooled_std': pooled_std
        }
    
    async def _complete_test(self, test_id: str, early_stopped: bool = False):
        """Complete an A/B test and determine the winner."""
        test_result = self.active_tests[test_id]
        test_result.status = ABTestStatus.COMPLETED
        test_result.end_time = datetime.now(timezone.utc)
        test_result.early_stopped = early_stopped
        
        # Calculate test duration
        test_result.test_duration_hours = (
            test_result.end_time - test_result.start_time
        ).total_seconds() / 3600
        
        # Perform final statistical analysis
        analysis = await self._perform_statistical_analysis(test_id)
        test_result.p_value = analysis['p_value']
        test_result.effect_size = analysis['effect_size']
        test_result.significance = analysis['significance']
        test_result.statistical_details = analysis
        
        # Determine winner
        best_variant = max(
            test_result.variants.values(),
            key=lambda v: v.mean_reward
        )
        
        test_result.winning_variant_id = best_variant.variant_id
        
        # Calculate improvement percentage
        variants = list(test_result.variants.values())
        if len(variants) == 2:
            other_variant = variants[1] if variants[0] == best_variant else variants[0]
            if other_variant.mean_reward > 0:
                test_result.improvement_percentage = (
                    (best_variant.mean_reward - other_variant.mean_reward) / other_variant.mean_reward * 100
                )
        
        # Calculate total samples
        test_result.total_samples = sum(v.sample_count for v in test_result.variants.values())
        
        # Move to completed tests
        self.completed_tests[test_id] = test_result
        del self.active_tests[test_id]
        
        logger.info(f"Completed A/B test '{test_id}': winner={best_variant.template_name}, "
                   f"improvement={test_result.improvement_percentage:.2f}%, "
                   f"significance={test_result.significance.value}")
    
    def get_test_results(self, test_id: str) -> Optional[ABTestResult]:
        """Get results for a specific test."""
        if test_id in self.active_tests:
            return self.active_tests[test_id]
        elif test_id in self.completed_tests:
            return self.completed_tests[test_id]
        return None
    
    def get_active_tests(self) -> Dict[str, ABTestResult]:
        """Get all active tests."""
        return self.active_tests.copy()
    
    def get_completed_tests(self) -> Dict[str, ABTestResult]:
        """Get all completed tests."""
        return self.completed_tests.copy()
    
    async def stop_test(self, test_id: str, reason: str = "Manual stop"):
        """Manually stop an active test."""
        if test_id in self.active_tests:
            test_result = self.active_tests[test_id]
            test_result.status = ABTestStatus.STOPPED
            test_result.end_time = datetime.now(timezone.utc)
            
            # Move to completed tests
            self.completed_tests[test_id] = test_result
            del self.active_tests[test_id]
            
            logger.info(f"Stopped A/B test '{test_id}': {reason}")
    
    def calculate_required_sample_size(
        self,
        effect_size: float,
        power: float = 0.8,
        significance_level: float = 0.05
    ) -> int:
        """Calculate required sample size for detecting effect size."""
        # Using Cohen's formula for two-sample t-test
        z_alpha = stats.norm.ppf(1 - significance_level / 2)
        z_beta = stats.norm.ppf(power)
        
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        return int(np.ceil(n))
    
    def export_test_results(self, test_id: str) -> Dict[str, Any]:
        """Export test results in a structured format."""
        test_result = self.get_test_results(test_id)
        if not test_result:
            return {}
        
        return {
            "test_id": test_result.test_id,
            "status": test_result.status.value,
            "start_time": test_result.start_time.isoformat(),
            "end_time": test_result.end_time.isoformat() if test_result.end_time else None,
            "duration_hours": test_result.test_duration_hours,
            "total_samples": test_result.total_samples,
            "statistical_results": {
                "p_value": test_result.p_value,
                "effect_size": test_result.effect_size,
                "significance": test_result.significance.value,
                "confidence_interval": test_result.confidence_interval,
                "early_stopped": test_result.early_stopped
            },
            "winner": {
                "variant_id": test_result.winning_variant_id,
                "improvement_percentage": test_result.improvement_percentage
            },
            "variants": {
                variant_id: {
                    "template_id": variant.template_id,
                    "template_name": variant.template_name,
                    "allocation_percentage": variant.allocation_percentage,
                    "sample_count": variant.sample_count,
                    "mean_reward": variant.mean_reward,
                    "std_reward": variant.std_reward,
                    "success_rate": variant.success_rate,
                    "confidence_interval": variant.confidence_interval
                }
                for variant_id, variant in test_result.variants.items()
            },
            "statistical_details": test_result.statistical_details
        }
