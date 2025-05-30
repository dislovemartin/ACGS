"""
Comprehensive Test Suite for Phase 3 Cryptographic Integrity (PGP Assurance)
Tests digital signatures, key management, Merkle trees, and RFC 3161 timestamping
"""

import asyncio
import json
import base64
from datetime import datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import the services we're testing
from backend.integrity_service.app.services.crypto_service import crypto_service, merkle_service
from backend.integrity_service.app.services.key_management import key_manager
from backend.integrity_service.app.services.timestamp_service import timestamp_manager
from backend.integrity_service.app.services.integrity_verification import integrity_verifier
from backend.integrity_service.app.models import PolicyRule, AuditLog, CryptoKey


class TestCryptographicIntegrityPhase3:
    """Test suite for Phase 3 cryptographic integrity features"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_data = {
            "policy_rule_content": "allow(user, action, resource) :- role(user, admin), action = read.",
            "audit_log_data": {
                "service_name": "test_service",
                "action": "CREATE_POLICY",
                "user_id": "test_user_123",
                "details": {"policy_id": 1, "version": 1}
            }
        }
    
    def test_sha3_hash_generation(self):
        """Test SHA3-256 hash generation"""
        test_data = "Hello, ACGS-PGP Framework!"
        
        # Generate hash
        hash_value = crypto_service.generate_sha3_hash(test_data)
        
        # Verify hash properties
        assert len(hash_value) == 64  # SHA3-256 produces 64-character hex string
        assert all(c in '0123456789abcdef' for c in hash_value)
        
        # Verify deterministic behavior
        hash_value2 = crypto_service.generate_sha3_hash(test_data)
        assert hash_value == hash_value2
        
        print(f"✓ SHA3-256 hash generation: {hash_value[:16]}...")
    
    def test_content_hash_generation(self):
        """Test deterministic content hash generation"""
        content1 = {"rule": "allow(user, read)", "version": 1}
        content2 = {"version": 1, "rule": "allow(user, read)"}  # Different order
        
        # Generate hashes
        hash1 = crypto_service.generate_content_hash(content1)
        hash2 = crypto_service.generate_content_hash(content2)
        
        # Should be identical despite different key order
        assert hash1 == hash2
        assert len(hash1) == 64
        
        print(f"✓ Deterministic content hash: {hash1[:16]}...")
    
    def test_rsa_key_generation(self):
        """Test RSA key pair generation"""
        # Generate key pair
        key_id, private_pem, public_pem = crypto_service.generate_key_pair(2048)
        
        # Verify key properties
        assert len(key_id) == 32  # First 32 chars of SHA3 hash
        assert "-----BEGIN PRIVATE KEY-----" in private_pem
        assert "-----BEGIN PUBLIC KEY-----" in public_pem
        assert "-----END PRIVATE KEY-----" in private_pem
        assert "-----END PUBLIC KEY-----" in public_pem
        
        print(f"✓ RSA key generation: {key_id}")
    
    def test_digital_signature_creation_and_verification(self):
        """Test digital signature creation and verification"""
        # Generate key pair
        key_id, private_pem, public_pem = crypto_service.generate_key_pair(2048)
        
        # Test data
        test_data = self.test_data["policy_rule_content"]
        
        # Create signature
        signature = crypto_service.sign_data(test_data, private_pem)
        assert isinstance(signature, bytes)
        assert len(signature) > 0
        
        # Verify signature
        is_valid = crypto_service.verify_signature(test_data, signature, public_pem)
        assert is_valid
        
        # Test with wrong data
        wrong_data = "This is different data"
        is_invalid = crypto_service.verify_signature(wrong_data, signature, public_pem)
        assert not is_invalid
        
        print(f"✓ Digital signature: Created and verified successfully")
    
    def test_merkle_tree_construction(self):
        """Test Merkle tree construction and verification"""
        # Test data hashes
        data_hashes = [
            crypto_service.generate_sha3_hash(f"data_{i}") 
            for i in range(8)
        ]
        
        # Build Merkle tree
        tree_result = merkle_service.build_merkle_tree(data_hashes)
        
        # Verify tree structure
        assert "root_hash" in tree_result
        assert "tree_levels" in tree_result
        assert "leaf_count" in tree_result
        assert tree_result["leaf_count"] == 8
        assert len(tree_result["tree_levels"]) == 4  # log2(8) + 1
        assert len(tree_result["root_hash"]) == 64
        
        print(f"✓ Merkle tree: Root {tree_result['root_hash'][:16]}... (8 leaves)")
    
    def test_merkle_proof_generation_and_verification(self):
        """Test Merkle proof generation and verification"""
        # Test data
        data_hashes = [
            crypto_service.generate_sha3_hash(f"data_{i}") 
            for i in range(4)
        ]
        
        # Build tree
        tree_result = merkle_service.build_merkle_tree(data_hashes)
        
        # Generate proof for first element
        proof = merkle_service.generate_merkle_proof(
            data_hashes[0], 
            tree_result["tree_levels"]
        )
        
        # Verify proof
        is_valid = merkle_service.verify_merkle_proof(
            data_hashes[0],
            proof,
            tree_result["root_hash"]
        )
        
        assert is_valid
        assert len(proof) == 2  # For 4 elements, proof length should be 2
        
        print(f"✓ Merkle proof: Generated and verified for leaf 0")
    
    def test_timestamp_service_mock(self):
        """Test mock timestamp service"""
        test_data = "Test data for timestamping"
        
        # Create timestamp
        result = timestamp_manager.timestamp_data(test_data)
        
        assert result is not None
        assert "timestamp_token" in result
        assert "timestamp_value" in result
        assert "tsa_url" in result
        assert "original_data_hash" in result
        assert result["tsa_url"] == "mock://localhost"
        
        # Verify timestamp
        is_valid = timestamp_manager.verify_timestamp(
            result["timestamp_token"],
            test_data
        )
        assert is_valid
        
        print(f"✓ Mock timestamp: Created and verified")
    
    def test_audit_log_timestamping(self):
        """Test audit log timestamping"""
        log_entry = self.test_data["audit_log_data"]
        
        # Create timestamp for audit log
        result = timestamp_manager.timestamp_audit_log(log_entry)
        
        assert result is not None
        assert "timestamp_token" in result
        assert "timestamp_value" in result
        
        print(f"✓ Audit log timestamp: Created successfully")
    
    def test_policy_rule_timestamping(self):
        """Test policy rule timestamping"""
        rule_content = self.test_data["policy_rule_content"]
        metadata = {"version": 1, "principle_ids": [1, 2]}
        
        # Create timestamp for policy rule
        result = timestamp_manager.timestamp_policy_rule(rule_content, metadata)
        
        assert result is not None
        assert "timestamp_token" in result
        assert "timestamp_value" in result
        
        print(f"✓ Policy rule timestamp: Created successfully")
    
    def test_comprehensive_integrity_workflow(self):
        """Test complete integrity workflow"""
        # 1. Generate key pair
        key_id, private_pem, public_pem = crypto_service.generate_key_pair(2048)
        
        # 2. Create content to sign
        content = {
            "rule_content": self.test_data["policy_rule_content"],
            "version": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
        
        # 3. Generate content hash
        content_hash = crypto_service.generate_sha3_hash(content_json)
        
        # 4. Create digital signature
        signature = crypto_service.sign_data(content_json, private_pem)
        
        # 5. Create timestamp
        timestamp_result = timestamp_manager.timestamp_data(content_json)
        
        # 6. Verify all components
        # Hash verification
        computed_hash = crypto_service.generate_sha3_hash(content_json)
        assert computed_hash == content_hash
        
        # Signature verification
        signature_valid = crypto_service.verify_signature(content_json, signature, public_pem)
        assert signature_valid
        
        # Timestamp verification
        timestamp_valid = timestamp_manager.verify_timestamp(
            timestamp_result["timestamp_token"],
            content_json
        )
        assert timestamp_valid
        
        print(f"✓ Complete integrity workflow: All verifications passed")
    
    def test_chain_integrity_simulation(self):
        """Test audit log chain integrity simulation"""
        # Simulate a chain of audit log entries
        log_entries = []
        previous_hash = None
        
        for i in range(5):
            # Create log entry
            entry_data = {
                "id": i + 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service_name": "test_service",
                "action": f"ACTION_{i}",
                "user_id": "test_user",
                "details": {"sequence": i}
            }
            
            # Generate entry hash
            entry_json = json.dumps(entry_data, sort_keys=True, separators=(',', ':'))
            entry_hash = crypto_service.generate_sha3_hash(entry_json)
            
            # Create chained content (current + previous hash)
            chained_content = entry_json + (previous_hash or "")
            chained_hash = crypto_service.generate_sha3_hash(chained_content)
            
            log_entries.append({
                "entry_data": entry_data,
                "entry_hash": entry_hash,
                "chained_hash": chained_hash,
                "previous_hash": previous_hash
            })
            
            # Update previous hash for next iteration
            previous_hash = entry_hash
        
        # Verify chain integrity
        for i, entry in enumerate(log_entries):
            expected_previous = log_entries[i-1]["entry_hash"] if i > 0 else None
            assert entry["previous_hash"] == expected_previous
        
        print(f"✓ Chain integrity: Verified {len(log_entries)} linked entries")
    
    def test_batch_merkle_verification(self):
        """Test batch verification using Merkle trees"""
        # Create multiple audit log hashes
        log_hashes = []
        for i in range(16):
            log_data = {
                "id": i + 1,
                "action": f"ACTION_{i}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            log_json = json.dumps(log_data, sort_keys=True, separators=(',', ':'))
            log_hash = crypto_service.generate_sha3_hash(log_json)
            log_hashes.append(log_hash)
        
        # Build Merkle tree for batch
        tree_result = merkle_service.build_merkle_tree(log_hashes)
        
        # Verify each log can be proven to be in the batch
        valid_proofs = 0
        for i, log_hash in enumerate(log_hashes):
            proof = merkle_service.generate_merkle_proof(
                log_hash,
                tree_result["tree_levels"]
            )
            
            is_valid = merkle_service.verify_merkle_proof(
                log_hash,
                proof,
                tree_result["root_hash"]
            )
            
            if is_valid:
                valid_proofs += 1
        
        assert valid_proofs == len(log_hashes)
        print(f"✓ Batch Merkle verification: {valid_proofs}/{len(log_hashes)} proofs valid")


def run_tests():
    """Run all cryptographic integrity tests"""
    print("🔐 ACGS-PGP Phase 3: Cryptographic Integrity (PGP Assurance) Test Suite")
    print("=" * 80)
    
    test_suite = TestCryptographicIntegrityPhase3()
    test_suite.setup_method()
    
    # Run all tests
    test_methods = [
        method for method in dir(test_suite) 
        if method.startswith('test_') and callable(getattr(test_suite, method))
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            print(f"\n🧪 Running {test_method}...")
            getattr(test_suite, test_method)()
            passed += 1
        except Exception as e:
            print(f"❌ {test_method} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All cryptographic integrity tests passed!")
        print("✅ Phase 3 PGP Assurance implementation is ready for deployment")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
