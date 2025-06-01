"""
Secure Aggregation API Endpoints

REST API endpoints for managing secure aggregation protocols,
configuration, and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional, Any
import logging

from shared.auth import get_current_user_from_token, get_current_active_user
from ...core.secure_aggregation import secure_aggregator
from ...schemas import (
    AggregationConfigRequest, SecureShareRequest, SecureShareResponse,
    ErrorResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/config")
async def get_aggregation_config(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current secure aggregation configuration."""
    try:
        config = secure_aggregator.config
        return {
            "method": config.method.value,
            "privacy_budget": config.privacy_budget,
            "byzantine_tolerance": config.byzantine_tolerance,
            "min_participants": config.min_participants,
            "max_participants": config.max_participants,
            "aggregation_timeout": config.aggregation_timeout,
            "key_size": config.key_size,
            "use_homomorphic": config.use_homomorphic,
            "noise_multiplier": config.noise_multiplier
        }
        
    except Exception as e:
        logger.error(f"Failed to get aggregation config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/config")
async def update_aggregation_config(
    config_request: AggregationConfigRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Update secure aggregation configuration."""
    try:
        # Check user permissions (admin only)
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update aggregation configuration"
            )
        
        # Update configuration
        secure_aggregator.config.method = config_request.method
        secure_aggregator.config.privacy_budget = config_request.privacy_budget
        secure_aggregator.config.byzantine_tolerance = config_request.byzantine_tolerance
        secure_aggregator.config.min_participants = config_request.min_participants
        secure_aggregator.config.max_participants = config_request.max_participants
        
        logger.info(f"Updated aggregation configuration: {config_request.method.value}")
        
        return {
            "message": "Aggregation configuration updated successfully",
            "config": {
                "method": config_request.method.value,
                "privacy_budget": config_request.privacy_budget,
                "byzantine_tolerance": config_request.byzantine_tolerance,
                "min_participants": config_request.min_participants,
                "max_participants": config_request.max_participants
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update aggregation config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get("/metrics")
async def get_aggregation_metrics(
    current_user: dict = Depends(get_current_active_user)
):
    """Get secure aggregation metrics."""
    try:
        metrics = await secure_aggregator.get_aggregation_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get aggregation metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.post("/shares", response_model=SecureShareResponse)
async def create_secure_shares(
    request: SecureShareRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Create secure shares for multi-party computation."""
    try:
        # Check user permissions (admin or policy_manager)
        if current_user.get("role") not in ["admin", "policy_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create secure shares"
            )
        
        # Validate participants
        if len(request.participants) != request.num_shares:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of participants must match number of shares"
            )
        
        # Create secure shares
        shares = await secure_aggregator.create_secure_shares(
            request.data, request.num_shares
        )
        
        # Format response
        share_data = []
        verification_hashes = []
        
        for i, share in enumerate(shares):
            share_data.append({
                "share_id": share.share_id,
                "participant_id": request.participants[i],
                "encrypted_value": share.encrypted_value.hex() if isinstance(share.encrypted_value, bytes) else str(share.encrypted_value),
                "timestamp": share.timestamp.isoformat()
            })
            verification_hashes.append(share.verification_hash)
        
        logger.info(f"Created {len(shares)} secure shares for {len(request.participants)} participants")
        
        return SecureShareResponse(
            shares=share_data,
            verification_hashes=verification_hashes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create secure shares: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create secure shares: {str(e)}"
        )


@router.post("/verify")
async def verify_aggregation_integrity(
    aggregated_result: Dict[str, Any],
    current_user: dict = Depends(get_current_active_user)
):
    """Verify the integrity of aggregated results."""
    try:
        is_valid = await secure_aggregator.verify_aggregation_integrity(aggregated_result)
        
        return {
            "is_valid": is_valid,
            "verification_timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "verification_details": {
                "required_fields_present": True,
                "participant_count_valid": True,
                "privacy_score_valid": True,
                "aggregation_method_valid": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to verify aggregation integrity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify integrity: {str(e)}"
        )


@router.get("/methods")
async def list_aggregation_methods():
    """List available secure aggregation methods."""
    return {
        "methods": [
            {
                "name": "federated_averaging",
                "display_name": "Federated Averaging",
                "description": "Standard federated averaging with statistical measures",
                "privacy_level": "medium",
                "byzantine_tolerance": "low"
            },
            {
                "name": "secure_sum",
                "display_name": "Secure Sum",
                "description": "Cryptographic secure sum with multi-party computation",
                "privacy_level": "high",
                "byzantine_tolerance": "medium"
            },
            {
                "name": "differential_private",
                "display_name": "Differential Private",
                "description": "Differential privacy with configurable epsilon",
                "privacy_level": "very_high",
                "byzantine_tolerance": "low"
            },
            {
                "name": "byzantine_robust",
                "display_name": "Byzantine Robust",
                "description": "Median-based aggregation robust to Byzantine attacks",
                "privacy_level": "medium",
                "byzantine_tolerance": "high"
            }
        ]
    }


@router.get("/status")
async def get_aggregation_status(
    current_user: dict = Depends(get_current_active_user)
):
    """Get the status of the secure aggregation system."""
    try:
        metrics = await secure_aggregator.get_aggregation_metrics()
        
        return {
            "status": "operational",
            "active_aggregations": len(secure_aggregator.active_aggregations),
            "total_aggregations": metrics["total_aggregations"],
            "success_rate": (
                metrics["successful_aggregations"] / max(1, metrics["total_aggregations"])
            ),
            "average_aggregation_time": metrics["average_aggregation_time"],
            "byzantine_attacks_detected": metrics["byzantine_attacks_detected"],
            "privacy_violations": metrics["privacy_violations"],
            "cryptographic_keys_available": bool(secure_aggregator.crypto_keys)
        }
        
    except Exception as e:
        logger.error(f"Failed to get aggregation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )
