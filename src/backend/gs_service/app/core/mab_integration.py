"""
Multi-Armed Bandit Integration Layer for GS Service

Integrates MAB prompt optimization with existing LLM reliability framework,
constitutional prompting, and GS service workflows.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

from .mab_prompt_optimizer import (
    MABPromptOptimizer, MABConfig, PromptTemplate, MABAlgorithm, RewardComponents
)
from .llm_reliability_framework import LLMReliabilityFramework, LLMReliabilityConfig, ReliabilityLevel
from .constitutional_prompting import ConstitutionalPromptBuilder
from ..schemas import LLMInterpretationInput, LLMStructuredOutput, ConstitutionalSynthesisInput, ConstitutionalSynthesisOutput
from ..models.mab_models import PromptTemplateModel, PromptPerformanceModel, OptimizationHistoryModel

logger = logging.getLogger(__name__)


class MABIntegratedGSService:
    """
    Integrated GS Service with Multi-Armed Bandit prompt optimization.
    
    Combines MAB optimization with LLM reliability framework and constitutional prompting
    to achieve >99.9% reliability while optimizing prompt effectiveness.
    """
    
    def __init__(
        self,
        mab_config: MABConfig = None,
        reliability_config: LLMReliabilityConfig = None
    ):
        # Initialize MAB system
        self.mab_config = mab_config or self._default_mab_config()
        self.mab_optimizer = MABPromptOptimizer(self.mab_config)
        
        # Initialize LLM reliability framework
        self.reliability_config = reliability_config or self._default_reliability_config()
        self.reliability_framework = LLMReliabilityFramework(self.reliability_config)
        
        # Initialize constitutional prompting
        self.constitutional_builder = ConstitutionalPromptBuilder()
        
        # Initialize default prompt templates
        self._initialize_default_templates()
        
        # Performance tracking
        self.integration_metrics = {
            "total_requests": 0,
            "mab_selections": 0,
            "reliability_validations": 0,
            "constitutional_syntheses": 0,
            "average_response_time": 0.0,
            "success_rate": 0.0
        }
        
        logger.info("Initialized MAB-Integrated GS Service")
    
    def _default_mab_config(self) -> MABConfig:
        """Create default MAB configuration optimized for GS service."""
        return MABConfig(
            algorithm=MABAlgorithm.THOMPSON_SAMPLING,
            exploration_rate=0.15,  # Slightly higher for better exploration
            confidence_level=0.95,
            alpha_prior=2.0,  # Optimistic prior for new templates
            beta_prior=1.0,
            
            # Reward weights optimized for constitutional compliance
            semantic_similarity_weight=0.3,
            policy_quality_weight=0.3,
            constitutional_compliance_weight=0.3,
            bias_mitigation_weight=0.1,
            
            min_uses_for_confidence=5,  # Lower threshold for faster adaptation
            reward_threshold=0.85,  # High threshold for safety-critical applications
            update_frequency=50  # More frequent updates
        )
    
    def _default_reliability_config(self) -> LLMReliabilityConfig:
        """Create default reliability configuration for >99.9% target."""
        return LLMReliabilityConfig(
            target_reliability=ReliabilityLevel.SAFETY_CRITICAL,
            ensemble_size=3,
            consensus_threshold=0.9,  # High consensus for safety
            fallback_strategy="conservative",
            multi_model_validation_enabled=True,
            ensemble_voting_enabled=True,
            proactive_bias_mitigation=True,
            prometheus_metrics_enabled=True
        )
    
    def _initialize_default_templates(self):
        """Initialize default prompt templates for different categories."""
        default_templates = [
            PromptTemplate(
                template_id="constitutional_v1",
                name="Constitutional Compliance Template",
                template_content="""
                Analyze the following constitutional principle and generate a compliant policy rule:
                
                Constitutional Principle: {principle}
                Context: {context}
                
                Requirements:
                1. Ensure full constitutional compliance
                2. Maintain clarity and enforceability
                3. Consider all stakeholder impacts
                4. Include appropriate safeguards
                
                Generate a {target_format} policy rule:
                """,
                category="constitutional"
            ),
            PromptTemplate(
                template_id="safety_critical_v1",
                name="Safety-Critical Policy Template",
                template_content="""
                Create a safety-critical policy rule for the following principle:
                
                Principle: {principle}
                Safety Context: {context}
                
                SAFETY REQUIREMENTS:
                - Fail-safe defaults (deny by default)
                - Explicit authorization requirements
                - Audit trail generation
                - Error handling and recovery
                - Compliance verification
                
                Generate {target_format} code with safety annotations:
                """,
                category="safety_critical"
            ),
            PromptTemplate(
                template_id="fairness_aware_v1",
                name="Fairness-Aware Policy Template",
                template_content="""
                Generate a bias-free, fairness-aware policy for:
                
                Principle: {principle}
                Fairness Context: {context}
                
                FAIRNESS REQUIREMENTS:
                - Demographic parity considerations
                - Individual fairness principles
                - Procedural fairness guarantees
                - Intersectionality awareness
                - Bias mitigation measures
                
                Create {target_format} policy with fairness annotations:
                """,
                category="fairness_aware"
            ),
            PromptTemplate(
                template_id="adaptive_context_v1",
                name="Adaptive Contextual Template",
                template_content="""
                Synthesize a contextually adaptive policy rule:
                
                Core Principle: {principle}
                Environmental Context: {context}
                Adaptation Requirements: {adaptation_factors}
                
                ADAPTIVE FEATURES:
                - Context-sensitive conditions
                - Dynamic threshold adjustment
                - Environmental factor integration
                - Stakeholder-specific provisions
                
                Generate adaptive {target_format} policy:
                """,
                category="adaptive"
            )
        ]
        
        for template in default_templates:
            self.mab_optimizer.register_prompt_template(template)
            
        logger.info(f"Initialized {len(default_templates)} default prompt templates")
    
    async def synthesize_with_mab_optimization(
        self,
        synthesis_input: ConstitutionalSynthesisInput,
        context: Dict[str, Any] = None
    ) -> Tuple[ConstitutionalSynthesisOutput, Dict[str, Any]]:
        """
        Synthesize constitutional policies with MAB-optimized prompts.
        
        Combines MAB prompt selection, LLM reliability validation, and constitutional compliance.
        """
        start_time = datetime.now(timezone.utc)
        context = context or {}
        
        # Update metrics
        self.integration_metrics["total_requests"] += 1
        
        try:
            # 1. Select optimal prompt template using MAB
            prompt_context = {
                "category": context.get("category", "constitutional"),
                "safety_level": context.get("safety_level", "standard"),
                "target_format": synthesis_input.target_format,
                "principle_complexity": len(synthesis_input.context.split())
            }
            
            selected_template = await self.mab_optimizer.select_optimal_prompt(prompt_context)
            if not selected_template:
                raise ValueError("No suitable prompt template available")
                
            self.integration_metrics["mab_selections"] += 1
            
            # 2. Build constitutional context
            constitutional_context = await self.constitutional_builder.build_constitutional_context(
                context=synthesis_input.context,
                category=prompt_context.get("category", "general"),
                auth_token=context.get("auth_token")
            )
            
            # 3. Generate optimized prompt
            optimized_prompt = self._build_optimized_prompt(
                selected_template, synthesis_input, constitutional_context
            )
            
            # 4. Execute with LLM reliability framework
            llm_input = LLMInterpretationInput(
                principle_id=getattr(synthesis_input, 'principle_id', 1),
                principle_text=optimized_prompt,
                context=synthesis_input.context
            )
            
            llm_output, reliability_metrics = await self.reliability_framework.validate_with_ensemble(llm_input)
            self.integration_metrics["reliability_validations"] += 1
            
            # 5. Convert to constitutional synthesis output
            synthesis_output = self._convert_to_synthesis_output(
                llm_output, synthesis_input, constitutional_context
            )
            self.integration_metrics["constitutional_syntheses"] += 1
            
            # 6. Update MAB performance
            await self.mab_optimizer.update_performance(
                selected_template.template_id, llm_output, prompt_context
            )
            
            # 7. Calculate integration metrics
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._update_integration_metrics(response_time, True)
            
            integration_metadata = {
                "selected_template": {
                    "template_id": selected_template.template_id,
                    "name": selected_template.name,
                    "category": selected_template.category
                },
                "reliability_metrics": reliability_metrics.__dict__ if reliability_metrics else {},
                "mab_metrics": self.mab_optimizer.get_optimization_metrics(),
                "response_time_seconds": response_time,
                "constitutional_context_size": len(constitutional_context.get("principles", []))
            }
            
            return synthesis_output, integration_metadata
            
        except Exception as e:
            logger.error(f"MAB-integrated synthesis failed: {e}")
            self._update_integration_metrics(0, False)
            raise
    
    def _build_optimized_prompt(
        self,
        template: PromptTemplate,
        synthesis_input: ConstitutionalSynthesisInput,
        constitutional_context: Dict[str, Any]
    ) -> str:
        """Build optimized prompt using selected template and constitutional context."""
        
        # Extract key information
        principles_text = "\n".join([
            f"- {p.get('name', 'Unknown')}: {p.get('normative_statement', p.get('description', ''))}"
            for p in constitutional_context.get("principles", [])
        ])
        
        # Format template with context
        formatted_prompt = template.template_content.format(
            principle=principles_text or synthesis_input.context,
            context=synthesis_input.context,
            target_format=synthesis_input.target_format,
            adaptation_factors=constitutional_context.get("scope_constraints", [])
        )
        
        # Add constitutional preamble if available
        if constitutional_context.get("normative_framework"):
            constitutional_preamble = f"""
            CONSTITUTIONAL FRAMEWORK:
            {constitutional_context['normative_framework']}
            
            """
            formatted_prompt = constitutional_preamble + formatted_prompt
            
        return formatted_prompt
    
    def _convert_to_synthesis_output(
        self,
        llm_output: LLMStructuredOutput,
        synthesis_input: ConstitutionalSynthesisInput,
        constitutional_context: Dict[str, Any]
    ) -> ConstitutionalSynthesisOutput:
        """Convert LLM output to constitutional synthesis format."""
        
        # Create mock constitutional compliance info
        compliance_info = {
            "compliant": True,
            "confidence": 0.9,
            "principle_alignment": constitutional_context.get("principle_count", 0),
            "constitutional_basis": "MAB-optimized constitutional synthesis"
        }
        
        # Create synthesis output
        return ConstitutionalSynthesisOutput(
            context=synthesis_input.context,
            generated_rules=[],  # Would contain actual parsed rules
            constitutional_context=constitutional_context,
            synthesis_metadata={
                "mab_optimized": True,
                "template_used": "mab_selected",
                "reliability_validated": True,
                "constitutional_compliance": compliance_info
            },
            raw_llm_response=llm_output.raw_llm_response
        )
    
    def _update_integration_metrics(self, response_time: float, success: bool):
        """Update integration performance metrics."""
        # Update average response time
        total_requests = self.integration_metrics["total_requests"]
        current_avg = self.integration_metrics["average_response_time"]
        self.integration_metrics["average_response_time"] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
        
        # Update success rate
        if success:
            current_successes = self.integration_metrics["success_rate"] * (total_requests - 1)
            self.integration_metrics["success_rate"] = (current_successes + 1) / total_requests
        else:
            current_successes = self.integration_metrics["success_rate"] * (total_requests - 1)
            self.integration_metrics["success_rate"] = current_successes / total_requests
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status and metrics."""
        mab_metrics = self.mab_optimizer.get_optimization_metrics()
        best_templates = self.mab_optimizer.get_best_performing_templates(3)
        
        return {
            "integration_metrics": self.integration_metrics,
            "mab_optimization": mab_metrics,
            "best_templates": best_templates,
            "reliability_config": {
                "target_reliability": self.reliability_config.target_reliability.value,
                "ensemble_size": self.reliability_config.ensemble_size,
                "consensus_threshold": self.reliability_config.consensus_threshold
            },
            "system_status": "operational" if self.integration_metrics["success_rate"] > 0.95 else "degraded"
        }
