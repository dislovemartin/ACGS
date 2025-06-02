"""
qec_enhanced_synthesizer.py

QEC-Enhanced Policy Synthesizer integrating QEC-inspired resilience mechanisms
with the existing GS service LLM reliability framework.

Classes:
    QECEnhancedSynthesizer: Main synthesizer with QEC enhancements
    QECSynthesisInput: Enhanced input structure with QEC metadata
    QECSynthesisOutput: Enhanced output structure with QEC metrics
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Import existing GS service components
from .llm_reliability_framework import (
    EnhancedLLMReliabilityFramework,
    LLMReliabilityConfig,
    ReliabilityMetrics
)
from .constitutional_prompting import ConstitutionalPromptBuilder
from ..schemas import LLMInterpretationInput, LLMStructuredOutput

# Import QEC enhancement components
from alphaevolve_gs_engine.services.qec_enhancement import (
    ConstitutionalDistanceCalculator,
    ValidationDSLParser,
    ErrorPredictionModel,
    RecoveryStrategyDispatcher,
    FailureType,
    SynthesisAttemptLog,
    RecoveryStrategy
)
from alphaevolve_gs_engine.core.constitutional_principle import ConstitutionalPrinciple

logger = logging.getLogger(__name__)


@dataclass
class QECSynthesisInput:
    """Enhanced synthesis input with QEC metadata."""
    principle: ConstitutionalPrinciple
    context: Dict[str, Any]
    llm_input: LLMInterpretationInput
    qec_metadata: Optional[Dict[str, Any]] = None


@dataclass
class QECSynthesisOutput:
    """Enhanced synthesis output with QEC metrics."""
    llm_output: LLMStructuredOutput
    reliability_metrics: ReliabilityMetrics
    constitutional_distance: float
    error_predictions: Dict[FailureType, float]
    recovery_strategy_used: Optional[RecoveryStrategy]
    qec_metadata: Dict[str, Any]
    synthesis_success: bool
    total_attempts: int


class QECEnhancedSynthesizer:
    """
    QEC-Enhanced Policy Synthesizer.
    
    Integrates QEC-inspired resilience mechanisms with the existing GS service
    LLM reliability framework to improve synthesis success rates and reduce
    failure recovery time.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the QEC-enhanced synthesizer.
        
        Args:
            config: Configuration dictionary for QEC enhancements
        """
        self.config = config or self._get_default_config()
        
        # Initialize existing GS service components
        reliability_config = LLMReliabilityConfig()
        self.llm_framework = EnhancedLLMReliabilityFramework(reliability_config)
        self.prompt_builder = ConstitutionalPromptBuilder()
        
        # Initialize QEC enhancement components
        self.distance_calculator = ConstitutionalDistanceCalculator()
        self.validation_parser = ValidationDSLParser()
        self.error_predictor = ErrorPredictionModel()
        self.recovery_dispatcher = RecoveryStrategyDispatcher()
        
        # Synthesis metrics
        self.synthesis_stats = {
            "total_attempts": 0,
            "successful_syntheses": 0,
            "qec_interventions": 0,
            "recovery_successes": 0
        }
        
        logger.info("QEC-Enhanced Synthesizer initialized")
    
    async def initialize(self):
        """Initialize all framework components."""
        await self.llm_framework.initialize()
        logger.info("QEC-Enhanced Synthesizer fully initialized")
    
    async def synthesize_with_qec(
        self, 
        synthesis_input: QECSynthesisInput
    ) -> QECSynthesisOutput:
        """
        Synthesize policy with QEC-inspired enhancements.
        
        Args:
            synthesis_input: QECSynthesisInput with principle and context
            
        Returns:
            QECSynthesisOutput with enhanced metrics and recovery information
        """
        start_time = time.time()
        principle = synthesis_input.principle
        
        try:
            # Phase 1: Constitutional Distance Assessment
            distance_score = self.distance_calculator.calculate_score(principle)
            logger.debug(f"Constitutional distance for {principle.principle_id}: {distance_score:.3f}")
            
            # Phase 2: Error Prediction
            prediction_result = self.error_predictor.predict_synthesis_challenges(principle)
            logger.debug(f"Error prediction for {principle.principle_id}: risk={prediction_result.overall_risk_score:.3f}")
            
            # Phase 3: Strategy Selection
            synthesis_strategy = self._select_synthesis_strategy(
                distance_score, 
                prediction_result.overall_risk_score,
                prediction_result.recommended_strategy
            )
            
            # Phase 4: Enhanced Synthesis with Recovery
            synthesis_result = await self._execute_synthesis_with_recovery(
                synthesis_input,
                synthesis_strategy,
                prediction_result
            )
            
            # Update statistics
            self.synthesis_stats["total_attempts"] += synthesis_result.total_attempts
            if synthesis_result.synthesis_success:
                self.synthesis_stats["successful_syntheses"] += 1
            if synthesis_result.recovery_strategy_used:
                self.synthesis_stats["qec_interventions"] += 1
                if synthesis_result.synthesis_success:
                    self.synthesis_stats["recovery_successes"] += 1
            
            # Calculate total time
            total_time = time.time() - start_time
            synthesis_result.qec_metadata.update({
                "total_synthesis_time_ms": round(total_time * 1000, 2),
                "qec_version": "1.0.0"
            })
            
            logger.info(f"QEC synthesis completed for {principle.principle_id}: success={synthesis_result.synthesis_success}")
            return synthesis_result
            
        except Exception as e:
            logger.error(f"QEC synthesis failed for {principle.principle_id}: {e}")
            # Return fallback result
            return await self._create_fallback_result(synthesis_input, str(e))
    
    async def _execute_synthesis_with_recovery(
        self,
        synthesis_input: QECSynthesisInput,
        strategy: str,
        prediction_result
    ) -> QECSynthesisOutput:
        """Execute synthesis with recovery mechanisms."""
        principle = synthesis_input.principle
        max_attempts = self.config.get("max_synthesis_attempts", 3)
        
        last_error = None
        recovery_strategy_used = None
        
        for attempt in range(max_attempts):
            try:
                # Attempt synthesis
                llm_output, reliability_metrics = await self.llm_framework.process_with_reliability(
                    synthesis_input.llm_input
                )
                
                # Validate synthesis result
                if self._validate_synthesis_result(llm_output, principle):
                    # Success!
                    return QECSynthesisOutput(
                        llm_output=llm_output,
                        reliability_metrics=reliability_metrics,
                        constitutional_distance=principle.distance_score or 0.0,
                        error_predictions=prediction_result.predicted_failures,
                        recovery_strategy_used=recovery_strategy_used,
                        qec_metadata={
                            "synthesis_strategy": strategy,
                            "attempts_made": attempt + 1,
                            "prediction_accuracy": self._calculate_prediction_accuracy(
                                prediction_result, None
                            )
                        },
                        synthesis_success=True,
                        total_attempts=attempt + 1
                    )
                
            except Exception as e:
                last_error = e
                logger.warning(f"Synthesis attempt {attempt + 1} failed for {principle.principle_id}: {e}")
                
                # Log the failure
                failure_log = SynthesisAttemptLog(
                    attempt_id=f"{principle.principle_id}_{attempt}_{int(time.time())}",
                    principle_id=principle.principle_id,
                    timestamp=datetime.now(),
                    llm_model="gpt-4",  # Would be dynamic in real implementation
                    prompt_template=strategy,
                    failure_type=self._classify_failure_type(e),
                    error_details={"error_message": str(e)},
                    recovery_strategy=None,
                    final_outcome="failed"
                )
                
                # Get recovery strategy for next attempt
                if attempt < max_attempts - 1:
                    recovery_strategy = self.recovery_dispatcher.get_recovery_strategy(
                        failure_log, principle.principle_id
                    )
                    recovery_strategy_used = recovery_strategy
                    
                    # Execute recovery strategy
                    recovery_result = self.recovery_dispatcher.execute_recovery_strategy(
                        recovery_strategy,
                        principle.principle_id,
                        synthesis_input.llm_input.dict(),
                        {"error": str(e), "attempt": attempt}
                    )
                    
                    if not recovery_result.success and recovery_strategy == RecoveryStrategy.ESCALATE_TO_HUMAN:
                        # Human escalation required
                        break
        
        # All attempts failed
        return QECSynthesisOutput(
            llm_output=LLMStructuredOutput(
                interpretations=[],
                raw_llm_response=f"Synthesis failed after {max_attempts} attempts: {last_error}"
            ),
            reliability_metrics=ReliabilityMetrics(),
            constitutional_distance=principle.distance_score or 0.0,
            error_predictions=prediction_result.predicted_failures,
            recovery_strategy_used=recovery_strategy_used,
            qec_metadata={
                "synthesis_strategy": strategy,
                "attempts_made": max_attempts,
                "final_error": str(last_error),
                "prediction_accuracy": self._calculate_prediction_accuracy(
                    prediction_result, last_error
                )
            },
            synthesis_success=False,
            total_attempts=max_attempts
        )
    
    def _select_synthesis_strategy(
        self, 
        distance_score: float, 
        risk_score: float,
        recommended_strategy: str
    ) -> str:
        """Select synthesis strategy based on QEC assessments."""
        if distance_score < 0.3 or risk_score > 0.8:
            return "high_risk_synthesis"
        elif distance_score < 0.6 or risk_score > 0.6:
            return "enhanced_validation_synthesis"
        elif recommended_strategy == "multi_model_consensus":
            return "consensus_synthesis"
        else:
            return "standard_synthesis"
    
    def _validate_synthesis_result(
        self, 
        llm_output: LLMStructuredOutput, 
        principle: ConstitutionalPrinciple
    ) -> bool:
        """Validate synthesis result quality."""
        # Basic validation checks
        if not llm_output.raw_llm_response:
            return False
        
        if len(llm_output.raw_llm_response) < 50:  # Too short
            return False
        
        # Check for obvious errors
        error_indicators = ["error", "failed", "unable", "cannot"]
        response_lower = llm_output.raw_llm_response.lower()
        if any(indicator in response_lower for indicator in error_indicators):
            return False
        
        # Additional validation based on principle characteristics
        if principle.validation_criteria_structured:
            # Would run structured validation tests here
            pass
        
        return True
    
    def _classify_failure_type(self, error: Exception) -> FailureType:
        """Classify the type of synthesis failure."""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return FailureType.TIMEOUT
        elif "syntax" in error_str:
            return FailureType.SYNTAX_ERROR
        elif "validation" in error_str:
            return FailureType.VALIDATION_FAILED
        elif "confidence" in error_str:
            return FailureType.CONFIDENCE_LOW
        elif "ambiguous" in error_str:
            return FailureType.AMBIGUOUS_PRINCIPLE
        else:
            return FailureType.SEMANTIC_CONFLICT
    
    def _calculate_prediction_accuracy(
        self, 
        prediction_result, 
        actual_error: Optional[Exception]
    ) -> float:
        """Calculate accuracy of error prediction."""
        if actual_error is None:
            # Success case - check if low risk was predicted
            return 1.0 - prediction_result.overall_risk_score
        else:
            # Failure case - check if high risk was predicted
            return prediction_result.overall_risk_score
    
    async def _create_fallback_result(
        self, 
        synthesis_input: QECSynthesisInput, 
        error_message: str
    ) -> QECSynthesisOutput:
        """Create fallback result for critical errors."""
        return QECSynthesisOutput(
            llm_output=LLMStructuredOutput(
                interpretations=[],
                raw_llm_response=f"Critical synthesis error: {error_message}"
            ),
            reliability_metrics=ReliabilityMetrics(),
            constitutional_distance=0.0,
            error_predictions={},
            recovery_strategy_used=None,
            qec_metadata={
                "fallback": True,
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            },
            synthesis_success=False,
            total_attempts=1
        )
    
    def get_synthesis_statistics(self) -> Dict[str, Any]:
        """Get synthesis performance statistics."""
        total = self.synthesis_stats["total_attempts"]
        successful = self.synthesis_stats["successful_syntheses"]
        interventions = self.synthesis_stats["qec_interventions"]
        recovery_successes = self.synthesis_stats["recovery_successes"]
        
        return {
            "total_attempts": total,
            "successful_syntheses": successful,
            "success_rate": successful / max(total, 1),
            "qec_interventions": interventions,
            "recovery_successes": recovery_successes,
            "recovery_success_rate": recovery_successes / max(interventions, 1),
            "improvement_from_qec": (recovery_successes / max(total, 1)) if total > 0 else 0.0
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for QEC enhancements."""
        return {
            "max_synthesis_attempts": 3,
            "distance_threshold_high_risk": 0.3,
            "distance_threshold_medium_risk": 0.6,
            "risk_threshold_high": 0.8,
            "risk_threshold_medium": 0.6,
            "enable_recovery_strategies": True,
            "enable_prediction_logging": True
        }
