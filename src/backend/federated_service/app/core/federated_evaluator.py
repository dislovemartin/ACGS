"""
Federated Evaluation Framework for ACGS-PGP

Implements cross-platform validation of constitutional AI policies across
different environments while integrating with the Multi-Armed Bandit (MAB)
prompt optimization system from Task 5.

Based on Task 6 requirements and AlphaEvolve-ACGS Integration System research.
"""

import asyncio
import logging
import time
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from datetime import datetime, timezone
from abc import ABC, abstractmethod

# Core dependencies
from shared.database import get_async_db
from shared.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Supported platform types for federated evaluation."""
    CLOUD_OPENAI = "cloud_openai"
    CLOUD_ANTHROPIC = "cloud_anthropic" 
    CLOUD_COHERE = "cloud_cohere"
    CLOUD_GROQ = "cloud_groq"
    EDGE_LOCAL = "edge_local"
    FEDERATED_NODE = "federated_node"


class EvaluationStatus(Enum):
    """Status of federated evaluation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    AGGREGATING = "aggregating"


@dataclass
class FederatedNode:
    """Federated evaluation node configuration."""
    node_id: str
    platform_type: PlatformType
    endpoint_url: str
    api_key: Optional[str] = None
    capabilities: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # MAB integration
    mab_template_preferences: Dict[str, float] = field(default_factory=dict)
    prompt_optimization_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EvaluationTask:
    """Individual evaluation task for federated execution."""
    task_id: str
    policy_content: str
    evaluation_criteria: Dict[str, Any]
    target_platforms: List[PlatformType]
    mab_context: Dict[str, Any]
    privacy_requirements: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: EvaluationStatus = EvaluationStatus.PENDING
    results: Dict[str, Any] = field(default_factory=dict)


class FederatedEvaluator:
    """
    Core federated evaluation framework that coordinates policy validation
    across multiple platforms while preserving privacy and integrating with MAB optimization.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.nodes: Dict[str, FederatedNode] = {}
        self.active_evaluations: Dict[str, EvaluationTask] = {}
        self.secure_aggregator = None  # Will be initialized later
        self.privacy_manager = None  # Will be initialized later
        
        # MAB integration
        self.mab_client = None  # Will be initialized with GS service client
        self.template_performance_cache = {}
        
        # Performance tracking
        self.evaluation_metrics = {
            "total_evaluations": 0,
            "successful_evaluations": 0,
            "failed_evaluations": 0,
            "average_response_time": 0.0,
            "cross_platform_consistency": 0.0,
            "privacy_preservation_score": 0.0
        }
        
        logger.info("Initialized Federated Evaluator")
    
    async def initialize(self):
        """Initialize the federated evaluator."""
        try:
            # Import here to avoid circular imports
            from .secure_aggregation import SecureAggregator
            from .privacy_metrics import DifferentialPrivacyManager

            # Initialize components
            self.secure_aggregator = SecureAggregator()
            self.privacy_manager = DifferentialPrivacyManager(epsilon=1.0)

            # Initialize secure aggregator
            await self.secure_aggregator.initialize()

            # Initialize privacy manager
            await self.privacy_manager.initialize()

            # Initialize MAB client connection to GS service
            await self._initialize_mab_client()

            # Load existing nodes from database
            await self._load_federated_nodes()

            logger.info("Federated Evaluator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Federated Evaluator: {e}")
            raise
    
    async def _initialize_mab_client(self):
        """Initialize connection to GS service MAB system."""
        try:
            import httpx
            
            # Create HTTP client for GS service communication
            self.mab_client = httpx.AsyncClient(
                base_url="http://gs_service:8004",
                timeout=30.0
            )
            
            # Test connection
            response = await self.mab_client.get("/health")
            if response.status_code == 200:
                logger.info("MAB client connection established")
            else:
                logger.warning("MAB client connection test failed")
                
        except Exception as e:
            logger.error(f"Failed to initialize MAB client: {e}")
            # Continue without MAB integration for now
            self.mab_client = None
    
    async def register_node(self, node_config: Any) -> str:
        """Register a new federated evaluation node."""
        try:
            node_id = f"{node_config.platform_type.value}_{int(time.time())}"
            
            node = FederatedNode(
                node_id=node_id,
                platform_type=node_config.platform_type,
                endpoint_url=node_config.endpoint_url,
                api_key=node_config.api_key,
                capabilities=node_config.capabilities,
                status="active"
            )
            
            self.nodes[node_id] = node
            
            # Store in database
            await self._store_node_config(node)
            
            logger.info(f"Registered federated node: {node_id} ({node_config.platform_type.value})")
            return node_id
            
        except Exception as e:
            logger.error(f"Failed to register node: {e}")
            raise
    
    async def submit_evaluation(self, request: Any) -> str:
        """Submit a new federated evaluation task."""
        try:
            task_id = hashlib.md5(f"{request.policy_content}_{time.time()}".encode()).hexdigest()[:16]
            
            # Get MAB-optimized context if available
            mab_context = await self._get_mab_context(request)
            
            task = EvaluationTask(
                task_id=task_id,
                policy_content=request.policy_content,
                evaluation_criteria=request.evaluation_criteria,
                target_platforms=request.target_platforms,
                mab_context=mab_context,
                privacy_requirements=request.privacy_requirements
            )
            
            self.active_evaluations[task_id] = task
            
            # Start evaluation asynchronously
            asyncio.create_task(self._execute_federated_evaluation(task))
            
            logger.info(f"Submitted federated evaluation: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit evaluation: {e}")
            raise
    
    async def _get_mab_context(self, request: Any) -> Dict[str, Any]:
        """Get MAB-optimized context for evaluation."""
        mab_context = {
            "category": request.evaluation_criteria.get("category", "constitutional"),
            "safety_level": request.evaluation_criteria.get("safety_level", "standard"),
            "target_platforms": [p.value for p in request.target_platforms],
            "optimization_enabled": self.mab_client is not None
        }
        
        if self.mab_client:
            try:
                # Get optimal prompt template from MAB system
                response = await self.mab_client.post(
                    "/api/v1/mab/select-template",
                    json={"context": mab_context}
                )
                
                if response.status_code == 200:
                    template_data = response.json()
                    mab_context["selected_template"] = template_data
                    logger.debug(f"MAB template selected: {template_data.get('template_id')}")
                    
            except Exception as e:
                logger.warning(f"Failed to get MAB context: {e}")
        
        return mab_context

    async def _execute_federated_evaluation(self, task: EvaluationTask):
        """Execute federated evaluation across multiple nodes."""
        try:
            task.status = EvaluationStatus.IN_PROGRESS
            start_time = time.time()

            # Select nodes for evaluation
            selected_nodes = await self._select_evaluation_nodes(task.target_platforms)
            if not selected_nodes:
                raise ValueError("No suitable nodes available for evaluation")

            # Distribute evaluation tasks
            node_tasks = []
            for node in selected_nodes:
                node_task = asyncio.create_task(
                    self._evaluate_on_node(node, task)
                )
                node_tasks.append((node.node_id, node_task))

            # Collect results with timeout
            node_results = {}
            for node_id, node_task in node_tasks:
                try:
                    result = await asyncio.wait_for(node_task, timeout=120.0)
                    node_results[node_id] = result
                except asyncio.TimeoutError:
                    logger.warning(f"Node {node_id} evaluation timed out")
                    node_results[node_id] = {"error": "timeout", "success": False}
                except Exception as e:
                    logger.error(f"Node {node_id} evaluation failed: {e}")
                    node_results[node_id] = {"error": str(e), "success": False}

            # Apply differential privacy to results
            private_results = await self.privacy_manager.apply_differential_privacy(
                node_results, task.privacy_requirements
            )

            # Secure aggregation of results
            task.status = EvaluationStatus.AGGREGATING
            aggregated_results = await self.secure_aggregator.aggregate_results(
                private_results, task.evaluation_criteria
            )

            # Update MAB system with performance feedback
            if self.mab_client and task.mab_context.get("selected_template"):
                await self._update_mab_performance(task, aggregated_results)

            # Store final results
            task.results = aggregated_results
            task.status = EvaluationStatus.COMPLETED

            # Update metrics
            execution_time = time.time() - start_time
            await self._update_evaluation_metrics(task, execution_time, True)

            logger.info(f"Federated evaluation completed: {task.task_id} in {execution_time:.2f}s")

        except Exception as e:
            task.status = EvaluationStatus.FAILED
            task.results = {"error": str(e), "success": False}

            execution_time = time.time() - start_time
            await self._update_evaluation_metrics(task, execution_time, False)

            logger.error(f"Federated evaluation failed: {task.task_id} - {e}")

    async def _select_evaluation_nodes(self, target_platforms: List[PlatformType]) -> List[FederatedNode]:
        """Select optimal nodes for evaluation based on platform requirements."""
        selected_nodes = []

        for platform in target_platforms:
            # Find active nodes for this platform
            platform_nodes = [
                node for node in self.nodes.values()
                if node.platform_type == platform and node.status == "active"
            ]

            if platform_nodes:
                # Select best performing node for this platform
                best_node = max(
                    platform_nodes,
                    key=lambda n: n.performance_metrics.get("success_rate", 0.0)
                )
                selected_nodes.append(best_node)
            else:
                logger.warning(f"No active nodes found for platform: {platform.value}")

        return selected_nodes

    async def _evaluate_on_node(self, node: FederatedNode, task: EvaluationTask) -> Dict[str, Any]:
        """Execute evaluation on a specific federated node."""
        try:
            # Prepare evaluation payload
            payload = {
                "policy_content": task.policy_content,
                "evaluation_criteria": task.evaluation_criteria,
                "mab_context": task.mab_context,
                "node_capabilities": node.capabilities
            }

            # Execute evaluation based on platform type
            if node.platform_type in [PlatformType.CLOUD_OPENAI, PlatformType.CLOUD_ANTHROPIC,
                                     PlatformType.CLOUD_COHERE, PlatformType.CLOUD_GROQ]:
                result = await self._evaluate_cloud_platform(node, payload)
            elif node.platform_type == PlatformType.EDGE_LOCAL:
                result = await self._evaluate_edge_platform(node, payload)
            elif node.platform_type == PlatformType.FEDERATED_NODE:
                result = await self._evaluate_federated_node(node, payload)
            else:
                raise ValueError(f"Unsupported platform type: {node.platform_type}")

            # Update node performance metrics
            await self._update_node_metrics(node, result)

            return result

        except Exception as e:
            logger.error(f"Evaluation failed on node {node.node_id}: {e}")
            return {"error": str(e), "success": False, "node_id": node.node_id}

    async def _evaluate_cloud_platform(self, node: FederatedNode, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate policy on cloud platform (OpenAI, Anthropic, etc.)."""
        try:
            import httpx

            # Create platform-specific client
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Add authentication headers
                headers = {}
                if node.api_key:
                    if node.platform_type == PlatformType.CLOUD_OPENAI:
                        headers["Authorization"] = f"Bearer {node.api_key}"
                    elif node.platform_type == PlatformType.CLOUD_ANTHROPIC:
                        headers["x-api-key"] = node.api_key
                    elif node.platform_type == PlatformType.CLOUD_COHERE:
                        headers["Authorization"] = f"Bearer {node.api_key}"
                    elif node.platform_type == PlatformType.CLOUD_GROQ:
                        headers["Authorization"] = f"Bearer {node.api_key}"

                # Make evaluation request
                response = await client.post(
                    f"{node.endpoint_url}/evaluate",
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    result = response.json()
                    result["success"] = True
                    result["node_id"] = node.node_id
                    result["platform_type"] = node.platform_type.value
                    return result
                else:
                    return {
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "success": False,
                        "node_id": node.node_id
                    }

        except Exception as e:
            return {"error": str(e), "success": False, "node_id": node.node_id}

    async def _evaluate_edge_platform(self, node: FederatedNode, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate policy on edge platform (local deployment)."""
        try:
            # Mock edge evaluation - would integrate with actual edge deployment
            await asyncio.sleep(0.5)  # Simulate processing time

            # Simulate edge evaluation results
            result = {
                "policy_compliance_score": np.random.uniform(0.7, 0.95),
                "execution_time_ms": np.random.uniform(50, 200),
                "resource_usage": {
                    "cpu_percent": np.random.uniform(10, 40),
                    "memory_mb": np.random.uniform(100, 500)
                },
                "edge_specific_metrics": {
                    "latency_ms": np.random.uniform(5, 20),
                    "offline_capability": True,
                    "local_privacy_preserved": True
                },
                "success": True,
                "node_id": node.node_id,
                "platform_type": node.platform_type.value
            }

            return result

        except Exception as e:
            return {"error": str(e), "success": False, "node_id": node.node_id}

    async def _evaluate_federated_node(self, node: FederatedNode, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate policy on federated learning node."""
        try:
            import httpx

            # Connect to federated node
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{node.endpoint_url}/federated-evaluate",
                    json=payload,
                    headers={"Authorization": f"Bearer {node.api_key}"} if node.api_key else {}
                )

                if response.status_code == 200:
                    result = response.json()
                    result["success"] = True
                    result["node_id"] = node.node_id
                    result["platform_type"] = node.platform_type.value
                    return result
                else:
                    return {
                        "error": f"Federated node error: {response.status_code}",
                        "success": False,
                        "node_id": node.node_id
                    }

        except Exception as e:
            return {"error": str(e), "success": False, "node_id": node.node_id}

    async def _update_mab_performance(self, task: EvaluationTask, results: Dict[str, Any]):
        """Update MAB system with federated evaluation performance feedback."""
        try:
            if not self.mab_client or not task.mab_context.get("selected_template"):
                return

            # Calculate composite performance score
            performance_score = self._calculate_performance_score(results)

            # Prepare MAB update payload
            mab_update = {
                "template_id": task.mab_context["selected_template"]["template_id"],
                "performance_score": performance_score,
                "context": task.mab_context,
                "evaluation_results": {
                    "cross_platform_consistency": results.get("consistency_score", 0.0),
                    "privacy_preservation": results.get("privacy_score", 0.0),
                    "execution_time": results.get("average_execution_time", 0.0),
                    "success_rate": results.get("success_rate", 0.0)
                }
            }

            # Send update to MAB system
            response = await self.mab_client.post(
                "/api/v1/mab/update-performance",
                json=mab_update
            )

            if response.status_code == 200:
                logger.debug(f"MAB performance updated for template: {mab_update['template_id']}")
            else:
                logger.warning(f"Failed to update MAB performance: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to update MAB performance: {e}")

    def _calculate_performance_score(self, results: Dict[str, Any]) -> float:
        """Calculate composite performance score for MAB feedback."""
        try:
            # Weight different performance aspects
            weights = {
                "success_rate": 0.4,
                "consistency_score": 0.3,
                "privacy_score": 0.2,
                "efficiency_score": 0.1
            }

            # Extract metrics with defaults
            success_rate = results.get("success_rate", 0.0)
            consistency_score = results.get("consistency_score", 0.0)
            privacy_score = results.get("privacy_score", 0.0)

            # Calculate efficiency score (inverse of execution time, normalized)
            avg_time = results.get("average_execution_time", 1000.0)
            efficiency_score = max(0.0, 1.0 - (avg_time / 1000.0))  # Normalize to 0-1

            # Calculate weighted composite score
            composite_score = (
                weights["success_rate"] * success_rate +
                weights["consistency_score"] * consistency_score +
                weights["privacy_score"] * privacy_score +
                weights["efficiency_score"] * efficiency_score
            )

            return min(1.0, max(0.0, composite_score))  # Clamp to [0, 1]

        except Exception as e:
            logger.error(f"Failed to calculate performance score: {e}")
            return 0.0

    async def _update_evaluation_metrics(self, task: EvaluationTask, execution_time: float, success: bool):
        """Update global evaluation metrics."""
        try:
            self.evaluation_metrics["total_evaluations"] += 1

            if success:
                self.evaluation_metrics["successful_evaluations"] += 1

                # Update average response time
                total_evals = self.evaluation_metrics["total_evaluations"]
                current_avg = self.evaluation_metrics["average_response_time"]
                self.evaluation_metrics["average_response_time"] = (
                    (current_avg * (total_evals - 1) + execution_time) / total_evals
                )

                # Update consistency and privacy scores from results
                if task.results:
                    self.evaluation_metrics["cross_platform_consistency"] = task.results.get("consistency_score", 0.0)
                    self.evaluation_metrics["privacy_preservation_score"] = task.results.get("privacy_score", 0.0)
            else:
                self.evaluation_metrics["failed_evaluations"] += 1

            # Store metrics in Redis for monitoring
            redis_client = await get_redis_client()
            if redis_client:
                await redis_client.hset(
                    "federated_evaluation_metrics",
                    mapping={k: str(v) for k, v in self.evaluation_metrics.items()}
                )

        except Exception as e:
            logger.error(f"Failed to update evaluation metrics: {e}")

    async def _update_node_metrics(self, node: FederatedNode, result: Dict[str, Any]):
        """Update performance metrics for a specific node."""
        try:
            if result.get("success", False):
                # Update success rate
                current_successes = node.performance_metrics.get("total_successes", 0)
                current_total = node.performance_metrics.get("total_evaluations", 0)

                node.performance_metrics["total_successes"] = current_successes + 1
                node.performance_metrics["total_evaluations"] = current_total + 1
                node.performance_metrics["success_rate"] = (
                    node.performance_metrics["total_successes"] /
                    node.performance_metrics["total_evaluations"]
                )

                # Update response time
                if "execution_time_ms" in result:
                    current_avg = node.performance_metrics.get("average_response_time", 0.0)
                    total_evals = node.performance_metrics["total_evaluations"]
                    node.performance_metrics["average_response_time"] = (
                        (current_avg * (total_evals - 1) + result["execution_time_ms"]) / total_evals
                    )
            else:
                # Update failure count
                current_total = node.performance_metrics.get("total_evaluations", 0)
                node.performance_metrics["total_evaluations"] = current_total + 1

                current_successes = node.performance_metrics.get("total_successes", 0)
                node.performance_metrics["success_rate"] = (
                    current_successes / node.performance_metrics["total_evaluations"]
                )

            # Update last heartbeat
            node.last_heartbeat = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to update node metrics: {e}")

    async def get_evaluation_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a federated evaluation task."""
        try:
            if task_id not in self.active_evaluations:
                return None

            task = self.active_evaluations[task_id]
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "target_platforms": [p.value for p in task.target_platforms],
                "results": task.results if task.status == EvaluationStatus.COMPLETED else None,
                "error": task.results.get("error") if task.status == EvaluationStatus.FAILED else None
            }

        except Exception as e:
            logger.error(f"Failed to get evaluation status: {e}")
            return None

    async def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a federated node."""
        try:
            if node_id not in self.nodes:
                return None

            node = self.nodes[node_id]
            return {
                "node_id": node.node_id,
                "platform_type": node.platform_type.value,
                "status": node.status,
                "last_heartbeat": node.last_heartbeat.isoformat(),
                "performance_metrics": node.performance_metrics,
                "capabilities": node.capabilities
            }

        except Exception as e:
            logger.error(f"Failed to get node status: {e}")
            return None

    async def get_evaluation_metrics(self) -> Dict[str, Any]:
        """Get global evaluation metrics."""
        return self.evaluation_metrics.copy()

    async def _load_federated_nodes(self):
        """Load federated nodes from database."""
        try:
            # Mock implementation - would load from actual database
            logger.info("Loading federated nodes from database...")

            # Add some default nodes for testing
            default_nodes = [
                {
                    "platform_type": PlatformType.CLOUD_OPENAI,
                    "endpoint_url": "https://api.openai.com/v1",
                    "capabilities": {"models": ["gpt-4", "gpt-3.5-turbo"], "max_tokens": 4096}
                },
                {
                    "platform_type": PlatformType.CLOUD_ANTHROPIC,
                    "endpoint_url": "https://api.anthropic.com/v1",
                    "capabilities": {"models": ["claude-3-sonnet", "claude-3-haiku"], "max_tokens": 4096}
                },
                {
                    "platform_type": PlatformType.EDGE_LOCAL,
                    "endpoint_url": "http://localhost:8080",
                    "capabilities": {"models": ["local-llm"], "max_tokens": 2048, "offline": True}
                }
            ]

            for node_config in default_nodes:
                node_id = f"{node_config['platform_type'].value}_default"
                node = FederatedNode(
                    node_id=node_id,
                    platform_type=node_config["platform_type"],
                    endpoint_url=node_config["endpoint_url"],
                    capabilities=node_config["capabilities"],
                    status="active"
                )
                self.nodes[node_id] = node

            logger.info(f"Loaded {len(self.nodes)} federated nodes")

        except Exception as e:
            logger.error(f"Failed to load federated nodes: {e}")

    async def _store_node_config(self, node: FederatedNode):
        """Store node configuration in database."""
        try:
            # Mock implementation - would store in actual database
            logger.debug(f"Storing node configuration: {node.node_id}")

        except Exception as e:
            logger.error(f"Failed to store node configuration: {e}")

    async def shutdown(self):
        """Shutdown the federated evaluator."""
        try:
            logger.info("Shutting down Federated Evaluator...")

            # Close MAB client
            if self.mab_client:
                await self.mab_client.aclose()

            # Shutdown secure aggregator
            await self.secure_aggregator.shutdown()

            # Shutdown privacy manager
            await self.privacy_manager.shutdown()

            logger.info("Federated Evaluator shutdown complete")

        except Exception as e:
            logger.error(f"Failed to shutdown Federated Evaluator: {e}")


# Global federated evaluator instance
federated_evaluator = FederatedEvaluator()
