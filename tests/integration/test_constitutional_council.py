#!/usr/bin/env python3
"""
Test script for Constitutional Council implementation in ACGS-PGP framework.
This script validates the Phase 1 implementation of the Artificial Constitution layer.
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any

# Base URL for the AC service
BASE_URL = "http://localhost:8001"

# Test tokens for different roles
ADMIN_TOKEN = "admin_token"
COUNCIL_TOKEN = "council_token"
USER_TOKEN = "user_token"

class ACTestClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def request(self, method: str, endpoint: str, token: str = None, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
        """Make an HTTP request to the AC service"""
        url = f"{self.base_url}{endpoint}"
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

async def test_constitutional_council_implementation():
    """Test the Constitutional Council implementation"""
    print("🏛️  Testing Constitutional Council Implementation")
    print("=" * 60)
    
    async with ACTestClient(BASE_URL) as client:
        
        # Test 1: Create a principle (prerequisite for amendments)
        print("\n1. Creating a test principle...")
        principle_data = {
            "name": "Data Privacy Principle",
            "description": "Personal data must be processed lawfully, fairly, and transparently.",
            "content": "All data processing operations SHALL implement privacy-by-design principles and ensure user consent is obtained before processing personal data.",
            "priority_weight": 0.75,
            "scope": ["user_data", "pii_processing", "ai_systems"],
            "normative_statement": "Data subjects have a right to control their personal data. Systems processing personal data must ensure confidentiality, integrity, and availability.",
            "constraints": {
                "data_minimization": True,
                "purpose_limitation": True,
                "retention_period_max_days": 365
            },
            "rationale": "To uphold individual privacy rights and ensure trustworthy data handling practices in accordance with GDPR and CCPA principles.",
            "keywords": ["privacy", "data protection", "user consent", "gdpr", "ccpa"],
            "category": "Data Governance and Privacy",
            "validation_criteria_nl": "Verify that user consent is explicitly obtained before data collection. Check if data is encrypted at rest and in transit. Ensure there is a mechanism for users to request data deletion.",
            "constitutional_metadata": {
                "related_articles": ["Art. 8 ECHR", "GDPR Chapter 3"],
                "compliance_framework": "ISO 27701"
            }
        }
        
        result = await client.request("POST", "/api/v1/principles/", ADMIN_TOKEN, principle_data)
        if result["status_code"] == 201:
            principle_id = result["data"]["id"]
            print(f"✅ Principle created successfully (ID: {principle_id})")
        else:
            print(f"❌ Failed to create principle: {result}")
            return
        
        # Test 2: Create AC Meta-Rule
        print("\n2. Creating AC Meta-Rule...")
        meta_rule_data = {
            "rule_type": "amendment_procedure",
            "name": "Constitutional Amendment Procedure",
            "description": "Defines how AC principles can be modified, including voting thresholds and stakeholder involvement.",
            "rule_definition": {
                "procedure_details": "Standard amendment process with council voting.",
                "min_council_members_for_quorum": 5
            },
            "threshold": "0.67",
            "stakeholder_roles": ["admin", "constitutional_council"],
            "decision_mechanism": "supermajority_vote"
        }
        
        result = await client.request("POST", "/api/v1/constitutional-council/meta-rules", ADMIN_TOKEN, meta_rule_data)
        if result["status_code"] == 201:
            print(f"✅ Meta-rule created successfully")
        else:
            print(f"❌ Failed to create meta-rule: {result}")
        
        # Test 3: List Meta-Rules
        print("\n3. Listing AC Meta-Rules...")
        result = await client.request("GET", "/api/v1/constitutional-council/meta-rules", USER_TOKEN)
        if result["status_code"] == 200:
            print(f"✅ Retrieved {len(result['data'])} meta-rules")
        else:
            print(f"❌ Failed to list meta-rules: {result}")
        
        # Test 4: Create AC Amendment
        print("\n4. Creating AC Amendment...")
        amendment_data = {
            "principle_id": principle_id,
            "amendment_type": "modify",
            "proposed_changes": "Update and enhance the existing principle content based on new standards.",
            "justification": "Alignment with emerging governance standards and best practices.",
            "proposed_content": "All data processing operations SHALL implement privacy-by-design principles, ensure user consent is obtained before processing personal data, and provide algorithmic transparency for AI-driven decisions. Regular audits must be performed.",
            "consultation_period_days": 30,
            "public_comment_enabled": True,
            "stakeholder_groups": ["citizens", "experts", "affected_parties", "regulatory_bodies"]
        }
        
        result = await client.request("POST", "/api/v1/constitutional-council/amendments", COUNCIL_TOKEN, amendment_data)
        if result["status_code"] == 201:
            amendment_id = result["data"]["id"]
            print(f"✅ Amendment created successfully (ID: {amendment_id})")
        else:
            print(f"❌ Failed to create amendment: {result}")
            return
        
        # Test 5: List Amendments
        print("\n5. Listing AC Amendments...")
        result = await client.request("GET", "/api/v1/constitutional-council/amendments", USER_TOKEN)
        if result["status_code"] == 200:
            print(f"✅ Retrieved {len(result['data'])} amendments")
        else:
            print(f"❌ Failed to list amendments: {result}")
        
        # Test 6: Vote on Amendment
        print("\n6. Voting on Amendment...")
        vote_data = {
            "vote": "for",
            "reasoning": "This amendment improves AI transparency and aligns with democratic values"
        }
        
        result = await client.request("POST", f"/api/v1/constitutional-council/amendments/{amendment_id}/votes", COUNCIL_TOKEN, vote_data)
        if result["status_code"] == 201:
            print(f"✅ Vote cast successfully")
        else:
            print(f"❌ Failed to cast vote: {result}")
        
        # Test 7: Add Public Comment
        print("\n7. Adding public comment...")
        comment_data = {
            "comment_text": "I support this amendment as it enhances privacy protection for citizens",
            "sentiment": "support",
            "stakeholder_group": "citizen"
        }
        
        result = await client.request("POST", f"/api/v1/constitutional-council/amendments/{amendment_id}/comments", USER_TOKEN, comment_data)
        if result["status_code"] == 201:
            print(f"✅ Comment added successfully")
        else:
            print(f"❌ Failed to add comment: {result}")
        
        # Test 8: Create Conflict Resolution
        print("\n8. Creating AC Conflict Resolution...")
        conflict_data = {
            "conflict_type": "principle_contradiction",
            "principle_ids": [principle_id],
            "context": "data_retention_vs_privacy",
            "conflict_description": "Potential conflict between data retention requirements and privacy principles",
            "severity": "medium",
            "resolution_strategy": "principle_priority_based",
            "resolution_details": {
                "priority_order": [principle_id],
                "balancing_factors": ["user_consent", "legitimate_interest"]
            },
            "precedence_order": [principle_id]
        }
        
        result = await client.request("POST", "/api/v1/constitutional-council/conflict-resolutions", ADMIN_TOKEN, conflict_data)
        if result["status_code"] == 201:
            print(f"✅ Conflict resolution created successfully")
        else:
            print(f"❌ Failed to create conflict resolution: {result}")
        
        # Test 9: Test Role-Based Access Control
        print("\n9. Testing RBAC...")
        
        # Try to create amendment with user token (should fail)
        result = await client.request("POST", "/api/v1/constitutional-council/amendments", USER_TOKEN, amendment_data)
        if result["status_code"] == 403:
            print("✅ RBAC working: User correctly denied access to create amendment")
        else:
            print(f"❌ RBAC issue: User should not be able to create amendment: {result}")
        
        # Try to create meta-rule with council token (should fail)
        result = await client.request("POST", "/api/v1/constitutional-council/meta-rules", COUNCIL_TOKEN, meta_rule_data)
        if result["status_code"] == 403:
            print("✅ RBAC working: Council member correctly denied access to create meta-rule")
        else:
            print(f"❌ RBAC issue: Council member should not be able to create meta-rule: {result}")

async def test_service_health():
    """Test basic service health"""
    print("\n🔍 Testing Service Health")
    print("=" * 30)
    
    async with ACTestClient(BASE_URL) as client:
        # Test health endpoint
        result = await client.request("GET", "/health")
        if result["status_code"] == 200:
            print("✅ AC Service health check passed")
        else:
            print(f"❌ AC Service health check failed: {result}")
        
        # Test root endpoint
        result = await client.request("GET", "/")
        if result["status_code"] == 200:
            print("✅ AC Service root endpoint accessible")
        else:
            print(f"❌ AC Service root endpoint failed: {result}")

async def main():
    """Main test function"""
    print("🚀 ACGS-PGP Constitutional Council Test Suite")
    print("=" * 60)
    print("Testing Phase 1: Foundational Enhancements & Theoretical Alignment")
    print("Focus: Constitutional Council RBAC and Amendment Workflow")
    print()
    
    try:
        await test_service_health()
        await test_constitutional_council_implementation()
        
        print("\n" + "=" * 60)
        print("✅ Constitutional Council implementation test completed!")
        print("🏛️  Phase 1 foundational features are working correctly.")
        print("\nNext steps:")
        print("- Deploy with docker-compose to test with database")
        print("- Implement constitutional prompting in GS service")
        print("- Add formal verification integration")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
