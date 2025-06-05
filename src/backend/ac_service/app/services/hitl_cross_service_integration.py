"""
Cross-Service Integration for Human-in-the-Loop Sampling

This module provides integration between the HITL sampling system and other
ACGS-PGP microservices, enabling comprehensive uncertainty assessment and
human oversight coordination across the entire system.

Key Features:
- Integration with GS Service for LLM confidence scoring
- Integration with FV Service for bias detection confidence
- Integration with PGC Service for policy enforcement confidence
- Integration with Integrity Service for cryptographic verification
- Coordination with Constitutional Council workflows
- Cross-service performance monitoring
"""

import asyncio
import logging
import httpx
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from shared import get_config
from .human_in_the_loop_sampler import HumanInTheLoopSampler, UncertaintyAssessment
from .human_escalation_system import EscalationLevel

logger = logging.getLogger(__name__)
config = get_config()


@dataclass
class CrossServiceConfidenceMetrics:
    """Confidence metrics from all ACGS-PGP services."""
    gs_llm_confidence: Optional[float] = None
    gs_synthesis_confidence: Optional[float] = None
    fv_bias_confidence: Optional[float] = None
    fv_fairness_confidence: Optional[float] = None
    pgc_enforcement_confidence: Optional[float] = None
    pgc_compilation_confidence: Optional[float] = None
    integrity_verification_confidence: Optional[float] = None
    integrity_cryptographic_confidence: Optional[float] = None
    
    def get_average_confidence(self) -> float:
        """Calculate average confidence across all available metrics."""
        confidences = [
            self.gs_llm_confidence,
            self.gs_synthesis_confidence,
            self.fv_bias_confidence,
            self.fv_fairness_confidence,
            self.pgc_enforcement_confidence,
            self.pgc_compilation_confidence,
            self.integrity_verification_confidence,
            self.integrity_cryptographic_confidence
        ]
        
        valid_confidences = [c for c in confidences if c is not None]
        return sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.5


class HITLCrossServiceIntegrator:
    """
    Cross-service integrator for HITL sampling system.
    
    Coordinates uncertainty assessment and human oversight across all
    ACGS-PGP microservices for comprehensive governance oversight.
    """
    
    def __init__(self, hitl_sampler: HumanInTheLoopSampler):
        """Initialize cross-service integrator."""
        self.hitl_sampler = hitl_sampler
        
        # Service URLs from configuration
        self.gs_service_url = config.get('gs_service_url', 'http://localhost:8004')
        self.fv_service_url = config.get('fv_service_url', 'http://localhost:8003')
        self.pgc_service_url = config.get('pgc_service_url', 'http://localhost:8005')
        self.integrity_service_url = config.get('integrity_service_url', 'http://localhost:8002')
        
        # HTTP client for cross-service communication
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Integration metrics
        self.integration_metrics = {
            "total_cross_service_assessments": 0,
            "successful_integrations": 0,
            "failed_integrations": 0,
            "service_availability": {
                "gs_service": True,
                "fv_service": True,
                "pgc_service": True,
                "integrity_service": True
            },
            "avg_integration_time_ms": 0.0
        }
        
        logger.info("HITL Cross-Service Integrator initialized")
    
    async def assess_cross_service_uncertainty(
        self,
        db: AsyncSession,
        decision_context: Dict[str, Any],
        principle_ids: Optional[List[int]] = None,
        include_services: Optional[List[str]] = None
    ) -> Tuple[UncertaintyAssessment, CrossServiceConfidenceMetrics]:
        """
        Perform comprehensive uncertainty assessment across all services.
        
        Args:
            db: Database session
            decision_context: Decision context information
            principle_ids: Related constitutional principle IDs
            include_services: List of services to include (default: all)
            
        Returns:
            Tuple of uncertainty assessment and cross-service confidence metrics
        """
        start_time = datetime.utcnow()
        self.integration_metrics["total_cross_service_assessments"] += 1
        
        try:
            # Default to all services if not specified
            if include_services is None:
                include_services = ["gs_service", "fv_service", "pgc_service", "integrity_service"]
            
            # Gather confidence metrics from all services
            confidence_metrics = await self._gather_cross_service_confidence(
                decision_context, principle_ids, include_services
            )
            
            # Enhance decision context with cross-service information
            enhanced_context = dict(decision_context)
            enhanced_context.update({
                "cross_service_confidence": confidence_metrics.get_average_confidence(),
                "gs_available": self.integration_metrics["service_availability"]["gs_service"],
                "fv_available": self.integration_metrics["service_availability"]["fv_service"],
                "pgc_available": self.integration_metrics["service_availability"]["pgc_service"],
                "integrity_available": self.integration_metrics["service_availability"]["integrity_service"],
                "multi_service_decision": len(include_services) > 1
            })
            
            # Perform enhanced uncertainty assessment
            assessment = await self.hitl_sampler.assess_uncertainty(
                db=db,
                decision_context=enhanced_context,
                ai_confidence=confidence_metrics.get_average_confidence(),
                principle_ids=principle_ids
            )
            
            # Update integration metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.integration_metrics["successful_integrations"] += 1
            self._update_avg_integration_time(processing_time)
            
            logger.info(f"Cross-service uncertainty assessment completed: "
                       f"services={include_services}, "
                       f"avg_confidence={confidence_metrics.get_average_confidence():.3f}, "
                       f"oversight_required={assessment.requires_human_oversight}")
            
            return assessment, confidence_metrics
            
        except Exception as e:
            self.integration_metrics["failed_integrations"] += 1
            logger.error(f"Cross-service uncertainty assessment failed: {e}")
            
            # Fallback to local assessment
            fallback_assessment = await self.hitl_sampler.assess_uncertainty(
                db=db,
                decision_context=decision_context,
                principle_ids=principle_ids
            )
            
            return fallback_assessment, CrossServiceConfidenceMetrics()
    
    async def _gather_cross_service_confidence(
        self,
        decision_context: Dict[str, Any],
        principle_ids: Optional[List[int]],
        include_services: List[str]
    ) -> CrossServiceConfidenceMetrics:
        """Gather confidence metrics from all specified services."""
        confidence_metrics = CrossServiceConfidenceMetrics()
        
        # Gather confidence metrics in parallel
        tasks = []
        
        if "gs_service" in include_services:
            tasks.append(self._get_gs_confidence(decision_context, principle_ids))
        
        if "fv_service" in include_services:
            tasks.append(self._get_fv_confidence(decision_context, principle_ids))
        
        if "pgc_service" in include_services:
            tasks.append(self._get_pgc_confidence(decision_context, principle_ids))
        
        if "integrity_service" in include_services:
            tasks.append(self._get_integrity_confidence(decision_context, principle_ids))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        service_index = 0
        for service in include_services:
            if service_index < len(results):
                result = results[service_index]
                if not isinstance(result, Exception):
                    self._update_confidence_metrics(confidence_metrics, service, result)
                else:
                    logger.warning(f"Failed to get confidence from {service}: {result}")
                    self.integration_metrics["service_availability"][service] = False
                service_index += 1
        
        return confidence_metrics
    
    async def _get_gs_confidence(
        self,
        decision_context: Dict[str, Any],
        principle_ids: Optional[List[int]]
    ) -> Dict[str, float]:
        """Get confidence metrics from GS Service."""
        try:
            request_data = {
                "context": decision_context.get("context", ""),
                "principle_ids": principle_ids or [],
                "synthesis_type": "constitutional_synthesis"
            }
            
            response = await self.http_client.post(
                f"{self.gs_service_url}/api/v1/llm-reliability/confidence-assessment",
                json=request_data,
                timeout=10.0
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "llm_confidence": data.get("llm_confidence", 0.5),
                "synthesis_confidence": data.get("synthesis_confidence", 0.5),
                "reliability_score": data.get("reliability_score", 0.5)
            }
            
        except Exception as e:
            logger.warning(f"GS Service confidence assessment failed: {e}")
            self.integration_metrics["service_availability"]["gs_service"] = False
            return {"llm_confidence": 0.5, "synthesis_confidence": 0.5}
    
    async def _get_fv_confidence(
        self,
        decision_context: Dict[str, Any],
        principle_ids: Optional[List[int]]
    ) -> Dict[str, float]:
        """Get confidence metrics from FV Service."""
        try:
            request_data = {
                "policy_context": decision_context,
                "principle_ids": principle_ids or [],
                "bias_metrics": ["demographic_parity", "equalized_odds"]
            }
            
            response = await self.http_client.post(
                f"{self.fv_service_url}/api/v1/bias-detection/confidence-assessment",
                json=request_data,
                timeout=10.0
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "bias_confidence": data.get("bias_confidence", 0.5),
                "fairness_confidence": data.get("fairness_confidence", 0.5),
                "validation_confidence": data.get("validation_confidence", 0.5)
            }
            
        except Exception as e:
            logger.warning(f"FV Service confidence assessment failed: {e}")
            self.integration_metrics["service_availability"]["fv_service"] = False
            return {"bias_confidence": 0.5, "fairness_confidence": 0.5}
    
    async def _get_pgc_confidence(
        self,
        decision_context: Dict[str, Any],
        principle_ids: Optional[List[int]]
    ) -> Dict[str, float]:
        """Get confidence metrics from PGC Service."""
        try:
            request_data = {
                "policy_context": decision_context,
                "principle_ids": principle_ids or [],
                "compilation_target": "rego"
            }
            
            response = await self.http_client.post(
                f"{self.pgc_service_url}/api/v1/compilation/confidence-assessment",
                json=request_data,
                timeout=10.0
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "enforcement_confidence": data.get("enforcement_confidence", 0.5),
                "compilation_confidence": data.get("compilation_confidence", 0.5),
                "policy_confidence": data.get("policy_confidence", 0.5)
            }
            
        except Exception as e:
            logger.warning(f"PGC Service confidence assessment failed: {e}")
            self.integration_metrics["service_availability"]["pgc_service"] = False
            return {"enforcement_confidence": 0.5, "compilation_confidence": 0.5}
    
    async def _get_integrity_confidence(
        self,
        decision_context: Dict[str, Any],
        principle_ids: Optional[List[int]]
    ) -> Dict[str, float]:
        """Get confidence metrics from Integrity Service."""
        try:
            request_data = {
                "verification_context": decision_context,
                "principle_ids": principle_ids or [],
                "verification_type": "constitutional_integrity"
            }
            
            response = await self.http_client.post(
                f"{self.integrity_service_url}/api/v1/verification/confidence-assessment",
                json=request_data,
                timeout=10.0
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "verification_confidence": data.get("verification_confidence", 0.5),
                "cryptographic_confidence": data.get("cryptographic_confidence", 0.5),
                "integrity_confidence": data.get("integrity_confidence", 0.5)
            }
            
        except Exception as e:
            logger.warning(f"Integrity Service confidence assessment failed: {e}")
            self.integration_metrics["service_availability"]["integrity_service"] = False
            return {"verification_confidence": 0.5, "cryptographic_confidence": 0.5}
    
    def _update_confidence_metrics(
        self,
        confidence_metrics: CrossServiceConfidenceMetrics,
        service: str,
        result: Dict[str, float]
    ):
        """Update confidence metrics with service results."""
        if service == "gs_service":
            confidence_metrics.gs_llm_confidence = result.get("llm_confidence")
            confidence_metrics.gs_synthesis_confidence = result.get("synthesis_confidence")
        elif service == "fv_service":
            confidence_metrics.fv_bias_confidence = result.get("bias_confidence")
            confidence_metrics.fv_fairness_confidence = result.get("fairness_confidence")
        elif service == "pgc_service":
            confidence_metrics.pgc_enforcement_confidence = result.get("enforcement_confidence")
            confidence_metrics.pgc_compilation_confidence = result.get("compilation_confidence")
        elif service == "integrity_service":
            confidence_metrics.integrity_verification_confidence = result.get("verification_confidence")
            confidence_metrics.integrity_cryptographic_confidence = result.get("cryptographic_confidence")
    
    def _update_avg_integration_time(self, processing_time_ms: float):
        """Update average integration time metric."""
        current_avg = self.integration_metrics["avg_integration_time_ms"]
        total_assessments = self.integration_metrics["total_cross_service_assessments"]
        
        # Calculate new average
        new_avg = ((current_avg * (total_assessments - 1)) + processing_time_ms) / total_assessments
        self.integration_metrics["avg_integration_time_ms"] = new_avg
    
    async def coordinate_cross_service_oversight(
        self,
        assessment: UncertaintyAssessment,
        confidence_metrics: CrossServiceConfidenceMetrics,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Coordinate human oversight across all relevant services.
        
        Args:
            assessment: Uncertainty assessment result
            confidence_metrics: Cross-service confidence metrics
            user_id: User ID for oversight context
            
        Returns:
            Coordination result with service-specific oversight actions
        """
        try:
            if not assessment.requires_human_oversight:
                return {"oversight_required": False, "services_notified": []}
            
            # Determine which services need oversight coordination
            services_to_notify = []
            
            if confidence_metrics.gs_llm_confidence and confidence_metrics.gs_llm_confidence < 0.7:
                services_to_notify.append("gs_service")
            
            if confidence_metrics.fv_bias_confidence and confidence_metrics.fv_bias_confidence < 0.7:
                services_to_notify.append("fv_service")
            
            if confidence_metrics.pgc_enforcement_confidence and confidence_metrics.pgc_enforcement_confidence < 0.7:
                services_to_notify.append("pgc_service")
            
            if confidence_metrics.integrity_verification_confidence and confidence_metrics.integrity_verification_confidence < 0.7:
                services_to_notify.append("integrity_service")
            
            # Notify relevant services about oversight requirement
            notification_results = await self._notify_services_of_oversight(
                services_to_notify, assessment, user_id
            )
            
            return {
                "oversight_required": True,
                "oversight_level": assessment.recommended_oversight_level.value,
                "services_notified": services_to_notify,
                "notification_results": notification_results,
                "coordination_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cross-service oversight coordination failed: {e}")
            return {"error": str(e), "oversight_required": True}
    
    async def _notify_services_of_oversight(
        self,
        services: List[str],
        assessment: UncertaintyAssessment,
        user_id: Optional[int]
    ) -> Dict[str, bool]:
        """Notify services about oversight requirement."""
        notification_results = {}
        
        oversight_notification = {
            "assessment_id": assessment.decision_id,
            "oversight_level": assessment.recommended_oversight_level.value,
            "triggers": [trigger.value for trigger in assessment.triggers_activated],
            "uncertainty_score": assessment.overall_uncertainty,
            "confidence_score": assessment.confidence_score,
            "user_id": user_id,
            "timestamp": assessment.timestamp.isoformat()
        }
        
        for service in services:
            try:
                service_url = getattr(self, f"{service}_url")
                response = await self.http_client.post(
                    f"{service_url}/api/v1/oversight/notification",
                    json=oversight_notification,
                    timeout=5.0
                )
                response.raise_for_status()
                notification_results[service] = True
                
            except Exception as e:
                logger.warning(f"Failed to notify {service} of oversight: {e}")
                notification_results[service] = False
        
        return notification_results
    
    async def get_integration_metrics(self) -> Dict[str, Any]:
        """Get cross-service integration metrics."""
        return {
            **self.integration_metrics,
            "success_rate": (
                self.integration_metrics["successful_integrations"] / 
                max(1, self.integration_metrics["total_cross_service_assessments"])
            ),
            "service_availability_rate": sum(
                1 for available in self.integration_metrics["service_availability"].values() 
                if available
            ) / len(self.integration_metrics["service_availability"])
        }
    
    async def close(self):
        """Close HTTP client and cleanup resources."""
        await self.http_client.aclose()
        logger.info("HITL Cross-Service Integrator closed")
