#!/usr/bin/env python3
"""
WINA SVD Integration Test Script

Comprehensive testing script for WINA SVD transformation integration
with the GS Engine LLM clients in the AlphaEvolve-ACGS framework.

This script validates:
1. SVD transformation with real model weights
2. Computational invariance verification
3. Performance metrics and GFLOPs reduction
4. Constitutional compliance validation
5. Integration with policy synthesis workloads
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import torch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import WINA components
from src.backend.shared.wina import (
    WINAConfig,
    WINAIntegrationConfig,
    WINAModelIntegrator,
    MockModelWeightExtractor,
    SVDTransformation
)
from src.backend.shared.wina.config import load_wina_config_from_env

# Import GS Engine components
from src.backend.gs_service.app.core.wina_llm_integration import (
    WINAOptimizedLLMClient,
    get_wina_optimized_llm_client,
    query_llm_with_wina_optimization
)
from src.backend.gs_service.app.schemas import LLMInterpretationInput, ConstitutionalSynthesisInput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WINASVDIntegrationTester:
    """Comprehensive tester for WINA SVD integration."""
    
    def __init__(self):
        """Initialize the tester."""
        self.results = {}
        self.performance_metrics = {}
        
        # Initialize WINA configuration
        try:
            self.wina_config, self.integration_config = load_wina_config_from_env()
        except Exception:
            # Use default configuration if environment not set
            self.wina_config = WINAConfig(
                target_sparsity=0.6,
                gflops_reduction_target=0.5,
                accuracy_threshold=0.95,
                enable_svd_transformation=True,
                svd_rank_reduction=0.8
            )
            self.integration_config = WINAIntegrationConfig(
                gs_engine_optimization=True,
                constitutional_compliance_strict=True
            )
        
        # Initialize components
        self.model_integrator = WINAModelIntegrator(self.wina_config, self.integration_config)
        self.svd_transformer = SVDTransformation(self.wina_config)
        self.wina_client = WINAOptimizedLLMClient(enable_wina=True)
        
        logger.info("WINA SVD Integration Tester initialized")
    
    async def test_svd_transformation_accuracy(self) -> Dict[str, Any]:
        """Test SVD transformation accuracy and numerical stability."""
        logger.info("Testing SVD transformation accuracy...")
        
        test_results = {}
        test_matrices = [
            ("small_matrix", torch.randn(256, 512)),
            ("medium_matrix", torch.randn(1024, 2048)),
            ("large_matrix", torch.randn(4096, 8192)),
            ("attention_matrix", torch.randn(768, 768)),
            ("mlp_gate_matrix", torch.randn(768, 3072))
        ]
        
        for matrix_name, test_matrix in test_matrices:
            try:
                # Apply SVD transformation
                result = self.svd_transformer.transform_weight_matrix(test_matrix, matrix_name)
                
                # Verify computational invariance
                invariance_metrics = self.svd_transformer.verify_computational_invariance(
                    test_matrix, result.transformed_tensor, tolerance=1e-6
                )
                
                test_results[matrix_name] = {
                    "original_shape": test_matrix.shape,
                    "compression_ratio": result.compression_ratio,
                    "numerical_stability": result.numerical_stability,
                    "transformation_time": result.transformation_time,
                    "invariance_maintained": invariance_metrics["invariance_maintained"],
                    "relative_error": invariance_metrics["relative_error"],
                    "frobenius_error": invariance_metrics["frobenius_error"]
                }
                
                logger.info(f"  {matrix_name}: compression={result.compression_ratio:.3f}, "
                           f"stability={result.numerical_stability:.3f}, "
                           f"invariance={invariance_metrics['invariance_maintained']}")
                
            except Exception as e:
                logger.error(f"SVD transformation failed for {matrix_name}: {e}")
                test_results[matrix_name] = {"error": str(e)}
        
        return test_results
    
    async def test_model_weight_extraction(self) -> Dict[str, Any]:
        """Test model weight extraction for different model types."""
        logger.info("Testing model weight extraction...")
        
        extractor = MockModelWeightExtractor()
        test_models = ["mock-model-small", "mock-model-large", "gpt-4", "llama-3.3-70b-versatile"]
        
        extraction_results = {}
        
        for model_id in test_models:
            try:
                weight_infos = await extractor.extract_weights(model_id)
                
                extraction_results[model_id] = {
                    "weights_extracted": len(weight_infos),
                    "layer_types": list(set(info.layer_type for info in weight_infos)),
                    "matrix_types": list(set(info.matrix_type for info in weight_infos)),
                    "total_parameters": sum(info.weight_matrix.numel() for info in weight_infos),
                    "average_matrix_size": np.mean([info.weight_matrix.numel() for info in weight_infos])
                }
                
                logger.info(f"  {model_id}: {len(weight_infos)} weights extracted, "
                           f"{extraction_results[model_id]['total_parameters']} total parameters")
                
            except Exception as e:
                logger.error(f"Weight extraction failed for {model_id}: {e}")
                extraction_results[model_id] = {"error": str(e)}
        
        return extraction_results
    
    async def test_end_to_end_optimization(self) -> Dict[str, Any]:
        """Test end-to-end model optimization with performance measurement."""
        logger.info("Testing end-to-end model optimization...")
        
        test_models = [
            ("mock-model-small", "mock"),
            ("mock-model-large", "mock"),
            ("gpt-4", "openai"),
            ("llama-3.3-70b-versatile", "groq")
        ]
        
        optimization_results = {}
        
        for model_id, model_type in test_models:
            try:
                start_time = time.time()
                
                # Apply WINA optimization
                result = await self.model_integrator.optimize_model(
                    model_identifier=model_id,
                    model_type=model_type,
                    force_recompute=True
                )
                
                optimization_time = time.time() - start_time
                
                optimization_results[model_id] = {
                    "gflops_reduction": result.gflops_reduction,
                    "accuracy_preservation": result.accuracy_preservation,
                    "constitutional_compliance": result.constitutional_compliance,
                    "layers_optimized": len(result.transformed_layers),
                    "optimization_time": optimization_time,
                    "performance_metrics": result.performance_metrics
                }
                
                logger.info(f"  {model_id}: GFLOPs reduction={result.gflops_reduction:.3f}, "
                           f"accuracy={result.accuracy_preservation:.3f}, "
                           f"time={optimization_time:.3f}s")
                
            except Exception as e:
                logger.error(f"Optimization failed for {model_id}: {e}")
                optimization_results[model_id] = {"error": str(e)}
        
        return optimization_results
    
    async def test_computational_invariance_verification(self) -> Dict[str, Any]:
        """Test computational invariance verification with policy synthesis workloads."""
        logger.info("Testing computational invariance verification...")
        
        # Create test cases representing policy synthesis workloads
        test_cases = [
            torch.randn(1, 512),    # Single policy input
            torch.randn(5, 512),    # Batch of policies
            torch.randn(10, 768),   # Larger batch
            torch.randn(3, 1024),   # High-dimensional input
        ]
        
        model_id = "mock-model-large"
        
        try:
            # First optimize the model
            await self.model_integrator.optimize_model(model_id, "mock")
            
            # Verify computational invariance
            verification_result = await self.model_integrator.verify_computational_invariance(
                model_id, test_cases, tolerance=1e-6
            )
            
            invariance_results = {
                "overall_invariance_maintained": verification_result["overall_invariance_maintained"],
                "test_cases_count": verification_result["test_inputs_count"],
                "layer_results_count": len(verification_result["layer_results"]),
                "tolerance": verification_result["tolerance"]
            }
            
            # Analyze layer-specific results
            layer_invariance_summary = {}
            for layer_name, layer_result in verification_result["layer_results"].items():
                layer_invariance_summary[layer_name] = {
                    "invariance_maintained": layer_result.get("invariance_maintained", False),
                    "relative_error": layer_result.get("relative_error", float('inf'))
                }
            
            invariance_results["layer_summary"] = layer_invariance_summary
            
            logger.info(f"  Overall invariance: {verification_result['overall_invariance_maintained']}")
            logger.info(f"  Test cases: {len(test_cases)}, Layers verified: {len(verification_result['layer_results'])}")
            
            return invariance_results
            
        except Exception as e:
            logger.error(f"Computational invariance verification failed: {e}")
            return {"error": str(e)}
    
    async def test_policy_synthesis_integration(self) -> Dict[str, Any]:
        """Test WINA integration with actual policy synthesis workloads."""
        logger.info("Testing policy synthesis integration...")
        
        # Create test policy synthesis inputs
        test_inputs = [
            LLMInterpretationInput(
                principle_id=1,
                principle_text="Ensure fairness in algorithmic decision-making",
                context="healthcare_ai",
                environmental_factors={"domain": "healthcare", "risk_level": "high"}
            ),
            LLMInterpretationInput(
                principle_id=2,
                principle_text="Protect user privacy and data confidentiality",
                context="data_processing",
                environmental_factors={"domain": "finance", "data_sensitivity": "high"}
            ),
            LLMInterpretationInput(
                principle_id=3,
                principle_text="Maintain transparency in AI system operations",
                context="automated_decision",
                environmental_factors={"domain": "legal", "explainability": "required"}
            )
        ]
        
        synthesis_results = {}
        
        for i, test_input in enumerate(test_inputs):
            try:
                # Test with WINA optimization enabled
                result_with_wina = await self.wina_client.get_structured_interpretation_optimized(
                    test_input, apply_wina=True
                )
                
                # Test with WINA optimization disabled
                result_without_wina = await self.wina_client.get_structured_interpretation_optimized(
                    test_input, apply_wina=False
                )
                
                synthesis_results[f"principle_{test_input.principle_id}"] = {
                    "with_wina": {
                        "optimization_applied": result_with_wina.optimization_applied,
                        "constitutional_compliance": result_with_wina.constitutional_compliance,
                        "synthesis_time": result_with_wina.synthesis_time,
                        "performance_metrics": result_with_wina.performance_metrics
                    },
                    "without_wina": {
                        "optimization_applied": result_without_wina.optimization_applied,
                        "constitutional_compliance": result_without_wina.constitutional_compliance,
                        "synthesis_time": result_without_wina.synthesis_time,
                        "performance_metrics": result_without_wina.performance_metrics
                    }
                }
                
                logger.info(f"  Principle {test_input.principle_id}: "
                           f"WINA time={result_with_wina.synthesis_time:.3f}s, "
                           f"baseline time={result_without_wina.synthesis_time:.3f}s")
                
            except Exception as e:
                logger.error(f"Policy synthesis failed for principle {test_input.principle_id}: {e}")
                synthesis_results[f"principle_{test_input.principle_id}"] = {"error": str(e)}
        
        return synthesis_results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive WINA SVD integration test suite."""
        logger.info("Starting comprehensive WINA SVD integration test...")
        
        start_time = time.time()
        
        # Run all test suites
        test_suites = [
            ("svd_transformation_accuracy", self.test_svd_transformation_accuracy()),
            ("model_weight_extraction", self.test_model_weight_extraction()),
            ("end_to_end_optimization", self.test_end_to_end_optimization()),
            ("computational_invariance", self.test_computational_invariance_verification()),
            ("policy_synthesis_integration", self.test_policy_synthesis_integration())
        ]
        
        results = {}
        
        for suite_name, test_coro in test_suites:
            logger.info(f"Running test suite: {suite_name}")
            try:
                suite_results = await test_coro
                results[suite_name] = suite_results
                logger.info(f"✓ {suite_name} completed successfully")
            except Exception as e:
                logger.error(f"✗ {suite_name} failed: {e}")
                results[suite_name] = {"error": str(e)}
        
        # Generate performance summary
        total_time = time.time() - start_time
        performance_summary = self.model_integrator.get_performance_summary()
        
        results["test_summary"] = {
            "total_test_time": total_time,
            "test_suites_run": len(test_suites),
            "successful_suites": len([r for r in results.values() if "error" not in r]),
            "wina_performance_summary": performance_summary
        }
        
        logger.info(f"Comprehensive test completed in {total_time:.2f}s")
        return results


async def main():
    """Main test execution function."""
    logger.info("WINA SVD Integration Test Script Starting...")
    
    try:
        # Initialize tester
        tester = WINASVDIntegrationTester()
        
        # Run comprehensive tests
        results = await tester.run_comprehensive_test()
        
        # Print summary
        print("\n" + "="*80)
        print("WINA SVD INTEGRATION TEST RESULTS")
        print("="*80)
        
        for suite_name, suite_results in results.items():
            if suite_name == "test_summary":
                continue
                
            print(f"\n{suite_name.upper()}:")
            if "error" in suite_results:
                print(f"  ✗ FAILED: {suite_results['error']}")
            else:
                print(f"  ✓ PASSED")
                if isinstance(suite_results, dict):
                    for key, value in suite_results.items():
                        if isinstance(value, dict) and "error" not in value:
                            print(f"    {key}: OK")
                        elif "error" in str(value):
                            print(f"    {key}: FAILED")
        
        # Print test summary
        summary = results.get("test_summary", {})
        print(f"\nTEST SUMMARY:")
        print(f"  Total time: {summary.get('total_test_time', 0):.2f}s")
        print(f"  Test suites: {summary.get('successful_suites', 0)}/{summary.get('test_suites_run', 0)}")
        
        # Print WINA performance summary
        wina_summary = summary.get("wina_performance_summary", {})
        if wina_summary and "message" not in wina_summary:
            print(f"  WINA optimizations: {wina_summary.get('total_optimizations', 0)}")
            print(f"  Avg GFLOPs reduction: {wina_summary.get('average_gflops_reduction', 0):.3f}")
            print(f"  Avg accuracy preservation: {wina_summary.get('average_accuracy_preservation', 0):.3f}")
            print(f"  Constitutional compliance rate: {wina_summary.get('constitutional_compliance_rate', 0):.3f}")
        
        print("\n" + "="*80)
        
        # Determine exit code
        failed_suites = len([r for r in results.values() if isinstance(r, dict) and "error" in r])
        if failed_suites == 0:
            logger.info("All tests passed successfully!")
            return 0
        else:
            logger.error(f"{failed_suites} test suite(s) failed")
            return 1
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
