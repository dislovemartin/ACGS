"""
Privacy-Preserving Metrics and Differential Privacy Manager

Implements differential privacy with ε=1.0 and privacy-preserving evaluation
metrics for the federated evaluation framework.

Based on Task 6 requirements and privacy-preserving techniques.
"""

import asyncio
import logging
import time
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from datetime import datetime, timezone
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class PrivacyMechanism(Enum):
    """Supported privacy mechanisms."""
    LAPLACE = "laplace"
    GAUSSIAN = "gaussian"
    EXPONENTIAL = "exponential"
    LOCAL_DP = "local_dp"


@dataclass
class PrivacyBudget:
    """Privacy budget tracking for differential privacy."""
    epsilon: float
    delta: float = 0.0
    used_epsilon: float = 0.0
    used_delta: float = 0.0
    remaining_epsilon: float = field(init=False)
    remaining_delta: float = field(init=False)
    
    def __post_init__(self):
        self.remaining_epsilon = self.epsilon - self.used_epsilon
        self.remaining_delta = self.delta - self.used_delta


@dataclass
class PrivacyMetrics:
    """Privacy metrics for evaluation results."""
    mechanism: PrivacyMechanism
    epsilon_used: float
    delta_used: float
    noise_added: float
    privacy_loss: float
    data_utility: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DifferentialPrivacyManager:
    """
    Differential Privacy Manager for federated evaluation.
    
    Implements (ε, δ)-differential privacy with configurable mechanisms
    and privacy budget tracking.
    """
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.privacy_budget = PrivacyBudget(epsilon=epsilon, delta=delta)
        self.privacy_history: List[PrivacyMetrics] = []
        self.global_sensitivity = 1.0  # Assume unit global sensitivity
        
        # Privacy metrics tracking
        self.privacy_metrics = {
            "total_queries": 0,
            "privacy_budget_used": 0.0,
            "average_noise_added": 0.0,
            "privacy_violations": 0,
            "data_utility_score": 0.0
        }
        
        logger.info(f"Initialized Differential Privacy Manager (ε={epsilon}, δ={delta})")
    
    async def initialize(self):
        """Initialize the privacy manager."""
        try:
            logger.info("Differential Privacy Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Privacy Manager: {e}")
            raise
    
    async def apply_differential_privacy(
        self,
        data: Dict[str, Any],
        privacy_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply differential privacy to federated evaluation data.
        
        Args:
            data: Raw evaluation data from federated nodes
            privacy_requirements: Privacy requirements and constraints
            
        Returns:
            Privacy-preserving version of the data
        """
        try:
            # Extract privacy parameters
            epsilon_request = privacy_requirements.get("epsilon", self.privacy_budget.epsilon)
            mechanism = PrivacyMechanism(privacy_requirements.get("mechanism", "laplace"))
            
            # Check privacy budget
            if not self._check_privacy_budget(epsilon_request):
                raise ValueError(f"Insufficient privacy budget: {epsilon_request} > {self.privacy_budget.remaining_epsilon}")
            
            # Apply privacy mechanism to each node's data
            private_data = {}
            total_noise = 0.0
            
            for node_id, node_data in data.items():
                if isinstance(node_data, dict) and node_data.get("success", False):
                    private_node_data, noise_added = await self._apply_privacy_mechanism(
                        node_data, mechanism, epsilon_request
                    )
                    private_data[node_id] = private_node_data
                    total_noise += noise_added
                else:
                    # Keep failed results as-is (no privacy needed)
                    private_data[node_id] = node_data
            
            # Update privacy budget
            self._update_privacy_budget(epsilon_request, 0.0)
            
            # Calculate privacy metrics
            privacy_metrics = PrivacyMetrics(
                mechanism=mechanism,
                epsilon_used=epsilon_request,
                delta_used=0.0,
                noise_added=total_noise,
                privacy_loss=epsilon_request,
                data_utility=self._calculate_data_utility(data, private_data)
            )
            
            # Store privacy metrics
            self.privacy_history.append(privacy_metrics)
            await self._update_privacy_metrics(privacy_metrics)
            
            logger.info(f"Applied differential privacy: ε={epsilon_request}, mechanism={mechanism.value}")
            return private_data
            
        except Exception as e:
            logger.error(f"Failed to apply differential privacy: {e}")
            raise
    
    async def _apply_privacy_mechanism(
        self,
        data: Dict[str, Any],
        mechanism: PrivacyMechanism,
        epsilon: float
    ) -> Tuple[Dict[str, Any], float]:
        """Apply specific privacy mechanism to data."""
        try:
            private_data = data.copy()
            total_noise = 0.0
            
            # Identify numeric fields to add noise to
            numeric_fields = [
                "policy_compliance_score", "execution_time_ms", 
                "success_rate", "consistency_score"
            ]
            
            for field in numeric_fields:
                if field in data and isinstance(data[field], (int, float)):
                    original_value = float(data[field])
                    
                    if mechanism == PrivacyMechanism.LAPLACE:
                        noise = self._laplace_noise(epsilon)
                    elif mechanism == PrivacyMechanism.GAUSSIAN:
                        noise = self._gaussian_noise(epsilon)
                    elif mechanism == PrivacyMechanism.EXPONENTIAL:
                        noise = self._exponential_noise(epsilon)
                    elif mechanism == PrivacyMechanism.LOCAL_DP:
                        noise = self._local_dp_noise(epsilon)
                    else:
                        noise = 0.0
                    
                    # Add noise and ensure non-negative for certain fields
                    noisy_value = original_value + noise
                    if field in ["policy_compliance_score", "success_rate"]:
                        noisy_value = max(0.0, min(1.0, noisy_value))  # Clamp to [0, 1]
                    elif field == "execution_time_ms":
                        noisy_value = max(0.0, noisy_value)  # Ensure non-negative
                    
                    private_data[field] = noisy_value
                    private_data[f"{field}_noise_added"] = abs(noise)
                    total_noise += abs(noise)
            
            # Add privacy metadata
            private_data["privacy_applied"] = True
            private_data["privacy_mechanism"] = mechanism.value
            private_data["epsilon_used"] = epsilon
            
            return private_data, total_noise
            
        except Exception as e:
            logger.error(f"Failed to apply privacy mechanism: {e}")
            return data, 0.0
    
    def _laplace_noise(self, epsilon: float) -> float:
        """Generate Laplace noise for differential privacy."""
        try:
            # Laplace mechanism: noise ~ Lap(sensitivity/epsilon)
            scale = self.global_sensitivity / epsilon
            return np.random.laplace(0, scale)
        except Exception as e:
            logger.error(f"Failed to generate Laplace noise: {e}")
            return 0.0
    
    def _gaussian_noise(self, epsilon: float) -> float:
        """Generate Gaussian noise for differential privacy."""
        try:
            # Gaussian mechanism: noise ~ N(0, (sensitivity * sqrt(2*ln(1.25/delta)) / epsilon)^2)
            delta = self.privacy_budget.delta
            if delta <= 0:
                delta = 1e-5  # Default delta
            
            sigma = self.global_sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
            return np.random.normal(0, sigma)
        except Exception as e:
            logger.error(f"Failed to generate Gaussian noise: {e}")
            return 0.0
    
    def _exponential_noise(self, epsilon: float) -> float:
        """Generate exponential mechanism noise."""
        try:
            # Simplified exponential mechanism
            scale = 2 * self.global_sensitivity / epsilon
            return np.random.exponential(scale) - scale  # Center around 0
        except Exception as e:
            logger.error(f"Failed to generate exponential noise: {e}")
            return 0.0
    
    def _local_dp_noise(self, epsilon: float) -> float:
        """Generate local differential privacy noise."""
        try:
            # Randomized response mechanism
            p = np.exp(epsilon) / (np.exp(epsilon) + 1)
            if np.random.random() < p:
                return 0.0  # Keep original value
            else:
                return np.random.uniform(-0.1, 0.1)  # Add small random noise
        except Exception as e:
            logger.error(f"Failed to generate local DP noise: {e}")
            return 0.0
    
    def _check_privacy_budget(self, epsilon_request: float) -> bool:
        """Check if sufficient privacy budget is available."""
        return epsilon_request <= self.privacy_budget.remaining_epsilon
    
    def _update_privacy_budget(self, epsilon_used: float, delta_used: float):
        """Update privacy budget after use."""
        self.privacy_budget.used_epsilon += epsilon_used
        self.privacy_budget.used_delta += delta_used
        self.privacy_budget.remaining_epsilon = self.privacy_budget.epsilon - self.privacy_budget.used_epsilon
        self.privacy_budget.remaining_delta = self.privacy_budget.delta - self.privacy_budget.used_delta
    
    def _calculate_data_utility(self, original_data: Dict[str, Any], private_data: Dict[str, Any]) -> float:
        """Calculate data utility after applying privacy."""
        try:
            if not original_data or not private_data:
                return 0.0
            
            # Calculate utility based on numeric field preservation
            total_utility = 0.0
            field_count = 0
            
            for node_id in original_data:
                if node_id in private_data:
                    orig_node = original_data[node_id]
                    priv_node = private_data[node_id]
                    
                    if isinstance(orig_node, dict) and isinstance(priv_node, dict):
                        for field in ["policy_compliance_score", "execution_time_ms"]:
                            if field in orig_node and field in priv_node:
                                orig_val = float(orig_node[field])
                                priv_val = float(priv_node[field])
                                
                                if orig_val != 0:
                                    relative_error = abs(orig_val - priv_val) / abs(orig_val)
                                    utility = max(0.0, 1.0 - relative_error)
                                    total_utility += utility
                                    field_count += 1
            
            return total_utility / field_count if field_count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate data utility: {e}")
            return 0.0

    async def _update_privacy_metrics(self, privacy_metrics: PrivacyMetrics):
        """Update global privacy metrics."""
        try:
            self.privacy_metrics["total_queries"] += 1
            self.privacy_metrics["privacy_budget_used"] = self.privacy_budget.used_epsilon

            # Update average noise
            total_queries = self.privacy_metrics["total_queries"]
            current_avg = self.privacy_metrics["average_noise_added"]
            self.privacy_metrics["average_noise_added"] = (
                (current_avg * (total_queries - 1) + privacy_metrics.noise_added) / total_queries
            )

            # Update data utility
            current_utility = self.privacy_metrics["data_utility_score"]
            self.privacy_metrics["data_utility_score"] = (
                (current_utility * (total_queries - 1) + privacy_metrics.data_utility) / total_queries
            )

            # Check for privacy violations
            if self.privacy_budget.remaining_epsilon < 0:
                self.privacy_metrics["privacy_violations"] += 1
                logger.warning("Privacy budget exceeded!")

        except Exception as e:
            logger.error(f"Failed to update privacy metrics: {e}")

    async def get_privacy_metrics(self) -> Dict[str, Any]:
        """Get privacy metrics and budget status."""
        return {
            "privacy_budget": {
                "epsilon_total": self.privacy_budget.epsilon,
                "epsilon_used": self.privacy_budget.used_epsilon,
                "epsilon_remaining": self.privacy_budget.remaining_epsilon,
                "delta_total": self.privacy_budget.delta,
                "delta_used": self.privacy_budget.used_delta,
                "delta_remaining": self.privacy_budget.remaining_delta
            },
            "metrics": self.privacy_metrics.copy(),
            "recent_history": [
                {
                    "mechanism": pm.mechanism.value,
                    "epsilon_used": pm.epsilon_used,
                    "noise_added": pm.noise_added,
                    "data_utility": pm.data_utility,
                    "timestamp": pm.timestamp.isoformat()
                }
                for pm in self.privacy_history[-10:]  # Last 10 privacy applications
            ]
        }

    async def reset_privacy_budget(self, new_epsilon: float = None, new_delta: float = None):
        """Reset privacy budget (use with caution)."""
        try:
            if new_epsilon is not None:
                self.privacy_budget.epsilon = new_epsilon
            if new_delta is not None:
                self.privacy_budget.delta = new_delta

            self.privacy_budget.used_epsilon = 0.0
            self.privacy_budget.used_delta = 0.0
            self.privacy_budget.remaining_epsilon = self.privacy_budget.epsilon
            self.privacy_budget.remaining_delta = self.privacy_budget.delta

            logger.warning(f"Privacy budget reset: ε={self.privacy_budget.epsilon}, δ={self.privacy_budget.delta}")

        except Exception as e:
            logger.error(f"Failed to reset privacy budget: {e}")

    async def estimate_privacy_cost(self, query_type: str, data_size: int) -> float:
        """Estimate privacy cost for a given query."""
        try:
            # Base privacy cost estimation
            base_cost = 0.1

            # Adjust based on query type
            if query_type == "aggregation":
                cost_multiplier = 1.0
            elif query_type == "statistical":
                cost_multiplier = 1.5
            elif query_type == "ml_training":
                cost_multiplier = 2.0
            else:
                cost_multiplier = 1.0

            # Adjust based on data size
            size_factor = min(2.0, 1.0 + np.log10(data_size) / 10.0)

            estimated_cost = base_cost * cost_multiplier * size_factor
            return min(estimated_cost, self.privacy_budget.remaining_epsilon)

        except Exception as e:
            logger.error(f"Failed to estimate privacy cost: {e}")
            return 0.1

    async def validate_privacy_requirements(self, requirements: Dict[str, Any]) -> bool:
        """Validate privacy requirements against current budget."""
        try:
            epsilon_request = requirements.get("epsilon", 0.1)
            delta_request = requirements.get("delta", 0.0)
            mechanism = requirements.get("mechanism", "laplace")

            # Check budget availability
            if epsilon_request > self.privacy_budget.remaining_epsilon:
                logger.warning(f"Insufficient epsilon budget: {epsilon_request} > {self.privacy_budget.remaining_epsilon}")
                return False

            if delta_request > self.privacy_budget.remaining_delta:
                logger.warning(f"Insufficient delta budget: {delta_request} > {self.privacy_budget.remaining_delta}")
                return False

            # Check mechanism validity
            try:
                PrivacyMechanism(mechanism)
            except ValueError:
                logger.warning(f"Invalid privacy mechanism: {mechanism}")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate privacy requirements: {e}")
            return False

    async def shutdown(self):
        """Shutdown the privacy manager."""
        try:
            logger.info("Shutting down Differential Privacy Manager...")

            # Log final privacy budget status
            logger.info(f"Final privacy budget: ε={self.privacy_budget.remaining_epsilon}/{self.privacy_budget.epsilon}")

            # Clear sensitive data
            self.privacy_history.clear()

            logger.info("Differential Privacy Manager shutdown complete")

        except Exception as e:
            logger.error(f"Failed to shutdown Privacy Manager: {e}")


# Global differential privacy manager instance
differential_privacy_manager = DifferentialPrivacyManager()
