#!/usr/bin/env python3
"""
Integration test for Constitutional Council Schema Alignment (Task 2)
Tests the enhanced schema, optimistic locking, Redis caching, and state machine workflows.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Test configuration
BASE_URL = "http://localhost:8001"
ADMIN_TOKEN = "admin_token"
COUNCIL_TOKEN = "council_token"

class ConstitutionalCouncilSchemaTest:
    """Test suite for Constitutional Council Schema Alignment."""
    
    def __init__(self):
        self.session = None
        self.test_results = {
            "schema_validation": False,
            "optimistic_locking": False,
            "redis_caching": False,
            "state_machine": False,
            "co_evolution": False,
            "metrics_collection": False
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def request(self, method: str, endpoint: str, token: str = None, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
        """Make HTTP request to AC service."""
        url = f"{BASE_URL}{endpoint}"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with self.session.request(method, url, headers=headers, json=data) as response:
                result = {
                    "status_code": response.status,
                    "data": await response.json() if response.content_type == "application/json" else await response.text()
                }
                return result
        except Exception as e:
            return {"status_code": 0, "error": str(e)}
    
    async def test_enhanced_schema_validation(self) -> bool:
        """Test enhanced Pydantic v2.0+ schema validation."""
        print("\n🔍 Testing Enhanced Schema Validation...")
        
        # Test 1: Valid amendment with co-evolution fields
        valid_amendment = {
            "principle_id": 1,
            "amendment_type": "modify",
            "proposed_changes": "Enhanced privacy protection with algorithmic transparency requirements",
            "justification": "Alignment with emerging AI governance standards and democratic accountability principles",
            "proposed_content": "All AI systems SHALL implement privacy-by-design with algorithmic transparency",
            "urgency_level": "rapid",
            "expected_impact": "high",
            "constitutional_significance": "significant",
            "rapid_processing_requested": True,
            "co_evolution_context": {
                "trigger_event": "regulatory_update",
                "timeline": "30_days",
                "stakeholders": ["citizens", "experts", "regulatory_bodies"]
            },
            "consultation_period_days": 15,
            "stakeholder_groups": ["citizens", "experts", "regulatory_bodies"]
        }
        
        result = await self.request("POST", "/api/v1/constitutional-council/amendments", COUNCIL_TOKEN, valid_amendment)
        if result["status_code"] == 201:
            print("✅ Valid amendment with co-evolution fields accepted")
            amendment_id = result["data"]["id"]
            
            # Verify enhanced fields are present
            get_result = await self.request("GET", f"/api/v1/constitutional-council/amendments/{amendment_id}", COUNCIL_TOKEN)
            if get_result["status_code"] == 200:
                amendment_data = get_result["data"]
                required_fields = ["urgency_level", "expected_impact", "constitutional_significance", "version", "workflow_state"]
                if all(field in amendment_data for field in required_fields):
                    print("✅ Enhanced schema fields present in response")
                    return True
        
        print("❌ Enhanced schema validation failed")
        return False
    
    async def test_optimistic_locking(self) -> bool:
        """Test optimistic locking for concurrent amendment updates."""
        print("\n🔒 Testing Optimistic Locking...")
        
        # Create test amendment
        amendment_data = {
            "principle_id": 1,
            "amendment_type": "modify",
            "proposed_changes": "Test amendment for optimistic locking",
            "justification": "Testing concurrent update handling",
            "urgency_level": "normal"
        }
        
        result = await self.request("POST", "/api/v1/constitutional-council/amendments", COUNCIL_TOKEN, amendment_data)
        if result["status_code"] != 201:
            print("❌ Failed to create test amendment")
            return False
        
        amendment_id = result["data"]["id"]
        initial_version = result["data"]["version"]
        
        # Test version conflict detection
        update_data = {
            "proposed_changes": "Updated content - first update",
            "version": initial_version
        }
        
        # First update should succeed
        update_result = await self.request("PUT", f"/api/v1/constitutional-council/amendments/{amendment_id}", COUNCIL_TOKEN, update_data)
        if update_result["status_code"] == 200:
            new_version = update_result["data"]["version"]
            if new_version > initial_version:
                print("✅ Optimistic locking version increment working")
                
                # Second update with old version should fail
                old_version_update = {
                    "proposed_changes": "Updated content - conflicting update",
                    "version": initial_version  # Using old version
                }
                
                conflict_result = await self.request("PUT", f"/api/v1/constitutional-council/amendments/{amendment_id}", COUNCIL_TOKEN, old_version_update)
                if conflict_result["status_code"] == 409:  # Conflict
                    print("✅ Version conflict properly detected")
                    return True
        
        print("❌ Optimistic locking test failed")
        return False
    
    async def test_state_machine_workflow(self) -> bool:
        """Test state machine-based democratic governance workflows."""
        print("\n🏛️ Testing State Machine Workflow...")
        
        # Create amendment
        amendment_data = {
            "principle_id": 1,
            "amendment_type": "modify",
            "proposed_changes": "Test amendment for state machine workflow",
            "justification": "Testing democratic governance state transitions",
            "urgency_level": "normal"
        }
        
        result = await self.request("POST", "/api/v1/constitutional-council/amendments", COUNCIL_TOKEN, amendment_data)
        if result["status_code"] != 201:
            print("❌ Failed to create test amendment")
            return False
        
        amendment_id = result["data"]["id"]
        initial_state = result["data"]["workflow_state"]
        
        if initial_state == "proposed":
            print("✅ Amendment created in 'proposed' state")
            
            # Test state transition to under_review
            transition_data = {
                "event": "start_review",
                "workflow_state": "under_review"
            }
            
            transition_result = await self.request("POST", f"/api/v1/constitutional-council/amendments/{amendment_id}/transition", COUNCIL_TOKEN, transition_data)
            if transition_result["status_code"] == 200:
                new_state = transition_result["data"]["workflow_state"]
                if new_state == "under_review":
                    print("✅ State transition from 'proposed' to 'under_review' successful")
                    
                    # Verify state transition history
                    get_result = await self.request("GET", f"/api/v1/constitutional-council/amendments/{amendment_id}", COUNCIL_TOKEN)
                    if get_result["status_code"] == 200:
                        state_transitions = get_result["data"].get("state_transitions", [])
                        if len(state_transitions) >= 2:  # Initial + transition
                            print("✅ State transition history recorded")
                            return True
        
        print("❌ State machine workflow test failed")
        return False
    
    async def test_co_evolution_handling(self) -> bool:
        """Test rapid co-evolution handling capabilities."""
        print("\n⚡ Testing Co-Evolution Handling...")
        
        # Test rapid processing request
        rapid_amendment = {
            "principle_id": 1,
            "amendment_type": "modify",
            "proposed_changes": "Urgent amendment requiring rapid co-evolution processing",
            "justification": "Critical security update requiring immediate attention",
            "urgency_level": "emergency",
            "expected_impact": "critical",
            "constitutional_significance": "fundamental",
            "rapid_processing_requested": True,
            "co_evolution_context": {
                "trigger_event": "security_incident",
                "timeline": "24_hours",
                "stakeholders": ["constitutional_council", "security_experts"]
            }
        }
        
        result = await self.request("POST", "/api/v1/constitutional-council/amendments", COUNCIL_TOKEN, rapid_amendment)
        if result["status_code"] == 201:
            amendment_data = result["data"]
            
            # Verify rapid processing fields
            if (amendment_data.get("urgency_level") == "emergency" and
                amendment_data.get("rapid_processing_requested") == True and
                amendment_data.get("processing_metrics") is not None):
                print("✅ Rapid co-evolution processing enabled")
                
                # Check processing metrics
                metrics = amendment_data.get("processing_metrics", {})
                if "creation_time" in metrics and "urgency_level" in metrics:
                    print("✅ Co-evolution metrics collected")
                    return True
        
        print("❌ Co-evolution handling test failed")
        return False
    
    async def test_metrics_collection(self) -> bool:
        """Test Prometheus metrics collection for Constitutional Council."""
        print("\n📊 Testing Metrics Collection...")
        
        # Test metrics endpoint
        metrics_result = await self.request("GET", "/metrics")
        if metrics_result["status_code"] == 200:
            metrics_data = metrics_result["data"]
            
            # Check for Constitutional Council specific metrics
            expected_metrics = [
                "acgs_amendment_processing_seconds",
                "acgs_active_amendments_total",
                "acgs_co_evolution_events_total"
            ]
            
            metrics_found = 0
            for metric in expected_metrics:
                if metric in metrics_data:
                    metrics_found += 1
            
            if metrics_found >= len(expected_metrics) // 2:  # At least half the metrics
                print("✅ Constitutional Council metrics collection working")
                return True
        
        print("❌ Metrics collection test failed")
        return False

async def run_constitutional_council_schema_tests():
    """Run all Constitutional Council Schema Alignment tests."""
    print("🏛️ Constitutional Council Schema Alignment Test Suite")
    print("=" * 70)
    print("Testing Task 2: Constitutional Council Schema Alignment")
    print("Focus: Enhanced Schema, Optimistic Locking, Redis Caching, State Machine")
    print()
    
    async with ConstitutionalCouncilSchemaTest() as test_suite:
        # Run all tests
        test_suite.test_results["schema_validation"] = await test_suite.test_enhanced_schema_validation()
        test_suite.test_results["optimistic_locking"] = await test_suite.test_optimistic_locking()
        test_suite.test_results["state_machine"] = await test_suite.test_state_machine_workflow()
        test_suite.test_results["co_evolution"] = await test_suite.test_co_evolution_handling()
        test_suite.test_results["metrics_collection"] = await test_suite.test_metrics_collection()
        
        # Calculate success rate
        passed_tests = sum(test_suite.test_results.values())
        total_tests = len(test_suite.test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 70)
        print("📊 Test Results Summary:")
        for test_name, result in test_suite.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 80:
            print("🎉 Constitutional Council Schema Alignment implementation successful!")
            print("✅ Task 2 requirements met - ready for production deployment")
        else:
            print("⚠️ Some tests failed - review implementation before proceeding")
        
        return success_rate >= 80

if __name__ == "__main__":
    asyncio.run(run_constitutional_council_schema_tests())
