# backend/gs_service/app/services/alphaevolve_bridge.py

"""
AlphaEvolve Service Bridge

This module provides integration between the AlphaEvolve governance engine
and the main ACGS-PGP services, enabling constitutional governance for
evolutionary computation systems.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import sys
import os

# Add alphaevolve_gs_engine to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../alphaevolve_gs_engine/src'))

try:
    from alphaevolve_gs_engine import (
        ConstitutionalPrinciple,
        OperationalRule,
        PolicySynthesizer,
        LLMPolicyGenerator,
        PolicySynthesisInput,
        get_llm_service
    )
    from alphaevolve_gs_engine.services.validation.syntactic_validator import SyntacticValidator
    from alphaevolve_gs_engine.services.validation.semantic_validator import ScenarioBasedSemanticValidator
    ALPHAEVOLVE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"AlphaEvolve engine not available: {e}")
    ALPHAEVOLVE_AVAILABLE = False

from .. import schemas as gs_schemas
from .ac_client import ac_service_client
from .integrity_client import integrity_service_client

logger = logging.getLogger(__name__)


class AlphaEvolveBridge:
    """
    Bridge service for integrating AlphaEvolve governance engine with ACGS-PGP services.
    
    This class provides:
    - Constitutional principle synchronization
    - Policy synthesis for EC systems
    - Real-time governance evaluation
    - Constitutional prompting for EC operations
    """
    
    def __init__(self):
        self.llm_service = None
        self.policy_synthesizer = None
        self.syntactic_validator = None
        self.semantic_validator = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the AlphaEvolve bridge with required services."""
        if not ALPHAEVOLVE_AVAILABLE:
            logger.error("AlphaEvolve engine not available - bridge cannot be initialized")
            return False
            
        try:
            # Initialize LLM service for AlphaEvolve
            self.llm_service = get_llm_service("mock")  # Use mock for now, can be configured
            
            # Initialize policy synthesizer
            self.policy_synthesizer = LLMPolicyGenerator(llm_service=self.llm_service)
            
            # Initialize validators
            self.syntactic_validator = SyntacticValidator()
            self.semantic_validator = ScenarioBasedSemanticValidator()
            
            self._initialized = True
            logger.info("AlphaEvolve bridge initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AlphaEvolve bridge: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if AlphaEvolve integration is available."""
        return ALPHAEVOLVE_AVAILABLE and self._initialized
    
    async def sync_constitutional_principles(self) -> List[ConstitutionalPrinciple]:
        """
        Synchronize constitutional principles from AC service to AlphaEvolve format.
        
        Returns:
            List of ConstitutionalPrinciple objects in AlphaEvolve format
        """
        if not self.is_available():
            logger.warning("AlphaEvolve bridge not available for principle synchronization")
            return []
        
        try:
            # Fetch principles from AC service
            ac_principles = await ac_service_client.get_all_principles()
            
            # Convert to AlphaEvolve format
            alphaevolve_principles = []
            for ac_principle in ac_principles:
                principle = ConstitutionalPrinciple(
                    principle_id=f"AC_{ac_principle['id']}",
                    name=ac_principle.get('name', 'Unknown Principle'),
                    description=ac_principle.get('description', ''),
                    category=ac_principle.get('category', 'General'),
                    policy_code=self._convert_to_rego_policy(ac_principle),
                    metadata={
                        "source": "acgs_ac_service",
                        "original_id": ac_principle['id'],
                        "priority_weight": ac_principle.get('priority_weight', 0.5),
                        "scope": ac_principle.get('scope', []),
                        "sync_timestamp": datetime.utcnow().isoformat()
                    }
                )
                alphaevolve_principles.append(principle)
            
            logger.info(f"Synchronized {len(alphaevolve_principles)} constitutional principles")
            return alphaevolve_principles
            
        except Exception as e:
            logger.error(f"Failed to sync constitutional principles: {e}")
            return []
    
    async def synthesize_ec_governance_rules(
        self,
        ec_context: str,
        optimization_objective: str,
        constitutional_constraints: List[str],
        target_format: str = "rego"
    ) -> Dict[str, Any]:
        """
        Synthesize governance rules specifically for evolutionary computation systems.
        
        Args:
            ec_context: The EC system context
            optimization_objective: The optimization objective
            constitutional_constraints: List of constitutional constraints
            target_format: Target format for rules (rego, datalog)
            
        Returns:
            Dictionary containing synthesized rules and metadata
        """
        if not self.is_available():
            logger.warning("AlphaEvolve bridge not available for rule synthesis")
            return {"rules": [], "metadata": {"error": "Bridge not available"}}
        
        try:
            # Create synthesis input for AlphaEvolve
            synthesis_input = PolicySynthesisInput(
                synthesis_goal=f"Generate governance rules for evolutionary computation in context: {ec_context}",
                policy_type="operational_rule",
                desired_format=target_format,
                constraints=constitutional_constraints,
                context_data={
                    "ec_context": ec_context,
                    "optimization_objective": optimization_objective,
                    "target_system": "evolutionary_computation",
                    "governance_type": "constitutional"
                }
            )
            
            # Synthesize policy using AlphaEvolve
            policy_suggestion = self.policy_synthesizer.synthesize_policy(synthesis_input)
            
            if not policy_suggestion:
                logger.warning("Policy synthesis returned no suggestions")
                return {"rules": [], "metadata": {"error": "No policy suggestions generated"}}
            
            # Validate synthesized policy
            validation_results = await self._validate_synthesized_policy(policy_suggestion)
            
            # Convert to operational rule
            operational_rule = OperationalRule(
                rule_id=f"EC_{uuid.uuid4().hex[:8]}",
                name=f"EC Governance Rule for {ec_context}",
                description=f"Governance rule for evolutionary computation in {ec_context}",
                policy_code=policy_suggestion.policy_code,
                derived_from_principles=[],  # Will be populated from AC principles
                metadata={
                    "synthesis_timestamp": datetime.utcnow().isoformat(),
                    "ec_context": ec_context,
                    "optimization_objective": optimization_objective,
                    "target_format": target_format,
                    "validation_results": validation_results,
                    "confidence": policy_suggestion.confidence if hasattr(policy_suggestion, 'confidence') else 0.8
                }
            )
            
            return {
                "rules": [operational_rule.to_dict()],
                "metadata": {
                    "synthesis_successful": True,
                    "rule_count": 1,
                    "validation_passed": validation_results.get("syntactic_valid", False),
                    "ec_context": ec_context,
                    "target_format": target_format
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to synthesize EC governance rules: {e}")
            return {"rules": [], "metadata": {"error": str(e)}}
    
    async def evaluate_ec_proposal(
        self,
        proposal: gs_schemas.ECProposal,
        constitutional_principles: List[Dict[str, Any]]
    ) -> gs_schemas.ECGovernanceDecision:
        """
        Evaluate an EC proposal for constitutional compliance using AlphaEvolve.
        
        Args:
            proposal: The EC proposal to evaluate
            constitutional_principles: List of applicable constitutional principles
            
        Returns:
            Governance decision for the proposal
        """
        if not self.is_available():
            logger.warning("AlphaEvolve bridge not available for proposal evaluation")
            return self._create_fallback_decision(proposal, "Bridge not available")
        
        try:
            # Convert principles to AlphaEvolve format
            alphaevolve_principles = []
            for principle in constitutional_principles:
                alphaevolve_principle = ConstitutionalPrinciple(
                    principle_id=f"EVAL_{principle['id']}",
                    name=principle.get('name', 'Unknown'),
                    description=principle.get('description', ''),
                    category=principle.get('category', 'General'),
                    policy_code=self._convert_to_rego_policy(principle)
                )
                alphaevolve_principles.append(alphaevolve_principle)
            
            # Evaluate proposal against principles
            evaluation_result = await self._evaluate_against_principles(
                proposal,
                alphaevolve_principles
            )
            
            # Create governance decision
            decision = gs_schemas.ECGovernanceDecision(
                proposal_id=proposal.proposal_id,
                decision=evaluation_result["decision"],
                confidence=evaluation_result["confidence"],
                violated_principles=evaluation_result["violated_principles"],
                governance_penalty=evaluation_result["governance_penalty"],
                explanation=evaluation_result["explanation"],
                enforcement_actions=evaluation_result["enforcement_actions"],
                timestamp=datetime.utcnow()
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Failed to evaluate EC proposal: {e}")
            return self._create_fallback_decision(proposal, f"Evaluation error: {str(e)}")
    
    def _convert_to_rego_policy(self, ac_principle: Dict[str, Any]) -> str:
        """Convert AC principle to Rego policy format."""
        principle_name = ac_principle.get('name', 'unknown').lower().replace(' ', '_')
        
        rego_policy = f"""
package constitutional.{principle_name}

# Constitutional Principle: {ac_principle.get('name', 'Unknown')}
# Description: {ac_principle.get('description', 'No description')}

default allow = false

# Allow if principle requirements are met
allow {{
    # Basic compliance check
    input.proposal.constitutional_compliance == true
    
    # Category-specific checks
    {self._generate_category_checks(ac_principle)}
}}

# Violation detection
violation[msg] {{
    not allow
    msg := "Violation of constitutional principle: {ac_principle.get('name', 'Unknown')}"
}}
"""
        return rego_policy.strip()
    
    def _generate_category_checks(self, principle: Dict[str, Any]) -> str:
        """Generate category-specific Rego checks."""
        category = principle.get('category', '').lower()
        
        if 'safety' in category:
            return 'input.proposal.safety_score >= 0.8'
        elif 'privacy' in category:
            return 'input.proposal.privacy_compliant == true'
        elif 'fairness' in category:
            return 'input.proposal.fairness_score >= 0.7'
        else:
            return 'input.proposal.general_compliance == true'
    
    async def _validate_synthesized_policy(self, policy_suggestion) -> Dict[str, Any]:
        """Validate synthesized policy using AlphaEvolve validators."""
        validation_results = {
            "syntactic_valid": False,
            "semantic_valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Syntactic validation
            if self.syntactic_validator:
                syntactic_result = self.syntactic_validator.validate(policy_suggestion.policy_code)
                validation_results["syntactic_valid"] = syntactic_result.is_valid
                if not syntactic_result.is_valid:
                    validation_results["errors"].extend(syntactic_result.errors)
            
            # Semantic validation (simplified)
            validation_results["semantic_valid"] = True  # Placeholder
            
        except Exception as e:
            validation_results["errors"].append(f"Validation error: {str(e)}")
        
        return validation_results
    
    async def _evaluate_against_principles(
        self,
        proposal: gs_schemas.ECProposal,
        principles: List[ConstitutionalPrinciple]
    ) -> Dict[str, Any]:
        """Evaluate proposal against constitutional principles."""
        
        # Simplified evaluation logic
        decision = "allow"
        confidence = 0.8
        violated_principles = []
        governance_penalty = 0.0
        explanation = f"Evaluated proposal {proposal.proposal_id}"
        enforcement_actions = []
        
        # Check code for potential violations
        code = proposal.solution_code.lower()
        
        for principle in principles:
            principle_violated = False
            
            # Simple keyword-based checks (in production, use more sophisticated analysis)
            if 'safety' in principle.category.lower():
                if any(keyword in code for keyword in ['unsafe', 'dangerous', 'harmful']):
                    principle_violated = True
            elif 'privacy' in principle.category.lower():
                if any(keyword in code for keyword in ['leak', 'expose', 'unauthorized']):
                    principle_violated = True
            
            if principle_violated:
                violated_principles.append(principle.principle_id)
                governance_penalty += 0.2
                decision = "deny" if governance_penalty > 0.3 else "modify"
                explanation += f". Violated principle: {principle.name}"
        
        # Adjust confidence based on violations
        if violated_principles:
            confidence = max(0.1, confidence - len(violated_principles) * 0.15)
        
        # Generate enforcement actions
        if governance_penalty > 0.1:
            enforcement_actions.append("Apply governance penalty")
        if violated_principles:
            enforcement_actions.append("Flag for review")
        
        return {
            "decision": decision,
            "confidence": confidence,
            "violated_principles": violated_principles,
            "governance_penalty": governance_penalty,
            "explanation": explanation,
            "enforcement_actions": enforcement_actions
        }
    
    def _create_fallback_decision(
        self,
        proposal: gs_schemas.ECProposal,
        reason: str
    ) -> gs_schemas.ECGovernanceDecision:
        """Create a fallback governance decision when evaluation fails."""
        return gs_schemas.ECGovernanceDecision(
            proposal_id=proposal.proposal_id,
            decision="deny",
            confidence=0.1,
            violated_principles=[],
            governance_penalty=1.0,
            explanation=f"Fallback decision due to: {reason}",
            enforcement_actions=["Manual review required"],
            timestamp=datetime.utcnow()
        )


# Global bridge instance
alphaevolve_bridge = AlphaEvolveBridge()


async def get_alphaevolve_bridge() -> AlphaEvolveBridge:
    """Get the global AlphaEvolve bridge instance."""
    if not alphaevolve_bridge._initialized:
        await alphaevolve_bridge.initialize()
    return alphaevolve_bridge
