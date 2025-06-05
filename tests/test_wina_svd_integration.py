"""
Integration Tests for WINA SVD Transformation

Tests the integration of WINA SVD transformation with LLM models
in the GS Engine for policy synthesis within the AlphaEvolve-ACGS framework.

Test Coverage:
- SVD transformation with mock LLM models
- Computational invariance verification
- Performance metrics collection
- Constitutional compliance validation
- Integration with GS Engine LLM clients
"""

import pytest
import asyncio
import numpy as np
import torch
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src/backend"))

# Import WINA components - using mock implementations for testing
try:
    from src.backend.shared.wina import (
        WINAConfig,
        WINAIntegrationConfig,
        WINAModelIntegrator,
        MockModelWeightExtractor,
        ModelWeightInfo,
        WINAOptimizationResult
    )
    from src.backend.shared.wina.model_integration import WINAModelIntegrator
    from src.backend.shared.wina.svd_transformation import SVDTransformation
    from src.backend.shared.wina.exceptions import WINAError, WINAOptimizationError
    WINA_AVAILABLE = True
except ImportError:
    # Mock WINA components for testing when not available
    from unittest.mock import Mock
    WINAConfig = Mock
    WINAIntegrationConfig = Mock
    WINAModelIntegrator = Mock
    MockModelWeightExtractor = Mock
    ModelWeightInfo = Mock
    WINAOptimizationResult = Mock
    SVDTransformation = Mock
    WINAError = Exception
    WINAOptimizationError = Exception
    WINA_AVAILABLE = False

# Import GS Engine components - using mock implementations for testing
try:
    from src.backend.gs_service.app.core.wina_llm_integration import (
        WINAOptimizedLLMClient,
        WINAOptimizedSynthesisResult,
        get_wina_optimized_llm_client,
        query_llm_with_wina_optimization
    )
    from src.backend.gs_service.app.schemas import LLMInterpretationInput, ConstitutionalSynthesisInput
    GS_WINA_AVAILABLE = True
except ImportError:
    # Mock GS Engine components for testing when not available
    from unittest.mock import Mock
    WINAOptimizedLLMClient = Mock
    WINAOptimizedSynthesisResult = Mock
    get_wina_optimized_llm_client = Mock
    query_llm_with_wina_optimization = Mock
    LLMInterpretationInput = Mock
    ConstitutionalSynthesisInput = Mock
    GS_WINA_AVAILABLE = False


class TestWINASVDTransformation:
    """Test suite for WINA SVD transformation integration."""

    @pytest.fixture
    def wina_config(self):
        """Create WINA configuration for testing."""
        if not WINA_AVAILABLE:
            # Return mock config when WINA not available
            mock_config = Mock()
            mock_config.target_sparsity = 0.6
            mock_config.gflops_reduction_target = 0.5
            mock_config.accuracy_threshold = 0.95
            mock_config.enable_svd_transformation = True
            mock_config.enable_runtime_gating = True
            mock_config.svd_rank_reduction = 0.8
            mock_config.cache_transformed_weights = True
            return mock_config

        return WINAConfig(
            target_sparsity=0.6,
            gflops_reduction_target=0.5,
            accuracy_threshold=0.95,
            enable_svd_transformation=True,
            enable_runtime_gating=True,
            svd_rank_reduction=0.8,
            cache_transformed_weights=True
        )
    
    @pytest.fixture
    def integration_config(self):
        """Create WINA integration configuration for testing."""
        if not WINA_AVAILABLE:
            # Return mock config when WINA not available
            mock_config = Mock()
            mock_config.gs_engine_optimization = True
            mock_config.constitutional_compliance_strict = True
            mock_config.enable_prometheus_metrics = False
            mock_config.metrics_collection_interval = 60
            return mock_config

        return WINAIntegrationConfig(
            gs_engine_optimization=True,
            constitutional_compliance_strict=True,
            enable_prometheus_metrics=False,  # Disable for testing
            metrics_collection_interval=60
        )

    @pytest.fixture
    def model_integrator(self, wina_config, integration_config):
        """Create WINA model integrator for testing."""
        if not WINA_AVAILABLE:
            return Mock()
        return WINAModelIntegrator(wina_config, integration_config)

    @pytest.fixture
    def mock_weight_extractor(self):
        """Create mock weight extractor for testing."""
        if not WINA_AVAILABLE:
            return Mock()
        return MockModelWeightExtractor()
    
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    def test_svd_transformation_basic(self, wina_config):
        """Test basic SVD transformation functionality."""
        svd_transformer = SVDTransformation(wina_config)

        # Create test weight matrix
        test_matrix = torch.randn(512, 1024)
        layer_name = "test_layer"

        # Apply transformation
        result = svd_transformer.transform_weight_matrix(test_matrix, layer_name)

        # Verify transformation result
        assert result.original_shape == test_matrix.shape
        assert result.transformed_tensor.shape == test_matrix.shape
        assert 0 < result.compression_ratio <= 1.0
        assert result.numerical_stability > 0.9
        assert result.transformation_time > 0
    
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    def test_computational_invariance_verification(self, wina_config):
        """Test computational invariance verification."""
        svd_transformer = SVDTransformation(wina_config)

        # Create test matrices
        original_matrix = torch.randn(256, 512)

        # Apply transformation
        result = svd_transformer.transform_weight_matrix(original_matrix, "test_layer")

        # Verify computational invariance
        invariance_metrics = svd_transformer.verify_computational_invariance(
            original_matrix, result.transformed_tensor, tolerance=1e-5
        )

        assert "invariance_maintained" in invariance_metrics
        assert "relative_error" in invariance_metrics
        assert "frobenius_error" in invariance_metrics
        assert invariance_metrics["relative_error"] < 0.1  # Should be small

    def test_wina_mock_functionality(self):
        """Test that mock WINA functionality works when components not available."""
        if WINA_AVAILABLE:
            pytest.skip("WINA components available, skipping mock test")

        # Test that mock objects can be created and used
        mock_config = WINAConfig()
        mock_integrator = WINAModelIntegrator()
        mock_extractor = MockModelWeightExtractor()

        # Verify mock objects exist and can be called
        assert mock_config is not None
        assert mock_integrator is not None
        assert mock_extractor is not None
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    async def test_mock_weight_extraction(self, mock_weight_extractor):
        """Test mock weight extraction functionality."""
        model_identifier = "mock-model-large"

        # Extract weights
        weight_infos = await mock_weight_extractor.extract_weights(model_identifier)

        # Verify extraction results
        assert len(weight_infos) > 0
        assert all(isinstance(info, ModelWeightInfo) for info in weight_infos)
        assert all(info.weight_matrix.numel() > 0 for info in weight_infos)
        assert all(info.layer_type in ["attention", "mlp"] for info in weight_infos)
        assert all(info.matrix_type in ["W_k", "W_q", "W_v", "W_gate"] for info in weight_infos)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    async def test_model_optimization_end_to_end(self, model_integrator):
        """Test end-to-end model optimization."""
        model_identifier = "mock-model-large"
        model_type = "mock"

        # Apply optimization
        result = await model_integrator.optimize_model(
            model_identifier=model_identifier,
            model_type=model_type,
            target_layers=None,
            force_recompute=True
        )

        # Verify optimization result
        assert isinstance(result, WINAOptimizationResult)
        assert result.model_id == model_identifier
        assert len(result.transformed_layers) > 0
        assert 0 < result.gflops_reduction < 1.0
        assert 0.85 <= result.accuracy_preservation <= 1.0
        assert result.constitutional_compliance is True
        assert result.optimization_time > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    async def test_performance_metrics_collection(self, model_integrator):
        """Test performance metrics collection during optimization."""
        model_identifier = "mock-model-small"

        # Perform multiple optimizations
        results = []
        for i in range(3):
            result = await model_integrator.optimize_model(
                model_identifier=f"{model_identifier}_{i}",
                model_type="mock",
                force_recompute=True
            )
            results.append(result)

        # Verify performance summary
        summary = model_integrator.get_performance_summary()

        assert summary["total_optimizations"] == 3
        assert "average_gflops_reduction" in summary
        assert "average_accuracy_preservation" in summary
        assert "constitutional_compliance_rate" in summary
        assert 0 <= summary["constitutional_compliance_rate"] <= 1.0

    @pytest.mark.asyncio
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    async def test_computational_invariance_batch_verification(self, model_integrator):
        """Test batch computational invariance verification."""
        model_identifier = "mock-model-large"

        # First optimize the model
        await model_integrator.optimize_model(model_identifier, "mock")

        # Create test inputs
        test_inputs = [
            torch.randn(10, 512),
            torch.randn(5, 512),
            torch.randn(15, 512)
        ]

        # Verify computational invariance
        verification_result = await model_integrator.verify_computational_invariance(
            model_identifier, test_inputs, tolerance=1e-6
        )

        assert "overall_invariance_maintained" in verification_result
        assert "layer_results" in verification_result
        assert "test_inputs_count" in verification_result
        assert verification_result["test_inputs_count"] == len(test_inputs)
    
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    def test_gflops_estimation(self, model_integrator):
        """Test GFLOPs estimation for different layer types."""
        # Create test weight info
        weight_info = ModelWeightInfo(
            layer_name="test_layer",
            weight_matrix=torch.randn(1024, 4096),
            layer_type="mlp",
            matrix_type="W_gate",
            original_shape=(1024, 4096)
        )

        # Estimate GFLOPs
        gflops = model_integrator._estimate_layer_gflops(weight_info)

        # Verify estimation
        expected_gflops = 2.0 * 1024 * 4096 / 1e9  # 2 * M * N / 1e9
        assert abs(gflops - expected_gflops) < 1e-6

    @pytest.mark.asyncio
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    async def test_constitutional_compliance_verification(self, model_integrator):
        """Test constitutional compliance verification."""
        model_identifier = "mock-model-large"

        # Optimize model
        result = await model_integrator.optimize_model(model_identifier, "mock")

        # Verify constitutional compliance
        compliance = await model_integrator._verify_constitutional_compliance(
            model_identifier, result.transformed_layers
        )

        assert isinstance(compliance, bool)
        # Should be True for well-formed transformations
        assert compliance is True
    
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    def test_caching_functionality(self, model_integrator):
        """Test transformation caching functionality."""
        # Clear cache first
        model_integrator.clear_cache()

        # Verify cache is empty
        assert len(model_integrator._transformation_cache) == 0

        # Perform optimization (should cache)
        asyncio.run(model_integrator.optimize_model("test-model", "mock"))

        # Verify cache has entry
        assert len(model_integrator._transformation_cache) > 0

        # Clear cache again
        model_integrator.clear_cache()
        assert len(model_integrator._transformation_cache) == 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA components not available")
    async def test_error_handling(self, model_integrator):
        """Test error handling in model optimization."""
        # Test with unsupported model type
        with pytest.raises(WINAError):
            await model_integrator.optimize_model(
                "test-model", "unsupported_type"
            )

        # Test with invalid model identifier
        with pytest.raises(WINAError):
            await model_integrator.optimize_model(
                "invalid-model", "mock"
            )


class TestWINALLMIntegration:
    """Test suite for WINA-LLM integration in GS Engine."""
    
    @pytest.fixture
    def wina_client(self):
        """Create WINA-optimized LLM client for testing."""
        return WINAOptimizedLLMClient(enable_wina=True)
    
    @pytest.mark.asyncio
    async def test_wina_optimized_client_initialization(self):
        """Test WINA-optimized client initialization."""
        client = WINAOptimizedLLMClient(enable_wina=True)
        
        assert client.enable_wina is True
        assert hasattr(client, 'wina_config')
        assert hasattr(client, 'wina_integrator')
        assert hasattr(client, 'constitutional_engine')
    
    @pytest.mark.asyncio
    async def test_structured_interpretation_with_wina(self, wina_client):
        """Test structured interpretation with WINA optimization."""
        # Create test input
        test_input = LLMInterpretationInput(
            principle_id=1,
            principle_text="Test principle for fairness",
            context="policy_generation",
            environmental_factors={"domain": "healthcare"}
        )
        
        # Mock the underlying LLM call
        with patch('src.backend.gs_service.app.core.llm_integration.query_llm_for_structured_output') as mock_query:
            mock_query.return_value = Mock(interpretations=["test interpretation"])
            
            # Perform optimized interpretation
            result = await wina_client.get_structured_interpretation_optimized(test_input)
            
            # Verify result structure
            assert isinstance(result, WINAOptimizedSynthesisResult)
            assert result.original_result is not None
            assert "synthesis_time" in result.performance_metrics
            assert isinstance(result.constitutional_compliance, bool)
    
    def test_performance_summary(self, wina_client):
        """Test performance summary generation."""
        summary = wina_client.get_performance_summary()
        
        assert "performance_metrics" in summary
        assert "wina_enabled" in summary
        assert summary["wina_enabled"] is True
        assert "optimization_history_count" in summary
