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
        """Initialize the federated evaluator with enhanced multi-node support."""
        try:
            # Import here to avoid circular imports
            from .secure_aggregation import SecureAggregator
            from .privacy_metrics import DifferentialPrivacyManager
            from .cross_platform_coordinator import CrossPlatformCoordinator

            # Initialize components
            self.secure_aggregator = SecureAggregator()
            self.privacy_manager = DifferentialPrivacyManager(epsilon=1.0)
            self.cross_platform_coordinator = CrossPlatformCoordinator()

            # Initialize secure aggregator with enhanced Byzantine fault tolerance
            await self.secure_aggregator.initialize()

            # Initialize privacy manager with multi-node support
            await self.privacy_manager.initialize()

            # Initialize cross-platform coordinator for 10+ nodes
            await self.cross_platform_coordinator.initialize()

            # Initialize MAB client connection to GS service
            await self._initialize_mab_client()

            # Load existing nodes from database
            await self._load_federated_nodes()

            # Initialize node health monitoring
            await self._initialize_node_monitoring()

            # Setup Byzantine fault detection
            await self._initialize_byzantine_detection()

            logger.info("Federated Evaluator initialized successfully with multi-node support")

        except Exception as e:
            logger.error(f"Failed to initialize Federated Evaluator: {e}")
            raise

    async def _initialize_node_monitoring(self):
        """Initialize node health monitoring for 10+ federated nodes."""
        try:
            # Setup periodic health checks
            self.node_health_check_interval = 30  # seconds
            self.node_timeout_threshold = 120  # seconds
            self.max_concurrent_evaluations_per_node = 5

            # Initialize node load balancing
            self.node_load_balancer = {
                "strategy": "least_loaded",  # "round_robin", "least_loaded", "performance_based"
                "weights": {},  # Node performance weights
                "current_loads": {}  # Current evaluation loads per node
            }

            # Start background health monitoring task
            asyncio.create_task(self._monitor_node_health())

            logger.info("Node monitoring initialized for multi-node federation")

        except Exception as e:
            logger.error(f"Failed to initialize node monitoring: {e}")
            raise

    async def _initialize_byzantine_detection(self):
        """Initialize Byzantine fault detection algorithms."""
        try:
            # Byzantine detection configuration
            self.byzantine_config = {
                "detection_threshold": 0.3,  # Threshold for marking node as Byzantine
                "consensus_threshold": 0.67,  # Minimum agreement for consensus
                "outlier_detection_method": "statistical",  # "statistical", "ml_based", "consensus"
                "max_byzantine_nodes": 3,  # Maximum tolerable Byzantine nodes
                "quarantine_duration": 300  # seconds to quarantine suspected nodes
            }

            # Initialize detection algorithms
            self.byzantine_detector = {
                "statistical_outlier_detector": self._statistical_outlier_detection,
                "consensus_validator": self._validate_consensus,
                "performance_anomaly_detector": self._detect_performance_anomalies
            }

            # Quarantined nodes tracking
            self.quarantined_nodes = {}

            logger.info("Byzantine fault detection initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Byzantine detection: {e}")
            raise

    async def _monitor_node_health(self):
        """Background task to monitor node health and performance."""
        while True:
            try:
                current_time = datetime.now(timezone.utc)

                for node_id, node in self.nodes.items():
                    # Check heartbeat timeout
                    if node.last_heartbeat:
                        time_since_heartbeat = (current_time - node.last_heartbeat).total_seconds()

                        if time_since_heartbeat > self.node_timeout_threshold:
                            await self._handle_node_timeout(node_id)

                    # Update node health score based on recent performance
                    await self._update_node_health_score(node_id)

                    # Check for performance anomalies
                    await self._check_node_performance_anomalies(node_id)

                # Update load balancing weights
                await self._update_load_balancing_weights()

                # Sleep until next health check
                await asyncio.sleep(self.node_health_check_interval)

            except Exception as e:
                logger.error(f"Error in node health monitoring: {e}")
                await asyncio.sleep(self.node_health_check_interval)

    async def _handle_node_timeout(self, node_id: str):
        """Handle node timeout by marking as inactive and redistributing tasks."""
        try:
            if node_id in self.nodes:
                self.nodes[node_id].status = "inactive"
                logger.warning(f"Node {node_id} marked as inactive due to timeout")

                # Redistribute active evaluations from this node
                await self._redistribute_node_evaluations(node_id)

                # Update metrics
                self.evaluation_metrics["failed_evaluations"] += 1

        except Exception as e:
            logger.error(f"Error handling node timeout for {node_id}: {e}")

    async def _update_node_health_score(self, node_id: str):
        """Update node health score based on recent performance metrics."""
        try:
            if node_id not in self.nodes:
                return

            node = self.nodes[node_id]

            # Calculate health score based on multiple factors
            success_rate = (node.successful_evaluations / max(node.total_evaluations, 1))
            response_time_factor = min(1.0, 1000.0 / max(node.average_response_time_ms, 100.0))

            # Combine factors with weights
            health_score = (
                0.6 * success_rate +
                0.3 * response_time_factor +
                0.1 * (1.0 if node.status == "active" else 0.0)
            )

            node.health_score = max(0.0, min(1.0, health_score))

            # Update load balancing weights
            self.node_load_balancer["weights"][node_id] = node.health_score

        except Exception as e:
            logger.error(f"Error updating health score for node {node_id}: {e}")

    async def _check_node_performance_anomalies(self, node_id: str):
        """Check for performance anomalies that might indicate Byzantine behavior."""
        try:
            if node_id not in self.nodes:
                return

            node = self.nodes[node_id]

            # Check for suspicious patterns
            anomalies = []

            # Unusually high failure rate
            if node.total_evaluations > 10:
                failure_rate = (node.failed_evaluations / node.total_evaluations)
                if failure_rate > 0.5:
                    anomalies.append("high_failure_rate")

            # Unusually slow response times
            if node.average_response_time_ms > 10000:  # 10 seconds
                anomalies.append("slow_response")

            # Inconsistent results (would need historical data)
            # This would be implemented with more sophisticated analysis

            if anomalies:
                await self._handle_performance_anomaly(node_id, anomalies)

        except Exception as e:
            logger.error(f"Error checking performance anomalies for node {node_id}: {e}")

    async def _handle_performance_anomaly(self, node_id: str, anomalies: List[str]):
        """Handle detected performance anomalies."""
        try:
            logger.warning(f"Performance anomalies detected for node {node_id}: {anomalies}")

            # Increase monitoring frequency for this node
            # Reduce evaluation assignments temporarily
            # Consider quarantine if anomalies persist

            if len(anomalies) >= 2:
                await self._quarantine_node(node_id, "performance_anomalies")

        except Exception as e:
            logger.error(f"Error handling performance anomaly for node {node_id}: {e}")

    async def _quarantine_node(self, node_id: str, reason: str):
        """Quarantine a node suspected of Byzantine behavior."""
        try:
            if node_id in self.nodes:
                self.nodes[node_id].status = "maintenance"
                self.quarantined_nodes[node_id] = {
                    "reason": reason,
                    "quarantined_at": datetime.now(timezone.utc),
                    "duration": self.byzantine_config["quarantine_duration"]
                }

                logger.warning(f"Node {node_id} quarantined for {reason}")

                # Redistribute evaluations
                await self._redistribute_node_evaluations(node_id)

        except Exception as e:
            logger.error(f"Error quarantining node {node_id}: {e}")
    
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
        """Submit a new federated evaluation task with enhanced multi-node support."""
        try:
            task_id = hashlib.md5(f"{request.policy_content}_{time.time()}".encode()).hexdigest()[:16]

            # Get MAB-optimized context if available
            mab_context = await self._get_mab_context(request)

            # Select optimal nodes for this evaluation
            selected_nodes = await self._select_optimal_nodes(request.target_platforms, request.evaluation_criteria)

            if len(selected_nodes) < 2:
                raise ValueError("Insufficient active nodes for federated evaluation")

            task = EvaluationTask(
                task_id=task_id,
                policy_content=request.policy_content,
                evaluation_criteria=request.evaluation_criteria,
                target_platforms=request.target_platforms,
                mab_context=mab_context,
                privacy_requirements=request.privacy_requirements
            )

            self.active_evaluations[task_id] = task

            # Store evaluation in database
            await self._store_evaluation_in_db(task, selected_nodes)

            # Start evaluation asynchronously with selected nodes
            asyncio.create_task(self._execute_federated_evaluation(task, selected_nodes))

            logger.info(f"Submitted federated evaluation: {task_id} with {len(selected_nodes)} nodes")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit evaluation: {e}")
            raise

    async def _select_optimal_nodes(self, target_platforms: List[str], evaluation_criteria: Dict[str, Any]) -> List[str]:
        """Select optimal nodes for federated evaluation based on platform requirements and performance."""
        try:
            # Filter nodes by platform type and status
            available_nodes = []
            for node_id, node in self.nodes.items():
                if (node.status == "active" and
                    node.platform_type.value in target_platforms and
                    node_id not in self.quarantined_nodes):
                    available_nodes.append((node_id, node))

            if len(available_nodes) < 2:
                raise ValueError(f"Insufficient nodes available for platforms: {target_platforms}")

            # Sort nodes by health score and current load
            def node_score(node_data):
                node_id, node = node_data
                current_load = self.node_load_balancer["current_loads"].get(node_id, 0)
                load_factor = max(0.1, 1.0 - (current_load / self.max_concurrent_evaluations_per_node))
                return node.health_score * load_factor

            available_nodes.sort(key=node_score, reverse=True)

            # Select top nodes (minimum 2, maximum based on evaluation requirements)
            min_nodes = max(2, len(target_platforms))
            max_nodes = min(10, len(available_nodes))  # Cap at 10 nodes for performance

            # Determine optimal number of nodes based on evaluation criteria
            complexity_factor = evaluation_criteria.get("complexity", "medium")
            if complexity_factor == "high":
                target_node_count = min(max_nodes, 6)
            elif complexity_factor == "medium":
                target_node_count = min(max_nodes, 4)
            else:
                target_node_count = min(max_nodes, 3)

            selected_node_count = max(min_nodes, target_node_count)
            selected_nodes = [node_id for node_id, _ in available_nodes[:selected_node_count]]

            # Update current loads
            for node_id in selected_nodes:
                current_load = self.node_load_balancer["current_loads"].get(node_id, 0)
                self.node_load_balancer["current_loads"][node_id] = current_load + 1

            logger.info(f"Selected {len(selected_nodes)} nodes for evaluation: {selected_nodes}")
            return selected_nodes

        except Exception as e:
            logger.error(f"Failed to select optimal nodes: {e}")
            raise

    async def _store_evaluation_in_db(self, task: EvaluationTask, selected_nodes: List[str]):
        """Store evaluation task and node assignments in database."""
        try:
            from shared.database import get_async_db
            from shared.models import FederatedEvaluation, EvaluationNodeAssignment

            async with get_async_db() as db:
                # Create federated evaluation record
                db_evaluation = FederatedEvaluation(
                    task_id=task.task_id,
                    policy_content=task.policy_content,
                    evaluation_criteria=task.evaluation_criteria,
                    target_platforms=task.target_platforms,
                    privacy_requirements=task.privacy_requirements,
                    mab_context=task.mab_context,
                    status=task.status.value,
                    participant_count=len(selected_nodes)
                )

                db.add(db_evaluation)
                await db.flush()  # Get the ID

                # Create node assignments
                for i, node_id in enumerate(selected_nodes):
                    assignment = EvaluationNodeAssignment(
                        evaluation_id=db_evaluation.id,
                        node_id=self._get_node_db_id(node_id),
                        priority=1 if i < 2 else 2,  # First 2 nodes get high priority
                        status="assigned"
                    )
                    db.add(assignment)

                await db.commit()

                logger.info(f"Stored evaluation {task.task_id} in database with {len(selected_nodes)} node assignments")

        except Exception as e:
            logger.error(f"Failed to store evaluation in database: {e}")
            raise

    def _get_node_db_id(self, node_id: str) -> int:
        """Get database ID for a node (placeholder - would need actual implementation)."""
        # This would need to be implemented to map node_id to database ID
        # For now, return a placeholder
        return hash(node_id) % 1000000

    async def _redistribute_node_evaluations(self, failed_node_id: str):
        """Redistribute evaluations from a failed node to other available nodes."""
        try:
            # Find active evaluations assigned to the failed node
            evaluations_to_redistribute = []

            for task_id, task in self.active_evaluations.items():
                if task.status in [EvaluationStatus.PENDING, EvaluationStatus.RUNNING]:
                    evaluations_to_redistribute.append(task_id)

            if not evaluations_to_redistribute:
                return

            logger.info(f"Redistributing {len(evaluations_to_redistribute)} evaluations from failed node {failed_node_id}")

            for task_id in evaluations_to_redistribute:
                task = self.active_evaluations[task_id]

                # Select new nodes excluding the failed one
                available_platforms = [p for p in task.target_platforms]
                new_nodes = await self._select_optimal_nodes(available_platforms, task.evaluation_criteria)

                if new_nodes:
                    # Restart evaluation with new nodes
                    asyncio.create_task(self._execute_federated_evaluation(task, new_nodes))
                    logger.info(f"Redistributed evaluation {task_id} to new nodes: {new_nodes}")
                else:
                    # Mark evaluation as failed if no nodes available
                    task.status = EvaluationStatus.FAILED
                    task.results["error"] = f"No available nodes after {failed_node_id} failure"
                    logger.warning(f"Failed to redistribute evaluation {task_id} - no available nodes")

        except Exception as e:
            logger.error(f"Failed to redistribute evaluations from node {failed_node_id}: {e}")

    async def _update_load_balancing_weights(self):
        """Update load balancing weights based on current node performance."""
        try:
            for node_id, node in self.nodes.items():
                if node_id not in self.node_load_balancer["weights"]:
                    self.node_load_balancer["weights"][node_id] = node.health_score
                else:
                    # Exponential moving average for weight updates
                    current_weight = self.node_load_balancer["weights"][node_id]
                    new_weight = 0.7 * current_weight + 0.3 * node.health_score
                    self.node_load_balancer["weights"][node_id] = new_weight

        except Exception as e:
            logger.error(f"Failed to update load balancing weights: {e}")
    
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
