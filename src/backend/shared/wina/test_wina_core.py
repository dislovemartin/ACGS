"""
Test script for WINA core functionality.

This script tests the basic functionality of the WINA (Weight Informed Neuron Activation)
core library to ensure proper setup and integration.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the shared directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from wina import (
        WINACore, WINAOptimizer, WINAConfig, WINAIntegrationConfig,
        SVDTransformation, RuntimeGating, WINAMetrics,
        ConstitutionalWINASupport
    )
    from wina.exceptions import WINAError, WINAConfigurationError
except ImportError as e:
    print(f"Failed to import WINA modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_wina_configuration():
    """Test WINA configuration setup."""
    logger.info("Testing WINA configuration...")
    
    try:
        # Test basic configuration
        config = WINAConfig(
            target_sparsity=0.6,
            gflops_reduction_target=0.5,
            accuracy_threshold=0.95
        )
        
        assert config.target_sparsity == 0.6
        assert config.gflops_reduction_target == 0.5
        assert config.accuracy_threshold == 0.95
        
        logger.info("✓ Basic WINA configuration test passed")
        
        # Test integration configuration
        integration_config = WINAIntegrationConfig(
            gs_engine_optimization=True,
            ec_layer_oversight=True,
            pgc_enforcement_enhancement=True
        )
        
        assert integration_config.gs_engine_optimization is True
        assert integration_config.ec_layer_oversight is True
        
        logger.info("✓ WINA integration configuration test passed")
        
        # Test invalid configuration
        try:
            invalid_config = WINAConfig(target_sparsity=1.5)  # Invalid value
            assert False, "Should have raised WINAConfigurationError"
        except WINAConfigurationError:
            logger.info("✓ Configuration validation test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ WINA configuration test failed: {e}")
        return False


async def test_wina_core():
    """Test WINA core functionality."""
    logger.info("Testing WINA core functionality...")
    
    try:
        # Create configuration
        config = WINAConfig(
            target_sparsity=0.5,
            gflops_reduction_target=0.4,
            accuracy_threshold=0.95
        )
        
        integration_config = WINAIntegrationConfig()
        
        # Initialize WINA core
        wina_core = WINACore(config, integration_config)
        
        assert wina_core.config.target_sparsity == 0.5
        assert wina_core.integration_config is not None
        
        logger.info("✓ WINA core initialization test passed")
        
        # Test metrics initialization
        assert wina_core.metrics is not None
        assert wina_core.gflops_tracker is not None
        
        logger.info("✓ WINA core components test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ WINA core test failed: {e}")
        return False


async def test_svd_transformation():
    """Test SVD transformation functionality."""
    logger.info("Testing SVD transformation...")
    
    try:
        import torch
        
        config = WINAConfig(svd_rank_reduction=0.8)
        svd_transformer = SVDTransformation(config)
        
        # Create test weight matrix
        test_matrix = torch.randn(100, 100)
        
        # Apply transformation
        result = svd_transformer.transform_weight_matrix(test_matrix, "test_layer")
        
        assert result.original_shape == test_matrix.shape
        assert result.transformed_tensor is not None
        assert result.compression_ratio <= 1.0
        
        logger.info("✓ SVD transformation test passed")
        
        # Test computational invariance verification
        invariance_metrics = svd_transformer.verify_computational_invariance(
            test_matrix, result.transformed_tensor
        )
        
        assert "relative_error" in invariance_metrics
        assert "invariance_maintained" in invariance_metrics
        
        logger.info("✓ Computational invariance test passed")
        
        return True
        
    except ImportError:
        logger.warning("PyTorch not available, skipping SVD transformation test")
        return True
    except Exception as e:
        logger.error(f"✗ SVD transformation test failed: {e}")
        return False


async def test_runtime_gating():
    """Test runtime gating functionality."""
    logger.info("Testing runtime gating...")
    
    try:
        import numpy as np
        
        config = WINAConfig(target_sparsity=0.6, gating_threshold=0.1)
        runtime_gating = RuntimeGating(config)
        
        # Initialize gates for a test layer
        runtime_gating.initialize_layer_gates("test_layer", 100)
        
        assert "test_layer" in runtime_gating.gates
        assert len(runtime_gating.gates["test_layer"]) == 100
        
        logger.info("✓ Runtime gating initialization test passed")
        
        # Test gating decision
        test_scores = np.random.rand(100)
        decision = runtime_gating.make_gating_decision("test_layer", test_scores)
        
        assert decision.layer_name == "test_layer"
        assert len(decision.active_neurons) > 0
        assert decision.sparsity_achieved >= 0.0
        
        logger.info("✓ Runtime gating decision test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Runtime gating test failed: {e}")
        return False


async def test_constitutional_integration():
    """Test constitutional integration functionality."""
    logger.info("Testing constitutional integration...")
    
    try:
        config = WINAConfig()
        integration_config = WINAIntegrationConfig()
        
        constitutional_support = ConstitutionalWINASupport(config, integration_config)
        
        # Initialize efficiency principles
        await constitutional_support.initialize_efficiency_principles()
        
        principles = constitutional_support.get_efficiency_principles()
        assert len(principles) > 0
        assert "EFF001" in principles
        
        logger.info("✓ Constitutional integration initialization test passed")
        
        # Test compliance evaluation
        optimization_context = {
            "accuracy_retention": 0.96,
            "gflops_reduction": 0.4,
            "optimization_technique": "WINA"
        }
        
        compliance_results = await constitutional_support.evaluate_wina_compliance(optimization_context)
        
        assert "overall_compliant" in compliance_results
        assert "principle_evaluations" in compliance_results
        
        logger.info("✓ Constitutional compliance evaluation test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Constitutional integration test failed: {e}")
        return False


async def test_wina_optimizer():
    """Test WINA optimizer functionality."""
    logger.info("Testing WINA optimizer...")
    
    try:
        config = WINAConfig()
        integration_config = WINAIntegrationConfig()
        
        optimizer = WINAOptimizer(config, integration_config)
        
        assert optimizer.config is not None
        assert optimizer.integration_config is not None
        assert optimizer.wina_core is not None
        
        logger.info("✓ WINA optimizer initialization test passed")
        
        # Test metrics retrieval
        metrics = await optimizer.get_optimization_metrics()
        assert isinstance(metrics, dict)
        
        logger.info("✓ WINA optimizer metrics test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ WINA optimizer test failed: {e}")
        return False


async def test_environment_configuration():
    """Test environment configuration loading."""
    logger.info("Testing environment configuration...")
    
    try:
        # Set test environment variables
        os.environ["WINA_TARGET_SPARSITY"] = "0.7"
        os.environ["WINA_GFLOPS_REDUCTION_TARGET"] = "0.6"
        os.environ["WINA_ACCURACY_THRESHOLD"] = "0.98"
        
        from wina.config import load_wina_config_from_env
        
        wina_config, integration_config = load_wina_config_from_env()
        
        assert wina_config.target_sparsity == 0.7
        assert wina_config.gflops_reduction_target == 0.6
        assert wina_config.accuracy_threshold == 0.98
        
        logger.info("✓ Environment configuration test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Environment configuration test failed: {e}")
        return False


async def run_all_tests():
    """Run all WINA tests."""
    logger.info("Starting WINA core library tests...")
    
    tests = [
        test_wina_configuration,
        test_wina_core,
        test_svd_transformation,
        test_runtime_gating,
        test_constitutional_integration,
        test_wina_optimizer,
        test_environment_configuration
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\nWINA Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All WINA core library tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
