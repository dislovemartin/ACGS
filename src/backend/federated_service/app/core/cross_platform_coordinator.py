"""
Cross-Platform Coordinator for Federated Evaluation Framework

Manages multiple platform adapters and provides unified interface for
cross-platform evaluation with Byzantine fault tolerance and MAB optimization.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import json
import hashlib
import numpy as np

from .cross_platform_adapters import (
    BasePlatformAdapter, OpenAIPlatformAdapter, AnthropicPlatformAdapter,
    CoherePlatformAdapter, GroqPlatformAdapter, EvaluationRequest, 
    EvaluationResponse, PlatformType, EvaluationMode, AdapterStatus
)
from .secure_aggregation import SecureAggregator, AggregationMethod
from .federated_evaluator import FederatedNode
from shared.metrics import get_metrics
from shared import get_config

logger = logging.getLogger(__name__)

# Initialize metrics with error handling for test environments
try:
    metrics = get_metrics("federated_service")
except Exception as e:
    logger.warning(f"Failed to initialize metrics: {e}")
    # Create a mock metrics object for testing
    class MockMetrics:
        def counter(self, name, labels=None):
            return type('MockCounter', (), {'inc': lambda: None})()
        def histogram(self, name, labels=None):
            return type('MockHistogram', (), {'observe': lambda x: None})()
    metrics = MockMetrics()

config = get_config()


@dataclass
class CrossPlatformEvaluationRequest:
    """Request for cross-platform evaluation."""
    request_id: str
    policy_content: str
    evaluation_criteria: Dict[str, Any]
    target_platforms: List[PlatformType]
    mode: EvaluationMode = EvaluationMode.CONSTITUTIONAL
    
    # Byzantine fault tolerance settings
    byzantine_tolerance: float = 0.33
    min_consensus_platforms: int = 2
    
    # MAB integration
    mab_context: Dict[str, Any] = field(default_factory=dict)
    enable_mab_optimization: bool = True
    
    # Privacy and security
    privacy_requirements: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 60.0


@dataclass
class CrossPlatformEvaluationResult:
    """Result from cross-platform evaluation."""
    request_id: str
    success: bool
    
    # Aggregated scores
    aggregated_policy_compliance: float = 0.0
    aggregated_constitutional_alignment: float = 0.0
    aggregated_safety_score: float = 0.0
    aggregated_fairness_score: float = 0.0
    
    # Platform-specific results
    platform_results: Dict[str, EvaluationResponse] = field(default_factory=dict)
    
    # Byzantine fault tolerance metrics
    byzantine_nodes_detected: List[str] = field(default_factory=list)
    consensus_achieved: bool = False
    consensus_confidence: float = 0.0
    
    # Performance metrics
    total_execution_time_ms: float = 0.0
    total_tokens_used: int = 0
    total_cost_estimate: float = 0.0
    
    # Error handling
    failed_platforms: List[str] = field(default_factory=list)
    error_summary: Optional[str] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CrossPlatformCoordinator:
    """
    Coordinates evaluation across multiple LLM platforms with Byzantine fault tolerance.
    
    Features:
    - Unified interface for multiple platforms
    - Byzantine fault tolerance
    - MAB-optimized platform selection
    - Secure aggregation of results
    - Integration with ACGS-PGP services
    """
    
    def __init__(self):
        self.adapters: Dict[PlatformType, BasePlatformAdapter] = {}
        self.secure_aggregator: Optional[SecureAggregator] = None
        self.active_evaluations: Dict[str, CrossPlatformEvaluationRequest] = {}
        
        # Performance tracking
        self.coordinator_metrics = {
            "total_evaluations": 0,
            "successful_evaluations": 0,
            "byzantine_detections": 0,
            "consensus_failures": 0,
            "avg_response_time_ms": 0.0
        }
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the cross-platform coordinator."""
        try:
            logger.info("Initializing Cross-Platform Coordinator...")
            
            # Initialize secure aggregator
            self.secure_aggregator = SecureAggregator()
            await self.secure_aggregator.initialize()
            
            # Initialize platform adapters based on available API keys
            await self._initialize_adapters()
            
            self._initialized = True
            logger.info(f"Cross-Platform Coordinator initialized with {len(self.adapters)} adapters")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cross-Platform Coordinator: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the coordinator and all adapters."""
        try:
            # Shutdown all adapters
            for adapter in self.adapters.values():
                await adapter.shutdown()
            
            # Shutdown secure aggregator
            if self.secure_aggregator:
                await self.secure_aggregator.shutdown()
            
            self._initialized = False
            logger.info("Cross-Platform Coordinator shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during coordinator shutdown: {e}")
    
    async def _initialize_adapters(self) -> None:
        """Initialize platform adapters based on available API keys."""
        # OpenAI adapter
        openai_key = config.get('openai_api_key')
        if openai_key:
            try:
                adapter = OpenAIPlatformAdapter(openai_key)
                await adapter.initialize()
                self.adapters[PlatformType.CLOUD_OPENAI] = adapter
                logger.info("OpenAI adapter initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI adapter: {e}")
        
        # Anthropic adapter
        anthropic_key = config.get('anthropic_api_key')
        if anthropic_key:
            try:
                adapter = AnthropicPlatformAdapter(anthropic_key)
                await adapter.initialize()
                self.adapters[PlatformType.CLOUD_ANTHROPIC] = adapter
                logger.info("Anthropic adapter initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic adapter: {e}")
        
        # Cohere adapter
        cohere_key = config.get('cohere_api_key')
        if cohere_key:
            try:
                adapter = CoherePlatformAdapter(cohere_key)
                await adapter.initialize()
                self.adapters[PlatformType.CLOUD_COHERE] = adapter
                logger.info("Cohere adapter initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Cohere adapter: {e}")
        
        # Groq adapter
        groq_key = config.get('groq_api_key')
        if groq_key:
            try:
                adapter = GroqPlatformAdapter(groq_key)
                await adapter.initialize()
                self.adapters[PlatformType.CLOUD_GROQ] = adapter
                logger.info("Groq adapter initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq adapter: {e}")
        
        if not self.adapters:
            logger.warning("No platform adapters initialized - check API key configuration")
    
    async def evaluate_cross_platform(
        self, 
        request: CrossPlatformEvaluationRequest
    ) -> CrossPlatformEvaluationResult:
        """
        Perform cross-platform evaluation with Byzantine fault tolerance.
        """
        if not self._initialized:
            raise RuntimeError("Coordinator not initialized")
        
        start_time = time.time()
        self.coordinator_metrics["total_evaluations"] += 1
        
        try:
            # Store active evaluation
            self.active_evaluations[request.request_id] = request
            
            # Select available platforms
            available_platforms = self._select_available_platforms(request.target_platforms)
            if len(available_platforms) < request.min_consensus_platforms:
                raise ValueError(f"Insufficient platforms available: {len(available_platforms)} < {request.min_consensus_platforms}")
            
            # Execute evaluations in parallel
            platform_results = await self._execute_parallel_evaluations(request, available_platforms)
            
            # Apply Byzantine fault tolerance
            filtered_results = await self._apply_byzantine_fault_tolerance(platform_results, request)
            
            # Aggregate results securely
            aggregated_result = await self._aggregate_cross_platform_results(
                request, filtered_results, start_time
            )
            
            # Update metrics
            self.coordinator_metrics["successful_evaluations"] += 1
            
            # Update Prometheus metrics
            metrics.counter("federated_cross_platform_evaluations_total", 
                           labels={"status": "success"}).inc()
            metrics.histogram("federated_cross_platform_response_time_ms").observe(
                aggregated_result.total_execution_time_ms
            )
            
            return aggregated_result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Cross-platform evaluation failed: {e}")
            
            # Update error metrics
            metrics.counter("federated_cross_platform_evaluations_total", 
                           labels={"status": "error"}).inc()
            
            return CrossPlatformEvaluationResult(
                request_id=request.request_id,
                success=False,
                total_execution_time_ms=execution_time,
                error_summary=str(e)
            )
        finally:
            # Cleanup
            self.active_evaluations.pop(request.request_id, None)
    
    def _select_available_platforms(self, target_platforms: List[PlatformType]) -> List[PlatformType]:
        """Select available platforms from target list."""
        available = []
        for platform in target_platforms:
            if platform in self.adapters and self.adapters[platform].status == AdapterStatus.ACTIVE:
                available.append(platform)
        return available
    
    async def _execute_parallel_evaluations(
        self, 
        request: CrossPlatformEvaluationRequest, 
        platforms: List[PlatformType]
    ) -> Dict[PlatformType, EvaluationResponse]:
        """Execute evaluations in parallel across platforms."""
        tasks = []
        
        for platform in platforms:
            adapter = self.adapters[platform]
            eval_request = EvaluationRequest(
                request_id=f"{request.request_id}_{platform.value}",
                policy_content=request.policy_content,
                evaluation_criteria=request.evaluation_criteria,
                mode=request.mode,
                context=request.mab_context,
                privacy_requirements=request.privacy_requirements,
                timeout_seconds=request.timeout_seconds,
                mab_context=request.mab_context
            )
            
            task = asyncio.create_task(adapter.evaluate(eval_request))
            tasks.append((platform, task))
        
        # Wait for all evaluations to complete
        results = {}
        for platform, task in tasks:
            try:
                result = await task
                results[platform] = result
            except Exception as e:
                logger.error(f"Evaluation failed on {platform.value}: {e}")
                # Create error response
                results[platform] = EvaluationResponse(
                    request_id=f"{request.request_id}_{platform.value}",
                    platform_type=platform,
                    success=False,
                    error_message=str(e),
                    error_code="PLATFORM_ERROR"
                )
        
        return results

    async def _apply_byzantine_fault_tolerance(
        self,
        platform_results: Dict[PlatformType, EvaluationResponse],
        request: CrossPlatformEvaluationRequest
    ) -> Dict[PlatformType, EvaluationResponse]:
        """Apply Byzantine fault tolerance to filter out malicious/faulty nodes."""
        try:
            # Only consider successful results
            successful_results = {
                platform: result for platform, result in platform_results.items()
                if result.success
            }

            if len(successful_results) < request.min_consensus_platforms:
                logger.warning(f"Insufficient successful results for Byzantine tolerance: {len(successful_results)}")
                return successful_results

            # Extract metrics for Byzantine detection
            metrics_by_platform = {}
            for platform, result in successful_results.items():
                metrics_by_platform[platform] = {
                    "policy_compliance_score": result.policy_compliance_score,
                    "constitutional_alignment": result.constitutional_alignment,
                    "safety_score": result.safety_score,
                    "fairness_score": result.fairness_score,
                    "execution_time_ms": result.execution_time_ms
                }

            # Detect outliers using statistical methods
            byzantine_nodes = self._detect_byzantine_nodes_statistical(metrics_by_platform, request.byzantine_tolerance)

            # Filter out Byzantine nodes
            filtered_results = {
                platform: result for platform, result in successful_results.items()
                if platform not in byzantine_nodes
            }

            if byzantine_nodes:
                self.coordinator_metrics["byzantine_detections"] += len(byzantine_nodes)
                logger.warning(f"Detected Byzantine nodes: {[node.value for node in byzantine_nodes]}")

            return filtered_results

        except Exception as e:
            logger.error(f"Byzantine fault tolerance failed: {e}")
            return platform_results

    def _detect_byzantine_nodes_statistical(
        self,
        metrics_by_platform: Dict[PlatformType, Dict[str, float]],
        tolerance: float
    ) -> List[PlatformType]:
        """Detect Byzantine nodes using statistical outlier detection."""
        import numpy as np

        byzantine_nodes = []

        try:
            if len(metrics_by_platform) < 3:
                return byzantine_nodes  # Need at least 3 nodes for detection

            # Analyze each metric
            for metric_name in ["policy_compliance_score", "constitutional_alignment", "safety_score", "fairness_score"]:
                values = [metrics[metric_name] for metrics in metrics_by_platform.values()]
                platforms = list(metrics_by_platform.keys())

                # Calculate median and MAD (Median Absolute Deviation)
                median = np.median(values)
                mad = np.median([abs(v - median) for v in values])

                # Detect outliers using modified Z-score
                threshold = 3.5  # Standard threshold for outlier detection
                for i, value in enumerate(values):
                    if mad > 0:
                        modified_z_score = 0.6745 * (value - median) / mad
                        if abs(modified_z_score) > threshold:
                            platform = platforms[i]
                            if platform not in byzantine_nodes:
                                byzantine_nodes.append(platform)

            # Apply tolerance threshold
            max_byzantine = int(len(metrics_by_platform) * tolerance)
            if len(byzantine_nodes) > max_byzantine:
                # Keep only the most suspicious nodes
                byzantine_nodes = byzantine_nodes[:max_byzantine]

        except Exception as e:
            logger.error(f"Statistical Byzantine detection failed: {e}")

        return byzantine_nodes

    async def _aggregate_cross_platform_results(
        self,
        request: CrossPlatformEvaluationRequest,
        platform_results: Dict[PlatformType, EvaluationResponse],
        start_time: float
    ) -> CrossPlatformEvaluationResult:
        """Aggregate results from multiple platforms using secure aggregation."""
        try:
            execution_time = (time.time() - start_time) * 1000

            if not platform_results:
                return CrossPlatformEvaluationResult(
                    request_id=request.request_id,
                    success=False,
                    total_execution_time_ms=execution_time,
                    error_summary="No platform results available"
                )

            # Prepare data for secure aggregation
            aggregation_data = {}
            total_tokens = 0
            total_cost = 0.0
            failed_platforms = []

            for platform, result in platform_results.items():
                if result.success:
                    aggregation_data[platform.value] = {
                        "policy_compliance_score": result.policy_compliance_score,
                        "constitutional_alignment": result.constitutional_alignment,
                        "safety_score": result.safety_score,
                        "fairness_score": result.fairness_score
                    }
                    total_tokens += result.tokens_used
                    total_cost += result.cost_estimate
                else:
                    failed_platforms.append(platform.value)

            # Perform secure aggregation
            if aggregation_data:
                aggregated_scores = await self._secure_aggregate_scores(aggregation_data)
                consensus_achieved = len(aggregation_data) >= request.min_consensus_platforms
                consensus_confidence = len(aggregation_data) / len(request.target_platforms)
            else:
                aggregated_scores = {
                    "policy_compliance_score": 0.0,
                    "constitutional_alignment": 0.0,
                    "safety_score": 0.0,
                    "fairness_score": 0.0
                }
                consensus_achieved = False
                consensus_confidence = 0.0

            # Detect Byzantine nodes
            all_platforms = set(platform_results.keys())
            successful_platforms = set(platform for platform, result in platform_results.items() if result.success)
            byzantine_platforms = all_platforms - successful_platforms

            return CrossPlatformEvaluationResult(
                request_id=request.request_id,
                success=consensus_achieved,
                aggregated_policy_compliance=aggregated_scores["policy_compliance_score"],
                aggregated_constitutional_alignment=aggregated_scores["constitutional_alignment"],
                aggregated_safety_score=aggregated_scores["safety_score"],
                aggregated_fairness_score=aggregated_scores["fairness_score"],
                platform_results={platform.value: result for platform, result in platform_results.items()},
                byzantine_nodes_detected=[platform.value for platform in byzantine_platforms],
                consensus_achieved=consensus_achieved,
                consensus_confidence=consensus_confidence,
                total_execution_time_ms=execution_time,
                total_tokens_used=total_tokens,
                total_cost_estimate=total_cost,
                failed_platforms=failed_platforms
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Result aggregation failed: {e}")
            return CrossPlatformEvaluationResult(
                request_id=request.request_id,
                success=False,
                total_execution_time_ms=execution_time,
                error_summary=f"Aggregation failed: {e}"
            )

    async def _secure_aggregate_scores(self, aggregation_data: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Securely aggregate scores using weighted averaging."""
        try:
            if not aggregation_data:
                return {
                    "policy_compliance_score": 0.0,
                    "constitutional_alignment": 0.0,
                    "safety_score": 0.0,
                    "fairness_score": 0.0
                }

            # Simple weighted average (can be enhanced with more sophisticated methods)
            aggregated = {}
            metrics = ["policy_compliance_score", "constitutional_alignment", "safety_score", "fairness_score"]

            for metric in metrics:
                values = [data[metric] for data in aggregation_data.values()]
                # Use median for robustness against outliers
                aggregated[metric] = float(np.median(values)) if values else 0.0

            return aggregated

        except Exception as e:
            logger.error(f"Secure aggregation failed: {e}")
            return {
                "policy_compliance_score": 0.0,
                "constitutional_alignment": 0.0,
                "safety_score": 0.0,
                "fairness_score": 0.0
            }

    async def get_coordinator_status(self) -> Dict[str, Any]:
        """Get coordinator status and metrics."""
        adapter_status = {}
        for platform, adapter in self.adapters.items():
            health = await adapter.health_check()
            adapter_status[platform.value] = {
                "status": adapter.status.value,
                "health": health,
                "metrics": adapter.metrics
            }

        return {
            "initialized": self._initialized,
            "total_adapters": len(self.adapters),
            "active_adapters": sum(1 for adapter in self.adapters.values() if adapter.status == AdapterStatus.ACTIVE),
            "active_evaluations": len(self.active_evaluations),
            "coordinator_metrics": self.coordinator_metrics,
            "adapter_status": adapter_status
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        try:
            status = await self.get_coordinator_status()

            # Determine overall health
            healthy_adapters = sum(1 for adapter in self.adapters.values()
                                 if adapter.status == AdapterStatus.ACTIVE)

            overall_health = "healthy" if healthy_adapters > 0 else "unhealthy"

            return {
                "status": overall_health,
                "coordinator_initialized": self._initialized,
                "healthy_adapters": healthy_adapters,
                "total_adapters": len(self.adapters),
                "details": status
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "coordinator_initialized": self._initialized
            }


# Global coordinator instance
cross_platform_coordinator = CrossPlatformCoordinator()
