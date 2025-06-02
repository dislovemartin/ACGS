"""
QEC-Enhanced Conflict Resolution Service

Integrates QEC (Quality, Error, and Correction) principles with conflict resolution
workflows for intelligent automated patch suggestions and validation.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..models import ACPrinciple, ACConflictResolution
from ..schemas import ACConflictResolutionCreate, ACConflictResolutionUpdate

# Import QEC enhancement components
try:
    from alphaevolve_gs_engine.services.qec_enhancement import (
        ConstitutionalDistanceCalculator,
        ErrorPredictionModel,
        RecoveryStrategyDispatcher,
        ValidationDSLParser,
        FailureType,
        RecoveryStrategy
    )
    from alphaevolve_gs_engine.core.constitutional_principle import ConstitutionalPrinciple
    QEC_AVAILABLE = True
except ImportError:
    QEC_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ConflictAnalysis:
    """Results of QEC-enhanced conflict analysis."""
    conflict_id: int
    constitutional_distances: List[float]
    average_distance: float
    error_predictions: List[Dict[str, Any]]
    recommended_strategy: Optional[str]
    validation_scenarios: List[Dict[str, Any]]
    priority_score: float
    qec_metadata: Dict[str, Any]


@dataclass
class PatchResult:
    """Results of automated patch generation."""
    success: bool
    patch_content: Optional[str]
    strategy_used: Optional[str]
    validation_tests: List[Dict[str, Any]]
    confidence_score: float
    metadata: Dict[str, Any]


class QECConflictResolver:
    """
    QEC-Enhanced Conflict Resolution Service.
    
    Integrates constitutional distance scoring, error prediction, recovery strategies,
    and validation DSL parsing for intelligent conflict resolution.
    """
    
    def __init__(self):
        """Initialize QEC components if available."""
        self.qec_available = QEC_AVAILABLE
        
        if self.qec_available:
            self.distance_calculator = ConstitutionalDistanceCalculator()
            self.error_predictor = ErrorPredictionModel()
            self.recovery_dispatcher = RecoveryStrategyDispatcher()
            self.validation_parser = ValidationDSLParser()
        else:
            logger.warning("QEC components not available - using fallback implementations")
    
    async def analyze_conflict(
        self, 
        conflict: ACConflictResolution, 
        principles: List[ACPrinciple]
    ) -> ConflictAnalysis:
        """
        Perform comprehensive QEC-enhanced conflict analysis.
        
        Args:
            conflict: The conflict resolution to analyze
            principles: List of principles involved in the conflict
            
        Returns:
            ConflictAnalysis with QEC insights
        """
        if not self.qec_available:
            return self._fallback_analysis(conflict, principles)
        
        try:
            # Convert AC principles to Constitutional principles for QEC processing
            constitutional_principles = self._convert_to_constitutional_principles(principles)
            
            # Calculate constitutional distances for prioritization
            distance_scores = []
            for principle in constitutional_principles:
                score = self.distance_calculator.calculate_distance(principle)
                distance_scores.append(score)
            
            # Predict potential synthesis challenges
            error_predictions = []
            for principle in constitutional_principles:
                prediction = self.error_predictor.predict_synthesis_challenges(principle)
                error_predictions.append({
                    "principle_id": principle.principle_id,
                    "overall_risk": prediction.overall_risk,
                    "failure_predictions": {
                        failure_type.value: prob 
                        for failure_type, prob in prediction.failure_predictions.items()
                    },
                    "recommended_strategy": prediction.recommended_strategy,
                    "confidence": prediction.confidence
                })
            
            # Recommend recovery strategy
            recovery_strategy = self.recovery_dispatcher.recommend_strategy(
                conflict_type=conflict.conflict_type,
                severity=conflict.severity,
                error_predictions=error_predictions
            )
            
            # Generate validation scenarios
            validation_scenarios = []
            for principle in constitutional_principles:
                if principle.validation_criteria_structured:
                    scenario = self.validation_parser.parse_validation_criteria(
                        principle.validation_criteria_structured
                    )
                    validation_scenarios.append({
                        "principle_id": principle.principle_id,
                        "scenario_type": scenario.scenario_type,
                        "test_cases": len(scenario.test_cases),
                        "validation_rules": scenario.validation_rules
                    })
            
            # Calculate priority score based on distance and risk
            average_distance = sum(distance_scores) / len(distance_scores) if distance_scores else 0
            average_risk = sum(pred["overall_risk"] for pred in error_predictions) / len(error_predictions) if error_predictions else 0
            priority_score = self._calculate_priority_score(
                average_distance, average_risk, conflict.severity
            )
            
            # Prepare QEC metadata
            qec_metadata = {
                "analysis_timestamp": datetime.now().isoformat(),
                "qec_version": "1.0.0",
                "distance_calculation": {
                    "scores": distance_scores,
                    "average": average_distance,
                    "calculator_version": "1.0.0"
                },
                "error_prediction": {
                    "predictions": error_predictions,
                    "model_accuracy": self.error_predictor.model_accuracy,
                    "model_version": "1.0.0"
                },
                "recovery_strategy": {
                    "recommended": recovery_strategy.strategy_type.value if recovery_strategy else None,
                    "confidence": recovery_strategy.confidence if recovery_strategy else 0,
                    "dispatcher_version": "1.0.0"
                },
                "validation": {
                    "scenarios_generated": len(validation_scenarios),
                    "parser_version": "1.0.0"
                }
            }
            
            return ConflictAnalysis(
                conflict_id=conflict.id,
                constitutional_distances=distance_scores,
                average_distance=average_distance,
                error_predictions=error_predictions,
                recommended_strategy=recovery_strategy.strategy_type.value if recovery_strategy else None,
                validation_scenarios=validation_scenarios,
                priority_score=priority_score,
                qec_metadata=qec_metadata
            )
            
        except Exception as e:
            logger.error(f"QEC conflict analysis failed: {e}")
            return self._fallback_analysis(conflict, principles)
    
    async def generate_patch(
        self, 
        conflict: ACConflictResolution, 
        principles: List[ACPrinciple],
        analysis: ConflictAnalysis
    ) -> PatchResult:
        """
        Generate automated patch for conflict resolution using QEC insights.
        
        Args:
            conflict: The conflict resolution
            principles: List of principles involved
            analysis: Previous QEC analysis results
            
        Returns:
            PatchResult with generated patch and validation tests
        """
        if not self.qec_available:
            return self._fallback_patch_generation(conflict, principles)
        
        try:
            # Convert principles for QEC processing
            constitutional_principles = self._convert_to_constitutional_principles(principles)
            
            # Apply recovery strategy based on analysis
            recovery_result = await self.recovery_dispatcher.apply_strategy(
                conflict_type=conflict.conflict_type,
                principles=constitutional_principles,
                context={
                    "conflict_id": conflict.id,
                    "analysis": analysis.qec_metadata,
                    "severity": conflict.severity
                }
            )
            
            # Generate validation tests using DSL parser
            validation_tests = []
            for scenario_data in analysis.validation_scenarios:
                # Create test specifications based on validation scenarios
                test_spec = {
                    "principle_id": scenario_data["principle_id"],
                    "test_type": scenario_data["scenario_type"],
                    "test_cases": scenario_data["test_cases"],
                    "validation_rules": scenario_data["validation_rules"],
                    "expected_outcome": "pass"
                }
                validation_tests.append(test_spec)
            
            # Calculate confidence score
            confidence_score = self._calculate_patch_confidence(
                recovery_result, analysis, len(validation_tests)
            )
            
            # Prepare patch metadata
            patch_metadata = {
                "generation_timestamp": datetime.now().isoformat(),
                "strategy_applied": recovery_result.strategy_applied.value if recovery_result.strategy_applied else None,
                "recovery_success": recovery_result.success,
                "validation_tests_generated": len(validation_tests),
                "confidence_score": confidence_score,
                "qec_analysis_used": analysis.conflict_id,
                "patch_version": "1.0.0"
            }
            
            return PatchResult(
                success=recovery_result.success,
                patch_content=recovery_result.metadata.get("patch_content"),
                strategy_used=recovery_result.strategy_applied.value if recovery_result.strategy_applied else None,
                validation_tests=validation_tests,
                confidence_score=confidence_score,
                metadata=patch_metadata
            )
            
        except Exception as e:
            logger.error(f"QEC patch generation failed: {e}")
            return self._fallback_patch_generation(conflict, principles)
    
    def prioritize_conflicts(
        self, 
        conflicts: List[Tuple[ACConflictResolution, ConflictAnalysis]]
    ) -> List[Tuple[ACConflictResolution, ConflictAnalysis]]:
        """
        Prioritize conflicts based on QEC analysis.
        
        Args:
            conflicts: List of (conflict, analysis) tuples
            
        Returns:
            Sorted list with highest priority conflicts first
        """
        try:
            # Sort by priority score (higher score = higher priority)
            return sorted(
                conflicts, 
                key=lambda x: x[1].priority_score, 
                reverse=True
            )
        except Exception as e:
            logger.error(f"Conflict prioritization failed: {e}")
            return conflicts
    
    def _convert_to_constitutional_principles(
        self, 
        ac_principles: List[ACPrinciple]
    ) -> List[ConstitutionalPrinciple]:
        """Convert AC principles to Constitutional principles for QEC processing."""
        constitutional_principles = []
        
        for ac_principle in ac_principles:
            # Create ConstitutionalPrinciple with QEC fields
            constitutional_principle = ConstitutionalPrinciple(
                principle_id=str(ac_principle.id),
                title=ac_principle.title,
                description=ac_principle.description,
                category=ac_principle.category or "general",
                priority_weight=ac_principle.priority_weight or 1.0,
                scope=ac_principle.scope or "general",
                normative_statement=ac_principle.normative_statement or ac_principle.description,
                constraints=ac_principle.constraints or {},
                rationale=ac_principle.rationale or "",
                validation_criteria_structured=ac_principle.validation_criteria_structured or {},
                distance_score=getattr(ac_principle, 'distance_score', None),
                score_updated_at=getattr(ac_principle, 'score_updated_at', None),
                error_prediction_metadata=getattr(ac_principle, 'error_prediction_metadata', {}),
                recovery_strategies=getattr(ac_principle, 'recovery_strategies', [])
            )
            constitutional_principles.append(constitutional_principle)
        
        return constitutional_principles
    
    def _calculate_priority_score(
        self, 
        average_distance: float, 
        average_risk: float, 
        severity: str
    ) -> float:
        """Calculate priority score for conflict resolution."""
        # Base score from constitutional distance (lower distance = higher priority)
        distance_score = 1.0 - average_distance
        
        # Risk factor (higher risk = higher priority)
        risk_score = average_risk
        
        # Severity multiplier
        severity_multipliers = {
            "critical": 2.0,
            "high": 1.5,
            "medium": 1.0,
            "low": 0.5
        }
        severity_multiplier = severity_multipliers.get(severity, 1.0)
        
        # Combined priority score
        priority_score = (distance_score * 0.4 + risk_score * 0.6) * severity_multiplier
        
        return min(priority_score, 1.0)  # Cap at 1.0
    
    def _calculate_patch_confidence(
        self, 
        recovery_result, 
        analysis: ConflictAnalysis, 
        validation_tests_count: int
    ) -> float:
        """Calculate confidence score for generated patch."""
        base_confidence = 0.7 if recovery_result.success else 0.3
        
        # Boost confidence based on analysis quality
        distance_confidence = 1.0 - analysis.average_distance
        validation_confidence = min(validation_tests_count / 5.0, 1.0)  # Max boost at 5 tests
        
        # Combined confidence
        confidence = (base_confidence * 0.5 + 
                     distance_confidence * 0.3 + 
                     validation_confidence * 0.2)
        
        return min(confidence, 1.0)
    
    def _fallback_analysis(
        self, 
        conflict: ACConflictResolution, 
        principles: List[ACPrinciple]
    ) -> ConflictAnalysis:
        """Fallback analysis when QEC components are not available."""
        return ConflictAnalysis(
            conflict_id=conflict.id,
            constitutional_distances=[0.5] * len(principles),
            average_distance=0.5,
            error_predictions=[],
            recommended_strategy="manual_review",
            validation_scenarios=[],
            priority_score=0.5,
            qec_metadata={"fallback": True, "timestamp": datetime.now().isoformat()}
        )
    
    def _fallback_patch_generation(
        self, 
        conflict: ACConflictResolution, 
        principles: List[ACPrinciple]
    ) -> PatchResult:
        """Fallback patch generation when QEC components are not available."""
        return PatchResult(
            success=False,
            patch_content=None,
            strategy_used="manual_review_required",
            validation_tests=[],
            confidence_score=0.0,
            metadata={"fallback": True, "timestamp": datetime.now().isoformat()}
        )
