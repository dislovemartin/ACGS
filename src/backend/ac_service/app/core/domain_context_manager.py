"""
Domain Context Manager for ACGS-PGP Task 13

Implements domain metadata management and context-aware principle adaptation logic
that maintains constitutional fidelity across different domains.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from shared.models import DomainContext, Principle

logger = logging.getLogger(__name__)


class AdaptationStrategy(str, Enum):
    """Strategies for adapting principles to domain contexts."""
    CONSERVATIVE = "conservative"  # Minimal changes, preserve original intent
    CONTEXTUAL = "contextual"     # Adapt to domain-specific requirements
    TRANSFORMATIVE = "transformative"  # Significant adaptation for domain fit


@dataclass
class PrincipleAdaptation:
    """Result of principle adaptation to domain context."""
    original_principle_id: int
    adapted_content: str
    adaptation_strategy: AdaptationStrategy
    adaptation_rationale: str
    constitutional_fidelity_score: float  # 0.0 to 1.0
    domain_fit_score: float  # 0.0 to 1.0
    adaptation_metadata: Dict[str, Any]


@dataclass
class CrossDomainMapping:
    """Mapping between principles across domains."""
    source_principle_id: int
    target_principle_id: int
    source_domain_id: int
    target_domain_id: int
    mapping_type: str  # "equivalent", "adapted", "conflicting", "complementary"
    similarity_score: float  # 0.0 to 1.0
    conflict_indicators: List[str]
    resolution_recommendations: List[str]


class DomainContextManager:
    """
    Manages domain-specific contexts and principle adaptations for cross-domain testing.
    """
    
    def __init__(self):
        self.domain_cache = {}
        self.adaptation_cache = {}
        self.mapping_cache = {}
    
    async def adapt_principle_to_domain(
        self,
        principle: Principle,
        domain_context: DomainContext,
        strategy: AdaptationStrategy = AdaptationStrategy.CONTEXTUAL
    ) -> PrincipleAdaptation:
        """
        Adapt a constitutional principle to a specific domain context.
        
        Args:
            principle: The principle to adapt
            domain_context: Target domain context
            strategy: Adaptation strategy to use
            
        Returns:
            PrincipleAdaptation with adapted content and metadata
        """
        
        cache_key = f"{principle.id}_{domain_context.id}_{strategy.value}"
        if cache_key in self.adaptation_cache:
            return self.adaptation_cache[cache_key]
        
        logger.info(f"Adapting principle {principle.id} to domain {domain_context.domain_name}")
        
        # Analyze domain-specific requirements
        domain_requirements = await self._analyze_domain_requirements(domain_context)
        
        # Analyze principle characteristics
        principle_characteristics = await self._analyze_principle_characteristics(principle)
        
        # Perform adaptation based on strategy
        if strategy == AdaptationStrategy.CONSERVATIVE:
            adaptation = await self._conservative_adaptation(
                principle, domain_context, domain_requirements, principle_characteristics
            )
        elif strategy == AdaptationStrategy.CONTEXTUAL:
            adaptation = await self._contextual_adaptation(
                principle, domain_context, domain_requirements, principle_characteristics
            )
        else:  # TRANSFORMATIVE
            adaptation = await self._transformative_adaptation(
                principle, domain_context, domain_requirements, principle_characteristics
            )
        
        # Calculate constitutional fidelity score
        fidelity_score = await self._calculate_constitutional_fidelity(
            principle, adaptation.adapted_content
        )
        adaptation.constitutional_fidelity_score = fidelity_score
        
        # Calculate domain fit score
        fit_score = await self._calculate_domain_fit(
            adaptation.adapted_content, domain_context
        )
        adaptation.domain_fit_score = fit_score
        
        # Cache the result
        self.adaptation_cache[cache_key] = adaptation
        
        return adaptation
    
    async def create_cross_domain_mapping(
        self,
        source_principle: Principle,
        target_principle: Principle,
        source_domain: DomainContext,
        target_domain: DomainContext
    ) -> CrossDomainMapping:
        """
        Create a mapping between principles across different domains.
        
        Args:
            source_principle: Source principle
            target_principle: Target principle
            source_domain: Source domain context
            target_domain: Target domain context
            
        Returns:
            CrossDomainMapping with similarity and conflict analysis
        """
        
        cache_key = f"{source_principle.id}_{target_principle.id}_{source_domain.id}_{target_domain.id}"
        if cache_key in self.mapping_cache:
            return self.mapping_cache[cache_key]
        
        logger.info(f"Creating cross-domain mapping between principles {source_principle.id} and {target_principle.id}")
        
        # Calculate semantic similarity
        similarity_score = await self._calculate_semantic_similarity(
            source_principle, target_principle
        )
        
        # Detect potential conflicts
        conflict_indicators = await self._detect_cross_domain_conflicts(
            source_principle, target_principle, source_domain, target_domain
        )
        
        # Determine mapping type
        mapping_type = await self._determine_mapping_type(
            similarity_score, conflict_indicators, source_domain, target_domain
        )
        
        # Generate resolution recommendations
        recommendations = await self._generate_resolution_recommendations(
            source_principle, target_principle, conflict_indicators, mapping_type
        )
        
        mapping = CrossDomainMapping(
            source_principle_id=source_principle.id,
            target_principle_id=target_principle.id,
            source_domain_id=source_domain.id,
            target_domain_id=target_domain.id,
            mapping_type=mapping_type,
            similarity_score=similarity_score,
            conflict_indicators=conflict_indicators,
            resolution_recommendations=recommendations
        )
        
        # Cache the result
        self.mapping_cache[cache_key] = mapping
        
        return mapping
    
    async def detect_principle_conflicts(
        self,
        principles: List[Principle],
        domain_context: DomainContext
    ) -> Dict[str, Any]:
        """
        Detect conflicts between multiple principles within a domain context.
        
        Args:
            principles: List of principles to analyze
            domain_context: Domain context for analysis
            
        Returns:
            Dictionary containing conflict analysis results
        """
        
        conflicts = {
            "direct_conflicts": [],
            "indirect_conflicts": [],
            "regulatory_conflicts": [],
            "cultural_conflicts": [],
            "stakeholder_conflicts": []
        }
        
        # Analyze pairwise conflicts
        for i, p1 in enumerate(principles):
            for j, p2 in enumerate(principles[i+1:], i+1):
                conflict_analysis = await self._analyze_principle_pair_conflicts(
                    p1, p2, domain_context
                )
                
                if conflict_analysis["has_conflict"]:
                    conflict_entry = {
                        "principle_1_id": p1.id,
                        "principle_2_id": p2.id,
                        "conflict_type": conflict_analysis["conflict_type"],
                        "severity": conflict_analysis["severity"],
                        "description": conflict_analysis["description"],
                        "resolution_suggestions": conflict_analysis["resolution_suggestions"]
                    }
                    
                    conflicts[conflict_analysis["conflict_category"]].append(conflict_entry)
        
        # Analyze regulatory conflicts
        regulatory_conflicts = await self._analyze_regulatory_conflicts(principles, domain_context)
        conflicts["regulatory_conflicts"].extend(regulatory_conflicts)
        
        # Analyze cultural conflicts
        cultural_conflicts = await self._analyze_cultural_conflicts(principles, domain_context)
        conflicts["cultural_conflicts"].extend(cultural_conflicts)
        
        return conflicts
    
    async def _analyze_domain_requirements(self, domain_context: DomainContext) -> Dict[str, Any]:
        """Analyze domain-specific requirements and constraints."""
        
        requirements = {
            "regulatory_frameworks": domain_context.regulatory_frameworks or [],
            "compliance_requirements": domain_context.compliance_requirements or {},
            "cultural_factors": domain_context.cultural_contexts or {},
            "risk_factors": domain_context.risk_factors or [],
            "stakeholder_groups": domain_context.stakeholder_groups or [],
            "domain_constraints": domain_context.domain_constraints or {}
        }
        
        # Add domain-specific analysis
        if domain_context.domain_name.lower() == "healthcare":
            requirements["privacy_level"] = "high"
            requirements["safety_criticality"] = "high"
            requirements["regulatory_complexity"] = "high"
        elif domain_context.domain_name.lower() == "finance":
            requirements["regulatory_complexity"] = "very_high"
            requirements["risk_tolerance"] = "low"
            requirements["audit_requirements"] = "strict"
        elif domain_context.domain_name.lower() == "education":
            requirements["accessibility_requirements"] = "high"
            requirements["privacy_level"] = "medium"
            requirements["inclusivity_focus"] = "high"
        
        return requirements
    
    async def _analyze_principle_characteristics(self, principle: Principle) -> Dict[str, Any]:
        """Analyze characteristics of a constitutional principle."""
        
        characteristics = {
            "content_length": len(principle.content),
            "scope": principle.scope or [],
            "priority_weight": principle.priority_weight or 0.5,
            "keywords": principle.keywords or [],
            "category": principle.category or "general",
            "normative_statement": principle.normative_statement,
            "constraints": principle.constraints or {}
        }
        
        # Analyze content for domain-relevant keywords
        content_lower = principle.content.lower()
        
        characteristics["domain_relevance"] = {
            "healthcare": any(keyword in content_lower for keyword in 
                            ["health", "medical", "patient", "privacy", "safety", "hipaa"]),
            "finance": any(keyword in content_lower for keyword in 
                         ["financial", "money", "payment", "risk", "compliance", "audit"]),
            "education": any(keyword in content_lower for keyword in 
                           ["education", "learning", "student", "accessibility", "inclusive"]),
            "governance": any(keyword in content_lower for keyword in 
                            ["governance", "policy", "democratic", "transparency", "accountability"]),
            "technology": any(keyword in content_lower for keyword in 
                            ["technology", "ai", "algorithm", "data", "system", "automation"])
        }
        
        return characteristics
    
    async def _conservative_adaptation(
        self,
        principle: Principle,
        domain_context: DomainContext,
        domain_requirements: Dict[str, Any],
        principle_characteristics: Dict[str, Any]
    ) -> PrincipleAdaptation:
        """Perform conservative adaptation with minimal changes."""
        
        adapted_content = principle.content
        rationale = "Conservative adaptation preserving original principle intent"
        
        # Add minimal domain-specific context
        if domain_context.domain_name.lower() in ["healthcare", "finance"]:
            if "compliance" not in adapted_content.lower():
                adapted_content += f" This principle must be applied in compliance with {domain_context.domain_name} regulations."
                rationale += f" Added {domain_context.domain_name} compliance requirement."
        
        return PrincipleAdaptation(
            original_principle_id=principle.id,
            adapted_content=adapted_content,
            adaptation_strategy=AdaptationStrategy.CONSERVATIVE,
            adaptation_rationale=rationale,
            constitutional_fidelity_score=0.0,  # Will be calculated later
            domain_fit_score=0.0,  # Will be calculated later
            adaptation_metadata={
                "changes_made": ["minimal_compliance_addition"] if adapted_content != principle.content else [],
                "original_length": len(principle.content),
                "adapted_length": len(adapted_content)
            }
        )
    
    async def _contextual_adaptation(
        self,
        principle: Principle,
        domain_context: DomainContext,
        domain_requirements: Dict[str, Any],
        principle_characteristics: Dict[str, Any]
    ) -> PrincipleAdaptation:
        """Perform contextual adaptation with domain-specific modifications."""
        
        adapted_content = principle.content
        changes_made = []
        
        # Domain-specific adaptations
        if domain_context.domain_name.lower() == "healthcare":
            if "data" in adapted_content.lower() and "privacy" not in adapted_content.lower():
                adapted_content = adapted_content.replace("data", "patient data with privacy protections")
                changes_made.append("added_privacy_protections")
            
            if "decision" in adapted_content.lower() and "safety" not in adapted_content.lower():
                adapted_content += " All decisions must prioritize patient safety and clinical best practices."
                changes_made.append("added_safety_requirements")
        
        elif domain_context.domain_name.lower() == "finance":
            if "transaction" in adapted_content.lower() and "audit" not in adapted_content.lower():
                adapted_content += " All transactions must maintain comprehensive audit trails."
                changes_made.append("added_audit_requirements")
            
            if "risk" not in adapted_content.lower():
                adapted_content += " Risk assessment and mitigation procedures must be implemented."
                changes_made.append("added_risk_management")
        
        rationale = f"Contextual adaptation for {domain_context.domain_name} domain with specific requirements"
        
        return PrincipleAdaptation(
            original_principle_id=principle.id,
            adapted_content=adapted_content,
            adaptation_strategy=AdaptationStrategy.CONTEXTUAL,
            adaptation_rationale=rationale,
            constitutional_fidelity_score=0.0,  # Will be calculated later
            domain_fit_score=0.0,  # Will be calculated later
            adaptation_metadata={
                "changes_made": changes_made,
                "domain_requirements_applied": list(domain_requirements.keys()),
                "original_length": len(principle.content),
                "adapted_length": len(adapted_content)
            }
        )
    
    async def _transformative_adaptation(
        self,
        principle: Principle,
        domain_context: DomainContext,
        domain_requirements: Dict[str, Any],
        principle_characteristics: Dict[str, Any]
    ) -> PrincipleAdaptation:
        """Perform transformative adaptation with significant domain-specific changes."""
        
        # This would involve more sophisticated NLP and domain knowledge
        # For now, implement a simplified version
        
        adapted_content = f"In the context of {domain_context.domain_name}: {principle.content}"
        
        # Add comprehensive domain-specific requirements
        if domain_context.regulatory_frameworks:
            adapted_content += f" This principle must comply with: {', '.join(domain_context.regulatory_frameworks)}."
        
        if domain_context.stakeholder_groups:
            adapted_content += f" Implementation must consider the needs of: {', '.join(domain_context.stakeholder_groups)}."
        
        rationale = f"Transformative adaptation significantly modified for {domain_context.domain_name} domain requirements"
        
        return PrincipleAdaptation(
            original_principle_id=principle.id,
            adapted_content=adapted_content,
            adaptation_strategy=AdaptationStrategy.TRANSFORMATIVE,
            adaptation_rationale=rationale,
            constitutional_fidelity_score=0.0,  # Will be calculated later
            domain_fit_score=0.0,  # Will be calculated later
            adaptation_metadata={
                "changes_made": ["domain_contextualization", "regulatory_integration", "stakeholder_consideration"],
                "transformation_level": "high",
                "original_length": len(principle.content),
                "adapted_length": len(adapted_content)
            }
        )
    
    async def _calculate_constitutional_fidelity(
        self,
        original_principle: Principle,
        adapted_content: str
    ) -> float:
        """Calculate how well the adaptation preserves constitutional fidelity."""
        
        # Simplified fidelity calculation based on content similarity
        original_words = set(original_principle.content.lower().split())
        adapted_words = set(adapted_content.lower().split())
        
        # Jaccard similarity
        intersection = len(original_words.intersection(adapted_words))
        union = len(original_words.union(adapted_words))
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # Adjust for length changes (penalize excessive additions)
        length_ratio = len(original_principle.content) / len(adapted_content)
        length_penalty = max(0.0, 1.0 - abs(1.0 - length_ratio))
        
        fidelity_score = (jaccard_similarity * 0.7) + (length_penalty * 0.3)
        
        return min(1.0, max(0.0, fidelity_score))
    
    async def _calculate_domain_fit(
        self,
        adapted_content: str,
        domain_context: DomainContext
    ) -> float:
        """Calculate how well the adaptation fits the domain context."""
        
        fit_score = 0.5  # Base score
        
        # Check for domain-specific keywords
        content_lower = adapted_content.lower()
        domain_name = domain_context.domain_name.lower()
        
        if domain_name in content_lower:
            fit_score += 0.2
        
        # Check for regulatory framework mentions
        if domain_context.regulatory_frameworks:
            for framework in domain_context.regulatory_frameworks:
                if framework.lower() in content_lower:
                    fit_score += 0.1
        
        # Check for stakeholder group mentions
        if domain_context.stakeholder_groups:
            for group in domain_context.stakeholder_groups:
                if group.lower() in content_lower:
                    fit_score += 0.05
        
        return min(1.0, fit_score)
    
    async def _calculate_semantic_similarity(
        self,
        principle1: Principle,
        principle2: Principle
    ) -> float:
        """Calculate semantic similarity between two principles."""
        
        # Simplified similarity calculation
        words1 = set(principle1.content.lower().split())
        words2 = set(principle2.content.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    async def _detect_cross_domain_conflicts(
        self,
        source_principle: Principle,
        target_principle: Principle,
        source_domain: DomainContext,
        target_domain: DomainContext
    ) -> List[str]:
        """Detect potential conflicts between principles across domains."""
        
        conflicts = []
        
        # Check for regulatory conflicts
        source_regs = set(source_domain.regulatory_frameworks or [])
        target_regs = set(target_domain.regulatory_frameworks or [])
        
        if source_regs and target_regs and not source_regs.intersection(target_regs):
            conflicts.append("regulatory_framework_mismatch")
        
        # Check for cultural conflicts
        source_cultural = source_domain.cultural_contexts or {}
        target_cultural = target_domain.cultural_contexts or {}
        
        if source_cultural.get("privacy_expectations") != target_cultural.get("privacy_expectations"):
            conflicts.append("privacy_expectation_mismatch")
        
        return conflicts
    
    async def _determine_mapping_type(
        self,
        similarity_score: float,
        conflict_indicators: List[str],
        source_domain: DomainContext,
        target_domain: DomainContext
    ) -> str:
        """Determine the type of mapping between principles."""
        
        if conflict_indicators:
            return "conflicting"
        elif similarity_score > 0.8:
            return "equivalent"
        elif similarity_score > 0.5:
            return "adapted"
        else:
            return "complementary"
    
    async def _generate_resolution_recommendations(
        self,
        source_principle: Principle,
        target_principle: Principle,
        conflict_indicators: List[str],
        mapping_type: str
    ) -> List[str]:
        """Generate recommendations for resolving conflicts or improving mappings."""
        
        recommendations = []
        
        if "regulatory_framework_mismatch" in conflict_indicators:
            recommendations.append("Harmonize regulatory requirements across domains")
            recommendations.append("Create domain-specific compliance guidelines")
        
        if "privacy_expectation_mismatch" in conflict_indicators:
            recommendations.append("Establish unified privacy standards")
            recommendations.append("Implement context-aware privacy controls")
        
        if mapping_type == "conflicting":
            recommendations.append("Consider principle hierarchy and precedence rules")
            recommendations.append("Implement conflict resolution mechanisms")
        
        return recommendations
    
    async def _analyze_principle_pair_conflicts(
        self,
        principle1: Principle,
        principle2: Principle,
        domain_context: DomainContext
    ) -> Dict[str, Any]:
        """Analyze conflicts between a pair of principles."""
        
        # Simplified conflict analysis
        content1 = principle1.content.lower()
        content2 = principle2.content.lower()
        
        # Check for direct contradictions
        if ("allow" in content1 and "prohibit" in content2) or ("prohibit" in content1 and "allow" in content2):
            return {
                "has_conflict": True,
                "conflict_type": "direct_contradiction",
                "conflict_category": "direct_conflicts",
                "severity": "high",
                "description": "Principles contain contradictory directives",
                "resolution_suggestions": ["Establish principle hierarchy", "Define context-specific application"]
            }
        
        return {
            "has_conflict": False,
            "conflict_type": None,
            "conflict_category": None,
            "severity": "none",
            "description": "No conflicts detected",
            "resolution_suggestions": []
        }
    
    async def _analyze_regulatory_conflicts(
        self,
        principles: List[Principle],
        domain_context: DomainContext
    ) -> List[Dict[str, Any]]:
        """Analyze regulatory conflicts for principles in domain context."""
        return []  # Simplified implementation
    
    async def _analyze_cultural_conflicts(
        self,
        principles: List[Principle],
        domain_context: DomainContext
    ) -> List[Dict[str, Any]]:
        """Analyze cultural conflicts for principles in domain context."""
        return []  # Simplified implementation


# Global instance
domain_context_manager = DomainContextManager()
