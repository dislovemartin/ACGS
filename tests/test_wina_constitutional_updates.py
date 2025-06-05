"""
Tests for WINA Constitutional Principle Updates

This module tests the WINA-informed constitutional principle update functionality,
including analysis, proposal, approval, and monitoring workflows.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch

# Import WINA constitutional components
from src.backend.shared.wina.constitutional_integration import (
    WINAConstitutionalPrincipleAnalyzer,
    WINAConstitutionalUpdateService,
    ConstitutionalPrincipleUpdate
)


class TestWINAConstitutionalPrincipleAnalyzer:
    """Test cases for WINA Constitutional Principle Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return WINAConstitutionalPrincipleAnalyzer()
    
    @pytest.fixture
    def sample_principle(self):
        """Sample constitutional principle for testing."""
        return {
            "principle_id": "CP001",
            "name": "Efficiency Optimization Principle",
            "description": "Optimize AI system efficiency while maintaining safety",
            "category": "efficiency",
            "policy_code": """
            package efficiency_optimization
            
            default allow_optimization = false
            
            allow_optimization {
                input.accuracy_retention >= 0.95
                input.safety_verified == true
            }
            """,
            "dependencies": ["CP002", "CP003"]
        }
    
    @pytest.fixture
    def optimization_context(self):
        """Sample optimization context for testing."""
        return {
            "target_gflops_reduction": 0.5,
            "min_accuracy_retention": 0.95,
            "optimization_mode": "conservative",
            "safety_critical_domains": ["safety", "security"]
        }
    
    @pytest.mark.asyncio
    async def test_analyze_principle_for_wina_optimization(self, analyzer, sample_principle, optimization_context):
        """Test principle analysis for WINA optimization."""
        analysis = await analyzer.analyze_principle_for_wina_optimization(
            sample_principle, optimization_context
        )
        
        # Verify analysis structure
        assert "principle_id" in analysis
        assert "optimization_potential" in analysis
        assert "efficiency_impact" in analysis
        assert "constitutional_compatibility" in analysis
        assert "risk_factors" in analysis
        assert "recommendations" in analysis
        assert "wina_specific_insights" in analysis
        
        # Verify analysis values
        assert analysis["principle_id"] == "CP001"
        assert 0.0 <= analysis["optimization_potential"] <= 1.0
        assert 0.0 <= analysis["constitutional_compatibility"] <= 1.0
        assert isinstance(analysis["risk_factors"], list)
        assert isinstance(analysis["recommendations"], list)
    
    @pytest.mark.asyncio
    async def test_propose_constitutional_update(self, analyzer, sample_principle, optimization_context):
        """Test constitutional update proposal."""
        # First analyze the principle
        analysis = await analyzer.analyze_principle_for_wina_optimization(
            sample_principle, optimization_context
        )
        
        # Propose update
        update = await analyzer.propose_constitutional_update(
            sample_principle, analysis, optimization_context
        )
        
        # Verify update structure
        assert isinstance(update, ConstitutionalPrincipleUpdate)
        assert update.principle_id == "CP001"
        assert update.update_type in ["modify", "add", "deprecate"]
        assert update.proposed_content is not None
        assert update.rationale is not None
        assert update.approval_status == "pending"
        assert update.wina_analysis == analysis
        assert update.constitutional_distance is not None
        assert update.risk_assessment is not None
        assert update.validation_criteria is not None
        assert update.recovery_strategies is not None
    
    @pytest.mark.asyncio
    async def test_efficiency_analysis_by_category(self, analyzer, optimization_context):
        """Test efficiency analysis varies by principle category."""
        categories = ["efficiency", "safety", "fairness", "transparency"]
        results = {}
        
        for category in categories:
            principle = {
                "principle_id": f"CP_{category}",
                "name": f"{category.title()} Principle",
                "description": f"Test {category} principle",
                "category": category,
                "policy_code": "default allow = true",
                "dependencies": []
            }
            
            analysis = await analyzer.analyze_principle_for_wina_optimization(
                principle, optimization_context
            )
            results[category] = analysis["optimization_potential"]
        
        # Efficiency category should have highest potential
        assert results["efficiency"] >= results["safety"]
        assert results["efficiency"] >= results["fairness"]
    
    @pytest.mark.asyncio
    async def test_risk_factor_identification(self, analyzer, optimization_context):
        """Test risk factor identification for different principle types."""
        # Safety-critical principle
        safety_principle = {
            "principle_id": "CP_SAFETY",
            "name": "Safety Critical Principle",
            "description": "Critical safety requirements",
            "category": "safety",
            "policy_code": "strict safety requirements mandatory",
            "dependencies": ["CP1", "CP2", "CP3", "CP4"]  # High dependency coupling
        }
        
        analysis = await analyzer.analyze_principle_for_wina_optimization(
            safety_principle, optimization_context
        )
        
        risk_factors = analysis["risk_factors"]
        assert "safety_critical_principle" in risk_factors
        assert "strict_compliance_required" in risk_factors
        assert "high_dependency_coupling" in risk_factors


class TestWINAConstitutionalUpdateService:
    """Test cases for WINA Constitutional Update Service."""
    
    @pytest.fixture
    def update_service(self):
        """Create update service instance for testing."""
        analyzer = WINAConstitutionalPrincipleAnalyzer()
        return WINAConstitutionalUpdateService(analyzer=analyzer)
    
    @pytest.fixture
    def sample_principles(self):
        """Sample constitutional principles for testing."""
        return [
            {
                "principle_id": "CP001",
                "name": "Efficiency Principle",
                "description": "Optimize efficiency",
                "category": "efficiency",
                "policy_code": "default allow_optimization = true",
                "dependencies": []
            },
            {
                "principle_id": "CP002",
                "name": "Safety Principle",
                "description": "Ensure safety",
                "category": "safety",
                "policy_code": "default deny_unsafe = true",
                "dependencies": []
            }
        ]
    
    @pytest.fixture
    def optimization_context(self):
        """Sample optimization context for testing."""
        return {
            "target_gflops_reduction": 0.5,
            "min_accuracy_retention": 0.95,
            "optimization_mode": "conservative"
        }
    
    @pytest.mark.asyncio
    async def test_propose_constitutional_updates(self, update_service, sample_principles, optimization_context):
        """Test proposing constitutional updates for multiple principles."""
        proposed_updates = await update_service.propose_constitutional_updates(
            sample_principles, optimization_context
        )
        
        # Verify updates were proposed
        assert isinstance(proposed_updates, list)
        assert len(proposed_updates) <= len(sample_principles)  # Only principles with sufficient potential
        
        # Verify each update
        for update in proposed_updates:
            assert isinstance(update, ConstitutionalPrincipleUpdate)
            assert update.principle_id in ["CP001", "CP002"]
            assert update.approval_status == "pending"
            assert update.principle_id in update_service.pending_updates
    
    @pytest.mark.asyncio
    async def test_submit_update_for_approval(self, update_service, sample_principles, optimization_context):
        """Test submitting constitutional update for approval."""
        # First propose updates
        proposed_updates = await update_service.propose_constitutional_updates(
            sample_principles, optimization_context
        )
        
        if proposed_updates:
            update = proposed_updates[0]
            
            # Submit for approval
            submission_result = await update_service.submit_update_for_approval(
                update, {"submitter": "test_user"}
            )
            
            # Verify submission result
            assert submission_result["success"] is True
            assert "approval_status" in submission_result
    
    @pytest.mark.asyncio
    async def test_apply_approved_update(self, update_service, sample_principles, optimization_context):
        """Test applying approved constitutional update."""
        # Create a mock approved update
        update = ConstitutionalPrincipleUpdate(
            principle_id="CP001",
            update_type="modify",
            proposed_content="test content",
            rationale="test rationale",
            efficiency_impact={"gflops_reduction": 0.5},
            compliance_assessment={"score": 0.9},
            approval_status="approved",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Apply update
        application_result = await update_service.apply_approved_update(
            update, {"applicant": "test_user"}
        )
        
        # Verify application result
        assert application_result["success"] is True
        assert update.principle_id in update_service.approved_updates
    
    @pytest.mark.asyncio
    async def test_monitor_update_performance(self, update_service):
        """Test monitoring performance of applied constitutional update."""
        # Create a mock applied update
        update = ConstitutionalPrincipleUpdate(
            principle_id="CP001",
            update_type="modify",
            proposed_content="test content",
            rationale="test rationale",
            efficiency_impact={
                "gflops_reduction_potential": 0.5,
                "accuracy_retention_expected": 0.95,
                "latency_impact": 0.1
            },
            compliance_assessment={
                "constitutional_compliance_score": 0.9,
                "safety_compliance_score": 0.85,
                "overall_compliance_score": 0.9
            },
            approval_status="approved",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Monitor performance
        monitoring_results = await update_service.monitor_update_performance(
            update, monitoring_duration=60  # 1 minute for testing
        )
        
        # Verify monitoring results
        assert monitoring_results["principle_id"] == "CP001"
        assert "performance_metrics" in monitoring_results
        assert "efficiency" in monitoring_results["performance_metrics"]
        assert "compliance" in monitoring_results["performance_metrics"]
        assert "accuracy" in monitoring_results["performance_metrics"]
        assert monitoring_results["compliance_status"] in ["compliant", "warning", "non_compliant", "monitoring"]
    
    @pytest.mark.asyncio
    async def test_auto_approval_low_risk_updates(self, update_service):
        """Test auto-approval of low-risk constitutional updates."""
        # Create low-risk update
        update = ConstitutionalPrincipleUpdate(
            principle_id="CP001",
            update_type="modify",
            proposed_content="test content",
            rationale="test rationale",
            efficiency_impact={"gflops_reduction": 0.3},
            compliance_assessment={"score": 0.95},
            approval_status="pending",
            timestamp=datetime.now(timezone.utc),
            risk_assessment={"overall_risk_level": "low"}
        )
        
        # Submit for approval
        submission_result = await update_service.submit_update_for_approval(update)
        
        # Verify auto-approval for low-risk update
        assert submission_result["success"] is True
        assert submission_result["approval_status"] == "auto_approved"


class TestWINAConstitutionalIntegration:
    """Integration tests for WINA constitutional updates."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_constitutional_update_workflow(self):
        """Test complete constitutional update workflow."""
        # Initialize services
        analyzer = WINAConstitutionalPrincipleAnalyzer()
        update_service = WINAConstitutionalUpdateService(analyzer=analyzer)
        
        # Sample principle
        principle = {
            "principle_id": "CP_E2E",
            "name": "End-to-End Test Principle",
            "description": "Test principle for E2E workflow",
            "category": "efficiency",
            "policy_code": "default allow_optimization = true",
            "dependencies": []
        }
        
        optimization_context = {
            "target_gflops_reduction": 0.5,
            "min_accuracy_retention": 0.95
        }
        
        # Step 1: Analyze principle
        analysis = await analyzer.analyze_principle_for_wina_optimization(
            principle, optimization_context
        )
        assert analysis["optimization_potential"] > 0.0
        
        # Step 2: Propose update
        update = await analyzer.propose_constitutional_update(
            principle, analysis, optimization_context
        )
        assert update.approval_status == "pending"
        
        # Step 3: Submit for approval
        submission_result = await update_service.submit_update_for_approval(update)
        assert submission_result["success"] is True
        
        # Step 4: Simulate approval
        update.approval_status = "approved"
        
        # Step 5: Apply update
        application_result = await update_service.apply_approved_update(update)
        assert application_result["success"] is True
        
        # Step 6: Monitor performance
        monitoring_results = await update_service.monitor_update_performance(update, 30)
        assert monitoring_results["compliance_status"] in ["compliant", "warning", "monitoring"]
        
        # Verify complete workflow
        assert update.principle_id in update_service.approved_updates
        assert len(update_service.update_history) > 0


if __name__ == "__main__":
    pytest.main([__file__])
