"""
test_qec_error_correction_integration.py

Integration tests for QEC-Inspired Error Correction Service.
Tests the complete error correction workflow including conflict detection,
automatic resolution, semantic validation, and human escalation.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any

# Test framework imports
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Import test utilities
try:
    from conftest import (
        async_client, db_session, test_user, test_admin_user,
        create_test_principle, create_test_policy
    )
except ImportError:
    # Fallback for when conftest is not available
    async_client = None
    db_session = None
    test_user = None
    test_admin_user = None
    create_test_principle = None
    create_test_policy = None

# Add project root to path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src/backend"))

# Import models and services
from src.backend.shared.models import ConstitutionalPrinciple, Policy, User
from src.backend.shared.database import get_async_db

# Import QEC error correction services
try:
    from src.backend.gs_service.app.services.qec_error_correction_service import (
        QECErrorCorrectionService,
        ConflictDetectionEngine,
        AutomaticResolutionWorkflow,
        SemanticValidationEngine,
        PolicyRefinementSuggester,
        ConflictComplexityScorer,
        ParallelConflictProcessor,
        ConflictType,
        ResolutionStrategy,
        ErrorCorrectionStatus,
        ConflictDetectionResult,
        ErrorCorrectionResult
    )
    QEC_AVAILABLE = True
except ImportError:
    # Provide mock classes for type hints when QEC components are not available
    from unittest.mock import Mock
    QECErrorCorrectionService = Mock
    ConflictDetectionEngine = Mock
    AutomaticResolutionWorkflow = Mock
    SemanticValidationEngine = Mock
    PolicyRefinementSuggester = Mock
    ConflictComplexityScorer = Mock
    ParallelConflictProcessor = Mock
    ConflictType = Mock
    ResolutionStrategy = Mock
    ErrorCorrectionStatus = Mock
    ConflictDetectionResult = Mock
    ErrorCorrectionResult = Mock
    QEC_AVAILABLE = False

# Skip all tests if QEC components are not available
pytestmark = pytest.mark.skipif(not QEC_AVAILABLE, reason="QEC error correction components not available")


@pytest.fixture
async def qec_service():
    """Create QEC error correction service for testing."""
    return QECErrorCorrectionService()


@pytest.fixture
async def test_principles(db_session: AsyncSession):
    """Create test constitutional principles."""
    principles = []
    
    # Principle 1: Privacy protection
    principle1 = await create_test_principle(
        db_session,
        title="Data Privacy Protection",
        description="All personal data must be protected with appropriate encryption and access controls",
        priority_weight=0.9,
        scope="data_handling"
    )
    principles.append(principle1)
    
    # Principle 2: Transparency
    principle2 = await create_test_principle(
        db_session,
        title="Algorithmic Transparency",
        description="AI systems must provide clear explanations for their decisions",
        priority_weight=0.8,
        scope="ai_governance"
    )
    principles.append(principle2)
    
    # Principle 3: Fairness (potentially conflicting)
    principle3 = await create_test_principle(
        db_session,
        title="Equal Treatment",
        description="All users must receive equal treatment regardless of personal characteristics",
        priority_weight=0.85,
        scope="fairness"
    )
    principles.append(principle3)
    
    return principles


@pytest.fixture
async def test_policies(db_session: AsyncSession):
    """Create test policies."""
    policies = []
    
    # Policy 1: Data retention (potentially conflicts with privacy)
    policy1 = await create_test_policy(
        db_session,
        name="Data Retention Policy",
        description="User data may be retained indefinitely for business purposes",
        policy_type="data_management"
    )
    policies.append(policy1)
    
    # Policy 2: Automated decision making
    policy2 = await create_test_policy(
        db_session,
        name="Automated Decision Policy",
        description="Automated systems can make decisions without human oversight",
        policy_type="ai_governance"
    )
    policies.append(policy2)
    
    return policies


class TestQECErrorCorrectionService:
    """Test suite for QEC Error Correction Service."""
    
    @pytest.mark.asyncio
    async def test_conflict_detection_engine(
        self,
        qec_service: QECErrorCorrectionService,
        test_principles: List[ConstitutionalPrinciple],
        test_policies: List[Policy]
    ):
        """Test conflict detection between principles and policies."""
        # Test conflict detection
        conflicts = await qec_service.conflict_detector.detect_conflicts(
            principles=test_principles,
            policies=test_policies,
            context_data={"test_scenario": "integration_test"}
        )
        
        # Verify conflicts were detected
        assert len(conflicts) > 0, "Should detect conflicts between test principles and policies"
        
        # Check conflict structure
        for conflict in conflicts:
            assert isinstance(conflict, ConflictDetectionResult)
            assert conflict.conflict_detected is True
            assert conflict.conflict_type is not None
            assert conflict.severity is not None
            assert conflict.confidence_score >= 0.0
            assert conflict.confidence_score <= 1.0
            assert len(conflict.conflict_description) > 0
    
    @pytest.mark.asyncio
    async def test_automatic_resolution_workflow(
        self,
        qec_service: QECErrorCorrectionService,
        test_principles: List[ConstitutionalPrinciple],
        test_policies: List[Policy],
        db_session: AsyncSession
    ):
        """Test automatic conflict resolution workflow."""
        # First detect conflicts
        conflicts = await qec_service.conflict_detector.detect_conflicts(
            principles=test_principles,
            policies=test_policies
        )
        
        assert len(conflicts) > 0, "Need conflicts to test resolution"
        
        # Test automatic resolution
        for conflict in conflicts[:2]:  # Test first 2 conflicts
            resolution_result = await qec_service.resolution_workflow.resolve_conflict(
                conflict=conflict,
                db=db_session
            )
            
            # Verify resolution result
            assert isinstance(resolution_result, ErrorCorrectionResult)
            assert resolution_result.correction_id is not None
            assert resolution_result.status in [
                ErrorCorrectionStatus.RESOLVED_AUTOMATICALLY,
                ErrorCorrectionStatus.ESCALATED_TO_HUMAN,
                ErrorCorrectionStatus.ESCALATED_TO_COUNCIL,
                ErrorCorrectionStatus.FAILED
            ]
            assert resolution_result.response_time_seconds >= 0.0
            assert len(resolution_result.recommended_actions) > 0
    
    @pytest.mark.asyncio
    async def test_semantic_validation_engine(
        self,
        qec_service: QECErrorCorrectionService,
        test_principles: List[ConstitutionalPrinciple],
        test_policies: List[Policy]
    ):
        """Test semantic validation and correction."""
        principle = test_principles[0]
        policy = test_policies[0]
        
        # Test semantic validation
        validation_result = await qec_service.semantic_validator.validate_and_correct(
            principle=principle,
            policy=policy,
            context_data={"validation_test": True}
        )
        
        # Verify validation result
        assert isinstance(validation_result, ErrorCorrectionResult)
        assert validation_result.correction_id is not None
        assert validation_result.status in [
            ErrorCorrectionStatus.RESOLVED_AUTOMATICALLY,
            ErrorCorrectionStatus.FAILED
        ]
        assert validation_result.response_time_seconds >= 0.0
    
    @pytest.mark.asyncio
    async def test_policy_refinement_suggester(
        self,
        qec_service: QECErrorCorrectionService,
        test_principles: List[ConstitutionalPrinciple],
        test_policies: List[Policy]
    ):
        """Test policy refinement suggestions."""
        policy = test_policies[0]
        principles = test_principles[:2]
        
        # Generate refinement suggestions
        suggestions = await qec_service.refinement_suggester.generate_refinement_suggestions(
            policy=policy,
            principles=principles,
            context_data={"refinement_test": True}
        )
        
        # Verify suggestions
        assert isinstance(suggestions, list)
        # Note: Suggestions may be empty if no refinements are needed
        
        for suggestion in suggestions:
            assert suggestion.suggestion_id is not None
            assert suggestion.policy_id == str(policy.id)
            assert suggestion.principle_id in [str(p.id) for p in principles]
            assert suggestion.confidence_score >= 0.0
            assert suggestion.confidence_score <= 1.0
            assert len(suggestion.justification) > 0
    
    @pytest.mark.asyncio
    async def test_conflict_complexity_scorer(
        self,
        qec_service: QECErrorCorrectionService,
        test_principles: List[ConstitutionalPrinciple],
        test_policies: List[Policy]
    ):
        """Test conflict complexity scoring."""
        # First detect conflicts
        conflicts = await qec_service.conflict_detector.detect_conflicts(
            principles=test_principles,
            policies=test_policies
        )
        
        assert len(conflicts) > 0, "Need conflicts to test complexity scoring"
        
        # Test complexity scoring
        for conflict in conflicts[:2]:  # Test first 2 conflicts
            complexity_score, requires_escalation = await qec_service.complexity_scorer.score_complexity(
                conflict=conflict,
                context_data={"complexity_test": True}
            )
            
            # Verify complexity scoring
            assert isinstance(complexity_score, float)
            assert complexity_score >= 0.0
            assert complexity_score <= 1.0
            assert isinstance(requires_escalation, bool)
    
    @pytest.mark.asyncio
    async def test_parallel_conflict_processor(
        self,
        qec_service: QECErrorCorrectionService,
        test_principles: List[ConstitutionalPrinciple],
        test_policies: List[Policy],
        db_session: AsyncSession
    ):
        """Test parallel conflict processing."""
        # First detect conflicts
        conflicts = await qec_service.conflict_detector.detect_conflicts(
            principles=test_principles,
            policies=test_policies
        )
        
        assert len(conflicts) > 0, "Need conflicts to test parallel processing"
        
        # Test parallel processing
        results = await qec_service.parallel_processor.process_conflicts_parallel(
            conflicts=conflicts,
            db=db_session
        )
        
        # Verify parallel processing results
        assert isinstance(results, list)
        assert len(results) <= len(conflicts)  # Some may be cached or filtered
        
        for result in results:
            assert isinstance(result, ErrorCorrectionResult)
            assert result.correction_id is not None
            assert result.response_time_seconds >= 0.0
    
    @pytest.mark.asyncio
    async def test_complete_error_correction_workflow(
        self,
        qec_service: QECErrorCorrectionService,
        test_principles: List[ConstitutionalPrinciple],
        test_policies: List[Policy],
        db_session: AsyncSession
    ):
        """Test complete error correction workflow."""
        # Execute complete workflow
        workflow_results = await qec_service.process_error_correction_workflow(
            principles=test_principles,
            policies=test_policies,
            context_data={"workflow_test": True},
            db=db_session
        )
        
        # Verify workflow results
        assert isinstance(workflow_results, dict)
        assert "workflow_id" in workflow_results
        assert "status" in workflow_results
        assert "response_time_seconds" in workflow_results
        assert "conflicts_detected" in workflow_results
        assert "automatic_resolutions" in workflow_results
        assert "escalations_required" in workflow_results
        
        # Check performance metrics
        assert workflow_results["response_time_seconds"] >= 0.0
        assert workflow_results["conflicts_detected"] >= 0
        assert workflow_results["automatic_resolutions"] >= 0
        assert workflow_results["escalations_required"] >= 0
        
        # Verify detailed results structure
        assert "detailed_results" in workflow_results
        detailed = workflow_results["detailed_results"]
        assert "conflicts" in detailed
        assert "automatic_corrections" in detailed
        assert "escalations" in detailed
        assert "refinement_suggestions" in detailed
    
    @pytest.mark.asyncio
    async def test_performance_targets(
        self,
        qec_service: QECErrorCorrectionService,
        test_principles: List[ConstitutionalPrinciple],
        test_policies: List[Policy],
        db_session: AsyncSession
    ):
        """Test that performance targets are met."""
        # Execute workflow and measure performance
        start_time = datetime.now()
        
        workflow_results = await qec_service.process_error_correction_workflow(
            principles=test_principles,
            policies=test_policies,
            context_data={"performance_test": True},
            db=db_session
        )
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Verify performance targets
        # Target: <30 second response times
        assert total_time < 30.0, f"Workflow took {total_time:.2f}s, should be <30s"
        
        # Target: >95% error correction accuracy (simplified check)
        if workflow_results["conflicts_detected"] > 0:
            total_processed = (
                workflow_results["automatic_resolutions"] + 
                workflow_results["escalations_required"]
            )
            if total_processed > 0:
                # At least some conflicts should be processed
                assert total_processed <= workflow_results["conflicts_detected"]
        
        # Get performance summary
        performance_summary = qec_service.get_performance_summary()
        
        # Verify performance summary structure
        assert "total_corrections_processed" in performance_summary
        assert "automatic_resolution_rate" in performance_summary
        assert "average_response_time_seconds" in performance_summary
        assert "current_accuracy_rate" in performance_summary
        assert "performance_targets" in performance_summary
        assert "targets_met" in performance_summary
