"""
Standalone Test Suite for Phase 3 Cryptographic Integrity
Tests core cryptographic functions without database dependencies
"""

import hashlib
import json
import base64
import secrets
from datetime import datetime, timezone

# Test cryptography library availability
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature
    CRYPTOGRAPHY_AVAILABLE = True
    print("✅ Cryptography library available")
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("❌ Cryptography library not available")


class StandaloneCryptoService:
    """Standalone cryptographic service for testing"""
    
    def __init__(self):
        self.hash_algorithm = hashes.SHA3_256()
        
    def generate_sha3_hash(self, data: str) -> str:
        """Generate SHA3-256 hash"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha3_256(data).hexdigest()
    
    def generate_content_hash(self, content: dict) -> str:
        """Generate deterministic hash of structured content"""
        json_str = json.dumps(content, sort_keys=True, separators=(',', ':'))
        return self.generate_sha3_hash(json_str)
    
    def generate_key_pair(self, key_size: int = 2048):
        """Generate RSA key pair"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        public_key = private_key.public_key()
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        key_id = self.generate_sha3_hash(public_pem)[:32]
        
        return key_id, private_pem, public_pem
    
    def sign_data(self, data: str, private_key_pem: str) -> bytes:
        """Create digital signature"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        
        signature = private_key.sign(
            data.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature
    
    def verify_signature(self, data: str, signature: bytes, public_key_pem: str) -> bool:
        """Verify digital signature"""
        if not CRYPTOGRAPHY_AVAILABLE:
            return False
        
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            public_key.verify(
                signature,
                data.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except InvalidSignature:
            return False
        except Exception:
            return False


class StandaloneMerkleService:
    """Standalone Merkle tree service for testing"""
    
    def __init__(self):
        self.crypto_service = StandaloneCryptoService()
    
    def build_merkle_tree(self, data_hashes: list) -> dict:
        """Build Merkle tree from list of data hashes"""
        if not data_hashes:
            return {"root_hash": "", "tree_levels": [], "leaf_count": 0}
        
        if len(data_hashes) % 2 == 1:
            data_hashes.append(data_hashes[-1])
        
        tree_levels = [data_hashes]
        current_level = data_hashes
        
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left_hash = current_level[i]
                right_hash = current_level[i + 1] if i + 1 < len(current_level) else left_hash
                
                combined = left_hash + right_hash
                parent_hash = self.crypto_service.generate_sha3_hash(combined)
                next_level.append(parent_hash)
            
            tree_levels.append(next_level)
            current_level = next_level
        
        root_hash = current_level[0] if current_level else ""
        
        return {
            "root_hash": root_hash,
            "tree_levels": tree_levels,
            "leaf_count": len(data_hashes)
        }
    
    def generate_merkle_proof(self, data_hash: str, tree_levels: list) -> list:
        """Generate Merkle proof for a specific data hash"""
        if not tree_levels or data_hash not in tree_levels[0]:
            return []
        
        proof = []
        current_index = tree_levels[0].index(data_hash)
        
        for level in range(len(tree_levels) - 1):
            current_level = tree_levels[level]
            
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                position = "right"
            else:
                sibling_index = current_index - 1
                position = "left"
            
            if sibling_index < len(current_level):
                sibling_hash = current_level[sibling_index]
                proof.append({
                    "hash": sibling_hash,
                    "position": position
                })
            
            current_index = current_index // 2
        
        return proof
    
    def verify_merkle_proof(self, data_hash: str, proof: list, root_hash: str) -> bool:
        """Verify Merkle proof for a data hash"""
        current_hash = data_hash
        
        for proof_element in proof:
            sibling_hash = proof_element["hash"]
            position = proof_element["position"]
            
            if position == "left":
                combined = sibling_hash + current_hash
            else:
                combined = current_hash + sibling_hash
            
            current_hash = self.crypto_service.generate_sha3_hash(combined)
        
        return current_hash == root_hash


def test_sha3_hash_generation():
    """Test SHA3-256 hash generation"""
    crypto_service = StandaloneCryptoService()
    test_data = "Hello, ACGS-PGP Framework!"
    
    hash_value = crypto_service.generate_sha3_hash(test_data)
    
    assert len(hash_value) == 64
    assert all(c in '0123456789abcdef' for c in hash_value)
    
    hash_value2 = crypto_service.generate_sha3_hash(test_data)
    assert hash_value == hash_value2
    
    print(f"✓ SHA3-256 hash generation: {hash_value[:16]}...")


def test_content_hash_generation():
    """Test deterministic content hash generation"""
    crypto_service = StandaloneCryptoService()
    content1 = {"rule": "allow(user, read)", "version": 1}
    content2 = {"version": 1, "rule": "allow(user, read)"}
    
    hash1 = crypto_service.generate_content_hash(content1)
    hash2 = crypto_service.generate_content_hash(content2)
    
    assert hash1 == hash2
    assert len(hash1) == 64
    
    print(f"✓ Deterministic content hash: {hash1[:16]}...")


def test_rsa_key_generation():
    """Test RSA key pair generation"""
    if not CRYPTOGRAPHY_AVAILABLE:
        print("⚠️  Skipping RSA key generation (cryptography not available)")
        return
    
    crypto_service = StandaloneCryptoService()
    key_id, private_pem, public_pem = crypto_service.generate_key_pair(2048)
    
    assert len(key_id) == 32
    assert "-----BEGIN PRIVATE KEY-----" in private_pem
    assert "-----BEGIN PUBLIC KEY-----" in public_pem
    
    print(f"✓ RSA key generation: {key_id}")


def test_digital_signature():
    """Test digital signature creation and verification"""
    if not CRYPTOGRAPHY_AVAILABLE:
        print("⚠️  Skipping digital signature test (cryptography not available)")
        return
    
    crypto_service = StandaloneCryptoService()
    key_id, private_pem, public_pem = crypto_service.generate_key_pair(2048)
    
    test_data = "allow(user, action, resource) :- role(user, admin), action = read."
    
    signature = crypto_service.sign_data(test_data, private_pem)
    assert isinstance(signature, bytes)
    assert len(signature) > 0
    
    is_valid = crypto_service.verify_signature(test_data, signature, public_pem)
    assert is_valid
    
    wrong_data = "This is different data"
    is_invalid = crypto_service.verify_signature(wrong_data, signature, public_pem)
    assert not is_invalid
    
    print(f"✓ Digital signature: Created and verified successfully")


def test_merkle_tree_construction():
    """Test Merkle tree construction"""
    crypto_service = StandaloneCryptoService()
    merkle_service = StandaloneMerkleService()
    
    data_hashes = [
        crypto_service.generate_sha3_hash(f"data_{i}") 
        for i in range(8)
    ]
    
    tree_result = merkle_service.build_merkle_tree(data_hashes)
    
    assert "root_hash" in tree_result
    assert "tree_levels" in tree_result
    assert "leaf_count" in tree_result
    assert tree_result["leaf_count"] == 8
    assert len(tree_result["tree_levels"]) == 4
    assert len(tree_result["root_hash"]) == 64
    
    print(f"✓ Merkle tree: Root {tree_result['root_hash'][:16]}... (8 leaves)")


def test_merkle_proof():
    """Test Merkle proof generation and verification"""
    crypto_service = StandaloneCryptoService()
    merkle_service = StandaloneMerkleService()
    
    data_hashes = [
        crypto_service.generate_sha3_hash(f"data_{i}") 
        for i in range(4)
    ]
    
    tree_result = merkle_service.build_merkle_tree(data_hashes)
    
    proof = merkle_service.generate_merkle_proof(
        data_hashes[0], 
        tree_result["tree_levels"]
    )
    
    is_valid = merkle_service.verify_merkle_proof(
        data_hashes[0],
        proof,
        tree_result["root_hash"]
    )
    
    assert is_valid
    assert len(proof) == 2
    
    print(f"✓ Merkle proof: Generated and verified for leaf 0")


def test_chain_integrity():
    """Test audit log chain integrity simulation"""
    crypto_service = StandaloneCryptoService()
    
    log_entries = []
    previous_hash = None
    
    for i in range(5):
        entry_data = {
            "id": i + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "test_service",
            "action": f"ACTION_{i}",
            "user_id": "test_user",
            "details": {"sequence": i}
        }
        
        entry_json = json.dumps(entry_data, sort_keys=True, separators=(',', ':'))
        entry_hash = crypto_service.generate_sha3_hash(entry_json)
        
        chained_content = entry_json + (previous_hash or "")
        chained_hash = crypto_service.generate_sha3_hash(chained_content)
        
        log_entries.append({
            "entry_data": entry_data,
            "entry_hash": entry_hash,
            "chained_hash": chained_hash,
            "previous_hash": previous_hash
        })
        
        previous_hash = entry_hash
    
    for i, entry in enumerate(log_entries):
        expected_previous = log_entries[i-1]["entry_hash"] if i > 0 else None
        assert entry["previous_hash"] == expected_previous
    
    print(f"✓ Chain integrity: Verified {len(log_entries)} linked entries")


def run_standalone_tests():
    """Run all standalone cryptographic tests"""
    print("🔐 ACGS-PGP Phase 3: Cryptographic Integrity Standalone Tests")
    print("=" * 70)
    
    tests = [
        test_sha3_hash_generation,
        test_content_hash_generation,
        test_rsa_key_generation,
        test_digital_signature,
        test_merkle_tree_construction,
        test_merkle_proof,
        test_chain_integrity
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n🧪 Running {test.__name__}...")
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All cryptographic integrity tests passed!")
        print("✅ Phase 3 PGP Assurance core functionality verified")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_standalone_tests()
    exit(0 if success else 1)
