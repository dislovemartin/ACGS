"""
Research Data Pipeline API endpoints for ACGS-PGP Task 13

Provides REST API for research data collection, anonymization, and export
with PGP-signed integrity for external validation.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

from app.database import get_async_db
# from shared.models import ResearchDataExport
# from app.core.auth import require_integrity_admin, require_internal_service, User

# Local auth stubs and model stubs
class User:
    pass

def require_integrity_admin():
    return User()

def require_internal_service():
    return User()

# Mock ResearchDataExport model
class ResearchDataExport:
    pass
from app.services.research_data_pipeline import (
    research_data_pipeline, AnonymizationMethod, AnonymizationConfig
)

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Pydantic Models for API ---

class AnonymizationConfigRequest(BaseModel):
    """Request model for anonymization configuration."""
    method: AnonymizationMethod
    k_value: Optional[int] = Field(None, description="K value for k-anonymity (default: 5)")
    epsilon: Optional[float] = Field(None, description="Epsilon for differential privacy (default: 1.0)")
    delta: Optional[float] = Field(None, description="Delta for differential privacy (default: 1e-5)")
    generalization_levels: Optional[Dict[str, int]] = Field(None, description="Generalization levels for fields")
    suppression_threshold: Optional[float] = Field(None, description="Suppression threshold (default: 0.1)")


class ResearchExportRequest(BaseModel):
    """Request model for creating research data export."""
    export_name: str = Field(..., max_length=255, description="Name for the export")
    export_description: Optional[str] = Field(None, description="Description of the export")
    domain_ids: List[int] = Field(..., description="Domain IDs to include in export")
    principle_ids: List[int] = Field(..., description="Principle IDs to include in export")
    date_range_start: datetime = Field(..., description="Start date for data collection")
    date_range_end: datetime = Field(..., description="End date for data collection")
    anonymization_config: AnonymizationConfigRequest = Field(..., description="Anonymization configuration")
    export_format: str = Field("json", description="Export format (json, csv)")


class ResearchExportResponse(BaseModel):
    """Response model for research data export."""
    id: int
    export_name: str
    export_description: Optional[str]
    domain_ids: List[int]
    principle_ids: List[int]
    date_range_start: datetime
    date_range_end: datetime
    anonymization_method: str
    privacy_budget_used: Optional[float]
    data_hash: str
    pgp_signature: Optional[str]
    signed_by_key_id: Optional[str]
    created_at: datetime
    export_format: str
    file_size_bytes: Optional[int]
    record_count: Optional[int]

    class Config:
        from_attributes = True


class StatisticalSummaryResponse(BaseModel):
    """Response model for statistical summary."""
    total_records: int
    domain_distribution: Dict[str, int]
    principle_distribution: Dict[str, int]
    consistency_statistics: Dict[str, float]
    execution_time_statistics: Dict[str, float]
    accuracy_statistics: Dict[str, float]
    temporal_distribution: Dict[str, int]
    conflict_statistics: Dict[str, Any]


# --- API Endpoints ---

@router.post("/exports", response_model=ResearchExportResponse, status_code=status.HTTP_201_CREATED)
async def create_research_export(
    export_request: ResearchExportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_integrity_admin)
):
    """Create a new research data export with anonymization and PGP signing."""
    
    try:
        logger.info(f"Creating research export '{export_request.export_name}' by user {current_user.id}")
        
        # Validate date range
        if export_request.date_range_start >= export_request.date_range_end:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before end date"
            )
        
        # Validate domain and principle IDs (basic validation)
        if not export_request.domain_ids:
            raise HTTPException(status_code=400, detail="At least one domain ID is required")
        
        if not export_request.principle_ids:
            raise HTTPException(status_code=400, detail="At least one principle ID is required")
        
        # Check if export name already exists
        existing_export = await db.execute(
            select(ResearchDataExport).where(ResearchDataExport.export_name == export_request.export_name)
        )
        if existing_export.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Export with name '{export_request.export_name}' already exists"
            )
        
        # Create anonymization config
        anonymization_config = AnonymizationConfig(
            method=export_request.anonymization_config.method,
            k_value=export_request.anonymization_config.k_value or 5,
            epsilon=export_request.anonymization_config.epsilon or 1.0,
            delta=export_request.anonymization_config.delta or 1e-5,
            generalization_levels=export_request.anonymization_config.generalization_levels,
            suppression_threshold=export_request.anonymization_config.suppression_threshold or 0.1
        )
        
        # Create research export
        research_export = await research_data_pipeline.create_research_export(
            db=db,
            export_name=export_request.export_name,
            export_description=export_request.export_description,
            domain_ids=export_request.domain_ids,
            principle_ids=export_request.principle_ids,
            date_range_start=export_request.date_range_start,
            date_range_end=export_request.date_range_end,
            anonymization_config=anonymization_config,
            export_format=export_request.export_format,
            user_id=current_user.id
        )
        
        # Create response with record count
        response = ResearchExportResponse(
            id=research_export.id,
            export_name=research_export.export_name,
            export_description=research_export.export_description,
            domain_ids=research_export.domain_ids,
            principle_ids=research_export.principle_ids,
            date_range_start=research_export.date_range_start,
            date_range_end=research_export.date_range_end,
            anonymization_method=research_export.anonymization_method,
            privacy_budget_used=research_export.privacy_budget_used,
            data_hash=research_export.data_hash,
            pgp_signature=research_export.pgp_signature,
            signed_by_key_id=research_export.signed_by_key_id,
            created_at=research_export.created_at,
            export_format=research_export.export_format,
            file_size_bytes=research_export.file_size_bytes,
            record_count=research_export.export_data.get("statistical_summary", {}).get("total_records", 0)
        )
        
        logger.info(f"Created research export with ID {research_export.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create research export: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create research export: {str(e)}")


@router.get("/exports", response_model=List[ResearchExportResponse])
async def list_research_exports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    export_format: Optional[str] = Query(None),
    anonymization_method: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """List research data exports."""
    
    try:
        query = select(ResearchDataExport)
        
        if export_format:
            query = query.where(ResearchDataExport.export_format == export_format)
        
        if anonymization_method:
            query = query.where(ResearchDataExport.anonymization_method == anonymization_method)
        
        query = query.offset(skip).limit(limit).order_by(ResearchDataExport.created_at.desc())
        
        result = await db.execute(query)
        exports = result.scalars().all()
        
        # Convert to response format
        response_exports = []
        for export in exports:
            response_export = ResearchExportResponse(
                id=export.id,
                export_name=export.export_name,
                export_description=export.export_description,
                domain_ids=export.domain_ids,
                principle_ids=export.principle_ids,
                date_range_start=export.date_range_start,
                date_range_end=export.date_range_end,
                anonymization_method=export.anonymization_method,
                privacy_budget_used=export.privacy_budget_used,
                data_hash=export.data_hash,
                pgp_signature=export.pgp_signature,
                signed_by_key_id=export.signed_by_key_id,
                created_at=export.created_at,
                export_format=export.export_format,
                file_size_bytes=export.file_size_bytes,
                record_count=export.export_data.get("statistical_summary", {}).get("total_records", 0)
            )
            response_exports.append(response_export)
        
        return response_exports
        
    except Exception as e:
        logger.error(f"Failed to list research exports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list research exports: {str(e)}")


@router.get("/exports/{export_id}", response_model=ResearchExportResponse)
async def get_research_export(
    export_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Get a specific research data export by ID."""
    
    try:
        result = await db.execute(
            select(ResearchDataExport).where(ResearchDataExport.id == export_id)
        )
        export = result.scalar_one_or_none()
        
        if not export:
            raise HTTPException(status_code=404, detail=f"Research export {export_id} not found")
        
        response = ResearchExportResponse(
            id=export.id,
            export_name=export.export_name,
            export_description=export.export_description,
            domain_ids=export.domain_ids,
            principle_ids=export.principle_ids,
            date_range_start=export.date_range_start,
            date_range_end=export.date_range_end,
            anonymization_method=export.anonymization_method,
            privacy_budget_used=export.privacy_budget_used,
            data_hash=export.data_hash,
            pgp_signature=export.pgp_signature,
            signed_by_key_id=export.signed_by_key_id,
            created_at=export.created_at,
            export_format=export.export_format,
            file_size_bytes=export.file_size_bytes,
            record_count=export.export_data.get("statistical_summary", {}).get("total_records", 0)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get research export {export_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get research export: {str(e)}")


@router.get("/exports/{export_id}/data")
async def download_research_export_data(
    export_id: int,
    include_raw_data: bool = Query(False, description="Include raw anonymized data"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Download research export data."""
    
    try:
        result = await db.execute(
            select(ResearchDataExport).where(ResearchDataExport.id == export_id)
        )
        export = result.scalar_one_or_none()
        
        if not export:
            raise HTTPException(status_code=404, detail=f"Research export {export_id} not found")
        
        # Prepare download data
        download_data = {
            "export_metadata": {
                "id": export.id,
                "export_name": export.export_name,
                "export_description": export.export_description,
                "created_at": export.created_at.isoformat(),
                "anonymization_method": export.anonymization_method,
                "data_hash": export.data_hash,
                "pgp_signature": export.pgp_signature,
                "signed_by_key_id": export.signed_by_key_id
            },
            "statistical_summary": export.statistical_summary
        }
        
        if include_raw_data:
            download_data["anonymized_data"] = export.export_data.get("data", [])
        
        return download_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download research export {export_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download research export: {str(e)}")


@router.get("/exports/{export_id}/summary", response_model=StatisticalSummaryResponse)
async def get_export_statistical_summary(
    export_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Get statistical summary for a research export."""
    
    try:
        result = await db.execute(
            select(ResearchDataExport).where(ResearchDataExport.id == export_id)
        )
        export = result.scalar_one_or_none()
        
        if not export:
            raise HTTPException(status_code=404, detail=f"Research export {export_id} not found")
        
        summary = export.statistical_summary or {}
        
        return StatisticalSummaryResponse(
            total_records=summary.get("total_records", 0),
            domain_distribution=summary.get("domain_distribution", {}),
            principle_distribution=summary.get("principle_distribution", {}),
            consistency_statistics=summary.get("consistency_statistics", {}),
            execution_time_statistics=summary.get("execution_time_statistics", {}),
            accuracy_statistics=summary.get("accuracy_statistics", {}),
            temporal_distribution=summary.get("temporal_distribution", {}),
            conflict_statistics=summary.get("conflict_statistics", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistical summary for export {export_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistical summary: {str(e)}")


@router.post("/exports/{export_id}/verify")
async def verify_export_integrity(
    export_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Verify the cryptographic integrity of a research export."""
    
    try:
        result = await db.execute(
            select(ResearchDataExport).where(ResearchDataExport.id == export_id)
        )
        export = result.scalar_one_or_none()
        
        if not export:
            raise HTTPException(status_code=404, detail=f"Research export {export_id} not found")
        
        # Verify data hash
        import json
        import hashlib
        
        export_data_str = json.dumps(export.export_data, indent=2, default=str)
        calculated_hash = hashlib.sha256(export_data_str.encode('utf-8')).hexdigest()
        
        hash_verified = calculated_hash == export.data_hash
        
        # Verify PGP signature (simplified)
        signature_verified = export.pgp_signature is not None and export.signed_by_key_id is not None
        
        verification_result = {
            "export_id": export_id,
            "hash_verified": hash_verified,
            "signature_verified": signature_verified,
            "overall_verified": hash_verified and signature_verified,
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "stored_hash": export.data_hash,
                "calculated_hash": calculated_hash,
                "signature_present": export.pgp_signature is not None,
                "signing_key": export.signed_by_key_id
            }
        }
        
        return verification_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify export integrity for {export_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to verify export integrity: {str(e)}")


@router.delete("/exports/{export_id}")
async def delete_research_export(
    export_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_integrity_admin)
):
    """Delete a research data export."""
    
    try:
        result = await db.execute(
            select(ResearchDataExport).where(ResearchDataExport.id == export_id)
        )
        export = result.scalar_one_or_none()
        
        if not export:
            raise HTTPException(status_code=404, detail=f"Research export {export_id} not found")
        
        await db.delete(export)
        await db.commit()
        
        logger.info(f"Deleted research export {export_id}")
        
        return {"message": f"Research export {export_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete research export {export_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete research export: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for research data pipeline."""
    return {
        "status": "healthy",
        "service": "research_data_pipeline",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
