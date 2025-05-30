"""
Cryptographic Integrity Service for ACGS-PGP Framework
Implements digital signatures, hash functions, Merkle trees, and RFC 3161 timestamping
"""

import hashlib
import json
import secrets
import base64
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
import logging

# Cryptography library imports
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("Cryptography library not available. Cryptographic operations will be disabled.")

logger = logging.getLogger(__name__)


class CryptographicIntegrityService:
    """
    Comprehensive cryptographic service for ACGS-PGP integrity assurance
    """
    
    def __init__(self):
        self.hash_algorithm = hashes.SHA3_256()
        self.signature_algorithm = "RSA-PSS-SHA256"
        
    def generate_sha3_hash(self, data: str) -> str:
        """
        Generate SHA3-256 hash of the input data
        
        Args:
            data: String data to hash
            
        Returns:
            Hexadecimal hash string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        digest = hashlib.sha3_256(data).hexdigest()
        logger.debug(f"Generated SHA3-256 hash: {digest[:16]}...")
        return digest
    
    def generate_content_hash(self, content: Dict[str, Any]) -> str:
        """
        Generate deterministic hash of structured content
        
        Args:
            content: Dictionary content to hash
            
        Returns:
            SHA3-256 hash of the content
        """
        # Create deterministic JSON representation
        json_str = json.dumps(content, sort_keys=True, separators=(',', ':'))
        return self.generate_sha3_hash(json_str)
    
    def generate_key_pair(self, key_size: int = 2048) -> Tuple[str, str, str]:
        """
        Generate RSA key pair for digital signatures
        
        Args:
            key_size: RSA key size in bits (default: 2048)
            
        Returns:
            Tuple of (key_id, private_key_pem, public_key_pem)
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize keys to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Generate key ID from public key hash
        key_id = self.generate_sha3_hash(public_pem)[:32]  # First 32 chars
        
        logger.info(f"Generated RSA key pair: {key_id}")
        return key_id, private_pem, public_pem
    
    def sign_data(self, data: str, private_key_pem: str) -> bytes:
        """
        Create digital signature of data using RSA-PSS
        
        Args:
            data: Data to sign
            private_key_pem: PEM-encoded private key
            
        Returns:
            Digital signature bytes
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        
        # Sign data
        signature = private_key.sign(
            data.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        logger.debug(f"Created signature for data: {data[:50]}...")
        return signature
    
    def verify_signature(self, data: str, signature: bytes, public_key_pem: str) -> bool:
        """
        Verify digital signature using RSA-PSS
        
        Args:
            data: Original data
            signature: Digital signature bytes
            public_key_pem: PEM-encoded public key
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            return False
        
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Verify signature
            public_key.verify(
                signature,
                data.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            logger.debug("Signature verification successful")
            return True
            
        except InvalidSignature:
            logger.warning("Signature verification failed")
            return False
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False


class MerkleTreeService:
    """
    Merkle Tree implementation for batch integrity verification
    """
    
    def __init__(self):
        self.crypto_service = CryptographicIntegrityService()
    
    def build_merkle_tree(self, data_hashes: List[str]) -> Dict[str, Any]:
        """
        Build Merkle tree from list of data hashes
        
        Args:
            data_hashes: List of SHA3-256 hashes
            
        Returns:
            Dictionary containing tree structure and root hash
        """
        if not data_hashes:
            return {"root_hash": "", "tree_levels": [], "leaf_count": 0}
        
        # Ensure even number of leaves (pad with last hash if odd)
        if len(data_hashes) % 2 == 1:
            data_hashes.append(data_hashes[-1])
        
        tree_levels = [data_hashes]  # Level 0: leaf nodes
        current_level = data_hashes
        
        # Build tree bottom-up
        while len(current_level) > 1:
            next_level = []
            
            # Process pairs of nodes
            for i in range(0, len(current_level), 2):
                left_hash = current_level[i]
                right_hash = current_level[i + 1] if i + 1 < len(current_level) else left_hash
                
                # Combine hashes
                combined = left_hash + right_hash
                parent_hash = self.crypto_service.generate_sha3_hash(combined)
                next_level.append(parent_hash)
            
            tree_levels.append(next_level)
            current_level = next_level
        
        root_hash = current_level[0] if current_level else ""
        
        logger.info(f"Built Merkle tree with root: {root_hash[:16]}... ({len(data_hashes)} leaves)")
        
        return {
            "root_hash": root_hash,
            "tree_levels": tree_levels,
            "leaf_count": len(data_hashes)
        }
    
    def generate_merkle_proof(self, data_hash: str, tree_levels: List[List[str]]) -> List[Dict[str, str]]:
        """
        Generate Merkle proof for a specific data hash
        
        Args:
            data_hash: Hash to generate proof for
            tree_levels: Complete tree structure
            
        Returns:
            List of proof elements with hash and position
        """
        if not tree_levels or data_hash not in tree_levels[0]:
            return []
        
        proof = []
        current_index = tree_levels[0].index(data_hash)
        
        # Generate proof path from leaf to root
        for level in range(len(tree_levels) - 1):
            current_level = tree_levels[level]
            
            # Find sibling hash
            if current_index % 2 == 0:  # Left node
                sibling_index = current_index + 1
                position = "right"
            else:  # Right node
                sibling_index = current_index - 1
                position = "left"
            
            if sibling_index < len(current_level):
                sibling_hash = current_level[sibling_index]
                proof.append({
                    "hash": sibling_hash,
                    "position": position
                })
            
            # Move to parent level
            current_index = current_index // 2
        
        return proof
    
    def verify_merkle_proof(self, data_hash: str, proof: List[Dict[str, str]], root_hash: str) -> bool:
        """
        Verify Merkle proof for a data hash
        
        Args:
            data_hash: Original data hash
            proof: Merkle proof elements
            root_hash: Expected root hash
            
        Returns:
            True if proof is valid, False otherwise
        """
        current_hash = data_hash
        
        # Reconstruct path to root
        for proof_element in proof:
            sibling_hash = proof_element["hash"]
            position = proof_element["position"]
            
            if position == "left":
                combined = sibling_hash + current_hash
            else:
                combined = current_hash + sibling_hash
            
            current_hash = self.crypto_service.generate_sha3_hash(combined)
        
        is_valid = current_hash == root_hash
        logger.debug(f"Merkle proof verification: {'valid' if is_valid else 'invalid'}")
        return is_valid


# Global service instances
crypto_service = CryptographicIntegrityService()
merkle_service = MerkleTreeService()
