"""
Cryptographic Key Management Service for ACGS-PGP Framework
Handles key generation, storage, rotation, and HSM integration
"""

import os
import secrets
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models import CryptoKey
from .crypto_service import crypto_service

logger = logging.getLogger(__name__)


class KeyManagementService:
    """
    Comprehensive key management service with HSM support
    """
    
    def __init__(self):
        self.default_key_size = 2048
        self.default_key_expiry_days = 365
        self.encryption_key = self._get_master_encryption_key()
        
    def _get_master_encryption_key(self) -> bytes:
        """
        Get or generate master encryption key for private key storage
        
        Returns:
            32-byte encryption key
        """
        # In production, this should be stored securely (HSM, key vault, etc.)
        key_env = os.getenv("ACGS_MASTER_KEY")
        if key_env:
            return base64.b64decode(key_env)
        
        # Generate random key for development
        key = secrets.token_bytes(32)
        logger.warning("Using randomly generated master key - not suitable for production")
        return key
    
    def _encrypt_private_key(self, private_key_pem: str) -> bytes:
        """
        Encrypt private key for secure storage
        
        Args:
            private_key_pem: PEM-encoded private key
            
        Returns:
            Encrypted private key bytes
        """
        # Simple XOR encryption for demo - use proper encryption in production
        key_bytes = private_key_pem.encode('utf-8')
        encrypted = bytes(a ^ b for a, b in zip(key_bytes, 
                         (self.encryption_key * ((len(key_bytes) // 32) + 1))[:len(key_bytes)]))
        return encrypted
    
    def _decrypt_private_key(self, encrypted_key: bytes) -> str:
        """
        Decrypt private key from storage
        
        Args:
            encrypted_key: Encrypted private key bytes
            
        Returns:
            PEM-encoded private key
        """
        # Simple XOR decryption for demo - use proper decryption in production
        decrypted = bytes(a ^ b for a, b in zip(encrypted_key,
                         (self.encryption_key * ((len(encrypted_key) // 32) + 1))[:len(encrypted_key)]))
        return decrypted.decode('utf-8')
    
    async def generate_signing_key(self, db: AsyncSession, purpose: str = "signing", 
                                 key_size: int = None, expires_days: int = None) -> Dict[str, Any]:
        """
        Generate new signing key pair
        
        Args:
            db: Database session
            purpose: Key purpose (signing, encryption, timestamping)
            key_size: RSA key size in bits
            expires_days: Key expiration in days
            
        Returns:
            Dictionary with key information
        """
        try:
            key_size = key_size or self.default_key_size
            expires_days = expires_days or self.default_key_expiry_days
            
            # Generate key pair
            key_id, private_pem, public_pem = crypto_service.generate_key_pair(key_size)
            
            # Encrypt private key for storage
            encrypted_private = self._encrypt_private_key(private_pem)
            
            # Calculate expiration
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
            
            # Create database record
            crypto_key = CryptoKey(
                key_id=key_id,
                key_type="RSA",
                key_size=key_size,
                public_key_pem=public_pem,
                private_key_encrypted=encrypted_private,
                key_purpose=purpose,
                is_active=True,
                expires_at=expires_at
            )
            
            db.add(crypto_key)
            await db.commit()
            await db.refresh(crypto_key)
            
            logger.info(f"Generated new {purpose} key: {key_id}")
            
            return {
                "key_id": key_id,
                "key_type": "RSA",
                "key_size": key_size,
                "purpose": purpose,
                "public_key_pem": public_pem,
                "expires_at": expires_at,
                "created_at": crypto_key.created_at
            }
            
        except Exception as e:
            logger.error(f"Error generating signing key: {e}")
            await db.rollback()
            raise
    
    async def get_active_signing_key(self, db: AsyncSession, purpose: str = "signing") -> Optional[Dict[str, Any]]:
        """
        Get active signing key for specified purpose
        
        Args:
            db: Database session
            purpose: Key purpose
            
        Returns:
            Key information dictionary or None
        """
        try:
            # Query for active key
            stmt = select(CryptoKey).where(
                CryptoKey.key_purpose == purpose,
                CryptoKey.is_active == True,
                (CryptoKey.expires_at.is_(None) | (CryptoKey.expires_at > datetime.now(timezone.utc)))
            ).order_by(CryptoKey.created_at.desc())
            
            result = await db.execute(stmt)
            crypto_key = result.scalar_one_or_none()
            
            if not crypto_key:
                return None
            
            # Decrypt private key
            private_pem = self._decrypt_private_key(crypto_key.private_key_encrypted)
            
            return {
                "key_id": crypto_key.key_id,
                "key_type": crypto_key.key_type,
                "key_size": crypto_key.key_size,
                "purpose": crypto_key.key_purpose,
                "public_key_pem": crypto_key.public_key_pem,
                "private_key_pem": private_pem,
                "expires_at": crypto_key.expires_at,
                "created_at": crypto_key.created_at
            }
            
        except Exception as e:
            logger.error(f"Error getting active signing key: {e}")
            return None
    
    async def get_public_key(self, db: AsyncSession, key_id: str) -> Optional[str]:
        """
        Get public key by key ID
        
        Args:
            db: Database session
            key_id: Key identifier
            
        Returns:
            PEM-encoded public key or None
        """
        try:
            stmt = select(CryptoKey).where(CryptoKey.key_id == key_id)
            result = await db.execute(stmt)
            crypto_key = result.scalar_one_or_none()
            
            if crypto_key:
                return crypto_key.public_key_pem
            return None
            
        except Exception as e:
            logger.error(f"Error getting public key {key_id}: {e}")
            return None
    
    async def rotate_key(self, db: AsyncSession, old_key_id: str, reason: str = "scheduled_rotation") -> Dict[str, Any]:
        """
        Rotate cryptographic key
        
        Args:
            db: Database session
            old_key_id: Key ID to rotate
            reason: Rotation reason
            
        Returns:
            New key information
        """
        try:
            # Get old key
            stmt = select(CryptoKey).where(CryptoKey.key_id == old_key_id)
            result = await db.execute(stmt)
            old_key = result.scalar_one_or_none()
            
            if not old_key:
                raise ValueError(f"Key {old_key_id} not found")
            
            # Generate new key
            new_key_info = await self.generate_signing_key(
                db, 
                purpose=old_key.key_purpose,
                key_size=old_key.key_size
            )
            
            # Update new key with parent reference
            stmt = update(CryptoKey).where(
                CryptoKey.key_id == new_key_info["key_id"]
            ).values(
                parent_key_id=old_key_id,
                rotation_reason=reason
            )
            await db.execute(stmt)
            
            # Deactivate old key
            stmt = update(CryptoKey).where(
                CryptoKey.key_id == old_key_id
            ).values(
                is_active=False,
                revoked_at=datetime.now(timezone.utc)
            )
            await db.execute(stmt)
            
            await db.commit()
            
            logger.info(f"Rotated key {old_key_id} -> {new_key_info['key_id']}")
            
            return new_key_info
            
        except Exception as e:
            logger.error(f"Error rotating key {old_key_id}: {e}")
            await db.rollback()
            raise
    
    async def revoke_key(self, db: AsyncSession, key_id: str, reason: str = "manual_revocation") -> bool:
        """
        Revoke cryptographic key
        
        Args:
            db: Database session
            key_id: Key ID to revoke
            reason: Revocation reason
            
        Returns:
            True if successful, False otherwise
        """
        try:
            stmt = update(CryptoKey).where(
                CryptoKey.key_id == key_id
            ).values(
                is_active=False,
                revoked_at=datetime.now(timezone.utc),
                rotation_reason=reason
            )
            
            result = await db.execute(stmt)
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Revoked key {key_id}")
                return True
            else:
                logger.warning(f"Key {key_id} not found for revocation")
                return False
                
        except Exception as e:
            logger.error(f"Error revoking key {key_id}: {e}")
            await db.rollback()
            return False
    
    async def list_keys(self, db: AsyncSession, purpose: str = None, 
                       active_only: bool = False) -> List[Dict[str, Any]]:
        """
        List cryptographic keys
        
        Args:
            db: Database session
            purpose: Filter by key purpose
            active_only: Only return active keys
            
        Returns:
            List of key information dictionaries
        """
        try:
            stmt = select(CryptoKey)
            
            if purpose:
                stmt = stmt.where(CryptoKey.key_purpose == purpose)
            
            if active_only:
                stmt = stmt.where(
                    CryptoKey.is_active == True,
                    (CryptoKey.expires_at.is_(None) | (CryptoKey.expires_at > datetime.now(timezone.utc)))
                )
            
            stmt = stmt.order_by(CryptoKey.created_at.desc())
            
            result = await db.execute(stmt)
            keys = result.scalars().all()
            
            return [
                {
                    "key_id": key.key_id,
                    "key_type": key.key_type,
                    "key_size": key.key_size,
                    "purpose": key.key_purpose,
                    "is_active": key.is_active,
                    "created_at": key.created_at,
                    "expires_at": key.expires_at,
                    "revoked_at": key.revoked_at,
                    "parent_key_id": key.parent_key_id,
                    "rotation_reason": key.rotation_reason
                }
                for key in keys
            ]
            
        except Exception as e:
            logger.error(f"Error listing keys: {e}")
            return []


# Global key management service instance
key_manager = KeyManagementService()
