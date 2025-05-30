#!/usr/bin/env python3
"""
Phase 3 Appeal and Dispute Resolution Test Script for ACGS-PGP
Tests the democratic governance mechanisms for challenging algorithmic decisions
"""

import asyncio
import json
import sys
import time
from typing import Dict, List, Any
import httpx

# Test configuration
BASE_URL = "http://localhost:8002"  # Integrity service port
ADMIN_TOKEN = "admin_token"  # Replace with actual admin token
TEST_TIMEOUT = 30

class Phase3AppealsTestRunner:
    """Test runner for Phase 3 appeal and dispute resolution features."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        self.headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test_result(self, test_name: str, passed: bool, message: str):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": time.time()
        })
    
    async def test_create_appeal(self):
        """Test creating a new appeal."""
        test_name = "Create Appeal"
        
        try:
            appeal_data = {
                "decision_id": "decision_12345",
                "appeal_reason": "I believe the decision was made in error due to incorrect data processing",
                "evidence": "Attached documentation shows that my profile was incorrectly categorized",
                "requested_remedy": "Please review the decision and correct the categorization",
                "appellant_contact": "user@example.com"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/appeals",
                headers=self.headers,
                json=appeal_data
            )
            
            if response.status_code == 201:
                appeal = response.json()
                required_fields = ["id", "decision_id", "status", "escalation_level", "submitted_at"]
                if all(field in appeal for field in required_fields):
                    self.log_test_result(test_name, True, f"Appeal created with ID {appeal['id']}")
                    return appeal["id"]
                else:
                    self.log_test_result(test_name, False, "Missing required fields in appeal response")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
        
        return None
    
    async def test_get_appeals(self):
        """Test retrieving appeals list."""
        test_name = "Get Appeals List"
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/appeals",
                headers=self.headers
            )
            
            if response.status_code == 200:
                appeals_list = response.json()
                if "appeals" in appeals_list and "total" in appeals_list:
                    self.log_test_result(test_name, True, f"Retrieved {appeals_list['total']} appeals")
                else:
                    self.log_test_result(test_name, False, "Missing required fields in appeals list response")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_get_appeal_by_id(self, appeal_id: int):
        """Test retrieving a specific appeal by ID."""
        test_name = "Get Appeal by ID"
        
        if not appeal_id:
            self.log_test_result(test_name, False, "No appeal ID provided")
            return
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/appeals/{appeal_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                appeal = response.json()
                if appeal["id"] == appeal_id:
                    self.log_test_result(test_name, True, f"Retrieved appeal {appeal_id} with status {appeal['status']}")
                else:
                    self.log_test_result(test_name, False, "Appeal ID mismatch in response")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_update_appeal(self, appeal_id: int):
        """Test updating an appeal."""
        test_name = "Update Appeal"
        
        if not appeal_id:
            self.log_test_result(test_name, False, "No appeal ID provided")
            return
        
        try:
            update_data = {
                "status": "under_review",
                "reviewer_notes": "Appeal is being reviewed by the technical team"
            }
            
            response = await self.client.patch(
                f"{BASE_URL}/api/v1/appeals/{appeal_id}",
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code == 200:
                appeal = response.json()
                if appeal["status"] == "under_review":
                    self.log_test_result(test_name, True, f"Appeal {appeal_id} updated to under_review status")
                else:
                    self.log_test_result(test_name, False, "Appeal status not updated correctly")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_escalate_appeal(self, appeal_id: int):
        """Test escalating an appeal."""
        test_name = "Escalate Appeal"
        
        if not appeal_id:
            self.log_test_result(test_name, False, "No appeal ID provided")
            return
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/v1/appeals/{appeal_id}/escalate",
                headers=self.headers
            )
            
            if response.status_code == 200:
                appeal = response.json()
                if appeal["escalation_level"] > 1:
                    self.log_test_result(test_name, True, f"Appeal {appeal_id} escalated to level {appeal['escalation_level']}")
                else:
                    self.log_test_result(test_name, False, "Appeal escalation level not increased")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_create_dispute_resolution(self, appeal_id: int):
        """Test creating a dispute resolution process."""
        test_name = "Create Dispute Resolution"
        
        if not appeal_id:
            self.log_test_result(test_name, False, "No appeal ID provided")
            return None
        
        try:
            dispute_data = {
                "appeal_id": appeal_id,
                "resolution_method": "technical_review",
                "panel_composition": ["technical_expert_1", "technical_expert_2", "ombudsperson"],
                "timeline_days": 14
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/dispute-resolutions",
                headers=self.headers,
                json=dispute_data
            )
            
            if response.status_code == 201:
                dispute = response.json()
                required_fields = ["id", "appeal_id", "resolution_method", "status"]
                if all(field in dispute for field in required_fields):
                    self.log_test_result(test_name, True, f"Dispute resolution created with ID {dispute['id']}")
                    return dispute["id"]
                else:
                    self.log_test_result(test_name, False, "Missing required fields in dispute resolution response")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
        
        return None
    
    async def test_explain_decision(self):
        """Test decision explanation functionality."""
        test_name = "Explain Decision"
        
        try:
            explanation_request = {
                "decision_id": "decision_12345",
                "explanation_level": "standard",
                "include_counterfactuals": True,
                "target_audience": "affected_individual"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/explain",
                headers=self.headers,
                json=explanation_request
            )
            
            if response.status_code == 200:
                explanation = response.json()
                required_fields = ["decision_id", "explanation", "rule_provenance", "confidence_score"]
                if all(field in explanation for field in required_fields):
                    self.log_test_result(test_name, True, f"Explanation generated with confidence {explanation['confidence_score']:.3f}")
                else:
                    self.log_test_result(test_name, False, "Missing required fields in explanation response")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_rule_provenance(self):
        """Test rule provenance functionality."""
        test_name = "Rule Provenance"
        
        try:
            rule_id = "rule_001"
            
            response = await self.client.get(
                f"{BASE_URL}/api/v1/provenance/{rule_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                provenance = response.json()
                required_fields = ["rule_id", "source_principles", "creation_context", "modification_history"]
                if all(field in provenance for field in required_fields):
                    self.log_test_result(test_name, True, f"Provenance retrieved for rule {rule_id}")
                else:
                    self.log_test_result(test_name, False, "Missing required fields in provenance response")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all Phase 3 appeal and dispute resolution tests."""
        print("🚀 Starting Phase 3 Appeal and Dispute Resolution Tests")
        print("=" * 60)
        
        # Test sequence
        appeal_id = await self.test_create_appeal()
        await asyncio.sleep(0.5)
        
        await self.test_get_appeals()
        await asyncio.sleep(0.5)
        
        if appeal_id:
            await self.test_get_appeal_by_id(appeal_id)
            await asyncio.sleep(0.5)
            
            await self.test_update_appeal(appeal_id)
            await asyncio.sleep(0.5)
            
            await self.test_escalate_appeal(appeal_id)
            await asyncio.sleep(0.5)
            
            dispute_id = await self.test_create_dispute_resolution(appeal_id)
            await asyncio.sleep(0.5)
        
        await self.test_explain_decision()
        await asyncio.sleep(0.5)
        
        await self.test_rule_provenance()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        passed_tests = [r for r in self.test_results if r["passed"]]
        failed_tests = [r for r in self.test_results if not r["passed"]]
        
        print(f"✅ Passed: {len(passed_tests)}/{len(self.test_results)}")
        print(f"❌ Failed: {len(failed_tests)}/{len(self.test_results)}")
        
        if failed_tests:
            print("\nFailed Tests:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['message']}")
        
        # Save results
        with open("phase3_appeals_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        return len(failed_tests) == 0


async def main():
    """Main test execution."""
    print("Phase 3 Appeal and Dispute Resolution Test Suite")
    print("Testing democratic governance mechanisms for challenging algorithmic decisions")
    print()
    
    async with Phase3AppealsTestRunner() as test_runner:
        success = await test_runner.run_all_tests()
        
        if success:
            print("\n🎉 All Phase 3 appeal and dispute resolution tests passed!")
            sys.exit(0)
        else:
            print("\n💥 Some Phase 3 appeal and dispute resolution tests failed!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
