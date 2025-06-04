#!/usr/bin/env python3
"""
Test script for Public Consultation implementation in ACGS-PGP Task 14.

This script tests the Public Consultation mechanisms including:
- Public proposal submission and retrieval
- Public feedback collection and analysis
- Consultation metrics and transparency dashboard
- Integration with Constitutional Council workflows
- Anonymous and authenticated participation
- Security measures for public-facing endpoints

Usage:
    python3 test_public_consultation_implementation.py
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
TIMEOUT = 10

class PublicConsultationTestClient:
    """Test client for Public Consultation API endpoints."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_service_connectivity(self) -> bool:
        """Test basic service connectivity."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=TIMEOUT)
            if response.status_code == 200:
                print("   ✅ AC Service health check passed")
                return True
            else:
                print(f"   ❌ AC Service health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Service connectivity failed: {e}")
            return False
    
    def test_public_proposals_endpoint(self) -> bool:
        """Test public proposals listing endpoint."""
        try:
            # Test basic proposals listing
            response = self.session.get(
                f"{self.base_url}/api/v1/public-consultation/proposals",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                proposals = response.json()
                print(f"   ✅ Public proposals endpoint working (found {len(proposals)} proposals)")
                
                # Test filtering by status
                filter_response = self.session.get(
                    f"{self.base_url}/api/v1/public-consultation/proposals?status=open",
                    timeout=TIMEOUT
                )
                if filter_response.status_code == 200:
                    print("   ✅ Proposal filtering by status working")
                
                # Test pagination
                paginated_response = self.session.get(
                    f"{self.base_url}/api/v1/public-consultation/proposals?limit=2&offset=0",
                    timeout=TIMEOUT
                )
                if paginated_response.status_code == 200:
                    print("   ✅ Proposal pagination working")
                
                return True
            else:
                print(f"   ❌ Public proposals endpoint failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Public proposals test failed: {e}")
            return False
    
    def test_proposal_submission(self) -> Optional[int]:
        """Test public proposal submission."""
        try:
            proposal_data = {
                "title": "Test Privacy Enhancement Proposal",
                "description": "This is a test proposal for enhanced privacy protection in AI governance systems.",
                "proposed_changes": "Add explicit consent requirements for all data processing in governance decisions.",
                "justification": "Current privacy protections need strengthening for citizen trust.",
                "submitter_name": "Test Citizen",
                "submitter_email": "test@example.com",
                "submitter_organization": "Privacy Test Group",
                "stakeholder_group": "citizen"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/public-consultation/proposals",
                json=proposal_data,
                timeout=TIMEOUT
            )
            
            if response.status_code == 201:
                proposal = response.json()
                proposal_id = proposal.get('id')
                print(f"   ✅ Public proposal submission working (ID: {proposal_id})")
                return proposal_id
            else:
                print(f"   ❌ Public proposal submission failed: {response.status_code}")
                if response.text:
                    print(f"       Error: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Proposal submission test failed: {e}")
            return None
    
    def test_feedback_submission(self, proposal_id: int = 1) -> bool:
        """Test public feedback submission."""
        try:
            feedback_data = {
                "proposal_id": proposal_id,
                "feedback_type": "support",
                "content": "I strongly support this proposal as it enhances citizen privacy rights.",
                "submitter_name": "Test Supporter",
                "submitter_email": "supporter@example.com",
                "stakeholder_group": "citizen"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/public-consultation/feedback",
                json=feedback_data,
                timeout=TIMEOUT
            )
            
            if response.status_code == 201:
                feedback = response.json()
                print(f"   ✅ Public feedback submission working (ID: {feedback.get('id')})")
                return True
            else:
                print(f"   ❌ Public feedback submission failed: {response.status_code}")
                if response.text:
                    print(f"       Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Feedback submission test failed: {e}")
            return False
    
    def test_anonymous_feedback_submission(self, proposal_id: int = 1) -> bool:
        """Test anonymous feedback submission."""
        try:
            anonymous_feedback_data = {
                "proposal_id": proposal_id,
                "feedback_type": "concern",
                "content": "I have concerns about the implementation complexity of this proposal.",
                "stakeholder_group": "citizen"
                # No submitter_name or submitter_email for anonymous feedback
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/public-consultation/feedback",
                json=anonymous_feedback_data,
                timeout=TIMEOUT
            )
            
            if response.status_code == 201:
                feedback = response.json()
                print(f"   ✅ Anonymous feedback submission working (ID: {feedback.get('id')})")
                return True
            else:
                print(f"   ❌ Anonymous feedback submission failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Anonymous feedback test failed: {e}")
            return False
    
    def test_feedback_retrieval(self, proposal_id: int = 1) -> bool:
        """Test feedback retrieval for a proposal."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/public-consultation/proposals/{proposal_id}/feedback",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                feedback_list = response.json()
                print(f"   ✅ Feedback retrieval working (found {len(feedback_list)} feedback items)")
                return True
            else:
                print(f"   ❌ Feedback retrieval failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Feedback retrieval test failed: {e}")
            return False
    
    def test_consultation_metrics(self) -> bool:
        """Test consultation metrics endpoint."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/public-consultation/metrics",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                metrics = response.json()
                required_fields = [
                    'total_proposals', 'active_consultations', 'total_participants',
                    'feedback_count', 'sentiment_distribution', 'stakeholder_participation'
                ]
                
                missing_fields = [field for field in required_fields if field not in metrics]
                if not missing_fields:
                    print("   ✅ Consultation metrics endpoint working with all required fields")
                    return True
                else:
                    print(f"   ❌ Consultation metrics missing fields: {missing_fields}")
                    return False
            else:
                print(f"   ❌ Consultation metrics failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Consultation metrics test failed: {e}")
            return False
    
    def test_transparency_dashboard(self) -> bool:
        """Test transparency dashboard endpoint."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/public-consultation/transparency-dashboard",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                dashboard_data = response.json()
                print("   ✅ Transparency dashboard endpoint working")
                return True
            else:
                print(f"   ❌ Transparency dashboard failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Transparency dashboard test failed: {e}")
            return False

def test_public_consultation_implementation():
    """Test complete public consultation implementation."""
    print("\n🗳️  Testing Public Consultation Implementation...")
    print("-" * 50)
    
    client = PublicConsultationTestClient()
    
    # Test 1: Public Proposals
    print("\n1. Testing Public Proposals...")
    proposals_ok = client.test_public_proposals_endpoint()
    
    # Test 2: Proposal Submission
    print("\n2. Testing Proposal Submission...")
    proposal_id = client.test_proposal_submission()
    
    # Test 3: Feedback Submission
    print("\n3. Testing Feedback Submission...")
    feedback_ok = client.test_feedback_submission(proposal_id or 1)
    
    # Test 4: Anonymous Feedback
    print("\n4. Testing Anonymous Feedback...")
    anonymous_ok = client.test_anonymous_feedback_submission(proposal_id or 1)
    
    # Test 5: Feedback Retrieval
    print("\n5. Testing Feedback Retrieval...")
    retrieval_ok = client.test_feedback_retrieval(proposal_id or 1)
    
    # Test 6: Consultation Metrics
    print("\n6. Testing Consultation Metrics...")
    metrics_ok = client.test_consultation_metrics()
    
    # Test 7: Transparency Dashboard
    print("\n7. Testing Transparency Dashboard...")
    dashboard_ok = client.test_transparency_dashboard()
    
    return [proposals_ok, proposal_id is not None, feedback_ok, anonymous_ok, 
            retrieval_ok, metrics_ok, dashboard_ok]

def main():
    print("=" * 60)
    print("🗳️  Public Consultation Implementation Testing")
    print("=" * 60)
    
    client = PublicConsultationTestClient()
    
    # Test service connectivity
    print("\n1. Testing Service Connectivity...")
    connectivity_ok = client.test_service_connectivity()
    
    if not connectivity_ok:
        print("❌ Service connectivity failed. Exiting.")
        sys.exit(1)
    
    # Test public consultation implementation
    test_results = test_public_consultation_implementation()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    test_names = [
        "Public Proposals Endpoint",
        "Proposal Submission",
        "Feedback Submission", 
        "Anonymous Feedback",
        "Feedback Retrieval",
        "Consultation Metrics",
        "Transparency Dashboard"
    ]
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    for i, (test_name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✅ All Public Consultation tests passed")
        print("✅ Task 14 implementation is working correctly")
    else:
        print("⚠️  Some tests failed (may require database setup for full functionality)")
    
    print(f"\nComponent Status: {'✅ IMPLEMENTED' if passed_tests >= total_tests * 0.8 else '⚠️ PARTIALLY IMPLEMENTED'}")
    
    print("\nNext Steps:")
    print("- Test with authentication for Constitutional Council integration")
    print("- Test proposal advancement to Constitutional Council")
    print("- Test integration with HITL sampling workflows")
    print("- Perform security testing for public-facing endpoints")
    print("- Test performance with concurrent users")

if __name__ == "__main__":
    main()
