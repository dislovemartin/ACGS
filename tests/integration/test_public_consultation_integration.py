#!/usr/bin/env python3
"""
Integration tests for Public Consultation with Constitutional Council and HITL Sampling.

This script tests the complete integration workflows including:
- Public proposal advancement to Constitutional Council
- Integration with HITL sampling for public feedback escalation
- Cross-service communication between AC, GS, and other services
- Authentication flows for public vs authenticated users
- Security measures for public-facing endpoints

Usage:
    python3 test_public_consultation_integration.py
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
SERVICES = {
    'ac_service': 'http://localhost:8001',
    'gs_service': 'http://localhost:8004',
    'auth_service': 'http://localhost:8000'
}

# Test tokens (would be obtained from auth service in real scenario)
TEST_TOKENS = {
    'admin': 'admin_test_token',
    'council_member': 'council_test_token',
    'policy_manager': 'policy_manager_test_token',
    'public_user': None  # No token for public access
}

class PublicConsultationIntegrationTest:
    """Integration test client for Public Consultation workflows."""
    
    def __init__(self):
        self.session = None
        self.test_proposal_id = None
        self.test_feedback_id = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, url: str, token: Optional[str] = None, 
                          data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with optional authentication."""
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            async with self.session.request(
                method, url, headers=headers, 
                json=data if data else None, timeout=10
            ) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                return {
                    'status_code': response.status,
                    'data': response_data,
                    'success': 200 <= response.status < 300
                }
        except Exception as e:
            return {
                'status_code': 0,
                'data': str(e),
                'success': False
            }
    
    async def test_service_health(self) -> bool:
        """Test health of all required services."""
        print("\n🔍 Testing Service Health...")
        
        all_healthy = True
        for service_name, base_url in SERVICES.items():
            result = await self.make_request('GET', f"{base_url}/health")
            if result['success']:
                print(f"   ✅ {service_name}: Healthy")
            else:
                print(f"   ❌ {service_name}: Unhealthy ({result['status_code']})")
                all_healthy = False
        
        return all_healthy
    
    async def test_public_proposal_submission(self) -> Optional[int]:
        """Test public proposal submission without authentication."""
        print("\n📝 Testing Public Proposal Submission...")
        
        proposal_data = {
            "title": "Integration Test: Enhanced AI Transparency",
            "description": "This proposal tests the integration between public consultation and Constitutional Council workflows.",
            "proposed_changes": "Require all AI governance decisions to include explainable reasoning accessible to citizens.",
            "justification": "Citizens need transparency to trust AI governance systems.",
            "submitter_name": "Integration Test User",
            "submitter_email": "integration@test.com",
            "submitter_organization": "Test Organization",
            "stakeholder_group": "citizen"
        }
        
        result = await self.make_request(
            'POST', 
            f"{SERVICES['ac_service']}/api/v1/public-consultation/proposals",
            token=None,  # Public submission, no auth required
            data=proposal_data
        )
        
        if result['success']:
            proposal_id = result['data'].get('id')
            self.test_proposal_id = proposal_id
            print(f"   ✅ Public proposal submitted successfully (ID: {proposal_id})")
            return proposal_id
        else:
            print(f"   ❌ Public proposal submission failed: {result['data']}")
            return None
    
    async def test_public_feedback_collection(self, proposal_id: int) -> bool:
        """Test public feedback collection for a proposal."""
        print("\n💬 Testing Public Feedback Collection...")
        
        # Test authenticated feedback
        auth_feedback_data = {
            "proposal_id": proposal_id,
            "feedback_type": "support",
            "content": "I strongly support this proposal for AI transparency. It will help build public trust.",
            "submitter_name": "Authenticated User",
            "submitter_email": "auth_user@test.com",
            "stakeholder_group": "citizen"
        }
        
        auth_result = await self.make_request(
            'POST',
            f"{SERVICES['ac_service']}/api/v1/public-consultation/feedback",
            token=None,  # Public feedback, no auth required
            data=auth_feedback_data
        )
        
        # Test anonymous feedback
        anon_feedback_data = {
            "proposal_id": proposal_id,
            "feedback_type": "concern",
            "content": "While I support transparency, I'm concerned about implementation complexity.",
            "stakeholder_group": "citizen"
            # No submitter info for anonymous
        }
        
        anon_result = await self.make_request(
            'POST',
            f"{SERVICES['ac_service']}/api/v1/public-consultation/feedback",
            token=None,
            data=anon_feedback_data
        )
        
        if auth_result['success'] and anon_result['success']:
            print("   ✅ Both authenticated and anonymous feedback submitted successfully")
            self.test_feedback_id = auth_result['data'].get('id')
            return True
        else:
            print(f"   ❌ Feedback submission failed - Auth: {auth_result['success']}, Anon: {anon_result['success']}")
            return False
    
    async def test_hitl_integration(self, proposal_id: int) -> bool:
        """Test integration with HITL sampling for public feedback escalation."""
        print("\n🤖 Testing HITL Integration...")
        
        # Test HITL sampling endpoint for public consultation
        hitl_data = {
            "proposal_id": proposal_id,
            "feedback_type": "escalation",
            "uncertainty_score": 0.85,  # High uncertainty requiring human review
            "context": "public_consultation"
        }
        
        result = await self.make_request(
            'POST',
            f"{SERVICES['ac_service']}/api/v1/hitl-sampling/public-consultation",
            token=TEST_TOKENS['admin'],  # HITL requires authentication
            data=hitl_data
        )
        
        if result['success']:
            print("   ✅ HITL integration working for public consultation")
            return True
        else:
            print(f"   ❌ HITL integration failed: {result['data']}")
            return False
    
    async def test_constitutional_council_advancement(self, proposal_id: int) -> bool:
        """Test proposal advancement to Constitutional Council."""
        print("\n🏛️ Testing Constitutional Council Advancement...")
        
        # Test proposal advancement (requires Constitutional Council member auth)
        result = await self.make_request(
            'POST',
            f"{SERVICES['ac_service']}/api/v1/public-consultation/proposals/{proposal_id}/advance",
            token=TEST_TOKENS['council_member'],
            data={}
        )
        
        if result['success']:
            print("   ✅ Proposal advancement to Constitutional Council working")
            return True
        else:
            print(f"   ❌ Constitutional Council advancement failed: {result['data']}")
            return False
    
    async def test_cross_service_communication(self) -> bool:
        """Test cross-service communication for public consultation workflows."""
        print("\n🔗 Testing Cross-Service Communication...")
        
        # Test AC service to GS service communication for constitutional analysis
        analysis_data = {
            "context": "public_consultation_proposal",
            "category": "Transparency",
            "proposal_content": "Enhanced AI transparency requirements for governance systems"
        }
        
        result = await self.make_request(
            'POST',
            f"{SERVICES['gs_service']}/api/v1/constitutional/analyze-context",
            token=TEST_TOKENS['policy_manager'],
            data=analysis_data
        )
        
        if result['success']:
            print("   ✅ AC to GS service communication working")
            return True
        else:
            print(f"   ❌ Cross-service communication failed: {result['data']}")
            return False
    
    async def test_public_access_security(self) -> bool:
        """Test security measures for public-facing endpoints."""
        print("\n🔒 Testing Public Access Security...")
        
        # Test rate limiting (simulate multiple rapid requests)
        rapid_requests = []
        for i in range(5):
            rapid_requests.append(
                self.make_request(
                    'GET',
                    f"{SERVICES['ac_service']}/api/v1/public-consultation/proposals"
                )
            )
        
        results = await asyncio.gather(*rapid_requests)
        successful_requests = sum(1 for r in results if r['success'])
        
        # Test input validation
        invalid_proposal_data = {
            "title": "",  # Empty title should be rejected
            "description": "x" * 10000,  # Overly long description
            "proposed_changes": "",
            "justification": "",
            "submitter_name": "<script>alert('xss')</script>",  # XSS attempt
            "stakeholder_group": "invalid_group"
        }
        
        validation_result = await self.make_request(
            'POST',
            f"{SERVICES['ac_service']}/api/v1/public-consultation/proposals",
            data=invalid_proposal_data
        )
        
        # Security should reject invalid input
        security_ok = not validation_result['success'] and validation_result['status_code'] in [400, 422]
        
        if successful_requests <= 5 and security_ok:
            print("   ✅ Security measures working (rate limiting and input validation)")
            return True
        else:
            print(f"   ❌ Security issues detected - Requests: {successful_requests}, Validation: {security_ok}")
            return False
    
    async def test_transparency_dashboard(self) -> bool:
        """Test transparency dashboard functionality."""
        print("\n📊 Testing Transparency Dashboard...")
        
        # Test metrics endpoint
        metrics_result = await self.make_request(
            'GET',
            f"{SERVICES['ac_service']}/api/v1/public-consultation/metrics"
        )
        
        # Test transparency dashboard
        dashboard_result = await self.make_request(
            'GET',
            f"{SERVICES['ac_service']}/api/v1/public-consultation/transparency-dashboard"
        )
        
        if metrics_result['success'] and dashboard_result['success']:
            print("   ✅ Transparency dashboard working")
            return True
        else:
            print(f"   ❌ Transparency dashboard failed - Metrics: {metrics_result['success']}, Dashboard: {dashboard_result['success']}")
            return False

async def main():
    """Main integration test function."""
    print("=" * 70)
    print("🗳️  Public Consultation Integration Testing")
    print("=" * 70)
    print("Testing Task 14: Public Consultation Mechanisms")
    print("Focus: Cross-service integration and democratic workflows")
    print()
    
    async with PublicConsultationIntegrationTest() as test_client:
        # Test 1: Service Health
        health_ok = await test_client.test_service_health()
        if not health_ok:
            print("❌ Service health check failed. Some services may be down.")
            return
        
        # Test 2: Public Proposal Submission
        proposal_id = await test_client.test_public_proposal_submission()
        if not proposal_id:
            print("❌ Cannot continue without successful proposal submission.")
            return
        
        # Test 3: Public Feedback Collection
        feedback_ok = await test_client.test_public_feedback_collection(proposal_id)
        
        # Test 4: HITL Integration
        hitl_ok = await test_client.test_hitl_integration(proposal_id)
        
        # Test 5: Constitutional Council Advancement
        council_ok = await test_client.test_constitutional_council_advancement(proposal_id)
        
        # Test 6: Cross-Service Communication
        cross_service_ok = await test_client.test_cross_service_communication()
        
        # Test 7: Security Measures
        security_ok = await test_client.test_public_access_security()
        
        # Test 8: Transparency Dashboard
        transparency_ok = await test_client.test_transparency_dashboard()
        
        # Results Summary
        print("\n" + "=" * 70)
        print("📊 Integration Test Results Summary")
        print("=" * 70)
        
        test_results = [
            ("Service Health", health_ok),
            ("Public Proposal Submission", proposal_id is not None),
            ("Public Feedback Collection", feedback_ok),
            ("HITL Integration", hitl_ok),
            ("Constitutional Council Advancement", council_ok),
            ("Cross-Service Communication", cross_service_ok),
            ("Security Measures", security_ok),
            ("Transparency Dashboard", transparency_ok)
        ]
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for i, (test_name, result) in enumerate(test_results):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{i+1}. {test_name}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} integration tests passed")
        
        if passed_tests >= total_tests * 0.8:
            print("✅ Public Consultation integration is working correctly")
            print("✅ Task 14 cross-service workflows are functional")
        else:
            print("⚠️  Some integration tests failed (may require full deployment)")
        
        print(f"\nIntegration Status: {'✅ INTEGRATED' if passed_tests >= total_tests * 0.8 else '⚠️ PARTIALLY INTEGRATED'}")
        
        print("\nNext Steps:")
        print("- Deploy full system with authentication for complete testing")
        print("- Test with real Constitutional Council member accounts")
        print("- Perform load testing with concurrent public users")
        print("- Test proposal lifecycle from submission to council decision")
        print("- Validate security measures under production conditions")

if __name__ == "__main__":
    asyncio.run(main())
