"""
Integration tests for OPA Integration

Tests the actual OPA integration functionality including server connectivity,
policy evaluation, and performance requirements.

Phase 2: Governance Synthesis Hardening with Rego/OPA Integration
"""

import pytest
import asyncio
import time
import json
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any

from src.backend.gs_service.app.core.opa_integration import (
    OPAClient,
    PolicyDecisionRequest,
    PolicyDecisionResponse,
    PolicyValidationResult,
    BatchPolicyDecision,
    OPAIntegrationError,
    get_opa_client,
    close_opa_client
)
from src.backend.gs_service.app.config.opa_config import OPAMode, get_opa_config


@pytest.fixture
def mock_opa_config():
    """Mock OPA configuration for testing."""
    config = MagicMock()
    config.mode = OPAMode.EMBEDDED
    config.performance.max_policy_decision_latency_ms = 50
    config.performance.enable_decision_caching = True
    config.performance.cache_ttl_seconds = 300
    config.performance.cache_max_size = 1000
    config.performance.enable_batch_evaluation = True
    config.performance.batch_size = 100
    config.performance.enable_parallel_evaluation = True
    config.performance.max_parallel_workers = 4
    config.server.host = "localhost"
    config.server.port = 8181
    config.server.timeout_seconds = 5
    config.server.max_retries = 3
    config.server.health_check_interval_seconds = 30
    config.server.base_url = "http://localhost:8181"
    config.server.health_url = "http://localhost:8181/health"
    return config


@pytest.fixture
def opa_client(mock_opa_config):
    """OPA client with mocked configuration."""
    with patch('src.backend.gs_service.app.core.opa_integration.get_opa_config', return_value=mock_opa_config):
        client = OPAClient()
        return client


@pytest.fixture
def sample_policy_decision_request():
    """Sample policy decision request."""
    return PolicyDecisionRequest(
        input_data={
            "policy_content": "package test\ndefault allow := true",
            "policy_type": "governance_rule",
            "constitutional_principles": [
                {"description": "Ensure fairness", "type": "fairness"}
            ],
            "context": {"target_system": "acgs", "governance_type": "operational"}
        },
        policy_path="acgs/constitutional/compliance_report",
        explain=True
    )


class TestOPAClientInitialization:
    """Test cases for OPA client initialization."""
    
    @pytest.mark.asyncio
    async def test_embedded_mode_initialization(self, mock_opa_config):
        """Test OPA client initialization in embedded mode."""
        mock_opa_config.mode = OPAMode.EMBEDDED
        
        with patch('src.backend.gs_service.app.core.opa_integration.get_opa_config', return_value=mock_opa_config):
            with patch('src.backend.gs_service.app.core.opa_integration.OPA_CLIENT_AVAILABLE', True):
                with patch('src.backend.gs_service.app.core.opa_integration.OPA') as mock_opa:
                    mock_opa.return_value = MagicMock()
                    
                    client = OPAClient()
                    await client.initialize()
                    
                    assert client._initialized
                    assert client.opa_client is not None
                    mock_opa.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_server_mode_initialization(self, mock_opa_config):
        """Test OPA client initialization in server mode."""
        mock_opa_config.mode = OPAMode.SERVER
        
        with patch('src.backend.gs_service.app.core.opa_integration.get_opa_config', return_value=mock_opa_config):
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session_instance = AsyncMock()
                mock_session.return_value = mock_session_instance
                
                # Mock health check response
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_session_instance.get.return_value.__aenter__.return_value = mock_response
                
                client = OPAClient()
                await client.initialize()
                
                assert client._initialized
                assert client.session is not None
                mock_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hybrid_mode_initialization(self, mock_opa_config):
        """Test OPA client initialization in hybrid mode."""
        mock_opa_config.mode = OPAMode.HYBRID
        
        with patch('src.backend.gs_service.app.core.opa_integration.get_opa_config', return_value=mock_opa_config):
            with patch('src.backend.gs_service.app.core.opa_integration.OPA_CLIENT_AVAILABLE', True):
                with patch('src.backend.gs_service.app.core.opa_integration.OPA') as mock_opa:
                    with patch('aiohttp.ClientSession') as mock_session:
                        mock_opa.return_value = MagicMock()
                        mock_session_instance = AsyncMock()
                        mock_session.return_value = mock_session_instance
                        
                        # Mock health check response
                        mock_response = AsyncMock()
                        mock_response.status = 200
                        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
                        
                        client = OPAClient()
                        await client.initialize()
                        
                        assert client._initialized
                        assert client.opa_client is not None
                        assert client.session is not None
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, mock_opa_config):
        """Test OPA client initialization failure handling."""
        mock_opa_config.mode = OPAMode.EMBEDDED
        
        with patch('src.backend.gs_service.app.core.opa_integration.get_opa_config', return_value=mock_opa_config):
            with patch('src.backend.gs_service.app.core.opa_integration.OPA_CLIENT_AVAILABLE', False):
                client = OPAClient()
                
                with pytest.raises(OPAIntegrationError):
                    await client.initialize()
                
                assert not client._initialized


class TestPolicyEvaluation:
    """Test cases for policy evaluation."""
    
    @pytest.mark.asyncio
    async def test_evaluate_policy_embedded_mode(self, opa_client, sample_policy_decision_request):
        """Test policy evaluation in embedded mode."""
        opa_client.config.mode = OPAMode.EMBEDDED
        opa_client.opa_client = MagicMock()
        opa_client._initialized = True
        
        response = await opa_client.evaluate_policy(sample_policy_decision_request)
        
        assert isinstance(response, PolicyDecisionResponse)
        assert response.decision_id is not None
        assert response.decision_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_evaluate_policy_server_mode(self, opa_client, sample_policy_decision_request):
        """Test policy evaluation in server mode."""
        opa_client.config.mode = OPAMode.SERVER
        opa_client._initialized = True
        
        # Mock HTTP session
        mock_session = AsyncMock()
        opa_client.session = mock_session
        
        # Mock server response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "result": {"allowed": True, "compliance_score": 0.9},
            "explanation": {"trace": []},
            "metrics": {"timer_rego_query_eval_ns": 1000000}
        }
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        response = await opa_client.evaluate_policy(sample_policy_decision_request)
        
        assert isinstance(response, PolicyDecisionResponse)
        assert response.result["allowed"] is True
        assert response.result["compliance_score"] == 0.9
        assert response.explanation is not None
        assert response.metrics is not None
    
    @pytest.mark.asyncio
    async def test_evaluate_policy_server_error(self, opa_client, sample_policy_decision_request):
        """Test policy evaluation server error handling."""
        opa_client.config.mode = OPAMode.SERVER
        opa_client._initialized = True
        
        # Mock HTTP session with error response
        mock_session = AsyncMock()
        opa_client.session = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal server error"
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(OPAIntegrationError):
            await opa_client.evaluate_policy(sample_policy_decision_request)
    
    @pytest.mark.asyncio
    async def test_evaluate_policy_with_caching(self, opa_client, sample_policy_decision_request):
        """Test policy evaluation with caching enabled."""
        opa_client.config.mode = OPAMode.EMBEDDED
        opa_client.config.performance.enable_decision_caching = True
        opa_client.opa_client = MagicMock()
        opa_client._initialized = True
        
        # First evaluation
        response1 = await opa_client.evaluate_policy(sample_policy_decision_request)
        
        # Second evaluation (should hit cache)
        response2 = await opa_client.evaluate_policy(sample_policy_decision_request)
        
        assert response1.decision_id != response2.decision_id  # Different decision IDs
        assert opa_client.metrics["cache_hits"] > 0


class TestPolicyValidation:
    """Test cases for policy validation."""
    
    @pytest.mark.asyncio
    async def test_validate_policy_success(self, opa_client):
        """Test successful policy validation."""
        opa_client._initialized = True
        
        policy_content = """
        package acgs.test
        
        default allow := false
        
        allow if {
            input.user.role == "admin"
        }
        """
        
        result = await opa_client.validate_policy(policy_content, "test_policy")
        
        assert isinstance(result, PolicyValidationResult)
        assert result.policy_path == "test_policy"
        assert result.validation_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_validate_policy_syntax_error(self, opa_client):
        """Test policy validation with syntax errors."""
        opa_client._initialized = True
        
        # Invalid policy content
        policy_content = "invalid rego syntax"
        
        result = await opa_client.validate_policy(policy_content, "invalid_policy")
        
        assert isinstance(result, PolicyValidationResult)
        assert not result.is_valid
        assert len(result.syntax_errors) > 0
    
    @pytest.mark.asyncio
    async def test_validate_empty_policy(self, opa_client):
        """Test validation of empty policy."""
        opa_client._initialized = True
        
        result = await opa_client.validate_policy("", "empty_policy")
        
        assert not result.is_valid
        assert "empty" in result.syntax_errors[0].lower()


class TestBatchEvaluation:
    """Test cases for batch policy evaluation."""
    
    @pytest.mark.asyncio
    async def test_batch_evaluate_parallel(self, opa_client):
        """Test batch evaluation with parallel execution."""
        opa_client.config.performance.enable_parallel_evaluation = True
        opa_client.config.performance.max_parallel_workers = 2
        opa_client._initialized = True
        opa_client.opa_client = MagicMock()
        
        # Create batch request
        requests = [
            PolicyDecisionRequest(
                input_data={"test": f"data_{i}"},
                policy_path="test/policy"
            )
            for i in range(5)
        ]
        
        batch = BatchPolicyDecision(
            decisions=requests,
            batch_id="test_batch",
            parallel_execution=True
        )
        
        responses = await opa_client.batch_evaluate(batch)
        
        assert len(responses) == 5
        for response in responses:
            assert isinstance(response, PolicyDecisionResponse)
    
    @pytest.mark.asyncio
    async def test_batch_evaluate_sequential(self, opa_client):
        """Test batch evaluation with sequential execution."""
        opa_client.config.performance.enable_parallel_evaluation = False
        opa_client._initialized = True
        opa_client.opa_client = MagicMock()
        
        # Create batch request
        requests = [
            PolicyDecisionRequest(
                input_data={"test": f"data_{i}"},
                policy_path="test/policy"
            )
            for i in range(3)
        ]
        
        batch = BatchPolicyDecision(
            decisions=requests,
            batch_id="test_batch",
            parallel_execution=False
        )
        
        responses = await opa_client.batch_evaluate(batch)
        
        assert len(responses) == 3
        for response in responses:
            assert isinstance(response, PolicyDecisionResponse)
    
    @pytest.mark.asyncio
    async def test_batch_evaluate_empty(self, opa_client):
        """Test batch evaluation with empty request list."""
        opa_client._initialized = True
        
        batch = BatchPolicyDecision(
            decisions=[],
            batch_id="empty_batch"
        )
        
        responses = await opa_client.batch_evaluate(batch)
        
        assert len(responses) == 0


class TestPerformanceMetrics:
    """Test cases for performance metrics tracking."""
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, opa_client, sample_policy_decision_request):
        """Test performance metrics tracking."""
        opa_client._initialized = True
        opa_client.opa_client = MagicMock()
        
        initial_metrics = opa_client.get_metrics()
        initial_count = initial_metrics["total_decisions"]
        
        await opa_client.evaluate_policy(sample_policy_decision_request)
        
        updated_metrics = opa_client.get_metrics()
        assert updated_metrics["total_decisions"] == initial_count + 1
        assert updated_metrics["average_latency_ms"] >= 0
        assert updated_metrics["max_latency_ms"] >= 0
    
    @pytest.mark.asyncio
    async def test_latency_threshold_tracking(self, opa_client, sample_policy_decision_request):
        """Test latency threshold tracking."""
        opa_client._initialized = True
        opa_client.opa_client = MagicMock()
        
        # Mock slow evaluation
        async def slow_evaluate(*args, **kwargs):
            await asyncio.sleep(0.06)  # 60ms delay
            return PolicyDecisionResponse(
                result={"allowed": True},
                decision_id="slow_decision",
                decision_time_ms=60.0
            )
        
        with patch.object(opa_client, '_evaluate_policy_internal', side_effect=slow_evaluate):
            response = await opa_client.evaluate_policy(sample_policy_decision_request)
            
            assert response.decision_time_ms > opa_client.config.performance.max_policy_decision_latency_ms
            
            metrics = opa_client.get_metrics()
            assert metrics["max_latency_ms"] > 50


class TestHealthChecking:
    """Test cases for OPA server health checking."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, opa_client):
        """Test successful health check."""
        # Mock HTTP session
        mock_session = AsyncMock()
        opa_client.session = mock_session
        
        # Mock successful health check response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await opa_client._check_server_health()
        
        assert result is True
        assert opa_client.metrics["last_health_check"] is not None
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, opa_client):
        """Test failed health check."""
        # Mock HTTP session
        mock_session = AsyncMock()
        opa_client.session = mock_session
        
        # Mock failed health check response
        mock_response = AsyncMock()
        mock_response.status = 503
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await opa_client._check_server_health()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, opa_client):
        """Test health check with connection exception."""
        # Mock HTTP session
        mock_session = AsyncMock()
        opa_client.session = mock_session
        
        # Mock connection exception
        mock_session.get.side_effect = Exception("Connection refused")
        
        result = await opa_client._check_server_health()
        
        assert result is False


class TestResourceCleanup:
    """Test cases for resource cleanup."""
    
    @pytest.mark.asyncio
    async def test_client_close(self, opa_client):
        """Test OPA client resource cleanup."""
        # Mock session and health check task
        mock_session = AsyncMock()
        opa_client.session = mock_session
        opa_client._health_check_task = AsyncMock()
        opa_client._initialized = True
        
        await opa_client.close()
        
        assert not opa_client._initialized
        mock_session.close.assert_called_once()
        opa_client._health_check_task.cancel.assert_called_once()


class TestGlobalOPAClient:
    """Test cases for global OPA client instance."""
    
    @pytest.mark.asyncio
    async def test_get_opa_client_singleton(self):
        """Test that get_opa_client returns singleton instance."""
        with patch('src.backend.gs_service.app.core.opa_integration.OPAClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.initialize = AsyncMock()
            mock_client_class.return_value = mock_client
            
            client1 = await get_opa_client()
            client2 = await get_opa_client()
            
            assert client1 is client2
            mock_client.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_opa_client(self):
        """Test global OPA client cleanup."""
        with patch('src.backend.gs_service.app.core.opa_integration.OPAClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.initialize = AsyncMock()
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Get client instance
            await get_opa_client()
            
            # Close client
            await close_opa_client()
            
            mock_client.close.assert_called_once()


@pytest.mark.performance
class TestOPAIntegrationPerformance:
    """Performance tests for OPA integration."""
    
    @pytest.mark.asyncio
    async def test_policy_evaluation_latency(self, opa_client, sample_policy_decision_request):
        """Test that policy evaluation meets latency requirements."""
        opa_client._initialized = True
        opa_client.opa_client = MagicMock()
        
        start_time = time.time()
        response = await opa_client.evaluate_policy(sample_policy_decision_request)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        # Should meet the 50ms latency requirement
        assert latency_ms < 50
        assert response.decision_time_ms < 50
    
    @pytest.mark.asyncio
    async def test_batch_evaluation_scaling(self, opa_client):
        """Test batch evaluation performance scaling."""
        opa_client._initialized = True
        opa_client.opa_client = MagicMock()
        opa_client.config.performance.enable_parallel_evaluation = True
        
        # Create large batch
        requests = [
            PolicyDecisionRequest(
                input_data={"test": f"data_{i}"},
                policy_path="test/policy"
            )
            for i in range(50)
        ]
        
        batch = BatchPolicyDecision(
            decisions=requests,
            batch_id="performance_test",
            parallel_execution=True
        )
        
        start_time = time.time()
        responses = await opa_client.batch_evaluate(batch)
        end_time = time.time()
        
        batch_latency_ms = (end_time - start_time) * 1000
        avg_latency_per_request = batch_latency_ms / len(requests)
        
        assert len(responses) == 50
        assert avg_latency_per_request < 10  # Should be very fast with parallel processing
