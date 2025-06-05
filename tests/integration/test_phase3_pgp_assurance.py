#!/usr/bin/env python3
"""
Phase 3 PGP Assurance Test Script for ACGS-PGP
Tests the cryptographic integrity features including digital signatures, Merkle trees, key management, and timestamping
"""

import asyncio
import json
import sys
import time
from typing import Dict, List, Any
import httpx

# Test configuration
BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "admin_token"  # Replace with actual admin token
TEST_TIMEOUT = 30

class Phase3PGPAssuranceTestRunner:
    """Test runner for Phase 3 PGP Assurance functionality"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        self.headers = {
            "Authorization": f"Bearer {ADMIN_TOKEN}",
            "Content-Type": "application/json"
        }
        self.test_results = []
        self.generated_key_id = None
        self.test_ac_data = "test_ac_version_1.0_constitutional_principles"
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        
        self.test_results.append({
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": time.time()
        })
    
    async def test_integrity_service_health(self):
        """Test integrity service health check"""
        test_name = "Integrity Service Health Check"
        
        try:
            response = await self.client.get(f"{BASE_URL}/integrity/health")
            
            if response.status_code == 200:
                self.log_test_result(test_name, True, "Service is healthy")
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Connection error: {e}")
            return False
    
    async def test_pgp_assurance_health(self):
        """Test PGP Assurance service health check"""
        test_name = "PGP Assurance Health Check"
        
        try:
            response = await self.client.get(f"{BASE_URL}/integrity/api/v1/pgp-assurance/health")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test_result(test_name, True, f"Status: {result.get('status')}")
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Connection error: {e}")
            return False
    
    async def test_key_generation(self):
        """Test cryptographic key generation"""
        test_name = "Key Generation"
        
        try:
            key_data = {
                "algorithm": "ECDSA_P256",
                "key_id": f"test_key_{int(time.time())}"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/integrity/api/v1/pgp-assurance/generate-keys",
                headers=self.headers,
                json=key_data
            )
            
            if response.status_code == 201:
                result = response.json()
                self.generated_key_id = result["key_id"]
                self.log_test_result(test_name, True, f"Generated key: {self.generated_key_id}")
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {e}")
            return False
    
    async def test_ac_version_signing(self):
        """Test AC version digital signing"""
        test_name = "AC Version Digital Signing"
        
        if not self.generated_key_id:
            self.log_test_result(test_name, False, "No key available for signing")
            return False
        
        try:
            sign_data = {
                "ac_version_data": self.test_ac_data,
                "key_id": self.generated_key_id,
                "algorithm": "ECDSA_P256",
                "include_timestamp": True
            }
            
            response = await self.client.post(
                f"{BASE_URL}/integrity/api/v1/pgp-assurance/sign-ac-version",
                headers=self.headers,
                json=sign_data
            )
            
            if response.status_code == 201:
                result = response.json()
                self.integrity_package = result["integrity_package"]
                self.log_test_result(test_name, True, f"Signature ID: {result['signature_id']}")
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {e}")
            return False
    
    async def test_signature_verification(self):
        """Test digital signature verification"""
        test_name = "Digital Signature Verification"
        
        if not hasattr(self, 'integrity_package'):
            self.log_test_result(test_name, False, "No integrity package available for verification")
            return False
        
        try:
            verify_data = {
                "data": self.test_ac_data,
                "integrity_package": self.integrity_package
            }
            
            response = await self.client.post(
                f"{BASE_URL}/integrity/api/v1/pgp-assurance/verify-signature",
                headers=self.headers,
                json=verify_data
            )
            
            if response.status_code == 200:
                result = response.json()
                verification_result = result["verification_result"]
                self.log_test_result(test_name, verification_result, f"Verification: {verification_result}")
                return verification_result
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {e}")
            return False
    
    async def test_merkle_tree_creation(self):
        """Test Merkle tree creation"""
        test_name = "Merkle Tree Creation"
        
        try:
            tree_data = {
                "data_list": [
                    "rule_1_privacy_protection",
                    "rule_2_data_minimization", 
                    "rule_3_consent_management",
                    "rule_4_transparency_requirements"
                ],
                "tree_id": f"test_tree_{int(time.time())}"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/integrity/api/v1/pgp-assurance/merkle-tree",
                headers=self.headers,
                json=tree_data
            )
            
            if response.status_code == 201:
                result = response.json()
                self.merkle_tree_id = result["tree_id"]
                self.merkle_root_hash = result["root_hash"]
                self.log_test_result(test_name, True, f"Tree ID: {self.merkle_tree_id}")
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {e}")
            return False
    
    async def test_merkle_root_retrieval(self):
        """Test Merkle tree root hash retrieval"""
        test_name = "Merkle Root Hash Retrieval"
        
        if not hasattr(self, 'merkle_tree_id'):
            self.log_test_result(test_name, False, "No Merkle tree available")
            return False
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/integrity/api/v1/pgp-assurance/merkle-tree/{self.merkle_tree_id}/root",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                retrieved_hash = result["root_hash"]
                matches = retrieved_hash == self.merkle_root_hash
                self.log_test_result(test_name, matches, f"Hash matches: {matches}")
                return matches
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {e}")
            return False
    
    async def test_timestamp_creation(self):
        """Test RFC 3161 timestamp creation"""
        test_name = "RFC 3161 Timestamp Creation"
        
        try:
            timestamp_data = {
                "document_hash": "test_document_hash_sha256",
                "timestamp_authority": "test_tsa"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/integrity/api/v1/pgp-assurance/timestamp",
                headers=self.headers,
                json=timestamp_data
            )
            
            if response.status_code == 201:
                result = response.json()
                self.timestamp_token = result["timestamp_token"]
                self.log_test_result(test_name, True, f"Timestamp created")
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {e}")
            return False
    
    async def test_timestamp_verification(self):
        """Test RFC 3161 timestamp verification"""
        test_name = "RFC 3161 Timestamp Verification"
        
        if not hasattr(self, 'timestamp_token'):
            self.log_test_result(test_name, False, "No timestamp token available")
            return False
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/integrity/api/v1/pgp-assurance/verify-timestamp",
                headers=self.headers,
                params={"original_document_hash": "test_document_hash_sha256"},
                json=self.timestamp_token
            )
            
            if response.status_code == 200:
                result = response.json()
                verification_result = result["verification_result"]
                self.log_test_result(test_name, verification_result, f"Verification: {verification_result}")
                return verification_result
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all Phase 3 PGP Assurance tests"""
        print("🚀 Starting Phase 3 PGP Assurance Tests")
        print("=" * 60)
        
        # Service health checks
        integrity_healthy = await self.test_integrity_service_health()
        pgp_healthy = await self.test_pgp_assurance_health()
        
        if not (integrity_healthy and pgp_healthy):
            print("\n❌ Service health checks failed. Aborting tests.")
            return False
        
        # Core PGP Assurance functionality tests
        tests = [
            self.test_key_generation,
            self.test_ac_version_signing,
            self.test_signature_verification,
            self.test_merkle_tree_creation,
            self.test_merkle_root_retrieval,
            self.test_timestamp_creation,
            self.test_timestamp_verification
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed_tests += 1
                await asyncio.sleep(0.5)  # Brief pause between tests
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        # Summary
        print(f"\n📊 Test Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All Phase 3 PGP Assurance tests passed!")
            return True
        else:
            print("💥 Some Phase 3 PGP Assurance tests failed!")
            return False


async def main():
    """Main test execution"""
    print("Phase 3 PGP Assurance Test Suite")
    print("Testing cryptographic integrity features: digital signatures, Merkle trees, key management, and timestamping")
    print()
    
    async with Phase3PGPAssuranceTestRunner() as test_runner:
        success = await test_runner.run_all_tests()
        
        if success:
            print("\n🎉 All Phase 3 PGP Assurance tests passed!")
            sys.exit(0)
        else:
            print("\n💥 Some Phase 3 PGP Assurance tests failed!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
