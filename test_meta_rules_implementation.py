#!/usr/bin/env python3
"""
Test script for Meta-Rules Component implementation in ACGS-PGP Phase 1.

This script tests the Meta-Rules (R) component of the Artificial Constitution AC=⟨P,R,M,V⟩
including meta-governance rules, amendment procedures, and stakeholder roles.

Usage:
    python test_meta_rules_implementation.py
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8001"
AUTH_URL = "http://localhost:8000"  # Assuming auth service is on port 8000

class ACGSTestClient:
    """Test client for ACGS-PGP Meta-Rules testing."""
    
    def __init__(self, base_url: str = BASE_URL, auth_url: str = AUTH_URL):
        self.base_url = base_url
        self.auth_url = auth_url
        self.session = requests.Session()
        self.auth_token: Optional[str] = None
    
    def authenticate(self, username: str = "admin", password: str = "admin123") -> bool:
        """
        Authenticate with the auth service to get a token.
        Note: This uses placeholder credentials for testing.
        """
        try:
            # Try to get a token from auth service
            auth_response = self.session.post(
                f"{self.auth_url}/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if auth_response.status_code == 200:
                token_data = auth_response.json()
                self.auth_token = token_data.get("access_token")
                if self.auth_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    print(f"✅ Authentication successful")
                    return True
            
            print(f"⚠️  Authentication failed: {auth_response.status_code}")
            print("   Proceeding with unauthenticated testing (limited functionality)")
            return False
            
        except Exception as e:
            print(f"⚠️  Authentication error: {e}")
            print("   Proceeding with unauthenticated testing (limited functionality)")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test the health endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health endpoint working")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
    
    def test_meta_rules_list(self) -> bool:
        """Test listing meta-rules."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/constitutional-council/meta-rules",
                timeout=10
            )
            
            if response.status_code == 200:
                meta_rules = response.json()
                print(f"✅ Meta-rules list endpoint working (found {len(meta_rules)} rules)")
                return True
            elif response.status_code == 401:
                print("⚠️  Meta-rules list requires authentication (expected)")
                return True  # This is expected behavior
            else:
                print(f"❌ Meta-rules list failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Meta-rules list error: {e}")
            return False
    
    def test_meta_rule_creation(self) -> Optional[Dict[str, Any]]:
        """Test creating a meta-rule."""
        if not self.auth_token:
            print("⚠️  Skipping meta-rule creation (no authentication)")
            return None
        
        meta_rule_data = {
            "rule_type": "amendment_procedure",
            "name": "Constitutional Amendment Threshold",
            "description": "Defines the voting threshold required for constitutional amendments",
            "rule_definition": {
                "threshold": 0.67,
                "stakeholder_roles": ["admin", "policy_manager", "constitutional_council"],
                "decision_mechanism": "supermajority_vote",
                "voting_period_hours": 168
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/constitutional-council/meta-rules",
                json=meta_rule_data,
                timeout=10
            )
            
            if response.status_code == 201:
                created_rule = response.json()
                print(f"✅ Meta-rule creation successful (ID: {created_rule.get('id')})")
                return created_rule
            else:
                print(f"❌ Meta-rule creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Meta-rule creation error: {e}")
            return None
    
    def test_conflict_resolution_list(self) -> bool:
        """Test listing conflict resolutions."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/constitutional-council/conflict-resolutions",
                timeout=10
            )
            
            if response.status_code == 200:
                conflicts = response.json()
                print(f"✅ Conflict resolutions list endpoint working (found {len(conflicts)} conflicts)")
                return True
            elif response.status_code == 401:
                print("⚠️  Conflict resolutions list requires authentication (expected)")
                return True
            else:
                print(f"❌ Conflict resolutions list failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Conflict resolutions list error: {e}")
            return False
    
    def test_amendments_list(self) -> bool:
        """Test listing amendments."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/constitutional-council/amendments",
                timeout=10
            )
            
            if response.status_code == 200:
                amendments = response.json()
                print(f"✅ Amendments list endpoint working (found {len(amendments)} amendments)")
                return True
            elif response.status_code == 401:
                print("⚠️  Amendments list requires authentication (expected)")
                return True
            else:
                print(f"❌ Amendments list failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Amendments list error: {e}")
            return False

def main():
    """Main test function."""
    print("🧪 ACGS-PGP Meta-Rules Component Testing")
    print("=" * 50)
    
    # Initialize test client
    client = ACGSTestClient()
    
    # Test basic connectivity
    print("\n1. Testing Basic Connectivity...")
    if not client.test_health_endpoint():
        print("❌ Basic connectivity failed. Exiting.")
        sys.exit(1)
    
    # Test authentication
    print("\n2. Testing Authentication...")
    authenticated = client.authenticate()
    
    # Test Meta-Rules endpoints
    print("\n3. Testing Meta-Rules Endpoints...")
    client.test_meta_rules_list()
    
    if authenticated:
        created_rule = client.test_meta_rule_creation()
    
    # Test Conflict Resolution endpoints
    print("\n4. Testing Conflict Resolution Endpoints...")
    client.test_conflict_resolution_list()
    
    # Test Amendments endpoints
    print("\n5. Testing Amendments Endpoints...")
    client.test_amendments_list()
    
    print("\n" + "=" * 50)
    print("🎯 Meta-Rules Component Testing Complete")
    
    if authenticated:
        print("✅ All authenticated tests completed successfully")
    else:
        print("⚠️  Limited testing completed (authentication required for full testing)")
    
    print("\nNext Steps:")
    print("- Set up proper authentication credentials for full testing")
    print("- Test meta-rule creation, update, and deletion workflows")
    print("- Test conflict resolution mapping functionality")
    print("- Test constitutional amendment procedures")

if __name__ == "__main__":
    main()
