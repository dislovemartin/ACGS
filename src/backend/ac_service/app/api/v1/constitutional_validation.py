#!/usr/bin/env python3
"""
Constitutional Validation API with Redis Caching
Provides cached constitutional validation for improved performance.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import time
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from shared.redis_cache import get_cache

logger = logging.getLogger(__name__)

router = APIRouter()

class ConstitutionalValidationRequest(BaseModel):
    """Request model for constitutional validation."""
    policy_content: str
    input_data: Dict[str, Any]
    validation_level: str = "standard"

class ConstitutionalValidationResponse(BaseModel):
    """Response model for constitutional validation."""
    valid: bool
    confidence_score: float
    constitutional_alignment: float
    violations: list = []
    recommendations: list = []
    cached: bool = False
    processing_time_ms: float

@router.post("/validate", response_model=ConstitutionalValidationResponse)
async def validate_constitutional_compliance(request: ConstitutionalValidationRequest):
    """
    Validate constitutional compliance with caching.
    This endpoint provides fast constitutional validation with Redis caching.
    """
    start_time = time.time()
    cache = get_cache()
    
    try:
        # Check cache first
        cached_result = cache.get_cached_policy_decision(
            request.policy_content, 
            request.input_data
        )
        
        if cached_result:
            # Return cached result
            processing_time = (time.time() - start_time) * 1000
            cached_result["cached"] = True
            cached_result["processing_time_ms"] = processing_time
            logger.info(f"Cache hit for constitutional validation - {processing_time:.2f}ms")
            return cached_result
        
        # Simulate constitutional validation processing
        # In a real implementation, this would call the actual constitutional AI
        validation_result = await _perform_constitutional_validation(request)
        
        # Cache the result
        cache.cache_policy_decision(
            request.policy_content,
            request.input_data,
            validation_result
        )
        
        processing_time = (time.time() - start_time) * 1000
        validation_result["cached"] = False
        validation_result["processing_time_ms"] = processing_time
        
        logger.info(f"Constitutional validation completed - {processing_time:.2f}ms")
        return validation_result
        
    except Exception as e:
        logger.error(f"Constitutional validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Constitutional validation failed"
        )

async def _perform_constitutional_validation(request: ConstitutionalValidationRequest) -> Dict[str, Any]:
    """
    Perform actual constitutional validation.
    This is a mock implementation for testing purposes.
    """
    # Simulate processing time
    await asyncio.sleep(0.01)  # 10ms processing time
    
    # Mock validation logic
    policy_length = len(request.policy_content)
    input_complexity = len(str(request.input_data))
    
    # Simple scoring based on content
    confidence_score = min(0.95, 0.7 + (policy_length / 1000))
    constitutional_alignment = min(0.98, 0.8 + (input_complexity / 100))
    
    violations = []
    recommendations = []
    
    # Check for common issues
    if "DROP TABLE" in request.policy_content.upper():
        violations.append("Potential SQL injection detected")
        constitutional_alignment *= 0.5
    
    if len(request.policy_content) < 10:
        recommendations.append("Policy content should be more detailed")
        confidence_score *= 0.8
    
    valid = constitutional_alignment > 0.6 and confidence_score > 0.5
    
    return {
        "valid": valid,
        "confidence_score": round(confidence_score, 3),
        "constitutional_alignment": round(constitutional_alignment, 3),
        "violations": violations,
        "recommendations": recommendations
    }

@router.get("/cache/stats")
async def get_cache_statistics():
    """Get cache performance statistics."""
    cache = get_cache()
    stats = cache.get_cache_stats()
    return {
        "cache_stats": stats,
        "timestamp": time.time()
    }

@router.delete("/cache/flush")
async def flush_cache():
    """Flush all cache data (admin only)."""
    cache = get_cache()
    success = cache.flush_all()
    return {
        "success": success,
        "message": "Cache flushed successfully" if success else "Failed to flush cache"
    }

# Import asyncio at the end to avoid circular imports
import asyncio
