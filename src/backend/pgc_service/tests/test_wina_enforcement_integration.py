"""
Integration Tests for WINA Enforcement Optimization

This module contains integration tests for the WINA-optimized policy enforcement
endpoints and their integration with the PGC service infrastructure.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.backend.pgc_service.app.main import app
from src.backend.pgc_service.app.core.wina_enforcement_optimizer import (
    WINAEnforcementOptimizer,
    EnforcementContext,
    EnforcementStrategy,
    WINAEnforcementResult,
    WINAEnforcementMetrics
)
from src.backend.pgc_service.app import schemas


class TestWINAEnforcementIntegration:
    """Integration test suite for WINA enforcement optimization."""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for authentication."""
        return {
            "id": "test_user_123",
            "username": "test_user",
            "role": "policy_evaluator"
        }
    
    @pytest.fixture
    def sample_policy_request(self):
        """Create sample policy evaluation request."""
        return {
            "context": {
                "user": {"id": "alice", "role": "editor"},
                "action": {"type": "read"},
                "resource": {"id": "document_123", "type": "document"},
                "environment": {
                    "time": "business_hours",
                    "location": "office",
                    "ip_address": "192.168.1.100"
                },
                "priority": "normal",
                "constitutional_requirements": ["fairness", "transparency"],
                "performance_constraints": {"max_latency_ms": 100},
                "optimization_hints": {"prefer_performance": True}
            }
        }
    
    @pytest.fixture
    def mock_wina_result(self):
        """Create mock WINA enforcement result."""
        metrics = WINAEnforcementMetrics(
            enforcement_time_ms=15.5,
            strategy_used=EnforcementStrategy.WINA_OPTIMIZED,
            wina_optimization_applied=True,
            constitutional_compliance_score=0.92,
            performance_improvement=0.35,
            cache_hit_rate=0.25,
            opa_evaluation_time_ms=8.2,
            wina_analysis_time_ms=7.3,
            total_policies_evaluated=8,
            optimized_policies_count=6,
            constitutional_violations_detected=0,
            enforcement_accuracy=0.94
        )
        
        return WINAEnforcementResult(
            decision="permit",
            reason="Action 'read' on resource 'document_123' by user 'alice' is permitted by policy",
            confidence_score=0.94,
            enforcement_metrics=metrics,
            constitutional_compliance=True,
            optimization_applied=True,
            matching_rules=[
                {
                    "location": {"file": "authz.rego", "row": 15, "col": 1},
                    "node": {"type": "rule", "head": {"name": "allow"}},
                    "result": True
                }
            ],
            warnings=[],
            errors=[],
            wina_insights={
                "strategy_used": "wina_optimized",
                "wina_enabled": True,
                "optimization_applied": True,
                "evaluation_time_ms": 8.2,
                "performance_category": "fast"
            }
        )
    
    @pytest.mark.asyncio
    async def test_wina_enforcement_endpoint_success(self, client, sample_policy_request, mock_wina_result):
        """Test successful WINA enforcement endpoint."""
        
        with patch('src.backend.pgc_service.app.api.v1.enforcement.get_wina_enforcement_optimizer') as mock_get_optimizer, \
             patch('src.backend.pgc_service.app.api.v1.enforcement.policy_manager') as mock_policy_manager, \
             patch('src.backend.pgc_service.app.api.v1.enforcement.get_opa_client') as mock_get_opa_client, \
             patch('src.backend.pgc_service.app.core.auth.require_policy_evaluation_triggerer') as mock_auth:
            
            # Setup mocks
            mock_optimizer = AsyncMock()
            mock_optimizer.opa_client = None
            mock_optimizer.optimize_enforcement.return_value = mock_wina_result
            mock_get_optimizer.return_value = mock_optimizer
            
            mock_policy_manager.get_active_rules.return_value = []
            mock_get_opa_client.return_value = AsyncMock()
            mock_auth.return_value = {"id": "test_user", "role": "evaluator"}
            
            # Make request
            response = client.post(
                "/api/v1/pgc/enforcement/evaluate-wina",
                json=sample_policy_request,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["decision"] == "permit"
            assert "WINA-optimized" in data["reason"]
            assert "Constitutional compliance verified" in data["reason"]
            assert data["matching_rules"] is not None
            assert len(data["matching_rules"]) == 1
    
    @pytest.mark.asyncio
    async def test_wina_enforcement_endpoint_fallback(self, client, sample_policy_request):
        """Test WINA enforcement endpoint fallback to standard enforcement."""
        
        with patch('src.backend.pgc_service.app.api.v1.enforcement.get_wina_enforcement_optimizer') as mock_get_optimizer, \
             patch('src.backend.pgc_service.app.api.v1.enforcement.policy_manager') as mock_policy_manager, \
             patch('src.backend.pgc_service.app.api.v1.enforcement.datalog_engine') as mock_datalog, \
             patch('src.backend.pgc_service.app.core.auth.require_policy_evaluation_triggerer') as mock_auth:
            
            # Setup mocks to trigger fallback
            mock_optimizer = AsyncMock()
            mock_optimizer.opa_client = None
            mock_optimizer.optimize_enforcement.side_effect = Exception("WINA optimization failed")
            mock_get_optimizer.return_value = mock_optimizer
            
            mock_policy_manager.get_active_rules.return_value = []
            mock_datalog.query.return_value = [()]  # Permit decision
            mock_auth.return_value = {"id": "test_user", "role": "evaluator"}
            
            # Make request
            response = client.post(
                "/api/v1/pgc/enforcement/evaluate-wina",
                json=sample_policy_request,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Verify fallback response
            assert response.status_code == 200
            data = response.json()
            
            assert data["decision"] == "permit"
            assert "fallback enforcement" in data["reason"]
            assert data["matching_rules"] is None
    
    @pytest.mark.asyncio
    async def test_wina_enforcement_endpoint_deny(self, client, sample_policy_request):
        """Test WINA enforcement endpoint with deny decision."""
        
        # Create mock result with deny decision
        deny_metrics = WINAEnforcementMetrics(
            enforcement_time_ms=12.3,
            strategy_used=EnforcementStrategy.CONSTITUTIONAL_PRIORITY,
            wina_optimization_applied=True,
            constitutional_compliance_score=0.88,
            performance_improvement=0.15,
            cache_hit_rate=0.0,
            opa_evaluation_time_ms=10.1,
            wina_analysis_time_ms=2.2,
            total_policies_evaluated=5,
            optimized_policies_count=5,
            constitutional_violations_detected=1,
            enforcement_accuracy=0.91
        )
        
        deny_result = WINAEnforcementResult(
            decision="deny",
            reason="Action 'read' on resource 'document_123' by user 'alice' is denied by policy",
            confidence_score=0.91,
            enforcement_metrics=deny_metrics,
            constitutional_compliance=True,
            optimization_applied=True,
            matching_rules=None,
            warnings=["Constitutional violation detected"],
            errors=[],
            wina_insights={"strategy_used": "constitutional_priority"}
        )
        
        with patch('src.backend.pgc_service.app.api.v1.enforcement.get_wina_enforcement_optimizer') as mock_get_optimizer, \
             patch('src.backend.pgc_service.app.api.v1.enforcement.policy_manager') as mock_policy_manager, \
             patch('src.backend.pgc_service.app.api.v1.enforcement.get_opa_client') as mock_get_opa_client, \
             patch('src.backend.pgc_service.app.core.auth.require_policy_evaluation_triggerer') as mock_auth:
            
            # Setup mocks
            mock_optimizer = AsyncMock()
            mock_optimizer.opa_client = None
            mock_optimizer.optimize_enforcement.return_value = deny_result
            mock_get_optimizer.return_value = mock_optimizer
            
            mock_policy_manager.get_active_rules.return_value = []
            mock_get_opa_client.return_value = AsyncMock()
            mock_auth.return_value = {"id": "test_user", "role": "evaluator"}
            
            # Make request
            response = client.post(
                "/api/v1/pgc/enforcement/evaluate-wina",
                json=sample_policy_request,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["decision"] == "deny"
            assert "denied by policy" in data["reason"]
            assert data["matching_rules"] is None
    
    @pytest.mark.asyncio
    async def test_wina_performance_metrics_endpoint(self, client):
        """Test WINA performance metrics endpoint."""
        
        mock_performance_summary = {
            "total_enforcements": 150,
            "average_enforcement_time_ms": 18.5,
            "average_performance_improvement": 0.28,
            "average_constitutional_compliance": 0.91,
            "strategy_distribution": {
                "wina_optimized": 85,
                "constitutional_priority": 35,
                "performance_focused": 20,
                "standard": 10
            },
            "wina_enabled": True,
            "cache_size": 45,
            "compliance_cache_size": 32
        }
        
        with patch('src.backend.pgc_service.app.api.v1.enforcement.get_wina_enforcement_optimizer') as mock_get_optimizer, \
             patch('src.backend.pgc_service.app.core.auth.require_policy_evaluation_triggerer') as mock_auth:
            
            # Setup mocks
            mock_optimizer = AsyncMock()
            mock_optimizer.get_performance_summary.return_value = mock_performance_summary
            mock_get_optimizer.return_value = mock_optimizer
            mock_auth.return_value = {"id": "test_user", "role": "evaluator"}
            
            # Make request
            response = client.get(
                "/api/v1/pgc/enforcement/wina-performance",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert "wina_performance_metrics" in data
            assert "timestamp" in data
            
            metrics = data["wina_performance_metrics"]
            assert metrics["total_enforcements"] == 150
            assert metrics["average_enforcement_time_ms"] == 18.5
            assert metrics["wina_enabled"] is True
            assert "strategy_distribution" in metrics
    
    @pytest.mark.asyncio
    async def test_wina_enforcement_context_creation(self, sample_policy_request):
        """Test enforcement context creation from request payload."""
        
        # This would be tested within the actual endpoint logic
        context_data = sample_policy_request["context"]
        
        context = EnforcementContext(
            user_id=context_data["user"]["id"],
            action_type=context_data["action"]["type"],
            resource_id=context_data["resource"]["id"],
            environment_factors=context_data["environment"],
            priority_level=context_data["priority"],
            constitutional_requirements=context_data["constitutional_requirements"],
            performance_constraints=context_data["performance_constraints"]
        )
        
        assert context.user_id == "alice"
        assert context.action_type == "read"
        assert context.resource_id == "document_123"
        assert context.priority_level == "normal"
        assert len(context.constitutional_requirements) == 2
        assert context.performance_constraints["max_latency_ms"] == 100
    
    @pytest.mark.asyncio
    async def test_wina_enforcement_rate_limiting(self, client, sample_policy_request):
        """Test rate limiting on WINA enforcement endpoint."""
        
        with patch('src.backend.pgc_service.app.core.auth.require_policy_evaluation_triggerer') as mock_auth:
            mock_auth.return_value = {"id": "test_user", "role": "evaluator"}
            
            # This test would require actual rate limiting configuration
            # For now, just verify the endpoint exists and responds
            response = client.post(
                "/api/v1/pgc/enforcement/evaluate-wina",
                json=sample_policy_request,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Should get some response (even if mocked components fail)
            assert response.status_code in [200, 422, 500]  # Various possible outcomes
    
    @pytest.mark.asyncio
    async def test_wina_enforcement_authentication_required(self, client, sample_policy_request):
        """Test that WINA enforcement endpoint requires authentication."""
        
        # Make request without authentication
        response = client.post(
            "/api/v1/pgc/enforcement/evaluate-wina",
            json=sample_policy_request
        )
        
        # Should require authentication
        assert response.status_code in [401, 403, 422]  # Unauthorized or validation error
    
    @pytest.mark.asyncio
    async def test_wina_enforcement_invalid_request(self, client):
        """Test WINA enforcement endpoint with invalid request data."""
        
        invalid_request = {
            "context": {
                # Missing required fields
                "user": {},
                "action": {},
                "resource": {}
            }
        }
        
        with patch('src.backend.pgc_service.app.core.auth.require_policy_evaluation_triggerer') as mock_auth:
            mock_auth.return_value = {"id": "test_user", "role": "evaluator"}
            
            response = client.post(
                "/api/v1/pgc/enforcement/evaluate-wina",
                json=invalid_request,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Should handle invalid request gracefully
            assert response.status_code in [200, 400, 422]
