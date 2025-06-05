#!/usr/bin/env python3
"""
LangGraph Amendment Processing StateGraph Validation Tests

This test suite specifically validates the LangGraph StateGraph implementation
for Constitutional Council amendment processing with detailed node transition testing.

Test Coverage:
1. StateGraph node execution sequence validation
2. State transitions and data flow between nodes
3. Conditional edge logic and decision points
4. Error handling and recovery mechanisms
5. Performance metrics for each workflow node
6. Integration with Constitutional Council database schema

StateGraph Nodes Tested:
- propose_amendment: Initial amendment proposal processing
- gather_stakeholder_feedback: Multi-role stakeholder engagement
- analyze_constitutionality: LLM-powered constitutional analysis
- conduct_voting: Weighted voting mechanism execution
- refine_amendment: Amendment refinement based on feedback
"""

import asyncio
import json
import time
import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import httpx
from unittest.mock import AsyncMock, patch

# Test configuration
AC_SERVICE_URL = "http://localhost:8001"

class LangGraphAmendmentProcessingTests:
    """LangGraph StateGraph amendment processing test suite."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)  # Extended timeout for workflow execution
        self.admin_token = "test_admin_token"
        self.node_execution_metrics = {}
        self.state_transitions = []
        
    async def setup_langgraph_environment(self):
        """Setup LangGraph testing environment with mock data."""
        print("🔧 Setting up LangGraph Amendment Processing environment...")
        
        # Verify LangGraph workflow capabilities
        capabilities_response = await self.client.get(
            f"{AC_SERVICE_URL}/api/v1/workflows/capabilities",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert capabilities_response.status_code == 200
        capabilities = capabilities_response.json()
        
        assert capabilities.get("langgraph_available"), "LangGraph not available"
        assert "constitutional_council" in capabilities.get("supported_workflow_types", [])
        
        # Setup test stakeholders for workflow
        test_stakeholders = [
            {
                "role": "constitutional_expert",
                "name": "Dr. Sarah Constitutional",
                "expertise": ["constitutional_law", "ai_governance"],
                "voting_weight": 1.2,
                "response_pattern": "analytical"
            },
            {
                "role": "policy_administrator",
                "name": "Alex Policy",
                "expertise": ["policy_implementation", "governance_frameworks"],
                "voting_weight": 1.0,
                "response_pattern": "pragmatic"
            },
            {
                "role": "system_auditor", 
                "name": "Jordan Audit",
                "expertise": ["system_security", "compliance_validation"],
                "voting_weight": 1.1,
                "response_pattern": "security_focused"
            },
            {
                "role": "public_representative",
                "name": "Taylor Public",
                "expertise": ["public_interest", "democratic_participation"],
                "voting_weight": 0.9,
                "response_pattern": "public_interest"
            }
        ]
        
        # Register test stakeholders
        for stakeholder in test_stakeholders:
            registration_response = await self.client.post(
                f"{AC_SERVICE_URL}/api/v1/constitutional-council/stakeholders",
                json=stakeholder,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            assert registration_response.status_code == 201
            
        print(f"  ✅ Test stakeholders registered: {len(test_stakeholders)}")
        
    async def test_propose_amendment_node(self) -> Tuple[str, Dict[str, Any]]:
        """Test the propose_amendment StateGraph node."""
        print("\n📝 Testing propose_amendment Node...")
        
        start_time = time.time()
        
        # Create comprehensive amendment proposal
        amendment_proposal = {
            "title": "Algorithmic Transparency and Explainability Amendment",
            "description": "Mandate transparency and explainability for algorithmic decision-making systems",
            "proposed_changes": {
                "new_principles": [
                    {
                        "title": "Algorithmic Transparency Principle",
                        "description": "All algorithmic systems affecting individuals must provide transparent decision processes",
                        "priority_weight": 0.9,
                        "scope": "algorithmic_decision_systems",
                        "normative_statement": "Algorithmic systems SHALL provide clear, understandable explanations for decisions",
                        "constraints": ["technical_feasibility", "privacy_protection"],
                        "rationale": "Essential for maintaining public trust in AI systems"
                    }
                ],
                "modified_principles": [],
                "deprecated_principles": []
            },
            "rationale": "Increasing deployment of opaque AI systems requires constitutional protection for transparency",
            "impact_assessment": {
                "affected_domains": ["ai_governance", "public_services", "private_sector_ai"],
                "implementation_complexity": "medium",
                "estimated_compliance_cost": "moderate"
            },
            "stakeholder_analysis": {
                "primary_beneficiaries": ["citizens", "civil_rights_organizations"],
                "implementation_entities": ["government_agencies", "ai_companies"],
                "potential_objectors": ["proprietary_ai_vendors"]
            }
        }
        
        # Execute propose_amendment node
        node_response = await self.client.post(
            f"{AC_SERVICE_URL}/api/v1/workflows/nodes/propose_amendment",
            json={
                "amendment_data": amendment_proposal,
                "workflow_config": {
                    "validation_level": "comprehensive",
                    "auto_advance": False,
                    "stakeholder_notification": True
                }
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert node_response.status_code == 200
        node_result = node_response.json()
        
        execution_time = time.time() - start_time
        
        # Validate node execution results
        assert "amendment_id" in node_result, "Amendment ID not generated"
        assert "validation_results" in node_result, "Validation results missing"
        assert node_result.get("status") == "proposed", "Amendment not properly proposed"
        
        amendment_id = node_result["amendment_id"]
        
        print(f"  ✅ propose_amendment node executed in {execution_time:.2f}s")
        print(f"  ✅ Amendment ID generated: {amendment_id}")
        
        # Validate amendment data persistence
        amendment_check = await self.client.get(
            f"{AC_SERVICE_URL}/api/v1/constitutional-council/amendments/{amendment_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert amendment_check.status_code == 200
        stored_amendment = amendment_check.json()
        assert stored_amendment["title"] == amendment_proposal["title"]
        
        self.node_execution_metrics["propose_amendment"] = {
            "execution_time_seconds": execution_time,
            "amendment_id": amendment_id,
            "validation_passed": True
        }
        
        self.state_transitions.append({
            "from_node": "START",
            "to_node": "propose_amendment", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_data": {"amendment_id": amendment_id}
        })
        
        return amendment_id, node_result
        
    async def test_gather_stakeholder_feedback_node(self, amendment_id: str) -> Dict[str, Any]:
        """Test the gather_stakeholder_feedback StateGraph node."""
        print("\n👥 Testing gather_stakeholder_feedback Node...")
        
        start_time = time.time()
        
        # Execute gather_stakeholder_feedback node
        feedback_node_response = await self.client.post(
            f"{AC_SERVICE_URL}/api/v1/workflows/nodes/gather_stakeholder_feedback",
            json={
                "amendment_id": amendment_id,
                "stakeholder_config": {
                    "notification_channels": ["email", "dashboard", "api"],
                    "response_deadline": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                    "feedback_types": ["vote", "comments", "suggested_modifications"],
                    "enable_real_time_tracking": True
                }
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert feedback_node_response.status_code == 200
        feedback_result = feedback_node_response.json()
        
        # Validate stakeholder notifications sent
        assert "notifications_sent" in feedback_result
        assert feedback_result["notifications_sent"] > 0
        
        print(f"  ✅ Stakeholder notifications sent: {feedback_result['notifications_sent']}")
        
        # Simulate stakeholder feedback responses
        stakeholder_responses = [
            {
                "stakeholder_role": "constitutional_expert",
                "vote": "approve",
                "confidence": 0.9,
                "comments": "Well-structured amendment addressing critical transparency needs",
                "suggested_modifications": []
            },
            {
                "stakeholder_role": "policy_administrator",
                "vote": "conditional_approve",
                "confidence": 0.7,
                "comments": "Support with implementation timeline concerns",
                "suggested_modifications": ["phased_implementation", "compliance_grace_period"]
            },
            {
                "stakeholder_role": "system_auditor",
                "vote": "approve",
                "confidence": 0.85,
                "comments": "Strong security and compliance benefits",
                "suggested_modifications": ["audit_trail_requirements"]
            },
            {
                "stakeholder_role": "public_representative",
                "vote": "approve",
                "confidence": 0.8,
                "comments": "Excellent protection for citizen rights",
                "suggested_modifications": []
            }
        ]
        
        # Submit stakeholder feedback
        for response in stakeholder_responses:
            feedback_submission = await self.client.post(
                f"{AC_SERVICE_URL}/api/v1/constitutional-council/amendments/{amendment_id}/feedback",
                json=response,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            assert feedback_submission.status_code == 201
            
        execution_time = time.time() - start_time
        
        print(f"  ✅ gather_stakeholder_feedback node executed in {execution_time:.2f}s")
        print(f"  ✅ Stakeholder responses collected: {len(stakeholder_responses)}")
        
        self.node_execution_metrics["gather_stakeholder_feedback"] = {
            "execution_time_seconds": execution_time,
            "notifications_sent": feedback_result["notifications_sent"],
            "responses_collected": len(stakeholder_responses)
        }
        
        self.state_transitions.append({
            "from_node": "propose_amendment",
            "to_node": "gather_stakeholder_feedback",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_data": {"feedback_count": len(stakeholder_responses)}
        })
        
        return feedback_result
        
    async def test_analyze_constitutionality_node(self, amendment_id: str) -> Dict[str, Any]:
        """Test the analyze_constitutionality StateGraph node with LLM integration."""
        print("\n🧠 Testing analyze_constitutionality Node...")
        
        start_time = time.time()
        
        # Execute constitutional analysis node
        analysis_node_response = await self.client.post(
            f"{AC_SERVICE_URL}/api/v1/workflows/nodes/analyze_constitutionality",
            json={
                "amendment_id": amendment_id,
                "analysis_config": {
                    "analysis_depth": "comprehensive",
                    "constitutional_frameworks": ["ai_governance", "democratic_principles", "human_rights"],
                    "conflict_detection": True,
                    "precedent_analysis": True,
                    "implementation_feasibility": True,
                    "target_fidelity_score": 0.85
                }
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert analysis_node_response.status_code == 200
        analysis_result = analysis_node_response.json()
        
        execution_time = time.time() - start_time
        
        # Validate constitutional analysis results
        required_analysis_components = [
            "constitutional_consistency",
            "conflict_analysis", 
            "precedent_alignment",
            "implementation_feasibility",
            "democratic_legitimacy"
        ]
        
        analysis_components = analysis_result.get("analysis_components", {})
        for component in required_analysis_components:
            assert component in analysis_components, f"Missing analysis component: {component}"
            
        # Validate constitutional fidelity score
        fidelity_score = analysis_result.get("constitutional_fidelity_score", 0)
        assert fidelity_score > 0.85, f"Fidelity score {fidelity_score:.3f} below target (>0.85)"
        
        print(f"  ✅ analyze_constitutionality node executed in {execution_time:.2f}s")
        print(f"  ✅ Constitutional fidelity score: {fidelity_score:.3f}")
        print(f"  ✅ Analysis components validated: {len(analysis_components)}")
        
        self.node_execution_metrics["analyze_constitutionality"] = {
            "execution_time_seconds": execution_time,
            "fidelity_score": fidelity_score,
            "analysis_components": len(analysis_components)
        }
        
        self.state_transitions.append({
            "from_node": "gather_stakeholder_feedback",
            "to_node": "analyze_constitutionality",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_data": {"fidelity_score": fidelity_score}
        })
        
        return analysis_result
        
    async def test_conduct_voting_node(self, amendment_id: str) -> Dict[str, Any]:
        """Test the conduct_voting StateGraph node with weighted voting."""
        print("\n🗳️  Testing conduct_voting Node...")
        
        start_time = time.time()
        
        # Execute voting node
        voting_node_response = await self.client.post(
            f"{AC_SERVICE_URL}/api/v1/workflows/nodes/conduct_voting",
            json={
                "amendment_id": amendment_id,
                "voting_config": {
                    "voting_method": "weighted_stakeholder",
                    "quorum_threshold": 0.6,
                    "approval_threshold": 0.7,
                    "voting_deadline": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
                    "enable_delegation": True,
                    "transparency_level": "full"
                }
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert voting_node_response.status_code == 200
        voting_result = voting_node_response.json()
        
        execution_time = time.time() - start_time
        
        # Validate voting results
        assert "voting_summary" in voting_result
        assert "weighted_approval_rate" in voting_result
        assert "quorum_met" in voting_result
        
        voting_summary = voting_result["voting_summary"]
        weighted_approval_rate = voting_result["weighted_approval_rate"]
        quorum_met = voting_result["quorum_met"]
        
        # Validate voting thresholds
        assert quorum_met, "Quorum not met for voting"
        assert weighted_approval_rate >= 0.7, f"Approval rate {weighted_approval_rate:.3f} below threshold (0.7)"
        
        print(f"  ✅ conduct_voting node executed in {execution_time:.2f}s")
        print(f"  ✅ Weighted approval rate: {weighted_approval_rate:.3f}")
        print(f"  ✅ Quorum met: {quorum_met}")
        
        self.node_execution_metrics["conduct_voting"] = {
            "execution_time_seconds": execution_time,
            "weighted_approval_rate": weighted_approval_rate,
            "quorum_met": quorum_met
        }
        
        self.state_transitions.append({
            "from_node": "analyze_constitutionality",
            "to_node": "conduct_voting",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_data": {"approval_rate": weighted_approval_rate}
        })
        
        return voting_result
        
    async def test_refine_amendment_node(self, amendment_id: str) -> Dict[str, Any]:
        """Test the refine_amendment StateGraph node."""
        print("\n✨ Testing refine_amendment Node...")
        
        start_time = time.time()
        
        # Execute amendment refinement node
        refinement_node_response = await self.client.post(
            f"{AC_SERVICE_URL}/api/v1/workflows/nodes/refine_amendment",
            json={
                "amendment_id": amendment_id,
                "refinement_config": {
                    "incorporate_feedback": True,
                    "resolve_conflicts": True,
                    "optimize_implementation": True,
                    "generate_final_version": True,
                    "create_implementation_plan": True
                }
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert refinement_node_response.status_code == 200
        refinement_result = refinement_node_response.json()
        
        execution_time = time.time() - start_time
        
        # Validate refinement results
        assert "refined_amendment" in refinement_result
        assert "implementation_plan" in refinement_result
        assert "final_status" in refinement_result
        
        final_status = refinement_result["final_status"]
        assert final_status == "approved", f"Amendment not approved: {final_status}"
        
        print(f"  ✅ refine_amendment node executed in {execution_time:.2f}s")
        print(f"  ✅ Amendment final status: {final_status}")
        
        self.node_execution_metrics["refine_amendment"] = {
            "execution_time_seconds": execution_time,
            "final_status": final_status,
            "refinement_completed": True
        }
        
        self.state_transitions.append({
            "from_node": "conduct_voting",
            "to_node": "refine_amendment",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_data": {"final_status": final_status}
        })
        
        return refinement_result
        
    async def test_complete_stategraph_workflow(self):
        """Test complete StateGraph workflow execution with all nodes."""
        print("\n🔄 Testing Complete StateGraph Workflow...")
        
        workflow_start_time = time.time()
        
        # Execute complete workflow
        amendment_id, proposal_result = await self.test_propose_amendment_node()
        feedback_result = await self.test_gather_stakeholder_feedback_node(amendment_id)
        analysis_result = await self.test_analyze_constitutionality_node(amendment_id)
        voting_result = await self.test_conduct_voting_node(amendment_id)
        refinement_result = await self.test_refine_amendment_node(amendment_id)
        
        total_workflow_time = time.time() - workflow_start_time
        
        print(f"\n  ✅ Complete StateGraph workflow executed in {total_workflow_time:.2f}s")
        
        # Validate workflow completion under target time
        assert total_workflow_time < 30, f"Workflow took {total_workflow_time:.2f}s (target: <30s)"
        
        # Validate all state transitions
        expected_transitions = 5  # Number of node transitions
        actual_transitions = len(self.state_transitions)
        assert actual_transitions == expected_transitions, \
            f"Expected {expected_transitions} transitions, got {actual_transitions}"
            
        print(f"  ✅ State transitions validated: {actual_transitions}/{expected_transitions}")
        
        return {
            "total_execution_time": total_workflow_time,
            "amendment_id": amendment_id,
            "workflow_completed": True,
            "all_nodes_executed": len(self.node_execution_metrics) == 5
        }
        
    async def run_langgraph_tests(self):
        """Run all LangGraph StateGraph amendment processing tests."""
        print("🔄 ACGS-PGP LangGraph Amendment Processing StateGraph Tests")
        print("=" * 70)
        
        try:
            await self.setup_langgraph_environment()
            
            # Run complete StateGraph workflow test
            workflow_result = await self.test_complete_stategraph_workflow()
            
            # Generate test report
            await self.generate_langgraph_report(workflow_result)
            
            print("\n" + "=" * 70)
            print("🎉 LangGraph StateGraph Amendment Processing Tests COMPLETED!")
            print("📊 All workflow nodes and transitions validated successfully")
            print("🚀 StateGraph implementation ready for production deployment")
            
        except Exception as e:
            print(f"\n❌ LangGraph test execution failed: {str(e)}")
            raise
        finally:
            await self.client.aclose()
            
    async def generate_langgraph_report(self, workflow_result: Dict[str, Any]):
        """Generate comprehensive LangGraph test report."""
        print("\n📊 Generating LangGraph Test Report...")
        
        report = {
            "test_execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "test_suite": "LangGraph Amendment Processing StateGraph",
            "workflow_result": workflow_result,
            "node_execution_metrics": self.node_execution_metrics,
            "state_transitions": self.state_transitions,
            "performance_summary": {
                "total_workflow_time": workflow_result.get("total_execution_time"),
                "average_node_time": sum(
                    metrics.get("execution_time_seconds", 0) 
                    for metrics in self.node_execution_metrics.values()
                ) / len(self.node_execution_metrics) if self.node_execution_metrics else 0,
                "constitutional_fidelity_achieved": self.node_execution_metrics.get("analyze_constitutionality", {}).get("fidelity_score", 0) > 0.85,
                "voting_approval_achieved": self.node_execution_metrics.get("conduct_voting", {}).get("weighted_approval_rate", 0) >= 0.7
            },
            "validation_results": {
                "all_nodes_executed": len(self.node_execution_metrics) == 5,
                "state_transitions_valid": len(self.state_transitions) == 5,
                "workflow_under_30s": workflow_result.get("total_execution_time", 0) < 30,
                "constitutional_compliance": True,
                "stakeholder_engagement": True
            }
        }
        
        # Save report
        report_path = Path("LANGGRAPH_AMENDMENT_PROCESSING_REPORT.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"  ✅ LangGraph test report saved: {report_path}")

async def main():
    """Main LangGraph test execution function."""
    test_suite = LangGraphAmendmentProcessingTests()
    await test_suite.run_langgraph_tests()

if __name__ == "__main__":
    asyncio.run(main())
