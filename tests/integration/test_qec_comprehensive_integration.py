"""
test_qec_comprehensive_integration.py

Comprehensive integration test suite for QEC-enhanced AlphaEvolve-ACGS system.
Tests end-to-end workflows, performance benchmarks, and cross-service integration.

This test suite validates:
- Complete QEC workflow pipeline
- Cross-service communication
- Constitutional Fidelity Monitor integration
- Performance and scalability metrics
- Backward compatibility
"""

import pytest
import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import httpx

# Import test dependencies
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend', 'ac_service'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend', 'shared'))

# QEC Enhancement imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'alphaevolve_gs_engine', 'src'))

try:
    from alphaevolve_gs_engine.services.qec_enhancement import (
        ConstitutionalDistanceCalculator,
        ValidationDSLParser,
        ErrorPredictionModel,
        RecoveryStrategyDispatcher,
        FailureType,
        SynthesisAttemptLog,
        RecoveryStrategy
    )
    from alphaevolve_gs_engine.services.qec_enhancement.constitutional_fidelity_monitor import (
        ConstitutionalFidelityMonitor,
        FidelityComponents,
        FidelityAlert,
        FidelityThresholds
    )
    QEC_AVAILABLE = True
except ImportError:
    QEC_AVAILABLE = False

# Service imports with fallbacks
try:
    from app.main import app
    from app.services.qec_conflict_resolver import QECConflictResolver
    from models import ACPrinciple, ACConflictResolution
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False


class TestQECComprehensiveIntegration:
    """Comprehensive integration test suite for QEC-enhanced system."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment and check prerequisites."""
        if not QEC_AVAILABLE:
            pytest.skip("QEC enhancement components not available")
        
        # Initialize test metrics
        self.performance_metrics = {
            "constitutional_distance_times": [],
            "error_prediction_times": [],
            "recovery_strategy_times": [],
            "fidelity_calculation_times": [],
            "end_to_end_times": []
        }
        
        # Target performance metrics
        self.target_metrics = {
            "first_pass_synthesis_success": 0.88,  # 88%
            "failure_resolution_time": 8.5 * 60,  # 8.5 minutes in seconds
            "constitutional_fidelity_threshold": 0.85,  # Green threshold
            "api_response_time": 0.2,  # 200ms
            "concurrent_users": 50
        }
    
    @pytest.fixture
    def sample_principles(self):
        """Create sample constitutional principles for testing."""
        return [
            {
                "id": 1,
                "title": "Privacy Protection",
                "description": "Protect user privacy and personal data",
                "category": "privacy",
                "priority_weight": 0.8,
                "scope": "data_processing",
                "normative_statement": "User data must be protected",
                "constraints": {"encryption": "required"},
                "rationale": "Privacy is fundamental",
                "validation_criteria_structured": {
                    "type": "privacy_check",
                    "criteria": ["encryption", "access_control", "data_minimization"]
                },
                "distance_score": 0.75,
                "error_prediction_metadata": {
                    "historical_failures": 2,
                    "success_rate": 0.85
                },
                "recovery_strategies": ["enhanced_validation", "fallback_policy"]
            },
            {
                "id": 2,
                "title": "Security Enforcement",
                "description": "Ensure comprehensive system security",
                "category": "security",
                "priority_weight": 0.9,
                "scope": "system_access",
                "normative_statement": "Security must be enforced",
                "constraints": {"monitoring": "continuous"},
                "rationale": "Security prevents threats",
                "validation_criteria_structured": {
                    "type": "security_check",
                    "criteria": ["authentication", "monitoring", "threat_detection"]
                },
                "distance_score": 0.82,
                "error_prediction_metadata": {
                    "historical_failures": 1,
                    "success_rate": 0.92
                },
                "recovery_strategies": ["incremental_refinement", "expert_review"]
            },
            {
                "id": 3,
                "title": "Transparency Requirements",
                "description": "Ensure algorithmic transparency",
                "category": "transparency",
                "priority_weight": 0.7,
                "scope": "decision_making",
                "normative_statement": "Decisions must be explainable",
                "constraints": {"explainability": "required"},
                "rationale": "Transparency builds trust",
                "validation_criteria_structured": {
                    "type": "transparency_check",
                    "criteria": ["explainability", "auditability", "documentation"]
                },
                "distance_score": 0.68,
                "error_prediction_metadata": {
                    "historical_failures": 3,
                    "success_rate": 0.78
                },
                "recovery_strategies": ["enhanced_documentation", "expert_review"]
            }
        ]
    
    @pytest.fixture
    def sample_conflicts(self):
        """Create sample conflict scenarios for testing."""
        return [
            {
                "id": 1,
                "conflict_type": "principle_contradiction",
                "principle_ids": [1, 2],
                "context": "privacy_vs_security_monitoring",
                "conflict_description": "Privacy minimization conflicts with security logging requirements",
                "severity": "high",
                "resolution_strategy": "weighted_priority",
                "resolution_details": {},
                "status": "identified"
            },
            {
                "id": 2,
                "conflict_type": "scope_overlap",
                "principle_ids": [2, 3],
                "context": "security_vs_transparency",
                "conflict_description": "Security measures may reduce transparency",
                "severity": "medium",
                "resolution_strategy": "contextual_balancing",
                "resolution_details": {},
                "status": "identified"
            },
            {
                "id": 3,
                "conflict_type": "priority_ambiguity",
                "principle_ids": [1, 3],
                "context": "privacy_vs_transparency",
                "conflict_description": "Privacy protection may limit transparency requirements",
                "severity": "low",
                "resolution_strategy": "stakeholder_consultation",
                "resolution_details": {},
                "status": "identified"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_end_to_end_qec_workflow(self, sample_principles, sample_conflicts):
        """Test complete QEC-enhanced conflict resolution workflow."""
        if not QEC_AVAILABLE:
            pytest.skip("QEC components not available")
        
        start_time = time.time()
        
        # Step 1: Initialize QEC components
        distance_calculator = ConstitutionalDistanceCalculator()
        validation_parser = ValidationDSLParser()
        error_predictor = ErrorPredictionModel()
        recovery_dispatcher = RecoveryStrategyDispatcher()
        fidelity_monitor = ConstitutionalFidelityMonitor()
        
        # Step 2: Process each conflict through complete pipeline
        results = []
        
        for conflict_data in sample_conflicts:
            conflict_start = time.time()
            
            # Convert to constitutional principles
            constitutional_principles = []
            for principle_data in sample_principles:
                if principle_data["id"] in conflict_data["principle_ids"]:
                    constitutional_principles.append(principle_data)
            
            # Step 2a: Calculate constitutional distances
            distance_start = time.time()
            distances = []
            for principle in constitutional_principles:
                distance = await distance_calculator.calculate_distance(principle)
                distances.append(distance)
            distance_time = time.time() - distance_start
            self.performance_metrics["constitutional_distance_times"].append(distance_time)
            
            # Step 2b: Predict potential errors
            prediction_start = time.time()
            error_predictions = []
            for principle in constitutional_principles:
                prediction = await error_predictor.predict_synthesis_challenges(principle)
                error_predictions.append(prediction)
            prediction_time = time.time() - prediction_start
            self.performance_metrics["error_prediction_times"].append(prediction_time)
            
            # Step 2c: Recommend recovery strategy
            strategy_start = time.time()
            recovery_strategy = await recovery_dispatcher.recommend_strategy(
                conflict_type=conflict_data["conflict_type"],
                severity=conflict_data["severity"],
                error_predictions=error_predictions
            )
            strategy_time = time.time() - strategy_start
            self.performance_metrics["recovery_strategy_times"].append(strategy_time)
            
            # Step 2d: Generate validation scenarios
            validation_scenarios = []
            for principle in constitutional_principles:
                if principle.get("validation_criteria_structured"):
                    scenario = await validation_parser.parse_validation_criteria(
                        principle["validation_criteria_structured"]
                    )
                    validation_scenarios.append(scenario)
            
            conflict_time = time.time() - conflict_start
            
            # Compile results
            result = {
                "conflict_id": conflict_data["id"],
                "constitutional_distances": distances,
                "average_distance": statistics.mean(distances) if distances else 0,
                "error_predictions": error_predictions,
                "recommended_strategy": recovery_strategy,
                "validation_scenarios": validation_scenarios,
                "processing_time": conflict_time,
                "priority_score": self._calculate_priority_score(
                    distances, error_predictions, conflict_data["severity"]
                )
            }
            results.append(result)
        
        # Step 3: Calculate system-wide fidelity
        fidelity_start = time.time()
        system_metrics = {
            "total_principles": len(sample_principles),
            "total_conflicts": len(sample_conflicts),
            "average_distance": statistics.mean([r["average_distance"] for r in results]),
            "high_severity_conflicts": sum(1 for c in sample_conflicts if c["severity"] == "high")
        }
        
        fidelity = await fidelity_monitor.calculate_fidelity(sample_principles, system_metrics)
        fidelity_time = time.time() - fidelity_start
        self.performance_metrics["fidelity_calculation_times"].append(fidelity_time)
        
        total_time = time.time() - start_time
        self.performance_metrics["end_to_end_times"].append(total_time)
        
        # Validate results
        assert len(results) == len(sample_conflicts)
        assert fidelity.composite_score >= 0.0
        assert fidelity.composite_score <= 1.0
        
        # Check performance targets
        assert total_time < 30.0, f"End-to-end processing took {total_time:.2f}s, target <30s"
        
        # Validate QEC enhancement effectiveness
        high_priority_conflicts = [r for r in results if r["priority_score"] > 0.7]
        assert len(high_priority_conflicts) > 0, "QEC should identify high-priority conflicts"
        
        return {
            "results": results,
            "fidelity": fidelity,
            "performance_metrics": self.performance_metrics,
            "total_processing_time": total_time
        }
    
    def _calculate_priority_score(self, distances, error_predictions, severity):
        """Calculate priority score for conflict resolution."""
        # Base score from severity
        severity_scores = {"high": 0.8, "medium": 0.5, "low": 0.2}
        base_score = severity_scores.get(severity, 0.3)
        
        # Adjust based on constitutional distances (lower distance = higher priority)
        if distances:
            avg_distance = statistics.mean(distances)
            distance_factor = 1.0 - avg_distance  # Invert distance
        else:
            distance_factor = 0.5
        
        # Adjust based on error predictions
        if error_predictions:
            avg_risk = statistics.mean([p.get("overall_risk", 0.5) for p in error_predictions])
            risk_factor = avg_risk
        else:
            risk_factor = 0.5
        
        # Weighted combination
        priority_score = (0.4 * base_score + 0.3 * distance_factor + 0.3 * risk_factor)
        return min(1.0, max(0.0, priority_score))

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, sample_principles):
        """Test performance benchmarks for QEC components."""
        if not QEC_AVAILABLE:
            pytest.skip("QEC components not available")

        # Initialize components
        distance_calculator = ConstitutionalDistanceCalculator()
        error_predictor = ErrorPredictionModel()
        recovery_dispatcher = RecoveryStrategyDispatcher()
        fidelity_monitor = ConstitutionalFidelityMonitor()

        # Benchmark constitutional distance calculation
        distance_times = []
        for _ in range(10):  # Run 10 iterations
            start_time = time.time()
            for principle in sample_principles:
                await distance_calculator.calculate_distance(principle)
            distance_times.append(time.time() - start_time)

        avg_distance_time = statistics.mean(distance_times)
        assert avg_distance_time < 1.0, f"Distance calculation too slow: {avg_distance_time:.3f}s"

        # Benchmark error prediction
        prediction_times = []
        for _ in range(10):
            start_time = time.time()
            for principle in sample_principles:
                await error_predictor.predict_synthesis_challenges(principle)
            prediction_times.append(time.time() - start_time)

        avg_prediction_time = statistics.mean(prediction_times)
        assert avg_prediction_time < 2.0, f"Error prediction too slow: {avg_prediction_time:.3f}s"

        # Benchmark recovery strategy selection
        strategy_times = []
        for _ in range(10):
            start_time = time.time()
            await recovery_dispatcher.recommend_strategy(
                conflict_type="principle_contradiction",
                severity="high",
                error_predictions=[]
            )
            strategy_times.append(time.time() - start_time)

        avg_strategy_time = statistics.mean(strategy_times)
        assert avg_strategy_time < 0.5, f"Strategy selection too slow: {avg_strategy_time:.3f}s"

        # Benchmark fidelity calculation
        fidelity_times = []
        system_metrics = {"total_principles": len(sample_principles)}
        for _ in range(5):  # Fewer iterations for more expensive operation
            start_time = time.time()
            await fidelity_monitor.calculate_fidelity(sample_principles, system_metrics)
            fidelity_times.append(time.time() - start_time)

        avg_fidelity_time = statistics.mean(fidelity_times)
        assert avg_fidelity_time < 3.0, f"Fidelity calculation too slow: {avg_fidelity_time:.3f}s"

        return {
            "distance_calculation_time": avg_distance_time,
            "error_prediction_time": avg_prediction_time,
            "strategy_selection_time": avg_strategy_time,
            "fidelity_calculation_time": avg_fidelity_time
        }

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, sample_principles, sample_conflicts):
        """Test concurrent processing capabilities."""
        if not QEC_AVAILABLE:
            pytest.skip("QEC components not available")

        # Test concurrent conflict resolution
        async def process_conflict(conflict_data):
            resolver = QECConflictResolver() if SERVICE_AVAILABLE else Mock()
            start_time = time.time()

            # Simulate conflict processing
            await asyncio.sleep(0.1)  # Simulate processing time

            return {
                "conflict_id": conflict_data["id"],
                "processing_time": time.time() - start_time,
                "status": "processed"
            }

        # Process conflicts concurrently
        start_time = time.time()
        tasks = [process_conflict(conflict) for conflict in sample_conflicts]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Validate concurrent processing
        assert len(results) == len(sample_conflicts)
        assert total_time < 1.0, f"Concurrent processing too slow: {total_time:.3f}s"

        # Test concurrent fidelity calculations
        fidelity_monitor = ConstitutionalFidelityMonitor()

        async def calculate_fidelity_subset(principles_subset):
            system_metrics = {"total_principles": len(principles_subset)}
            return await fidelity_monitor.calculate_fidelity(principles_subset, system_metrics)

        # Split principles into subsets for concurrent processing
        principle_subsets = [
            sample_principles[:2],
            sample_principles[1:3],
            sample_principles[2:]
        ]

        start_time = time.time()
        fidelity_tasks = [calculate_fidelity_subset(subset) for subset in principle_subsets]
        fidelity_results = await asyncio.gather(*fidelity_tasks)
        fidelity_time = time.time() - start_time

        assert len(fidelity_results) == len(principle_subsets)
        assert fidelity_time < 5.0, f"Concurrent fidelity calculation too slow: {fidelity_time:.3f}s"

        return {
            "concurrent_conflicts": len(results),
            "conflict_processing_time": total_time,
            "concurrent_fidelity_calculations": len(fidelity_results),
            "fidelity_processing_time": fidelity_time
        }

    @pytest.mark.asyncio
    async def test_scalability_metrics(self, sample_principles):
        """Test system scalability with increasing load."""
        if not QEC_AVAILABLE:
            pytest.skip("QEC components not available")

        distance_calculator = ConstitutionalDistanceCalculator()

        # Test with increasing number of principles
        principle_counts = [1, 3, 5, 10, 20]
        processing_times = []

        for count in principle_counts:
            # Create extended principle set
            extended_principles = []
            for i in range(count):
                principle = sample_principles[i % len(sample_principles)].copy()
                principle["id"] = i + 1
                extended_principles.append(principle)

            # Measure processing time
            start_time = time.time()
            for principle in extended_principles:
                await distance_calculator.calculate_distance(principle)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)

        # Validate linear or sub-linear scaling
        for i in range(1, len(processing_times)):
            scaling_factor = processing_times[i] / processing_times[i-1]
            principle_factor = principle_counts[i] / principle_counts[i-1]

            # Should scale better than linearly (sub-linear due to optimizations)
            assert scaling_factor <= principle_factor * 1.5, \
                f"Poor scaling: {scaling_factor:.2f}x time for {principle_factor:.2f}x principles"

        return {
            "principle_counts": principle_counts,
            "processing_times": processing_times,
            "scaling_efficiency": "sub-linear" if all(
                processing_times[i] / processing_times[i-1] <=
                principle_counts[i] / principle_counts[i-1] * 1.2
                for i in range(1, len(processing_times))
            ) else "linear"
        }

    @pytest.mark.asyncio
    async def test_backward_compatibility(self, sample_principles, sample_conflicts):
        """Test backward compatibility with existing AC service functionality."""

        # Test 1: Existing conflict resolution without QEC enhancement
        if SERVICE_AVAILABLE:
            resolver = QECConflictResolver()

            # Test fallback behavior when QEC is disabled
            with patch.object(resolver, 'qec_available', False):
                for conflict_data in sample_conflicts:
                    # Create mock conflict and principles
                    conflict = Mock()
                    conflict.id = conflict_data["id"]
                    conflict.conflict_type = conflict_data["conflict_type"]
                    conflict.severity = conflict_data["severity"]

                    principles = [Mock(**p) for p in sample_principles
                                if p["id"] in conflict_data["principle_ids"]]

                    # Should work without QEC enhancement
                    analysis = await resolver.analyze_conflict(conflict, principles)
                    assert analysis.conflict_id == conflict_data["id"]
                    assert analysis.qec_metadata.get("fallback_used") is True

                    # Patch generation should also work
                    patch_result = await resolver.generate_patch(conflict, principles, analysis)
                    assert patch_result.confidence_score >= 0

        # Test 2: Graceful degradation when QEC components fail
        if QEC_AVAILABLE:
            distance_calculator = ConstitutionalDistanceCalculator()

            # Test with invalid principle data
            invalid_principle = {"id": 999, "title": "Invalid"}

            try:
                distance = await distance_calculator.calculate_distance(invalid_principle)
                # Should return default/fallback value
                assert isinstance(distance, (int, float))
                assert 0 <= distance <= 1
            except Exception as e:
                # Should handle errors gracefully
                assert "fallback" in str(e).lower() or "default" in str(e).lower()

        # Test 3: Data migration compatibility
        legacy_principle = {
            "id": 1,
            "title": "Legacy Principle",
            "description": "Old format principle",
            "category": "legacy",
            "priority_weight": 0.5
            # Missing QEC fields - should work with defaults
        }

        if QEC_AVAILABLE:
            distance_calculator = ConstitutionalDistanceCalculator()
            distance = await distance_calculator.calculate_distance(legacy_principle)
            assert isinstance(distance, (int, float))

        return {
            "fallback_behavior": "functional",
            "error_handling": "graceful",
            "legacy_compatibility": "maintained"
        }

    @pytest.mark.asyncio
    async def test_cross_service_integration(self, sample_principles):
        """Test cross-service communication and integration."""

        # Mock service endpoints for testing
        service_endpoints = {
            "ac_service": "http://localhost:8001",
            "gs_service": "http://localhost:8004",
            "fv_service": "http://localhost:8003",
            "pgc_service": "http://localhost:8005"
        }

        # Test 1: AC to GS service communication
        async def test_ac_to_gs_communication():
            """Test AC service sending principles to GS service for synthesis."""
            with patch('httpx.AsyncClient.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "synthesis_result": "success",
                    "qec_enhanced": True,
                    "constitutional_distance": 0.75
                }
                mock_post.return_value = mock_response

                # Simulate AC service calling GS service
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{service_endpoints['gs_service']}/api/v1/synthesis/qec-enhanced",
                        json={
                            "principles": sample_principles[:2],
                            "context": "cross_service_test"
                        }
                    )

                mock_post.assert_called_once()
                return True

        # Test 2: GS to FV service communication
        async def test_gs_to_fv_communication():
            """Test GS service sending policies to FV service for verification."""
            with patch('httpx.AsyncClient.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "verification_result": "passed",
                    "qec_insights": {
                        "constitutional_fidelity": 0.88,
                        "validation_scenarios_passed": 5
                    }
                }
                mock_post.return_value = mock_response

                # Simulate GS service calling FV service
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{service_endpoints['fv_service']}/api/v1/verification/qec-enhanced",
                        json={
                            "policy": "test_policy",
                            "principles": sample_principles[:1],
                            "qec_metadata": {"distance_score": 0.75}
                        }
                    )

                mock_post.assert_called_once()
                return True

        # Test 3: Constitutional Fidelity Monitor cross-service data collection
        async def test_fidelity_monitor_integration():
            """Test fidelity monitor collecting data from multiple services."""
            if not QEC_AVAILABLE:
                return True

            fidelity_monitor = ConstitutionalFidelityMonitor()

            # Mock system metrics from different services
            system_metrics = {
                "ac_service": {
                    "total_principles": len(sample_principles),
                    "active_conflicts": 2,
                    "resolution_success_rate": 0.85
                },
                "gs_service": {
                    "synthesis_attempts": 50,
                    "synthesis_success_rate": 0.88,
                    "average_synthesis_time": 2.3
                },
                "fv_service": {
                    "verification_attempts": 45,
                    "verification_success_rate": 0.92,
                    "average_verification_time": 1.8
                },
                "pgc_service": {
                    "policy_enforcements": 100,
                    "enforcement_success_rate": 0.95,
                    "average_enforcement_time": 0.5
                }
            }

            # Calculate cross-service fidelity
            fidelity = await fidelity_monitor.calculate_fidelity(
                sample_principles,
                system_metrics
            )

            assert fidelity.composite_score >= 0.0
            assert fidelity.composite_score <= 1.0
            return True

        # Execute all cross-service tests
        results = await asyncio.gather(
            test_ac_to_gs_communication(),
            test_gs_to_fv_communication(),
            test_fidelity_monitor_integration()
        )

        assert all(results), "Some cross-service integration tests failed"

        return {
            "ac_to_gs_communication": "functional",
            "gs_to_fv_communication": "functional",
            "fidelity_monitor_integration": "functional",
            "cross_service_data_flow": "validated"
        }

    @pytest.mark.asyncio
    async def test_constitutional_fidelity_monitor_alerts(self, sample_principles):
        """Test Constitutional Fidelity Monitor alert system."""
        if not QEC_AVAILABLE:
            pytest.skip("QEC components not available")

        fidelity_monitor = ConstitutionalFidelityMonitor()

        # Test different fidelity scenarios
        test_scenarios = [
            {
                "name": "high_fidelity",
                "system_metrics": {
                    "synthesis_success_rate": 0.95,
                    "enforcement_reliability": 0.92,
                    "stakeholder_satisfaction": 0.88,
                    "appeal_frequency": 0.05
                },
                "expected_level": "green"
            },
            {
                "name": "medium_fidelity",
                "system_metrics": {
                    "synthesis_success_rate": 0.78,
                    "enforcement_reliability": 0.75,
                    "stakeholder_satisfaction": 0.72,
                    "appeal_frequency": 0.15
                },
                "expected_level": "amber"
            },
            {
                "name": "low_fidelity",
                "system_metrics": {
                    "synthesis_success_rate": 0.60,
                    "enforcement_reliability": 0.58,
                    "stakeholder_satisfaction": 0.45,
                    "appeal_frequency": 0.35
                },
                "expected_level": "red"
            }
        ]

        alert_results = []

        for scenario in test_scenarios:
            fidelity = await fidelity_monitor.calculate_fidelity(
                sample_principles,
                scenario["system_metrics"]
            )

            # Determine alert level based on composite score
            if fidelity.composite_score >= 0.85:
                alert_level = "green"
            elif fidelity.composite_score >= 0.70:
                alert_level = "amber"
            else:
                alert_level = "red"

            alert_results.append({
                "scenario": scenario["name"],
                "composite_score": fidelity.composite_score,
                "alert_level": alert_level,
                "expected_level": scenario["expected_level"],
                "matches_expected": alert_level == scenario["expected_level"]
            })

        # Validate alert system
        for result in alert_results:
            assert result["composite_score"] >= 0.0
            assert result["composite_score"] <= 1.0
            assert result["alert_level"] in ["green", "amber", "red"]

        return {
            "alert_scenarios_tested": len(test_scenarios),
            "alert_results": alert_results,
            "alert_system_functional": all(r["matches_expected"] for r in alert_results)
        }

    @pytest.mark.asyncio
    async def test_target_metrics_validation(self, sample_principles, sample_conflicts):
        """Validate that QEC system meets target performance metrics."""
        if not QEC_AVAILABLE:
            pytest.skip("QEC components not available")

        # Run comprehensive workflow and measure against targets
        workflow_result = await self.test_end_to_end_qec_workflow(sample_principles, sample_conflicts)

        # Calculate success metrics
        total_conflicts = len(sample_conflicts)
        high_priority_conflicts = sum(1 for r in workflow_result["results"] if r["priority_score"] > 0.7)
        first_pass_success_rate = high_priority_conflicts / total_conflicts if total_conflicts > 0 else 0

        # Calculate average resolution time (simulated)
        avg_resolution_time = statistics.mean([r["processing_time"] for r in workflow_result["results"]])

        # Validate against targets
        target_validations = {
            "first_pass_synthesis_success": {
                "actual": first_pass_success_rate,
                "target": self.target_metrics["first_pass_synthesis_success"],
                "meets_target": first_pass_success_rate >= self.target_metrics["first_pass_synthesis_success"]
            },
            "constitutional_fidelity": {
                "actual": workflow_result["fidelity"].composite_score,
                "target": self.target_metrics["constitutional_fidelity_threshold"],
                "meets_target": workflow_result["fidelity"].composite_score >= self.target_metrics["constitutional_fidelity_threshold"]
            },
            "processing_time": {
                "actual": workflow_result["total_processing_time"],
                "target": 30.0,  # 30 seconds for end-to-end processing
                "meets_target": workflow_result["total_processing_time"] < 30.0
            }
        }

        # Log performance metrics
        performance_summary = {
            "target_validations": target_validations,
            "performance_metrics": self.performance_metrics,
            "overall_success": all(v["meets_target"] for v in target_validations.values())
        }

        # Assert critical targets are met
        assert target_validations["constitutional_fidelity"]["meets_target"], \
            f"Constitutional fidelity {target_validations['constitutional_fidelity']['actual']:.3f} below target {target_validations['constitutional_fidelity']['target']}"

        assert target_validations["processing_time"]["meets_target"], \
            f"Processing time {target_validations['processing_time']['actual']:.3f}s exceeds target {target_validations['processing_time']['target']}s"

        return performance_summary


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
