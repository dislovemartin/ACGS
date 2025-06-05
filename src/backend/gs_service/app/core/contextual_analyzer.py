"""
Contextual Analyzer Module for ACGS-PGP Phase 1

This module implements basic contextual analysis that processes environmental factors
and integrates contextual data during policy generation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class EnvironmentalFactor:
    """Represents an environmental factor that can influence policy generation."""
    
    def __init__(
        self, 
        factor_id: str, 
        factor_type: str, 
        value: Any, 
        timestamp: Optional[datetime] = None,
        source: Optional[str] = None,
        confidence: float = 1.0
    ):
        self.factor_id = factor_id
        self.factor_type = factor_type  # e.g., "regulatory", "operational", "technical", "social"
        self.value = value
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.source = source
        self.confidence = confidence  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "factor_type": self.factor_type,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "confidence": self.confidence
        }


class ContextualAnalyzer:
    """
    Analyzes environmental factors and provides contextual insights for policy generation.
    
    This is a basic implementation for Phase 1 that focuses on:
    1. Environmental factor processing
    2. Context similarity matching
    3. Change detection
    4. Contextual rule adaptation triggers
    """
    
    def __init__(self):
        self.environmental_factors: Dict[str, EnvironmentalFactor] = {}
        self.context_history: List[Dict[str, Any]] = []
        self.similarity_threshold = 0.7  # Threshold for context similarity matching
        
    def add_environmental_factor(self, factor: EnvironmentalFactor) -> None:
        """Add or update an environmental factor."""
        self.environmental_factors[factor.factor_id] = factor
        logger.info(f"Added environmental factor: {factor.factor_id} ({factor.factor_type})")
    
    def get_environmental_factors_by_type(self, factor_type: str) -> List[EnvironmentalFactor]:
        """Get all environmental factors of a specific type."""
        return [
            factor for factor in self.environmental_factors.values() 
            if factor.factor_type == factor_type
        ]
    
    def analyze_context(self, context: str, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a given context and return contextual insights.
        
        Args:
            context: The target context for analysis
            additional_data: Additional contextual data to consider
            
        Returns:
            Dictionary containing contextual analysis results
        """
        logger.info(f"Analyzing context: {context}")
        
        # Get relevant environmental factors
        relevant_factors = self._get_relevant_factors(context)
        
        # Perform context similarity analysis
        similar_contexts = self._find_similar_contexts(context)
        
        # Detect environmental changes
        changes = self._detect_environmental_changes(context)
        
        # Generate contextual recommendations
        recommendations = self._generate_contextual_recommendations(
            context, relevant_factors, changes
        )
        
        analysis_result = {
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "relevant_factors": [factor.to_dict() for factor in relevant_factors],
            "similar_contexts": similar_contexts,
            "environmental_changes": changes,
            "recommendations": recommendations,
            "additional_data": additional_data or {},
            "analysis_metadata": {
                "factor_count": len(relevant_factors),
                "similarity_matches": len(similar_contexts),
                "change_count": len(changes),
                "analyzer_version": "1.0.0"
            }
        }
        
        # Store in context history for future analysis
        self.context_history.append(analysis_result)
        
        logger.info(f"Context analysis completed for '{context}' with {len(relevant_factors)} relevant factors")
        return analysis_result
    
    def _get_relevant_factors(self, context: str) -> List[EnvironmentalFactor]:
        """Get environmental factors relevant to the given context."""
        relevant_factors = []
        
        # Simple keyword-based relevance matching
        # In a more sophisticated implementation, this could use NLP or ML
        context_lower = context.lower()
        
        for factor in self.environmental_factors.values():
            # Check if factor is relevant based on context keywords
            if self._is_factor_relevant(factor, context_lower):
                relevant_factors.append(factor)
        
        # Sort by confidence and recency
        relevant_factors.sort(
            key=lambda f: (f.confidence, f.timestamp), 
            reverse=True
        )
        
        return relevant_factors
    
    def _is_factor_relevant(self, factor: EnvironmentalFactor, context_lower: str) -> bool:
        """Determine if an environmental factor is relevant to the context."""
        # Basic keyword matching - could be enhanced with semantic analysis
        factor_keywords = {
            "regulatory": ["compliance", "regulation", "legal", "audit", "policy"],
            "operational": ["performance", "efficiency", "operation", "workflow", "process"],
            "technical": ["security", "infrastructure", "system", "technology", "data"],
            "social": ["user", "stakeholder", "community", "public", "social"]
        }
        
        # Check if context contains keywords related to the factor type
        relevant_keywords = factor_keywords.get(factor.factor_type, [])
        for keyword in relevant_keywords:
            if keyword in context_lower:
                return True
        
        # Check if factor value contains context-related information
        if isinstance(factor.value, str) and any(
            keyword in factor.value.lower() for keyword in context_lower.split()
        ):
            return True
        
        return False
    
    def _find_similar_contexts(self, context: str) -> List[Dict[str, Any]]:
        """Find historically similar contexts."""
        similar_contexts = []
        
        for historical_context in self.context_history:
            similarity_score = self._calculate_context_similarity(
                context, historical_context["context"]
            )
            
            if similarity_score >= self.similarity_threshold:
                similar_contexts.append({
                    "context": historical_context["context"],
                    "similarity_score": similarity_score,
                    "timestamp": historical_context["timestamp"],
                    "factor_count": historical_context["analysis_metadata"]["factor_count"]
                })
        
        # Sort by similarity score
        similar_contexts.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar_contexts[:5]  # Return top 5 similar contexts
    
    def _calculate_context_similarity(self, context1: str, context2: str) -> float:
        """Calculate similarity between two contexts using simple word overlap."""
        # Simple Jaccard similarity - could be enhanced with semantic embeddings
        words1 = set(context1.lower().split())
        words2 = set(context2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _detect_environmental_changes(self, context: str) -> List[Dict[str, Any]]:
        """Detect recent changes in environmental factors relevant to the context."""
        changes = []
        
        # Look for factors that have changed recently (within last hour for demo)
        current_time = datetime.now(timezone.utc)
        
        for factor in self.environmental_factors.values():
            if self._is_factor_relevant(factor, context.lower()):
                # Check if this factor has changed recently
                time_diff = current_time - factor.timestamp
                if time_diff.total_seconds() < 3600:  # Within last hour
                    changes.append({
                        "factor_id": factor.factor_id,
                        "factor_type": factor.factor_type,
                        "change_type": "recent_update",
                        "timestamp": factor.timestamp.isoformat(),
                        "confidence": factor.confidence
                    })
        
        return changes
    
    def _generate_contextual_recommendations(
        self, 
        context: str, 
        relevant_factors: List[EnvironmentalFactor],
        changes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate contextual recommendations for policy adaptation."""
        recommendations = []
        
        # Recommendation based on high-confidence factors
        high_confidence_factors = [f for f in relevant_factors if f.confidence > 0.8]
        if high_confidence_factors:
            recommendations.append({
                "type": "high_confidence_factors",
                "description": f"Consider {len(high_confidence_factors)} high-confidence environmental factors",
                "priority": "HIGH",
                "factors": [f.factor_id for f in high_confidence_factors]
            })
        
        # Recommendation based on recent changes
        if changes:
            recommendations.append({
                "type": "environmental_changes",
                "description": f"Adapt policies due to {len(changes)} recent environmental changes",
                "priority": "MEDIUM",
                "changes": [c["factor_id"] for c in changes]
            })
        
        # Recommendation based on factor diversity
        factor_types = set(f.factor_type for f in relevant_factors)
        if len(factor_types) > 2:
            recommendations.append({
                "type": "multi_dimensional_context",
                "description": f"Context spans {len(factor_types)} environmental dimensions",
                "priority": "LOW",
                "dimensions": list(factor_types)
            })
        
        return recommendations
    
    def get_context_adaptation_triggers(self, context: str) -> Dict[str, Any]:
        """
        Get triggers that indicate when policies should be adapted for the given context.
        """
        analysis = self.analyze_context(context)
        
        triggers = {
            "immediate_triggers": [],
            "scheduled_triggers": [],
            "conditional_triggers": []
        }
        
        # Immediate triggers based on high-priority changes
        for change in analysis["environmental_changes"]:
            if change.get("confidence", 0) > 0.9:
                triggers["immediate_triggers"].append({
                    "trigger_type": "environmental_change",
                    "factor_id": change["factor_id"],
                    "reason": "High-confidence environmental change detected"
                })
        
        # Conditional triggers based on factor combinations
        regulatory_factors = [f for f in analysis["relevant_factors"] if f["factor_type"] == "regulatory"]
        if len(regulatory_factors) > 1:
            triggers["conditional_triggers"].append({
                "trigger_type": "regulatory_complexity",
                "condition": "Multiple regulatory factors present",
                "factor_count": len(regulatory_factors)
            })
        
        return triggers


# Global instance for use across the GS service
contextual_analyzer = ContextualAnalyzer()
