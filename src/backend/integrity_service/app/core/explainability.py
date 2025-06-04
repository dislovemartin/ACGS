"""
Explainability and Rule Provenance Module for ACGS-PGP Phase 3
Provides decision explanations and rule traceability
"""

import time
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from ..schemas import ExplainabilityRequest, ExplainabilityResponse, RuleProvenanceResponse
from .. import crud, models
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """
    Provides explanations for policy decisions and rule provenance tracking.
    Supports multiple explanation levels and audiences.
    """
    
    def __init__(self):
        self.explanation_cache = {}
        self.provenance_cache = {}
        
    async def generate_explanation(
        self,
        request: ExplainabilityRequest,
        db: AsyncSession
    ) -> ExplainabilityResponse:
        """
        Generate explanation for a policy decision.
        """
        start_time = time.time()
        
        logger.info(f"Generating explanation for decision {request.decision_id}")
        
        # Check cache first
        cache_key = f"{request.decision_id}_{request.explanation_level}_{request.target_audience}"
        if cache_key in self.explanation_cache:
            return self.explanation_cache[cache_key]
        
        # Generate explanation based on level and audience
        explanation = await self._generate_explanation_content(request, db)
        rule_provenance = await self._get_rule_provenance(request.decision_id, db)
        
        # Generate counterfactual examples if requested
        counterfactual_examples = None
        if request.include_counterfactuals:
            counterfactual_examples = await self._generate_counterfactuals(request.decision_id, db)
        
        # Calculate confidence score
        confidence_score = await self._calculate_confidence_score(request.decision_id, db)
        
        response = ExplainabilityResponse(
            decision_id=request.decision_id,
            explanation=explanation,
            rule_provenance=rule_provenance,
            counterfactual_examples=counterfactual_examples,
            confidence_score=confidence_score,
            generated_at=datetime.utcnow()
        )
        
        # Cache the response
        self.explanation_cache[cache_key] = response
        
        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"Explanation generated in {total_time}ms")
        
        return response
    
    async def _generate_explanation_content(
        self,
        request: ExplainabilityRequest,
        db: AsyncSession
    ) -> str:
        """
        Generate explanation content based on level and audience.
        """
        # Mock explanation generation (in real implementation, use actual decision data)
        decision_id = request.decision_id
        level = request.explanation_level
        audience = request.target_audience
        
        if level == "basic":
            if audience == "general":
                explanation = f"Decision {decision_id} was made based on established policy rules. " \
                            f"The system evaluated your request against our governance framework and " \
                            f"determined the appropriate outcome."
            elif audience == "affected_individual":
                explanation = f"Your request (ID: {decision_id}) was processed according to our policy framework. " \
                            f"The decision was based on rules designed to ensure fair and consistent treatment."
            else:  # technical
                explanation = f"Decision {decision_id} processed through policy evaluation pipeline. " \
                            f"Rule matching and conflict resolution applied."
        
        elif level == "standard":
            if audience == "general":
                explanation = f"Decision {decision_id} was made by evaluating your request against multiple policy rules. " \
                            f"The system checked for applicable rules, resolved any conflicts, and applied the " \
                            f"most specific and recent policies. The decision process included bias detection " \
                            f"and fairness validation to ensure equitable treatment."
            elif audience == "affected_individual":
                explanation = f"Your request (ID: {decision_id}) was evaluated using our automated policy system. " \
                            f"The system considered relevant rules, checked for potential bias, and ensured " \
                            f"the decision meets fairness criteria. You have the right to appeal this decision " \
                            f"if you believe it was made in error."
            else:  # technical
                explanation = f"Decision {decision_id} processed through tiered validation pipeline. " \
                            f"Rule evaluation included conflict resolution, bias detection (statistical, " \
                            f"counterfactual, embedding analysis), and fairness validation. " \
                            f"Z3 SMT solver verified logical consistency."
        
        else:  # detailed
            if audience == "general":
                explanation = f"Decision {decision_id} underwent comprehensive evaluation: " \
                            f"1) Rule matching identified applicable policies from our governance framework. " \
                            f"2) Conflict resolution ensured consistent application of overlapping rules. " \
                            f"3) Bias detection algorithms (statistical, counterfactual, semantic) verified " \
                            f"fair treatment across protected attributes. " \
                            f"4) Formal verification confirmed logical consistency. " \
                            f"5) Human oversight validated the automated decision process."
            elif audience == "affected_individual":
                explanation = f"Your request (ID: {decision_id}) received thorough evaluation: " \
                            f"• Policy Matching: Relevant rules were identified from our governance database. " \
                            f"• Fairness Check: Multiple algorithms verified equitable treatment. " \
                            f"• Bias Detection: Statistical and semantic analysis ensured no discriminatory patterns. " \
                            f"• Verification: Formal methods confirmed decision consistency. " \
                            f"• Appeal Rights: You may challenge this decision through our dispute resolution process."
            else:  # technical
                explanation = f"Decision {decision_id} - Technical Details: " \
                            f"Rule Evaluation: {self._get_mock_rule_count()} rules processed, " \
                            f"Conflict Resolution: Meta-rule hierarchy applied, " \
                            f"Bias Detection: 4 algorithms (demographic parity, counterfactual, embedding, LLM), " \
                            f"Fairness Validation: Individual fairness, equalized odds verified, " \
                            f"Z3 Verification: SAT solving confirmed logical consistency, " \
                            f"Confidence: {await self._calculate_confidence_score(decision_id, db):.3f}"
        
        return explanation
    
    async def _get_rule_provenance(
        self,
        decision_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Get provenance information for rules used in decision.
        """
        # Mock rule provenance (in real implementation, track actual rule usage)
        provenance = [
            {
                "rule_id": "rule_001",
                "rule_content": "allow(X) :- user(X), verified(X), not_suspended(X)",
                "source_principle_id": 1,
                "principle_name": "User Access Control",
                "version": 2,
                "created_at": "2024-01-15T10:30:00Z",
                "verified_at": "2024-01-15T11:00:00Z",
                "confidence": 0.95
            },
            {
                "rule_id": "rule_002", 
                "rule_content": "deny(X) :- user(X), suspended(X)",
                "source_principle_id": 2,
                "principle_name": "Account Suspension Policy",
                "version": 1,
                "created_at": "2024-01-10T14:20:00Z",
                "verified_at": "2024-01-10T14:45:00Z",
                "confidence": 0.98
            }
        ]
        
        return provenance
    
    async def _generate_counterfactuals(
        self,
        decision_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Generate counterfactual examples for decision explanation.
        """
        # Mock counterfactual generation
        counterfactuals = [
            {
                "scenario": "If user verification status was different",
                "original_value": "verified=true",
                "counterfactual_value": "verified=false",
                "predicted_outcome": "deny",
                "explanation": "Without verification, access would be denied per security policy"
            },
            {
                "scenario": "If user had different role",
                "original_value": "role=standard_user",
                "counterfactual_value": "role=admin",
                "predicted_outcome": "allow_with_elevated_permissions",
                "explanation": "Admin role would grant additional access privileges"
            }
        ]
        
        return counterfactuals
    
    async def _calculate_confidence_score(
        self,
        decision_id: str,
        db: AsyncSession
    ) -> float:
        """
        Calculate confidence score for the decision.
        """
        # Mock confidence calculation (in real implementation, use actual metrics)
        # Factors: rule coverage, conflict resolution clarity, bias detection results, etc.
        
        base_confidence = 0.85
        
        # Adjust based on mock factors
        rule_coverage_factor = 0.1  # High rule coverage
        bias_detection_factor = 0.05  # Low bias detected
        verification_factor = 0.0   # All rules verified
        
        confidence = base_confidence + rule_coverage_factor + bias_detection_factor + verification_factor
        return min(confidence, 1.0)
    
    def _get_mock_rule_count(self) -> int:
        """Get mock rule count for technical explanations."""
        return 15  # Mock number of rules evaluated
    
    async def get_rule_provenance(
        self,
        rule_id: str,
        db: AsyncSession
    ) -> RuleProvenanceResponse:
        """
        Get detailed provenance information for a specific rule.
        """
        # Check cache first
        if rule_id in self.provenance_cache:
            return self.provenance_cache[rule_id]
        
        # Mock rule provenance response (in real implementation, query actual data)
        response = RuleProvenanceResponse(
            rule_id=rule_id,
            source_principles=[
                {
                    "principle_id": 1,
                    "name": "User Access Control",
                    "content": "Users must be verified before accessing system resources",
                    "created_at": "2024-01-01T00:00:00Z",
                    "version": 2
                }
            ],
            creation_context={
                "created_by": "policy_generator_v2.1",
                "creation_method": "constitutional_prompting",
                "source_documents": ["security_policy_v3.pdf", "access_control_guidelines.md"],
                "review_process": "automated_validation + human_review"
            },
            modification_history=[
                {
                    "version": 1,
                    "modified_at": "2024-01-01T00:00:00Z",
                    "modified_by": "system",
                    "changes": "Initial creation",
                    "reason": "Policy framework initialization"
                },
                {
                    "version": 2,
                    "modified_at": "2024-01-15T10:30:00Z",
                    "modified_by": "admin_user",
                    "changes": "Added verification requirement",
                    "reason": "Security enhancement"
                }
            ],
            verification_history=[
                {
                    "verified_at": "2024-01-01T01:00:00Z",
                    "verification_method": "z3_smt_solver",
                    "status": "verified",
                    "confidence": 0.98
                },
                {
                    "verified_at": "2024-01-15T11:00:00Z",
                    "verification_method": "tiered_validation",
                    "status": "verified",
                    "confidence": 0.95
                }
            ],
            usage_statistics={
                "total_applications": 1247,
                "successful_applications": 1198,
                "failed_applications": 49,
                "average_confidence": 0.94,
                "last_used": "2024-01-20T15:30:00Z"
            }
        )
        
        # Cache the response
        self.provenance_cache[rule_id] = response
        
        return response


# Global instance
explainability_engine = ExplainabilityEngine()
