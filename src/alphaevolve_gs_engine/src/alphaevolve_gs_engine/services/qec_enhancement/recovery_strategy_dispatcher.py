"""
recovery_strategy_dispatcher.py

QEC-inspired Recovery Strategy Dispatcher for intelligent re-synthesis strategy selection.
Applies targeted recovery strategies based on error type, minimizing synthesis attempts
while maximizing success rate.

Classes:
    RecoveryStrategyDispatcher: Main dispatcher for recovery strategy selection
    RecoveryStrategy: Enumeration of available recovery strategies
    RecoveryConfig: Configuration for recovery strategies
    RecoveryResult: Result structure for recovery attempts
"""

import logging
import yaml
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import defaultdict

from .error_prediction_model import FailureType, SynthesisAttemptLog

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Enumeration of available recovery strategies."""
    DEFAULT = "default"
    SIMPLIFIED_SYNTAX_PROMPT = "simplified_syntax_prompt"
    EXPLICIT_DISAMBIGUATION = "explicit_disambiguation"
    MULTI_MODEL_CONSENSUS = "multi_model_consensus"
    ENHANCED_CONTEXT_PROMPT = "enhanced_context_prompt"
    DECOMPOSE_PRINCIPLE = "decompose_principle"
    HUMAN_CLARIFICATION = "human_clarification"
    ESCALATE_TO_HUMAN = "escalate_to_human"


@dataclass
class RecoveryConfig:
    """Configuration for a recovery strategy."""
    strategy: RecoveryStrategy
    max_attempts: int
    timeout_seconds: Optional[int] = None
    fallback_strategy: Optional[RecoveryStrategy] = None
    success_threshold: float = 0.7
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RecoveryResult:
    """Result structure for recovery attempts."""
    strategy_used: RecoveryStrategy
    success: bool
    attempts_made: int
    total_time_seconds: float
    final_output: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RecoveryStrategyDispatcher:
    """
    QEC-inspired Recovery Strategy Dispatcher.
    
    Applies targeted recovery strategies based on error type, minimizing synthesis
    attempts while maximizing success rate through intelligent strategy selection.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the recovery strategy dispatcher.
        
        Args:
            config_path: Path to YAML configuration file for strategies
        """
        self.strategies = self._load_strategy_config(config_path)
        self.attempt_history = defaultdict(list)
        self.strategy_performance = defaultdict(lambda: {"successes": 0, "attempts": 0})
        
        logger.info("Recovery Strategy Dispatcher initialized")
    
    def get_recovery_strategy(
        self, 
        failure_log: SynthesisAttemptLog,
        principle_id: str
    ) -> RecoveryStrategy:
        """
        Get the appropriate recovery strategy for a synthesis failure.
        
        Args:
            failure_log: SynthesisAttemptLog with failure details
            principle_id: Principle identifier for attempt tracking
            
        Returns:
            RecoveryStrategy to apply
        """
        if not failure_log.failure_type:
            return RecoveryStrategy.DEFAULT
        
        # Check attempt history for this principle
        attempts = len(self.attempt_history[principle_id])
        
        # Get strategy configuration for this failure type
        strategy_config = self.strategies.get(failure_log.failure_type)
        if not strategy_config:
            return RecoveryStrategy.DEFAULT
        
        # Check if we've exceeded max attempts
        if attempts >= strategy_config.max_attempts:
            return RecoveryStrategy.ESCALATE_TO_HUMAN
        
        # Select strategy based on attempt number
        if attempts == 0:
            return strategy_config.strategy
        else:
            # Use fallback strategy for subsequent attempts
            return strategy_config.fallback_strategy or RecoveryStrategy.ESCALATE_TO_HUMAN
    
    def execute_recovery_strategy(
        self,
        strategy: RecoveryStrategy,
        principle_id: str,
        original_input: Dict[str, Any],
        failure_context: Optional[Dict[str, Any]] = None
    ) -> RecoveryResult:
        """
        Execute a recovery strategy.
        
        Args:
            strategy: RecoveryStrategy to execute
            principle_id: Principle identifier
            original_input: Original synthesis input
            failure_context: Context about the failure
            
        Returns:
            RecoveryResult with execution details
        """
        start_time = datetime.now()
        
        try:
            # Record attempt
            self.attempt_history[principle_id].append({
                "strategy": strategy,
                "timestamp": start_time,
                "failure_context": failure_context
            })
            
            # Execute strategy
            result = self._execute_strategy_implementation(
                strategy, principle_id, original_input, failure_context
            )
            
            # Update performance metrics
            self.strategy_performance[strategy]["attempts"] += 1
            if result.success:
                self.strategy_performance[strategy]["successes"] += 1
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.total_time_seconds = execution_time
            
            logger.info(f"Recovery strategy {strategy.value} executed for {principle_id}: success={result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing recovery strategy {strategy.value} for {principle_id}: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return RecoveryResult(
                strategy_used=strategy,
                success=False,
                attempts_made=1,
                total_time_seconds=execution_time,
                error_message=str(e)
            )
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for all recovery strategies.
        
        Returns:
            Dictionary with strategy performance data
        """
        performance = {}
        
        for strategy, metrics in self.strategy_performance.items():
            attempts = metrics["attempts"]
            successes = metrics["successes"]
            success_rate = successes / attempts if attempts > 0 else 0.0
            
            performance[strategy.value] = {
                "attempts": attempts,
                "successes": successes,
                "success_rate": success_rate,
                "failure_rate": 1.0 - success_rate
            }
        
        return performance
    
    def update_strategy_config(
        self, 
        failure_type: FailureType, 
        config: RecoveryConfig
    ) -> None:
        """
        Update configuration for a specific failure type.
        
        Args:
            failure_type: FailureType to configure
            config: RecoveryConfig with new settings
        """
        self.strategies[failure_type] = config
        logger.info(f"Updated recovery strategy config for {failure_type.value}")
    
    def clear_attempt_history(self, principle_id: Optional[str] = None) -> None:
        """
        Clear attempt history for a principle or all principles.
        
        Args:
            principle_id: Specific principle to clear, or None for all
        """
        if principle_id:
            self.attempt_history[principle_id].clear()
            logger.info(f"Cleared attempt history for principle {principle_id}")
        else:
            self.attempt_history.clear()
            logger.info("Cleared all attempt history")
    
    def _execute_strategy_implementation(
        self,
        strategy: RecoveryStrategy,
        principle_id: str,
        original_input: Dict[str, Any],
        failure_context: Optional[Dict[str, Any]]
    ) -> RecoveryResult:
        """
        Execute the actual implementation of a recovery strategy.
        
        This is a simplified implementation. In a real system, this would
        integrate with the actual LLM synthesis pipeline.
        """
        if strategy == RecoveryStrategy.SIMPLIFIED_SYNTAX_PROMPT:
            return self._execute_simplified_syntax_strategy(original_input)
        
        elif strategy == RecoveryStrategy.EXPLICIT_DISAMBIGUATION:
            return self._execute_disambiguation_strategy(original_input, failure_context)
        
        elif strategy == RecoveryStrategy.MULTI_MODEL_CONSENSUS:
            return self._execute_consensus_strategy(original_input)
        
        elif strategy == RecoveryStrategy.ENHANCED_CONTEXT_PROMPT:
            return self._execute_enhanced_context_strategy(original_input)
        
        elif strategy == RecoveryStrategy.DECOMPOSE_PRINCIPLE:
            return self._execute_decomposition_strategy(original_input)
        
        elif strategy == RecoveryStrategy.HUMAN_CLARIFICATION:
            return self._execute_human_clarification_strategy(original_input)
        
        elif strategy == RecoveryStrategy.ESCALATE_TO_HUMAN:
            return self._execute_human_escalation_strategy(original_input)
        
        else:
            return self._execute_default_strategy(original_input)
    
    def _execute_simplified_syntax_strategy(self, original_input: Dict[str, Any]) -> RecoveryResult:
        """Execute simplified syntax prompt strategy."""
        # Simulate simplified syntax approach
        success = True  # Simplified approach often works
        
        return RecoveryResult(
            strategy_used=RecoveryStrategy.SIMPLIFIED_SYNTAX_PROMPT,
            success=success,
            attempts_made=1,
            total_time_seconds=0.0,
            final_output="Simplified syntax policy generated",
            metadata={"approach": "simplified_syntax", "complexity_reduced": True}
        )
    
    def _execute_disambiguation_strategy(
        self, 
        original_input: Dict[str, Any], 
        failure_context: Optional[Dict[str, Any]]
    ) -> RecoveryResult:
        """Execute explicit disambiguation strategy."""
        # Simulate disambiguation approach
        success = True  # Disambiguation usually helps with semantic conflicts
        
        return RecoveryResult(
            strategy_used=RecoveryStrategy.EXPLICIT_DISAMBIGUATION,
            success=success,
            attempts_made=1,
            total_time_seconds=0.0,
            final_output="Disambiguated policy generated",
            metadata={"approach": "disambiguation", "ambiguity_resolved": True}
        )
    
    def _execute_consensus_strategy(self, original_input: Dict[str, Any]) -> RecoveryResult:
        """Execute multi-model consensus strategy."""
        # Simulate multi-model consensus
        success = True  # Consensus approach is robust
        
        return RecoveryResult(
            strategy_used=RecoveryStrategy.MULTI_MODEL_CONSENSUS,
            success=success,
            attempts_made=3,  # Multiple models
            total_time_seconds=0.0,
            final_output="Consensus policy generated",
            metadata={"approach": "consensus", "models_used": 3, "agreement_score": 0.85}
        )
    
    def _execute_enhanced_context_strategy(self, original_input: Dict[str, Any]) -> RecoveryResult:
        """Execute enhanced context prompt strategy."""
        # Simulate enhanced context approach
        success = True  # More context usually helps
        
        return RecoveryResult(
            strategy_used=RecoveryStrategy.ENHANCED_CONTEXT_PROMPT,
            success=success,
            attempts_made=1,
            total_time_seconds=0.0,
            final_output="Context-enhanced policy generated",
            metadata={"approach": "enhanced_context", "context_expanded": True}
        )
    
    def _execute_decomposition_strategy(self, original_input: Dict[str, Any]) -> RecoveryResult:
        """Execute principle decomposition strategy."""
        # Simulate decomposition approach
        success = True  # Breaking down complex principles helps
        
        return RecoveryResult(
            strategy_used=RecoveryStrategy.DECOMPOSE_PRINCIPLE,
            success=success,
            attempts_made=1,
            total_time_seconds=0.0,
            final_output="Decomposed sub-policies generated",
            metadata={"approach": "decomposition", "sub_policies_count": 3}
        )
    
    def _execute_human_clarification_strategy(self, original_input: Dict[str, Any]) -> RecoveryResult:
        """Execute human clarification strategy."""
        # Simulate human clarification request
        success = False  # Requires human intervention
        
        return RecoveryResult(
            strategy_used=RecoveryStrategy.HUMAN_CLARIFICATION,
            success=success,
            attempts_made=1,
            total_time_seconds=0.0,
            final_output=None,
            metadata={"approach": "human_clarification", "clarification_requested": True}
        )
    
    def _execute_human_escalation_strategy(self, original_input: Dict[str, Any]) -> RecoveryResult:
        """Execute human escalation strategy."""
        # Simulate human escalation
        success = False  # Requires human intervention
        
        return RecoveryResult(
            strategy_used=RecoveryStrategy.ESCALATE_TO_HUMAN,
            success=success,
            attempts_made=1,
            total_time_seconds=0.0,
            final_output=None,
            metadata={"approach": "human_escalation", "escalated": True}
        )
    
    def _execute_default_strategy(self, original_input: Dict[str, Any]) -> RecoveryResult:
        """Execute default recovery strategy."""
        # Simulate default approach
        success = False  # Default often fails if we're in recovery
        
        return RecoveryResult(
            strategy_used=RecoveryStrategy.DEFAULT,
            success=success,
            attempts_made=1,
            total_time_seconds=0.0,
            final_output=None,
            metadata={"approach": "default", "retry_attempted": True}
        )
    
    def _load_strategy_config(self, config_path: Optional[str]) -> Dict[FailureType, RecoveryConfig]:
        """
        Load recovery strategy configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Dictionary mapping failure types to recovery configurations
        """
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                return self._parse_config_data(config_data)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}. Using defaults.")
        
        return self._get_default_strategy_config()
    
    def _parse_config_data(self, config_data: Dict[str, Any]) -> Dict[FailureType, RecoveryConfig]:
        """Parse configuration data into RecoveryConfig objects."""
        strategies = {}
        
        for failure_type_str, strategy_data in config_data.get("strategies", {}).items():
            try:
                failure_type = FailureType(failure_type_str)
                strategy = RecoveryStrategy(strategy_data["primary"])
                fallback = None
                if "fallback" in strategy_data:
                    fallback = RecoveryStrategy(strategy_data["fallback"])
                
                config = RecoveryConfig(
                    strategy=strategy,
                    max_attempts=strategy_data.get("max_attempts", 2),
                    timeout_seconds=strategy_data.get("timeout_seconds"),
                    fallback_strategy=fallback,
                    success_threshold=strategy_data.get("success_threshold", 0.7),
                    metadata=strategy_data.get("metadata", {})
                )
                
                strategies[failure_type] = config
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid strategy config for {failure_type_str}: {e}")
        
        return strategies
    
    def _get_default_strategy_config(self) -> Dict[FailureType, RecoveryConfig]:
        """Get default recovery strategy configuration."""
        return {
            FailureType.SYNTAX_ERROR: RecoveryConfig(
                strategy=RecoveryStrategy.SIMPLIFIED_SYNTAX_PROMPT,
                max_attempts=2,
                fallback_strategy=RecoveryStrategy.DECOMPOSE_PRINCIPLE
            ),
            FailureType.SEMANTIC_CONFLICT: RecoveryConfig(
                strategy=RecoveryStrategy.EXPLICIT_DISAMBIGUATION,
                max_attempts=3,
                fallback_strategy=RecoveryStrategy.HUMAN_CLARIFICATION
            ),
            FailureType.CONFIDENCE_LOW: RecoveryConfig(
                strategy=RecoveryStrategy.ENHANCED_CONTEXT_PROMPT,
                max_attempts=2,
                fallback_strategy=RecoveryStrategy.MULTI_MODEL_CONSENSUS
            ),
            FailureType.AMBIGUOUS_PRINCIPLE: RecoveryConfig(
                strategy=RecoveryStrategy.EXPLICIT_DISAMBIGUATION,
                max_attempts=2,
                fallback_strategy=RecoveryStrategy.HUMAN_CLARIFICATION
            ),
            FailureType.COMPLEXITY_HIGH: RecoveryConfig(
                strategy=RecoveryStrategy.DECOMPOSE_PRINCIPLE,
                max_attempts=2,
                fallback_strategy=RecoveryStrategy.HUMAN_CLARIFICATION
            ),
            FailureType.TIMEOUT: RecoveryConfig(
                strategy=RecoveryStrategy.SIMPLIFIED_SYNTAX_PROMPT,
                max_attempts=1,
                fallback_strategy=RecoveryStrategy.ESCALATE_TO_HUMAN
            ),
            FailureType.VALIDATION_FAILED: RecoveryConfig(
                strategy=RecoveryStrategy.ENHANCED_CONTEXT_PROMPT,
                max_attempts=2,
                fallback_strategy=RecoveryStrategy.HUMAN_CLARIFICATION
            ),
            FailureType.BIAS_DETECTED: RecoveryConfig(
                strategy=RecoveryStrategy.MULTI_MODEL_CONSENSUS,
                max_attempts=2,
                fallback_strategy=RecoveryStrategy.HUMAN_CLARIFICATION
            )
        }
