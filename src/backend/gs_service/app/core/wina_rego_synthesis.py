"""
WINA-Optimized Rego Policy Synthesis Module

This module integrates WINA (Weight Informed Neuron Activation) optimization
into the Rego policy synthesis pipeline for the AlphaEvolve-ACGS framework.

Key Features:
- WINA-optimized LLM inference for Rego policy generation
- Constitutional compliance verification for WINA-optimized policies
- Performance metrics tracking (GFLOPs reduction, synthesis accuracy)
- Integration with AlphaEvolve PolicySynthesizer and PGC service
- Seamless compatibility with existing Rego policy synthesis mechanisms

Target Performance:
- 40-70% GFLOPs reduction
- >95% synthesis accuracy maintenance
- Constitutional compliance preservation
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

# Import WINA components
from shared.wina import WINACore, WINAConfig, WINAIntegrationConfig
from shared.wina.model_integration import WINAModelIntegrator, WINAOptimizationResult
from shared.wina.config import load_wina_config_from_env
from shared.wina.exceptions import WINAError, WINAOptimizationError
from shared.wina.metrics import WINAMetrics

# Import GS Engine components
from .wina_llm_integration import WINAOptimizedLLMClient, WINAOptimizedSynthesisResult
from .constitutional_prompting import ConstitutionalPromptBuilder
from .llm_integration import get_llm_client
from ..schemas import ConstitutionalSynthesisInput, ConstitutionalSynthesisOutput

# Import AlphaEvolve components
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../alphaevolve_gs_engine/src'))
    from alphaevolve_gs_engine.services.policy_synthesizer import (
        LLMPolicyGenerator, PolicySynthesisInput, PolicySuggestion
    )
    from alphaevolve_gs_engine.services.llm_service import get_llm_service
    ALPHAEVOLVE_AVAILABLE = True
except ImportError as e:
    ALPHAEVOLVE_AVAILABLE = False

    # Mock PolicySuggestion for when AlphaEvolve is not available
    class PolicySuggestion:
        def __init__(self, suggested_policy_code="", confidence_score=0.0):
            self.suggested_policy_code = suggested_policy_code
            self.confidence_score = confidence_score

logger = logging.getLogger(__name__)


@dataclass
class WINARegoSynthesisMetrics:
    """Metrics for WINA-optimized Rego policy synthesis."""
    synthesis_time: float
    gflops_reduction: float
    accuracy_preservation: float
    constitutional_compliance: bool
    rego_validation_success: bool
    policy_complexity_score: float
    optimization_applied: bool
    error_count: int


@dataclass
class WINARegoSynthesisResult:
    """Result of WINA-optimized Rego policy synthesis."""
    policy_suggestion: Optional[PolicySuggestion]
    rego_content: str
    constitutional_compliance: bool
    wina_optimization: Optional[WINAOptimizationResult]
    synthesis_metrics: WINARegoSynthesisMetrics
    validation_result: Optional[Dict[str, Any]]
    warnings: List[str]
    success: bool


class WINARegoSynthesizer:
    """
    WINA-optimized Rego policy synthesizer.
    
    Integrates WINA optimization with the AlphaEvolve PolicySynthesizer
    to generate Rego policies with significant GFLOPs reduction while
    maintaining high synthesis accuracy and constitutional compliance.
    """
    
    def __init__(self, enable_wina: bool = True):
        """
        Initialize WINA-optimized Rego synthesizer.
        
        Args:
            enable_wina: Whether to enable WINA optimization
        """
        self.enable_wina = enable_wina
        
        # Initialize WINA components
        if enable_wina:
            try:
                self.wina_config, self.wina_integration_config = load_wina_config_from_env()
                self.wina_integrator = WINAModelIntegrator(self.wina_config, self.wina_integration_config)
                self.wina_metrics = WINAMetrics(self.wina_config)
                logger.info("WINA optimization enabled for Rego policy synthesis")
            except Exception as e:
                logger.warning(f"Failed to initialize WINA: {e}. Disabling WINA optimization.")
                self.enable_wina = False
        
        # Initialize LLM components
        self.wina_llm_client = WINAOptimizedLLMClient(enable_wina=enable_wina)
        self.constitutional_prompt_builder = ConstitutionalPromptBuilder()
        
        # Initialize AlphaEvolve components if available
        if ALPHAEVOLVE_AVAILABLE:
            try:
                llm_service = get_llm_service("real")  # Use real LLM for production
                self.alphaevolve_synthesizer = LLMPolicyGenerator(llm_service=llm_service)
                logger.info("AlphaEvolve PolicySynthesizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize AlphaEvolve synthesizer: {e}")
                self.alphaevolve_synthesizer = None
        else:
            self.alphaevolve_synthesizer = None
        
        # Performance tracking
        self._synthesis_history: List[WINARegoSynthesisResult] = []
        self._performance_metrics = {
            "total_syntheses": 0,
            "wina_optimized_syntheses": 0,
            "average_gflops_reduction": 0.0,
            "average_accuracy_preservation": 0.0,
            "constitutional_compliance_rate": 0.0,
            "rego_validation_success_rate": 0.0,
        }
    
    async def synthesize_rego_policy(
        self,
        synthesis_goal: str,
        constitutional_principles: List[Dict[str, Any]],
        constraints: Optional[List[str]] = None,
        context_data: Optional[Dict[str, Any]] = None,
        apply_wina: Optional[bool] = None
    ) -> WINARegoSynthesisResult:
        """
        Synthesize a Rego policy with WINA optimization.
        
        Args:
            synthesis_goal: Natural language description of policy goal
            constitutional_principles: List of constitutional principles to incorporate
            constraints: Optional constraints for the policy
            context_data: Additional context information
            apply_wina: Override WINA application (None uses default)
            
        Returns:
            WINARegoSynthesisResult containing optimized synthesis results
        """
        start_time = time.time()
        should_apply_wina = apply_wina if apply_wina is not None else self.enable_wina
        warnings = []
        
        try:
            logger.info(f"Starting WINA-optimized Rego synthesis for goal: '{synthesis_goal}' "
                       f"(WINA: {'enabled' if should_apply_wina else 'disabled'})")
            
            # Phase 1: Constitutional prompting with WINA optimization
            constitutional_synthesis_input = await self._prepare_constitutional_synthesis_input(
                synthesis_goal, constitutional_principles, constraints, context_data
            )
            
            # Phase 2: WINA-optimized constitutional synthesis
            wina_synthesis_result = await self.wina_llm_client.get_constitutional_synthesis_optimized(
                constitutional_synthesis_input, apply_wina=should_apply_wina
            )
            
            # Phase 3: AlphaEvolve policy synthesis (if available)
            policy_suggestion = None
            if self.alphaevolve_synthesizer:
                policy_suggestion = await self._synthesize_with_alphaevolve(
                    synthesis_goal, constitutional_principles, constraints, context_data,
                    wina_synthesis_result
                )
            
            # Phase 4: Extract and validate Rego content
            rego_content = await self._extract_rego_content(
                wina_synthesis_result, policy_suggestion, synthesis_goal
            )
            
            # Phase 5: Validate Rego syntax and constitutional compliance
            validation_result = await self._validate_rego_policy(rego_content)
            constitutional_compliance = await self._verify_constitutional_compliance(
                rego_content, constitutional_principles, wina_synthesis_result.wina_optimization
            )
            
            # Phase 6: Calculate performance metrics
            synthesis_time = time.time() - start_time
            synthesis_metrics = self._calculate_synthesis_metrics(
                wina_synthesis_result, synthesis_time, validation_result, constitutional_compliance
            )
            
            # Create result
            result = WINARegoSynthesisResult(
                policy_suggestion=policy_suggestion,
                rego_content=rego_content,
                constitutional_compliance=constitutional_compliance,
                wina_optimization=wina_synthesis_result.wina_optimization,
                synthesis_metrics=synthesis_metrics,
                validation_result=validation_result,
                warnings=warnings,
                success=validation_result.get('is_valid', False) and constitutional_compliance
            )
            
            # Update tracking
            await self._update_synthesis_tracking(result)
            
            logger.info(f"WINA-optimized Rego synthesis completed. "
                       f"Time: {synthesis_time:.3f}s, "
                       f"Success: {result.success}, "
                       f"GFLOPs reduction: {synthesis_metrics.gflops_reduction:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"WINA-optimized Rego synthesis failed: {e}")
            synthesis_time = time.time() - start_time
            
            # Return error result
            return WINARegoSynthesisResult(
                policy_suggestion=None,
                rego_content="",
                constitutional_compliance=False,
                wina_optimization=None,
                synthesis_metrics=WINARegoSynthesisMetrics(
                    synthesis_time=synthesis_time,
                    gflops_reduction=0.0,
                    accuracy_preservation=0.0,
                    constitutional_compliance=False,
                    rego_validation_success=False,
                    policy_complexity_score=0.0,
                    optimization_applied=False,
                    error_count=1
                ),
                validation_result={"is_valid": False, "error": str(e)},
                warnings=[f"Synthesis failed: {e}"],
                success=False
            )

    async def _prepare_constitutional_synthesis_input(
        self,
        synthesis_goal: str,
        constitutional_principles: List[Dict[str, Any]],
        constraints: Optional[List[str]],
        context_data: Optional[Dict[str, Any]]
    ) -> ConstitutionalSynthesisInput:
        """Prepare constitutional synthesis input with Rego-specific prompting."""

        # Build constitutional context
        constitutional_context = await self.constitutional_prompt_builder.build_constitutional_context(
            constitutional_principles
        )

        # Create Rego-specific requirements
        rego_requirements = [
            "Generate syntactically correct Rego policy code",
            "Include proper package declaration",
            "Follow Rego best practices and conventions",
            "Ensure policy is enforceable and testable",
            "Include clear rule logic and conditions"
        ]

        if constraints:
            rego_requirements.extend(constraints)

        # Create Rego-specific constraints
        rego_constraints = [
            "Output must be valid Rego syntax",
            "Policy must be compatible with OPA (Open Policy Agent)",
            "Include appropriate default rules",
            "Use clear variable naming conventions"
        ]

        # Prepare context with WINA optimization hints
        enhanced_context = {
            "target_format": "rego",
            "synthesis_goal": synthesis_goal,
            "constitutional_principles": constitutional_principles,
            "wina_optimization_enabled": self.enable_wina,
            "performance_targets": {
                "gflops_reduction": "40-70%",
                "accuracy_preservation": ">95%",
                "constitutional_compliance": "required"
            }
        }

        if context_data:
            enhanced_context.update(context_data)

        return ConstitutionalSynthesisInput(
            context=f"Rego Policy Synthesis: {synthesis_goal}",
            target_format="rego",
            requirements=rego_requirements,
            constraints=rego_constraints,
            constitutional_context=constitutional_context,
            additional_context=enhanced_context
        )

    async def _synthesize_with_alphaevolve(
        self,
        synthesis_goal: str,
        constitutional_principles: List[Dict[str, Any]],
        constraints: Optional[List[str]],
        context_data: Optional[Dict[str, Any]],
        wina_synthesis_result: WINAOptimizedSynthesisResult
    ) -> Optional[PolicySuggestion]:
        """Synthesize policy using AlphaEvolve with WINA optimization context."""

        if not self.alphaevolve_synthesizer:
            return None

        try:
            # Prepare AlphaEvolve synthesis input
            alphaevolve_input = PolicySynthesisInput(
                synthesis_goal=synthesis_goal,
                policy_type="operational_rule",
                desired_format="rego",
                constraints=constraints or [],
                context_data={
                    **(context_data or {}),
                    "constitutional_principles": constitutional_principles,
                    "wina_optimization_applied": wina_synthesis_result.optimization_applied,
                    "wina_performance_metrics": wina_synthesis_result.performance_metrics
                }
            )

            # Synthesize with AlphaEvolve
            policy_suggestion = self.alphaevolve_synthesizer.synthesize_policy(alphaevolve_input)

            if policy_suggestion:
                logger.info(f"AlphaEvolve synthesis successful. "
                           f"Confidence: {policy_suggestion.confidence_score}")
            else:
                logger.warning("AlphaEvolve synthesis returned no suggestion")

            return policy_suggestion

        except Exception as e:
            logger.error(f"AlphaEvolve synthesis failed: {e}")
            return None

    async def _extract_rego_content(
        self,
        wina_synthesis_result: WINAOptimizedSynthesisResult,
        policy_suggestion: Optional[PolicySuggestion],
        synthesis_goal: str
    ) -> str:
        """Extract and prioritize Rego content from synthesis results."""

        rego_content = ""

        # Priority 1: AlphaEvolve policy suggestion
        if policy_suggestion and policy_suggestion.suggested_policy_code:
            rego_content = policy_suggestion.suggested_policy_code
            logger.debug("Using Rego content from AlphaEvolve policy suggestion")

        # Priority 2: WINA constitutional synthesis result
        elif (wina_synthesis_result.original_result and
              hasattr(wina_synthesis_result.original_result, 'generated_rules') and
              wina_synthesis_result.original_result.generated_rules):

            # Extract Rego from generated rules
            rules = wina_synthesis_result.original_result.generated_rules
            if isinstance(rules, list) and rules:
                rego_content = rules[0]  # Take first rule
            elif isinstance(rules, str):
                rego_content = rules

            logger.debug("Using Rego content from WINA constitutional synthesis")

        # Priority 3: Generate fallback Rego policy
        else:
            rego_content = self._generate_fallback_rego_policy(synthesis_goal)
            logger.warning("Using fallback Rego policy generation")

        # Ensure proper Rego format
        rego_content = self._ensure_rego_format(rego_content, synthesis_goal)

        return rego_content

    def _generate_fallback_rego_policy(self, synthesis_goal: str) -> str:
        """Generate a basic fallback Rego policy."""

        package_name = "acgs.generated_policy"
        policy_name = synthesis_goal.lower().replace(" ", "_").replace("-", "_")[:50]

        return f"""
package {package_name}

# Generated policy for: {synthesis_goal}
# This is a fallback policy - manual review required

default allow = false
default deny = false

# Basic allow rule - customize based on requirements
allow {{
    # Add your policy logic here
    input.action == "read"
    input.resource != "sensitive"
}}

# Basic deny rule for sensitive resources
deny {{
    input.resource == "sensitive"
    not input.user.role == "admin"
}}

# Policy metadata
metadata := {{
    "name": "{policy_name}",
    "description": "{synthesis_goal}",
    "generated_by": "WINA-optimized synthesis",
    "requires_review": true
}}
""".strip()

    def _ensure_rego_format(self, content: str, synthesis_goal: str) -> str:
        """Ensure content is properly formatted as Rego policy."""

        if not content.strip():
            return self._generate_fallback_rego_policy(synthesis_goal)

        # Check if content already has package declaration
        if not content.strip().startswith("package "):
            package_name = "acgs.generated_policy"
            content = f"package {package_name}\n\n{content}"

        # Ensure default rules exist
        if "default allow" not in content and "default deny" not in content:
            lines = content.split('\n')
            package_line = lines[0] if lines[0].startswith("package ") else ""
            rest_content = '\n'.join(lines[1:] if package_line else lines)

            content = f"""{package_line}

# Default rules
default allow = false
default deny = false

{rest_content}"""

        return content.strip()

    async def _validate_rego_policy(self, rego_content: str) -> Dict[str, Any]:
        """Validate Rego policy syntax and structure."""

        validation_result = {
            "is_valid": False,
            "syntax_valid": False,
            "structure_valid": False,
            "warnings": [],
            "errors": []
        }

        try:
            # Basic syntax validation
            if not rego_content.strip():
                validation_result["errors"].append("Empty Rego content")
                return validation_result

            # Check for package declaration
            if not rego_content.strip().startswith("package "):
                validation_result["warnings"].append("Missing package declaration")
            else:
                validation_result["structure_valid"] = True

            # Check for basic Rego syntax elements
            required_elements = ["package ", "default ", "{", "}"]
            missing_elements = [elem for elem in required_elements if elem not in rego_content]

            if missing_elements:
                validation_result["warnings"].extend([
                    f"Missing Rego element: {elem.strip()}" for elem in missing_elements
                ])

            # Basic syntax validation (simplified)
            try:
                # Check for balanced braces
                open_braces = rego_content.count('{')
                close_braces = rego_content.count('}')
                if open_braces != close_braces:
                    validation_result["errors"].append(
                        f"Unbalanced braces: {open_braces} open, {close_braces} close"
                    )
                else:
                    validation_result["syntax_valid"] = True

            except Exception as e:
                validation_result["errors"].append(f"Syntax validation error: {e}")

            # Overall validation
            validation_result["is_valid"] = (
                validation_result["syntax_valid"] and
                len(validation_result["errors"]) == 0
            )

            logger.debug(f"Rego validation result: {validation_result}")

        except Exception as e:
            validation_result["errors"].append(f"Validation failed: {e}")
            logger.error(f"Rego validation error: {e}")

        return validation_result

    async def _verify_constitutional_compliance(
        self,
        rego_content: str,
        constitutional_principles: List[Dict[str, Any]],
        wina_optimization: Optional[WINAOptimizationResult]
    ) -> bool:
        """Verify constitutional compliance of the generated Rego policy."""

        try:
            compliance_checks = []

            # Check if WINA optimization maintains constitutional compliance
            if wina_optimization:
                compliance_checks.append(wina_optimization.constitutional_compliance)

            # Check if policy content references constitutional principles
            principle_references = 0
            for principle in constitutional_principles:
                principle_text = principle.get('description', '') or principle.get('text', '')
                if principle_text:
                    # Simple keyword matching (could be enhanced with semantic analysis)
                    keywords = principle_text.lower().split()[:5]  # Take first 5 words
                    for keyword in keywords:
                        if len(keyword) > 3 and keyword in rego_content.lower():
                            principle_references += 1
                            break

            # Constitutional compliance based on principle integration
            principle_compliance = principle_references > 0 or len(constitutional_principles) == 0
            compliance_checks.append(principle_compliance)

            # Check for basic policy structure compliance
            structure_compliance = (
                "package " in rego_content and
                ("allow" in rego_content or "deny" in rego_content)
            )
            compliance_checks.append(structure_compliance)

            # Overall compliance
            constitutional_compliance = all(compliance_checks) if compliance_checks else True

            logger.debug(f"Constitutional compliance: {constitutional_compliance}, "
                        f"checks: {compliance_checks}")

            return constitutional_compliance

        except Exception as e:
            logger.error(f"Constitutional compliance verification failed: {e}")
            return False

    def _calculate_synthesis_metrics(
        self,
        wina_synthesis_result: WINAOptimizedSynthesisResult,
        synthesis_time: float,
        validation_result: Dict[str, Any],
        constitutional_compliance: bool
    ) -> WINARegoSynthesisMetrics:
        """Calculate comprehensive synthesis metrics."""

        # Extract WINA optimization metrics
        gflops_reduction = 0.0
        accuracy_preservation = 0.0
        optimization_applied = False

        if wina_synthesis_result.wina_optimization:
            gflops_reduction = wina_synthesis_result.wina_optimization.gflops_reduction
            accuracy_preservation = wina_synthesis_result.wina_optimization.accuracy_preservation
            optimization_applied = True

        # Calculate policy complexity score (simplified)
        policy_complexity_score = 0.0
        if hasattr(wina_synthesis_result.original_result, 'generated_rules'):
            rules = wina_synthesis_result.original_result.generated_rules
            if isinstance(rules, list):
                policy_complexity_score = len(rules) * 0.1
            elif isinstance(rules, str):
                policy_complexity_score = len(rules.split('\n')) * 0.05

        # Count errors
        error_count = len(validation_result.get('errors', []))

        return WINARegoSynthesisMetrics(
            synthesis_time=synthesis_time,
            gflops_reduction=gflops_reduction,
            accuracy_preservation=accuracy_preservation,
            constitutional_compliance=constitutional_compliance,
            rego_validation_success=validation_result.get('is_valid', False),
            policy_complexity_score=policy_complexity_score,
            optimization_applied=optimization_applied,
            error_count=error_count
        )

    async def _update_synthesis_tracking(self, result: WINARegoSynthesisResult) -> None:
        """Update synthesis performance tracking."""

        try:
            self._synthesis_history.append(result)
            self._performance_metrics["total_syntheses"] += 1

            if result.synthesis_metrics.optimization_applied:
                self._performance_metrics["wina_optimized_syntheses"] += 1

            # Update running averages
            if result.wina_optimization:
                current_gflops = self._performance_metrics["average_gflops_reduction"]
                current_accuracy = self._performance_metrics["average_accuracy_preservation"]

                n = self._performance_metrics["wina_optimized_syntheses"]
                if n > 0:
                    self._performance_metrics["average_gflops_reduction"] = (
                        (current_gflops * (n - 1) + result.synthesis_metrics.gflops_reduction) / n
                    )
                    self._performance_metrics["average_accuracy_preservation"] = (
                        (current_accuracy * (n - 1) + result.synthesis_metrics.accuracy_preservation) / n
                    )

            # Update success rates
            compliant_syntheses = sum(1 for r in self._synthesis_history if r.constitutional_compliance)
            valid_syntheses = sum(1 for r in self._synthesis_history if r.synthesis_metrics.rego_validation_success)

            total = len(self._synthesis_history)
            self._performance_metrics["constitutional_compliance_rate"] = compliant_syntheses / total
            self._performance_metrics["rego_validation_success_rate"] = valid_syntheses / total

            # Log performance update
            logger.debug(f"Updated synthesis tracking. Total: {total}, "
                        f"WINA optimized: {self._performance_metrics['wina_optimized_syntheses']}, "
                        f"Compliance rate: {self._performance_metrics['constitutional_compliance_rate']:.3f}")

        except Exception as e:
            logger.error(f"Failed to update synthesis tracking: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""

        return {
            "performance_metrics": self._performance_metrics.copy(),
            "synthesis_history_count": len(self._synthesis_history),
            "wina_enabled": self.enable_wina,
            "recent_syntheses": [
                {
                    "success": r.success,
                    "gflops_reduction": r.synthesis_metrics.gflops_reduction,
                    "constitutional_compliance": r.constitutional_compliance,
                    "synthesis_time": r.synthesis_metrics.synthesis_time
                }
                for r in self._synthesis_history[-5:]  # Last 5 syntheses
            ],
            "target_performance": {
                "gflops_reduction_target": "40-70%",
                "accuracy_preservation_target": ">95%",
                "constitutional_compliance_target": "100%"
            }
        }


# Global instance for easy access
_wina_rego_synthesizer: Optional[WINARegoSynthesizer] = None


def get_wina_rego_synthesizer(enable_wina: bool = True) -> WINARegoSynthesizer:
    """
    Get the global WINA-optimized Rego synthesizer instance.

    Args:
        enable_wina: Whether to enable WINA optimization

    Returns:
        WINARegoSynthesizer instance
    """
    global _wina_rego_synthesizer

    if _wina_rego_synthesizer is None:
        _wina_rego_synthesizer = WINARegoSynthesizer(enable_wina=enable_wina)

    return _wina_rego_synthesizer


async def synthesize_rego_policy_with_wina(
    synthesis_goal: str,
    constitutional_principles: List[Dict[str, Any]],
    constraints: Optional[List[str]] = None,
    context_data: Optional[Dict[str, Any]] = None,
    apply_wina: Optional[bool] = None
) -> WINARegoSynthesisResult:
    """
    Helper function to synthesize Rego policy with WINA optimization.

    Args:
        synthesis_goal: Natural language description of policy goal
        constitutional_principles: List of constitutional principles to incorporate
        constraints: Optional constraints for the policy
        context_data: Additional context information
        apply_wina: Override WINA application (None uses default)

    Returns:
        WINARegoSynthesisResult containing optimized synthesis results
    """
    synthesizer = get_wina_rego_synthesizer()
    return await synthesizer.synthesize_rego_policy(
        synthesis_goal=synthesis_goal,
        constitutional_principles=constitutional_principles,
        constraints=constraints,
        context_data=context_data,
        apply_wina=apply_wina
    )


async def batch_synthesize_rego_policies_with_wina(
    synthesis_requests: List[Dict[str, Any]],
    enable_wina: bool = True
) -> List[WINARegoSynthesisResult]:
    """
    Batch synthesize multiple Rego policies with WINA optimization.

    Args:
        synthesis_requests: List of synthesis request dictionaries
        enable_wina: Whether to enable WINA optimization

    Returns:
        List of WINARegoSynthesisResult objects
    """
    synthesizer = get_wina_rego_synthesizer(enable_wina=enable_wina)
    results = []

    for request in synthesis_requests:
        try:
            result = await synthesizer.synthesize_rego_policy(
                synthesis_goal=request.get('synthesis_goal', ''),
                constitutional_principles=request.get('constitutional_principles', []),
                constraints=request.get('constraints'),
                context_data=request.get('context_data'),
                apply_wina=request.get('apply_wina')
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Batch synthesis failed for request: {e}")
            # Add error result
            results.append(WINARegoSynthesisResult(
                policy_suggestion=None,
                rego_content="",
                constitutional_compliance=False,
                wina_optimization=None,
                synthesis_metrics=WINARegoSynthesisMetrics(
                    synthesis_time=0.0,
                    gflops_reduction=0.0,
                    accuracy_preservation=0.0,
                    constitutional_compliance=False,
                    rego_validation_success=False,
                    policy_complexity_score=0.0,
                    optimization_applied=False,
                    error_count=1
                ),
                validation_result={"is_valid": False, "error": str(e)},
                warnings=[f"Batch synthesis failed: {e}"],
                success=False
            ))

    return results


def get_wina_rego_synthesis_performance_summary() -> Dict[str, Any]:
    """
    Get performance summary for WINA Rego synthesis operations.

    Returns:
        Dictionary containing performance metrics and statistics
    """
    synthesizer = get_wina_rego_synthesizer()
    return synthesizer.get_performance_summary()


def clear_wina_rego_synthesis_cache() -> None:
    """Clear WINA Rego synthesis cache and reset performance tracking."""
    global _wina_rego_synthesizer

    if _wina_rego_synthesizer:
        _wina_rego_synthesizer.wina_llm_client.clear_optimization_cache()
        _wina_rego_synthesizer._synthesis_history.clear()
        logger.info("WINA Rego synthesis cache cleared")


# Integration with existing GS service endpoints
class WINARegoSynthesisIntegration:
    """
    Integration class for connecting WINA Rego synthesis with existing GS service endpoints.
    """

    @staticmethod
    async def integrate_with_constitutional_synthesis(
        synthesis_input: ConstitutionalSynthesisInput,
        apply_wina: bool = True
    ) -> WINARegoSynthesisResult:
        """
        Integrate WINA Rego synthesis with constitutional synthesis endpoint.

        Args:
            synthesis_input: Constitutional synthesis input
            apply_wina: Whether to apply WINA optimization

        Returns:
            WINARegoSynthesisResult
        """
        # Extract constitutional principles from synthesis input
        constitutional_principles = []
        if hasattr(synthesis_input, 'constitutional_context'):
            # Parse constitutional context for principles
            context = synthesis_input.constitutional_context
            if isinstance(context, dict) and 'principles' in context:
                constitutional_principles = context['principles']

        # Extract constraints and context
        constraints = getattr(synthesis_input, 'constraints', [])
        context_data = getattr(synthesis_input, 'additional_context', {})

        # Perform WINA-optimized synthesis
        return await synthesize_rego_policy_with_wina(
            synthesis_goal=synthesis_input.context,
            constitutional_principles=constitutional_principles,
            constraints=constraints,
            context_data=context_data,
            apply_wina=apply_wina
        )

    @staticmethod
    async def integrate_with_alphaevolve_bridge(
        ec_context: str,
        optimization_objective: str,
        constitutional_constraints: List[str],
        apply_wina: bool = True
    ) -> WINARegoSynthesisResult:
        """
        Integrate WINA Rego synthesis with AlphaEvolve bridge.

        Args:
            ec_context: Evolutionary computation context
            optimization_objective: Optimization objective
            constitutional_constraints: Constitutional constraints
            apply_wina: Whether to apply WINA optimization

        Returns:
            WINARegoSynthesisResult
        """
        synthesis_goal = f"Generate governance rules for evolutionary computation: {optimization_objective}"

        # Create constitutional principles from constraints
        constitutional_principles = [
            {"description": constraint, "type": "governance_rule"}
            for constraint in constitutional_constraints
        ]

        context_data = {
            "ec_context": ec_context,
            "optimization_objective": optimization_objective,
            "target_system": "evolutionary_computation",
            "governance_type": "constitutional"
        }

        return await synthesize_rego_policy_with_wina(
            synthesis_goal=synthesis_goal,
            constitutional_principles=constitutional_principles,
            constraints=constitutional_constraints,
            context_data=context_data,
            apply_wina=apply_wina
        )
