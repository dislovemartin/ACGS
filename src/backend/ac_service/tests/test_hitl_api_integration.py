"""
Integration tests for Human-in-the-Loop Sampling API endpoints

Tests the complete API functionality including:
- Uncertainty assessment endpoints
- Human oversight triggering
- Feedback processing
- Performance metrics
- Configuration management
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.schemas import HITLSamplingRequest, HITLFeedbackRequest
from shared.models import User


class TestHITLSamplingAPI:
    """Test suite for HITL sampling API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        return Mock(
            id=1,
            username="test_user",
            roles=["admin", "policy_manager"]
        )
    
    @pytest.fixture
    def sample_hitl_request(self):
        """Create sample HITL sampling request."""
        return {
            "decision_id": "test_decision_001",
            "decision_context": {
                "policy_type": "privacy_protection",
                "affected_users": 1000,
                "regulatory_compliance": True
            },
            "ai_confidence": 0.72,
            "principle_ids": [1, 3, 7],
            "decision_scope": "system",
            "safety_critical": True,
            "stakeholder_count": 5,
            "stakeholder_conflicts": True,
            "time_pressure": "high",
            "impact_magnitude": "high"
        }
    
    def test_assess_uncertainty_endpoint(self, client, sample_hitl_request, mock_user):
        """Test uncertainty assessment endpoint."""
        with patch('app.api.hitl_sampling.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('app.api.hitl_sampling.get_db') as mock_get_db:
                mock_db = AsyncMock(spec=AsyncSession)
                mock_get_db.return_value = mock_db
                
                with patch('app.api.hitl_sampling.hitl_sampler.assess_uncertainty') as mock_assess:
                    # Mock assessment result
                    from app.services.human_in_the_loop_sampler import UncertaintyAssessment, UncertaintyDimension, SamplingTrigger
                    from app.services.human_escalation_system import EscalationLevel
                    from datetime import datetime
                    
                    mock_assessment = UncertaintyAssessment(
                        decision_id="test_decision_001",
                        overall_uncertainty=0.78,
                        dimensional_uncertainties={
                            UncertaintyDimension.CONSTITUTIONAL: 0.65,
                            UncertaintyDimension.TECHNICAL: 0.45,
                            UncertaintyDimension.STAKEHOLDER: 0.85,
                            UncertaintyDimension.PRECEDENT: 0.70,
                            UncertaintyDimension.COMPLEXITY: 0.75
                        },
                        confidence_score=0.72,
                        triggers_activated=[
                            SamplingTrigger.HIGH_UNCERTAINTY,
                            SamplingTrigger.STAKEHOLDER_CONFLICT,
                            SamplingTrigger.SAFETY_CRITICAL
                        ],
                        requires_human_oversight=True,
                        recommended_oversight_level=EscalationLevel.CONSTITUTIONAL_COUNCIL,
                        assessment_metadata={"test": "metadata"},
                        timestamp=datetime.utcnow()
                    )
                    mock_assess.return_value = mock_assessment
                    
                    response = client.post("/api/v1/hitl-sampling/assess", json=sample_hitl_request)
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["decision_id"] == "test_decision_001"
                    assert data["overall_uncertainty"] == 0.78
                    assert data["confidence_score"] == 0.72
                    assert data["requires_human_oversight"] is True
                    assert data["recommended_oversight_level"] == "constitutional_council"
                    assert "high_uncertainty" in data["triggers_activated"]
                    assert "stakeholder_conflict" in data["triggers_activated"]
                    assert "safety_critical" in data["triggers_activated"]
                    
                    # Check dimensional uncertainties
                    dim_uncertainties = data["dimensional_uncertainties"]
                    assert dim_uncertainties["constitutional"] == 0.65
                    assert dim_uncertainties["technical"] == 0.45
                    assert dim_uncertainties["stakeholder"] == 0.85
                    assert dim_uncertainties["precedent"] == 0.70
                    assert dim_uncertainties["complexity"] == 0.75
    
    def test_trigger_oversight_endpoint(self, client, sample_hitl_request, mock_user):
        """Test human oversight triggering endpoint."""
        with patch('app.api.hitl_sampling.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('app.api.hitl_sampling.get_db') as mock_get_db:
                mock_db = AsyncMock(spec=AsyncSession)
                mock_get_db.return_value = mock_db
                
                with patch('app.api.hitl_sampling.hitl_sampler.assess_uncertainty') as mock_assess:
                    with patch('app.api.hitl_sampling.hitl_sampler.trigger_human_oversight') as mock_trigger:
                        # Mock assessment and escalation
                        from app.services.human_in_the_loop_sampler import UncertaintyAssessment, SamplingTrigger
                        from app.services.human_escalation_system import EscalationLevel, EscalationRequest
                        from datetime import datetime
                        
                        mock_assessment = UncertaintyAssessment(
                            decision_id="test_decision_001",
                            overall_uncertainty=0.85,
                            dimensional_uncertainties={},
                            confidence_score=0.60,
                            triggers_activated=[SamplingTrigger.SAFETY_CRITICAL],
                            requires_human_oversight=True,
                            recommended_oversight_level=EscalationLevel.CONSTITUTIONAL_COUNCIL,
                            assessment_metadata={},
                            timestamp=datetime.utcnow()
                        )
                        mock_assess.return_value = mock_assessment
                        
                        mock_escalation = Mock()
                        mock_escalation.request_id = "escalation_001"
                        mock_trigger.return_value = mock_escalation
                        
                        response = client.post("/api/v1/hitl-sampling/trigger-oversight", json=sample_hitl_request)
                        
                        assert response.status_code == 200
                        data = response.json()
                        
                        assert data["decision_id"] == "test_decision_001"
                        assert data["oversight_triggered"] is True
                        assert data["oversight_level"] == "constitutional_council"
                        assert data["escalation_request_id"] == "escalation_001"
                        assert data["overall_uncertainty"] == 0.85
                        assert data["confidence_score"] == 0.60
    
    def test_submit_feedback_endpoint(self, client, mock_user):
        """Test human feedback submission endpoint."""
        feedback_request = {
            "assessment_id": "test_assessment_001",
            "human_decision": {
                "oversight_needed": True,
                "final_decision": "approved_with_conditions",
                "conditions": ["additional_stakeholder_review", "security_audit"]
            },
            "agreed_with_assessment": True,
            "reasoning": "Assessment correctly identified stakeholder conflicts",
            "quality_score": 0.9
        }
        
        with patch('app.api.hitl_sampling.require_roles') as mock_require_roles:
            mock_require_roles.return_value = lambda: mock_user
            
            with patch('app.api.hitl_sampling.get_db') as mock_get_db:
                mock_db = AsyncMock(spec=AsyncSession)
                mock_get_db.return_value = mock_db
                
                with patch('app.api.hitl_sampling.hitl_sampler.process_human_feedback') as mock_process:
                    mock_process.return_value = True
                    
                    response = client.post("/api/v1/hitl-sampling/feedback", json=feedback_request)
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["success"] is True
                    assert data["assessment_id"] == "test_assessment_001"
                    assert data["feedback_processed"] is True
    
    def test_get_metrics_endpoint(self, client, mock_user):
        """Test performance metrics endpoint."""
        with patch('app.api.hitl_sampling.require_roles') as mock_require_roles:
            mock_require_roles.return_value = lambda: mock_user
            
            with patch('app.api.hitl_sampling.hitl_sampler.get_performance_metrics') as mock_get_metrics:
                mock_metrics = {
                    "total_assessments": 1250,
                    "human_oversight_triggered": 187,
                    "oversight_rate": 0.15,
                    "accuracy_rate": 0.94,
                    "false_positive_rate": 0.04,
                    "recent_accuracy": 0.96,
                    "recent_quality": 0.88,
                    "current_thresholds": {
                        "uncertainty_threshold": 0.75,
                        "confidence_threshold": 0.75
                    },
                    "learning_enabled": True,
                    "feedback_samples": 89,
                    "threshold_adjustments_count": 3
                }
                mock_get_metrics.return_value = mock_metrics
                
                response = client.get("/api/v1/hitl-sampling/metrics")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["total_assessments"] == 1250
                assert data["oversight_rate"] == 0.15
                assert data["accuracy_rate"] == 0.94
                assert data["false_positive_rate"] == 0.04
                assert data["learning_enabled"] is True
    
    def test_get_config_endpoint(self, client, mock_user):
        """Test configuration retrieval endpoint."""
        with patch('app.api.hitl_sampling.require_roles') as mock_require_roles:
            mock_require_roles.return_value = lambda: mock_user
            
            response = client.get("/api/v1/hitl-sampling/config")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "uncertainty_threshold" in data
            assert "confidence_threshold" in data
            assert "dimensional_weights" in data
            assert "learning_enabled" in data
            assert "adaptation_rate" in data
    
    def test_update_config_endpoint(self, client, mock_user):
        """Test configuration update endpoint."""
        config_updates = {
            "uncertainty_threshold": 0.8,
            "confidence_threshold": 0.7,
            "learning_enabled": False,
            "adaptation_rate": 0.15
        }
        
        with patch('app.api.hitl_sampling.require_roles') as mock_require_roles:
            mock_require_roles.return_value = lambda: mock_user
            
            response = client.put("/api/v1/hitl-sampling/config", json=config_updates)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "updated_fields" in data
            assert "current_config" in data
            assert data["current_config"]["uncertainty_threshold"] == 0.8
            assert data["current_config"]["confidence_threshold"] == 0.7
            assert data["current_config"]["learning_enabled"] is False
    
    def test_invalid_config_update(self, client, mock_user):
        """Test invalid configuration update."""
        invalid_config = {
            "uncertainty_threshold": 1.5,  # Invalid: > 1.0
            "confidence_threshold": -0.1   # Invalid: < 0.0
        }
        
        with patch('app.api.hitl_sampling.require_roles') as mock_require_roles:
            mock_require_roles.return_value = lambda: mock_user
            
            response = client.put("/api/v1/hitl-sampling/config", json=invalid_config)
            
            assert response.status_code == 400
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        with patch('app.api.hitl_sampling.get_current_user') as mock_get_user:
            mock_get_user.side_effect = Exception("Unauthorized")
            
            response = client.post("/api/v1/hitl-sampling/assess", json={})
            assert response.status_code == 500  # Should be handled by exception handler
    
    def test_assessment_error_handling(self, client, sample_hitl_request, mock_user):
        """Test error handling in assessment endpoint."""
        with patch('app.api.hitl_sampling.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('app.api.hitl_sampling.get_db') as mock_get_db:
                mock_db = AsyncMock(spec=AsyncSession)
                mock_get_db.return_value = mock_db
                
                with patch('app.api.hitl_sampling.hitl_sampler.assess_uncertainty') as mock_assess:
                    mock_assess.side_effect = Exception("Assessment failed")
                    
                    response = client.post("/api/v1/hitl-sampling/assess", json=sample_hitl_request)
                    
                    assert response.status_code == 500
                    assert "Assessment failed" in response.json()["detail"]


class TestHITLIntegrationWorkflow:
    """Test suite for end-to-end HITL workflow integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        return Mock(
            id=1,
            username="admin_user",
            roles=["admin", "policy_manager", "constitutional_council"]
        )
    
    def test_complete_hitl_workflow(self, client, mock_admin_user):
        """Test complete HITL workflow from assessment to feedback."""
        # Step 1: Assess uncertainty
        assessment_request = {
            "decision_id": "workflow_test_001",
            "decision_context": {"test": "context"},
            "ai_confidence": 0.6,
            "safety_critical": True
        }
        
        with patch('app.api.hitl_sampling.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_admin_user
            
            with patch('app.api.hitl_sampling.get_db') as mock_get_db:
                mock_db = AsyncMock(spec=AsyncSession)
                mock_get_db.return_value = mock_db
                
                with patch('app.api.hitl_sampling.hitl_sampler.assess_uncertainty') as mock_assess:
                    # Mock high uncertainty assessment
                    from app.services.human_in_the_loop_sampler import UncertaintyAssessment, SamplingTrigger
                    from app.services.human_escalation_system import EscalationLevel
                    from datetime import datetime
                    
                    mock_assessment = UncertaintyAssessment(
                        decision_id="workflow_test_001",
                        overall_uncertainty=0.85,
                        dimensional_uncertainties={},
                        confidence_score=0.6,
                        triggers_activated=[SamplingTrigger.SAFETY_CRITICAL],
                        requires_human_oversight=True,
                        recommended_oversight_level=EscalationLevel.CONSTITUTIONAL_COUNCIL,
                        assessment_metadata={},
                        timestamp=datetime.utcnow()
                    )
                    mock_assess.return_value = mock_assessment
                    
                    # Step 1: Assessment
                    response = client.post("/api/v1/hitl-sampling/assess", json=assessment_request)
                    assert response.status_code == 200
                    assessment_data = response.json()
                    assert assessment_data["requires_human_oversight"] is True
                    
                    # Step 2: Trigger oversight
                    with patch('app.api.hitl_sampling.hitl_sampler.trigger_human_oversight') as mock_trigger:
                        mock_escalation = Mock()
                        mock_escalation.request_id = "escalation_workflow_001"
                        mock_trigger.return_value = mock_escalation
                        
                        response = client.post("/api/v1/hitl-sampling/trigger-oversight", json=assessment_request)
                        assert response.status_code == 200
                        oversight_data = response.json()
                        assert oversight_data["oversight_triggered"] is True
                        
                        # Step 3: Submit feedback
                        with patch('app.api.hitl_sampling.require_roles') as mock_require_roles:
                            mock_require_roles.return_value = lambda: mock_admin_user
                            
                            with patch('app.api.hitl_sampling.hitl_sampler.process_human_feedback') as mock_feedback:
                                mock_feedback.return_value = True
                                
                                feedback_request = {
                                    "assessment_id": "workflow_test_001",
                                    "human_decision": {"oversight_needed": True},
                                    "agreed_with_assessment": True,
                                    "quality_score": 0.9
                                }
                                
                                response = client.post("/api/v1/hitl-sampling/feedback", json=feedback_request)
                                assert response.status_code == 200
                                feedback_data = response.json()
                                assert feedback_data["success"] is True
                                
                                # Step 4: Check metrics
                                with patch('app.api.hitl_sampling.hitl_sampler.get_performance_metrics') as mock_metrics:
                                    mock_metrics.return_value = {
                                        "total_assessments": 1,
                                        "human_oversight_triggered": 1,
                                        "oversight_rate": 1.0,
                                        "accuracy_rate": 1.0,
                                        "false_positive_rate": 0.0,
                                        "recent_accuracy": 1.0,
                                        "recent_quality": 0.9,
                                        "current_thresholds": {"uncertainty_threshold": 0.75, "confidence_threshold": 0.75},
                                        "learning_enabled": True,
                                        "feedback_samples": 1,
                                        "threshold_adjustments_count": 0
                                    }
                                    
                                    response = client.get("/api/v1/hitl-sampling/metrics")
                                    assert response.status_code == 200
                                    metrics_data = response.json()
                                    assert metrics_data["total_assessments"] == 1
                                    assert metrics_data["oversight_rate"] == 1.0
