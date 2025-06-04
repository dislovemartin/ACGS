"""
Constitutional Fidelity Monitor API endpoints for the AC Service.
Provides system-wide health monitoring with real-time fidelity calculation and alerts.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime, timedelta

from shared.database import get_async_db as get_db
from ... import crud
from shared.auth import get_current_active_user as get_current_user, require_admin, require_policy_manager
from shared.models import User

# Import QEC enhancement components
try:
    from alphaevolve_gs_engine.services.qec_enhancement.constitutional_fidelity_monitor import (
        ConstitutionalFidelityMonitor,
        FidelityComponents,
        FidelityAlert,
        FidelityLevel
    )
    QEC_AVAILABLE = True
except ImportError:
    QEC_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize fidelity monitor if available
if QEC_AVAILABLE:
    fidelity_monitor = ConstitutionalFidelityMonitor()


@router.get("/current")
async def get_current_fidelity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current constitutional fidelity score and components."""
    if not QEC_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Constitutional Fidelity Monitor not available"
        )
    
    try:
        # Get current principles for fidelity calculation
        principles = await crud.get_ac_principles(db, skip=0, limit=1000)
        
        # Mock system metrics (in production, these would come from monitoring systems)
        system_metrics = {
            "synthesis_success_rate": 0.89,
            "enforcement_reliability": 0.92,
            "adaptation_speed": 0.85,
            "stakeholder_satisfaction": 0.88,
            "appeal_frequency": 0.12,
            "high_severity_appeals": False
        }
        
        # Calculate current fidelity
        fidelity = await fidelity_monitor.calculate_fidelity(principles, system_metrics)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "composite_score": fidelity.composite_score,
            "level": fidelity.level.value,
            "components": {
                "principle_coverage": fidelity.principle_coverage,
                "synthesis_success": fidelity.synthesis_success,
                "enforcement_reliability": fidelity.enforcement_reliability,
                "adaptation_speed": fidelity.adaptation_speed,
                "stakeholder_satisfaction": fidelity.stakeholder_satisfaction,
                "appeal_frequency": fidelity.appeal_frequency
            },
            "metadata": fidelity.metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to get current fidelity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fidelity calculation failed: {str(e)}"
        )


@router.get("/history")
async def get_fidelity_history(
    hours: int = Query(24, description="Number of hours of history to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get historical fidelity data for time-series analysis."""
    if not QEC_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Constitutional Fidelity Monitor not available"
        )
    
    try:
        # Get fidelity history from monitor
        history = fidelity_monitor.get_fidelity_history(hours=hours)
        
        return {
            "period_hours": hours,
            "data_points": len(history),
            "history": [
                {
                    "timestamp": f.timestamp.isoformat(),
                    "composite_score": f.composite_score,
                    "level": f.level.value,
                    "components": {
                        "principle_coverage": f.principle_coverage,
                        "synthesis_success": f.synthesis_success,
                        "enforcement_reliability": f.enforcement_reliability,
                        "adaptation_speed": f.adaptation_speed,
                        "stakeholder_satisfaction": f.stakeholder_satisfaction,
                        "appeal_frequency": f.appeal_frequency
                    }
                }
                for f in history
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get fidelity history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"History retrieval failed: {str(e)}"
        )


@router.get("/trend")
async def get_fidelity_trend(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current fidelity trend analysis."""
    if not QEC_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Constitutional Fidelity Monitor not available"
        )
    
    try:
        trend = fidelity_monitor.get_fidelity_trend()
        current_fidelity = fidelity_monitor.get_current_fidelity()
        
        return {
            "trend": trend,
            "current_score": current_fidelity.composite_score if current_fidelity else None,
            "current_level": current_fidelity.level.value if current_fidelity else None,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get fidelity trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend analysis failed: {str(e)}"
        )


@router.get("/alerts")
async def get_active_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get currently active fidelity alerts."""
    if not QEC_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Constitutional Fidelity Monitor not available"
        )
    
    try:
        alerts = fidelity_monitor.get_active_alerts()
        
        return {
            "active_alerts": len(alerts),
            "alerts": [
                {
                    "level": alert.level.value,
                    "title": alert.title,
                    "description": alert.description,
                    "timestamp": alert.timestamp.isoformat(),
                    "components_affected": alert.components_affected,
                    "recommended_actions": alert.recommended_actions,
                    "metadata": alert.metadata
                }
                for alert in alerts
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get active alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert retrieval failed: {str(e)}"
        )


@router.post("/start-monitoring")
async def start_monitoring(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Start continuous fidelity monitoring."""
    if not QEC_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Constitutional Fidelity Monitor not available"
        )
    
    try:
        await fidelity_monitor.start_monitoring()
        
        return {
            "message": "Constitutional fidelity monitoring started",
            "monitoring_active": fidelity_monitor.monitoring_active,
            "calculation_interval": fidelity_monitor.calculation_interval,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monitoring start failed: {str(e)}"
        )


@router.post("/stop-monitoring")
async def stop_monitoring(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Stop continuous fidelity monitoring."""
    if not QEC_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Constitutional Fidelity Monitor not available"
        )
    
    try:
        await fidelity_monitor.stop_monitoring()
        
        return {
            "message": "Constitutional fidelity monitoring stopped",
            "monitoring_active": fidelity_monitor.monitoring_active,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monitoring stop failed: {str(e)}"
        )


@router.get("/status")
async def get_monitoring_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current monitoring status and configuration."""
    if not QEC_AVAILABLE:
        return {
            "qec_available": False,
            "message": "Constitutional Fidelity Monitor not available"
        }
    
    try:
        current_fidelity = fidelity_monitor.get_current_fidelity()
        active_alerts = fidelity_monitor.get_active_alerts()
        
        return {
            "qec_available": True,
            "monitoring_active": fidelity_monitor.monitoring_active,
            "calculation_interval": fidelity_monitor.calculation_interval,
            "last_calculation": fidelity_monitor.last_calculation_time.isoformat() if fidelity_monitor.last_calculation_time else None,
            "current_score": current_fidelity.composite_score if current_fidelity else None,
            "current_level": current_fidelity.level.value if current_fidelity else None,
            "active_alerts": len(active_alerts),
            "alert_handlers": len(fidelity_monitor.alert_handlers),
            "history_size": len(fidelity_monitor.fidelity_history),
            "thresholds": {
                "green": fidelity_monitor.thresholds.green_threshold,
                "amber": fidelity_monitor.thresholds.amber_threshold,
                "red": fidelity_monitor.thresholds.red_threshold
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status retrieval failed: {str(e)}"
        )


@router.post("/recalculate")
async def force_recalculation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_policy_manager)
):
    """Force immediate recalculation of constitutional fidelity."""
    if not QEC_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Constitutional Fidelity Monitor not available"
        )
    
    try:
        # Get current principles
        principles = await crud.get_ac_principles(db, skip=0, limit=1000)
        
        # Mock system metrics (in production, these would come from monitoring systems)
        system_metrics = {
            "synthesis_success_rate": 0.89,
            "enforcement_reliability": 0.92,
            "adaptation_speed": 0.85,
            "stakeholder_satisfaction": 0.88,
            "appeal_frequency": 0.12,
            "high_severity_appeals": False
        }
        
        # Force recalculation
        fidelity = await fidelity_monitor.calculate_fidelity(principles, system_metrics)
        
        return {
            "message": "Fidelity recalculated successfully",
            "timestamp": datetime.now().isoformat(),
            "composite_score": fidelity.composite_score,
            "level": fidelity.level.value,
            "components": {
                "principle_coverage": fidelity.principle_coverage,
                "synthesis_success": fidelity.synthesis_success,
                "enforcement_reliability": fidelity.enforcement_reliability,
                "adaptation_speed": fidelity.adaptation_speed,
                "stakeholder_satisfaction": fidelity.stakeholder_satisfaction,
                "appeal_frequency": fidelity.appeal_frequency
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to recalculate fidelity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recalculation failed: {str(e)}"
        )
