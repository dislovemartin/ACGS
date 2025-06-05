"""
API endpoints for Ultra Low Latency Optimization.

This module provides REST API endpoints for ultra-low latency policy decisions,
performance monitoring, and optimization management targeting sub-25ms latency.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user_id
from ...core.ultra_low_latency_optimizer import (
    get_ultra_low_latency_optimizer,
    OptimizationLevel,
    CacheStrategy,
    LatencyTarget
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class PolicyDecisionRequest(BaseModel):
    """Request model for optimized policy decision."""
    user_id: str = Field(..., description="User identifier")
    resource: str = Field(..., description="Resource being accessed")
    action: str = Field(..., description="Action being performed")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    optimization_level: OptimizationLevel = Field(
        default=OptimizationLevel.ENHANCED,
        description="Target optimization level"
    )


class BenchmarkRequest(BaseModel):
    """Request model for performance benchmark."""
    num_requests: int = Field(default=100, description="Number of test requests")
    optimization_level: OptimizationLevel = Field(
        default=OptimizationLevel.ENHANCED,
        description="Optimization level for benchmark"
    )


class OptimizationResponse(BaseModel):
    """Response model for optimization result."""
    operation_id: str
    latency_ms: float
    cache_hit: bool
    optimization_level: str
    breakdown: Dict[str, float]
    recommendations: List[str]
    target_met: bool
    timestamp: str


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    avg_latency: float
    p95_latency: float
    p99_latency: float
    cache_hit_rate: float
    throughput_rps: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float


class OptimizationReportResponse(BaseModel):
    """Response model for optimization report."""
    performance_metrics: Dict[str, float]
    target_achievement: Dict[str, bool]
    optimization_trends: Dict[str, Dict[str, float]]
    fragment_cache_stats: Dict[str, Any]
    recommendations: List[str]
    latency_target: float
    total_optimizations: int
    timestamp: str


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_policy_decision(
    request: PolicyDecisionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform ultra-low latency policy decision optimization.
    
    This endpoint optimizes policy decisions targeting sub-25ms latency
    using advanced caching, speculative execution, and fragment-level optimization.
    """
    try:
        optimizer = get_ultra_low_latency_optimizer()
        
        # Prepare policy request
        policy_request = {
            "user_id": request.user_id,
            "resource": request.resource,
            "action": request.action,
            "context": request.context,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
        # Perform optimization
        result = await optimizer.optimize_policy_decision(
            policy_request=policy_request,
            optimization_level=request.optimization_level
        )
        
        return OptimizationResponse(
            operation_id=result.operation_id,
            latency_ms=result.latency_ms,
            cache_hit=result.cache_hit,
            optimization_level=result.optimization_level.value,
            breakdown=result.breakdown,
            recommendations=result.recommendations,
            target_met=result.latency_ms <= optimizer.target_latency,
            timestamp=result.timestamp.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in policy decision optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize policy decision: {str(e)}"
        )


@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current performance metrics for ultra-low latency optimization.
    
    Returns comprehensive metrics including latency percentiles, cache performance,
    throughput, and resource utilization.
    """
    try:
        optimizer = get_ultra_low_latency_optimizer()
        
        metrics = optimizer.get_performance_metrics()
        
        return PerformanceMetricsResponse(
            avg_latency=metrics.avg_latency,
            p95_latency=metrics.p95_latency,
            p99_latency=metrics.p99_latency,
            cache_hit_rate=metrics.cache_hit_rate,
            throughput_rps=metrics.throughput_rps,
            error_rate=metrics.error_rate,
            memory_usage_mb=metrics.memory_usage_mb,
            cpu_usage_percent=metrics.cpu_usage_percent
        )
        
    except Exception as e:
        logger.error(f"Error retrieving performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.get("/report", response_model=OptimizationReportResponse)
async def get_optimization_report(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive optimization report.
    
    Returns detailed analysis of optimization performance, target achievement,
    trends, and recommendations for further improvements.
    """
    try:
        optimizer = get_ultra_low_latency_optimizer()
        
        report = optimizer.get_optimization_report()
        
        return OptimizationReportResponse(
            performance_metrics=report["performance_metrics"],
            target_achievement=report["target_achievement"],
            optimization_trends=report["optimization_trends"],
            fragment_cache_stats=report["fragment_cache_stats"],
            recommendations=report["recommendations"],
            latency_target=report["latency_target"],
            total_optimizations=report["total_optimizations"],
            timestamp=report["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Error generating optimization report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate optimization report: {str(e)}"
        )


@router.post("/adaptive-optimization")
async def perform_adaptive_optimization(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform adaptive optimization based on current performance.
    
    Automatically adjusts optimization parameters based on current performance
    metrics to maintain target latency and improve efficiency.
    """
    try:
        optimizer = get_ultra_low_latency_optimizer()
        
        result = await optimizer.adaptive_optimization()
        
        return {
            "message": "Adaptive optimization completed",
            "optimization_result": result,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error in adaptive optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform adaptive optimization: {str(e)}"
        )


@router.post("/benchmark")
async def run_performance_benchmark(
    request: BenchmarkRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Run performance benchmark with specified parameters.
    
    Executes a series of test requests to measure performance characteristics
    and validate latency targets under controlled conditions.
    """
    try:
        optimizer = get_ultra_low_latency_optimizer()
        
        benchmark_results = await optimizer.benchmark_performance(
            num_requests=request.num_requests
        )
        
        return {
            "message": f"Benchmark completed with {request.num_requests} requests",
            "benchmark_results": benchmark_results,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error running performance benchmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run performance benchmark: {str(e)}"
        )


@router.get("/optimization-levels")
async def list_optimization_levels(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List available optimization levels and their characteristics."""
    try:
        optimization_levels = {
            OptimizationLevel.STANDARD.value: {
                "name": "Standard Optimization",
                "target_latency": "< 50ms",
                "description": "Standard optimization with basic caching",
                "use_case": "General purpose policy decisions",
                "resource_usage": "Low"
            },
            OptimizationLevel.ENHANCED.value: {
                "name": "Enhanced Optimization",
                "target_latency": "< 25ms",
                "description": "Advanced caching with fragment-level optimization",
                "use_case": "High-performance policy decisions",
                "resource_usage": "Medium"
            },
            OptimizationLevel.ULTRA.value: {
                "name": "Ultra Optimization",
                "target_latency": "< 10ms",
                "description": "Speculative execution with aggressive caching",
                "use_case": "Real-time critical decisions",
                "resource_usage": "High"
            },
            OptimizationLevel.EXTREME.value: {
                "name": "Extreme Optimization",
                "target_latency": "< 5ms",
                "description": "Maximum optimization with pre-computation",
                "use_case": "Ultra-low latency requirements",
                "resource_usage": "Very High"
            }
        }
        
        return {
            "message": "Available optimization levels",
            "optimization_levels": optimization_levels,
            "default_level": OptimizationLevel.ENHANCED.value,
            "recommendation": "Use ENHANCED for most applications, ULTRA for critical real-time decisions"
        }
        
    except Exception as e:
        logger.error(f"Error listing optimization levels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list optimization levels: {str(e)}"
        )


@router.get("/cache-strategies")
async def list_cache_strategies(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List available cache strategies and their TTL configurations."""
    try:
        cache_strategies = {
            CacheStrategy.IMMEDIATE.value: {
                "name": "Immediate Caching",
                "ttl": "No expiration",
                "description": "Cache immediately with no TTL",
                "use_case": "Static configuration data"
            },
            CacheStrategy.SHORT_TERM.value: {
                "name": "Short-term Caching",
                "ttl": "5 minutes",
                "description": "Short TTL for dynamic policy decisions",
                "use_case": "Policy decisions with frequent changes"
            },
            CacheStrategy.MEDIUM_TERM.value: {
                "name": "Medium-term Caching",
                "ttl": "1 hour",
                "description": "Medium TTL for governance rules",
                "use_case": "Governance rules and policies"
            },
            CacheStrategy.LONG_TERM.value: {
                "name": "Long-term Caching",
                "ttl": "24 hours",
                "description": "Long TTL for static configuration",
                "use_case": "Static system configuration"
            },
            CacheStrategy.ADAPTIVE.value: {
                "name": "Adaptive Caching",
                "ttl": "Dynamic based on access patterns",
                "description": "Dynamic TTL based on access frequency",
                "use_case": "Automatically optimized caching"
            }
        }
        
        return {
            "message": "Available cache strategies",
            "cache_strategies": cache_strategies,
            "performance_targets": {
                "cache_hit_rate": "> 80%",
                "cache_lookup_latency": "< 2ms",
                "fragment_cache_latency": "< 1ms"
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing cache strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cache strategies: {str(e)}"
        )
