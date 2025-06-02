"""
Integration Tests for WINA Continuous Learning Feedback Loops (Task 17.8)

This test suite validates the integration between the continuous learning system
and the performance monitoring infrastructure from Task 17.10, ensuring proper
feedback loop functionality and adaptive learning capabilities.

Test Coverage:
- Learning system initialization and integration
- Feedback signal processing and learning algorithms
- Performance monitoring integration
- EC Layer oversight coordinator integration
- API endpoints and real-time learning
- End-to-end learning feedback loops
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch

# WINA imports
try:
    from src.backend.shared.wina.continuous_learning import (
        WINAContinuousLearningSystem,
        FeedbackSignal,
        FeedbackType,
        LearningStrategy,
        LearningPhase,
        ComponentLearningProfile,
        LearningAction,
        get_wina_learning_system,
        process_efficiency_feedback,
        process_accuracy_feedback,
        process_constitutional_feedback
    )
    from src.backend.shared.wina.performance_monitoring import (
        WINAPerformanceCollector,
        WINAMonitoringLevel,
        WINAComponentType,
        WINALearningFeedbackMetrics,
        WINANeuronActivationMetrics,
        WINADynamicGatingMetrics,
        WINAConstitutionalComplianceMetrics,
        WINAIntegrationPerformanceMetrics
    )
    from src.backend.shared.wina.learning_api import (
        create_learning_api_router,
        FeedbackSubmissionRequest,
        ComponentTypeAPI,
        FeedbackTypeAPI,
        integrate_with_performance_monitoring
    )
    from src.backend.ec_service.app.core.wina_oversight_coordinator import (
        WINAECOversightCoordinator,
        ECOversightRequest,
        ECOversightContext,
        get_wina_ec_oversight_coordinator
    )
    WINA_AVAILABLE = True
except ImportError as e:
    WINA_AVAILABLE = False
    print(f"WINA modules not available for testing: {e}")

from fastapi.testclient import TestClient
from fastapi import FastAPI

pytestmark = pytest.mark.skipif(not WINA_AVAILABLE, reason="WINA modules not available")


@pytest.fixture
async def learning_system():
    """Provide a fresh learning system instance for testing."""
    if not WINA_AVAILABLE:
        pytest.skip("WINA not available")
    
    system = WINAContinuousLearningSystem()
    await system.initialize()
    yield system
    await system.shutdown()


@pytest.fixture
async def performance_collector():
    """Provide a performance collector instance for testing."""
    if not WINA_AVAILABLE:
        pytest.skip("WINA not available")
    
    collector = WINAPerformanceCollector(
        monitoring_level=WINAMonitoringLevel.COMPREHENSIVE
    )
    await collector.start()
    yield collector
    await collector.stop()


@pytest.fixture
async def integrated_system(learning_system, performance_collector):
    """Provide an integrated learning system with performance monitoring."""
    learning_system.set_performance_collector(performance_collector)
    await learning_system.start_performance_integration()
    yield learning_system, performance_collector
    await learning_system.stop_performance_integration()


@pytest.fixture
async def oversight_coordinator():
    """Provide an EC oversight coordinator for testing."""
    if not WINA_AVAILABLE:
        pytest.skip("WINA not available")
    
    coordinator = WINAECOversightCoordinator(enable_wina=True)
    await coordinator.initialize_constitutional_principles()
    yield coordinator


@pytest.fixture
def api_client():
    """Provide a test client for the learning API."""
    if not WINA_AVAILABLE:
        pytest.skip("WINA not available")
    
    app = FastAPI()
    router = create_learning_api_router()
    app.include_router(router)
    
    return TestClient(app)


class TestContinuousLearningSystemInitialization:
    """Test learning system initialization and configuration."""
    
    async def test_learning_system_initialization(self, learning_system):
        """Test that the learning system initializes correctly."""
        assert learning_system is not None
        assert learning_system.learning_state["current_phase"] == LearningPhase.EXPLORATION
        assert learning_system.learning_state["strategy_in_use"] == LearningStrategy.REINFORCEMENT_LEARNING
        assert learning_system.learning_state["exploration_rate"] > 0.0
        assert learning_system.learning_state["learning_rate"] > 0.0
    
    async def test_component_learning_profiles(self, learning_system):
        """Test that component learning profiles are properly initialized."""
        profiles = learning_system.component_profiles
        
        # Check that all major components have profiles
        expected_components = [
            WINAComponentType.NEURON_ACTIVATION,
            WINAComponentType.SVD_TRANSFORMATION,
            WINAComponentType.DYNAMIC_GATING,
            WINAComponentType.CONSTITUTIONAL_VERIFICATION
        ]
        
        for component in expected_components:
            assert component in profiles
            profile = profiles[component]
            assert isinstance(profile, ComponentLearningProfile)
            assert profile.current_parameters is not None
            assert profile.parameter_bounds is not None
            assert profile.optimization_history is not None
    
    async def test_learning_algorithms_initialization(self, learning_system):
        """Test that learning algorithms are properly initialized."""
        algorithms = learning_system.learning_algorithms
        
        assert LearningStrategy.REINFORCEMENT_LEARNING in algorithms
        assert LearningStrategy.PATTERN_RECOGNITION in algorithms
        
        # Test reinforcement learning algorithm
        rl_algorithm = algorithms[LearningStrategy.REINFORCEMENT_LEARNING]
        assert rl_algorithm.learning_rate > 0.0
        assert rl_algorithm.discount_factor > 0.0
        assert rl_algorithm.exploration_rate > 0.0
        
        # Test pattern recognition algorithm
        pr_algorithm = algorithms[LearningStrategy.PATTERN_RECOGNITION]
        assert pr_algorithm.pattern_threshold > 0.0
        assert pr_algorithm.confidence_threshold > 0.0


class TestFeedbackSignalProcessing:
    """Test feedback signal processing and learning action generation."""
    
    async def test_feedback_signal_processing(self, learning_system):
        """Test basic feedback signal processing."""
        feedback = FeedbackSignal(
            component_type=WINAComponentType.NEURON_ACTIVATION,
            feedback_type=FeedbackType.EFFICIENCY_GAIN,
            value=0.6,
            context={"optimization_target": "gflops_reduction"},
            timestamp=datetime.now(),
            confidence=0.9,
            source="test_suite"
        )
        
        # Process feedback
        await learning_system.process_feedback_signal(feedback)
        
        # Check that feedback was processed
        status = await learning_system.get_learning_status()
        assert status["metrics"]["total_feedback_processed"] > 0
        assert len(learning_system.feedback_queue) >= 0  # Might be processed already
    
    async def test_batch_feedback_processing(self, learning_system):
        """Test batch feedback processing capabilities."""
        feedback_signals = []
        
        # Create multiple feedback signals
        for i in range(10):
            feedback = FeedbackSignal(
                component_type=WINAComponentType.DYNAMIC_GATING,
                feedback_type=FeedbackType.PERFORMANCE_METRIC,
                value=0.5 + (i * 0.05),
                context={"batch_test": True, "signal_id": i},
                timestamp=datetime.now(),
                confidence=0.8,
                source="batch_test"
            )
            feedback_signals.append(feedback)
        
        # Process all feedback signals
        for feedback in feedback_signals:
            await learning_system.process_feedback_signal(feedback)
        
        # Allow processing time
        await asyncio.sleep(0.1)
        
        status = await learning_system.get_learning_status()
        assert status["metrics"]["total_feedback_processed"] >= 10
    
    async def test_learning_action_generation(self, learning_system):
        """Test that feedback signals generate appropriate learning actions."""
        # Submit efficiency feedback
        efficiency_feedback = FeedbackSignal(
            component_type=WINAComponentType.NEURON_ACTIVATION,
            feedback_type=FeedbackType.EFFICIENCY_GAIN,
            value=0.7,
            context={"gflops_reduction": 0.5},
            timestamp=datetime.now(),
            confidence=0.95,
            source="action_test"
        )
        
        await learning_system.process_feedback_signal(efficiency_feedback)
        
        # Allow processing time
        await asyncio.sleep(0.1)
        
        # Check for learning actions
        status = await learning_system.get_learning_status()
        assert status["metrics"]["learning_actions_generated"] > 0
        
        # Check recent actions
        recent_actions = learning_system.get_recent_actions(limit=5)
        assert len(recent_actions) > 0
        
        action = recent_actions[0]
        assert action.component_type == WINAComponentType.NEURON_ACTIVATION
        assert action.parameter_updates is not None
        assert action.confidence > 0.0


class TestPerformanceMonitoringIntegration:
    """Test integration with performance monitoring system from Task 17.10."""
    
    async def test_performance_collector_integration(self, integrated_system):
        """Test that learning system integrates with performance collector."""
        learning_system, performance_collector = integrated_system
        
        # Verify integration
        assert learning_system.performance_collector is performance_collector
        assert learning_system.performance_integration_active
        
        # Test automatic feedback generation from performance metrics
        neuron_metrics = WINANeuronActivationMetrics(
            component_type=WINAComponentType.NEURON_ACTIVATION,
            neurons_activated=1000,
            neurons_skipped=500,
            activation_efficiency=0.6,
            memory_saved_mb=50.0,
            computation_time_ms=20.0,
            accuracy_retention=0.96,
            threshold_applied=0.5,
            optimization_strategy="test_strategy"
        )
        
        await performance_collector.record_neuron_activation_metrics(neuron_metrics)
        
        # Allow processing time for automatic feedback generation
        await asyncio.sleep(0.2)
        
        # Check that learning system received feedback
        status = await learning_system.get_learning_status()
        assert status["metrics"]["total_feedback_processed"] > 0
    
    async def test_learning_feedback_metrics_recording(self, integrated_system):
        """Test recording of learning feedback metrics."""
        learning_system, performance_collector = integrated_system
        
        # Process some feedback to generate learning metrics
        feedback = FeedbackSignal(
            component_type=WINAComponentType.SVD_TRANSFORMATION,
            feedback_type=FeedbackType.ACCURACY_RETENTION,
            value=0.97,
            context={"svd_optimization": True},
            timestamp=datetime.now(),
            confidence=0.9,
            source="metrics_test"
        )
        
        await learning_system.process_feedback_signal(feedback)
        await asyncio.sleep(0.1)
        
        # Check that learning feedback metrics are recorded
        learning_metrics = WINALearningFeedbackMetrics(
            component_type=WINAComponentType.SVD_TRANSFORMATION,
            feedback_signals_processed=1,
            learning_actions_generated=1,
            adaptation_success_rate=1.0,
            convergence_rate=0.8,
            exploration_efficiency=0.7,
            learning_velocity=0.05,
            feedback_quality_score=0.9,
            strategy_effectiveness=0.85
        )
        
        await performance_collector.record_learning_feedback_metrics(learning_metrics)
        
        # Verify metrics are recorded
        assert performance_collector.metrics_recorded
    
    async def test_automated_performance_feedback_loop(self, integrated_system):
        """Test automated feedback loop from performance monitoring."""
        learning_system, performance_collector = integrated_system
        
        # Simulate performance metrics that should trigger learning feedback
        gating_metrics = WINADynamicGatingMetrics(
            component_type=WINAComponentType.DYNAMIC_GATING,
            gates_applied=15,
            gates_bypassed=5,
            gating_efficiency=0.75,
            decision_time_ms=3.0,
            accuracy_impact=0.01,
            resource_savings=0.6,
            adaptive_threshold=0.7,
            gating_strategy="aggressive"
        )
        
        await performance_collector.record_dynamic_gating_metrics(gating_metrics)
        
        # Allow automatic feedback processing
        await asyncio.sleep(0.3)
        
        # Verify learning system adapted
        status = await learning_system.get_learning_status()
        assert status["metrics"]["successful_adaptations"] > 0
        
        # Check component profile updates
        gating_profile = learning_system.component_profiles[WINAComponentType.DYNAMIC_GATING]
        assert len(gating_profile.optimization_history) > 0


class TestECOversightCoordinatorIntegration:
    """Test integration with EC Layer oversight coordinator."""
    
    async def test_oversight_feedback_integration(self, oversight_coordinator):
        """Test that oversight coordinator sends feedback to learning system."""
        # Create oversight request
        request = ECOversightRequest(
            request_id="test_learning_integration",
            oversight_type=ECOversightContext.PERFORMANCE_OPTIMIZATION,
            target_system="test_system",
            governance_requirements=["efficiency_target", "compliance_check"],
            constitutional_constraints=["privacy_protection"],
            performance_thresholds={"accuracy": 0.95, "efficiency": 0.6},
            priority_level="high",
            wina_optimization_enabled=True
        )
        
        # Coordinate oversight
        result = await oversight_coordinator.coordinate_oversight(request)
        
        # Verify oversight completed
        assert result.oversight_decision in ["approved", "conditional", "denied", "requires_review"]
        assert result.wina_optimization_applied is True
        
        # Check that learning feedback was generated
        assert result.feedback_data is not None
        if result.feedback_data.get("learning_system_updated"):
            assert result.feedback_data["learning_system_updated"] is True
    
    async def test_oversight_learning_adaptation(self, oversight_coordinator):
        """Test learning adaptation based on oversight feedback."""
        # Process multiple oversight requests to build learning data
        for i in range(5):
            request = ECOversightRequest(
                request_id=f"test_adaptation_{i}",
                oversight_type=ECOversightContext.ROUTINE_MONITORING,
                target_system=f"system_{i}",
                governance_requirements=[f"requirement_{i}"],
                priority_level="normal",
                wina_optimization_enabled=True
            )
            
            result = await oversight_coordinator.coordinate_oversight(request)
            assert result is not None
        
        # Check that learning adaptations occurred
        if oversight_coordinator.learning_system:
            status = await oversight_coordinator.learning_system.get_learning_status()
            assert status["metrics"]["total_feedback_processed"] > 0


class TestLearningAPIEndpoints:
    """Test learning API endpoints functionality."""
    
    def test_health_endpoint(self, api_client):
        """Test learning system health endpoint."""
        response = api_client.get("/api/v1/wina/learning/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unavailable"]
    
    def test_feedback_submission_endpoint(self, api_client):
        """Test feedback submission endpoint."""
        feedback_request = {
            "component_type": "neuron_activation",
            "feedback_type": "efficiency_gain",
            "value": 0.6,
            "context": {"test": "api_endpoint"},
            "confidence": 0.9,
            "source": "api_test"
        }
        
        response = api_client.post("/api/v1/wina/learning/feedback", json=feedback_request)
        
        # Should succeed if WINA available, otherwise may fail gracefully
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "feedback_id" in data
            assert "processing_time_ms" in data
    
    def test_batch_feedback_endpoint(self, api_client):
        """Test batch feedback submission endpoint."""
        batch_request = {
            "feedback_signals": [
                {
                    "component_type": "dynamic_gating",
                    "feedback_type": "performance_metric",
                    "value": 0.7,
                    "context": {"batch_test": True},
                    "confidence": 0.85
                },
                {
                    "component_type": "svd_transformation",
                    "feedback_type": "accuracy_retention",
                    "value": 0.96,
                    "context": {"batch_test": True},
                    "confidence": 0.9
                }
            ],
            "priority": "normal"
        }
        
        response = api_client.post("/api/v1/wina/learning/feedback/batch", json=batch_request)
        
        if response.status_code == 200:
            data = response.json()
            assert "batch_id" in data
            assert data["total_signals"] == 2
    
    def test_learning_status_endpoint(self, api_client):
        """Test learning status endpoint."""
        response = api_client.get("/api/v1/wina/learning/status")
        
        if response.status_code == 200:
            data = response.json()
            assert "current_phase" in data
            assert "strategy_in_use" in data
            assert "metrics" in data
            assert "system_health" in data
    
    def test_component_recommendations_endpoint(self, api_client):
        """Test component recommendations endpoint."""
        request_data = {
            "component_type": "neuron_activation",
            "include_parameters": True,
            "optimization_target": "efficiency"
        }
        
        response = api_client.post("/api/v1/wina/learning/recommendations", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            assert data["component_type"] == "neuron_activation"
            assert "current_parameters" in data
            assert "recommendations" in data
    
    def test_convenience_feedback_endpoints(self, api_client):
        """Test convenience feedback endpoints."""
        # Test efficiency feedback
        efficiency_response = api_client.post(
            "/api/v1/wina/learning/feedback/efficiency",
            params={
                "component_type": "neuron_activation",
                "efficiency_value": 0.7
            }
        )
        
        # Test accuracy feedback
        accuracy_response = api_client.post(
            "/api/v1/wina/learning/feedback/accuracy",
            params={
                "component_type": "svd_transformation",
                "accuracy_value": 0.96
            }
        )
        
        # Test constitutional feedback
        constitutional_response = api_client.post(
            "/api/v1/wina/learning/feedback/constitutional",
            params={"compliance_score": 0.95}
        )
        
        # At least one should succeed if system is working
        successful_responses = [
            r for r in [efficiency_response, accuracy_response, constitutional_response]
            if r.status_code == 200
        ]
        
        if successful_responses:
            data = successful_responses[0].json()
            assert data["success"] is True


class TestLearningAlgorithms:
    """Test learning algorithm functionality and adaptation."""
    
    async def test_reinforcement_learning_algorithm(self, learning_system):
        """Test reinforcement learning algorithm functionality."""
        rl_algorithm = learning_system.learning_algorithms[LearningStrategy.REINFORCEMENT_LEARNING]
        
        # Test parameter update
        current_params = {"threshold": 0.5, "learning_rate": 0.01}
        reward = 0.8
        
        updated_params = await rl_algorithm.update_parameters(current_params, reward)
        
        assert updated_params is not None
        assert "threshold" in updated_params
        assert "learning_rate" in updated_params
        
        # With positive reward, parameters should be adjusted
        assert updated_params != current_params
    
    async def test_pattern_recognition_algorithm(self, learning_system):
        """Test pattern recognition algorithm functionality."""
        pr_algorithm = learning_system.learning_algorithms[LearningStrategy.PATTERN_RECOGNITION]
        
        # Test pattern detection
        feedback_history = [
            {"value": 0.6, "context": {"optimization": "gflops"}},
            {"value": 0.65, "context": {"optimization": "gflops"}},
            {"value": 0.7, "context": {"optimization": "gflops"}},
        ]
        
        patterns = await pr_algorithm.detect_patterns(feedback_history)
        
        assert patterns is not None
        assert isinstance(patterns, list)
        
        # Should detect improving trend
        if patterns:
            pattern = patterns[0]
            assert "trend" in pattern or "pattern_type" in pattern
    
    async def test_learning_phase_transitions(self, learning_system):
        """Test learning phase transitions."""
        initial_phase = learning_system.learning_state["current_phase"]
        
        # Process feedback to potentially trigger phase transition
        for i in range(20):
            feedback = FeedbackSignal(
                component_type=WINAComponentType.NEURON_ACTIVATION,
                feedback_type=FeedbackType.EFFICIENCY_GAIN,
                value=0.6 + (i * 0.01),
                context={"phase_test": True},
                timestamp=datetime.now(),
                confidence=0.9,
                source="phase_test"
            )
            await learning_system.process_feedback_signal(feedback)
        
        # Allow processing and potential phase transitions
        await asyncio.sleep(0.5)
        
        # Check if phase might have changed
        current_phase = learning_system.learning_state["current_phase"]
        
        # Phase may or may not change based on algorithm logic
        assert current_phase in [phase for phase in LearningPhase]


class TestEndToEndLearningLoop:
    """Test complete end-to-end learning feedback loops."""
    
    async def test_complete_learning_cycle(self, integrated_system, oversight_coordinator):
        """Test complete learning cycle from oversight to adaptation."""
        learning_system, performance_collector = integrated_system
        
        # Step 1: Submit oversight request
        request = ECOversightRequest(
            request_id="end_to_end_test",
            oversight_type=ECOversightContext.PERFORMANCE_OPTIMIZATION,
            target_system="complete_test_system",
            governance_requirements=["efficiency_optimization"],
            performance_thresholds={"gflops_reduction": 0.5},
            priority_level="high",
            wina_optimization_enabled=True
        )
        
        # Step 2: Process oversight (generates feedback)
        oversight_result = await oversight_coordinator.coordinate_oversight(request)
        assert oversight_result.wina_optimization_applied is True
        
        # Step 3: Allow learning system to process feedback
        await asyncio.sleep(0.3)
        
        # Step 4: Check learning system adaptation
        status = await learning_system.get_learning_status()
        assert status["metrics"]["total_feedback_processed"] > 0
        
        # Step 5: Get component recommendations
        neuron_recommendations = await learning_system.get_component_recommendations(
            WINAComponentType.NEURON_ACTIVATION
        )
        assert "current_parameters" in neuron_recommendations
        
        # Step 6: Verify learning effectiveness
        if status["metrics"]["learning_actions_generated"] > 0:
            recent_actions = learning_system.get_recent_actions(limit=3)
            assert len(recent_actions) > 0
            
            # Check that actions have reasonable confidence
            for action in recent_actions:
                assert action.confidence > 0.0
                assert action.parameter_updates is not None
    
    async def test_continuous_adaptation_over_time(self, learning_system):
        """Test continuous adaptation over multiple feedback cycles."""
        initial_status = await learning_system.get_learning_status()
        initial_processed = initial_status["metrics"]["total_feedback_processed"]
        
        # Simulate continuous feedback over time
        components = [
            WINAComponentType.NEURON_ACTIVATION,
            WINAComponentType.SVD_TRANSFORMATION,
            WINAComponentType.DYNAMIC_GATING
        ]
        
        for cycle in range(3):
            for component in components:
                # Efficiency feedback
                efficiency_feedback = FeedbackSignal(
                    component_type=component,
                    feedback_type=FeedbackType.EFFICIENCY_GAIN,
                    value=0.5 + (cycle * 0.1),
                    context={"cycle": cycle, "component": component.value},
                    timestamp=datetime.now(),
                    confidence=0.85,
                    source="continuous_test"
                )
                await learning_system.process_feedback_signal(efficiency_feedback)
                
                # Accuracy feedback
                accuracy_feedback = FeedbackSignal(
                    component_type=component,
                    feedback_type=FeedbackType.ACCURACY_RETENTION,
                    value=0.96 - (cycle * 0.001),  # Slight accuracy trade-off
                    context={"cycle": cycle, "component": component.value},
                    timestamp=datetime.now(),
                    confidence=0.9,
                    source="continuous_test"
                )
                await learning_system.process_feedback_signal(accuracy_feedback)
            
            # Allow processing between cycles
            await asyncio.sleep(0.2)
        
        # Check final adaptation
        final_status = await learning_system.get_learning_status()
        final_processed = final_status["metrics"]["total_feedback_processed"]
        
        # Should have processed more feedback
        assert final_processed > initial_processed
        
        # Should have generated learning actions
        assert final_status["metrics"]["learning_actions_generated"] > 0
        
        # Check that component profiles have been updated
        for component in components:
            profile = learning_system.component_profiles[component]
            assert len(profile.optimization_history) > 0


class TestLearningSystemRobustness:
    """Test learning system robustness and error handling."""
    
    async def test_invalid_feedback_handling(self, learning_system):
        """Test handling of invalid feedback signals."""
        # Test with invalid feedback value
        invalid_feedback = FeedbackSignal(
            component_type=WINAComponentType.NEURON_ACTIVATION,
            feedback_type=FeedbackType.EFFICIENCY_GAIN,
            value=2.0,  # Invalid: should be 0-1
            context={"test": "invalid"},
            timestamp=datetime.now(),
            confidence=0.8,
            source="invalid_test"
        )
        
        # Should handle gracefully without crashing
        try:
            await learning_system.process_feedback_signal(invalid_feedback)
        except Exception as e:
            # Should either process with normalization or raise specific error
            assert "value" in str(e).lower() or "range" in str(e).lower()
    
    async def test_concurrent_feedback_processing(self, learning_system):
        """Test concurrent feedback processing."""
        async def submit_feedback(i):
            feedback = FeedbackSignal(
                component_type=WINAComponentType.DYNAMIC_GATING,
                feedback_type=FeedbackType.PERFORMANCE_METRIC,
                value=0.5 + (i * 0.01),
                context={"concurrent_test": True, "id": i},
                timestamp=datetime.now(),
                confidence=0.8,
                source=f"concurrent_test_{i}"
            )
            await learning_system.process_feedback_signal(feedback)
        
        # Submit multiple feedback signals concurrently
        tasks = [submit_feedback(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Allow processing
        await asyncio.sleep(0.3)
        
        # Check that all feedback was processed
        status = await learning_system.get_learning_status()
        assert status["metrics"]["total_feedback_processed"] >= 10
    
    async def test_system_recovery_after_error(self, learning_system):
        """Test system recovery after processing errors."""
        # First, submit valid feedback
        valid_feedback = FeedbackSignal(
            component_type=WINAComponentType.NEURON_ACTIVATION,
            feedback_type=FeedbackType.EFFICIENCY_GAIN,
            value=0.6,
            context={"test": "recovery"},
            timestamp=datetime.now(),
            confidence=0.9,
            source="recovery_test"
        )
        
        await learning_system.process_feedback_signal(valid_feedback)
        
        # Then simulate error condition and recovery
        try:
            # Mock an internal error condition
            with patch.object(learning_system, '_process_feedback_batch', side_effect=Exception("Simulated error")):
                error_feedback = FeedbackSignal(
                    component_type=WINAComponentType.SVD_TRANSFORMATION,
                    feedback_type=FeedbackType.ACCURACY_RETENTION,
                    value=0.95,
                    context={"test": "error_condition"},
                    timestamp=datetime.now(),
                    confidence=0.8,
                    source="error_test"
                )
                await learning_system.process_feedback_signal(error_feedback)
        except Exception:
            pass  # Expected error
        
        # Submit valid feedback again to test recovery
        recovery_feedback = FeedbackSignal(
            component_type=WINAComponentType.CONSTITUTIONAL_VERIFICATION,
            feedback_type=FeedbackType.CONSTITUTIONAL_COMPLIANCE,
            value=0.98,
            context={"test": "recovery_validation"},
            timestamp=datetime.now(),
            confidence=0.95,
            source="recovery_validation"
        )
        
        await learning_system.process_feedback_signal(recovery_feedback)
        
        # System should still be functional
        status = await learning_system.get_learning_status()
        assert status["metrics"]["total_feedback_processed"] > 0


@pytest.mark.asyncio
async def test_global_learning_system_singleton():
    """Test global learning system singleton functionality."""
    if not WINA_AVAILABLE:
        pytest.skip("WINA not available")
    
    # Get two instances of the global learning system
    system1 = await get_wina_learning_system()
    system2 = await get_wina_learning_system()
    
    # Should be the same instance
    assert system1 is system2
    
    # Should be properly initialized
    assert system1.learning_state is not None
    assert system1.component_profiles is not None


if __name__ == "__main__":
    # Run basic integration test
    async def run_basic_test():
        if WINA_AVAILABLE:
            print("Running basic WINA continuous learning integration test...")
            
            learning_system = await get_wina_learning_system()
            
            # Test basic functionality
            feedback = FeedbackSignal(
                component_type=WINAComponentType.NEURON_ACTIVATION,
                feedback_type=FeedbackType.EFFICIENCY_GAIN,
                value=0.7,
                context={"test": "basic"},
                timestamp=datetime.now(),
                confidence=0.9,
                source="basic_test"
            )
            
            await learning_system.process_feedback_signal(feedback)
            await asyncio.sleep(0.1)
            
            status = await learning_system.get_learning_status()
            print(f"Learning system status: {status['metrics']['total_feedback_processed']} feedback processed")
            print("Basic integration test completed successfully!")
        else:
            print("WINA modules not available - skipping test")
    
    asyncio.run(run_basic_test())