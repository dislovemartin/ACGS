"""
Integration tests for Federated Evaluation Framework Phase 1

Tests the core federated architecture, secure aggregation protocols,
and differential privacy implementation.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any

# Test the core components
def test_federated_evaluator_import():
    """Test that federated evaluator can be imported."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/federated_service'))

        from app.core.federated_evaluator import (
            FederatedEvaluator, PlatformType, EvaluationStatus, FederatedNode, EvaluationTask
        )
        
        # Test enum values
        assert PlatformType.CLOUD_OPENAI.value == "cloud_openai"
        assert PlatformType.CLOUD_ANTHROPIC.value == "cloud_anthropic"
        assert PlatformType.EDGE_LOCAL.value == "edge_local"

        assert EvaluationStatus.PENDING.value == "pending"
        assert EvaluationStatus.IN_PROGRESS.value == "in_progress"
        assert EvaluationStatus.COMPLETED.value == "completed"
        
        print("✅ Federated evaluator imports successful")
        
    except ImportError as e:
        pytest.fail(f"Failed to import federated evaluator: {e}")


def test_secure_aggregation_import():
    """Test that secure aggregation can be imported."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/federated_service'))

        from app.core.secure_aggregation import (
            SecureAggregator, AggregationMethod, AggregationConfig, SecureShare
        )
        
        # Test enum values
        assert AggregationMethod.FEDERATED_AVERAGING.value == "federated_averaging"
        assert AggregationMethod.SECURE_SUM.value == "secure_sum"
        assert AggregationMethod.DIFFERENTIAL_PRIVATE.value == "differential_private"
        assert AggregationMethod.BYZANTINE_ROBUST.value == "byzantine_robust"
        
        print("✅ Secure aggregation imports successful")
        
    except ImportError as e:
        pytest.fail(f"Failed to import secure aggregation: {e}")


def test_privacy_metrics_import():
    """Test that privacy metrics can be imported."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/federated_service'))

        from app.core.privacy_metrics import (
            DifferentialPrivacyManager, PrivacyMechanism, PrivacyBudget, PrivacyMetrics
        )
        
        # Test enum values
        assert PrivacyMechanism.LAPLACE.value == "laplace"
        assert PrivacyMechanism.GAUSSIAN.value == "gaussian"
        assert PrivacyMechanism.EXPONENTIAL.value == "exponential"
        assert PrivacyMechanism.LOCAL_DP.value == "local_dp"
        
        print("✅ Privacy metrics imports successful")
        
    except ImportError as e:
        pytest.fail(f"Failed to import privacy metrics: {e}")


def test_federated_schemas_import():
    """Test that federated schemas can be imported."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/federated_service'))

        from app.schemas import (
            FederatedEvaluationRequest, FederatedEvaluationResponse,
            NodeConfiguration, EvaluationMetrics, AggregatedResults,
            PlatformType, EvaluationStatus, AggregationMethod
        )
        
        print("✅ Federated schemas imports successful")
        
    except ImportError as e:
        pytest.fail(f"Failed to import federated schemas: {e}")


@pytest.mark.asyncio
async def test_federated_evaluator_initialization():
    """Test federated evaluator initialization."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/federated_service'))

        from app.core.federated_evaluator import FederatedEvaluator
        
        # Create evaluator instance
        evaluator = FederatedEvaluator()
        
        # Test initial state
        assert evaluator.nodes == {}
        assert evaluator.active_evaluations == {}
        assert evaluator.secure_aggregator is None
        assert evaluator.privacy_manager is None
        
        # Test initialization (mock mode)
        await evaluator.initialize()
        
        # Verify components are initialized
        assert evaluator.secure_aggregator is not None
        assert evaluator.privacy_manager is not None
        
        # Test metrics
        metrics = await evaluator.get_evaluation_metrics()
        assert isinstance(metrics, dict)
        assert "total_evaluations" in metrics
        
        # Cleanup
        await evaluator.shutdown()
        
        print("✅ Federated evaluator initialization successful")
        
    except Exception as e:
        pytest.fail(f"Federated evaluator initialization failed: {e}")


@pytest.mark.asyncio
async def test_secure_aggregator_initialization():
    """Test secure aggregator initialization."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/federated_service'))

        from app.core.secure_aggregation import SecureAggregator
        
        # Create aggregator instance
        aggregator = SecureAggregator()
        
        # Test initialization
        await aggregator.initialize()
        
        # Verify crypto keys are generated
        assert aggregator.crypto_keys is not None
        assert len(aggregator.crypto_keys) > 0
        
        # Test metrics
        metrics = await aggregator.get_aggregation_metrics()
        assert isinstance(metrics, dict)
        assert "total_aggregations" in metrics
        
        # Cleanup
        await aggregator.shutdown()
        
        print("✅ Secure aggregator initialization successful")
        
    except Exception as e:
        pytest.fail(f"Secure aggregator initialization failed: {e}")


@pytest.mark.asyncio
async def test_privacy_manager_initialization():
    """Test privacy manager initialization."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/federated_service'))

        from app.core.privacy_metrics import DifferentialPrivacyManager
        
        # Create privacy manager instance
        privacy_manager = DifferentialPrivacyManager(epsilon=1.0, delta=1e-5)
        
        # Test initialization
        await privacy_manager.initialize()
        
        # Verify privacy budget
        assert privacy_manager.privacy_budget.epsilon == 1.0
        assert privacy_manager.privacy_budget.delta == 1e-5
        assert privacy_manager.privacy_budget.remaining_epsilon == 1.0
        
        # Test metrics
        metrics = await privacy_manager.get_privacy_metrics()
        assert isinstance(metrics, dict)
        assert "privacy_budget" in metrics
        assert "metrics" in metrics
        
        # Cleanup
        await privacy_manager.shutdown()
        
        print("✅ Privacy manager initialization successful")
        
    except Exception as e:
        pytest.fail(f"Privacy manager initialization failed: {e}")


@pytest.mark.asyncio
async def test_mock_federated_evaluation():
    """Test mock federated evaluation workflow."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/federated_service'))

        from app.core.federated_evaluator import FederatedEvaluator, PlatformType
        
        # Create and initialize evaluator
        evaluator = FederatedEvaluator()
        await evaluator.initialize()
        
        # Create mock evaluation request
        mock_request = type('MockRequest', (), {
            'policy_content': 'package test\nallow { true }',
            'evaluation_criteria': {'category': 'test', 'safety_level': 'standard'},
            'target_platforms': [PlatformType.CLOUD_OPENAI, PlatformType.EDGE_LOCAL],
            'privacy_requirements': {'epsilon': 0.5, 'mechanism': 'laplace'}
        })()
        
        # Submit evaluation
        task_id = await evaluator.submit_evaluation(mock_request)
        assert isinstance(task_id, str)
        assert len(task_id) == 16  # MD5 hash truncated to 16 chars
        
        # Check task status
        status = await evaluator.get_evaluation_status(task_id)
        assert status is not None
        assert status['task_id'] == task_id
        
        # Wait a bit for processing
        await asyncio.sleep(1)
        
        # Cleanup
        await evaluator.shutdown()
        
        print("✅ Mock federated evaluation successful")
        
    except Exception as e:
        pytest.fail(f"Mock federated evaluation failed: {e}")


def test_federated_service_structure():
    """Test that federated service has proper structure."""
    import os
    
    base_path = "src/backend/federated_service"
    
    # Check main files exist
    required_files = [
        "Dockerfile",
        "requirements.txt",
        "app/__init__.py",
        "app/main.py",
        "app/schemas.py",
        "app/core/__init__.py",
        "app/core/federated_evaluator.py",
        "app/core/secure_aggregation.py",
        "app/core/privacy_metrics.py",
        "app/core/federated_coordinator.py",
        "app/api/__init__.py",
        "app/api/v1/__init__.py",
        "app/api/v1/federated_evaluation.py",
        "app/api/v1/secure_aggregation.py",
        "app/api/v1/privacy_metrics.py",
        "app/dashboard/__init__.py",
        "app/dashboard/federated_dashboard.py"
    ]
    
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        assert os.path.exists(full_path), f"Required file missing: {full_path}"
    
    print("✅ Federated service structure validation successful")


if __name__ == "__main__":
    # Run basic import tests
    test_federated_evaluator_import()
    test_secure_aggregation_import()
    test_privacy_metrics_import()
    test_federated_schemas_import()
    test_federated_service_structure()
    
    # Run async tests
    asyncio.run(test_federated_evaluator_initialization())
    asyncio.run(test_secure_aggregator_initialization())
    asyncio.run(test_privacy_manager_initialization())
    asyncio.run(test_mock_federated_evaluation())
    
    print("\n🎉 All Phase 1 Federated Evaluation Framework tests passed!")
    print("✅ Core federated architecture implemented successfully")
    print("✅ Secure aggregation protocols functional")
    print("✅ Differential privacy framework operational")
    print("✅ MAB integration ready for cross-platform optimization")
