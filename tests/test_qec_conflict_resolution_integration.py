"""
test_qec_conflict_resolution_integration.py

Integration tests for QEC-enhanced conflict resolution system.
Tests end-to-end workflows including API endpoints, database operations,
and Constitutional Fidelity Monitor integration.
"""

import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

# Import test dependencies
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend', 'ac_service'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend', 'shared'))

try:
    from app.main import app
    from app.api.v1.conflict_resolution import router
    from app.services.qec_conflict_resolver import QECConflictResolver
    from models import ACPrinciple, ACConflictResolution
except ImportError:
    # Fallback for testing without full service setup
    from unittest.mock import Mock
    app = Mock()
    router = Mock()
    QECConflictResolver = Mock()
    ACPrinciple = Mock()
    ACConflictResolution = Mock()


class TestQECConflictResolutionIntegration:
    """Integration test suite for QEC-enhanced conflict resolution."""
    
    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return Mock(id=1, username="test_user", roles=["admin"])
    
    @pytest.fixture
    def sample_conflict_data(self):
        """Sample conflict resolution data for testing."""
        return {
            "conflict_type": "principle_contradiction",
            "principle_ids": [1, 2],
            "context": "privacy_vs_security_testing",
            "conflict_description": "Privacy protection conflicts with security monitoring requirements",
            "severity": "high",
            "resolution_strategy": "weighted_priority",
            "resolution_details": {
                "weights": {"privacy": 0.6, "security": 0.4}
            },
            "precedence_order": [1, 2]
        }
    
    @pytest.fixture
    def sample_principles(self):
        """Sample AC principles for testing."""
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
                    "criteria": ["encryption", "access_control"]
                }
            },
            {
                "id": 2,
                "title": "Security Enforcement",
                "description": "Ensure system security",
                "category": "security",
                "priority_weight": 0.9,
                "scope": "system_access",
                "normative_statement": "Security must be enforced",
                "constraints": {"monitoring": "continuous"},
                "rationale": "Security prevents threats",
                "validation_criteria_structured": {
                    "type": "security_check",
                    "criteria": ["authentication", "monitoring"]
                }
            }
        ]
    
    @pytest.mark.asyncio
    async def test_create_conflict_resolution_with_qec_enhancement(
        self, 
        client, 
        sample_conflict_data,
        sample_principles
    ):
        """Test creating conflict resolution with QEC enhancement."""
        with patch('ac_service.app.crud.create_ac_conflict_resolution') as mock_create, \
             patch('ac_service.app.crud.get_ac_principles_by_ids') as mock_get_principles, \
             patch('ac_service.app.crud.update_ac_conflict_resolution') as mock_update, \
             patch('ac_service.app.api.v1.conflict_resolution.get_current_user') as mock_user, \
             patch('ac_service.app.api.v1.conflict_resolution.require_roles') as mock_roles:
            
            # Setup mocks
            mock_conflict = Mock()
            mock_conflict.id = 1
            mock_conflict.resolution_details = {}
            mock_conflict.principle_ids = [1, 2]
            mock_create.return_value = mock_conflict
            
            mock_principles = [Mock(**p) for p in sample_principles]
            mock_get_principles.return_value = mock_principles
            
            mock_update.return_value = mock_conflict
            mock_user.return_value = Mock(id=1)
            mock_roles.return_value = lambda: Mock(id=1)
            
            # Make request
            response = client.post(
                "/api/v1/conflict-resolution/",
                json=sample_conflict_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Verify response
            assert response.status_code == 200
            
            # Verify QEC enhancement was attempted
            mock_create.assert_called_once()
            mock_get_principles.assert_called_once_with(mock.ANY, [1, 2])
    
    @pytest.mark.asyncio
    async def test_list_conflicts_with_qec_prioritization(
        self, 
        client,
        sample_principles
    ):
        """Test listing conflicts with QEC-based prioritization."""
        with patch('ac_service.app.crud.get_ac_conflict_resolutions') as mock_get_conflicts, \
             patch('ac_service.app.api.v1.conflict_resolution.get_current_user') as mock_user:
            
            # Setup mock conflicts with different QEC analysis
            mock_conflicts = [
                Mock(
                    id=1,
                    resolution_details={
                        "qec_analysis": {"priority_score": 0.8}
                    }
                ),
                Mock(
                    id=2,
                    resolution_details={
                        "qec_analysis": {"priority_score": 0.3}
                    }
                ),
                Mock(
                    id=3,
                    resolution_details={
                        "qec_analysis": {"priority_score": 0.6}
                    }
                )
            ]
            mock_get_conflicts.return_value = mock_conflicts
            mock_user.return_value = Mock(id=1)
            
            # Make request with QEC prioritization
            response = client.get(
                "/api/v1/conflict-resolution/?priority_order=qec",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Verify response
            assert response.status_code == 200
            
            # Verify conflicts were retrieved
            mock_get_conflicts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_conflict_patch(
        self, 
        client,
        sample_principles
    ):
        """Test automated patch generation for conflict resolution."""
        with patch('ac_service.app.crud.get_ac_conflict_resolution') as mock_get_conflict, \
             patch('ac_service.app.crud.get_ac_principles_by_ids') as mock_get_principles, \
             patch('ac_service.app.api.v1.conflict_resolution.get_current_user') as mock_user, \
             patch('ac_service.app.api.v1.conflict_resolution.require_roles') as mock_roles:
            
            # Setup mocks
            mock_conflict = Mock()
            mock_conflict.id = 1
            mock_conflict.principle_ids = [1, 2]
            mock_conflict.conflict_type = "principle_contradiction"
            mock_conflict.resolution_details = {
                "qec_analysis": {
                    "constitutional_distances": [0.3, 0.4],
                    "average_distance": 0.35,
                    "error_predictions": [],
                    "recommended_strategy": "weighted_priority",
                    "validation_scenarios": [],
                    "priority_score": 0.7,
                    "qec_metadata": {}
                }
            }
            mock_get_conflict.return_value = mock_conflict
            
            mock_principles = [Mock(**p) for p in sample_principles]
            mock_get_principles.return_value = mock_principles
            
            mock_user.return_value = Mock(id=1)
            mock_roles.return_value = lambda: Mock(id=1)
            
            # Make request
            response = client.post(
                "/api/v1/conflict-resolution/1/generate-patch",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            assert "conflict_id" in response_data
            assert "patch_generated" in response_data
            assert "strategy_used" in response_data
            assert "confidence_score" in response_data
    
    @pytest.mark.asyncio
    async def test_get_qec_insights(
        self, 
        client
    ):
        """Test retrieving QEC insights for a conflict."""
        with patch('ac_service.app.crud.get_ac_conflict_resolution') as mock_get_conflict, \
             patch('ac_service.app.api.v1.conflict_resolution.get_current_user') as mock_user:
            
            # Setup mock conflict with QEC analysis
            mock_conflict = Mock()
            mock_conflict.id = 1
            mock_conflict.resolution_details = {
                "qec_analysis": {
                    "constitutional_distances": [0.3, 0.4],
                    "average_distance": 0.35,
                    "error_predictions": [
                        {
                            "principle_id": "1",
                            "overall_risk": 0.4,
                            "recommended_strategy": "enhanced_validation",
                            "confidence": 0.8
                        }
                    ],
                    "recommended_strategy": "weighted_priority",
                    "priority_score": 0.7,
                    "validation_scenarios": [
                        {
                            "principle_id": "1",
                            "scenario_type": "privacy_check",
                            "test_cases": 3
                        }
                    ],
                    "qec_metadata": {
                        "analysis_timestamp": "2024-01-15T14:30:00"
                    }
                }
            }
            mock_get_conflict.return_value = mock_conflict
            mock_user.return_value = Mock(id=1)
            
            # Make request
            response = client.get(
                "/api/v1/conflict-resolution/1/qec-insights",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["qec_enhanced"] is True
            assert response_data["constitutional_distances"] == [0.3, 0.4]
            assert response_data["average_distance"] == 0.35
            assert response_data["priority_score"] == 0.7
            assert len(response_data["error_predictions"]) == 1
            assert len(response_data["validation_scenarios"]) == 1
    
    @pytest.mark.asyncio
    async def test_constitutional_fidelity_monitoring(
        self, 
        client
    ):
        """Test Constitutional Fidelity Monitor endpoints."""
        with patch('ac_service.app.crud.get_ac_principles') as mock_get_principles, \
             patch('ac_service.app.api.v1.fidelity_monitor.get_current_user') as mock_user:
            
            mock_principles = [Mock(**p) for p in [
                {"id": 1, "title": "Test Principle 1"},
                {"id": 2, "title": "Test Principle 2"}
            ]]
            mock_get_principles.return_value = mock_principles
            mock_user.return_value = Mock(id=1)
            
            # Test current fidelity endpoint
            response = client.get(
                "/api/v1/fidelity/current",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Should return either fidelity data or 501 if QEC not available
            assert response.status_code in [200, 501]
            
            if response.status_code == 200:
                response_data = response.json()
                assert "composite_score" in response_data
                assert "level" in response_data
                assert "components" in response_data
    
    @pytest.mark.asyncio
    async def test_qec_resolver_service_integration(self):
        """Test QEC resolver service integration."""
        resolver = QECConflictResolver()
        
        # Create test data
        principles = [
            ACPrinciple(
                id=1,
                title="Test Principle 1",
                description="Test description 1",
                category="test",
                priority_weight=0.7,
                validation_criteria_structured={"type": "test_check"}
            )
        ]
        
        conflict = ACConflictResolution(
            id=1,
            conflict_type="test_conflict",
            principle_ids=[1],
            context="test_context",
            conflict_description="Test conflict",
            severity="medium",
            resolution_strategy="test_strategy",
            resolution_details={},
            status="identified",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Test analysis
        analysis = await resolver.analyze_conflict(conflict, principles)
        assert analysis.conflict_id == 1
        assert len(analysis.constitutional_distances) == 1
        assert analysis.priority_score >= 0
        
        # Test patch generation
        patch_result = await resolver.generate_patch(conflict, principles, analysis)
        assert patch_result.confidence_score >= 0
        
        # Test prioritization
        conflicts_with_analysis = [(conflict, analysis)]
        prioritized = resolver.prioritize_conflicts(conflicts_with_analysis)
        assert len(prioritized) == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(
        self, 
        client
    ):
        """Test error handling and fallback behavior."""
        with patch('ac_service.app.crud.get_ac_conflict_resolution') as mock_get_conflict, \
             patch('ac_service.app.api.v1.conflict_resolution.get_current_user') as mock_user:
            
            # Test 404 for non-existent conflict
            mock_get_conflict.return_value = None
            mock_user.return_value = Mock(id=1)
            
            response = client.get(
                "/api/v1/conflict-resolution/999/qec-insights",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 404
            
            # Test conflict without QEC analysis
            mock_conflict = Mock()
            mock_conflict.id = 1
            mock_conflict.resolution_details = {}
            mock_get_conflict.return_value = mock_conflict
            
            response = client.get(
                "/api/v1/conflict-resolution/1/qec-insights",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["qec_enhanced"] is False
            assert "message" in response_data


@pytest.mark.asyncio
async def test_end_to_end_qec_conflict_workflow():
    """End-to-end test of QEC-enhanced conflict resolution workflow."""
    resolver = QECConflictResolver()
    
    # Step 1: Create principles
    principles = [
        ACPrinciple(
            id=1,
            title="Privacy First",
            description="Prioritize user privacy",
            category="privacy",
            priority_weight=0.8,
            validation_criteria_structured={
                "type": "privacy_validation",
                "criteria": ["data_minimization", "consent_required"]
            }
        ),
        ACPrinciple(
            id=2,
            title="Security Monitoring",
            description="Monitor for security threats",
            category="security",
            priority_weight=0.9,
            validation_criteria_structured={
                "type": "security_validation",
                "criteria": ["threat_detection", "access_logging"]
            }
        )
    ]
    
    # Step 2: Create conflict
    conflict = ACConflictResolution(
        id=1,
        conflict_type="principle_contradiction",
        principle_ids=[1, 2],
        context="privacy_vs_security",
        conflict_description="Privacy minimization conflicts with security logging",
        severity="high",
        resolution_strategy="to_be_determined",
        resolution_details={},
        status="identified",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Step 3: Perform QEC analysis
    analysis = await resolver.analyze_conflict(conflict, principles)
    
    # Verify analysis results
    assert analysis.conflict_id == 1
    assert len(analysis.constitutional_distances) == 2
    assert analysis.average_distance >= 0
    assert analysis.priority_score >= 0
    
    # Step 4: Generate patch
    patch_result = await resolver.generate_patch(conflict, principles, analysis)
    
    # Verify patch generation
    assert patch_result.confidence_score >= 0
    assert patch_result.metadata is not None
    
    # Step 5: Test prioritization
    conflicts_with_analysis = [(conflict, analysis)]
    prioritized = resolver.prioritize_conflicts(conflicts_with_analysis)
    
    # Verify prioritization
    assert len(prioritized) == 1
    assert prioritized[0][0] == conflict
    assert prioritized[0][1] == analysis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
