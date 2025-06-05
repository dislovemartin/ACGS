"""
Enhanced Governance Synthesis API Endpoints

API endpoints for the enhanced governance synthesis service with OPA integration,
providing comprehensive policy validation, conflict detection, and performance
optimization.

Phase 2: Governance Synthesis Hardening with Rego/OPA Integration
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from pydantic import BaseModel, Field
from datetime import datetime

from ...services.enhanced_governance_synthesis import (
    EnhancedGovernanceSynthesis,
    EnhancedSynthesisRequest,
    EnhancedSynthesisResponse,
    get_enhanced_synthesis_service
)
from ...services.policy_validator import ValidationLevel, PolicyType
from ...core.opa_integration import OPAIntegrationError

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for API requests and responses
class ConstitutionalPrincipleAPI(BaseModel):
    """Constitutional principle for API requests."""
    description: str = Field(..., description="Description of the constitutional principle")
    type: str = Field(..., description="Type of principle (e.g., fairness, transparency)")
    category: Optional[str] = Field(None, description="Category of the principle")
    weight: Optional[float] = Field(1.0, description="Weight/importance of the principle")


class EnhancedSynthesisRequestAPI(BaseModel):
    """Enhanced synthesis request for API."""
    synthesis_goal: str = Field(..., description="Goal of the policy synthesis")
    constitutional_principles: List[ConstitutionalPrincipleAPI] = Field(
        ..., description="Constitutional principles to consider"
    )
    constraints: Optional[List[str]] = Field(None, description="Additional constraints")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Context data for synthesis")
    target_format: str = Field("rego", description="Target format for the policy")
    policy_type: str = Field("governance_rule", description="Type of policy to synthesize")
    
    # Validation options
    validation_level: str = Field("standard", description="Validation level (basic, standard, comprehensive)")
    enable_opa_validation: bool = Field(True, description="Enable OPA-based validation")
    enable_conflict_detection: bool = Field(True, description="Enable conflict detection")
    enable_compliance_checking: bool = Field(True, description="Enable compliance checking")
    enable_constitutional_validation: bool = Field(True, description="Enable constitutional validation")
    
    # Performance options
    enable_parallel_validation: bool = Field(True, description="Enable parallel validation")
    max_validation_latency_ms: int = Field(50, description="Maximum validation latency in milliseconds")
    
    # Integration options
    enable_wina_optimization: bool = Field(True, description="Enable WINA optimization")
    enable_alphaevolve_synthesis: bool = Field(True, description="Enable AlphaEvolve synthesis")
    enable_langgraph_workflow: bool = Field(True, description="Enable LangGraph workflow")


class ValidationResultAPI(BaseModel):
    """Validation result for API response."""
    is_valid: bool
    overall_score: float
    validation_time_ms: float
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]
    decision_latency_ms: float
    cache_hit: bool


class EnhancedSynthesisResponseAPI(BaseModel):
    """Enhanced synthesis response for API."""
    synthesis_id: str
    synthesis_time_ms: float
    synthesized_policy: str
    policy_metadata: Dict[str, Any]
    validation_result: Optional[ValidationResultAPI]
    is_valid: bool
    validation_score: float
    synthesis_latency_ms: float
    validation_latency_ms: float
    total_latency_ms: float
    wina_metadata: Optional[Dict[str, Any]]
    alphaevolve_metadata: Optional[Dict[str, Any]]
    langgraph_metadata: Optional[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


class BatchSynthesisRequestAPI(BaseModel):
    """Batch synthesis request for API."""
    requests: List[EnhancedSynthesisRequestAPI] = Field(
        ..., description="List of synthesis requests"
    )
    enable_parallel_processing: bool = Field(
        True, description="Enable parallel processing of requests"
    )


class HealthCheckResponseAPI(BaseModel):
    """Health check response for API."""
    service: str
    status: str
    components: Dict[str, Any]
    service_metrics: Dict[str, Any]
    timestamp: str


@router.post("/synthesize", response_model=EnhancedSynthesisResponseAPI)
async def synthesize_policy(
    request: EnhancedSynthesisRequestAPI,
    background_tasks: BackgroundTasks
) -> EnhancedSynthesisResponseAPI:
    """
    Synthesize a governance policy with comprehensive OPA validation.
    
    This endpoint provides enhanced policy synthesis with:
    - Multiple synthesis methods (WINA, AlphaEvolve, LangGraph)
    - Comprehensive OPA-based validation
    - Constitutional compliance checking
    - Policy conflict detection
    - Performance optimization with <50ms validation target
    """
    try:
        # Get enhanced synthesis service
        synthesis_service = await get_enhanced_synthesis_service()
        
        # Convert API request to service request
        service_request = EnhancedSynthesisRequest(
            synthesis_goal=request.synthesis_goal,
            constitutional_principles=[
                {
                    "description": p.description,
                    "type": p.type,
                    "category": p.category,
                    "weight": p.weight
                }
                for p in request.constitutional_principles
            ],
            constraints=request.constraints,
            context_data=request.context_data or {},
            target_format=request.target_format,
            policy_type=request.policy_type,
            validation_level=ValidationLevel(request.validation_level),
            enable_opa_validation=request.enable_opa_validation,
            enable_conflict_detection=request.enable_conflict_detection,
            enable_compliance_checking=request.enable_compliance_checking,
            enable_constitutional_validation=request.enable_constitutional_validation,
            enable_parallel_validation=request.enable_parallel_validation,
            max_validation_latency_ms=request.max_validation_latency_ms,
            enable_wina_optimization=request.enable_wina_optimization,
            enable_alphaevolve_synthesis=request.enable_alphaevolve_synthesis,
            enable_langgraph_workflow=request.enable_langgraph_workflow
        )
        
        # Execute synthesis
        synthesis_response = await synthesis_service.synthesize_policy(service_request)
        
        # Convert validation response
        validation_result = None
        if synthesis_response.validation_response:
            validation_result = ValidationResultAPI(
                is_valid=synthesis_response.validation_response.is_valid,
                overall_score=synthesis_response.validation_response.overall_score,
                validation_time_ms=synthesis_response.validation_response.validation_time_ms,
                errors=synthesis_response.validation_response.errors,
                warnings=synthesis_response.validation_response.warnings,
                recommendations=synthesis_response.validation_response.recommendations,
                decision_latency_ms=synthesis_response.validation_response.decision_latency_ms,
                cache_hit=synthesis_response.validation_response.cache_hit
            )
        
        # Convert service response to API response
        api_response = EnhancedSynthesisResponseAPI(
            synthesis_id=synthesis_response.synthesis_id,
            synthesis_time_ms=synthesis_response.synthesis_time_ms,
            synthesized_policy=synthesis_response.synthesized_policy,
            policy_metadata=synthesis_response.policy_metadata,
            validation_result=validation_result,
            is_valid=synthesis_response.is_valid,
            validation_score=synthesis_response.validation_score,
            synthesis_latency_ms=synthesis_response.synthesis_latency_ms,
            validation_latency_ms=synthesis_response.validation_latency_ms,
            total_latency_ms=synthesis_response.total_latency_ms,
            wina_metadata=synthesis_response.wina_result.__dict__ if synthesis_response.wina_result else None,
            alphaevolve_metadata=synthesis_response.alphaevolve_metadata,
            langgraph_metadata=synthesis_response.langgraph_metadata,
            errors=synthesis_response.errors,
            warnings=synthesis_response.warnings,
            recommendations=synthesis_response.recommendations
        )
        
        logger.info(f"Enhanced synthesis completed: {synthesis_response.synthesis_id}")
        return api_response
        
    except OPAIntegrationError as e:
        logger.error(f"OPA integration error in synthesis: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OPA integration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Enhanced synthesis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}"
        )


@router.post("/batch-synthesize", response_model=List[EnhancedSynthesisResponseAPI])
async def batch_synthesize_policies(
    request: BatchSynthesisRequestAPI,
    background_tasks: BackgroundTasks
) -> List[EnhancedSynthesisResponseAPI]:
    """
    Synthesize multiple governance policies in batch for improved performance.
    
    This endpoint provides batch processing with:
    - Parallel synthesis execution
    - Optimized resource utilization
    - Comprehensive validation for all policies
    - Performance metrics for batch operations
    """
    try:
        if not request.requests:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No synthesis requests provided"
            )
        
        if len(request.requests) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size exceeds maximum limit of 100 requests"
            )
        
        # Get enhanced synthesis service
        synthesis_service = await get_enhanced_synthesis_service()
        
        # Convert API requests to service requests
        service_requests = []
        for api_req in request.requests:
            service_req = EnhancedSynthesisRequest(
                synthesis_goal=api_req.synthesis_goal,
                constitutional_principles=[
                    {
                        "description": p.description,
                        "type": p.type,
                        "category": p.category,
                        "weight": p.weight
                    }
                    for p in api_req.constitutional_principles
                ],
                constraints=api_req.constraints,
                context_data=api_req.context_data or {},
                target_format=api_req.target_format,
                policy_type=api_req.policy_type,
                validation_level=ValidationLevel(api_req.validation_level),
                enable_opa_validation=api_req.enable_opa_validation,
                enable_conflict_detection=api_req.enable_conflict_detection,
                enable_compliance_checking=api_req.enable_compliance_checking,
                enable_constitutional_validation=api_req.enable_constitutional_validation,
                enable_parallel_validation=request.enable_parallel_processing,
                max_validation_latency_ms=api_req.max_validation_latency_ms,
                enable_wina_optimization=api_req.enable_wina_optimization,
                enable_alphaevolve_synthesis=api_req.enable_alphaevolve_synthesis,
                enable_langgraph_workflow=api_req.enable_langgraph_workflow
            )
            service_requests.append(service_req)
        
        # Execute batch synthesis
        synthesis_responses = await synthesis_service.batch_synthesize(service_requests)
        
        # Convert service responses to API responses
        api_responses = []
        for synthesis_response in synthesis_responses:
            if isinstance(synthesis_response, Exception):
                # Handle exceptions in batch processing
                api_response = EnhancedSynthesisResponseAPI(
                    synthesis_id=f"error_{len(api_responses)}",
                    synthesis_time_ms=0.0,
                    synthesized_policy="",
                    policy_metadata={},
                    validation_result=None,
                    is_valid=False,
                    validation_score=0.0,
                    synthesis_latency_ms=0.0,
                    validation_latency_ms=0.0,
                    total_latency_ms=0.0,
                    wina_metadata=None,
                    alphaevolve_metadata=None,
                    langgraph_metadata=None,
                    errors=[str(synthesis_response)],
                    warnings=[],
                    recommendations=["Fix synthesis errors and retry"]
                )
            else:
                # Convert validation response
                validation_result = None
                if synthesis_response.validation_response:
                    validation_result = ValidationResultAPI(
                        is_valid=synthesis_response.validation_response.is_valid,
                        overall_score=synthesis_response.validation_response.overall_score,
                        validation_time_ms=synthesis_response.validation_response.validation_time_ms,
                        errors=synthesis_response.validation_response.errors,
                        warnings=synthesis_response.validation_response.warnings,
                        recommendations=synthesis_response.validation_response.recommendations,
                        decision_latency_ms=synthesis_response.validation_response.decision_latency_ms,
                        cache_hit=synthesis_response.validation_response.cache_hit
                    )
                
                api_response = EnhancedSynthesisResponseAPI(
                    synthesis_id=synthesis_response.synthesis_id,
                    synthesis_time_ms=synthesis_response.synthesis_time_ms,
                    synthesized_policy=synthesis_response.synthesized_policy,
                    policy_metadata=synthesis_response.policy_metadata,
                    validation_result=validation_result,
                    is_valid=synthesis_response.is_valid,
                    validation_score=synthesis_response.validation_score,
                    synthesis_latency_ms=synthesis_response.synthesis_latency_ms,
                    validation_latency_ms=synthesis_response.validation_latency_ms,
                    total_latency_ms=synthesis_response.total_latency_ms,
                    wina_metadata=synthesis_response.wina_result.__dict__ if synthesis_response.wina_result else None,
                    alphaevolve_metadata=synthesis_response.alphaevolve_metadata,
                    langgraph_metadata=synthesis_response.langgraph_metadata,
                    errors=synthesis_response.errors,
                    warnings=synthesis_response.warnings,
                    recommendations=synthesis_response.recommendations
                )
            
            api_responses.append(api_response)
        
        logger.info(f"Batch synthesis completed: {len(api_responses)} policies")
        return api_responses
        
    except Exception as e:
        logger.error(f"Batch synthesis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch synthesis failed: {str(e)}"
        )


@router.get("/health", response_model=HealthCheckResponseAPI)
async def health_check() -> HealthCheckResponseAPI:
    """
    Perform health check on enhanced governance synthesis service.
    
    Returns status of all components including:
    - OPA integration
    - Policy validation engine
    - WINA synthesizer
    - AlphaEvolve bridge
    - Performance metrics
    """
    try:
        synthesis_service = await get_enhanced_synthesis_service()
        health_status = await synthesis_service.health_check()
        
        return HealthCheckResponseAPI(
            service=health_status["service"],
            status=health_status["status"],
            components=health_status["components"],
            service_metrics=health_status["service_metrics"],
            timestamp=health_status["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get performance metrics for enhanced governance synthesis service.
    
    Returns comprehensive metrics including:
    - Synthesis performance statistics
    - Validation latency metrics
    - OPA integration performance
    - Success/failure rates
    """
    try:
        synthesis_service = await get_enhanced_synthesis_service()
        return synthesis_service.get_metrics()
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )
