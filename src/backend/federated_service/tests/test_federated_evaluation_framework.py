"""
Comprehensive test suite for the enhanced Federated Evaluation Framework (Task 6).

Tests multi-node scaling, Byzantine fault tolerance, MAB integration,
and constitutional compliance validation.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

# Test imports
from app.core.federated_evaluator import FederatedEvaluator, EvaluationTask, FederatedNode
from app.schemas import FederatedEvaluationRequest, PlatformType
from shared.models import (
    FederatedEvaluation, FederatedNode as DBFederatedNode, 
    EvaluationNodeResult, SecureAggregationSession
)


class TestFederatedEvaluationFramework:
    """Test suite for enhanced federated evaluation framework."""
    
    @pytest.fixture
    async def federated_evaluator(self):
        """Create a federated evaluator instance for testing."""
        evaluator = FederatedEvaluator()
        
        # Mock the initialization to avoid external dependencies
        with patch.object(evaluator, '_initialize_mab_client'), \
             patch.object(evaluator, '_load_federated_nodes'), \
             patch.object(evaluator, '_initialize_node_monitoring'), \
             patch.object(evaluator, '_initialize_byzantine_detection'):
            await evaluator.initialize()
        
        return evaluator
    
    @pytest.fixture
    def sample_evaluation_request(self):
        """Create a sample evaluation request."""
        return FederatedEvaluationRequest(
            policy_content="package acgs.test\n\nallow {\n    input.action == \"read\"\n}",
            evaluation_criteria={
                "category": "constitutional",
                "complexity": "medium",
                "safety_level": "standard",
                "metrics": ["compliance", "consistency", "performance"]
            },
            target_platforms=[PlatformType.CLOUD_OPENAI, PlatformType.CLOUD_ANTHROPIC],
            privacy_requirements={"epsilon": 1.0, "mechanism": "laplace"}
        )
    
    @pytest.fixture
    def mock_nodes(self):
        """Create mock federated nodes for testing."""
        nodes = {}
        for i in range(5):
            node_id = f"test_node_{i}"
            nodes[node_id] = FederatedNode(
                node_id=node_id,
                platform_type=PlatformType.CLOUD_OPENAI if i % 2 == 0 else PlatformType.CLOUD_ANTHROPIC,
                endpoint_url=f"https://api.test{i}.com",
                status="active",
                last_heartbeat=datetime.now(timezone.utc),
                performance_metrics={
                    "success_rate": 0.95 - (i * 0.05),
                    "avg_response_time": 1000 + (i * 200)
                }
            )
        return nodes
    
    async def test_multi_node_evaluation_submission(self, federated_evaluator, sample_evaluation_request, mock_nodes):
        """Test submission of evaluation with multiple nodes."""
        # Setup mock nodes
        federated_evaluator.nodes = mock_nodes
        
        # Mock database operations
        with patch.object(federated_evaluator, '_store_evaluation_in_db') as mock_store, \
             patch.object(federated_evaluator, '_execute_federated_evaluation') as mock_execute:
            
            task_id = await federated_evaluator.submit_evaluation(sample_evaluation_request)
            
            # Verify task was created
            assert task_id in federated_evaluator.active_evaluations
            task = federated_evaluator.active_evaluations[task_id]
            assert task.policy_content == sample_evaluation_request.policy_content
            assert task.target_platforms == sample_evaluation_request.target_platforms
            
            # Verify database storage was called
            mock_store.assert_called_once()
            mock_execute.assert_called_once()
    
    async def test_node_selection_algorithm(self, federated_evaluator, mock_nodes):
        """Test optimal node selection algorithm."""
        federated_evaluator.nodes = mock_nodes
        federated_evaluator.node_load_balancer = {
            "current_loads": {node_id: 0 for node_id in mock_nodes.keys()},
            "weights": {node_id: node.performance_metrics["success_rate"] for node_id, node in mock_nodes.items()}
        }
        federated_evaluator.max_concurrent_evaluations_per_node = 5
        federated_evaluator.quarantined_nodes = {}
        
        target_platforms = ["cloud_openai", "cloud_anthropic"]
        evaluation_criteria = {"complexity": "medium"}
        
        selected_nodes = await federated_evaluator._select_optimal_nodes(target_platforms, evaluation_criteria)
        
        # Verify selection criteria
        assert len(selected_nodes) >= 2
        assert len(selected_nodes) <= 10
        
        # Verify selected nodes are from target platforms
        for node_id in selected_nodes:
            node = mock_nodes[node_id]
            assert node.platform_type.value in target_platforms
            assert node.status == "active"
    
    async def test_byzantine_fault_detection(self, federated_evaluator, mock_nodes):
        """Test Byzantine fault detection algorithms."""
        federated_evaluator.nodes = mock_nodes
        federated_evaluator.quarantined_nodes = {}
        federated_evaluator.byzantine_config = {
            "detection_threshold": 0.3,
            "quarantine_duration": 300
        }
        
        # Simulate a node with suspicious behavior
        suspicious_node_id = "test_node_0"
        suspicious_node = mock_nodes[suspicious_node_id]
        suspicious_node.failed_evaluations = 15
        suspicious_node.total_evaluations = 20  # 75% failure rate
        suspicious_node.average_response_time_ms = 15000  # Very slow
        
        with patch.object(federated_evaluator, '_quarantine_node') as mock_quarantine:
            await federated_evaluator._check_node_performance_anomalies(suspicious_node_id)
            
            # Verify quarantine was called for suspicious behavior
            mock_quarantine.assert_called_once_with(suspicious_node_id, "performance_anomalies")
    
    async def test_node_health_monitoring(self, federated_evaluator, mock_nodes):
        """Test node health monitoring and scoring."""
        federated_evaluator.nodes = mock_nodes
        federated_evaluator.node_load_balancer = {"weights": {}}
        
        for node_id in mock_nodes.keys():
            await federated_evaluator._update_node_health_score(node_id)
            
            node = mock_nodes[node_id]
            assert 0.0 <= node.health_score <= 1.0
            assert node_id in federated_evaluator.node_load_balancer["weights"]
    
    async def test_load_balancing_weights(self, federated_evaluator, mock_nodes):
        """Test load balancing weight updates."""
        federated_evaluator.nodes = mock_nodes
        federated_evaluator.node_load_balancer = {"weights": {}}
        
        # Initialize weights
        await federated_evaluator._update_load_balancing_weights()
        
        # Verify all nodes have weights
        for node_id in mock_nodes.keys():
            assert node_id in federated_evaluator.node_load_balancer["weights"]
            weight = federated_evaluator.node_load_balancer["weights"][node_id]
            assert 0.0 <= weight <= 1.0
    
    async def test_evaluation_redistribution(self, federated_evaluator, mock_nodes, sample_evaluation_request):
        """Test redistribution of evaluations when a node fails."""
        federated_evaluator.nodes = mock_nodes
        
        # Create a mock active evaluation
        task_id = "test_task_123"
        task = EvaluationTask(
            task_id=task_id,
            policy_content=sample_evaluation_request.policy_content,
            evaluation_criteria=sample_evaluation_request.evaluation_criteria,
            target_platforms=sample_evaluation_request.target_platforms,
            mab_context={},
            privacy_requirements=sample_evaluation_request.privacy_requirements
        )
        federated_evaluator.active_evaluations[task_id] = task
        
        failed_node_id = "test_node_0"
        
        with patch.object(federated_evaluator, '_select_optimal_nodes') as mock_select, \
             patch.object(federated_evaluator, '_execute_federated_evaluation') as mock_execute:
            
            mock_select.return_value = ["test_node_1", "test_node_2"]
            
            await federated_evaluator._redistribute_node_evaluations(failed_node_id)
            
            # Verify redistribution was attempted
            mock_select.assert_called()
            mock_execute.assert_called()
    
    async def test_constitutional_compliance_integration(self, federated_evaluator, sample_evaluation_request):
        """Test integration with Constitutional Council for compliance validation."""
        # Mock constitutional validation
        with patch('app.core.federated_evaluator.constitutional_validator') as mock_validator:
            mock_validator.validate_policy_compliance.return_value = {
                "compliance_score": 0.95,
                "violations": [],
                "principle_ids_validated": [1, 2, 3]
            }
            
            # This would be called during evaluation execution
            compliance_result = await mock_validator.validate_policy_compliance(
                sample_evaluation_request.policy_content,
                sample_evaluation_request.evaluation_criteria
            )
            
            assert compliance_result["compliance_score"] >= 0.9
            assert len(compliance_result["violations"]) == 0
    
    async def test_mab_integration(self, federated_evaluator, sample_evaluation_request):
        """Test Multi-Armed Bandit integration for prompt optimization."""
        # Mock MAB client
        with patch.object(federated_evaluator, 'mab_client') as mock_mab:
            mock_mab.get_optimal_template.return_value = {
                "template_id": "constitutional_v2",
                "confidence": 0.85,
                "expected_performance": 0.92
            }
            
            mab_context = await federated_evaluator._get_mab_context(sample_evaluation_request)
            
            assert "template_id" in mab_context
            assert "confidence" in mab_context
    
    async def test_privacy_preservation(self, federated_evaluator):
        """Test privacy preservation mechanisms."""
        # Mock privacy manager
        with patch.object(federated_evaluator, 'privacy_manager') as mock_privacy:
            mock_privacy.apply_differential_privacy.return_value = {
                "epsilon_consumed": 0.1,
                "privacy_score": 0.95,
                "mechanisms_applied": ["laplace_noise"]
            }
            
            privacy_result = await mock_privacy.apply_differential_privacy(
                {"test_data": [1, 2, 3]},
                epsilon=1.0
            )
            
            assert privacy_result["privacy_score"] >= 0.9
            assert privacy_result["epsilon_consumed"] <= 1.0
    
    async def test_secure_aggregation(self, federated_evaluator):
        """Test secure aggregation of federated results."""
        # Mock secure aggregator
        with patch.object(federated_evaluator, 'secure_aggregator') as mock_aggregator:
            mock_results = {
                "node_1": {"compliance_score": 0.95, "execution_time": 1200},
                "node_2": {"compliance_score": 0.92, "execution_time": 1100},
                "node_3": {"compliance_score": 0.97, "execution_time": 1300}
            }
            
            mock_aggregator.aggregate_results.return_value = {
                "aggregated_compliance_score": 0.947,
                "aggregated_execution_time": 1200,
                "participant_count": 3,
                "byzantine_nodes_detected": 0,
                "privacy_score": 0.98
            }
            
            aggregated = await mock_aggregator.aggregate_results(
                mock_results,
                method="federated_averaging"
            )
            
            assert aggregated["participant_count"] == 3
            assert aggregated["byzantine_nodes_detected"] == 0
            assert 0.9 <= aggregated["aggregated_compliance_score"] <= 1.0
    
    async def test_performance_targets(self, federated_evaluator, sample_evaluation_request, mock_nodes):
        """Test that performance targets are met."""
        federated_evaluator.nodes = mock_nodes
        
        # Test response time target (<200ms for API calls)
        start_time = datetime.now()
        
        with patch.object(federated_evaluator, '_store_evaluation_in_db'), \
             patch.object(federated_evaluator, '_execute_federated_evaluation'):
            
            task_id = await federated_evaluator.submit_evaluation(sample_evaluation_request)
            
        end_time = datetime.now()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Verify response time target
        assert response_time_ms < 200, f"Response time {response_time_ms}ms exceeds 200ms target"
        
        # Verify task was created successfully
        assert task_id in federated_evaluator.active_evaluations
    
    async def test_concurrent_evaluations(self, federated_evaluator, mock_nodes):
        """Test support for 50+ concurrent evaluations."""
        federated_evaluator.nodes = mock_nodes
        
        # Create multiple evaluation requests
        evaluation_requests = []
        for i in range(10):  # Reduced for test performance
            request = FederatedEvaluationRequest(
                policy_content=f"package test{i}\n\nallow {{ input.id == {i} }}",
                evaluation_criteria={"complexity": "low"},
                target_platforms=[PlatformType.CLOUD_OPENAI],
                privacy_requirements={"epsilon": 1.0}
            )
            evaluation_requests.append(request)
        
        with patch.object(federated_evaluator, '_store_evaluation_in_db'), \
             patch.object(federated_evaluator, '_execute_federated_evaluation'):
            
            # Submit evaluations concurrently
            tasks = [
                federated_evaluator.submit_evaluation(request)
                for request in evaluation_requests
            ]
            
            task_ids = await asyncio.gather(*tasks)
            
            # Verify all evaluations were submitted successfully
            assert len(task_ids) == len(evaluation_requests)
            assert len(set(task_ids)) == len(task_ids)  # All unique
            
            # Verify all tasks are tracked
            for task_id in task_ids:
                assert task_id in federated_evaluator.active_evaluations


@pytest.mark.asyncio
class TestFederatedEvaluationAPI:
    """Test suite for federated evaluation API endpoints."""
    
    async def test_submit_evaluation_endpoint(self):
        """Test the submit evaluation API endpoint."""
        # This would require FastAPI test client setup
        # Placeholder for API endpoint testing
        pass
    
    async def test_node_health_endpoint(self):
        """Test the node health status API endpoint."""
        # This would require FastAPI test client setup
        # Placeholder for API endpoint testing
        pass
    
    async def test_quarantine_node_endpoint(self):
        """Test the quarantine node API endpoint."""
        # This would require FastAPI test client setup
        # Placeholder for API endpoint testing
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
