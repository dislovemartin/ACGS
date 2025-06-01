"""
Multi-Armed Bandit Prompt Optimization System for ACGS-PGP

Implements Thompson Sampling and Upper Confidence Bound (UCB) algorithms
for optimizing prompt templates in the AlphaEvolve framework to improve
policy generation quality and achieve >99.9% LLM reliability.

Based on Task 5 requirements and AlphaEvolve-ACGS Integration System research.
"""

import asyncio
import logging
import time
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from datetime import datetime, timezone
from abc import ABC, abstractmethod

# Core dependencies
from ..schemas import LLMInterpretationInput, LLMStructuredOutput
from .llm_reliability_framework import LLMReliabilityFramework, LLMReliabilityConfig, ReliabilityLevel

logger = logging.getLogger(__name__)


class MABAlgorithm(Enum):
    """Multi-Armed Bandit algorithm types."""
    THOMPSON_SAMPLING = "thompson_sampling"
    UCB = "upper_confidence_bound"
    EPSILON_GREEDY = "epsilon_greedy"


@dataclass
class PromptTemplate:
    """Prompt template with metadata and performance tracking."""
    template_id: str
    name: str
    template_content: str
    category: str  # constitutional, safety_focused, fairness_aware, etc.
    version: str = "1.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Performance tracking
    total_uses: int = 0
    total_rewards: float = 0.0
    success_count: int = 0
    average_reward: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 1.0)


@dataclass
class MABConfig:
    """Configuration for Multi-Armed Bandit optimization."""
    algorithm: MABAlgorithm = MABAlgorithm.THOMPSON_SAMPLING
    exploration_rate: float = 0.1  # For epsilon-greedy
    confidence_level: float = 0.95  # For UCB
    alpha_prior: float = 1.0  # For Thompson Sampling (Beta distribution)
    beta_prior: float = 1.0   # For Thompson Sampling (Beta distribution)
    
    # Reward function weights
    semantic_similarity_weight: float = 0.4
    policy_quality_weight: float = 0.3
    constitutional_compliance_weight: float = 0.2
    bias_mitigation_weight: float = 0.1
    
    # Performance thresholds
    min_uses_for_confidence: int = 10
    reward_threshold: float = 0.8
    update_frequency: int = 100  # Update model every N uses


@dataclass
class RewardComponents:
    """Components of the reward function for prompt evaluation."""
    semantic_similarity: float = 0.0
    policy_quality: float = 0.0
    constitutional_compliance: float = 0.0
    bias_mitigation: float = 0.0
    composite_score: float = 0.0
    confidence: float = 0.0


class MABAlgorithmBase(ABC):
    """Abstract base class for Multi-Armed Bandit algorithms."""
    
    def __init__(self, config: MABConfig):
        self.config = config
        self.arm_stats = {}  # arm_id -> statistics
        
    @abstractmethod
    def select_arm(self, context: Dict[str, Any] = None, available_arms: List[str] = None) -> str:
        """Select the best arm (prompt template) given context."""
        pass
    
    @abstractmethod
    def update_reward(self, arm_id: str, reward: float, context: Dict[str, Any] = None):
        """Update arm statistics with new reward."""
        pass


class ThompsonSamplingMAB(MABAlgorithmBase):
    """Thompson Sampling algorithm for prompt optimization."""
    
    def __init__(self, config: MABConfig):
        super().__init__(config)
        self.alpha = {}  # Success counts + alpha_prior
        self.beta = {}   # Failure counts + beta_prior
        
    def select_arm(self, context: Dict[str, Any] = None, available_arms: List[str] = None) -> str:
        """Select arm using Thompson Sampling (Beta-Bernoulli)."""
        if not self.alpha:
            return None  # No arms available

        # Use available arms if provided, otherwise use all arms
        arms_to_consider = available_arms if available_arms else list(self.alpha.keys())

        if not arms_to_consider:
            return None

        # Sample from Beta distribution for each available arm
        samples = {}
        for arm_id in arms_to_consider:
            if arm_id in self.alpha:  # Ensure arm exists
                alpha_val = self.alpha[arm_id]
                beta_val = self.beta[arm_id]
                samples[arm_id] = np.random.beta(alpha_val, beta_val)

        if not samples:
            return None

        # Select arm with highest sample
        best_arm = max(samples.keys(), key=lambda x: samples[x])
        logger.debug(f"Thompson Sampling selected arm: {best_arm} (sample: {samples[best_arm]:.3f}) from {len(arms_to_consider)} available")
        return best_arm
    
    def update_reward(self, arm_id: str, reward: float, context: Dict[str, Any] = None):
        """Update Beta distribution parameters."""
        if arm_id not in self.alpha:
            self.alpha[arm_id] = self.config.alpha_prior
            self.beta[arm_id] = self.config.beta_prior
            
        # Convert reward to success/failure
        success = 1 if reward >= self.config.reward_threshold else 0
        
        if success:
            self.alpha[arm_id] += 1
        else:
            self.beta[arm_id] += 1
            
        logger.debug(f"Updated arm {arm_id}: α={self.alpha[arm_id]}, β={self.beta[arm_id]}")


class UCBAlgorithm(MABAlgorithmBase):
    """Upper Confidence Bound algorithm for prompt optimization."""
    
    def __init__(self, config: MABConfig):
        super().__init__(config)
        self.counts = {}      # Number of times each arm was selected
        self.rewards = {}     # Sum of rewards for each arm
        self.total_count = 0  # Total number of selections
        
    def select_arm(self, context: Dict[str, Any] = None, available_arms: List[str] = None) -> str:
        """Select arm using UCB1 algorithm."""
        if not self.counts:
            return None

        # Use available arms if provided, otherwise use all arms
        arms_to_consider = available_arms if available_arms else list(self.counts.keys())

        if not arms_to_consider:
            return None

        # Calculate UCB values for each available arm
        ucb_values = {}
        for arm_id in arms_to_consider:
            if arm_id in self.counts:  # Ensure arm exists
                if self.counts[arm_id] == 0:
                    ucb_values[arm_id] = float('inf')  # Unplayed arms get priority
                else:
                    avg_reward = self.rewards[arm_id] / self.counts[arm_id]
                    confidence_bonus = np.sqrt(
                        (2 * np.log(self.total_count)) / self.counts[arm_id]
                    )
                    ucb_values[arm_id] = avg_reward + confidence_bonus

        if not ucb_values:
            return None

        # Select arm with highest UCB value
        best_arm = max(ucb_values.keys(), key=lambda x: ucb_values[x])
        logger.debug(f"UCB selected arm: {best_arm} (UCB: {ucb_values[best_arm]:.3f}) from {len(arms_to_consider)} available")
        return best_arm
    
    def update_reward(self, arm_id: str, reward: float, context: Dict[str, Any] = None):
        """Update UCB statistics."""
        if arm_id not in self.counts:
            self.counts[arm_id] = 0
            self.rewards[arm_id] = 0.0
            
        self.counts[arm_id] += 1
        self.rewards[arm_id] += reward
        self.total_count += 1
        
        avg_reward = self.rewards[arm_id] / self.counts[arm_id]
        logger.debug(f"Updated arm {arm_id}: count={self.counts[arm_id]}, avg_reward={avg_reward:.3f}")


class RewardFunction:
    """Composite reward function for evaluating prompt performance."""
    
    def __init__(self, config: MABConfig):
        self.config = config
        
    async def calculate_reward(
        self,
        prompt_template: PromptTemplate,
        llm_output: LLMStructuredOutput,
        context: Dict[str, Any]
    ) -> RewardComponents:
        """Calculate composite reward for prompt performance."""
        components = RewardComponents()
        
        # 1. Semantic similarity (placeholder - would use SentenceTransformers)
        components.semantic_similarity = await self._calculate_semantic_similarity(
            prompt_template, llm_output, context
        )
        
        # 2. Policy quality metrics
        components.policy_quality = await self._calculate_policy_quality(
            llm_output, context
        )
        
        # 3. Constitutional compliance
        components.constitutional_compliance = await self._calculate_constitutional_compliance(
            llm_output, context
        )
        
        # 4. Bias mitigation
        components.bias_mitigation = await self._calculate_bias_mitigation(
            llm_output, context
        )
        
        # Calculate composite score
        components.composite_score = (
            self.config.semantic_similarity_weight * components.semantic_similarity +
            self.config.policy_quality_weight * components.policy_quality +
            self.config.constitutional_compliance_weight * components.constitutional_compliance +
            self.config.bias_mitigation_weight * components.bias_mitigation
        )
        
        # Calculate confidence based on output quality indicators
        components.confidence = min(
            components.semantic_similarity,
            components.policy_quality,
            components.constitutional_compliance
        )
        
        return components
    
    async def _calculate_semantic_similarity(
        self, prompt_template: PromptTemplate, output: LLMStructuredOutput, context: Dict[str, Any]
    ) -> float:
        """Calculate semantic similarity between prompt intent and output."""
        # Placeholder implementation - would use SentenceTransformers in practice
        if output.raw_llm_response and len(output.raw_llm_response) > 50:
            return 0.8  # Mock high similarity for substantial responses
        return 0.4
    
    async def _calculate_policy_quality(self, output: LLMStructuredOutput, context: Dict[str, Any]) -> float:
        """Calculate policy quality metrics (coverage, specificity, actionability)."""
        # Placeholder implementation
        quality_score = 0.0
        
        if output.raw_llm_response:
            response = output.raw_llm_response.lower()
            
            # Coverage: Does it address the main requirements?
            if any(keyword in response for keyword in ['allow', 'deny', 'rule', 'policy']):
                quality_score += 0.3
                
            # Specificity: Is it specific enough?
            if len(response.split()) > 20:  # Substantial content
                quality_score += 0.3
                
            # Actionability: Can it be implemented?
            if any(keyword in response for keyword in ['input', 'user', 'resource', 'action']):
                quality_score += 0.4
                
        return min(quality_score, 1.0)
    
    async def _calculate_constitutional_compliance(self, output: LLMStructuredOutput, context: Dict[str, Any]) -> float:
        """Calculate constitutional compliance score."""
        # Placeholder implementation - would integrate with AC service
        if output.raw_llm_response and 'constitutional' in context.get('category', ''):
            return 0.9  # High compliance for constitutional prompts
        return 0.7
    
    async def _calculate_bias_mitigation(self, output: LLMStructuredOutput, context: Dict[str, Any]) -> float:
        """Calculate bias mitigation effectiveness."""
        # Placeholder implementation - would integrate with bias detection
        if output.raw_llm_response:
            response = output.raw_llm_response.lower()
            # Check for inclusive language
            if any(term in response for term in ['fair', 'equal', 'inclusive', 'regardless']):
                return 0.8
        return 0.6


class MABPromptOptimizer:
    """Main Multi-Armed Bandit prompt optimization system."""

    def __init__(self, config: MABConfig = None, reliability_framework: LLMReliabilityFramework = None):
        self.config = config or MABConfig()
        self.reliability_framework = reliability_framework
        self.prompt_templates = {}  # template_id -> PromptTemplate
        self.reward_function = RewardFunction(self.config)

        # Initialize MAB algorithm
        if self.config.algorithm == MABAlgorithm.THOMPSON_SAMPLING:
            self.mab_algorithm = ThompsonSamplingMAB(self.config)
        elif self.config.algorithm == MABAlgorithm.UCB:
            self.mab_algorithm = UCBAlgorithm(self.config)
        else:
            raise ValueError(f"Unsupported MAB algorithm: {self.config.algorithm}")

        self.optimization_history = []
        self.total_optimizations = 0

        logger.info(f"Initialized MAB Prompt Optimizer with {self.config.algorithm.value}")

    def register_prompt_template(self, template: PromptTemplate):
        """Register a new prompt template for optimization."""
        self.prompt_templates[template.template_id] = template

        # Initialize algorithm with new arm
        if hasattr(self.mab_algorithm, 'alpha'):  # Thompson Sampling
            self.mab_algorithm.alpha[template.template_id] = self.config.alpha_prior
            self.mab_algorithm.beta[template.template_id] = self.config.beta_prior
        elif hasattr(self.mab_algorithm, 'counts'):  # UCB
            self.mab_algorithm.counts[template.template_id] = 0
            self.mab_algorithm.rewards[template.template_id] = 0.0

        logger.info(f"Registered prompt template: {template.name} ({template.template_id})")

    async def select_optimal_prompt(self, context: Dict[str, Any]) -> Optional[PromptTemplate]:
        """Select the optimal prompt template for given context."""
        if not self.prompt_templates:
            logger.warning("No prompt templates registered")
            return None

        # Filter templates by category if specified
        category = context.get('category')
        available_templates = self.prompt_templates
        if category:
            available_templates = {
                tid: template for tid, template in self.prompt_templates.items()
                if template.category == category
            }

        if not available_templates:
            logger.warning(f"No templates available for category: {category}")
            return None

        # Update algorithm with available arms
        available_template_ids = list(available_templates.keys())
        self._update_available_arms(available_template_ids)

        # Select optimal arm from available templates
        selected_template_id = self.mab_algorithm.select_arm(context, available_template_ids)
        if not selected_template_id:
            # Fallback to random selection
            selected_template_id = np.random.choice(available_template_ids)

        selected_template = available_templates[selected_template_id]
        selected_template.total_uses += 1

        logger.info(f"Selected prompt template: {selected_template.name} for context: {context.get('category', 'general')}")
        return selected_template

    async def update_performance(
        self,
        template_id: str,
        llm_output: LLMStructuredOutput,
        context: Dict[str, Any]
    ):
        """Update prompt template performance with new results."""
        if template_id not in self.prompt_templates:
            logger.warning(f"Template {template_id} not found for performance update")
            return

        template = self.prompt_templates[template_id]

        # Calculate reward components
        reward_components = await self.reward_function.calculate_reward(
            template, llm_output, context
        )

        # Update template statistics
        template.total_rewards += reward_components.composite_score
        template.average_reward = template.total_rewards / template.total_uses

        if reward_components.composite_score >= self.config.reward_threshold:
            template.success_count += 1

        # Update MAB algorithm
        self.mab_algorithm.update_reward(template_id, reward_components.composite_score, context)

        # Record optimization history
        self.optimization_history.append({
            "timestamp": datetime.now(timezone.utc),
            "template_id": template_id,
            "template_name": template.name,
            "context": context,
            "reward_components": reward_components,
            "composite_score": reward_components.composite_score,
            "total_uses": template.total_uses,
            "average_reward": template.average_reward
        })

        self.total_optimizations += 1

        # Periodic model updates
        if self.total_optimizations % self.config.update_frequency == 0:
            await self._update_confidence_intervals()

        logger.debug(f"Updated performance for {template.name}: reward={reward_components.composite_score:.3f}, avg={template.average_reward:.3f}")

    def _update_available_arms(self, available_template_ids: List[str]):
        """Update MAB algorithm with currently available arms."""
        if hasattr(self.mab_algorithm, 'alpha'):  # Thompson Sampling
            # Ensure all available templates are in the algorithm
            for template_id in available_template_ids:
                if template_id not in self.mab_algorithm.alpha:
                    self.mab_algorithm.alpha[template_id] = self.config.alpha_prior
                    self.mab_algorithm.beta[template_id] = self.config.beta_prior
        elif hasattr(self.mab_algorithm, 'counts'):  # UCB
            for template_id in available_template_ids:
                if template_id not in self.mab_algorithm.counts:
                    self.mab_algorithm.counts[template_id] = 0
                    self.mab_algorithm.rewards[template_id] = 0.0

    async def _update_confidence_intervals(self):
        """Update confidence intervals for all templates."""
        for template in self.prompt_templates.values():
            if template.total_uses >= self.config.min_uses_for_confidence:
                # Calculate confidence interval using normal approximation
                mean = template.average_reward
                std_error = np.sqrt(mean * (1 - mean) / template.total_uses)
                margin = 1.96 * std_error  # 95% confidence

                template.confidence_interval = (
                    max(0.0, mean - margin),
                    min(1.0, mean + margin)
                )

    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get comprehensive optimization metrics."""
        if not self.prompt_templates:
            return {"error": "No templates registered"}

        template_metrics = {}
        for template_id, template in self.prompt_templates.items():
            template_metrics[template_id] = {
                "name": template.name,
                "category": template.category,
                "total_uses": template.total_uses,
                "success_count": template.success_count,
                "success_rate": template.success_count / max(template.total_uses, 1),
                "average_reward": template.average_reward,
                "confidence_interval": template.confidence_interval
            }

        # Overall system metrics
        total_uses = sum(t.total_uses for t in self.prompt_templates.values())
        total_successes = sum(t.success_count for t in self.prompt_templates.values())

        return {
            "algorithm": self.config.algorithm.value,
            "total_optimizations": self.total_optimizations,
            "total_template_uses": total_uses,
            "overall_success_rate": total_successes / max(total_uses, 1),
            "template_count": len(self.prompt_templates),
            "template_metrics": template_metrics,
            "recent_history": self.optimization_history[-10:] if self.optimization_history else []
        }

    def get_best_performing_templates(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """Get top-k best performing templates."""
        if not self.prompt_templates:
            return []

        # Sort templates by average reward
        sorted_templates = sorted(
            self.prompt_templates.values(),
            key=lambda t: t.average_reward,
            reverse=True
        )

        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "category": t.category,
                "average_reward": t.average_reward,
                "total_uses": t.total_uses,
                "success_rate": t.success_count / max(t.total_uses, 1),
                "confidence_interval": t.confidence_interval
            }
            for t in sorted_templates[:top_k]
        ]
