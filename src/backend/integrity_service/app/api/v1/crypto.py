"""
Cryptographic Integrity API endpoints for ACGS-PGP Framework
Handles digital signatures, key management, Merkle trees, and timestamping
"""

import base64
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_async_db
from app.core.auth import require_internal_service, User
from app.schemas import (
    CryptoKeyCreate, CryptoKey, CryptoKeyList,
    SignatureRequest, SignatureResponse, SignatureVerification, SignatureVerificationResult,
    MerkleTreeBuild, MerkleTreeResult, MerkleProof, MerkleProofVerification, MerkleProofResult,
    TimestampRequest, TimestampResponse, TimestampVerification, TimestampVerificationResult,
    IntegrityReport
)
from app.services.crypto_service import crypto_service, merkle_service
from app.services.key_management import key_manager
from app.services.timestamp_service import timestamp_manager

router = APIRouter()


# --- Key Management Endpoints ---

@router.post("/keys", response_model=CryptoKey, status_code=status.HTTP_201_CREATED)
async def generate_crypto_key(
    key_request: CryptoKeyCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Generate new cryptographic key pair"""
    try:
        key_info = await key_manager.generate_signing_key(
            db=db,
            purpose=key_request.key_purpose,
            key_size=key_request.key_size,
            expires_days=(key_request.expires_at - datetime.now(timezone.utc)).days if key_request.expires_at else None
        )
        return key_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate key: {str(e)}")


@router.get("/keys", response_model=CryptoKeyList)
async def list_crypto_keys(
    purpose: str = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """List cryptographic keys"""
    keys = await key_manager.list_keys(db=db, purpose=purpose, active_only=active_only)
    return {"keys": keys, "total": len(keys)}


@router.get("/keys/{key_id}", response_model=CryptoKey)
async def get_crypto_key(
    key_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Get specific cryptographic key"""
    public_key = await key_manager.get_public_key(db=db, key_id=key_id)
    if not public_key:
        raise HTTPException(status_code=404, detail="Key not found")
    
    # Return key info without private key
    keys = await key_manager.list_keys(db=db, active_only=False)
    key_info = next((k for k in keys if k["key_id"] == key_id), None)
    
    if not key_info:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return key_info


@router.post("/keys/{key_id}/rotate", response_model=CryptoKey)
async def rotate_crypto_key(
    key_id: str,
    reason: str = "manual_rotation",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Rotate cryptographic key"""
    try:
        new_key_info = await key_manager.rotate_key(db=db, old_key_id=key_id, reason=reason)
        return new_key_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rotate key: {str(e)}")


@router.delete("/keys/{key_id}")
async def revoke_crypto_key(
    key_id: str,
    reason: str = "manual_revocation",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Revoke cryptographic key"""
    success = await key_manager.revoke_key(db=db, key_id=key_id, reason=reason)
    if not success:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"message": "Key revoked successfully"}


# --- Digital Signature Endpoints ---

@router.post("/sign", response_model=SignatureResponse)
async def sign_data(
    signature_request: SignatureRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Create digital signature for data"""
    try:
        # Get signing key
        if signature_request.key_id:
            # Use specific key
            key_info = await key_manager.get_active_signing_key(db=db, purpose=signature_request.purpose)
            if not key_info or key_info["key_id"] != signature_request.key_id:
                raise HTTPException(status_code=404, detail="Specified key not found or inactive")
        else:
            # Use active key for purpose
            key_info = await key_manager.get_active_signing_key(db=db, purpose=signature_request.purpose)
            if not key_info:
                raise HTTPException(status_code=404, detail=f"No active {signature_request.purpose} key found")
        
        # Create signature
        signature_bytes = crypto_service.sign_data(
            data=signature_request.data,
            private_key_pem=key_info["private_key_pem"]
        )
        
        # Encode signature as base64
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        
        return SignatureResponse(
            signature=signature_b64,
            key_id=key_info["key_id"],
            algorithm="RSA-PSS-SHA256",
            signed_at=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign data: {str(e)}")


@router.post("/verify", response_model=SignatureVerificationResult)
async def verify_signature(
    verification_request: SignatureVerification,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Verify digital signature"""
    try:
        # Get public key
        public_key_pem = await key_manager.get_public_key(db=db, key_id=verification_request.key_id)
        if not public_key_pem:
            raise HTTPException(status_code=404, detail="Key not found")
        
        # Decode signature
        signature_bytes = base64.b64decode(verification_request.signature)
        
        # Verify signature
        is_valid = crypto_service.verify_signature(
            data=verification_request.data,
            signature=signature_bytes,
            public_key_pem=public_key_pem
        )
        
        return SignatureVerificationResult(
            is_valid=is_valid,
            key_id=verification_request.key_id,
            verified_at=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify signature: {str(e)}")


# --- Merkle Tree Endpoints ---

@router.post("/merkle/build", response_model=MerkleTreeResult)
async def build_merkle_tree(
    tree_request: MerkleTreeBuild,
    current_user: User = Depends(require_internal_service)
):
    """Build Merkle tree from data hashes"""
    try:
        tree_result = merkle_service.build_merkle_tree(tree_request.data_hashes)
        
        return MerkleTreeResult(
            root_hash=tree_result["root_hash"],
            tree_levels=tree_result["tree_levels"],
            leaf_count=tree_result["leaf_count"],
            batch_id=tree_request.batch_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build Merkle tree: {str(e)}")


@router.post("/merkle/proof", response_model=MerkleProof)
async def generate_merkle_proof(
    proof_request: MerkleProofVerification,
    current_user: User = Depends(require_internal_service)
):
    """Generate Merkle proof for data hash"""
    try:
        # This would typically retrieve tree levels from database
        # For now, return empty proof as placeholder
        proof_elements = []
        
        return MerkleProof(
            data_hash=proof_request.data_hash,
            proof_elements=proof_elements,
            root_hash=proof_request.root_hash
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Merkle proof: {str(e)}")


@router.post("/merkle/verify", response_model=MerkleProofResult)
async def verify_merkle_proof(
    verification_request: MerkleProofVerification,
    current_user: User = Depends(require_internal_service)
):
    """Verify Merkle proof"""
    try:
        is_valid = merkle_service.verify_merkle_proof(
            data_hash=verification_request.data_hash,
            proof=verification_request.proof_elements,
            root_hash=verification_request.root_hash
        )
        
        return MerkleProofResult(
            is_valid=is_valid,
            data_hash=verification_request.data_hash,
            root_hash=verification_request.root_hash
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify Merkle proof: {str(e)}")


# --- Timestamp Endpoints ---

@router.post("/timestamp", response_model=TimestampResponse)
async def create_timestamp(
    timestamp_request: TimestampRequest,
    current_user: User = Depends(require_internal_service)
):
    """Create RFC 3161 timestamp for data"""
    try:
        result = timestamp_manager.timestamp_data(timestamp_request.data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create timestamp")
        
        return TimestampResponse(
            timestamp_token=base64.b64encode(result["timestamp_token"]).decode('utf-8'),
            timestamp_value=result["timestamp_value"],
            tsa_url=result["tsa_url"],
            hash_algorithm=result["hash_algorithm"],
            message_imprint=result["original_data_hash"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create timestamp: {str(e)}")


@router.post("/timestamp/verify", response_model=TimestampVerificationResult)
async def verify_timestamp(
    verification_request: TimestampVerification,
    current_user: User = Depends(require_internal_service)
):
    """Verify RFC 3161 timestamp"""
    try:
        timestamp_token = base64.b64decode(verification_request.timestamp_token)
        
        is_valid = timestamp_manager.verify_timestamp(
            timestamp_token=timestamp_token,
            original_data=verification_request.original_data
        )
        
        # Extract timestamp value (simplified)
        timestamp_value = timestamp_manager.timestamp_service.extract_timestamp_value(timestamp_token)
        
        return TimestampVerificationResult(
            is_valid=is_valid,
            timestamp_value=timestamp_value,
            tsa_url=timestamp_manager.timestamp_service.tsa_url
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify timestamp: {str(e)}")


# --- Hash Utility Endpoints ---

@router.post("/hash")
async def generate_hash(
    data: Dict[str, Any],
    current_user: User = Depends(require_internal_service)
):
    """Generate SHA3-256 hash of data"""
    try:
        if isinstance(data, dict) and "content" in data:
            content = data["content"]
        else:
            content = str(data)
        
        hash_value = crypto_service.generate_sha3_hash(content)
        
        return {
            "hash": hash_value,
            "algorithm": "SHA3-256",
            "generated_at": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate hash: {str(e)}")
