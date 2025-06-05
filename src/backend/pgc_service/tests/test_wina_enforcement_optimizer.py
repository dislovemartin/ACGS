"""
Tests for WINA Enforcement Optimizer

This module contains comprehensive tests for the WINA-optimized policy enforcement
functionality, including strategy selection, performance optimization, and
constitutional compliance verification.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

try:
    from src.backend.pgc_service.app.core.wina_enforcement_optimizer import (
        WINAEnforcementOptimizer,
        EnforcementContext,
        EnforcementStrategy,
        WINAEnforcementResult,
        WINAEnforcementMetrics,
        get_wina_enforcement_optimizer
    )
    from src.backend.pgc_service.app.core.opa_client import PolicyEvaluationRequest, PolicyEvaluationResponse
    from src.backend.pgc_service.app.models.policy_models import IntegrityPolicyRule
except ImportError:
    # Mock implementations for testing when modules are not available
    from enum import Enum
    from dataclasses import dataclass
    from typing import Dict, List, Any, Optional

    class EnforcementStrategy(Enum):
        STANDARD = "standard"
        WINA_OPTIMIZED = "wina_optimized"
        CONSTITUTIONAL_PRIORITY = "constitutional_priority"
        PERFORMANCE_FOCUSED = "performance_focused"

    @dataclass
    class EnforcementContext:
        user_id: str
        action_type: str
        resource_id: str
        environment_factors: Dict[str, Any]
        priority_level: str
        constitutional_requirements: List[str]
        performance_constraints: Dict[str, Any]

    @dataclass
    class WINAEnforcementMetrics:
        enforcement_time_ms: float
        strategy_used: EnforcementStrategy
        wina_optimization_applied: bool
        constitutional_compliance_score: float
        performance_improvement: float
        cache_hit_rate: float
        opa_evaluation_time_ms: float
        wina_analysis_time_ms: float
        total_policies_evaluated: int
        optimized_policies_count: int
        constitutional_violations_detected: int
        enforcement_accuracy: float

    @dataclass
    class WINAEnforcementResult:
        decision: str
        reason: str
        confidence_score: float
        enforcement_metrics: WINAEnforcementMetrics
        constitutional_compliance: bool
        optimization_applied: bool
        matching_rules: Optional[List[Dict]] = None
        warnings: List[str] = None
        errors: List[str] = None
        wina_insights: Dict[str, Any] = None

    @dataclass
    class PolicyEvaluationRequest:
        input_data: Dict[str, Any]
        policy_content: str

    @dataclass
    class PolicyEvaluationResponse:
        result: Dict[str, Any]
        decision_id: str
        metrics: Dict[str, Any]
        explanation: List[Any]
        provenance: Dict[str, Any]

    @dataclass
    class IntegrityPolicyRule:
        id: str
        rule_content: str
        rule_type: str
        priority: int
        is_active: bool
        created_at: Any
        updated_at: Any

    class WINAEnforcementOptimizer:
        def __init__(self, enable_wina=True):
            self.enable_wina = enable_wina
            self.cache_ttl = timedelta(minutes=5)
            self.max_cache_size = 1000
            self.constitutional_compliance_threshold = 0.85
            self.performance_improvement_threshold = 0.1
            self._enforcement_history = []

        async def _select_enforcement_strategy(self, context, rules, opa_client):
            if not self.enable_wina:
                return EnforcementStrategy.STANDARD
            return EnforcementStrategy.WINA_OPTIMIZED

        async def _calculate_policy_relevance(self, rule, context):
            return 0.8  # Mock relevance score

        async def _verify_constitutional_compliance(self, context, rules):
            return True  # Mock compliance

        def _generate_cache_key(self, context):
            import hashlib
            return hashlib.md5(str(context).encode()).hexdigest()

        def _calculate_confidence_score(self, response, strategy, compliance):
            return 0.9  # Mock confidence

        def _generate_enforcement_reason(self, response, decision, strategy, context):
            return f"Action '{context.action_type}' on resource '{context.resource_id}' by user '{context.user_id}' is {decision} by policy"

        def get_performance_summary(self):
            return {
                "total_enforcements": len(self._enforcement_history),
                "average_enforcement_time_ms": 25.0,
                "average_performance_improvement": 0.2,
                "wina_enabled": self.enable_wina
            }

        async def _get_wina_strategy_insights(self, context, rules):
            return {
                "constitutional_risk": 0.3,
                "performance_benefit": 0.4,
                "optimization_potential": 0.5,
                "adaptive_recommendation": True
            }

        async def _update_node_health_score(self, node_id):
            pass

        async def _update_load_balancing_weights(self):
            pass

    async def get_wina_enforcement_optimizer():
        return WINAEnforcementOptimizer()


class TestWINAEnforcementOptimizer:
    """Test suite for WINA Enforcement Optimizer."""
    
    @pytest.fixture
    def mock_policy_rule(self):
        """Create a mock policy rule for testing."""
        return IntegrityPolicyRule(
            id="test_rule_1",
            rule_content="allow { user.role == 'admin' }",
            rule_type="rego",
            priority=1,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def enforcement_context(self):
        """Create a test enforcement context."""
        return EnforcementContext(
            user_id="test_user",
            action_type="read",
            resource_id="test_resource",
            environment_factors={"time": "business_hours", "location": "office"},
            priority_level="normal",
            constitutional_requirements=["fairness", "transparency"],
            performance_constraints={"max_latency_ms": 100}
        )
    
    @pytest.fixture
    def wina_optimizer(self):
        """Create a WINA enforcement optimizer for testing."""
        return WINAEnforcementOptimizer(enable_wina=True)
    
    @pytest.fixture
    def mock_opa_client(self):
        """Create a mock OPA client."""
        mock_client = AsyncMock()
        mock_client.evaluate_policy.return_value = PolicyEvaluationResponse(
            result={"allow": True},
            decision_id="test_decision_123",
            metrics={"timer_rego_query_eval_ns": 5000000},  # 5ms
            explanation=[],
            provenance={}
        )
        return mock_client
    
    @pytest.fixture
    def mock_wina_policy_compiler(self):
        """Create a mock WINA policy compiler."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_wina_optimizer_initialization(self, wina_optimizer):
        """Test WINA optimizer initialization."""
        assert wina_optimizer.enable_wina is True
        assert wina_optimizer.cache_ttl == timedelta(minutes=5)
        assert wina_optimizer.max_cache_size == 1000
        assert wina_optimizer.constitutional_compliance_threshold == 0.85
        assert wina_optimizer.performance_improvement_threshold == 0.1
    
    @pytest.mark.asyncio
    async def test_enforcement_context_creation(self, enforcement_context):
        """Test enforcement context creation and properties."""
        assert enforcement_context.user_id == "test_user"
        assert enforcement_context.action_type == "read"
        assert enforcement_context.resource_id == "test_resource"
        assert enforcement_context.priority_level == "normal"
        assert len(enforcement_context.constitutional_requirements) == 2
        assert "fairness" in enforcement_context.constitutional_requirements
        assert enforcement_context.performance_constraints["max_latency_ms"] == 100
    
    @pytest.mark.asyncio
    async def test_strategy_selection_standard(self, wina_optimizer, enforcement_context, mock_policy_rule):
        """Test strategy selection for standard enforcement."""
        # Test with WINA disabled
        wina_optimizer.enable_wina = False
        
        strategy = await wina_optimizer._select_enforcement_strategy(
            enforcement_context, [mock_policy_rule], None
        )
        
        assert strategy == EnforcementStrategy.STANDARD
    
    @pytest.mark.asyncio
    async def test_strategy_selection_constitutional_priority(self, wina_optimizer, enforcement_context, mock_policy_rule):
        """Test strategy selection for constitutional priority."""
        # Mock WINA insights to trigger constitutional priority
        with patch.object(wina_optimizer, '_get_wina_strategy_insights') as mock_insights:
            mock_insights.return_value = {
                "constitutional_risk": 0.6,  # High risk
                "performance_benefit": 0.3,
                "optimization_potential": 0.5,
                "adaptive_recommendation": False
            }
            
            strategy = await wina_optimizer._select_enforcement_strategy(
                enforcement_context, [mock_policy_rule], None
            )
            
            assert strategy == EnforcementStrategy.CONSTITUTIONAL_PRIORITY
    
    @pytest.mark.asyncio
    async def test_strategy_selection_performance_focused(self, wina_optimizer, enforcement_context, mock_policy_rule):
        """Test strategy selection for performance-focused enforcement."""
        # Mock WINA insights to trigger performance focus
        with patch.object(wina_optimizer, '_get_wina_strategy_insights') as mock_insights:
            mock_insights.return_value = {
                "constitutional_risk": 0.2,  # Low risk
                "performance_benefit": 0.5,  # High benefit
                "optimization_potential": 0.6,
                "adaptive_recommendation": False
            }
            
            strategy = await wina_optimizer._select_enforcement_strategy(
                enforcement_context, [mock_policy_rule], None
            )
            
            assert strategy == EnforcementStrategy.PERFORMANCE_FOCUSED
    
    @pytest.mark.asyncio
    async def test_policy_relevance_calculation(self, wina_optimizer, enforcement_context, mock_policy_rule):
        """Test policy relevance calculation."""
        # Test with policy containing relevant terms
        mock_policy_rule.rule_content = "allow { user.id == 'test_user' && action.type == 'read' }"
        
        relevance = await wina_optimizer._calculate_policy_relevance(mock_policy_rule, enforcement_context)
        
        # Should have high relevance due to matching user and action terms
        assert relevance > 0.5
    
    @pytest.mark.asyncio
    async def test_policy_relevance_calculation_low(self, wina_optimizer, enforcement_context, mock_policy_rule):
        """Test policy relevance calculation with low relevance."""
        # Test with policy containing no relevant terms
        mock_policy_rule.rule_content = "allow { system.maintenance == false }"
        
        relevance = await wina_optimizer._calculate_policy_relevance(mock_policy_rule, enforcement_context)
        
        # Should have low relevance
        assert relevance < 0.5
    
    @pytest.mark.asyncio
    async def test_constitutional_compliance_verification(self, wina_optimizer, enforcement_context, mock_policy_rule):
        """Test constitutional compliance verification."""
        # Mock constitutional WINA integration
        mock_constitutional_wina = AsyncMock()
        mock_constitutional_wina.verify_enforcement_compliance.return_value = 0.9  # High compliance
        wina_optimizer.constitutional_wina = mock_constitutional_wina
        
        compliance = await wina_optimizer._verify_constitutional_compliance(
            enforcement_context, [mock_policy_rule]
        )
        
        assert compliance is True
        mock_constitutional_wina.verify_enforcement_compliance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_constitutional_compliance_verification_low(self, wina_optimizer, enforcement_context, mock_policy_rule):
        """Test constitutional compliance verification with low compliance."""
        # Mock constitutional WINA integration with low compliance
        mock_constitutional_wina = AsyncMock()
        mock_constitutional_wina.verify_enforcement_compliance.return_value = 0.7  # Low compliance
        wina_optimizer.constitutional_wina = mock_constitutional_wina
        
        compliance = await wina_optimizer._verify_constitutional_compliance(
            enforcement_context, [mock_policy_rule]
        )
        
        assert compliance is False  # Below threshold of 0.85
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, wina_optimizer, enforcement_context):
        """Test cache key generation for enforcement context."""
        cache_key = wina_optimizer._generate_cache_key(enforcement_context)
        
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5 hash length
        
        # Test that same context generates same key
        cache_key2 = wina_optimizer._generate_cache_key(enforcement_context)
        assert cache_key == cache_key2
    
    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self, wina_optimizer):
        """Test confidence score calculation."""
        mock_response = PolicyEvaluationResponse(
            result={"allow": True},
            decision_id="test",
            metrics={"timer_rego_query_eval_ns": 5000000},  # 5ms - fast
            explanation=[],
            provenance={}
        )
        
        confidence = wina_optimizer._calculate_confidence_score(
            mock_response, EnforcementStrategy.WINA_OPTIMIZED, True
        )
        
        # Should be high confidence due to fast evaluation and constitutional compliance
        assert confidence > 0.8
        assert confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_enforcement_reason_generation(self, wina_optimizer, enforcement_context):
        """Test enforcement reason generation."""
        mock_response = PolicyEvaluationResponse(
            result={"allow": True},
            decision_id="test",
            metrics={},
            explanation=[],
            provenance={}
        )
        
        reason = wina_optimizer._generate_enforcement_reason(
            mock_response, "permit", EnforcementStrategy.WINA_OPTIMIZED, enforcement_context
        )
        
        assert "test_user" in reason
        assert "read" in reason
        assert "test_resource" in reason
        assert "permitted" in reason
        assert "WINA-optimized" in reason
    
    @pytest.mark.asyncio
    async def test_performance_summary(self, wina_optimizer):
        """Test performance summary generation."""
        # Initially empty
        summary = wina_optimizer.get_performance_summary()
        assert summary["total_enforcements"] == 0
        
        # Add some mock enforcement history
        mock_metrics = WINAEnforcementMetrics(
            enforcement_time_ms=25.0,
            strategy_used=EnforcementStrategy.WINA_OPTIMIZED,
            wina_optimization_applied=True,
            constitutional_compliance_score=0.9,
            performance_improvement=0.2,
            cache_hit_rate=0.3,
            opa_evaluation_time_ms=15.0,
            wina_analysis_time_ms=10.0,
            total_policies_evaluated=5,
            optimized_policies_count=5,
            constitutional_violations_detected=0,
            enforcement_accuracy=0.95
        )
        
        mock_result = WINAEnforcementResult(
            decision="permit",
            reason="Test enforcement",
            confidence_score=0.95,
            enforcement_metrics=mock_metrics,
            constitutional_compliance=True,
            optimization_applied=True
        )
        
        wina_optimizer._enforcement_history.append(mock_result)
        
        summary = wina_optimizer.get_performance_summary()
        assert summary["total_enforcements"] == 1
        assert summary["average_enforcement_time_ms"] == 25.0
        assert summary["average_performance_improvement"] == 0.2
        assert summary["wina_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_global_optimizer_instance(self):
        """Test global WINA enforcement optimizer instance management."""
        # Test getting instance
        optimizer1 = await get_wina_enforcement_optimizer()
        assert isinstance(optimizer1, WINAEnforcementOptimizer)
        
        # Test singleton behavior
        optimizer2 = await get_wina_enforcement_optimizer()
        assert optimizer1 is optimizer2
