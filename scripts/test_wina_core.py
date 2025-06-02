#!/usr/bin/env python3
"""
WINA Core Functionality Test

Simple test script to validate the core WINA SVD transformation
functionality without complex dependencies.
"""

import sys
import asyncio
import logging
from pathlib import Path
import torch
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_wina_imports():
    """Test WINA module imports."""
    try:
        from src.backend.shared.wina import (
            WINAConfig,
            WINAIntegrationConfig,
            SVDTransformation,
            WINAModelIntegrator,
            MockModelWeightExtractor
        )
        logger.info("✓ WINA imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ WINA imports failed: {e}")
        return False

def test_svd_transformation():
    """Test SVD transformation functionality."""
    try:
        from src.backend.shared.wina import WINAConfig, SVDTransformation
        
        # Create configuration
        config = WINAConfig(
            target_sparsity=0.6,
            svd_rank_reduction=0.8,
            enable_svd_transformation=True
        )
        
        # Create SVD transformer
        transformer = SVDTransformation(config)
        
        # Test with different matrix sizes
        test_matrices = [
            ("small", torch.randn(256, 512)),
            ("medium", torch.randn(1024, 2048)),
            ("attention", torch.randn(768, 768)),
            ("mlp_gate", torch.randn(768, 3072))
        ]
        
        results = {}
        for name, matrix in test_matrices:
            result = transformer.transform_weight_matrix(matrix, f"test_{name}")
            
            # Verify computational invariance
            invariance = transformer.verify_computational_invariance(
                matrix, result.transformed_tensor, tolerance=1e-6
            )
            
            results[name] = {
                "compression_ratio": result.compression_ratio,
                "numerical_stability": result.numerical_stability,
                "invariance_maintained": invariance["invariance_maintained"],
                "relative_error": invariance["relative_error"]
            }
            
            logger.info(f"  {name}: compression={result.compression_ratio:.3f}, "
                       f"stability={result.numerical_stability:.3f}, "
                       f"invariance={invariance['invariance_maintained']}")
        
        # Verify all transformations are successful
        all_successful = all(
            r["compression_ratio"] > 0 and r["numerical_stability"] > 0.9
            for r in results.values()
        )
        
        if all_successful:
            logger.info("✓ SVD transformation tests passed")
            return True
        else:
            logger.error("✗ SVD transformation tests failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ SVD transformation test failed: {e}")
        return False

async def test_model_weight_extraction():
    """Test model weight extraction."""
    try:
        from src.backend.shared.wina import MockModelWeightExtractor
        
        extractor = MockModelWeightExtractor()
        
        # Test different model types
        test_models = ["mock-model-small", "mock-model-large", "gpt-4"]
        
        for model_id in test_models:
            weight_infos = await extractor.extract_weights(model_id)
            
            if len(weight_infos) == 0:
                logger.error(f"✗ No weights extracted for {model_id}")
                return False
            
            # Verify weight info structure
            for info in weight_infos:
                if info.weight_matrix.numel() == 0:
                    logger.error(f"✗ Empty weight matrix for {info.layer_name}")
                    return False
                
                if info.layer_type not in ["attention", "mlp"]:
                    logger.error(f"✗ Invalid layer type: {info.layer_type}")
                    return False
            
            logger.info(f"  {model_id}: {len(weight_infos)} weights extracted")
        
        logger.info("✓ Model weight extraction tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Model weight extraction test failed: {e}")
        return False

async def test_model_integration():
    """Test model integration functionality."""
    try:
        from src.backend.shared.wina import (
            WINAConfig, 
            WINAIntegrationConfig, 
            WINAModelIntegrator
        )
        
        # Create configurations
        config = WINAConfig(
            target_sparsity=0.6,
            gflops_reduction_target=0.5,
            accuracy_threshold=0.95,
            enable_svd_transformation=True
        )
        
        integration_config = WINAIntegrationConfig(
            gs_engine_optimization=True,
            constitutional_compliance_strict=True
        )
        
        # Create integrator
        integrator = WINAModelIntegrator(config, integration_config)
        
        # Test optimization
        result = await integrator.optimize_model(
            model_identifier="mock-model-large",
            model_type="mock",
            force_recompute=True
        )
        
        # Verify optimization result
        if result.gflops_reduction <= 0:
            logger.error("✗ No GFLOPs reduction achieved")
            return False
        
        if result.accuracy_preservation < 0.85:
            logger.error(f"✗ Low accuracy preservation: {result.accuracy_preservation}")
            return False
        
        if not result.constitutional_compliance:
            logger.error("✗ Constitutional compliance failed")
            return False
        
        logger.info(f"  GFLOPs reduction: {result.gflops_reduction:.3f}")
        logger.info(f"  Accuracy preservation: {result.accuracy_preservation:.3f}")
        logger.info(f"  Layers optimized: {len(result.transformed_layers)}")
        logger.info(f"  Optimization time: {result.optimization_time:.3f}s")
        
        logger.info("✓ Model integration tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Model integration test failed: {e}")
        return False

async def test_computational_invariance():
    """Test computational invariance verification."""
    try:
        from src.backend.shared.wina import (
            WINAConfig, 
            WINAIntegrationConfig, 
            WINAModelIntegrator
        )
        
        # Create integrator
        config = WINAConfig(enable_svd_transformation=True)
        integration_config = WINAIntegrationConfig()
        integrator = WINAModelIntegrator(config, integration_config)
        
        # Optimize model first
        await integrator.optimize_model("mock-model-large", "mock")
        
        # Create test cases
        test_cases = [
            torch.randn(1, 512),
            torch.randn(5, 768),
            torch.randn(10, 1024)
        ]
        
        # Verify computational invariance
        verification_result = await integrator.verify_computational_invariance(
            "mock-model-large", test_cases, tolerance=1e-6
        )
        
        if not verification_result.get("overall_invariance_maintained", False):
            logger.error("✗ Computational invariance not maintained")
            return False
        
        logger.info(f"  Test cases: {verification_result['test_inputs_count']}")
        logger.info(f"  Layers verified: {len(verification_result['layer_results'])}")
        logger.info(f"  Overall invariance: {verification_result['overall_invariance_maintained']}")
        
        logger.info("✓ Computational invariance tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Computational invariance test failed: {e}")
        return False

async def main():
    """Run all WINA core tests."""
    logger.info("Starting WINA Core Functionality Tests...")
    
    tests = [
        ("WINA Imports", test_wina_imports),
        ("SVD Transformation", test_svd_transformation),
        ("Model Weight Extraction", test_model_weight_extraction),
        ("Model Integration", test_model_integration),
        ("Computational Invariance", test_computational_invariance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"✗ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "="*60)
    print("WINA CORE FUNCTIONALITY TEST RESULTS")
    print("="*60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nSummary: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All WINA core tests passed successfully!")
        return 0
    else:
        logger.error(f"{total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
