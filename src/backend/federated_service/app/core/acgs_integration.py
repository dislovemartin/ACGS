"""
ACGS-PGP Service Integration for Federated Evaluation Framework

Provides integration layer between federated evaluation framework and
all 6 ACGS-PGP microservices for seamless policy validation workflows.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import httpx
from enum import Enum

from .federated_evaluator import FederatedEvaluator, EvaluationTask, EvaluationStatus
from .cross_platform_coordinator import CrossPlatformCoordinator
from shared.auth import get_auth_headers, get_service_token
from shared.metrics import get_metrics

logger = logging.getLogger(__name__)


class ACGSServiceType(Enum):
    """ACGS-PGP service types for integration."""
    AUTH = "auth_service"
    AC = "ac_service"
    INTEGRITY = "integrity_service"
    FV = "fv_service"
    GS = "gs_service"
    PGC = "pgc_service"


@dataclass
class ACGSServiceConfig:
    """Configuration for ACGS-PGP service integration."""
    service_type: ACGSServiceType
    base_url: str
    api_version: str = "v1"
    timeout_seconds: float = 30.0
    retry_attempts: int = 3
    health_check_endpoint: str = "/health"
    
    @property
    def api_base_url(self) -> str:
        """Get the full API base URL."""
        return f"{self.base_url}/api/{self.api_version}"


@dataclass
class ACGSIntegrationRequest:
    """Request for ACGS-PGP service integration with federated evaluation."""
    evaluation_task_id: str
    target_services: List[ACGSServiceType]
    policy_content: str
    evaluation_criteria: Dict[str, Any]
    integration_context: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # low, normal, high, critical
    
    # Service-specific parameters
    ac_principles: Optional[List[str]] = None
    gs_constitutional_prompting: bool = True
    fv_verification_level: str = "standard"  # basic, standard, comprehensive
    integrity_signature_required: bool = True
    pgc_enforcement_mode: str = "advisory"  # advisory, enforcing


@dataclass
class ACGSIntegrationResult:
    """Result from ACGS-PGP service integration."""
    request_id: str
    success: bool
    
    # Service-specific results
    service_results: Dict[ACGSServiceType, Dict[str, Any]] = field(default_factory=dict)
    
    # Integration metrics
    total_execution_time_ms: float = 0.0
    service_response_times: Dict[ACGSServiceType, float] = field(default_factory=dict)
    
    # Federated evaluation results
    federated_evaluation_result: Optional[Dict[str, Any]] = None
    
    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ACGSServiceIntegrator:
    """
    Integrates federated evaluation framework with ACGS-PGP microservices.
    
    Provides seamless integration between federated evaluation and all 6 ACGS-PGP
    services for comprehensive policy validation workflows.
    """
    
    def __init__(self):
        self.service_configs: Dict[ACGSServiceType, ACGSServiceConfig] = {}
        self.federated_evaluator: Optional[FederatedEvaluator] = None
        self.cross_platform_coordinator: Optional[CrossPlatformCoordinator] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Integration metrics
        self.integration_metrics = {
            "total_integrations": 0,
            "successful_integrations": 0,
            "failed_integrations": 0,
            "avg_integration_time_ms": 0.0,
            "service_availability": {}
        }
        
        self._initialized = False
    
    async def initialize(self, service_configs: Optional[Dict[ACGSServiceType, ACGSServiceConfig]] = None):
        """Initialize the ACGS service integrator."""
        try:
            # Set up default service configurations
            if service_configs:
                self.service_configs = service_configs
            else:
                self._setup_default_service_configs()
            
            # Initialize federated evaluator
            self.federated_evaluator = FederatedEvaluator()
            await self.federated_evaluator.initialize()
            
            # Initialize cross-platform coordinator
            self.cross_platform_coordinator = CrossPlatformCoordinator()
            await self.cross_platform_coordinator.initialize()
            
            # Initialize HTTP client
            self.http_client = httpx.AsyncClient(timeout=30.0)
            
            # Test service connectivity
            await self._test_service_connectivity()
            
            self._initialized = True
            logger.info("ACGS service integrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ACGS service integrator: {e}")
            raise
    
    def _setup_default_service_configs(self):
        """Set up default ACGS service configurations."""
        default_configs = {
            ACGSServiceType.AUTH: ACGSServiceConfig(
                service_type=ACGSServiceType.AUTH,
                base_url="http://localhost:8000"
            ),
            ACGSServiceType.AC: ACGSServiceConfig(
                service_type=ACGSServiceType.AC,
                base_url="http://localhost:8001"
            ),
            ACGSServiceType.INTEGRITY: ACGSServiceConfig(
                service_type=ACGSServiceType.INTEGRITY,
                base_url="http://localhost:8002"
            ),
            ACGSServiceType.FV: ACGSServiceConfig(
                service_type=ACGSServiceType.FV,
                base_url="http://localhost:8003"
            ),
            ACGSServiceType.GS: ACGSServiceConfig(
                service_type=ACGSServiceType.GS,
                base_url="http://localhost:8004"
            ),
            ACGSServiceType.PGC: ACGSServiceConfig(
                service_type=ACGSServiceType.PGC,
                base_url="http://localhost:8005"
            )
        }
        
        self.service_configs = default_configs
    
    async def _test_service_connectivity(self):
        """Test connectivity to all ACGS services."""
        connectivity_results = {}
        
        for service_type, config in self.service_configs.items():
            try:
                response = await self.http_client.get(
                    f"{config.base_url}{config.health_check_endpoint}",
                    timeout=5.0
                )
                connectivity_results[service_type] = {
                    "available": response.status_code in [200, 404],  # 404 acceptable for some endpoints
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            except Exception as e:
                connectivity_results[service_type] = {
                    "available": False,
                    "error": str(e)
                }
        
        # Update availability metrics
        for service_type, result in connectivity_results.items():
            self.integration_metrics["service_availability"][service_type.value] = result["available"]
        
        available_services = sum(1 for result in connectivity_results.values() if result["available"])
        total_services = len(connectivity_results)
        
        logger.info(f"ACGS service connectivity: {available_services}/{total_services} services available")
        
        # Log individual service status
        for service_type, result in connectivity_results.items():
            if result["available"]:
                logger.info(f"✅ {service_type.value}: Available ({result.get('response_time_ms', 0):.1f}ms)")
            else:
                logger.warning(f"❌ {service_type.value}: Unavailable - {result.get('error', 'Unknown error')}")
    
    async def submit_integration_request(self, request: ACGSIntegrationRequest) -> str:
        """Submit an ACGS integration request with federated evaluation."""
        if not self._initialized:
            raise RuntimeError("ACGS service integrator not initialized")
        
        try:
            start_time = time.time()
            
            # Create federated evaluation task
            federated_task = type('FederatedTask', (), {
                'policy_content': request.policy_content,
                'evaluation_criteria': {
                    **request.evaluation_criteria,
                    'acgs_integration': True,
                    'target_services': [s.value for s in request.target_services],
                    'integration_context': request.integration_context
                },
                'target_platforms': request.integration_context.get('target_platforms', []),
                'privacy_requirements': request.integration_context.get('privacy_requirements', {})
            })()
            
            # Submit to federated evaluator
            task_id = await self.federated_evaluator.submit_evaluation(federated_task)
            
            # Update metrics
            self.integration_metrics["total_integrations"] += 1
            
            logger.info(f"ACGS integration request submitted: {task_id}")
            return task_id
            
        except Exception as e:
            self.integration_metrics["failed_integrations"] += 1
            logger.error(f"Failed to submit ACGS integration request: {e}")
            raise
    
    async def get_integration_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an ACGS integration request."""
        if not self._initialized:
            raise RuntimeError("ACGS service integrator not initialized")
        
        try:
            # Get federated evaluation status
            federated_status = await self.federated_evaluator.get_evaluation_status(task_id)
            
            if not federated_status:
                return None
            
            # Enhance with ACGS-specific status information
            acgs_status = {
                **federated_status,
                "acgs_integration": True,
                "service_availability": self.integration_metrics["service_availability"],
                "integration_metrics": {
                    "total_integrations": self.integration_metrics["total_integrations"],
                    "success_rate": self._calculate_success_rate()
                }
            }
            
            return acgs_status
            
        except Exception as e:
            logger.error(f"Failed to get ACGS integration status: {e}")
            return None
    
    def _calculate_success_rate(self) -> float:
        """Calculate integration success rate."""
        total = self.integration_metrics["total_integrations"]
        if total == 0:
            return 1.0
        
        successful = self.integration_metrics["successful_integrations"]
        return successful / total
    
    async def get_integration_metrics(self) -> Dict[str, Any]:
        """Get comprehensive ACGS integration metrics."""
        if not self._initialized:
            raise RuntimeError("ACGS service integrator not initialized")
        
        try:
            # Get federated evaluation metrics
            federated_metrics = await self.federated_evaluator.get_evaluation_metrics()
            
            # Combine with ACGS integration metrics
            combined_metrics = {
                "acgs_integration_metrics": self.integration_metrics,
                "federated_evaluation_metrics": federated_metrics,
                "service_configurations": {
                    service_type.value: {
                        "base_url": config.base_url,
                        "timeout_seconds": config.timeout_seconds,
                        "available": self.integration_metrics["service_availability"].get(service_type.value, False)
                    }
                    for service_type, config in self.service_configs.items()
                },
                "system_health": {
                    "integrator_initialized": self._initialized,
                    "federated_evaluator_ready": self.federated_evaluator is not None,
                    "cross_platform_coordinator_ready": self.cross_platform_coordinator is not None,
                    "http_client_ready": self.http_client is not None
                }
            }
            
            return combined_metrics
            
        except Exception as e:
            logger.error(f"Failed to get ACGS integration metrics: {e}")
            return {}
    
    async def shutdown(self):
        """Shutdown the ACGS service integrator."""
        try:
            if self.federated_evaluator:
                await self.federated_evaluator.shutdown()
            
            if self.cross_platform_coordinator:
                await self.cross_platform_coordinator.shutdown()
            
            if self.http_client:
                await self.http_client.aclose()
            
            self._initialized = False
            logger.info("ACGS service integrator shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during ACGS service integrator shutdown: {e}")


# Global ACGS service integrator instance
acgs_service_integrator = ACGSServiceIntegrator()
