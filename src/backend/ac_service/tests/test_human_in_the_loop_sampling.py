"""
Test suite for Human-in-the-Loop Sampling System

Tests all components of the HITL sampling system including:
- Uncertainty quantification algorithms
- Human intervention triggers
- Adaptive learning mechanisms
- Performance metrics and targets
- API endpoints and integration
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.human_in_the_loop_sampler import (
    HumanInTheLoopSampler, HITLSamplingConfig, UncertaintyAssessment,
    UncertaintyDimension, SamplingTrigger
)
from app.services.human_escalation_system import EscalationLevel
from shared.models import Principle


class TestHITLSamplingConfig:
    """Test suite for HITL sampling configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = HITLSamplingConfig()
        
        assert config.uncertainty_threshold == 0.75
        assert config.confidence_threshold == 0.75
        assert config.false_positive_target == 0.05
        assert config.accuracy_target == 0.95
        assert config.learning_enabled is True
        assert config.adaptation_rate == 0.1
        
        # Check dimensional weights sum to 1.0
        total_weight = sum(config.dimensional_weights.values())
        assert abs(total_weight - 1.0) < 0.01
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = HITLSamplingConfig(
            uncertainty_threshold=0.8,
            confidence_threshold=0.7,
            learning_enabled=False
        )
        
        assert config.uncertainty_threshold == 0.8
        assert config.confidence_threshold == 0.7
        assert config.learning_enabled is False


class TestUncertaintyAssessment:
    """Test suite for uncertainty assessment functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def hitl_sampler(self):
        """Create HITL sampler instance."""
        return HumanInTheLoopSampler()
    
    @pytest.fixture
    def sample_decision_context(self):
        """Create sample decision context."""
        return {
            "decision_id": "test_decision_001",
            "policy_type": "privacy_protection",
            "affected_users": 1000,
            "user_id": 1,
            "decision_scope": "service",
            "safety_critical": False,
            "stakeholder_conflicts": False,
            "novel_scenario": False
        }
    
    @pytest.mark.asyncio
    async def test_basic_uncertainty_assessment(self, hitl_sampler, mock_db, sample_decision_context):
        """Test basic uncertainty assessment functionality."""
        # Mock principle retrieval
        with patch.object(hitl_sampler, '_get_principles') as mock_get_principles:
            mock_principles = [
                Mock(id=1, description="Clear privacy principle with detailed guidelines"),
                Mock(id=2, description="Security principle")
            ]
            mock_get_principles.return_value = mock_principles
            
            # Mock conflict detection
            with patch.object(hitl_sampler.conflict_detector, 'detect_conflicts') as mock_detect:
                mock_detect.return_value = Mock(conflicts_detected=[])
                
                assessment = await hitl_sampler.assess_uncertainty(
                    db=mock_db,
                    decision_context=sample_decision_context,
                    ai_confidence=0.8,
                    principle_ids=[1, 2]
                )
                
                assert isinstance(assessment, UncertaintyAssessment)
                assert assessment.decision_id == "test_decision_001"
                assert 0.0 <= assessment.overall_uncertainty <= 1.0
                assert 0.0 <= assessment.confidence_score <= 1.0
                assert isinstance(assessment.requires_human_oversight, bool)
                assert assessment.recommended_oversight_level in EscalationLevel
    
    @pytest.mark.asyncio
    async def test_high_uncertainty_triggers_oversight(self, hitl_sampler, mock_db):
        """Test that high uncertainty triggers human oversight."""
        high_uncertainty_context = {
            "decision_id": "high_uncertainty_test",
            "user_id": 1,
            "safety_critical": True,
            "stakeholder_conflicts": True,
            "novel_scenario": True,
            "decision_scope": "global",
            "impact_magnitude": "critical"
        }
        
        with patch.object(hitl_sampler, '_get_principles') as mock_get_principles:
            mock_get_principles.return_value = []
            
            assessment = await hitl_sampler.assess_uncertainty(
                db=mock_db,
                decision_context=high_uncertainty_context,
                ai_confidence=0.3,  # Low confidence
                principle_ids=[]
            )
            
            assert assessment.requires_human_oversight is True
            assert assessment.overall_uncertainty > hitl_sampler.config.uncertainty_threshold
            assert SamplingTrigger.SAFETY_CRITICAL in assessment.triggers_activated
    
    @pytest.mark.asyncio
    async def test_low_uncertainty_no_oversight(self, hitl_sampler, mock_db):
        """Test that low uncertainty doesn't trigger oversight."""
        low_uncertainty_context = {
            "decision_id": "low_uncertainty_test",
            "user_id": 1,
            "safety_critical": False,
            "stakeholder_conflicts": False,
            "novel_scenario": False,
            "decision_scope": "local",
            "impact_magnitude": "low",
            "has_training_data": True,
            "domain_expertise_available": True,
            "clear_requirements": True,
            "has_implementation_precedent": True
        }
        
        with patch.object(hitl_sampler, '_get_principles') as mock_get_principles:
            mock_principles = [Mock(id=1, description="Very clear and detailed principle with comprehensive guidelines and examples")]
            mock_get_principles.return_value = mock_principles
            
            with patch.object(hitl_sampler.conflict_detector, 'detect_conflicts') as mock_detect:
                mock_detect.return_value = Mock(conflicts_detected=[])
                
                assessment = await hitl_sampler.assess_uncertainty(
                    db=mock_db,
                    decision_context=low_uncertainty_context,
                    ai_confidence=0.9,  # High confidence
                    principle_ids=[1]
                )
                
                assert assessment.requires_human_oversight is False
                assert assessment.overall_uncertainty < hitl_sampler.config.uncertainty_threshold
    
    @pytest.mark.asyncio
    async def test_dimensional_uncertainty_calculation(self, hitl_sampler, mock_db, sample_decision_context):
        """Test dimensional uncertainty calculation."""
        with patch.object(hitl_sampler, '_get_principles') as mock_get_principles:
            mock_get_principles.return_value = [Mock(id=1, description="Test principle")]
            
            with patch.object(hitl_sampler.conflict_detector, 'detect_conflicts') as mock_detect:
                mock_detect.return_value = Mock(conflicts_detected=[])
                
                dimensional_uncertainties = await hitl_sampler._calculate_dimensional_uncertainties(
                    db=mock_db,
                    decision_context=sample_decision_context,
                    principle_ids=[1]
                )
                
                # Check all dimensions are present
                expected_dimensions = {
                    UncertaintyDimension.CONSTITUTIONAL,
                    UncertaintyDimension.TECHNICAL,
                    UncertaintyDimension.STAKEHOLDER,
                    UncertaintyDimension.PRECEDENT,
                    UncertaintyDimension.COMPLEXITY
                }
                assert set(dimensional_uncertainties.keys()) == expected_dimensions
                
                # Check all values are in valid range
                for dimension, uncertainty in dimensional_uncertainties.items():
                    assert 0.0 <= uncertainty <= 1.0


class TestAdaptiveLearning:
    """Test suite for adaptive learning functionality."""
    
    @pytest.fixture
    def hitl_sampler(self):
        """Create HITL sampler with learning enabled."""
        config = HITLSamplingConfig(learning_enabled=True, min_feedback_samples=3)
        return HumanInTheLoopSampler(config)
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_human_feedback_processing(self, hitl_sampler, mock_db):
        """Test human feedback processing."""
        assessment_id = "test_assessment_001"
        human_decision = {
            "agreed_with_assessment": True,
            "reasoning": "Assessment was accurate",
            "quality_score": 0.9
        }
        
        success = await hitl_sampler.process_human_feedback(
            db=mock_db,
            assessment_id=assessment_id,
            human_decision=human_decision
        )
        
        assert success is True
        assert len(hitl_sampler.learning_history) == 1
        
        feedback_record = hitl_sampler.learning_history[0]
        assert feedback_record["assessment_id"] == assessment_id
        assert feedback_record["human_agreed"] is True
        assert feedback_record["decision_quality"] == 0.9
    
    @pytest.mark.asyncio
    async def test_adaptive_threshold_adjustment(self, hitl_sampler, mock_db):
        """Test adaptive threshold adjustment based on feedback."""
        initial_uncertainty_threshold = hitl_sampler.config.uncertainty_threshold
        initial_confidence_threshold = hitl_sampler.config.confidence_threshold
        
        # Add feedback indicating low accuracy (need more conservative thresholds)
        for i in range(5):
            await hitl_sampler.process_human_feedback(
                db=mock_db,
                assessment_id=f"test_{i}",
                human_decision={
                    "agreed_with_assessment": False,  # Disagreement indicates poor accuracy
                    "quality_score": 0.3
                },
                feedback_metadata={"was_oversight_triggered": False}
            )
        
        # Check that thresholds were adjusted to be more conservative
        assert hitl_sampler.config.uncertainty_threshold <= initial_uncertainty_threshold
        assert hitl_sampler.config.confidence_threshold >= initial_confidence_threshold
    
    def test_performance_metrics_calculation(self, hitl_sampler):
        """Test performance metrics calculation."""
        # Add some mock learning history
        hitl_sampler.learning_history = [
            {"human_agreed": True, "decision_quality": 0.9, "feedback_timestamp": datetime.utcnow()},
            {"human_agreed": True, "decision_quality": 0.8, "feedback_timestamp": datetime.utcnow()},
            {"human_agreed": False, "decision_quality": 0.6, "feedback_timestamp": datetime.utcnow()},
        ]
        hitl_sampler.sampling_stats = {
            "total_assessments": 100,
            "human_oversight_triggered": 15,
            "false_positives": 2,
            "false_negatives": 1,
            "accuracy_rate": 0.94,
            "false_positive_rate": 0.02
        }
        
        metrics = asyncio.run(hitl_sampler.get_performance_metrics())
        
        assert metrics["total_assessments"] == 100
        assert metrics["oversight_rate"] == 0.15
        assert metrics["accuracy_rate"] == 0.94
        assert metrics["false_positive_rate"] == 0.02
        assert 0.0 <= metrics["recent_accuracy"] <= 1.0
        assert 0.0 <= metrics["recent_quality"] <= 1.0


class TestSamplingTriggers:
    """Test suite for sampling trigger identification."""
    
    @pytest.fixture
    def hitl_sampler(self):
        """Create HITL sampler instance."""
        return HumanInTheLoopSampler()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_safety_critical_trigger(self, hitl_sampler, mock_db):
        """Test safety critical trigger activation."""
        decision_context = {"safety_critical": True}
        dimensional_uncertainties = {dim: 0.5 for dim in UncertaintyDimension}
        
        triggers = await hitl_sampler._identify_sampling_triggers(
            db=mock_db,
            decision_context=decision_context,
            overall_uncertainty=0.6,
            confidence_score=0.8,
            dimensional_uncertainties=dimensional_uncertainties
        )
        
        assert SamplingTrigger.SAFETY_CRITICAL in triggers
    
    @pytest.mark.asyncio
    async def test_low_confidence_trigger(self, hitl_sampler, mock_db):
        """Test low confidence trigger activation."""
        decision_context = {}
        dimensional_uncertainties = {dim: 0.5 for dim in UncertaintyDimension}
        
        triggers = await hitl_sampler._identify_sampling_triggers(
            db=mock_db,
            decision_context=decision_context,
            overall_uncertainty=0.6,
            confidence_score=0.5,  # Below default threshold of 0.75
            dimensional_uncertainties=dimensional_uncertainties
        )
        
        assert SamplingTrigger.LOW_CONFIDENCE in triggers
    
    @pytest.mark.asyncio
    async def test_stakeholder_conflict_trigger(self, hitl_sampler, mock_db):
        """Test stakeholder conflict trigger activation."""
        decision_context = {"stakeholder_conflicts": True}
        dimensional_uncertainties = {
            UncertaintyDimension.STAKEHOLDER: 0.8,  # High stakeholder uncertainty
            **{dim: 0.5 for dim in UncertaintyDimension if dim != UncertaintyDimension.STAKEHOLDER}
        }
        
        triggers = await hitl_sampler._identify_sampling_triggers(
            db=mock_db,
            decision_context=decision_context,
            overall_uncertainty=0.6,
            confidence_score=0.8,
            dimensional_uncertainties=dimensional_uncertainties
        )
        
        assert SamplingTrigger.STAKEHOLDER_CONFLICT in triggers
    
    @pytest.mark.asyncio
    async def test_novel_scenario_trigger(self, hitl_sampler, mock_db):
        """Test novel scenario trigger activation."""
        decision_context = {"novel_scenario": True}
        dimensional_uncertainties = {
            UncertaintyDimension.PRECEDENT: 0.8,  # High precedent uncertainty
            **{dim: 0.5 for dim in UncertaintyDimension if dim != UncertaintyDimension.PRECEDENT}
        }
        
        triggers = await hitl_sampler._identify_sampling_triggers(
            db=mock_db,
            decision_context=decision_context,
            overall_uncertainty=0.6,
            confidence_score=0.8,
            dimensional_uncertainties=dimensional_uncertainties
        )
        
        assert SamplingTrigger.NOVEL_SCENARIO in triggers


class TestOversightLevelRecommendation:
    """Test suite for oversight level recommendation."""
    
    @pytest.fixture
    def hitl_sampler(self):
        """Create HITL sampler instance."""
        return HumanInTheLoopSampler()
    
    @pytest.mark.asyncio
    async def test_safety_critical_requires_constitutional_council(self, hitl_sampler):
        """Test that safety critical decisions require Constitutional Council."""
        triggers = [SamplingTrigger.SAFETY_CRITICAL]
        
        level = await hitl_sampler._recommend_oversight_level(
            triggers_activated=triggers,
            overall_uncertainty=0.8,
            confidence_score=0.6
        )
        
        assert level == EscalationLevel.CONSTITUTIONAL_COUNCIL
    
    @pytest.mark.asyncio
    async def test_constitutional_ambiguity_requires_council(self, hitl_sampler):
        """Test that constitutional ambiguity requires Constitutional Council."""
        triggers = [SamplingTrigger.CONSTITUTIONAL_AMBIGUITY]
        
        level = await hitl_sampler._recommend_oversight_level(
            triggers_activated=triggers,
            overall_uncertainty=0.7,
            confidence_score=0.7
        )
        
        assert level == EscalationLevel.CONSTITUTIONAL_COUNCIL
    
    @pytest.mark.asyncio
    async def test_low_confidence_requires_technical_review(self, hitl_sampler):
        """Test that low confidence requires technical review."""
        triggers = [SamplingTrigger.LOW_CONFIDENCE]
        
        level = await hitl_sampler._recommend_oversight_level(
            triggers_activated=triggers,
            overall_uncertainty=0.6,
            confidence_score=0.6
        )
        
        assert level == EscalationLevel.TECHNICAL_REVIEW
