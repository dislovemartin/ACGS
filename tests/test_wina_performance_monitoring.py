"""
Tests for WINA Performance Monitoring System

Comprehensive test suite for validating WINA performance monitoring,
metrics collection, dashboard functionality, and API endpoints.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from src.backend.shared.wina.performance_monitoring import (
    WINAPerformanceCollector,
    WINANeuronActivationMetrics,
    WINASVDTransformationMetrics,
    WINADynamicGatingMetrics,
    WINAConstitutionalComplianceMetrics,
    WINALearningFeedbackMetrics,
    WINAIntegrationMetrics,
    WINASystemHealthMetrics,
    WINAComponentType,
    WINAMonitoringLevel,
    get_wina_performance_collector
)

from src.backend.shared.wina.dashboard import (
    WINADashboard,
    get_wina_dashboard
)


class TestWINAPerformanceCollector:
    """Test cases for WINAPerformanceCollector."""
    
    @pytest.fixture
    async def collector(self):
        """Create a test performance collector."""
        collector = WINAPerformanceCollector(monitoring_level=WINAMonitoringLevel.DETAILED)
        await collector.start_monitoring()
        yield collector
        await collector.stop_monitoring()
    
    @pytest.fixture
    def sample_neuron_metrics(self):
        """Create sample neuron activation metrics."""
        return WINANeuronActivationMetrics(
            timestamp=datetime.now(timezone.utc),
            component_id="test_component",
            total_neurons=1000,
            active_neurons=650,
            activation_ratio=0.65,
            sparsity_ratio=0.35,
            energy_savings_ratio=0.4,
            gflops_before=100.0,
            gflops_after=60.0,
            optimization_type="dynamic_pruning"
        )
    
    @pytest.fixture
    def sample_svd_metrics(self):
        """Create sample SVD transformation metrics."""
        return WINASVDTransformationMetrics(
            timestamp=datetime.now(timezone.utc),
            component_id="test_svd",
            original_rank=512,
            reduced_rank=256,
            compression_ratio=0.5,
            reconstruction_error=0.02,
            transformation_time_ms=150.0,
            memory_savings_mb=128.0,
            computational_savings_ratio=0.45
        )
    
    @pytest.fixture
    def sample_constitutional_metrics(self):
        """Create sample constitutional compliance metrics."""
        return WINAConstitutionalComplianceMetrics(
            timestamp=datetime.now(timezone.utc),
            component_id="test_constitutional",
            compliance_score=0.96,
            violations_detected=1,
            principles_evaluated=["fairness", "transparency", "accountability"],
            compliance_details={"fairness": 0.98, "transparency": 0.95, "accountability": 0.95}
        )
    
    async def test_collector_initialization(self):
        """Test collector initialization."""
        collector = WINAPerformanceCollector()
        
        assert collector.monitoring_level == WINAMonitoringLevel.BASIC
        assert not collector.monitoring_active
        assert collector.collection_interval == 10.0
        assert len(collector.neuron_activation_metrics) == 0
    
    async def test_start_stop_monitoring(self, collector):
        """Test starting and stopping monitoring."""
        assert collector.monitoring_active
        
        await collector.stop_monitoring()
        assert not collector.monitoring_active
        
        await collector.start_monitoring()
        assert collector.monitoring_active
    
    async def test_record_neuron_activation_metrics(self, collector, sample_neuron_metrics):
        """Test recording neuron activation metrics."""
        await collector.record_neuron_activation_metrics(sample_neuron_metrics)
        
        assert len(collector.neuron_activation_metrics) == 1
        recorded_metric = collector.neuron_activation_metrics[0]
        assert recorded_metric.component_id == "test_component"
        assert recorded_metric.activation_ratio == 0.65
        assert recorded_metric.energy_savings_ratio == 0.4
    
    async def test_record_svd_transformation_metrics(self, collector, sample_svd_metrics):
        """Test recording SVD transformation metrics."""
        await collector.record_svd_transformation_metrics(sample_svd_metrics)
        
        assert len(collector.svd_transformation_metrics) == 1
        recorded_metric = collector.svd_transformation_metrics[0]
        assert recorded_metric.component_id == "test_svd"
        assert recorded_metric.compression_ratio == 0.5
        assert recorded_metric.computational_savings_ratio == 0.45
    
    async def test_record_constitutional_compliance_metrics(self, collector, sample_constitutional_metrics):
        """Test recording constitutional compliance metrics."""
        await collector.record_constitutional_compliance_metrics(sample_constitutional_metrics)
        
        assert len(collector.constitutional_compliance_metrics) == 1
        recorded_metric = collector.constitutional_compliance_metrics[0]
        assert recorded_metric.component_id == "test_constitutional"
        assert recorded_metric.compliance_score == 0.96
        assert recorded_metric.violations_detected == 1
    
    async def test_get_real_time_metrics(self, collector, sample_neuron_metrics, sample_svd_metrics):
        """Test getting real-time metrics."""
        # Record some metrics
        await collector.record_neuron_activation_metrics(sample_neuron_metrics)
        await collector.record_svd_transformation_metrics(sample_svd_metrics)
        
        real_time_metrics = await collector.get_real_time_metrics()
        
        assert "neuron_activation" in real_time_metrics
        assert "svd_transformation" in real_time_metrics
        assert "overall_performance" in real_time_metrics
        assert "system_health" in real_time_metrics
        
        # Check neuron activation metrics
        neuron_metrics = real_time_metrics["neuron_activation"]
        assert neuron_metrics["avg_activation_ratio"] == 0.65
        assert neuron_metrics["avg_energy_savings"] == 0.4
        
        # Check overall performance
        overall = real_time_metrics["overall_performance"]
        assert "gflops_reduction_achieved" in overall
        assert "performance_targets_met" in overall
    
    async def test_performance_report_generation(self, collector, sample_neuron_metrics):
        """Test performance report generation."""
        # Record some metrics
        await collector.record_neuron_activation_metrics(sample_neuron_metrics)
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        
        report = await collector.get_performance_report(start_time, end_time)
        
        assert report.start_time == start_time
        assert report.end_time == end_time
        assert report.total_operations >= 1
        assert 0.0 <= report.overall_gflops_reduction <= 1.0
        assert len(report.component_performance) >= 0
    
    async def test_alert_generation(self, collector):
        """Test alert generation for anomalies."""
        # Create metrics that should trigger alerts
        poor_metrics = WINANeuronActivationMetrics(
            timestamp=datetime.now(timezone.utc),
            component_id="failing_component",
            total_neurons=1000,
            active_neurons=950,  # High activation (poor optimization)
            activation_ratio=0.95,
            sparsity_ratio=0.05,
            energy_savings_ratio=0.1,  # Low energy savings
            gflops_before=100.0,
            gflops_after=90.0,  # Minimal reduction
            optimization_type="failed_pruning"
        )
        
        await collector.record_neuron_activation_metrics(poor_metrics)
        
        # Check if alerts were generated
        assert len(collector.alerts_history) > 0
        
        # Find relevant alert
        activation_alerts = [
            alert for alert in collector.alerts_history
            if "activation" in alert["message"].lower()
        ]
        assert len(activation_alerts) > 0
    
    async def test_metrics_cleanup(self, collector):
        """Test automatic cleanup of old metrics."""
        # Create old metrics
        old_timestamp = datetime.now(timezone.utc) - timedelta(hours=25)  # Older than retention
        old_metrics = WINANeuronActivationMetrics(
            timestamp=old_timestamp,
            component_id="old_component",
            total_neurons=1000,
            active_neurons=500,
            activation_ratio=0.5,
            sparsity_ratio=0.5,
            energy_savings_ratio=0.3,
            gflops_before=100.0,
            gflops_after=70.0,
            optimization_type="pruning"
        )
        
        await collector.record_neuron_activation_metrics(old_metrics)
        initial_count = len(collector.neuron_activation_metrics)
        
        # Trigger cleanup
        await collector._cleanup_old_metrics()
        
        # Old metrics should be removed
        assert len(collector.neuron_activation_metrics) < initial_count
    
    async def test_prometheus_metrics_export(self, collector, sample_neuron_metrics):
        """Test Prometheus metrics export."""
        await collector.record_neuron_activation_metrics(sample_neuron_metrics)
        
        prometheus_metrics = await collector.get_prometheus_metrics()
        
        assert isinstance(prometheus_metrics, str)
        assert "wina_neuron_activation_ratio" in prometheus_metrics
        assert "wina_energy_savings_ratio" in prometheus_metrics
        assert "wina_gflops_reduction" in prometheus_metrics
    
    async def test_component_metrics_tracking(self, collector):
        """Test component-specific metrics tracking."""
        component_type = WINAComponentType.NEURON_ACTIVATION
        operation_data = {
            "operation_type": "pruning",
            "duration_ms": 150.0,
            "success": True,
            "metadata": {"pruning_ratio": 0.3}
        }
        
        await collector.record_component_operation(component_type, operation_data)
        
        assert component_type in collector.component_metrics
        assert len(collector.component_metrics[component_type]) == 1
        
        recorded_operation = collector.component_metrics[component_type][0]
        assert recorded_operation["operation_type"] == "pruning"
        assert recorded_operation["success"] is True
    
    async def test_get_wina_performance_collector_singleton(self):
        """Test singleton behavior of get_wina_performance_collector."""
        collector1 = await get_wina_performance_collector()
        collector2 = await get_wina_performance_collector()
        
        assert collector1 is collector2
        assert isinstance(collector1, WINAPerformanceCollector)


class TestWINADashboard:
    """Test cases for WINADashboard."""
    
    @pytest.fixture
    async def dashboard(self):
        """Create a test dashboard with mocked collector."""
        with patch('src.backend.shared.wina.dashboard.get_wina_performance_collector') as mock_get_collector:
            mock_collector = AsyncMock(spec=WINAPerformanceCollector)
            mock_collector.monitoring_active = True
            mock_collector.alerts_history = []
            mock_collector.neuron_activation_metrics = []
            mock_collector.constitutional_compliance_metrics = []
            mock_collector.component_metrics = {component: [] for component in WINAComponentType}
            mock_collector.system_health_metrics = []
            mock_collector.integration_metrics = []
            
            # Mock real-time metrics
            mock_collector.get_real_time_metrics.return_value = {
                "overall_performance": {
                    "optimization_status": "active",
                    "performance_targets_met": True,
                    "gflops_reduction_achieved": 0.55,
                    "accuracy_retention": 0.96,
                    "constitutional_compliance_rate": 0.94,
                    "efficiency_score": 0.85
                },
                "system_health": {
                    "status": "healthy",
                    "availability": 0.99,
                    "error_rate": 2.5,
                    "throughput": 1000.0,
                    "cpu_utilization": 65.0,
                    "memory_utilization": 70.0
                },
                "neuron_activation": {"avg_activation_ratio": 0.6},
                "svd_transformation": {"avg_compression_ratio": 0.5},
                "dynamic_gating": {"avg_gating_efficiency": 0.8},
                "constitutional_compliance": {"avg_compliance_score": 0.94},
                "learning_feedback": {"adaptation_rate": 0.1},
                "integration_performance": {"avg_latency_ms": 45.0}
            }
            
            # Mock performance report
            mock_report = Mock()
            mock_report.trends = {"gflops": "improving", "accuracy": "stable"}
            mock_report.overall_gflops_reduction = 0.55
            mock_report.overall_accuracy_retention = 0.96
            mock_report.total_operations = 1440
            mock_collector.get_performance_report.return_value = mock_report
            
            mock_get_collector.return_value = mock_collector
            
            dashboard = WINADashboard()
            await dashboard.initialize()
            yield dashboard
    
    async def test_dashboard_initialization(self):
        """Test dashboard initialization."""
        dashboard = WINADashboard()
        
        assert dashboard.performance_collector is None
        assert dashboard.refresh_interval == 5
        assert dashboard.chart_data_points == 100
        assert dashboard.alert_display_limit == 50
    
    async def test_get_dashboard_data(self, dashboard):
        """Test getting comprehensive dashboard data."""
        dashboard_data = await dashboard.get_dashboard_data()
        
        assert "timestamp" in dashboard_data
        assert "overview" in dashboard_data
        assert "performance_metrics" in dashboard_data
        assert "component_status" in dashboard_data
        assert "alerts" in dashboard_data
        assert "charts" in dashboard_data
        assert "health_indicators" in dashboard_data
        assert "trends" in dashboard_data
        assert "recommendations" in dashboard_data
    
    async def test_system_overview(self, dashboard):
        """Test system overview generation."""
        overview = await dashboard._get_system_overview()
        
        assert overview["wina_optimization_status"] == "active"
        assert overview["performance_targets_met"] is True
        assert overview["gflops_reduction"]["current"] == 0.55
        assert overview["gflops_reduction"]["status"] == "optimal"
        assert overview["accuracy_retention"]["current"] == 0.96
        assert overview["constitutional_compliance"]["current"] == 0.94
        assert overview["monitoring_active"] is True
    
    async def test_performance_metrics(self, dashboard):
        """Test performance metrics retrieval."""
        metrics = await dashboard._get_performance_metrics()
        
        assert "neuron_activation" in metrics
        assert "svd_transformation" in metrics
        assert "dynamic_gating" in metrics
        assert "constitutional_compliance" in metrics
        assert "learning_feedback" in metrics
        assert "integration_performance" in metrics
        assert metrics["efficiency_score"] == 0.85
    
    async def test_component_status(self, dashboard):
        """Test component status generation."""
        status = await dashboard._get_component_status()
        
        # Should have status for all component types
        for component in WINAComponentType:
            assert component.value in status
            component_status = status[component.value]
            assert "status" in component_status
            assert "success_rate" in component_status
            assert "avg_duration_ms" in component_status
            assert "recent_operations" in component_status
    
    async def test_alerts_summary(self, dashboard):
        """Test alerts summary generation."""
        alerts_summary = await dashboard._get_alerts_summary()
        
        assert "total_alerts_24h" in alerts_summary
        assert "critical_alerts_24h" in alerts_summary
        assert "warning_alerts_24h" in alerts_summary
        assert "active_alerts" in alerts_summary
        assert "recent_alerts" in alerts_summary
        assert "alert_trend" in alerts_summary
    
    async def test_health_indicators(self, dashboard):
        """Test health indicators calculation."""
        health = await dashboard._get_health_indicators()
        
        assert "overall_health_score" in health
        assert "health_status" in health
        assert "performance_health_score" in health
        assert "system_health_score" in health
        assert "indicators" in health
        
        # Check individual indicators
        indicators = health["indicators"]
        assert "wina_optimization" in indicators
        assert "system_stability" in indicators
        assert "error_rate" in indicators
        assert "resource_utilization" in indicators
    
    async def test_trends_data(self, dashboard):
        """Test trends data generation."""
        trends = await dashboard._get_trends_data()
        
        assert "performance_trends" in trends
        assert "gflops_reduction_trend" in trends
        assert "accuracy_trend" in trends
        assert "operations_trend" in trends
        
        gflops_trend = trends["gflops_reduction_trend"]
        assert gflops_trend["current"] == 0.55
        assert gflops_trend["status"] == "on_target"
    
    async def test_recommendations(self, dashboard):
        """Test recommendations generation."""
        recommendations = await dashboard._get_recommendations()
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
    
    async def test_chart_data_generation(self, dashboard):
        """Test chart data generation."""
        charts = await dashboard._get_chart_data()
        
        assert "gflops_reduction_chart" in charts
        assert "accuracy_retention_chart" in charts
        assert "component_performance_chart" in charts
        assert "system_health_chart" in charts
        assert "integration_latency_chart" in charts
    
    async def test_export_dashboard_data(self, dashboard):
        """Test dashboard data export."""
        # Test JSON export
        json_export = await dashboard.export_dashboard_data("json")
        assert isinstance(json_export, str)
        assert "timestamp" in json_export
        
        # Test CSV export
        csv_export = await dashboard.export_dashboard_data("csv")
        assert isinstance(csv_export, str)
        assert "metric,value,timestamp" in csv_export
        
        # Test invalid format
        with pytest.raises(ValueError):
            await dashboard.export_dashboard_data("invalid")
    
    async def test_component_details(self, dashboard):
        """Test component details retrieval."""
        details = await dashboard.get_component_details("neuron_activation")
        
        assert details["component_type"] == "neuron_activation"
        assert "status" in details
        
        # Test invalid component
        invalid_details = await dashboard.get_component_details("invalid_component")
        assert "error" in invalid_details
    
    async def test_dashboard_caching(self, dashboard):
        """Test dashboard data caching."""
        # First call should populate cache
        data1 = await dashboard.get_dashboard_data()
        cache_time1 = dashboard.last_cache_update
        
        # Second call should use cache
        data2 = await dashboard.get_dashboard_data()
        cache_time2 = dashboard.last_cache_update
        
        assert cache_time1 == cache_time2
        assert data1 == data2
        
        # Force refresh should update cache
        data3 = await dashboard.get_dashboard_data(refresh_cache=True)
        cache_time3 = dashboard.last_cache_update
        
        assert cache_time3 > cache_time1
    
    async def test_get_wina_dashboard_singleton(self):
        """Test singleton behavior of get_wina_dashboard."""
        with patch('src.backend.shared.wina.dashboard.get_wina_performance_collector'):
            dashboard1 = await get_wina_dashboard()
            dashboard2 = await get_wina_dashboard()
            
            assert dashboard1 is dashboard2
            assert isinstance(dashboard1, WINADashboard)


class TestWINAMetricsDataClasses:
    """Test cases for WINA metrics data classes."""
    
    def test_neuron_activation_metrics_creation(self):
        """Test neuron activation metrics data class."""
        metrics = WINANeuronActivationMetrics(
            timestamp=datetime.now(timezone.utc),
            component_id="test",
            total_neurons=1000,
            active_neurons=600,
            activation_ratio=0.6,
            sparsity_ratio=0.4,
            energy_savings_ratio=0.35,
            gflops_before=100.0,
            gflops_after=65.0,
            optimization_type="pruning"
        )
        
        assert metrics.total_neurons == 1000
        assert metrics.activation_ratio == 0.6
        assert metrics.energy_savings_ratio == 0.35
    
    def test_svd_transformation_metrics_creation(self):
        """Test SVD transformation metrics data class."""
        metrics = WINASVDTransformationMetrics(
            timestamp=datetime.now(timezone.utc),
            component_id="test",
            original_rank=512,
            reduced_rank=256,
            compression_ratio=0.5,
            reconstruction_error=0.02,
            transformation_time_ms=100.0,
            memory_savings_mb=64.0,
            computational_savings_ratio=0.4
        )
        
        assert metrics.original_rank == 512
        assert metrics.compression_ratio == 0.5
        assert metrics.computational_savings_ratio == 0.4
    
    def test_constitutional_compliance_metrics_creation(self):
        """Test constitutional compliance metrics data class."""
        metrics = WINAConstitutionalComplianceMetrics(
            timestamp=datetime.now(timezone.utc),
            component_id="test",
            compliance_score=0.95,
            violations_detected=0,
            principles_evaluated=["fairness", "transparency"],
            compliance_details={"fairness": 0.96, "transparency": 0.94}
        )
        
        assert metrics.compliance_score == 0.95
        assert metrics.violations_detected == 0
        assert len(metrics.principles_evaluated) == 2


@pytest.mark.asyncio
class TestWINAPerformanceIntegration:
    """Integration tests for WINA performance monitoring."""
    
    async def test_end_to_end_monitoring_flow(self):
        """Test complete monitoring flow from metrics collection to dashboard display."""
        # Initialize collector
        collector = WINAPerformanceCollector(monitoring_level=WINAMonitoringLevel.DETAILED)
        await collector.start_monitoring()
        
        try:
            # Create sample metrics
            neuron_metrics = WINANeuronActivationMetrics(
                timestamp=datetime.now(timezone.utc),
                component_id="integration_test",
                total_neurons=2000,
                active_neurons=1200,
                activation_ratio=0.6,
                sparsity_ratio=0.4,
                energy_savings_ratio=0.45,
                gflops_before=200.0,
                gflops_after=110.0,
                optimization_type="integration_test"
            )
            
            constitutional_metrics = WINAConstitutionalComplianceMetrics(
                timestamp=datetime.now(timezone.utc),
                component_id="integration_test",
                compliance_score=0.97,
                violations_detected=0,
                principles_evaluated=["fairness", "transparency", "accountability"],
                compliance_details={"fairness": 0.98, "transparency": 0.96, "accountability": 0.97}
            )
            
            # Record metrics
            await collector.record_neuron_activation_metrics(neuron_metrics)
            await collector.record_constitutional_compliance_metrics(constitutional_metrics)
            
            # Get real-time metrics
            real_time_metrics = await collector.get_real_time_metrics()
            assert "neuron_activation" in real_time_metrics
            assert "constitutional_compliance" in real_time_metrics
            
            # Generate performance report
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=30)
            report = await collector.get_performance_report(start_time, end_time)
            
            assert report.total_operations >= 2
            assert 0.0 <= report.overall_gflops_reduction <= 1.0
            
            # Test Prometheus export
            prometheus_metrics = await collector.get_prometheus_metrics()
            assert "wina_neuron_activation_ratio" in prometheus_metrics
            assert "wina_constitutional_compliance_score" in prometheus_metrics
            
        finally:
            await collector.stop_monitoring()
    
    async def test_dashboard_with_real_collector(self):
        """Test dashboard with actual collector integration."""
        # Initialize real collector with data
        collector = WINAPerformanceCollector()
        await collector.start_monitoring()
        
        try:
            # Add some test data
            test_metrics = WINANeuronActivationMetrics(
                timestamp=datetime.now(timezone.utc),
                component_id="dashboard_test",
                total_neurons=1500,
                active_neurons=900,
                activation_ratio=0.6,
                sparsity_ratio=0.4,
                energy_savings_ratio=0.5,
                gflops_before=150.0,
                gflops_after=75.0,
                optimization_type="dashboard_test"
            )
            
            await collector.record_neuron_activation_metrics(test_metrics)
            
            # Create dashboard with real collector
            with patch('src.backend.shared.wina.dashboard.get_wina_performance_collector', return_value=collector):
                dashboard = WINADashboard()
                await dashboard.initialize()
                
                # Get dashboard data
                dashboard_data = await dashboard.get_dashboard_data()
                
                assert "overview" in dashboard_data
                assert "performance_metrics" in dashboard_data
                assert dashboard_data["overview"]["monitoring_active"] is True
                
        finally:
            await collector.stop_monitoring()


if __name__ == "__main__":
    pytest.main([__file__])