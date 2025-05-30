"""
PGP Assurance Service for Cryptographic Integrity
Implements digital signatures, hash functions, Merkle trees, key management, and timestamping
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# Try to import cryptography library
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, rsa, padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
    from cryptography.exceptions import InvalidSignature
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

logger = logging.getLogger(__name__)

class SignatureAlgorithm(Enum):
    """Supported signature algorithms"""
    ECDSA_P256 = "ECDSA_P256"
    RSA_PSS = "RSA_PSS"

class HashAlgorithm(Enum):
    """Supported hash algorithms"""
    SHA256 = "SHA256"
    SHA3_256 = "SHA3_256"
    SHA3_512 = "SHA3_512"

@dataclass
class DigitalSignature:
    """Digital signature data structure"""
    signature: bytes
    algorithm: SignatureAlgorithm
    public_key_pem: bytes
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class MerkleNode:
    """Merkle tree node"""
    hash_value: str
    left_child: Optional['MerkleNode'] = None
    right_child: Optional['MerkleNode'] = None
    data: Optional[str] = None

@dataclass
class TimestampToken:
    """RFC 3161 timestamp token"""
    timestamp: datetime
    hash_value: str
    authority: str
    token_data: bytes
    verification_status: bool

class PGPAssuranceService:
    """
    PGP Assurance Service providing cryptographic integrity for governance artifacts
    """
    
    def __init__(self):
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("Cryptography library not available. Some features will be disabled.")
        
        self.private_keys: Dict[str, Any] = {}
        self.public_keys: Dict[str, Any] = {}
        self.merkle_trees: Dict[str, MerkleNode] = {}
        self.signatures: Dict[str, DigitalSignature] = {}
        self.timestamps: Dict[str, TimestampToken] = {}
    
    # Digital Signatures Implementation
    
    def generate_key_pair(self, algorithm: SignatureAlgorithm = SignatureAlgorithm.ECDSA_P256) -> Tuple[bytes, bytes]:
        """Generate a new key pair for digital signatures"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        try:
            if algorithm == SignatureAlgorithm.ECDSA_P256:
                private_key = ec.generate_private_key(ec.SECP256R1())
            elif algorithm == SignatureAlgorithm.RSA_PSS:
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                )
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return private_pem, public_pem
            
        except Exception as e:
            logger.error(f"Error generating key pair: {e}")
            raise
    
    def sign_ac_version(self, ac_version_data: str, private_key_pem: bytes, 
                       algorithm: SignatureAlgorithm = SignatureAlgorithm.ECDSA_P256) -> DigitalSignature:
        """Sign an AC version with digital signature"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        try:
            # Load private key
            private_key = load_pem_private_key(private_key_pem, password=None)
            
            # Create signature
            data_bytes = ac_version_data.encode('utf-8')
            
            if algorithm == SignatureAlgorithm.ECDSA_P256:
                signature = private_key.sign(data_bytes, ec.ECDSA(hashes.SHA256()))
            elif algorithm == SignatureAlgorithm.RSA_PSS:
                signature = private_key.sign(
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            # Get public key
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Create signature object
            digital_signature = DigitalSignature(
                signature=signature,
                algorithm=algorithm,
                public_key_pem=public_pem,
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "data_hash": self.compute_hash(ac_version_data, HashAlgorithm.SHA256),
                    "data_length": len(ac_version_data)
                }
            )
            
            logger.info(f"AC version signed successfully with {algorithm.value}")
            return digital_signature
            
        except Exception as e:
            logger.error(f"Error signing AC version: {e}")
            raise
    
    def verify_signature(self, data: str, signature: DigitalSignature) -> bool:
        """Verify a digital signature"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        try:
            # Load public key
            public_key = load_pem_public_key(signature.public_key_pem)
            
            # Verify signature
            data_bytes = data.encode('utf-8')
            
            if signature.algorithm == SignatureAlgorithm.ECDSA_P256:
                public_key.verify(signature.signature, data_bytes, ec.ECDSA(hashes.SHA256()))
            elif signature.algorithm == SignatureAlgorithm.RSA_PSS:
                public_key.verify(
                    signature.signature,
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            else:
                raise ValueError(f"Unsupported algorithm: {signature.algorithm}")
            
            logger.info("Signature verification successful")
            return True
            
        except InvalidSignature:
            logger.warning("Signature verification failed")
            return False
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            raise
    
    # Hash Functions Implementation
    
    def compute_hash(self, data: str, algorithm: HashAlgorithm = HashAlgorithm.SHA3_256) -> str:
        """Compute cryptographic hash of data"""
        try:
            data_bytes = data.encode('utf-8')
            
            if algorithm == HashAlgorithm.SHA256:
                hash_obj = hashlib.sha256(data_bytes)
            elif algorithm == HashAlgorithm.SHA3_256:
                hash_obj = hashlib.sha3_256(data_bytes)
            elif algorithm == HashAlgorithm.SHA3_512:
                hash_obj = hashlib.sha3_512(data_bytes)
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"Error computing hash: {e}")
            raise
    
    def verify_integrity(self, data: str, expected_hash: str,
                        algorithm: HashAlgorithm = HashAlgorithm.SHA3_256) -> bool:
        """Verify data integrity using hash comparison"""
        try:
            computed_hash = self.compute_hash(data, algorithm)
            return computed_hash == expected_hash
        except Exception as e:
            logger.error(f"Error verifying integrity: {e}")
            return False

    # Merkle Trees Implementation

    def build_merkle_tree(self, data_list: List[str], tree_id: str) -> str:
        """Build a Merkle tree from a list of data items"""
        try:
            if not data_list:
                raise ValueError("Data list cannot be empty")

            # Create leaf nodes
            nodes = []
            for data in data_list:
                hash_value = self.compute_hash(data, HashAlgorithm.SHA3_256)
                node = MerkleNode(hash_value=hash_value, data=data)
                nodes.append(node)

            # Build tree bottom-up
            while len(nodes) > 1:
                next_level = []

                # Process pairs of nodes
                for i in range(0, len(nodes), 2):
                    left = nodes[i]
                    right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]  # Duplicate if odd

                    # Combine hashes
                    combined_data = left.hash_value + right.hash_value
                    combined_hash = self.compute_hash(combined_data, HashAlgorithm.SHA3_256)

                    parent = MerkleNode(
                        hash_value=combined_hash,
                        left_child=left,
                        right_child=right if right != left else None
                    )
                    next_level.append(parent)

                nodes = next_level

            # Store the tree
            root = nodes[0]
            self.merkle_trees[tree_id] = root

            logger.info(f"Merkle tree built successfully: {tree_id}")
            return root.hash_value

        except Exception as e:
            logger.error(f"Error building Merkle tree: {e}")
            raise

    def verify_merkle_proof(self, tree_id: str, data: str, proof_path: List[Tuple[str, str]]) -> bool:
        """Verify a Merkle proof for data inclusion"""
        try:
            if tree_id not in self.merkle_trees:
                raise ValueError(f"Merkle tree not found: {tree_id}")

            # Start with data hash
            current_hash = self.compute_hash(data, HashAlgorithm.SHA3_256)

            # Follow proof path
            for sibling_hash, position in proof_path:
                if position == "left":
                    combined_data = sibling_hash + current_hash
                else:  # position == "right"
                    combined_data = current_hash + sibling_hash

                current_hash = self.compute_hash(combined_data, HashAlgorithm.SHA3_256)

            # Compare with root hash
            root_hash = self.merkle_trees[tree_id].hash_value
            return current_hash == root_hash

        except Exception as e:
            logger.error(f"Error verifying Merkle proof: {e}")
            return False

    def get_merkle_root(self, tree_id: str) -> Optional[str]:
        """Get the root hash of a Merkle tree"""
        if tree_id in self.merkle_trees:
            return self.merkle_trees[tree_id].hash_value
        return None

    # Key Management Implementation

    def store_key_pair(self, key_id: str, private_key_pem: bytes, public_key_pem: bytes):
        """Store a key pair securely (in production, use HSM)"""
        try:
            # In production, private keys should be stored in HSM
            self.private_keys[key_id] = private_key_pem
            self.public_keys[key_id] = public_key_pem

            logger.info(f"Key pair stored: {key_id}")

        except Exception as e:
            logger.error(f"Error storing key pair: {e}")
            raise

    def get_public_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve a public key"""
        return self.public_keys.get(key_id)

    def get_private_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve a private key (HSM integration point)"""
        # In production, this should interface with HSM
        return self.private_keys.get(key_id)

    def rotate_keys(self, key_id: str, algorithm: SignatureAlgorithm = SignatureAlgorithm.ECDSA_P256):
        """Rotate keys for enhanced security"""
        try:
            # Generate new key pair
            private_pem, public_pem = self.generate_key_pair(algorithm)

            # Archive old keys (in production, follow key archival procedures)
            old_key_id = f"{key_id}_archived_{int(time.time())}"
            if key_id in self.private_keys:
                self.private_keys[old_key_id] = self.private_keys[key_id]
                self.public_keys[old_key_id] = self.public_keys[key_id]

            # Store new keys
            self.store_key_pair(key_id, private_pem, public_pem)

            logger.info(f"Keys rotated successfully: {key_id}")

        except Exception as e:
            logger.error(f"Error rotating keys: {e}")
            raise

    # RFC 3161 Timestamping Implementation

    def create_timestamp(self, document_hash: str, timestamp_authority: str = "trusted_tsa") -> TimestampToken:
        """Create an RFC 3161 compliant timestamp token"""
        try:
            # In production, this would make an actual RFC 3161 request to a TSA
            # For now, we create a mock timestamp token

            timestamp = datetime.now(timezone.utc)

            # Create timestamp token data (simplified)
            token_data = {
                "version": 1,
                "policy": "1.2.3.4.5",  # TSA policy OID
                "messageImprint": {
                    "hashAlgorithm": "sha256",
                    "hashedMessage": document_hash
                },
                "serialNumber": int(time.time() * 1000000),  # Unique serial number
                "genTime": timestamp.isoformat(),
                "tsa": timestamp_authority,
                "accuracy": {"seconds": 1}  # Timestamp accuracy
            }

            # In production, this would be the actual ASN.1 encoded timestamp token
            token_bytes = json.dumps(token_data).encode('utf-8')

            timestamp_token = TimestampToken(
                timestamp=timestamp,
                hash_value=document_hash,
                authority=timestamp_authority,
                token_data=token_bytes,
                verification_status=True
            )

            # Store timestamp
            token_id = f"ts_{int(time.time() * 1000000)}"
            self.timestamps[token_id] = timestamp_token

            logger.info(f"Timestamp created: {token_id}")
            return timestamp_token

        except Exception as e:
            logger.error(f"Error creating timestamp: {e}")
            raise

    def verify_timestamp(self, timestamp_token: TimestampToken, original_document_hash: str) -> bool:
        """Verify an RFC 3161 timestamp token"""
        try:
            # Parse token data
            token_data = json.loads(timestamp_token.token_data.decode('utf-8'))

            # Verify hash matches
            if token_data["messageImprint"]["hashedMessage"] != original_document_hash:
                logger.warning("Timestamp hash mismatch")
                return False

            # Verify timestamp is reasonable (not in future, not too old)
            now = datetime.now(timezone.utc)
            if timestamp_token.timestamp > now:
                logger.warning("Timestamp is in the future")
                return False

            # Check if timestamp is too old (configurable threshold)
            max_age_days = 365 * 10  # 10 years
            if (now - timestamp_token.timestamp).days > max_age_days:
                logger.warning("Timestamp is too old")
                return False

            # In production, verify TSA signature and certificate chain
            # For now, we trust the verification_status from creation

            logger.info("Timestamp verification successful")
            return timestamp_token.verification_status

        except Exception as e:
            logger.error(f"Error verifying timestamp: {e}")
            return False

    def get_timestamp_info(self, timestamp_token: TimestampToken) -> Dict[str, Any]:
        """Get detailed information about a timestamp token"""
        try:
            token_data = json.loads(timestamp_token.token_data.decode('utf-8'))

            return {
                "timestamp": timestamp_token.timestamp.isoformat(),
                "authority": timestamp_token.authority,
                "hash_value": timestamp_token.hash_value,
                "serial_number": token_data.get("serialNumber"),
                "policy": token_data.get("policy"),
                "accuracy": token_data.get("accuracy"),
                "verification_status": timestamp_token.verification_status
            }

        except Exception as e:
            logger.error(f"Error getting timestamp info: {e}")
            return {}

    # Comprehensive Integrity Verification

    def create_integrity_package(self, data: str, key_id: str, include_timestamp: bool = True) -> Dict[str, Any]:
        """Create a comprehensive integrity package with signature, hash, and timestamp"""
        try:
            # Compute hash
            data_hash = self.compute_hash(data, HashAlgorithm.SHA3_256)

            # Create digital signature
            private_key = self.get_private_key(key_id)
            if not private_key:
                raise ValueError(f"Private key not found: {key_id}")

            signature = self.sign_ac_version(data, private_key)

            # Create timestamp if requested
            timestamp_token = None
            if include_timestamp:
                timestamp_token = self.create_timestamp(data_hash)

            # Create integrity package
            package = {
                "data_hash": data_hash,
                "hash_algorithm": HashAlgorithm.SHA3_256.value,
                "signature": {
                    "algorithm": signature.algorithm.value,
                    "signature_bytes": signature.signature.hex(),
                    "public_key_pem": signature.public_key_pem.decode('utf-8'),
                    "timestamp": signature.timestamp.isoformat(),
                    "metadata": signature.metadata
                },
                "timestamp": self.get_timestamp_info(timestamp_token) if timestamp_token else None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "key_id": key_id
            }

            logger.info("Integrity package created successfully")
            return package

        except Exception as e:
            logger.error(f"Error creating integrity package: {e}")
            raise

    def verify_integrity_package(self, data: str, package: Dict[str, Any]) -> bool:
        """Verify a comprehensive integrity package"""
        try:
            # Verify hash
            expected_hash = package["data_hash"]
            hash_algorithm = HashAlgorithm(package["hash_algorithm"])
            if not self.verify_integrity(data, expected_hash, hash_algorithm):
                logger.warning("Hash verification failed")
                return False

            # Verify signature
            signature_data = package["signature"]
            signature = DigitalSignature(
                signature=bytes.fromhex(signature_data["signature_bytes"]),
                algorithm=SignatureAlgorithm(signature_data["algorithm"]),
                public_key_pem=signature_data["public_key_pem"].encode('utf-8'),
                timestamp=datetime.fromisoformat(signature_data["timestamp"]),
                metadata=signature_data["metadata"]
            )

            if not self.verify_signature(data, signature):
                logger.warning("Signature verification failed")
                return False

            # Verify timestamp if present
            if package.get("timestamp"):
                timestamp_info = package["timestamp"]
                timestamp_token = TimestampToken(
                    timestamp=datetime.fromisoformat(timestamp_info["timestamp"]),
                    hash_value=timestamp_info["hash_value"],
                    authority=timestamp_info["authority"],
                    token_data=json.dumps({
                        "serialNumber": timestamp_info["serial_number"],
                        "policy": timestamp_info["policy"],
                        "messageImprint": {
                            "hashAlgorithm": "sha256",
                            "hashedMessage": timestamp_info["hash_value"]
                        },
                        "genTime": timestamp_info["timestamp"],
                        "tsa": timestamp_info["authority"],
                        "accuracy": timestamp_info["accuracy"]
                    }).encode('utf-8'),
                    verification_status=timestamp_info["verification_status"]
                )

                if not self.verify_timestamp(timestamp_token, expected_hash):
                    logger.warning("Timestamp verification failed")
                    return False

            logger.info("Integrity package verification successful")
            return True

        except Exception as e:
            logger.error(f"Error verifying integrity package: {e}")
            return False
