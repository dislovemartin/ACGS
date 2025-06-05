"""
Comprehensive Integrity Verification Service for ACGS-PGP Framework
Orchestrates digital signatures, Merkle trees, timestamps, and chain integrity
"""

import json
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models import PolicyRule, AuditLog, CryptoKey, MerkleTreeNode, TimestampToken
from .crypto_service import crypto_service, merkle_service
from .key_management import key_manager
from .timestamp_service import timestamp_manager

logger = logging.getLogger(__name__)


class IntegrityVerificationService:
    """
    Comprehensive integrity verification orchestrator
    """
    
    def __init__(self):
        self.crypto_service = crypto_service
        self.merkle_service = merkle_service
        self.key_manager = key_manager
        self.timestamp_manager = timestamp_manager
    
    async def sign_policy_rule(self, db: AsyncSession, rule_id: int) -> Dict[str, Any]:
        """
        Sign a policy rule with digital signature and timestamp
        
        Args:
            db: Database session
            rule_id: Policy rule ID
            
        Returns:
            Signature and timestamp information
        """
        try:
            # Get policy rule
            stmt = select(PolicyRule).where(PolicyRule.id == rule_id)
            result = await db.execute(stmt)
            policy_rule = result.scalar_one_or_none()
            
            if not policy_rule:
                raise ValueError(f"Policy rule {rule_id} not found")
            
            # Create content for signing
            content_data = {
                "rule_content": policy_rule.rule_content,
                "version": policy_rule.version,
                "source_principle_ids": policy_rule.source_principle_ids,
                "verification_status": policy_rule.verification_status
            }
            content_json = json.dumps(content_data, sort_keys=True, separators=(',', ':'))
            
            # Generate content hash
            content_hash = self.crypto_service.generate_sha3_hash(content_json)
            
            # Get signing key
            key_info = await self.key_manager.get_active_signing_key(db=db, purpose="signing")
            if not key_info:
                raise RuntimeError("No active signing key available")
            
            # Create digital signature
            signature_bytes = self.crypto_service.sign_data(
                data=content_json,
                private_key_pem=key_info["private_key_pem"]
            )
            
            # Create timestamp
            timestamp_result = self.timestamp_manager.timestamp_data(content_json)
            
            # Update policy rule with cryptographic data
            policy_rule.content_hash = content_hash
            policy_rule.digital_signature = signature_bytes
            policy_rule.signature_algorithm = "RSA-PSS-SHA256"
            policy_rule.signed_by_key_id = key_info["key_id"]
            policy_rule.signed_at = datetime.now(timezone.utc)
            policy_rule.signature_verified = True
            
            if timestamp_result:
                policy_rule.rfc3161_timestamp = timestamp_result["timestamp_token"]
            
            await db.commit()
            
            logger.info(f"Signed policy rule {rule_id} with key {key_info['key_id']}")
            
            return {
                "rule_id": rule_id,
                "content_hash": content_hash,
                "signature": base64.b64encode(signature_bytes).decode('utf-8'),
                "key_id": key_info["key_id"],
                "signed_at": policy_rule.signed_at,
                "timestamp_token": base64.b64encode(timestamp_result["timestamp_token"]).decode('utf-8') if timestamp_result else None
            }
            
        except Exception as e:
            logger.error(f"Error signing policy rule {rule_id}: {e}")
            await db.rollback()
            raise
    
    async def sign_audit_log(self, db: AsyncSession, log_id: int) -> Dict[str, Any]:
        """
        Sign an audit log entry with digital signature, timestamp, and chain integrity
        
        Args:
            db: Database session
            log_id: Audit log ID
            
        Returns:
            Signature and integrity information
        """
        try:
            # Get audit log
            stmt = select(AuditLog).where(AuditLog.id == log_id)
            result = await db.execute(stmt)
            audit_log = result.scalar_one_or_none()
            
            if not audit_log:
                raise ValueError(f"Audit log {log_id} not found")
            
            # Create content for signing
            content_data = {
                "timestamp": audit_log.timestamp.isoformat(),
                "service_name": audit_log.service_name,
                "user_id": audit_log.user_id,
                "action": audit_log.action,
                "details": audit_log.details
            }
            content_json = json.dumps(content_data, sort_keys=True, separators=(',', ':'))
            
            # Generate entry hash
            entry_hash = self.crypto_service.generate_sha3_hash(content_json)
            
            # Get previous log entry hash for chain integrity
            previous_hash = await self._get_previous_log_hash(db, log_id)
            
            # Create chained content (current + previous hash)
            chained_content = content_json + (previous_hash or "")
            chained_hash = self.crypto_service.generate_sha3_hash(chained_content)
            
            # Get signing key
            key_info = await self.key_manager.get_active_signing_key(db=db, purpose="signing")
            if not key_info:
                raise RuntimeError("No active signing key available")
            
            # Create digital signature
            signature_bytes = self.crypto_service.sign_data(
                data=chained_content,
                private_key_pem=key_info["private_key_pem"]
            )
            
            # Create timestamp
            timestamp_result = self.timestamp_manager.timestamp_audit_log(content_data)
            
            # Update audit log with cryptographic data
            audit_log.entry_hash = entry_hash
            audit_log.digital_signature = signature_bytes
            audit_log.signature_algorithm = "RSA-PSS-SHA256"
            audit_log.signed_by_key_id = key_info["key_id"]
            audit_log.signed_at = datetime.now(timezone.utc)
            audit_log.signature_verified = True
            audit_log.previous_hash = previous_hash
            
            if timestamp_result:
                audit_log.rfc3161_timestamp = timestamp_result["timestamp_token"]
            
            await db.commit()
            
            logger.info(f"Signed audit log {log_id} with key {key_info['key_id']}")
            
            return {
                "log_id": log_id,
                "entry_hash": entry_hash,
                "chained_hash": chained_hash,
                "signature": base64.b64encode(signature_bytes).decode('utf-8'),
                "key_id": key_info["key_id"],
                "signed_at": audit_log.signed_at,
                "previous_hash": previous_hash,
                "timestamp_token": base64.b64encode(timestamp_result["timestamp_token"]).decode('utf-8') if timestamp_result else None
            }
            
        except Exception as e:
            logger.error(f"Error signing audit log {log_id}: {e}")
            await db.rollback()
            raise
    
    async def verify_policy_rule_integrity(self, db: AsyncSession, rule_id: int) -> Dict[str, Any]:
        """
        Verify complete integrity of a policy rule
        
        Args:
            db: Database session
            rule_id: Policy rule ID
            
        Returns:
            Comprehensive integrity verification results
        """
        try:
            # Get policy rule
            stmt = select(PolicyRule).where(PolicyRule.id == rule_id)
            result = await db.execute(stmt)
            policy_rule = result.scalar_one_or_none()
            
            if not policy_rule:
                raise ValueError(f"Policy rule {rule_id} not found")
            
            verification_results = {
                "rule_id": rule_id,
                "content_hash_verified": False,
                "signature_verified": False,
                "timestamp_verified": False,
                "overall_integrity": False,
                "verification_details": {}
            }
            
            # Verify content hash
            content_data = {
                "rule_content": policy_rule.rule_content,
                "version": policy_rule.version,
                "source_principle_ids": policy_rule.source_principle_ids,
                "verification_status": policy_rule.verification_status
            }
            content_json = json.dumps(content_data, sort_keys=True, separators=(',', ':'))
            computed_hash = self.crypto_service.generate_sha3_hash(content_json)
            
            verification_results["content_hash_verified"] = (computed_hash == policy_rule.content_hash)
            verification_results["verification_details"]["computed_hash"] = computed_hash
            verification_results["verification_details"]["stored_hash"] = policy_rule.content_hash
            
            # Verify digital signature
            if policy_rule.digital_signature and policy_rule.signed_by_key_id:
                public_key_pem = await self.key_manager.get_public_key(db=db, key_id=policy_rule.signed_by_key_id)
                if public_key_pem:
                    signature_valid = self.crypto_service.verify_signature(
                        data=content_json,
                        signature=policy_rule.digital_signature,
                        public_key_pem=public_key_pem
                    )
                    verification_results["signature_verified"] = signature_valid
                    verification_results["verification_details"]["signature_key_id"] = policy_rule.signed_by_key_id
                else:
                    verification_results["verification_details"]["signature_error"] = "Signing key not found"
            
            # Verify timestamp
            if policy_rule.rfc3161_timestamp:
                timestamp_valid = self.timestamp_manager.verify_timestamp(
                    timestamp_token=policy_rule.rfc3161_timestamp,
                    original_data=content_json
                )
                verification_results["timestamp_verified"] = timestamp_valid
            
            # Overall integrity
            verification_results["overall_integrity"] = (
                verification_results["content_hash_verified"] and
                verification_results["signature_verified"] and
                verification_results["timestamp_verified"]
            )
            
            verification_results["verified_at"] = datetime.now(timezone.utc)
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Error verifying policy rule {rule_id}: {e}")
            raise
    
    async def verify_audit_log_integrity(self, db: AsyncSession, log_id: int) -> Dict[str, Any]:
        """
        Verify complete integrity of an audit log entry including chain integrity
        
        Args:
            db: Database session
            log_id: Audit log ID
            
        Returns:
            Comprehensive integrity verification results
        """
        try:
            # Get audit log
            stmt = select(AuditLog).where(AuditLog.id == log_id)
            result = await db.execute(stmt)
            audit_log = result.scalar_one_or_none()
            
            if not audit_log:
                raise ValueError(f"Audit log {log_id} not found")
            
            verification_results = {
                "log_id": log_id,
                "entry_hash_verified": False,
                "signature_verified": False,
                "timestamp_verified": False,
                "chain_integrity": False,
                "overall_integrity": False,
                "verification_details": {}
            }
            
            # Verify entry hash
            content_data = {
                "timestamp": audit_log.timestamp.isoformat(),
                "service_name": audit_log.service_name,
                "user_id": audit_log.user_id,
                "action": audit_log.action,
                "details": audit_log.details
            }
            content_json = json.dumps(content_data, sort_keys=True, separators=(',', ':'))
            computed_hash = self.crypto_service.generate_sha3_hash(content_json)
            
            verification_results["entry_hash_verified"] = (computed_hash == audit_log.entry_hash)
            verification_results["verification_details"]["computed_hash"] = computed_hash
            verification_results["verification_details"]["stored_hash"] = audit_log.entry_hash
            
            # Verify chain integrity
            expected_previous_hash = await self._get_previous_log_hash(db, log_id)
            chain_integrity_valid = (expected_previous_hash == audit_log.previous_hash)
            verification_results["chain_integrity"] = chain_integrity_valid
            verification_results["verification_details"]["expected_previous_hash"] = expected_previous_hash
            verification_results["verification_details"]["stored_previous_hash"] = audit_log.previous_hash
            
            # Verify digital signature (with chain)
            if audit_log.digital_signature and audit_log.signed_by_key_id:
                chained_content = content_json + (audit_log.previous_hash or "")
                public_key_pem = await self.key_manager.get_public_key(db=db, key_id=audit_log.signed_by_key_id)
                if public_key_pem:
                    signature_valid = self.crypto_service.verify_signature(
                        data=chained_content,
                        signature=audit_log.digital_signature,
                        public_key_pem=public_key_pem
                    )
                    verification_results["signature_verified"] = signature_valid
                    verification_results["verification_details"]["signature_key_id"] = audit_log.signed_by_key_id
                else:
                    verification_results["verification_details"]["signature_error"] = "Signing key not found"
            
            # Verify timestamp
            if audit_log.rfc3161_timestamp:
                timestamp_valid = self.timestamp_manager.verify_timestamp(
                    timestamp_token=audit_log.rfc3161_timestamp,
                    original_data=content_json
                )
                verification_results["timestamp_verified"] = timestamp_valid
            
            # Overall integrity
            verification_results["overall_integrity"] = (
                verification_results["entry_hash_verified"] and
                verification_results["signature_verified"] and
                verification_results["timestamp_verified"] and
                verification_results["chain_integrity"]
            )
            
            verification_results["verified_at"] = datetime.now(timezone.utc)
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Error verifying audit log {log_id}: {e}")
            raise
    
    async def _get_previous_log_hash(self, db: AsyncSession, current_log_id: int) -> Optional[str]:
        """
        Get hash of previous audit log entry for chain integrity
        
        Args:
            db: Database session
            current_log_id: Current log ID
            
        Returns:
            Previous log entry hash or None
        """
        try:
            stmt = select(AuditLog).where(
                AuditLog.id < current_log_id
            ).order_by(AuditLog.id.desc()).limit(1)
            
            result = await db.execute(stmt)
            previous_log = result.scalar_one_or_none()
            
            return previous_log.entry_hash if previous_log else None
            
        except Exception as e:
            logger.error(f"Error getting previous log hash: {e}")
            return None


# Global integrity verification service instance
integrity_verifier = IntegrityVerificationService()
