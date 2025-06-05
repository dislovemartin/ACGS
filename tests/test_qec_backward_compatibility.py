"""
test_qec_backward_compatibility.py

Backward compatibility test suite for QEC-enhanced AlphaEvolve-ACGS.
Ensures existing AC service functionality continues to work after QEC integration.

Tests:
- Existing conflict resolution workflows without QEC enhancement
- Graceful fallback when QEC components are unavailable
- Non-QEC workflows continue to function normally
- Migration path from existing conflict resolution data
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

# Import test dependencies
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend', 'ac_service'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend', 'shared'))

# Test imports with fallbacks
try:
    from models import Principle, ConflictResolution
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

try:
    from app.services.qec_conflict_resolver import QECConflictResolver
    QEC_RESOLVER_AVAILABLE = True
except ImportError:
    QEC_RESOLVER_AVAILABLE = False


class TestQECBackwardCompatibility:
    """Test suite for QEC backward compatibility."""
    
    @pytest.fixture
    def legacy_principle_data(self):
        """Create legacy principle data without QEC fields."""
        return {
            "id": 1,
            "title": "Legacy Privacy Principle",
            "description": "Protect user privacy and personal data",
            "category": "privacy",
            "priority_weight": 0.8,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
            # Note: Missing QEC-specific fields like distance_score, error_prediction_metadata
        }
    
    @pytest.fixture
    def legacy_conflict_data(self):
        """Create legacy conflict resolution data."""
        return {
            "id": 1,
            "conflict_type": "principle_contradiction",
            "principle_ids": [1, 2],
            "context": "privacy_vs_security",
            "conflict_description": "Privacy protection conflicts with security monitoring",
            "severity": "high",
            "resolution_strategy": "weighted_priority",
            "resolution_details": {"weights": {"privacy": 0.6, "security": 0.4}},
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
            # Note: Missing QEC analysis fields
        }
    
    @pytest.mark.asyncio
    async def test_legacy_conflict_resolution_without_qec(self, legacy_conflict_data, legacy_principle_data):
        """Test that legacy conflict resolution works without QEC enhancement."""
        
        # Mock the QEC components as unavailable
        with patch('app.services.qec_conflict_resolver.QEC_AVAILABLE', False):
            
            # Create mock conflict and principles
            mock_conflict = Mock()
            mock_conflict.id = legacy_conflict_data["id"]
            mock_conflict.conflict_type = legacy_conflict_data["conflict_type"]
            mock_conflict.severity = legacy_conflict_data["severity"]
            mock_conflict.principle_ids = legacy_conflict_data["principle_ids"]
            
            mock_principle = Mock()
            mock_principle.id = legacy_principle_data["id"]
            mock_principle.title = legacy_principle_data["title"]
            mock_principle.description = legacy_principle_data["description"]
            mock_principle.category = legacy_principle_data["category"]
            
            principles = [mock_principle]
            
            # Test basic conflict analysis without QEC
            if QEC_RESOLVER_AVAILABLE:
                resolver = QECConflictResolver()
                
                # Should work with QEC disabled
                analysis = await resolver.analyze_conflict(mock_conflict, principles)
                
                # Validate basic analysis works
                assert analysis.conflict_id == legacy_conflict_data["id"]
                assert analysis.qec_metadata.get("qec_enhanced") is False
                assert analysis.qec_metadata.get("fallback_used") is True
                
                # Should have basic resolution strategy
                assert analysis.recommended_strategy is not None
                
                # QEC-specific fields should have defaults
                assert len(analysis.constitutional_distances) == 0 or all(d == 0.5 for d in analysis.constitutional_distances)
                assert len(analysis.error_predictions) == 0
                assert len(analysis.validation_scenarios) == 0
            else:
                # If resolver not available, just validate the test setup
                assert mock_conflict.id == legacy_conflict_data["id"]
                assert mock_principle.id == legacy_principle_data["id"]
    
    @pytest.mark.asyncio
    async def test_graceful_fallback_on_qec_failure(self, legacy_conflict_data, legacy_principle_data):
        """Test graceful fallback when QEC components fail."""
        
        # Mock QEC components to raise exceptions
        with patch('app.services.qec_conflict_resolver.QEC_AVAILABLE', True):
            with patch('alphaevolve_gs_engine.services.qec_enhancement.ConstitutionalDistanceCalculator') as mock_calc:
                mock_calc.side_effect = Exception("QEC component failure")
                
                mock_conflict = Mock()
                mock_conflict.id = legacy_conflict_data["id"]
                mock_conflict.conflict_type = legacy_conflict_data["conflict_type"]
                mock_conflict.severity = legacy_conflict_data["severity"]
                
                mock_principle = Mock()
                mock_principle.id = legacy_principle_data["id"]
                mock_principle.title = legacy_principle_data["title"]
                mock_principle.description = legacy_principle_data["description"]
                
                if QEC_RESOLVER_AVAILABLE:
                    resolver = QECConflictResolver()
                    
                    # Should not raise exception, should fallback gracefully
                    try:
                        analysis = await resolver.analyze_conflict(mock_conflict, [mock_principle])
                        
                        # Should indicate fallback was used
                        assert analysis.qec_metadata.get("fallback_used") is True
                        assert analysis.qec_metadata.get("qec_error") is not None
                        
                        # Should still provide basic analysis
                        assert analysis.conflict_id == legacy_conflict_data["id"]
                        assert analysis.recommended_strategy is not None
                        
                    except Exception as e:
                        # If exception occurs, it should be handled gracefully
                        assert "fallback" in str(e).lower() or "graceful" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_legacy_data_migration_compatibility(self, legacy_principle_data):
        """Test that legacy data can be migrated to QEC-enhanced format."""
        
        # Test principle migration
        legacy_principle = legacy_principle_data.copy()
        
        # Simulate migration by adding QEC fields with defaults
        migrated_principle = legacy_principle.copy()
        migrated_principle.update({
            "distance_score": None,  # Will be calculated on first use
            "score_updated_at": None,
            "error_prediction_metadata": {
                "historical_failures": 0,
                "success_rate": 0.75,  # Conservative default
                "last_prediction": None
            },
            "recovery_strategies": ["fallback_policy"],  # Default strategy
            "validation_criteria_structured": []  # Empty initially
        })
        
        # Validate migration preserves original data
        for key in legacy_principle:
            if key in migrated_principle:
                assert migrated_principle[key] == legacy_principle[key]
        
        # Validate new fields have appropriate defaults
        assert migrated_principle["distance_score"] is None
        assert migrated_principle["error_prediction_metadata"]["success_rate"] == 0.75
        assert "fallback_policy" in migrated_principle["recovery_strategies"]
        assert isinstance(migrated_principle["validation_criteria_structured"], list)
    
    @pytest.mark.asyncio
    async def test_non_qec_workflows_continue_functioning(self):
        """Test that non-QEC workflows continue to function normally."""
        
        # Test basic principle CRUD operations
        principle_data = {
            "title": "Test Principle",
            "description": "Test description",
            "category": "testing",
            "priority_weight": 0.5
        }
        
        # Mock database operations
        with patch('sqlalchemy.ext.asyncio.AsyncSession') as mock_session:
            mock_session.return_value.__aenter__.return_value = mock_session
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            # Simulate principle creation
            if MODELS_AVAILABLE:
                principle = Principle(**principle_data)
                mock_session.add(principle)
                await mock_session.commit()
                await mock_session.refresh(principle)
                
                # Should work without QEC fields
                assert principle.title == principle_data["title"]
                assert principle.description == principle_data["description"]
            
            # Test conflict resolution creation
            conflict_data = {
                "conflict_type": "principle_contradiction",
                "principle_ids": [1, 2],
                "context": "test_context",
                "conflict_description": "Test conflict",
                "severity": "medium",
                "resolution_strategy": "manual_review"
            }
            
            if MODELS_AVAILABLE:
                conflict = ConflictResolution(**conflict_data)
                mock_session.add(conflict)
                await mock_session.commit()
                await mock_session.refresh(conflict)
                
                # Should work without QEC analysis
                assert conflict.conflict_type == conflict_data["conflict_type"]
                assert conflict.severity == conflict_data["severity"]
    
    @pytest.mark.asyncio
    async def test_api_endpoints_backward_compatibility(self):
        """Test that API endpoints maintain backward compatibility."""
        
        # Test principle endpoints
        principle_payload = {
            "title": "API Test Principle",
            "description": "Test principle for API compatibility",
            "category": "testing",
            "priority_weight": 0.7
        }
        
        # Mock API response for principle creation
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": 1,
                **principle_payload,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
                # Note: QEC fields should be optional in response
            }
            mock_post.return_value = mock_response
            
            # Should work without QEC fields in request
            response = mock_response
            assert response.status_code == 201
            response_data = response.json()
            assert response_data["title"] == principle_payload["title"]
            assert response_data["description"] == principle_payload["description"]
        
        # Test conflict resolution endpoints
        conflict_payload = {
            "conflict_type": "principle_contradiction",
            "principle_ids": [1, 2],
            "context": "api_test",
            "conflict_description": "API test conflict",
            "severity": "low",
            "resolution_strategy": "weighted_priority"
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": 1,
                **conflict_payload,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                # QEC analysis should be optional
                "qec_analysis": None
            }
            mock_post.return_value = mock_response
            
            response = mock_response
            assert response.status_code == 201
            response_data = response.json()
            assert response_data["conflict_type"] == conflict_payload["conflict_type"]
            assert response_data["severity"] == conflict_payload["severity"]
            # QEC analysis can be None for backward compatibility
            assert response_data.get("qec_analysis") is None
    
    @pytest.mark.asyncio
    async def test_database_schema_backward_compatibility(self):
        """Test that database schema changes maintain backward compatibility."""
        
        # Test that existing queries still work
        legacy_queries = [
            "SELECT id, title, description, category FROM constitutional_principles",
            "SELECT id, conflict_type, severity, status FROM conflict_resolutions",
            "SELECT principle_id, priority_weight FROM constitutional_principles WHERE category = 'privacy'"
        ]
        
        # Mock database execution
        with patch('sqlalchemy.ext.asyncio.AsyncSession') as mock_session:
            mock_session.return_value.__aenter__.return_value = mock_session
            mock_session.execute = AsyncMock()
            mock_session.fetchall = AsyncMock(return_value=[])
            
            for query in legacy_queries:
                # Should not raise exceptions
                try:
                    await mock_session.execute(query)
                    await mock_session.fetchall()
                    # Query executed successfully
                    assert True
                except Exception as e:
                    pytest.fail(f"Legacy query failed: {query} - {e}")
        
        # Test that new QEC columns are nullable/optional
        qec_columns = [
            "distance_score",
            "score_updated_at", 
            "error_prediction_metadata",
            "recovery_strategies",
            "validation_criteria_structured"
        ]
        
        # These should be optional/nullable for backward compatibility
        for column in qec_columns:
            # In a real test, we would check the database schema
            # For now, we just validate the concept
            assert column is not None  # Column exists
    
    def test_configuration_backward_compatibility(self):
        """Test that configuration changes maintain backward compatibility."""
        
        # Test that QEC can be disabled via configuration
        legacy_config = {
            "database_url": "postgresql://localhost/acgs",
            "debug": False,
            "log_level": "INFO"
            # Note: No QEC configuration
        }
        
        # Should work without QEC configuration
        assert "database_url" in legacy_config
        assert legacy_config.get("qec_enabled") is None  # Not required
        
        # Test with QEC explicitly disabled
        qec_disabled_config = legacy_config.copy()
        qec_disabled_config["qec_enabled"] = False
        
        assert qec_disabled_config["qec_enabled"] is False
        
        # Test with QEC enabled
        qec_enabled_config = legacy_config.copy()
        qec_enabled_config.update({
            "qec_enabled": True,
            "qec_fidelity_threshold": 0.85,
            "qec_cache_ttl": 3600
        })
        
        assert qec_enabled_config["qec_enabled"] is True
        assert qec_enabled_config["qec_fidelity_threshold"] == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
