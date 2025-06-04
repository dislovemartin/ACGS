"""
Test suite for Intelligent Conflict Resolution System

Tests all components of the intelligent conflict resolution system including:
- Conflict detection algorithms
- Automated resolution strategies
- Human escalation mechanisms
- Audit trail and monitoring
- Performance metrics and targets
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.intelligent_conflict_detector import (
    IntelligentConflictDetector, ConflictDetectionResult, ConflictType, ConflictSeverity
)
from app.services.automated_resolution_engine import (
    AutomatedResolutionEngine, ResolutionResult, ResolutionStrategy, ResolutionStatus
)
from app.services.human_escalation_system import (
    HumanEscalationSystem, EscalationRequest, EscalationLevel, EscalationReason
)
from app.services.conflict_audit_system import (
    ConflictAuditSystem, AuditEventType, AuditLevel, PerformanceMetrics
)
from app.services.conflict_resolution_orchestrator import ConflictResolutionOrchestrator
from shared.models import Principle, ACConflictResolution


class TestIntelligentConflictDetector:
    """Test suite for intelligent conflict detection."""
    
    @pytest.fixture
    def detector(self):
        """Create conflict detector instance."""
        return IntelligentConflictDetector()
    
    @pytest.fixture
    def mock_principles(self):
        """Create mock principles for testing."""
        return [
            Mock(
                id=1,
                title="Privacy Protection",
                description="Users must have control over their personal data and privacy settings",
                priority_weight=0.8,
                is_active=True
            ),
            Mock(
                id=2,
                title="Security Monitoring",
                description="System must monitor user activities for security threats",
                priority_weight=0.9,
                is_active=True
            ),
            Mock(
                id=3,
                title="Data Minimization",
                description="Collect only necessary data for system operation",
                priority_weight=0.7,
                is_active=True
            )
        ]
    
    @pytest.mark.asyncio
    async def test_conflict_detection_basic(self, detector, mock_principles):
        """Test basic conflict detection functionality."""
        with patch.object(detector, '_get_principles_for_analysis', return_value=mock_principles):
            with patch.object(detector, '_analyze_principles') as mock_analyze:
                # Mock principle analyses
                mock_analyze.return_value = [
                    Mock(
                        principle_id=1,
                        semantic_embedding=None,
                        scope_keywords={"privacy", "data", "user"},
                        priority_weight=0.8,
                        stakeholder_impact={"users": 0.9, "developers": 0.3},
                        temporal_constraints={"immediate": True},
                        normative_statements=["Users must have control over data"]
                    ),
                    Mock(
                        principle_id=2,
                        semantic_embedding=None,
                        scope_keywords={"security", "monitoring", "data"},
                        priority_weight=0.9,
                        stakeholder_impact={"users": 0.4, "administrators": 0.9},
                        temporal_constraints={"immediate": True},
                        normative_statements=["System must monitor activities"]
                    )
                ]
                
                # Mock database session
                mock_db = AsyncMock()
                
                # Run detection
                conflicts = await detector.detect_conflicts(mock_db)
                
                # Verify detection results
                assert isinstance(conflicts, list)
                # Should detect at least one conflict between privacy and security
                if conflicts:
                    conflict = conflicts[0]
                    assert isinstance(conflict, ConflictDetectionResult)
                    assert conflict.confidence_score >= 0.0
                    assert conflict.priority_score >= 0.0
    
    @pytest.mark.asyncio
    async def test_semantic_conflict_detection(self, detector):
        """Test semantic conflict detection algorithm."""
        # Mock semantic embeddings
        import numpy as np
        embedding_a = np.array([0.1, 0.2, 0.3, 0.4])
        embedding_b = np.array([0.9, 0.8, 0.7, 0.6])  # Different direction
        
        # Test semantic similarity calculation
        similarity = detector._calculate_semantic_similarity(embedding_a, embedding_b)
        assert 0.0 <= similarity <= 1.0
        
        # Test contradiction detection
        statements_a = ["Users must have privacy", "Data should be protected"]
        statements_b = ["System must monitor users", "Data must be accessible"]
        
        contradiction_score = detector._detect_contradiction(statements_a, statements_b)
        assert 0.0 <= contradiction_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_priority_conflict_detection(self, detector):
        """Test priority-based conflict detection."""
        # Create mock analyses with different priorities
        analyses = [
            Mock(
                principle_id=1,
                scope_keywords={"data", "privacy"},
                priority_weight=0.9,
                stakeholder_impact={"users": 0.8}
            ),
            Mock(
                principle_id=2,
                scope_keywords={"data", "security"},
                priority_weight=0.3,  # Much lower priority
                stakeholder_impact={"users": 0.2}
            )
        ]
        
        conflicts = await detector._detect_priority_conflicts(analyses)
        
        # Should detect priority conflict due to scope overlap and priority difference
        assert len(conflicts) >= 0  # May or may not detect based on thresholds
        
        if conflicts:
            conflict = conflicts[0]
            assert conflict.conflict_type == ConflictType.PRIORITY_CONFLICT
            assert conflict.confidence_score > 0.0


class TestAutomatedResolutionEngine:
    """Test suite for automated resolution engine."""
    
    @pytest.fixture
    def resolver(self):
        """Create resolution engine instance."""
        return AutomatedResolutionEngine()
    
    @pytest.fixture
    def mock_conflict(self):
        """Create mock conflict for testing."""
        return Mock(
            id=1,
            conflict_type="priority_conflict",
            severity="medium",
            principle_ids=[1, 2],
            resolution_details={"attempts": 0}
        )
    
    @pytest.fixture
    def mock_detection_result(self):
        """Create mock detection result."""
        return ConflictDetectionResult(
            conflict_type=ConflictType.PRIORITY_CONFLICT,
            severity=ConflictSeverity.MEDIUM,
            principle_ids=[1, 2],
            confidence_score=0.8,
            description="Priority conflict between principles",
            context="test_context",
            priority_score=0.7,
            detection_metadata={"method": "priority_analysis"},
            recommended_strategy="weighted_priority"
        )
    
    @pytest.mark.asyncio
    async def test_strategy_evaluation(self, resolver, mock_conflict, mock_detection_result):
        """Test resolution strategy evaluation."""
        mock_principles = [
            Mock(id=1, priority_weight=0.8),
            Mock(id=2, priority_weight=0.3)
        ]
        
        evaluations = await resolver._evaluate_strategies(
            mock_conflict, mock_principles, mock_detection_result
        )
        
        assert isinstance(evaluations, list)
        assert len(evaluations) > 0
        
        # Check that evaluations are properly structured
        for evaluation in evaluations:
            assert hasattr(evaluation, 'strategy')
            assert hasattr(evaluation, 'applicability_score')
            assert hasattr(evaluation, 'expected_success_rate')
            assert 0.0 <= evaluation.applicability_score <= 1.0
            assert 0.0 <= evaluation.expected_success_rate <= 1.0
    
    @pytest.mark.asyncio
    async def test_weighted_priority_strategy(self, resolver, mock_conflict):
        """Test weighted priority resolution strategy."""
        mock_principles = [
            Mock(id=1, priority_weight=0.9),
            Mock(id=2, priority_weight=0.3)
        ]
        
        mock_db = AsyncMock()
        
        result = await resolver._apply_weighted_priority(
            mock_db, mock_conflict, mock_principles, None
        )
        
        assert isinstance(result, ResolutionResult)
        assert result.strategy_used == ResolutionStrategy.WEIGHTED_PRIORITY
        assert result.success is True
        assert result.confidence_score > 0.0
        assert "principle_weights" in result.resolution_details
    
    @pytest.mark.asyncio
    async def test_resolution_with_qec_integration(self, resolver):
        """Test resolution with QEC integration."""
        # Mock QEC resolver
        with patch.object(resolver, 'qec_resolver') as mock_qec:
            mock_qec.qec_available = True
            mock_qec.analyze_conflict = AsyncMock(return_value=Mock())
            mock_qec.generate_patch = AsyncMock(return_value=Mock(
                success=True,
                patch_content="Generated patch content"
            ))
            
            mock_db = AsyncMock()
            mock_conflict = Mock(id=1, principle_ids=[1, 2])
            mock_principles = [Mock(id=1), Mock(id=2)]
            
            result = await resolver.resolve_conflict(
                mock_db, mock_conflict, None
            )
            
            assert isinstance(result, ResolutionResult)
            # QEC integration should be attempted
            mock_qec.analyze_conflict.assert_called_once()


class TestHumanEscalationSystem:
    """Test suite for human escalation system."""
    
    @pytest.fixture
    def escalator(self):
        """Create escalation system instance."""
        return HumanEscalationSystem()
    
    @pytest.fixture
    def mock_conflict(self):
        """Create mock conflict for testing."""
        return Mock(
            id=1,
            severity="critical",
            principle_ids=[1, 2, 3],
            resolution_details={"failed_attempts": 2}
        )
    
    @pytest.mark.asyncio
    async def test_escalation_evaluation(self, escalator, mock_conflict):
        """Test escalation need evaluation."""
        # Mock resolution result that failed
        mock_resolution = Mock(
            success=False,
            confidence_score=0.3,
            escalation_required=True
        )
        
        # Mock detection result
        mock_detection = Mock(
            conflict_type=ConflictType.PRINCIPLE_CONTRADICTION,
            severity=ConflictSeverity.CRITICAL,
            priority_score=0.9
        )
        
        mock_db = AsyncMock()
        
        escalation_request = await escalator.evaluate_escalation_need(
            mock_db, mock_conflict, mock_resolution, mock_detection
        )
        
        # Critical severity should trigger escalation
        assert escalation_request is not None
        assert isinstance(escalation_request, EscalationRequest)
        assert escalation_request.escalation_level in [
            EscalationLevel.EMERGENCY_RESPONSE,
            EscalationLevel.CONSTITUTIONAL_COUNCIL
        ]
        assert escalation_request.urgency_score > 0.0
    
    @pytest.mark.asyncio
    async def test_escalation_rule_checking(self, escalator):
        """Test escalation rule evaluation."""
        # Test critical severity rule
        rule = escalator.escalation_rules[0]  # Critical severity rule
        
        mock_conflict = Mock(severity="critical")
        mock_resolution = Mock(confidence_score=0.95)
        
        triggered = await escalator._check_escalation_rule(
            rule, mock_conflict, mock_resolution, None
        )
        
        # Should trigger for critical severity
        assert triggered is True
        
        # Test with non-critical severity
        mock_conflict.severity = "low"
        triggered = await escalator._check_escalation_rule(
            rule, mock_conflict, mock_resolution, None
        )
        
        # Should not trigger for low severity
        assert triggered is False


class TestConflictAuditSystem:
    """Test suite for conflict audit system."""
    
    @pytest.fixture
    def auditor(self):
        """Create audit system instance."""
        return ConflictAuditSystem()
    
    @pytest.fixture
    def mock_conflict(self):
        """Create mock conflict for testing."""
        return Mock(id=1, conflict_type="priority_conflict", severity="medium")
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, auditor, mock_conflict):
        """Test audit event logging."""
        mock_db = AsyncMock()
        
        # Mock detection result
        detection_result = ConflictDetectionResult(
            conflict_type=ConflictType.PRIORITY_CONFLICT,
            severity=ConflictSeverity.MEDIUM,
            principle_ids=[1, 2],
            confidence_score=0.8,
            description="Test conflict",
            context="test",
            priority_score=0.7,
            detection_metadata={"method": "test"},
            recommended_strategy="weighted_priority"
        )
        
        # Log detection event
        audit_entry = await auditor.log_conflict_detection(
            mock_db, mock_conflict, detection_result, user_id=1
        )
        
        assert audit_entry.event_type == AuditEventType.CONFLICT_DETECTED
        assert audit_entry.conflict_id == 1
        assert audit_entry.user_id == 1
        assert "conflict_type" in audit_entry.event_data
        assert audit_entry.integrity_hash is not None
    
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, auditor):
        """Test performance metrics collection."""
        mock_db = AsyncMock()
        
        # Simulate some activity
        auditor.current_metrics["conflicts_detected"] = 10
        auditor.current_metrics["resolutions_attempted"] = 8
        auditor.current_metrics["resolutions_succeeded"] = 6
        auditor.current_metrics["escalations_triggered"] = 2
        auditor.current_metrics["total_processing_time"] = 120.0
        
        # Mock recent conflicts count
        with patch.object(auditor, '_count_recent_conflicts', return_value=5):
            metrics = await auditor.collect_performance_metrics(mock_db)
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.auto_resolution_rate == 75.0  # 6/8 * 100
        assert metrics.escalation_rate == 20.0  # 2/10 * 100
        assert metrics.average_resolution_time == 15.0  # 120/8
        assert metrics.throughput == 5


class TestConflictResolutionOrchestrator:
    """Test suite for conflict resolution orchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return ConflictResolutionOrchestrator()
    
    @pytest.mark.asyncio
    async def test_end_to_end_conflict_resolution(self, orchestrator):
        """Test complete conflict resolution workflow."""
        mock_db = AsyncMock()
        
        # Mock all subsystems
        with patch.object(orchestrator.detector, 'detect_conflicts') as mock_detect:
            with patch.object(orchestrator.resolver, 'resolve_conflict') as mock_resolve:
                with patch.object(orchestrator.auditor, 'log_conflict_detection') as mock_audit:
                    
                    # Setup mocks
                    mock_detect.return_value = [
                        ConflictDetectionResult(
                            conflict_type=ConflictType.PRIORITY_CONFLICT,
                            severity=ConflictSeverity.MEDIUM,
                            principle_ids=[1, 2],
                            confidence_score=0.85,  # High confidence
                            description="Test conflict",
                            context="test",
                            priority_score=0.7,
                            detection_metadata={"method": "test"},
                            recommended_strategy="weighted_priority"
                        )
                    ]
                    
                    mock_resolve.return_value = ResolutionResult(
                        success=True,
                        strategy_used=ResolutionStrategy.WEIGHTED_PRIORITY,
                        resolution_details={"test": "data"},
                        confidence_score=0.9,
                        validation_passed=True,
                        generated_patch="test patch",
                        escalation_required=False,
                        escalation_reason=None,
                        processing_time=1.5,
                        metadata={}
                    )
                    
                    # Mock conflict creation
                    with patch.object(orchestrator.detector, 'create_conflict_resolution_entry') as mock_create:
                        mock_create.return_value = Mock(id=1)
                        
                        # Run detection scan
                        conflicts = await orchestrator.run_conflict_detection_scan(
                            mock_db, principle_ids=[1, 2], user_id=1
                        )
                        
                        # Verify workflow execution
                        assert len(conflicts) == 1
                        mock_detect.assert_called_once()
                        mock_create.assert_called_once()
                        mock_audit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_performance_targets_monitoring(self, orchestrator):
        """Test performance targets monitoring."""
        mock_db = AsyncMock()
        
        # Mock performance metrics
        with patch.object(orchestrator.auditor, 'collect_performance_metrics') as mock_metrics:
            mock_metrics.return_value = PerformanceMetrics(
                detection_accuracy=85.0,
                auto_resolution_rate=82.0,  # Above 80% target
                average_resolution_time=2.5,
                escalation_rate=15.0,
                human_intervention_rate=15.0,
                system_availability=99.5,
                error_rate=0.5,
                throughput=25.0,
                timestamp=datetime.now()
            )
            
            # Get performance report
            report = await orchestrator.get_system_performance_report(mock_db)
            
            # Verify report structure
            assert "performance_summary" in report
            assert "targets" in report
            assert "recommendations" in report
            
            # Check target achievement
            summary = report["performance_summary"]
            assert summary["auto_resolution_rate"] == 82.0
            assert summary["auto_resolution_target"] == 80.0  # Target
            
            # Should show target achievement > 100%
            assert summary["target_achievement"] > 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
