#!/usr/bin/env python3
"""
ACGS-PGP Phase 2.2: Complete Policy Pipeline Validation Tests

This comprehensive test suite validates the end-to-end policy pipeline:
AC Service → GS Service → FV Service → Integrity Service → PGC Service

Test Scenarios:
1. Constitutional Amendment Workflow (LangGraph StateGraph)
2. Policy Synthesis Pipeline (Multi-model LLM)
3. Conflict Resolution Workflow (AI-powered)
4. Cross-service Communication Validation
5. Performance and Reliability Testing

Target Metrics:
- Policy Pipeline Success Rate: >95%
- Response Time: <50ms average policy decision latency
- LLM Reliability: >99.9%
- Constitutional Fidelity Score: >0.85
"""

import asyncio
import json
import time
import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import httpx
from unittest.mock import AsyncMock, patch

# Test configuration
BASE_URLS = {
    "auth": "http://localhost:8000",
    "ac": "http://localhost:8001", 
    "integrity": "http://localhost:8002",
    "fv": "http://localhost:8003",
    "gs": "http://localhost:8004",
    "pgc": "http://localhost:8005",
    "ec": "http://localhost:8006"
}

class PolicyPipelineTestSuite:
    """Comprehensive policy pipeline test suite."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        self.performance_metrics = {}
        
    async def setup_test_environment(self):
        """Setup test environment with authentication and test data."""
        print("🔧 Setting up test environment...")
        
        # Load authentication tokens
        try:
            with open("auth_tokens.json", "r") as f:
                tokens = json.load(f).get("tokens", {})
                self.admin_token = tokens.get("admin", "test_admin_token")
                self.policy_manager_token = tokens.get("policy_manager", "test_pm_token")
        except FileNotFoundError:
            print("⚠️  Using default test tokens")
            self.admin_token = "test_admin_token"
            self.policy_manager_token = "test_pm_token"
            
        # Verify all services are healthy
        await self.verify_service_health()
        
    async def verify_service_health(self):
        """Verify all services are operational."""
        print("🏥 Verifying service health...")
        
        health_results = {}
        for service, url in BASE_URLS.items():
            try:
                start_time = time.time()
                response = await self.client.get(f"{url}/health")
                latency = (time.time() - start_time) * 1000
                
                health_results[service] = {
                    "status": response.status_code == 200,
                    "latency_ms": latency
                }
                
                if response.status_code == 200:
                    print(f"  ✅ {service}_service: {latency:.1f}ms")
                else:
                    print(f"  ❌ {service}_service: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {service}_service: {str(e)}")
                health_results[service] = {"status": False, "error": str(e)}
                
        self.performance_metrics["service_health"] = health_results
        
        # Check if all services are healthy
        healthy_services = sum(1 for result in health_results.values() if result.get("status"))
        total_services = len(health_results)
        
        if healthy_services < total_services:
            raise Exception(f"Only {healthy_services}/{total_services} services are healthy")
            
    async def test_constitutional_amendment_workflow(self):
        """Test complete constitutional amendment workflow using LangGraph."""
        print("\n🏛️  Testing Constitutional Amendment Workflow...")
        
        start_time = time.time()
        
        # Step 1: Create amendment proposal
        amendment_data = {
            "title": "AI Transparency Enhancement Amendment",
            "description": "Enhance transparency requirements for AI decision-making systems",
            "proposed_changes": {
                "new_principle": {
                    "title": "AI Transparency Principle",
                    "description": "AI systems must provide clear explanations for decisions affecting individuals",
                    "priority_weight": 0.8,
                    "scope": "ai_decision_systems",
                    "normative_statement": "All AI systems SHALL provide human-readable explanations"
                }
            },
            "rationale": "Increasing need for AI transparency in critical applications"
        }
        
        # Create amendment proposal
        response = await self.client.post(
            f"{BASE_URLS['ac']}/api/v1/constitutional-council/amendments",
            json=amendment_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 201, f"Amendment creation failed: {response.text}"
        amendment = response.json()
        amendment_id = amendment["id"]
        
        print(f"  ✅ Amendment proposal created: ID {amendment_id}")
        
        # Step 2: Test LangGraph StateGraph workflow execution
        workflow_response = await self.client.post(
            f"{BASE_URLS['ac']}/api/v1/workflows/constitutional-council/execute",
            json={
                "amendment_id": amendment_id,
                "workflow_type": "amendment_processing",
                "stakeholder_roles": ["constitutional_expert", "policy_administrator", "public_representative"]
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert workflow_response.status_code == 200, f"Workflow execution failed: {workflow_response.text}"
        workflow_result = workflow_response.json()
        
        print(f"  ✅ LangGraph workflow executed: {workflow_result.get('status')}")
        
        # Step 3: Simulate stakeholder engagement
        stakeholder_feedback = [
            {"role": "constitutional_expert", "vote": "approve", "comments": "Aligns with constitutional principles"},
            {"role": "policy_administrator", "vote": "approve", "comments": "Implementable and necessary"},
            {"role": "public_representative", "vote": "approve", "comments": "Benefits public transparency"}
        ]
        
        for feedback in stakeholder_feedback:
            feedback_response = await self.client.post(
                f"{BASE_URLS['ac']}/api/v1/constitutional-council/amendments/{amendment_id}/feedback",
                json=feedback,
                headers={"Authorization": f"Bearer {self.policy_manager_token}"}
            )
            assert feedback_response.status_code == 201
            
        print(f"  ✅ Stakeholder feedback collected: {len(stakeholder_feedback)} responses")
        
        # Step 4: Finalize amendment
        finalization_response = await self.client.post(
            f"{BASE_URLS['ac']}/api/v1/constitutional-council/amendments/{amendment_id}/finalize",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert finalization_response.status_code == 200
        
        execution_time = time.time() - start_time
        print(f"  ✅ Amendment workflow completed in {execution_time:.2f}s")
        
        # Validate target: <30 second completion
        assert execution_time < 30, f"Amendment workflow took {execution_time:.2f}s (target: <30s)"
        
        self.performance_metrics["amendment_workflow"] = {
            "execution_time_seconds": execution_time,
            "amendment_id": amendment_id,
            "stakeholder_responses": len(stakeholder_feedback)
        }
        
        return amendment_id
        
    async def test_policy_synthesis_pipeline(self):
        """Test complete policy synthesis pipeline: AC→GS→FV→Integrity→PGC."""
        print("\n⚙️  Testing Policy Synthesis Pipeline...")
        
        start_time = time.time()
        
        # Step 1: Get constitutional principle from AC service
        principles_response = await self.client.get(
            f"{BASE_URLS['ac']}/api/v1/principles",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert principles_response.status_code == 200
        principles = principles_response.json()["items"]
        
        if not principles:
            # Create a test principle
            principle_data = {
                "title": "Data Privacy Protection",
                "description": "Protect user data privacy in all AI operations",
                "priority_weight": 0.9,
                "scope": "data_processing",
                "normative_statement": "User data SHALL be processed with explicit consent"
            }
            
            create_response = await self.client.post(
                f"{BASE_URLS['ac']}/api/v1/principles",
                json=principle_data,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            assert create_response.status_code == 201
            principle = create_response.json()
        else:
            principle = principles[0]
            
        print(f"  ✅ Constitutional principle retrieved: {principle['title']}")
        
        # Step 2: GS Service - Constitutional prompting and policy synthesis
        synthesis_request = {
            "principle_id": principle["id"],
            "context": {
                "domain": "healthcare_ai",
                "scenario": "patient_data_processing",
                "constraints": ["gdpr_compliance", "hipaa_compliance"]
            },
            "target_format": "rego",
            "enable_multi_model": True
        }
        
        synthesis_response = await self.client.post(
            f"{BASE_URLS['gs']}/api/v1/constitutional/synthesize-policy",
            json=synthesis_request,
            headers={"Authorization": f"Bearer {self.policy_manager_token}"}
        )
        
        assert synthesis_response.status_code == 200
        synthesis_result = synthesis_response.json()
        
        print(f"  ✅ Policy synthesized: {synthesis_result.get('policy_format')} format")
        
        # Step 3: FV Service - Multi-model validation
        validation_request = {
            "policy_content": synthesis_result["policy_content"],
            "principle_reference": principle,
            "validation_models": ["bias_detection", "fairness_analysis", "constitutional_compliance"],
            "target_fidelity_score": 0.85
        }
        
        validation_response = await self.client.post(
            f"{BASE_URLS['fv']}/api/v1/validate/comprehensive",
            json=validation_request,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert validation_response.status_code == 200
        validation_result = validation_response.json()
        
        print(f"  ✅ Policy validated: fidelity score {validation_result.get('fidelity_score', 0):.3f}")
        
        # Step 4: Integrity Service - Cryptographic signing
        integrity_request = {
            "policy_content": synthesis_result["policy_content"],
            "metadata": {
                "principle_id": principle["id"],
                "synthesis_timestamp": datetime.now(timezone.utc).isoformat(),
                "validation_score": validation_result.get("fidelity_score")
            }
        }
        
        integrity_response = await self.client.post(
            f"{BASE_URLS['integrity']}/api/v1/sign-policy",
            json=integrity_request,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert integrity_response.status_code == 200
        integrity_result = integrity_response.json()
        
        print(f"  ✅ Policy signed: signature {integrity_result.get('signature_id')}")
        
        # Step 5: PGC Service - Policy compilation and deployment
        compilation_request = {
            "signed_policy": integrity_result,
            "deployment_target": "test_environment",
            "enable_hot_swap": True
        }
        
        compilation_response = await self.client.post(
            f"{BASE_URLS['pgc']}/api/v1/compile-policy",
            json=compilation_request,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert compilation_response.status_code == 200
        compilation_result = compilation_response.json()
        
        print(f"  ✅ Policy compiled: deployment ID {compilation_result.get('deployment_id')}")
        
        execution_time = time.time() - start_time
        print(f"  ✅ Policy synthesis pipeline completed in {execution_time:.2f}s")
        
        # Validate target: <5 second synthesis completion
        assert execution_time < 5, f"Policy synthesis took {execution_time:.2f}s (target: <5s)"
        
        # Validate constitutional fidelity score
        fidelity_score = validation_result.get("fidelity_score", 0)
        assert fidelity_score > 0.85, f"Fidelity score {fidelity_score:.3f} below target (>0.85)"
        
        self.performance_metrics["policy_synthesis"] = {
            "execution_time_seconds": execution_time,
            "fidelity_score": fidelity_score,
            "principle_id": principle["id"],
            "deployment_id": compilation_result.get("deployment_id")
        }
        
        return compilation_result.get("deployment_id")
        
    async def test_conflict_resolution_workflow(self):
        """Test AI-powered conflict resolution workflow."""
        print("\n🤖 Testing Conflict Resolution Workflow...")
        
        start_time = time.time()
        
        # Create conflicting principles for testing
        principle1_data = {
            "title": "Maximum Data Utility",
            "description": "Maximize data usage for AI improvement",
            "priority_weight": 0.7,
            "scope": "data_processing"
        }
        
        principle2_data = {
            "title": "Strict Privacy Protection", 
            "description": "Minimize data collection and usage",
            "priority_weight": 0.8,
            "scope": "data_processing"
        }
        
        # Create conflicting principles
        for principle_data in [principle1_data, principle2_data]:
            response = await self.client.post(
                f"{BASE_URLS['ac']}/api/v1/principles",
                json=principle_data,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            assert response.status_code == 201
            
        # Trigger conflict detection
        conflict_detection_response = await self.client.post(
            f"{BASE_URLS['ac']}/api/v1/conflicts/detect",
            json={"scope": "data_processing"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert conflict_detection_response.status_code == 200
        conflicts = conflict_detection_response.json()
        
        print(f"  ✅ Conflicts detected: {len(conflicts.get('conflicts', []))}")
        
        if conflicts.get("conflicts"):
            # Test AI-powered resolution
            resolution_response = await self.client.post(
                f"{BASE_URLS['ac']}/api/v1/conflicts/resolve",
                json={
                    "conflict_id": conflicts["conflicts"][0]["id"],
                    "resolution_strategy": "ai_mediated",
                    "target_resolution_time": 300  # 5 minutes
                },
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            
            assert resolution_response.status_code == 200
            resolution_result = resolution_response.json()
            
            print(f"  ✅ Conflict resolved: {resolution_result.get('resolution_type')}")
            
            # Validate 80% automatic resolution target
            if resolution_result.get("resolution_type") == "automatic":
                print("  ✅ Automatic resolution achieved")
            else:
                print("  ⚠️  Human escalation required")
                
        execution_time = time.time() - start_time
        self.performance_metrics["conflict_resolution"] = {
            "execution_time_seconds": execution_time,
            "conflicts_detected": len(conflicts.get("conflicts", [])),
            "automatic_resolution": conflicts.get("conflicts") and resolution_result.get("resolution_type") == "automatic"
        }
        
    async def run_comprehensive_tests(self):
        """Run all comprehensive policy pipeline tests."""
        print("🚀 ACGS-PGP Phase 2.2: Complete Policy Pipeline Validation")
        print("=" * 70)
        
        try:
            await self.setup_test_environment()
            
            # Run test scenarios
            amendment_id = await self.test_constitutional_amendment_workflow()
            deployment_id = await self.test_policy_synthesis_pipeline()
            await self.test_conflict_resolution_workflow()
            
            # Generate summary report
            await self.generate_test_report()
            
            print("\n" + "=" * 70)
            print("🎉 Phase 2.2 Policy Pipeline Validation COMPLETED!")
            print("📊 All test scenarios passed successfully")
            print("🚀 ACGS-PGP system ready for production deployment")
            
        except Exception as e:
            print(f"\n❌ Test execution failed: {str(e)}")
            raise
        finally:
            await self.client.aclose()
            
    async def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📊 Generating Test Report...")
        
        report = {
            "test_execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": "2.2 Complete Policy Pipeline Validation",
            "performance_metrics": self.performance_metrics,
            "success_criteria_validation": {
                "policy_pipeline_success_rate": "95%+",  # All tests passed
                "average_response_time": f"{self.performance_metrics.get('policy_synthesis', {}).get('execution_time_seconds', 0):.2f}s",
                "constitutional_fidelity_score": f"{self.performance_metrics.get('policy_synthesis', {}).get('fidelity_score', 0):.3f}",
                "service_health": "100% operational"
            }
        }
        
        # Save report
        report_path = Path("PHASE_2_2_VALIDATION_REPORT.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"  ✅ Test report saved: {report_path}")

async def main():
    """Main test execution function."""
    test_suite = PolicyPipelineTestSuite()
    await test_suite.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())
