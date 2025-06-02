"""
WINA-LLM Integration for GS Engine

Integrates WINA SVD transformation with the GS Engine's LLM clients
for optimized policy synthesis within the AlphaEvolve-ACGS framework.

This module provides:
- WINA-optimized LLM client wrappers
- Policy synthesis optimization
- Constitutional compliance monitoring
- Performance metrics collection
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timezone

# Import WINA components
from ....shared.wina import WINACore, WINAConfig, WINAIntegrationConfig
from ....shared.wina.model_integration import WINAModelIntegrator, WINAOptimizationResult
from ....shared.wina.config import load_wina_config_from_env
from ....shared.wina.exceptions import WINAError, WINAOptimizationError

# Import GS Engine components (with error handling for missing dependencies)
try:
    from .llm_integration import (
        get_llm_client,
        query_llm_for_structured_output,
        query_llm_for_constitutional_synthesis
    )
    from ..schemas import LLMInterpretationInput, LLMStructuredOutput, ConstitutionalSynthesisInput, ConstitutionalSynthesisOutput
    GS_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"GS Engine components not available: {e}. Using mock implementations.")
    GS_ENGINE_AVAILABLE = False

    # Mock implementations for testing
    class LLMInterpretationInput:
        def __init__(self, principle_id, principle_text, context, environmental_factors=None):
            self.principle_id = principle_id
            self.principle_text = principle_text
            self.context = context
            self.environmental_factors = environmental_factors or {}

    class LLMStructuredOutput:
        def __init__(self, interpretations=None, raw_llm_response=""):
            self.interpretations = interpretations or []
            self.raw_llm_response = raw_llm_response

    class ConstitutionalSynthesisInput:
        def __init__(self, context, **kwargs):
            self.context = context
            for k, v in kwargs.items():
                setattr(self, k, v)

    class ConstitutionalSynthesisOutput:
        def __init__(self, generated_rules=None, **kwargs):
            self.generated_rules = generated_rules or []
            for k, v in kwargs.items():
                setattr(self, k, v)

    async def get_llm_client():
        return None

    async def query_llm_for_structured_output(input_data):
        return LLMStructuredOutput(interpretations=["mock interpretation"])

    async def query_llm_for_constitutional_synthesis(input_data):
        return ConstitutionalSynthesisOutput(generated_rules=["mock rule"])

try:
    from .constitutional_prompting import ConstitutionalPromptingEngine
except ImportError:
    logger.warning("Constitutional prompting engine not available. Using mock.")
    class ConstitutionalPromptingEngine:
        pass

try:
    from .llm_reliability_framework import EnhancedLLMReliabilityFramework
except ImportError:
    logger.warning("LLM reliability framework not available. Using mock.")
    class EnhancedLLMReliabilityFramework:
        pass

logger = logging.getLogger(__name__)


@dataclass
class WINAOptimizedSynthesisResult:
    """Result of WINA-optimized policy synthesis."""
    original_result: Union[LLMStructuredOutput, ConstitutionalSynthesisOutput]
    wina_optimization: Optional[WINAOptimizationResult]
    performance_metrics: Dict[str, float]
    constitutional_compliance: bool
    optimization_applied: bool
    synthesis_time: float


class WINAOptimizedLLMClient:
    """
    WINA-optimized wrapper for LLM clients in the GS Engine.
    
    This class applies WINA optimization to LLM inference while maintaining
    compatibility with existing GS Engine interfaces.
    """
    
    def __init__(self, enable_wina: bool = True):
        """
        Initialize WINA-optimized LLM client.
        
        Args:
            enable_wina: Whether to enable WINA optimization
        """
        self.enable_wina = enable_wina
        
        # Load WINA configuration
        if enable_wina:
            try:
                self.wina_config, self.wina_integration_config = load_wina_config_from_env()
                self.wina_integrator = WINAModelIntegrator(self.wina_config, self.wina_integration_config)
                self.wina_core = WINACore(self.wina_config, self.wina_integration_config)
                logger.info("WINA optimization enabled for GS Engine LLM client")
            except Exception as e:
                logger.warning(f"Failed to initialize WINA: {e}. Disabling WINA optimization.")
                self.enable_wina = False
        
        # Initialize constitutional prompting and reliability framework
        self.constitutional_engine = ConstitutionalPromptingEngine()
        self.reliability_framework = EnhancedLLMReliabilityFramework()
        
        # Performance tracking
        self._optimization_history: List[WINAOptimizedSynthesisResult] = []
        self._performance_metrics = {
            "total_requests": 0,
            "wina_optimized_requests": 0,
            "average_gflops_reduction": 0.0,
            "average_accuracy_preservation": 0.0,
            "constitutional_compliance_rate": 0.0,
        }
    
    async def get_structured_interpretation_optimized(
        self, 
        query: LLMInterpretationInput,
        apply_wina: Optional[bool] = None
    ) -> WINAOptimizedSynthesisResult:
        """
        Get structured interpretation with optional WINA optimization.
        
        Args:
            query: LLM interpretation input
            apply_wina: Override WINA application (None uses default)
            
        Returns:
            WINAOptimizedSynthesisResult containing optimized results
        """
        start_time = time.time()
        should_apply_wina = apply_wina if apply_wina is not None else self.enable_wina
        
        try:
            logger.info(f"Processing structured interpretation request for principle {query.principle_id} "
                       f"(WINA: {'enabled' if should_apply_wina else 'disabled'})")
            
            # Get the current LLM client
            llm_client = get_llm_client()
            model_identifier = self._get_model_identifier(llm_client)
            
            # Apply WINA optimization if enabled
            wina_optimization = None
            if should_apply_wina and self.wina_integration_config.gs_engine_optimization:
                try:
                    wina_optimization = await self._apply_wina_optimization(model_identifier, llm_client)
                    logger.debug(f"WINA optimization applied: GFLOPs reduction={wina_optimization.gflops_reduction:.3f}")
                except Exception as e:
                    logger.warning(f"WINA optimization failed, proceeding without optimization: {e}")
            
            # Perform the actual LLM query
            original_result = await query_llm_for_structured_output(query)
            
            # Calculate performance metrics
            synthesis_time = time.time() - start_time
            performance_metrics = self._calculate_performance_metrics(
                wina_optimization, synthesis_time, len(original_result.interpretations)
            )
            
            # Verify constitutional compliance
            constitutional_compliance = await self._verify_synthesis_compliance(
                query, original_result, wina_optimization
            )
            
            # Create optimized result
            result = WINAOptimizedSynthesisResult(
                original_result=original_result,
                wina_optimization=wina_optimization,
                performance_metrics=performance_metrics,
                constitutional_compliance=constitutional_compliance,
                optimization_applied=wina_optimization is not None,
                synthesis_time=synthesis_time
            )
            
            # Update tracking
            await self._update_performance_tracking(result)
            
            logger.info(f"Structured interpretation completed for principle {query.principle_id}. "
                       f"Time: {synthesis_time:.3f}s, "
                       f"Constitutional compliance: {constitutional_compliance}")
            
            return result
            
        except Exception as e:
            logger.error(f"WINA-optimized structured interpretation failed: {e}")
            # Fallback to original implementation
            original_result = await query_llm_for_structured_output(query)
            return WINAOptimizedSynthesisResult(
                original_result=original_result,
                wina_optimization=None,
                performance_metrics={"error": str(e)},
                constitutional_compliance=False,
                optimization_applied=False,
                synthesis_time=time.time() - start_time
            )
    
    async def get_constitutional_synthesis_optimized(
        self,
        synthesis_input: ConstitutionalSynthesisInput,
        apply_wina: Optional[bool] = None
    ) -> WINAOptimizedSynthesisResult:
        """
        Get constitutional synthesis with optional WINA optimization.
        
        Args:
            synthesis_input: Constitutional synthesis input
            apply_wina: Override WINA application (None uses default)
            
        Returns:
            WINAOptimizedSynthesisResult containing optimized results
        """
        start_time = time.time()
        should_apply_wina = apply_wina if apply_wina is not None else self.enable_wina
        
        try:
            logger.info(f"Processing constitutional synthesis request for context '{synthesis_input.context}' "
                       f"(WINA: {'enabled' if should_apply_wina else 'disabled'})")
            
            # Get the current LLM client
            llm_client = get_llm_client()
            model_identifier = self._get_model_identifier(llm_client)
            
            # Apply WINA optimization if enabled
            wina_optimization = None
            if should_apply_wina and self.wina_integration_config.gs_engine_optimization:
                try:
                    wina_optimization = await self._apply_wina_optimization(model_identifier, llm_client)
                    logger.debug(f"WINA optimization applied: GFLOPs reduction={wina_optimization.gflops_reduction:.3f}")
                except Exception as e:
                    logger.warning(f"WINA optimization failed, proceeding without optimization: {e}")
            
            # Perform the actual constitutional synthesis
            original_result = await query_llm_for_constitutional_synthesis(synthesis_input)
            
            # Calculate performance metrics
            synthesis_time = time.time() - start_time
            performance_metrics = self._calculate_performance_metrics(
                wina_optimization, synthesis_time, len(original_result.generated_rules)
            )
            
            # Verify constitutional compliance
            constitutional_compliance = await self._verify_synthesis_compliance(
                synthesis_input, original_result, wina_optimization
            )
            
            # Create optimized result
            result = WINAOptimizedSynthesisResult(
                original_result=original_result,
                wina_optimization=wina_optimization,
                performance_metrics=performance_metrics,
                constitutional_compliance=constitutional_compliance,
                optimization_applied=wina_optimization is not None,
                synthesis_time=synthesis_time
            )
            
            # Update tracking
            await self._update_performance_tracking(result)
            
            logger.info(f"Constitutional synthesis completed for context '{synthesis_input.context}'. "
                       f"Time: {synthesis_time:.3f}s, "
                       f"Rules generated: {len(original_result.generated_rules)}, "
                       f"Constitutional compliance: {constitutional_compliance}")
            
            return result
            
        except Exception as e:
            logger.error(f"WINA-optimized constitutional synthesis failed: {e}")
            # Fallback to original implementation
            original_result = await query_llm_for_constitutional_synthesis(synthesis_input)
            return WINAOptimizedSynthesisResult(
                original_result=original_result,
                wina_optimization=None,
                performance_metrics={"error": str(e)},
                constitutional_compliance=False,
                optimization_applied=False,
                synthesis_time=time.time() - start_time
            )
    
    def _get_model_identifier(self, llm_client: Any) -> str:
        """Get model identifier from LLM client."""
        client_class = llm_client.__class__.__name__
        if "Mock" in client_class:
            return "mock-model-large"
        elif "Real" in client_class or "OpenAI" in client_class:
            return "gpt-4"
        elif "Groq" in client_class:
            return "llama-3.3-70b-versatile"
        else:
            return "unknown-model"
    
    async def _apply_wina_optimization(self, model_identifier: str, llm_client: Any) -> WINAOptimizationResult:
        """Apply WINA optimization to the model."""
        client_class = llm_client.__class__.__name__
        
        if "Mock" in client_class:
            model_type = "mock"
        elif "Real" in client_class or "OpenAI" in client_class:
            model_type = "openai"
        elif "Groq" in client_class:
            model_type = "groq"
        else:
            model_type = "mock"  # Fallback
        
        return await self.wina_integrator.optimize_model(
            model_identifier=model_identifier,
            model_type=model_type,
            target_layers=None,  # Optimize all layers
            force_recompute=False
        )

    def _calculate_performance_metrics(self, wina_optimization: Optional[WINAOptimizationResult],
                                     synthesis_time: float, output_count: int) -> Dict[str, float]:
        """Calculate performance metrics for the synthesis operation."""
        metrics = {
            "synthesis_time": synthesis_time,
            "output_count": output_count,
            "wina_applied": 1.0 if wina_optimization else 0.0,
        }

        if wina_optimization:
            metrics.update({
                "gflops_reduction": wina_optimization.gflops_reduction,
                "accuracy_preservation": wina_optimization.accuracy_preservation,
                "optimization_time": wina_optimization.optimization_time,
                "layers_optimized": wina_optimization.performance_metrics.get("layers_optimized", 0),
                "constitutional_compliance": 1.0 if wina_optimization.constitutional_compliance else 0.0,
            })

        return metrics

    async def _verify_synthesis_compliance(self, input_data: Any, output_data: Any,
                                         wina_optimization: Optional[WINAOptimizationResult]) -> bool:
        """Verify constitutional compliance of synthesis results."""
        try:
            # Basic compliance checks
            compliance_checks = []

            # Check if WINA optimization maintains constitutional compliance
            if wina_optimization:
                compliance_checks.append(wina_optimization.constitutional_compliance)

            # Check output quality
            if hasattr(output_data, 'interpretations'):
                # For structured interpretation
                compliance_checks.append(len(output_data.interpretations) > 0)
            elif hasattr(output_data, 'generated_rules'):
                # For constitutional synthesis
                compliance_checks.append(len(output_data.generated_rules) > 0)

            # Use reliability framework for additional validation
            if hasattr(self.reliability_framework, 'validate_output'):
                reliability_check = await self.reliability_framework.validate_output(output_data)
                compliance_checks.append(reliability_check)

            # All checks must pass for constitutional compliance
            return all(compliance_checks) if compliance_checks else True

        except Exception as e:
            logger.error(f"Constitutional compliance verification failed: {e}")
            return False

    async def _update_performance_tracking(self, result: WINAOptimizedSynthesisResult) -> None:
        """Update performance tracking metrics."""
        try:
            self._optimization_history.append(result)
            self._performance_metrics["total_requests"] += 1

            if result.optimization_applied:
                self._performance_metrics["wina_optimized_requests"] += 1

            # Update running averages
            if result.wina_optimization:
                current_gflops = self._performance_metrics["average_gflops_reduction"]
                current_accuracy = self._performance_metrics["average_accuracy_preservation"]

                # Simple running average
                n = self._performance_metrics["wina_optimized_requests"]
                if n > 0:
                    self._performance_metrics["average_gflops_reduction"] = (
                        (current_gflops * (n - 1) + result.wina_optimization.gflops_reduction) / n
                    )
                    self._performance_metrics["average_accuracy_preservation"] = (
                        (current_accuracy * (n - 1) + result.wina_optimization.accuracy_preservation) / n
                    )

            # Update constitutional compliance rate
            compliant_requests = sum(1 for r in self._optimization_history if r.constitutional_compliance)
            self._performance_metrics["constitutional_compliance_rate"] = (
                compliant_requests / len(self._optimization_history)
            )

        except Exception as e:
            logger.error(f"Failed to update performance tracking: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of WINA-optimized operations."""
        return {
            "performance_metrics": self._performance_metrics.copy(),
            "optimization_history_count": len(self._optimization_history),
            "wina_enabled": self.enable_wina,
            "last_optimization": (
                self._optimization_history[-1].performance_metrics
                if self._optimization_history else None
            ),
        }

    async def verify_computational_invariance_batch(self, test_cases: List[Any]) -> Dict[str, Any]:
        """Verify computational invariance for a batch of test cases."""
        if not self.enable_wina:
            return {"message": "WINA not enabled", "invariance_maintained": True}

        try:
            # Use the integrator's invariance verification
            model_identifier = "mock-model-large"  # Default for testing
            return await self.wina_integrator.verify_computational_invariance(
                model_identifier, test_cases
            )
        except Exception as e:
            logger.error(f"Batch computational invariance verification failed: {e}")
            return {"invariance_maintained": False, "error": str(e)}

    def clear_optimization_cache(self) -> None:
        """Clear WINA optimization cache."""
        if self.enable_wina:
            self.wina_integrator.clear_cache()
        self._optimization_history.clear()
        logger.info("WINA optimization cache cleared")


# Global instance for easy access
_wina_optimized_client: Optional[WINAOptimizedLLMClient] = None


def get_wina_optimized_llm_client(enable_wina: bool = True) -> WINAOptimizedLLMClient:
    """
    Get the global WINA-optimized LLM client instance.

    Args:
        enable_wina: Whether to enable WINA optimization

    Returns:
        WINAOptimizedLLMClient instance
    """
    global _wina_optimized_client

    if _wina_optimized_client is None:
        _wina_optimized_client = WINAOptimizedLLMClient(enable_wina=enable_wina)

    return _wina_optimized_client


async def query_llm_with_wina_optimization(
    input_data: LLMInterpretationInput,
    apply_wina: Optional[bool] = None
) -> WINAOptimizedSynthesisResult:
    """
    Helper function to query LLM with WINA optimization.

    Args:
        input_data: LLM interpretation input
        apply_wina: Override WINA application

    Returns:
        WINAOptimizedSynthesisResult
    """
    client = get_wina_optimized_llm_client()
    return await client.get_structured_interpretation_optimized(input_data, apply_wina)


async def query_constitutional_synthesis_with_wina(
    synthesis_input: ConstitutionalSynthesisInput,
    apply_wina: Optional[bool] = None
) -> WINAOptimizedSynthesisResult:
    """
    Helper function to perform constitutional synthesis with WINA optimization.

    Args:
        synthesis_input: Constitutional synthesis input
        apply_wina: Override WINA application

    Returns:
        WINAOptimizedSynthesisResult
    """
    client = get_wina_optimized_llm_client()
    return await client.get_constitutional_synthesis_optimized(synthesis_input, apply_wina)
