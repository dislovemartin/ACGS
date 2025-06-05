"""
constitutional_distance_calculator.py

QEC-inspired Constitutional Distance Calculator for measuring principle robustness.
Implements the constitutional distance scoring mechanism from the QEC enhancement blueprint.

Classes:
    ConstitutionalDistanceCalculator: Main calculator for constitutional distance scoring
    DistanceMetrics: Data structure for distance calculation components
"""

import logging
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ...core.constitutional_principle import ConstitutionalPrinciple

logger = logging.getLogger(__name__)


@dataclass
class DistanceMetrics:
    """Data structure for constitutional distance calculation components."""
    language_ambiguity: float  # 0.0-1.0, higher = more ambiguous
    criteria_formality: float  # 0.0-1.0, higher = more formal
    synthesis_reliability: float  # 0.0-1.0, higher = more reliable
    composite_score: float  # 0.0-1.0, higher = more robust
    calculation_metadata: Dict[str, Any]


class ConstitutionalDistanceCalculator:
    """
    QEC-inspired Constitutional Distance Calculator.
    
    Calculates constitutional distance scores to identify high-risk principles
    requiring enhanced validation or human review. Based on the QEC enhancement
    blueprint's constitutional distance scoring mechanism.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the constitutional distance calculator.
        
        Args:
            config: Configuration dictionary with weights and thresholds
        """
        self.config = config or self._get_default_config()
        self.weights = self.config.get("weights", {
            'language_ambiguity': 0.3,
            'criteria_formality': 0.4,
            'synthesis_reliability': 0.3
        })
        
        # Cache for performance optimization
        self._ambiguity_cache = {}
        self._reliability_cache = {}
        
        # Ambiguity detection patterns
        self._ambiguity_patterns = self._load_ambiguity_patterns()
        
        logger.info("Constitutional Distance Calculator initialized")
    
    def calculate_score(self, principle: ConstitutionalPrinciple) -> float:
        """
        Calculate constitutional distance score for a principle.
        
        Args:
            principle: ConstitutionalPrinciple to evaluate
            
        Returns:
            Constitutional distance score (0.0-1.0, higher = more robust)
        """
        start_time = time.time()
        
        try:
            # Calculate component scores
            ambiguity = self._measure_language_ambiguity(principle.description)
            formality = self._assess_criteria_formality(principle)
            reliability = self._get_historical_success_rate(principle.principle_id)
            
            # Calculate weighted composite score
            score = sum(self.weights[k] * v for k, v in {
                'language_ambiguity': 1 - ambiguity,  # Invert ambiguity (lower ambiguity = higher score)
                'criteria_formality': formality,
                'synthesis_reliability': reliability
            }.items())
            
            # Update principle with calculated score
            principle.distance_score = score
            principle.score_updated_at = datetime.now()
            
            # Store calculation metadata
            calculation_time = time.time() - start_time
            metadata = {
                "calculation_timestamp": datetime.now().isoformat(),
                "calculation_time_ms": round(calculation_time * 1000, 2),
                "component_scores": {
                    "language_ambiguity": ambiguity,
                    "criteria_formality": formality,
                    "synthesis_reliability": reliability
                },
                "weights_used": self.weights,
                "calculator_version": "1.0.0"
            }
            
            principle.error_prediction_metadata.update({
                "distance_calculation": metadata
            })
            
            logger.debug(f"Constitutional distance calculated for {principle.principle_id}: {score:.3f}")
            return score
            
        except Exception as e:
            logger.error(f"Error calculating constitutional distance for {principle.principle_id}: {e}")
            return 0.0  # Conservative fallback
    
    def calculate_detailed_metrics(self, principle: ConstitutionalPrinciple) -> DistanceMetrics:
        """
        Calculate detailed constitutional distance metrics.
        
        Args:
            principle: ConstitutionalPrinciple to evaluate
            
        Returns:
            DistanceMetrics with detailed component scores
        """
        start_time = time.time()
        
        # Calculate component scores
        ambiguity = self._measure_language_ambiguity(principle.description)
        formality = self._assess_criteria_formality(principle)
        reliability = self._get_historical_success_rate(principle.principle_id)
        
        # Calculate composite score
        composite_score = sum(self.weights[k] * v for k, v in {
            'language_ambiguity': 1 - ambiguity,
            'criteria_formality': formality,
            'synthesis_reliability': reliability
        }.items())
        
        # Prepare metadata
        calculation_time = time.time() - start_time
        metadata = {
            "calculation_timestamp": datetime.now().isoformat(),
            "calculation_time_ms": round(calculation_time * 1000, 2),
            "principle_id": principle.principle_id,
            "weights_used": self.weights,
            "calculator_version": "1.0.0"
        }
        
        return DistanceMetrics(
            language_ambiguity=ambiguity,
            criteria_formality=formality,
            synthesis_reliability=reliability,
            composite_score=composite_score,
            calculation_metadata=metadata
        )
    
    def _measure_language_ambiguity(self, description: str) -> float:
        """
        Measure language ambiguity using pattern-based analysis.
        
        Args:
            description: Principle description text
            
        Returns:
            Ambiguity score (0.0-1.0, higher = more ambiguous)
        """
        if not description:
            return 1.0  # Maximum ambiguity for empty description
        
        # Check cache first
        cache_key = hash(description)
        if cache_key in self._ambiguity_cache:
            return self._ambiguity_cache[cache_key]
        
        ambiguity_score = 0.0
        text_lower = description.lower()
        
        # Pattern-based ambiguity detection
        for pattern_type, patterns in self._ambiguity_patterns.items():
            pattern_count = sum(1 for pattern in patterns if pattern in text_lower)
            if pattern_count > 0:
                # Weight different pattern types
                weight = {
                    'vague_terms': 0.3,
                    'subjective_language': 0.4,
                    'conditional_statements': 0.2,
                    'undefined_terms': 0.1
                }.get(pattern_type, 0.1)
                
                ambiguity_score += min(pattern_count * weight, 0.5)
        
        # Normalize to 0-1 range
        ambiguity_score = min(ambiguity_score, 1.0)
        
        # Cache result
        self._ambiguity_cache[cache_key] = ambiguity_score
        
        return ambiguity_score
    
    def _assess_criteria_formality(self, principle: ConstitutionalPrinciple) -> float:
        """
        Assess the formality of validation criteria.
        
        Args:
            principle: ConstitutionalPrinciple to evaluate
            
        Returns:
            Formality score (0.0-1.0, higher = more formal)
        """
        if not principle.validation_criteria_structured:
            return 0.0  # No structured criteria
        
        # Check if criteria pass basic validation
        valid_criteria = 0
        total_criteria = len(principle.validation_criteria_structured)
        
        for criterion in principle.validation_criteria_structured:
            if self._validate_criterion_structure(criterion):
                valid_criteria += 1
        
        if total_criteria == 0:
            return 0.0
        
        # Calculate formality score
        base_score = valid_criteria / total_criteria
        
        # Bonus for comprehensive criteria
        if total_criteria >= 3:
            base_score = min(base_score * 1.1, 1.0)
        
        return base_score
    
    def _get_historical_success_rate(self, principle_id: str) -> float:
        """
        Get historical synthesis success rate for a principle.
        
        Args:
            principle_id: Principle identifier
            
        Returns:
            Success rate (0.0-1.0, higher = more reliable)
        """
        # Check cache first
        if principle_id in self._reliability_cache:
            cached_data = self._reliability_cache[principle_id]
            # Use cached data if less than 1 hour old
            if datetime.now() - cached_data['timestamp'] < timedelta(hours=1):
                return cached_data['success_rate']
        
        # In a real implementation, this would query historical synthesis data
        # For now, return a default based on principle characteristics
        default_rate = 0.75  # Conservative default
        
        # Cache the result
        self._reliability_cache[principle_id] = {
            'success_rate': default_rate,
            'timestamp': datetime.now()
        }
        
        return default_rate
    
    def _validate_criterion_structure(self, criterion: Dict[str, Any]) -> bool:
        """
        Validate the structure of a validation criterion.
        
        Args:
            criterion: Validation criterion dictionary
            
        Returns:
            True if criterion has valid structure
        """
        required_fields = ['id', 'given', 'when', 'then']
        return all(field in criterion and criterion[field] for field in required_fields)
    
    def _load_ambiguity_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for ambiguity detection."""
        return {
            'vague_terms': [
                'appropriate', 'reasonable', 'sufficient', 'adequate', 'proper',
                'suitable', 'acceptable', 'relevant', 'significant', 'substantial'
            ],
            'subjective_language': [
                'should', 'might', 'could', 'may', 'possibly', 'probably',
                'likely', 'generally', 'typically', 'usually'
            ],
            'conditional_statements': [
                'if possible', 'when appropriate', 'as needed', 'where applicable',
                'if necessary', 'when feasible'
            ],
            'undefined_terms': [
                'best practices', 'industry standards', 'common sense',
                'reasonable person', 'good faith'
            ]
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the calculator."""
        return {
            "weights": {
                'language_ambiguity': 0.3,
                'criteria_formality': 0.4,
                'synthesis_reliability': 0.3
            },
            "thresholds": {
                "high_risk": 0.3,
                "medium_risk": 0.6,
                "low_risk": 0.8
            },
            "cache_ttl_hours": 1
        }
