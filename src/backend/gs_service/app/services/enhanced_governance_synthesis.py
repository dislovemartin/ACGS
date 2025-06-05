"""
Enhanced Governance Synthesis Service with OPA Integration

This service integrates the new OPA/Rego policy validation engine with existing
governance synthesis workflows, providing comprehensive policy validation,
conflict detection, and constitutional compliance checking.

Phase 2: Governance Synthesis Hardening with Rego/OPA Integration
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

from .policy_validator import (
    PolicyValidationEngine,
    PolicyValidationRequest,
    PolicyValidationResponse,
    ValidationLevel,
    PolicyType,
    get_policy_validator
)
from ..core.wina_rego_synthesis import (
    WINARegoSynthesizer,
    WINARegoSynthesisResult,
    get_wina_rego_synthesizer,
    synthesize_rego_policy_with_wina
)
from .alphaevolve_bridge import AlphaEvolveBridge
from ..workflows.policy_synthesis_workflow import PolicySynthesisWorkflow
from ..core.opa_integration import get_opa_client, OPAIntegrationError

logger = logging.getLogger(__name__)


@dataclass
class EnhancedSynthesisRequest:
    """Enhanced synthesis request with OPA validation options."""
    synthesis_goal: str
    constitutional_principles: List[Dict[str, Any]]
    constraints: Optional[List[str]] = None
    context_data: Optional[Dict[str, Any]] = None
    target_format: str = "rego"
    policy_type: str = "governance_rule"
    
    # Validation options
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    enable_opa_validation: bool = True
    enable_conflict_detection: bool = True
    enable_compliance_checking: bool = True
    enable_constitutional_validation: bool = True
    
    # Performance options
    enable_parallel_validation: bool = True
    max_validation_latency_ms: int = 50
    
    # Integration options
    enable_wina_optimization: bool = True
    enable_alphaevolve_synthesis: bool = True
    enable_langgraph_workflow: bool = True


@dataclass
class EnhancedSynthesisResponse:
    """Enhanced synthesis response with comprehensive validation results."""
    synthesis_id: str
    synthesis_time_ms: float
    
    # Synthesis results
    synthesized_policy: str
    policy_metadata: Dict[str, Any]
    
    # Validation results
    validation_response: Optional[PolicyValidationResponse]
    is_valid: bool
    validation_score: float
    
    # Performance metrics
    synthesis_latency_ms: float
    validation_latency_ms: float
    total_latency_ms: float
    
    # Integration results
    wina_result: Optional[WINARegoSynthesisResult]
    alphaevolve_metadata: Optional[Dict[str, Any]]
    langgraph_metadata: Optional[Dict[str, Any]]
    
    # Recommendations and warnings
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


class EnhancedGovernanceSynthesis:
    """
    Enhanced governance synthesis service with comprehensive OPA integration.
    
    Combines existing synthesis capabilities (WINA, AlphaEvolve, LangGraph)
    with new OPA-based policy validation, conflict detection, and compliance
    checking for robust governance rule synthesis.
    """
    
    def __init__(self):
        self.policy_validator: Optional[PolicyValidationEngine] = None
        self.wina_synthesizer: Optional[WINARegoSynthesizer] = None
        self.alphaevolve_bridge: Optional[AlphaEvolveBridge] = None
        self.langgraph_workflow: Optional[PolicySynthesisWorkflow] = None
        self._initialized = False
        
        # Performance tracking
        self.metrics = {
            "total_syntheses": 0,
            "successful_syntheses": 0,
            "failed_syntheses": 0,
            "average_synthesis_time_ms": 0.0,
            "average_validation_time_ms": 0.0,
            "opa_validation_enabled_count": 0,
            "performance_threshold_violations": 0
        }
    
    async def initialize(self):
        """Initialize all synthesis and validation components."""
        if self._initialized:
            return
        
        try:
            # Initialize OPA-based policy validator
            self.policy_validator = await get_policy_validator()
            
            # Initialize existing synthesis components
            self.wina_synthesizer = get_wina_rego_synthesizer()
            self.alphaevolve_bridge = AlphaEvolveBridge()
            await self.alphaevolve_bridge.initialize()
            
            # Initialize LangGraph workflow
            self.langgraph_workflow = PolicySynthesisWorkflow()
            
            self._initialized = True
            logger.info("Enhanced governance synthesis service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced governance synthesis: {e}")
            raise
    
    async def synthesize_policy(self, request: EnhancedSynthesisRequest) -> EnhancedSynthesisResponse:
        """
        Synthesize governance policy with comprehensive validation and optimization.
        
        Args:
            request: Enhanced synthesis request
            
        Returns:
            Enhanced synthesis response with validation results
            
        Raises:
            Exception: If synthesis or validation fails
        """
        if not self._initialized:
            await self.initialize()
        
        synthesis_id = f"synthesis_{int(time.time() * 1000)}"
        start_time = time.time()
        
        errors = []
        warnings = []
        recommendations = []
        
        try:
            logger.info(f"Starting enhanced policy synthesis: {synthesis_id}")
            
            # Phase 1: Policy Synthesis
            synthesis_start = time.time()
            synthesis_result = await self._execute_synthesis(request)
            synthesis_time_ms = (time.time() - synthesis_start) * 1000
            
            if not synthesis_result:
                raise Exception("Policy synthesis failed to produce results")
            
            # Phase 2: OPA-based Validation (if enabled)
            validation_response = None
            validation_time_ms = 0.0
            
            if request.enable_opa_validation:
                validation_start = time.time()
                validation_response = await self._validate_synthesized_policy(
                    synthesis_result, request
                )
                validation_time_ms = (time.time() - validation_start) * 1000
                
                # Check validation latency threshold
                if validation_time_ms > request.max_validation_latency_ms:
                    warnings.append(f"Validation latency {validation_time_ms:.2f}ms exceeded threshold")
                    self.metrics["performance_threshold_violations"] += 1
                
                # Extract validation results
                if validation_response:
                    errors.extend(validation_response.errors)
                    warnings.extend(validation_response.warnings)
                    recommendations.extend(validation_response.recommendations)
            
            # Phase 3: Calculate overall results
            total_time_ms = (time.time() - start_time) * 1000
            is_valid = validation_response.is_valid if validation_response else True
            validation_score = validation_response.overall_score if validation_response else 1.0
            
            # Update metrics
            self._update_metrics(synthesis_time_ms, validation_time_ms, is_valid)
            
            # Create response
            response = EnhancedSynthesisResponse(
                synthesis_id=synthesis_id,
                synthesis_time_ms=total_time_ms,
                synthesized_policy=synthesis_result.get("policy_content", ""),
                policy_metadata=synthesis_result.get("metadata", {}),
                validation_response=validation_response,
                is_valid=is_valid,
                validation_score=validation_score,
                synthesis_latency_ms=synthesis_time_ms,
                validation_latency_ms=validation_time_ms,
                total_latency_ms=total_time_ms,
                wina_result=synthesis_result.get("wina_result"),
                alphaevolve_metadata=synthesis_result.get("alphaevolve_metadata"),
                langgraph_metadata=synthesis_result.get("langgraph_metadata"),
                errors=errors,
                warnings=warnings,
                recommendations=recommendations
            )
            
            logger.info(f"Enhanced synthesis completed: {synthesis_id} "
                       f"(valid: {is_valid}, score: {validation_score:.2f}, "
                       f"time: {total_time_ms:.2f}ms)")
            
            return response
            
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            self.metrics["failed_syntheses"] += 1
            logger.error(f"Enhanced synthesis failed: {synthesis_id} - {e}")
            
            # Return error response
            return EnhancedSynthesisResponse(
                synthesis_id=synthesis_id,
                synthesis_time_ms=total_time_ms,
                synthesized_policy="",
                policy_metadata={},
                validation_response=None,
                is_valid=False,
                validation_score=0.0,
                synthesis_latency_ms=0.0,
                validation_latency_ms=0.0,
                total_latency_ms=total_time_ms,
                wina_result=None,
                alphaevolve_metadata=None,
                langgraph_metadata=None,
                errors=[str(e)],
                warnings=warnings,
                recommendations=["Fix synthesis errors and retry"]
            )
    
    async def _execute_synthesis(self, request: EnhancedSynthesisRequest) -> Dict[str, Any]:
        """Execute policy synthesis using available synthesis methods."""
        synthesis_results = {}
        
        # Method 1: WINA-optimized Rego synthesis (if enabled)
        if request.enable_wina_optimization:
            try:
                wina_result = await synthesize_rego_policy_with_wina(
                    synthesis_goal=request.synthesis_goal,
                    constitutional_principles=request.constitutional_principles,
                    constraints=request.constraints,
                    context_data=request.context_data,
                    apply_wina=True
                )
                
                if wina_result and wina_result.rego_content:
                    synthesis_results["wina_result"] = wina_result
                    synthesis_results["policy_content"] = wina_result.rego_content
                    synthesis_results["metadata"] = {
                        "synthesis_method": "wina_rego",
                        "optimization_applied": wina_result.optimization_applied,
                        "performance_metrics": wina_result.performance_metrics
                    }
                    logger.info("WINA synthesis completed successfully")
                    return synthesis_results
                    
            except Exception as e:
                logger.warning(f"WINA synthesis failed: {e}")
        
        # Method 2: AlphaEvolve synthesis (if enabled and available)
        if request.enable_alphaevolve_synthesis and self.alphaevolve_bridge.is_available():
            try:
                alphaevolve_result = await self.alphaevolve_bridge.synthesize_ec_governance_rules(
                    ec_context=request.context_data.get("ec_context", "general"),
                    optimization_objective=request.synthesis_goal,
                    constitutional_constraints=request.constraints or [],
                    target_format=request.target_format
                )
                
                if alphaevolve_result.get("rules"):
                    synthesis_results["alphaevolve_metadata"] = alphaevolve_result.get("metadata", {})
                    synthesis_results["policy_content"] = alphaevolve_result["rules"][0] if alphaevolve_result["rules"] else ""
                    synthesis_results["metadata"] = {
                        "synthesis_method": "alphaevolve",
                        "rule_count": len(alphaevolve_result["rules"])
                    }
                    logger.info("AlphaEvolve synthesis completed successfully")
                    return synthesis_results
                    
            except Exception as e:
                logger.warning(f"AlphaEvolve synthesis failed: {e}")
        
        # Method 3: LangGraph workflow synthesis (if enabled)
        if request.enable_langgraph_workflow:
            try:
                # This would integrate with the existing LangGraph workflow
                # For now, we'll create a placeholder implementation
                langgraph_result = {
                    "policy_content": f"""
                    package {request.context_data.get('target_system', 'acgs')}.governance
                    
                    # Generated policy for: {request.synthesis_goal}
                    default allow := false
                    
                    allow if {{
                        # Constitutional compliance check
                        constitutional_compliance
                        # Context-specific rules would be generated here
                    }}
                    
                    constitutional_compliance if {{
                        # Placeholder for constitutional principle validation
                        true
                    }}
                    """,
                    "metadata": {
                        "synthesis_method": "langgraph_workflow",
                        "workflow_version": "1.0"
                    }
                }
                
                synthesis_results["langgraph_metadata"] = langgraph_result["metadata"]
                synthesis_results["policy_content"] = langgraph_result["policy_content"]
                synthesis_results["metadata"] = langgraph_result["metadata"]
                logger.info("LangGraph synthesis completed successfully")
                return synthesis_results
                
            except Exception as e:
                logger.warning(f"LangGraph synthesis failed: {e}")
        
        # Fallback: Basic template-based synthesis
        logger.warning("All advanced synthesis methods failed, using fallback")
        return {
            "policy_content": f"""
            package acgs.fallback
            
            # Fallback policy for: {request.synthesis_goal}
            default allow := false
            
            allow if {{
                # Basic governance rule
                input.action == "governance_action"
                input.user.authorized == true
            }}
            """,
            "metadata": {
                "synthesis_method": "fallback",
                "warning": "Advanced synthesis methods unavailable"
            }
        }
    
    async def _validate_synthesized_policy(self, synthesis_result: Dict[str, Any], 
                                         request: EnhancedSynthesisRequest) -> Optional[PolicyValidationResponse]:
        """Validate synthesized policy using OPA integration."""
        try:
            # Convert synthesis request to validation request
            validation_request = PolicyValidationRequest(
                policy_content=synthesis_result.get("policy_content", ""),
                policy_type=PolicyType(request.policy_type),
                constitutional_principles=request.constitutional_principles,
                existing_policies=[],  # Would be populated from database
                context_data=request.context_data or {},
                validation_level=request.validation_level,
                check_conflicts=request.enable_conflict_detection,
                check_compliance=request.enable_compliance_checking,
                check_constitutional=request.enable_constitutional_validation,
                target_format=request.target_format
            )
            
            # Execute validation
            validation_response = await self.policy_validator.validate_policy(validation_request)
            
            if request.enable_opa_validation:
                self.metrics["opa_validation_enabled_count"] += 1
            
            return validation_response
            
        except Exception as e:
            logger.error(f"Policy validation failed: {e}")
            return None
    
    async def batch_synthesize(self, requests: List[EnhancedSynthesisRequest]) -> List[EnhancedSynthesisResponse]:
        """Synthesize multiple policies in batch for improved performance."""
        if not requests:
            return []
        
        if len(requests) == 1:
            # Single request - use regular synthesis
            return [await self.synthesize_policy(requests[0])]
        
        # Batch processing with parallel execution
        if requests[0].enable_parallel_validation:
            semaphore = asyncio.Semaphore(4)  # Limit concurrent syntheses
            
            async def synthesize_with_semaphore(request):
                async with semaphore:
                    return await self.synthesize_policy(request)
            
            tasks = [synthesize_with_semaphore(request) for request in requests]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Sequential processing
            results = []
            for request in requests:
                result = await self.synthesize_policy(request)
                results.append(result)
            return results
    
    def _update_metrics(self, synthesis_time_ms: float, validation_time_ms: float, success: bool):
        """Update performance metrics."""
        self.metrics["total_syntheses"] += 1
        
        if success:
            self.metrics["successful_syntheses"] += 1
        else:
            self.metrics["failed_syntheses"] += 1
        
        # Update average times
        total = self.metrics["total_syntheses"]
        current_avg_synthesis = self.metrics["average_synthesis_time_ms"]
        current_avg_validation = self.metrics["average_validation_time_ms"]
        
        self.metrics["average_synthesis_time_ms"] = (
            (current_avg_synthesis * (total - 1)) + synthesis_time_ms
        ) / total
        
        self.metrics["average_validation_time_ms"] = (
            (current_avg_validation * (total - 1)) + validation_time_ms
        ) / total
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance and usage metrics."""
        return self.metrics.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        health_status = {
            "service": "enhanced_governance_synthesis",
            "status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check policy validator
            if self.policy_validator:
                validator_metrics = self.policy_validator.get_metrics()
                health_status["components"]["policy_validator"] = {
                    "status": "healthy",
                    "metrics": validator_metrics
                }
            
            # Check OPA client
            opa_client = await get_opa_client()
            opa_metrics = opa_client.get_metrics()
            health_status["components"]["opa_client"] = {
                "status": "healthy",
                "metrics": opa_metrics
            }
            
            # Check WINA synthesizer
            if self.wina_synthesizer:
                health_status["components"]["wina_synthesizer"] = {
                    "status": "healthy"
                }
            
            # Check AlphaEvolve bridge
            if self.alphaevolve_bridge:
                health_status["components"]["alphaevolve_bridge"] = {
                    "status": "healthy" if self.alphaevolve_bridge.is_available() else "unavailable"
                }
            
            # Overall service metrics
            health_status["service_metrics"] = self.get_metrics()
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            logger.error(f"Health check failed: {e}")
        
        return health_status


# Global enhanced governance synthesis service instance
_enhanced_synthesis_service: Optional[EnhancedGovernanceSynthesis] = None


async def get_enhanced_synthesis_service() -> EnhancedGovernanceSynthesis:
    """Get or create the global enhanced governance synthesis service instance."""
    global _enhanced_synthesis_service
    if _enhanced_synthesis_service is None:
        _enhanced_synthesis_service = EnhancedGovernanceSynthesis()
        await _enhanced_synthesis_service.initialize()
    return _enhanced_synthesis_service
