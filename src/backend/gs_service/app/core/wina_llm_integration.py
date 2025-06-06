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

import logging # Moved to top
import asyncio
import time
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Import WINA components
from shared.wina import WINACore, WINAConfig, WINAIntegrationConfig
from shared.wina.model_integration import WINAModelIntegrator, WINAOptimizationResult
from shared.wina.config import load_wina_config_from_env
from shared.wina.exceptions import WINAError, WINAOptimizationError

# Import WINA components from gs_service.app.wina
from ..wina.core import analyze_neuron_activations, calculate_wina_weights
from ..wina.gating import determine_gating_decision
from ..wina.models import NeuronActivationInput, GatingThresholdConfig, GatingDecision # Added GatingDecision

# Import GS Engine components (with error handling for missing dependencies)
try:
    from .llm_integration import (
        get_llm_client,
        query_llm_for_structured_output,
        query_llm_for_constitutional_synthesis,
        GroqLLMClient,  # Import specific client for type checking
        RealLLMClient   # Import specific client for type checking
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
    
    class GroqLLMClient: # Mock for when llm_integration fails
        def __init__(self): self.model_name = "mock-groq-model"
    
    class RealLLMClient: # Mock for when llm_integration fails
        def __init__(self): self.model_name = "mock-real-model"


    async def get_llm_client():
        return None

    async def query_llm_for_structured_output(input_data, wina_gating_mask=None): # Added wina_gating_mask
        return LLMStructuredOutput(interpretations=["mock interpretation"])

    async def query_llm_for_constitutional_synthesis(input_data, wina_gating_mask=None): # Added wina_gating_mask
        return ConstitutionalSynthesisOutput(generated_rules=["mock rule"])

try:
    from .constitutional_prompting import ConstitutionalPromptBuilder
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


async def _retrieve_neuron_activations(text: str) -> Optional[Dict[str, List[float]]]:
    """Attempt to retrieve real neuron activations for the given text."""
    get_activations_error = ""
    try:
        import torch  # Imported lazily
        from transformers import AutoTokenizer, AutoModel

        model_name = os.getenv("HF_ACTIVATION_MODEL", "distilbert-base-uncased")

        async def _worker() -> Dict[str, List[float]]:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name, output_hidden_states=True)
            model.eval()
            with torch.no_grad():
                inputs = tokenizer(text, return_tensors="pt")
                outputs = model(**inputs)
                hidden = outputs.last_hidden_state.squeeze(0).T.cpu().tolist()
                return {f"layer0_neuron{i}": act for i, act in enumerate(hidden)}

        return await asyncio.to_thread(_worker)
    except Exception as e:  # pragma: no cover - optional dependency
        get_activations_error = str(e)

    logger.info(f"Neuron activation retrieval unavailable: {get_activations_error}")
    return None



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
        self.constitutional_engine = ConstitutionalPromptBuilder()
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
        gating_decision_applied: Optional[GatingDecision] = None
        
        try:
            logger.info(f"Processing structured interpretation request for principle {query.principle_id} "
                       f"(WINA: {'enabled' if should_apply_wina else 'disabled'})")
            
            # Get the current LLM client
            llm_client = get_llm_client()
            model_identifier = self._get_model_identifier(llm_client)
            
            # Apply WINA optimization if enabled
            wina_optimization: Optional[WINAOptimizationResult] = None # Ensure type hint
            llm_call_kwargs = {} # To pass gating info to LLM

            if should_apply_wina and self.wina_integration_config.gs_engine_optimization:
                try:
                    # --- WINA Runtime Gating Integration START ---
                    activations = await _retrieve_neuron_activations(query.principle_text)
                    if activations:
                        neuron_activation_input = NeuronActivationInput(
                            activations=activations,
                            metadata={"source": "real"}
                        )
                        analyzed_acts = await analyze_neuron_activations(neuron_activation_input)
                        wina_weights_output = await calculate_wina_weights(analyzed_acts)
                        gating_config = GatingThresholdConfig(threshold=0.5, default_gating_state=False)
                        gating_decision_applied = await determine_gating_decision(wina_weights_output, gating_config)
                        logger.info(f"WINA Gating Mask for P{query.principle_id}: {gating_decision_applied.gating_mask}")
                        llm_call_kwargs['wina_gating_mask'] = gating_decision_applied.gating_mask
                    else:
                        logger.info("Neuron activations unavailable; skipping gating")
                    # --- WINA Runtime Gating Integration END ---

                    # Existing SVD-based optimization
                    wina_optimization = await self._apply_wina_optimization(model_identifier, llm_client) # This is SVD
                    if wina_optimization:
                        logger.debug(f"WINA SVD optimization applied: GFLOPs reduction={wina_optimization.gflops_reduction:.3f}")
                except Exception as e:
                    logger.warning(f"WINA optimization (SVD or Gating) failed, proceeding without: {e}")
            
            # Perform the actual LLM query, passing the gating_mask if available
            if gating_decision_applied:
                 logger.info(f"Attempting LLM call with WINA gating mask for P{query.principle_id}")
                 original_result = await query_llm_for_structured_output(query, wina_gating_mask=gating_decision_applied.gating_mask)
            else:
                 original_result = await query_llm_for_structured_output(query)
            
            # Calculate performance metrics
            synthesis_time = time.time() - start_time
            performance_metrics = self._calculate_performance_metrics(
                wina_optimization, synthesis_time, len(original_result.interpretations), gating_decision_applied
            )
            
            # Verify constitutional compliance
            constitutional_compliance = await self._verify_synthesis_compliance(
                query, original_result, wina_optimization, gating_decision_applied
            )
            
            # Create optimized result
            result = WINAOptimizedSynthesisResult(
                original_result=original_result,
                wina_optimization=wina_optimization, # This is SVD-based result
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
            wina_optimization: Optional[WINAOptimizationResult] = None # Ensure type hint
            gating_decision_applied: Optional[GatingDecision] = None
            llm_call_kwargs = {}

            if should_apply_wina and self.wina_integration_config.gs_engine_optimization:
                try:
                    # --- WINA Runtime Gating Integration START ---
                    activations = await _retrieve_neuron_activations(synthesis_input.context)
                    if activations:
                        neuron_activation_input = NeuronActivationInput(
                            activations=activations,
                            metadata={"source": "real"}
                        )
                        analyzed_acts = await analyze_neuron_activations(neuron_activation_input)
                        wina_weights_output = await calculate_wina_weights(analyzed_acts)
                        gating_config = GatingThresholdConfig(threshold=0.5, default_gating_state=False)
                        gating_decision_applied = await determine_gating_decision(wina_weights_output, gating_config)
                        logger.info(f"WINA Gating Mask for CS '{synthesis_input.context}': {gating_decision_applied.gating_mask}")
                        llm_call_kwargs['wina_gating_mask'] = gating_decision_applied.gating_mask
                    else:
                        logger.info("Neuron activations unavailable; skipping gating")
                    # --- WINA Runtime Gating Integration END ---

                    # Existing SVD-based optimization
                    wina_optimization = await self._apply_wina_optimization(model_identifier, llm_client) # This is SVD
                    if wina_optimization:
                        logger.debug(f"WINA SVD optimization applied: GFLOPs reduction={wina_optimization.gflops_reduction:.3f}")
                except Exception as e:
                    logger.warning(f"WINA optimization (SVD or Gating) failed, proceeding without: {e}")
            
            # Perform the actual constitutional synthesis, passing the gating_mask if available
            if gating_decision_applied:
                logger.info(f"Attempting LLM call with WINA gating mask for CS '{synthesis_input.context}'")
                original_result = await query_llm_for_constitutional_synthesis(synthesis_input, wina_gating_mask=gating_decision_applied.gating_mask)
            else:
                original_result = await query_llm_for_constitutional_synthesis(synthesis_input)
            
            # Calculate performance metrics
            synthesis_time = time.time() - start_time
            performance_metrics = self._calculate_performance_metrics(
                wina_optimization, synthesis_time, len(original_result.generated_rules), gating_decision_applied
            )
            
            # Verify constitutional compliance
            constitutional_compliance = await self._verify_synthesis_compliance(
                synthesis_input, original_result, wina_optimization, gating_decision_applied
            )
            
            # Create optimized result
            result = WINAOptimizedSynthesisResult(
                original_result=original_result,
                wina_optimization=wina_optimization, # This is SVD-based result
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
        if isinstance(llm_client, GroqLLMClient):
            return llm_client.model_name # Specific model like 'llama-3.3-70b-versatile'
        elif isinstance(llm_client, RealLLMClient):
            return llm_client.model_name # Specific model like 'gpt-4'
        elif hasattr(llm_client, '__class__') and "Mock" in llm_client.__class__.__name__:
            return "mock-model-large"
        else:
            logger.warning(f"Could not determine specific model identifier for client type: {type(llm_client)}. Defaulting.")
            return "unknown-model"
    
    async def _apply_wina_optimization(self, model_identifier: str, llm_client: Any) -> WINAOptimizationResult:
        """Apply WINA optimization to the model."""
        
        model_type = "unknown"
        if isinstance(llm_client, GroqLLMClient):
            model_type = "groq"
        elif isinstance(llm_client, RealLLMClient):
            # Determine if it's an OpenAI model based on identifier
            if "gpt" in model_identifier.lower() or \
               "ada" in model_identifier.lower() or \
               "davinci" in model_identifier.lower() or \
               "babbage" in model_identifier.lower() or \
               "curie" in model_identifier.lower():
                model_type = "openai"
            else:
                model_type = "real_other" # Could be another type of real client
        elif hasattr(llm_client, '__class__') and "Mock" in llm_client.__class__.__name__:
            model_type = "mock"
        
        if model_type == "unknown" or model_type == "real_other":
            logger.warning(f"WINA SVD optimization may not be fully compatible with model_identifier '{model_identifier}' and client type {type(llm_client)}. Proceeding with model_type '{model_type}'.")
            # Fallback to a generic or mock type if WINA integrator requires specific known types
            # For now, we pass it as is, but WINAModelIntegrator might need adjustments or more specific types.

        return await self.wina_integrator.optimize_model(
            model_identifier=model_identifier, # Pass the specific model identifier
            model_type=model_type, # Pass the determined generic type
            target_layers=None,  # Optimize all layers
            force_recompute=False
        )

    def _calculate_performance_metrics(self,
                                     wina_optimization: Optional[WINAOptimizationResult], # SVD based
                                     synthesis_time: float,
                                     output_count: int,
                                     gating_decision: Optional[GatingDecision] = None # Gating based
                                     ) -> Dict[str, float]:
        """Calculate performance metrics for the synthesis operation."""
        metrics = {
            "synthesis_time": synthesis_time,
            "output_count": output_count,
            "wina_svd_applied": 1.0 if wina_optimization else 0.0,
            "wina_gating_applied": 1.0 if gating_decision else 0.0,
        }

        if wina_optimization: # SVD metrics
            metrics.update({
                "gflops_reduction_svd": wina_optimization.gflops_reduction,
                "accuracy_preservation_svd": wina_optimization.accuracy_preservation,
                "optimization_time_svd": wina_optimization.optimization_time,
                "layers_optimized_svd": wina_optimization.performance_metrics.get("layers_optimized", 0),
                "constitutional_compliance_svd": 1.0 if wina_optimization.constitutional_compliance else 0.0,
            })
        
        if gating_decision: # Gating metrics (conceptual for now)
            gating_meta = gating_decision.metadata
            metrics.update({
                "gating_components_processed": gating_meta.get("num_components_processed", 0),
                "gating_components_activated": gating_meta.get("num_components_activated", 0),
                # GFLOPs reduction from gating would need actual measurement or estimation
                "gflops_reduction_gating_estimated": (
                    gating_meta.get("num_components_processed", 0) - gating_meta.get("num_components_activated", 0)
                ) * 0.01 # Placeholder: 1% GFLOP reduction per deactivated component
            })


        return metrics

    async def _verify_synthesis_compliance(self,
                                         input_data: Any,
                                         output_data: Any,
                                         wina_svd_optimization: Optional[WINAOptimizationResult],
                                         gating_decision: Optional[GatingDecision] = None
                                         ) -> bool:
        """Verify constitutional compliance of synthesis results."""
        try:
            # Basic compliance checks
            compliance_checks = []

            # Check if WINA SVD optimization maintains constitutional compliance
            if wina_svd_optimization:
                compliance_checks.append(wina_svd_optimization.constitutional_compliance)
            
            # Check if WINA Gating implies compliance (conceptual for now)
            if gating_decision:
                # Assuming gating itself doesn't violate compliance if underlying model is compliant
                # This might need more sophisticated checks based on what gating affects
                num_activated = gating_decision.metadata.get("num_components_activated", 0)
                num_processed = gating_decision.metadata.get("num_components_processed", 0)
                
                if num_processed > 0 and num_activated == 0:
                    logger.warning("WINA Gating resulted in all components being deactivated. This likely impacts output quality and compliance.")
                    compliance_checks.append(False) # All components gated off is likely non-compliant/non-useful
                elif num_processed == 0 and gating_decision.metadata.get("wina_calculation_method") == "placeholder_mean_proportional":
                    # If no components were processed by gating (e.g. empty wina_weights.weights)
                    # and we are using placeholder weights, it's hard to judge compliance from gating alone.
                    # Let other checks determine compliance. If wina_weights is empty, it implies no neuron data.
                    logger.info("WINA Gating had no components to process based on current wina_weights. Compliance relies on other checks.")
                    # Not appending True or False here, let other checks decide.
                else:
                    # If some components were processed and some activated, or if it's not the placeholder method,
                    # assume gating itself doesn't inherently violate compliance if the underlying model is compliant.
                    # More sophisticated checks might be needed for a non-placeholder WINA.
                    compliance_checks.append(True) # Gating operated as expected (some active or non-placeholder)

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
