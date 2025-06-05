"""
error_prediction_model.py

QEC-inspired Error Prediction Model for anticipating and diagnosing LLM synthesis failures.
Enables proactive mitigation and faster recovery through predictive failure analysis.

Classes:
    ErrorPredictionModel: Main model for predicting synthesis failures
    FailureType: Enumeration of failure types
    SynthesisAttemptLog: Data structure for logging synthesis attempts
    PredictionResult: Result structure for error predictions
"""

import logging
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ...core.constitutional_principle import ConstitutionalPrinciple

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Enumeration of synthesis failure types."""
    SYNTAX_ERROR = "syntax_error"
    SEMANTIC_CONFLICT = "semantic_conflict"
    TIMEOUT = "timeout"
    CONFIDENCE_LOW = "confidence_low"
    VALIDATION_FAILED = "validation_failed"
    AMBIGUOUS_PRINCIPLE = "ambiguous_principle"
    BIAS_DETECTED = "bias_detected"
    COMPLEXITY_HIGH = "complexity_high"


@dataclass
class SynthesisAttemptLog:
    """Data structure for logging synthesis attempts."""
    attempt_id: str
    principle_id: str
    timestamp: datetime
    llm_model: str
    prompt_template: str
    failure_type: Optional[FailureType]
    error_details: Dict[str, Any]
    recovery_strategy: Optional[str]
    final_outcome: str
    prediction_accuracy: Optional[float] = None


@dataclass
class PredictionResult:
    """Result structure for error predictions."""
    principle_id: str
    predicted_failures: Dict[FailureType, float]  # Failure type -> confidence
    overall_risk_score: float  # 0.0-1.0, higher = more likely to fail
    recommended_strategy: str
    confidence: float
    prediction_metadata: Dict[str, Any]


class ErrorPredictionModel:
    """
    QEC-inspired Error Prediction Model.
    
    Anticipates and diagnoses LLM synthesis failures using historical patterns
    and principle characteristics, enabling proactive mitigation and faster recovery.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the error prediction model.
        
        Args:
            config: Configuration dictionary for model settings
        """
        self.config = config or self._get_default_config()
        
        # Historical data storage
        self.attempt_logs: List[SynthesisAttemptLog] = []
        self.failure_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Model state
        self.model_accuracy = 0.75  # Initial accuracy estimate
        self.last_training_time = datetime.now()
        
        # Feature extractors
        self._feature_extractors = self._initialize_feature_extractors()
        
        logger.info("Error Prediction Model initialized")
    
    def predict_synthesis_challenges(
        self, 
        principle: ConstitutionalPrinciple
    ) -> PredictionResult:
        """
        Predict potential synthesis challenges for a principle.
        
        Args:
            principle: ConstitutionalPrinciple to analyze
            
        Returns:
            PredictionResult with failure predictions and recommendations
        """
        start_time = time.time()
        
        try:
            # Extract features from principle
            features = self._extract_features(principle)
            
            # Predict failure probabilities for each type
            failure_predictions = {}
            for failure_type in FailureType:
                probability = self._predict_failure_probability(features, failure_type)
                failure_predictions[failure_type] = probability
            
            # Calculate overall risk score
            overall_risk = self._calculate_overall_risk(failure_predictions)
            
            # Recommend strategy based on predictions
            recommended_strategy = self._recommend_strategy(failure_predictions, overall_risk)
            
            # Calculate prediction confidence
            confidence = self._calculate_prediction_confidence(features, failure_predictions)
            
            # Prepare metadata
            prediction_time = time.time() - start_time
            metadata = {
                "prediction_timestamp": datetime.now().isoformat(),
                "prediction_time_ms": round(prediction_time * 1000, 2),
                "features_used": list(features.keys()),
                "model_accuracy": self.model_accuracy,
                "model_version": "1.0.0"
            }
            
            result = PredictionResult(
                principle_id=principle.principle_id,
                predicted_failures=failure_predictions,
                overall_risk_score=overall_risk,
                recommended_strategy=recommended_strategy,
                confidence=confidence,
                prediction_metadata=metadata
            )
            
            # Update principle metadata
            principle.error_prediction_metadata.update({
                "last_prediction": {
                    "timestamp": datetime.now().isoformat(),
                    "overall_risk": overall_risk,
                    "top_risks": self._get_top_risks(failure_predictions, 3)
                }
            })
            
            logger.debug(f"Predicted synthesis challenges for {principle.principle_id}: risk={overall_risk:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error predicting synthesis challenges for {principle.principle_id}: {e}")
            # Return conservative prediction
            return self._get_fallback_prediction(principle.principle_id)
    
    def log_synthesis_attempt(self, log_entry: SynthesisAttemptLog) -> None:
        """
        Log a synthesis attempt for model training.
        
        Args:
            log_entry: SynthesisAttemptLog with attempt details
        """
        self.attempt_logs.append(log_entry)
        
        # Update failure patterns
        self._update_failure_patterns(log_entry)
        
        # Trigger retraining if enough new data
        if len(self.attempt_logs) % self.config.get("retrain_interval", 100) == 0:
            self._retrain_model()
        
        logger.debug(f"Logged synthesis attempt {log_entry.attempt_id}")
    
    def diagnose_failure(self, log_entry: SynthesisAttemptLog) -> Dict[str, Any]:
        """
        Diagnose a synthesis failure and provide insights.
        
        Args:
            log_entry: SynthesisAttemptLog with failure details
            
        Returns:
            Diagnosis with insights and recommendations
        """
        diagnosis = {
            "failure_type": log_entry.failure_type.value if log_entry.failure_type else "unknown",
            "likely_causes": [],
            "recommendations": [],
            "similar_failures": [],
            "diagnosis_timestamp": datetime.now().isoformat()
        }
        
        if log_entry.failure_type:
            # Find similar failures
            similar_failures = self._find_similar_failures(log_entry)
            diagnosis["similar_failures"] = [
                {
                    "attempt_id": failure.attempt_id,
                    "principle_id": failure.principle_id,
                    "timestamp": failure.timestamp.isoformat(),
                    "recovery_strategy": failure.recovery_strategy
                }
                for failure in similar_failures[:5]  # Top 5 similar failures
            ]
            
            # Generate recommendations based on failure type
            diagnosis["recommendations"] = self._get_failure_recommendations(log_entry.failure_type)
            
            # Identify likely causes
            diagnosis["likely_causes"] = self._identify_failure_causes(log_entry)
        
        return diagnosis
    
    def _extract_features(self, principle: ConstitutionalPrinciple) -> Dict[str, float]:
        """Extract features from a constitutional principle."""
        features = {}
        
        # Text-based features
        description = principle.description or ""
        features["description_length"] = len(description)
        features["description_complexity"] = self._calculate_text_complexity(description)
        features["ambiguity_score"] = self._calculate_ambiguity_score(description)
        
        # Structural features
        features["has_structured_criteria"] = 1.0 if principle.validation_criteria_structured else 0.0
        features["criteria_count"] = len(principle.validation_criteria_structured)
        features["has_dependencies"] = 1.0 if principle.dependencies else 0.0
        features["dependency_count"] = len(principle.dependencies)
        
        # Historical features
        features["distance_score"] = principle.distance_score or 0.5
        features["principle_age_days"] = (datetime.now() - principle.creation_date).days
        features["version_count"] = principle.version
        
        # Category-based features
        category_weights = {
            "Safety": 0.8,
            "Fairness": 0.7,
            "Efficiency": 0.5,
            "Robustness": 0.6,
            "Transparency": 0.4,
            "Domain-Specific": 0.6
        }
        features["category_complexity"] = category_weights.get(principle.category, 0.5)
        
        return features
    
    def _predict_failure_probability(
        self, 
        features: Dict[str, float], 
        failure_type: FailureType
    ) -> float:
        """Predict probability of a specific failure type."""
        # Simple heuristic-based prediction (would be ML model in production)
        base_probability = 0.1
        
        if failure_type == FailureType.SYNTAX_ERROR:
            # Higher probability for complex descriptions
            probability = base_probability + (features.get("description_complexity", 0) * 0.3)
        elif failure_type == FailureType.SEMANTIC_CONFLICT:
            # Higher probability for ambiguous principles
            probability = base_probability + (features.get("ambiguity_score", 0) * 0.4)
        elif failure_type == FailureType.AMBIGUOUS_PRINCIPLE:
            # Directly related to ambiguity score
            probability = features.get("ambiguity_score", 0.5)
        elif failure_type == FailureType.COMPLEXITY_HIGH:
            # Related to multiple complexity factors
            complexity_factors = [
                features.get("description_complexity", 0),
                features.get("criteria_count", 0) / 10.0,  # Normalize
                features.get("category_complexity", 0)
            ]
            probability = base_probability + (sum(complexity_factors) / len(complexity_factors) * 0.5)
        else:
            # Default probability for other failure types
            probability = base_probability + (features.get("description_complexity", 0) * 0.2)
        
        return min(probability, 1.0)
    
    def _calculate_overall_risk(self, failure_predictions: Dict[FailureType, float]) -> float:
        """Calculate overall risk score from individual failure predictions."""
        # Weight different failure types by severity
        weights = {
            FailureType.SYNTAX_ERROR: 0.8,
            FailureType.SEMANTIC_CONFLICT: 1.0,
            FailureType.TIMEOUT: 0.6,
            FailureType.CONFIDENCE_LOW: 0.7,
            FailureType.VALIDATION_FAILED: 0.9,
            FailureType.AMBIGUOUS_PRINCIPLE: 0.8,
            FailureType.BIAS_DETECTED: 1.0,
            FailureType.COMPLEXITY_HIGH: 0.7
        }
        
        weighted_sum = sum(
            failure_predictions[failure_type] * weights.get(failure_type, 0.5)
            for failure_type in failure_predictions
        )
        
        # Normalize by total weight
        total_weight = sum(weights.values())
        return min(weighted_sum / total_weight, 1.0)
    
    def _recommend_strategy(
        self, 
        failure_predictions: Dict[FailureType, float], 
        overall_risk: float
    ) -> str:
        """Recommend synthesis strategy based on predictions."""
        if overall_risk < 0.3:
            return "standard_synthesis"
        elif overall_risk < 0.6:
            return "enhanced_validation"
        elif overall_risk < 0.8:
            return "multi_model_consensus"
        else:
            return "human_review_required"
    
    def _calculate_prediction_confidence(
        self, 
        features: Dict[str, float], 
        predictions: Dict[FailureType, float]
    ) -> float:
        """Calculate confidence in the prediction."""
        # Base confidence on model accuracy and feature completeness
        feature_completeness = len([v for v in features.values() if v > 0]) / len(features)
        return self.model_accuracy * feature_completeness
    
    def _get_top_risks(self, predictions: Dict[FailureType, float], count: int) -> List[Dict[str, Any]]:
        """Get top risk factors from predictions."""
        sorted_risks = sorted(
            predictions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {"failure_type": risk[0].value, "probability": risk[1]}
            for risk in sorted_risks[:count]
        ]
    
    def _calculate_text_complexity(self, text: str) -> float:
        """Calculate text complexity score."""
        if not text:
            return 0.0
        
        # Simple complexity metrics
        word_count = len(text.split())
        sentence_count = len([s for s in text.split('.') if s.strip()])
        avg_word_length = sum(len(word) for word in text.split()) / max(word_count, 1)
        
        # Normalize to 0-1 range
        complexity = min((word_count / 100.0) + (avg_word_length / 10.0), 1.0)
        return complexity
    
    def _calculate_ambiguity_score(self, text: str) -> float:
        """Calculate ambiguity score for text."""
        if not text:
            return 1.0
        
        # Simple ambiguity indicators
        ambiguous_terms = ['should', 'might', 'could', 'appropriate', 'reasonable']
        text_lower = text.lower()
        
        ambiguity_count = sum(1 for term in ambiguous_terms if term in text_lower)
        word_count = len(text.split())
        
        return min(ambiguity_count / max(word_count / 10.0, 1), 1.0)
    
    def _get_fallback_prediction(self, principle_id: str) -> PredictionResult:
        """Get conservative fallback prediction."""
        return PredictionResult(
            principle_id=principle_id,
            predicted_failures={failure_type: 0.5 for failure_type in FailureType},
            overall_risk_score=0.5,
            recommended_strategy="enhanced_validation",
            confidence=0.3,
            prediction_metadata={"fallback": True, "timestamp": datetime.now().isoformat()}
        )
    
    def _initialize_feature_extractors(self) -> Dict[str, Any]:
        """Initialize feature extraction components."""
        return {
            "text_analyzer": "simple_heuristic",
            "complexity_calculator": "word_based",
            "ambiguity_detector": "pattern_based"
        }
    
    def _update_failure_patterns(self, log_entry: SynthesisAttemptLog) -> None:
        """Update failure patterns based on new attempt log."""
        if log_entry.failure_type:
            pattern_key = f"{log_entry.principle_id}_{log_entry.failure_type.value}"
            if pattern_key not in self.failure_patterns:
                self.failure_patterns[pattern_key] = {
                    "count": 0,
                    "first_seen": log_entry.timestamp,
                    "last_seen": log_entry.timestamp,
                    "recovery_strategies": []
                }
            
            pattern = self.failure_patterns[pattern_key]
            pattern["count"] += 1
            pattern["last_seen"] = log_entry.timestamp
            
            if log_entry.recovery_strategy:
                pattern["recovery_strategies"].append(log_entry.recovery_strategy)
    
    def _retrain_model(self) -> None:
        """Retrain the prediction model with new data."""
        # In a real implementation, this would retrain an ML model
        # For now, just update accuracy based on recent performance
        recent_logs = [
            log for log in self.attempt_logs[-100:]  # Last 100 attempts
            if log.prediction_accuracy is not None
        ]
        
        if recent_logs:
            avg_accuracy = sum(log.prediction_accuracy for log in recent_logs) / len(recent_logs)
            self.model_accuracy = 0.7 * self.model_accuracy + 0.3 * avg_accuracy
            self.last_training_time = datetime.now()
            
            logger.info(f"Model retrained. New accuracy: {self.model_accuracy:.3f}")
    
    def _find_similar_failures(self, log_entry: SynthesisAttemptLog) -> List[SynthesisAttemptLog]:
        """Find similar failures in historical data."""
        similar_failures = []
        
        for log in self.attempt_logs:
            if (log.failure_type == log_entry.failure_type and 
                log.principle_id != log_entry.principle_id):
                similar_failures.append(log)
        
        # Sort by recency
        similar_failures.sort(key=lambda x: x.timestamp, reverse=True)
        return similar_failures
    
    def _get_failure_recommendations(self, failure_type: FailureType) -> List[str]:
        """Get recommendations for a specific failure type."""
        recommendations = {
            FailureType.SYNTAX_ERROR: [
                "Use simplified syntax prompt template",
                "Enable syntax validation in pipeline",
                "Consider decomposing complex principles"
            ],
            FailureType.SEMANTIC_CONFLICT: [
                "Apply explicit disambiguation prompting",
                "Use multi-model consensus validation",
                "Request human clarification for ambiguous terms"
            ],
            FailureType.AMBIGUOUS_PRINCIPLE: [
                "Enhance principle description with examples",
                "Add structured validation criteria",
                "Request stakeholder clarification"
            ],
            FailureType.COMPLEXITY_HIGH: [
                "Break down into simpler sub-principles",
                "Use iterative refinement approach",
                "Apply domain-specific prompt templates"
            ]
        }
        
        return recommendations.get(failure_type, ["Apply standard recovery procedures"])
    
    def _identify_failure_causes(self, log_entry: SynthesisAttemptLog) -> List[str]:
        """Identify likely causes of a synthesis failure."""
        causes = []
        
        if log_entry.failure_type == FailureType.TIMEOUT:
            causes.append("Complex principle requiring extended processing time")
            causes.append("LLM service performance issues")
        elif log_entry.failure_type == FailureType.SEMANTIC_CONFLICT:
            causes.append("Ambiguous or contradictory principle language")
            causes.append("Insufficient context for interpretation")
        elif log_entry.failure_type == FailureType.SYNTAX_ERROR:
            causes.append("Complex logical structure in principle")
            causes.append("Prompt template not suitable for principle type")
        
        return causes
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the error prediction model."""
        return {
            "retrain_interval": 100,
            "max_log_history": 10000,
            "prediction_cache_ttl": 3600,  # 1 hour
            "confidence_threshold": 0.7
        }
