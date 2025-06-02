"""
Integration Tests for WINA Performance Monitoring in EC Service

This test suite verifies the complete integration of WINA performance monitoring
with the EC oversight coordinator and API endpoints.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

# We'll use relative imports for the EC service components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from ec_service.app.main import app, get_wina_coordinator, get_wina_performance_collector
from ec_service.app.core.wina_oversight_coordinator import WINAECOversightCoordinator
from shared.wina.performance_monitoring import (
    WINAPerformanceCollector,
    WINAMonitoringLevel,
    WINAComponentType,
    WINANeuronActivationMetrics,
    WINADynamicGatingMetrics,
    WINAConstitutionalComplianceMetrics,
    WINASystemHealthMetrics,
    WINAIntegrationPerformanceMetrics
)
from shared.wina.performance_api import set_collector_getter


class TestWINAPerformanceIntegration:
    """Test suite for WINA performance monitoring integration."""

    @pytest.fixture
    async def mock_coordinator(self):
        """Create a mock WINA oversight coordinator with performance monitoring."""
        coordinator = Mock(spec=WINAECOversightCoordinator)
        coordinator.enable_wina = True
        coordinator.performance_collector = WINAPerformanceCollector(
            monitoring_level=WINAMonitoringLevel.COMPREHENSIVE
        )
        
        # Mock constitutional principles
        coordinator.constitutional_principles = {
            "democratic_oversight": {"weight": 0.8, "compliance_threshold": 0.9},
            "transparency": {"weight": 0.9, "compliance_threshold": 0.85},
            "efficiency": {"weight": 0.7, "compliance_threshold": 0.8}
        }
        
        # Mock async methods
        coordinator.initialize_constitutional_principles = AsyncMock()
        coordinator._perform_health_check = AsyncMock()
        coordinator.verify_constitutional_compliance = AsyncMock(return_value={
            "compliant": True,
            "score": 0.95,
            "violations": [],
            "principles_evaluated": 3
        })
        coordinator.apply_wina_optimization = AsyncMock(return_value={
            "optimization_applied": True,
            "gflops_reduction": 0.45,
            "accuracy_retention": 0.97
        })
        coordinator.record_learning_feedback = AsyncMock()
        
        await coordinator.performance_collector.start_monitoring()
        return coordinator

    @pytest.fixture
    def test_client(self, mock_coordinator):
        """Create test client with mocked coordinator."""
        
        def mock_get_coordinator():
            return mock_coordinator
        
        def mock_get_performance_collector():
            return mock_coordinator.performance_collector
        
        # Override the dependency functions
        app.dependency_overrides[get_wina_coordinator] = mock_get_coordinator
        
        # Configure the performance API
        set_collector_getter(mock_get_performance_collector)
        
        client = TestClient(app)
        
        yield client
        
        # Cleanup
        app.dependency_overrides.clear()

    def test_health_endpoint_includes_performance_monitoring(self, test_client):
        """Test that health endpoint includes performance monitoring status."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic health response
        assert data["status"] == "healthy"
        assert data["service"] == "evolutionary_computation"
        assert "wina_coordinator" in data
        
        # Verify performance monitoring features
        assert "performance_monitoring" in data
        performance_info = data["performance_monitoring"]
        
        assert "collector_available" in performance_info
        assert "monitoring_active" in performance_info
        assert "monitoring_level" in performance_info
        
        # Verify features include performance monitoring capabilities
        features = data["features"]
        assert features["performance_monitoring"] is True
        assert features["wina_performance_api"] is True
        assert features["real_time_metrics"] is True

    def test_root_endpoint_includes_performance_api_info(self, test_client):
        """Test that root endpoint includes performance API information."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify API endpoints include performance monitoring
        assert "api_endpoints" in data
        endpoints = data["api_endpoints"]
        assert "wina_performance" in endpoints
        assert endpoints["wina_performance"] == "/api/v1/wina/performance/*"
        
        # Verify features include performance capabilities
        features = data["features"]
        performance_features = [
            "Comprehensive WINA performance metrics",
            "REST API for performance data access",
            "Prometheus metrics export",
            "Performance dashboard and alerts"
        ]
        
        for feature in performance_features:
            assert feature in features

    def test_performance_api_health_endpoint(self, test_client):
        """Test WINA performance API health endpoint."""
        response = test_client.get("/api/v1/wina/performance/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify health response structure
        assert "status" in data
        assert "timestamp" in data
        assert "monitoring_active" in data
        assert "monitoring_level" in data
        assert "system_health" in data
        assert "performance_summary" in data
        assert "components_monitored" in data

    def test_performance_api_realtime_metrics(self, test_client):
        """Test WINA performance API real-time metrics endpoint."""
        response = test_client.get("/api/v1/wina/performance/metrics/realtime")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify real-time metrics structure
        assert isinstance(data, dict)
        # The exact structure depends on the implementation,
        # but we should get a valid response

    def test_performance_api_configuration(self, test_client):
        """Test WINA performance API configuration endpoint."""
        response = test_client.get("/api/v1/wina/performance/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify configuration response
        assert "monitoring_level" in data
        assert "monitoring_active" in data
        assert "collection_interval_seconds" in data
        assert "components_monitored" in data
        assert "metrics_storage_limits" in data
        
        # Verify monitoring level
        assert data["monitoring_level"] == "comprehensive"

    @pytest.mark.asyncio
    async def test_coordinator_performance_monitoring_integration(self, mock_coordinator):
        """Test that the coordinator properly integrates with performance monitoring."""
        collector = mock_coordinator.performance_collector
        
        # Verify collector is properly configured
        assert collector.monitoring_level == WINAMonitoringLevel.COMPREHENSIVE
        assert collector.monitoring_active
        
        # Test recording various metrics
        
        # 1. System health metrics
        system_metrics = WINASystemHealthMetrics(
            cpu_utilization_percent=75.5,
            memory_utilization_percent=82.3,
            gpu_utilization_percent=68.9,
            throughput_ops_per_second=1250.0,
            error_rate_percent=0.1,
            availability_percent=99.9,
            response_time_p95_ms=45.2,
            concurrent_operations=12,
            timestamp=datetime.now(timezone.utc)
        )
        await collector.record_system_health_metrics(system_metrics)
        
        # 2. Constitutional compliance metrics
        compliance_metrics = WINAConstitutionalComplianceMetrics(
            component_type="ec_oversight",
            principles_evaluated=3,
            compliance_score=0.95,
            violations_detected=0,
            compliance_check_time_ms=12.5,
            constitutional_overhead_ratio=0.08,
            principle_adherence_breakdown={
                "democratic_oversight": 0.96,
                "transparency": 0.94,
                "efficiency": 0.95
            },
            remediation_actions_taken=0,
            timestamp=datetime.now(timezone.utc)
        )
        await collector.record_constitutional_compliance_metrics(compliance_metrics)
        
        # 3. Integration performance metrics
        integration_metrics = WINAIntegrationPerformanceMetrics(
            integration_type="ec_wina_optimization",
            source_component="ec_coordinator",
            target_component="wina_core",
            integration_latency_ms=15.3,
            data_transfer_mb=2.4,
            synchronization_overhead_ms=3.1,
            integration_success_rate=0.99,
            error_count=0,
            performance_improvement_ratio=0.42,
            timestamp=datetime.now(timezone.utc)
        )
        await collector.record_integration_performance_metrics(integration_metrics)
        
        # 4. Neuron activation metrics
        neuron_metrics = WINANeuronActivationMetrics(
            layer_name="transformer_layer_12",
            total_neurons=4096,
            active_neurons=2048,
            deactivated_neurons=2048,
            activation_ratio=0.5,
            activation_scores_mean=0.72,
            activation_scores_std=0.18,
            performance_impact_ms=8.5,
            energy_savings_ratio=0.35,
            timestamp=datetime.now(timezone.utc)
        )
        await collector.record_neuron_activation_metrics(neuron_metrics)
        
        # 5. Dynamic gating metrics
        gating_metrics = WINADynamicGatingMetrics(
            gate_id="attention_gate_3",
            gating_strategy="adaptive_threshold",
            threshold_value=0.15,
            gates_activated=256,
            gates_total=512,
            gating_efficiency=0.5,
            decision_latency_ms=2.1,
            accuracy_impact=-0.002,
            resource_savings=0.28,
            timestamp=datetime.now(timezone.utc)
        )
        await collector.record_dynamic_gating_metrics(gating_metrics)
        
        # Verify metrics were recorded
        assert len(collector.system_health_metrics) > 0
        assert len(collector.constitutional_compliance_metrics) > 0
        assert len(collector.integration_performance_metrics) > 0
        assert len(collector.neuron_activation_metrics) > 0
        assert len(collector.dynamic_gating_metrics) > 0

    def test_performance_metrics_recording_endpoints(self, test_client):
        """Test API endpoints for recording performance metrics."""
        
        # Test neuron activation metrics recording
        neuron_data = {
            "layer_name": "test_layer",
            "total_neurons": 1000,
            "active_neurons": 500,
            "deactivated_neurons": 500,
            "activation_ratio": 0.5,
            "activation_scores_mean": 0.7,
            "activation_scores_std": 0.2,
            "performance_impact_ms": 10.0,
            "energy_savings_ratio": 0.3
        }
        
        response = test_client.post("/api/v1/wina/performance/metrics/neuron-activation", json=neuron_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Test constitutional compliance metrics recording
        compliance_data = {
            "component_type": "test_component",
            "principles_evaluated": 3,
            "compliance_score": 0.95,
            "violations_detected": 0,
            "compliance_check_time_ms": 5.0,
            "constitutional_overhead_ratio": 0.1,
            "principle_adherence_breakdown": {
                "principle1": 0.95,
                "principle2": 0.93,
                "principle3": 0.97
            },
            "remediation_actions_taken": 0
        }
        
        response = test_client.post("/api/v1/wina/performance/metrics/constitutional-compliance", json=compliance_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Test system health metrics recording
        health_data = {
            "cpu_utilization_percent": 75.0,
            "memory_utilization_percent": 80.0,
            "gpu_utilization_percent": 70.0,
            "throughput_ops_per_second": 1000.0,
            "error_rate_percent": 0.1,
            "availability_percent": 99.9,
            "response_time_p95_ms": 50.0,
            "concurrent_operations": 10
        }
        
        response = test_client.post("/api/v1/wina/performance/metrics/system-health", json=health_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_performance_monitoring_configuration_update(self, test_client):
        """Test updating performance monitoring configuration."""
        config_data = {
            "monitoring_level": "detailed",
            "collection_interval_seconds": 60,
            "enable_prometheus": True,
            "enable_real_time_alerts": True
        }
        
        response = test_client.post("/api/v1/wina/performance/config", json=config_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_performance_monitoring_start_stop(self, test_client):
        """Test starting and stopping performance monitoring."""
        # Test stop
        response = test_client.post("/api/v1/wina/performance/monitoring/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Test start
        response = test_client.post("/api/v1/wina/performance/monitoring/start")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_prometheus_metrics_export(self, test_client):
        """Test Prometheus metrics export endpoint."""
        response = test_client.get("/api/v1/wina/performance/prometheus")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Verify it's valid Prometheus format (basic check)
        content = response.text
        assert isinstance(content, str)
        assert len(content) > 0

    def test_performance_alerts_endpoint(self, test_client):
        """Test performance alerts retrieval."""
        response = test_client.get("/api/v1/wina/performance/alerts?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "alerts" in data
        assert "total_count" in data
        assert "time_range" in data
        assert isinstance(data["alerts"], list)

    def test_metrics_summary_endpoint(self, test_client):
        """Test metrics summary endpoint."""
        response = test_client.get("/api/v1/wina/performance/metrics/summary?time_range_hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "time_range" in data
        assert "overall_performance" in data
        assert "component_metrics" in data
        assert "integration_metrics" in data
        assert "health_metrics" in data

    @pytest.mark.asyncio
    async def test_end_to_end_oversight_with_monitoring(self, mock_coordinator):
        """Test complete oversight operation with performance monitoring."""
        coordinator = mock_coordinator
        collector = coordinator.performance_collector
        
        # Simulate a complete oversight operation
        
        # 1. Record initial system health
        system_metrics = WINASystemHealthMetrics(
            cpu_utilization_percent=70.0,
            memory_utilization_percent=75.0,
            gpu_utilization_percent=65.0,
            throughput_ops_per_second=1200.0,
            error_rate_percent=0.05,
            availability_percent=99.95,
            response_time_p95_ms=40.0,
            concurrent_operations=8,
            timestamp=datetime.now(timezone.utc)
        )
        await collector.record_system_health_metrics(system_metrics)
        
        # 2. Perform constitutional compliance check
        compliance_result = await coordinator.verify_constitutional_compliance("test_decision")
        compliance_metrics = WINAConstitutionalComplianceMetrics(
            component_type="ec_oversight",
            principles_evaluated=compliance_result["principles_evaluated"],
            compliance_score=compliance_result["score"],
            violations_detected=len(compliance_result["violations"]),
            compliance_check_time_ms=8.5,
            constitutional_overhead_ratio=0.06,
            principle_adherence_breakdown={
                "democratic_oversight": 0.96,
                "transparency": 0.94,
                "efficiency": 0.95
            },
            remediation_actions_taken=0,
            timestamp=datetime.now(timezone.utc)
        )
        await collector.record_constitutional_compliance_metrics(compliance_metrics)
        
        # 3. Apply WINA optimization
        optimization_result = await coordinator.apply_wina_optimization("test_input")
        
        # Record neuron activation metrics from optimization
        neuron_metrics = WINANeuronActivationMetrics(
            layer_name="optimization_layer",
            total_neurons=2048,
            active_neurons=1024,
            deactivated_neurons=1024,
            activation_ratio=0.5,
            activation_scores_mean=0.75,
            activation_scores_std=0.15,
            performance_impact_ms=12.0,
            energy_savings_ratio=optimization_result["gflops_reduction"] * 0.8,
            timestamp=datetime.now(timezone.utc)
        )
        await collector.record_neuron_activation_metrics(neuron_metrics)
        
        # 4. Record integration performance
        integration_metrics = WINAIntegrationPerformanceMetrics(
            integration_type="oversight_optimization",
            source_component="ec_coordinator",
            target_component="wina_optimizer",
            integration_latency_ms=18.5,
            data_transfer_mb=1.8,
            synchronization_overhead_ms=4.2,
            integration_success_rate=0.98,
            error_count=0,
            performance_improvement_ratio=optimization_result["gflops_reduction"],
            timestamp=datetime.now(timezone.utc)
        )
        await collector.record_integration_performance_metrics(integration_metrics)
        
        # 5. Verify all metrics were recorded
        assert len(collector.system_health_metrics) >= 1
        assert len(collector.constitutional_compliance_metrics) >= 1
        assert len(collector.neuron_activation_metrics) >= 1
        assert len(collector.integration_performance_metrics) >= 1
        
        # 6. Generate performance report
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        
        report = await collector.get_performance_report(start_time, end_time)
        
        # Verify report contains expected data
        assert report.total_operations > 0
        assert report.overall_gflops_reduction >= 0
        assert report.overall_accuracy_retention >= 0
        assert report.constitutional_compliance_rate >= 0
        assert len(report.component_metrics) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])