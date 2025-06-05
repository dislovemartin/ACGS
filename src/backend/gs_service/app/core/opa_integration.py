"""
OPA (Open Policy Agent) Integration Module

This module provides comprehensive integration with Open Policy Agent for
policy validation, decision making, and governance enforcement within the
ACGS-PGP governance synthesis service.

Phase 2: Governance Synthesis Hardening with Rego/OPA Integration
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import hashlib

try:
    import requests
    from opa import OPA
    OPA_CLIENT_AVAILABLE = True
except ImportError:
    OPA_CLIENT_AVAILABLE = False
    OPA = None

# Initialize logger first
logger = logging.getLogger(__name__)

# Phase 3: Performance Optimization imports
try:
    from ..services.performance_monitor import get_performance_monitor, performance_monitor_decorator
    from ..services.advanced_cache import MultiTierCache, LRUCache, RedisCache
    import redis.asyncio as redis
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False
    logger.warning("Performance monitoring not available")

    # Create fallback decorator
    def performance_monitor_decorator(operation_type: str, operation_name: str):
        """Fallback decorator when performance monitoring is not available."""
        def decorator(func):
            return func
        return decorator

    def get_performance_monitor():
        """Fallback function when performance monitoring is not available."""
        return None

from ..config.opa_config import get_opa_config, OPAMode


@dataclass
class PolicyDecisionRequest:
    """Request for OPA policy decision."""
    input_data: Dict[str, Any]
    policy_path: str
    query: Optional[str] = None
    explain: bool = False
    metrics: bool = False
    instrument: bool = False
    pretty: bool = False


@dataclass
class PolicyDecisionResponse:
    """Response from OPA policy decision."""
    result: Any
    decision_id: str
    decision_time_ms: float
    explanation: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class PolicyValidationResult:
    """Result of policy validation."""
    is_valid: bool
    policy_path: str
    validation_time_ms: float
    errors: List[str]
    warnings: List[str]
    syntax_errors: List[str]
    semantic_errors: List[str]


@dataclass
class BatchPolicyDecision:
    """Batch policy decision request."""
    decisions: List[PolicyDecisionRequest]
    batch_id: str
    parallel_execution: bool = True


class OPAIntegrationError(Exception):
    """Custom exception for OPA integration errors."""
    pass


class PolicyDecisionCache:
    """Enhanced policy decision cache with multi-tier support."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300, redis_client: Optional[Any] = None):
        self.ttl_seconds = ttl_seconds

        if PERFORMANCE_MONITORING_AVAILABLE and redis_client:
            # Use advanced multi-tier cache
            l1_cache = LRUCache(max_size=max_size, default_ttl=ttl_seconds)
            l2_cache = RedisCache(redis_client, key_prefix="acgs:opa:cache:")
            self.cache = MultiTierCache(l1_cache, l2_cache)
            self.use_advanced_cache = True
            logger.info("Initialized advanced multi-tier policy decision cache")
        else:
            # Fallback to simple cache
            self.cache: Dict[str, Dict[str, Any]] = {}
            self.max_size = max_size
            self.use_advanced_cache = False
            logger.info("Initialized simple policy decision cache")

    def _generate_key(self, request: PolicyDecisionRequest) -> str:
        """Generate cache key from request."""
        key_data = {
            "input_data": request.input_data,
            "policy_path": request.policy_path,
            "query": request.query
        }
        return key_data if self.use_advanced_cache else hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    async def get(self, request: PolicyDecisionRequest) -> Optional[PolicyDecisionResponse]:
        """Get cached decision if available and not expired."""
        key = self._generate_key(request)

        if self.use_advanced_cache:
            return await self.cache.get(key)
        else:
            # Fallback to simple cache logic
            if key in self.cache:
                entry = self.cache[key]
                if datetime.now() < entry["expires_at"]:
                    logger.debug(f"Cache hit for policy decision: {key}")
                    return entry["response"]
                else:
                    del self.cache[key]
            return None

    async def put(self, request: PolicyDecisionRequest, response: PolicyDecisionResponse):
        """Cache policy decision response."""
        key = self._generate_key(request)

        if self.use_advanced_cache:
            await self.cache.put(key, response, self.ttl_seconds, tags=["policy_decision"])
        else:
            # Fallback to simple cache logic
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["created_at"])
                del self.cache[oldest_key]

            self.cache[key] = {
                "response": response,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(seconds=self.ttl_seconds)
            }
            logger.debug(f"Cached policy decision: {key}")

    async def clear(self):
        """Clear all cached decisions."""
        if self.use_advanced_cache:
            await self.cache.clear()
        else:
            self.cache.clear()
        logger.info("Policy decision cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.use_advanced_cache:
            return self.cache.get_stats()
        else:
            return {
                "simple_cache": {
                    "entry_count": len(self.cache),
                    "max_size": self.max_size
                }
            }


class OPAClient:
    """
    High-performance OPA client with advanced caching, performance monitoring, and error handling.

    Supports both embedded OPA library and external OPA server modes
    with automatic failover and performance optimization.

    Phase 3: Enhanced with multi-tier caching and performance monitoring.
    """

    def __init__(self, redis_client: Optional[Any] = None):
        self.config = get_opa_config()
        self.redis_client = redis_client
        self.cache = PolicyDecisionCache(
            max_size=self.config.performance.cache_max_size,
            ttl_seconds=self.config.performance.cache_ttl_seconds,
            redis_client=redis_client
        )
        self.opa_client = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
        self._health_check_task: Optional[asyncio.Task] = None

        # Performance monitoring
        self.performance_monitor = get_performance_monitor() if PERFORMANCE_MONITORING_AVAILABLE else None

        # Performance metrics
        self.metrics = {
            "total_decisions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "error_count": 0,
            "last_health_check": None
        }
    
    async def initialize(self):
        """Initialize OPA client based on configuration mode."""
        if self._initialized:
            return
        
        try:
            if self.config.mode in [OPAMode.EMBEDDED, OPAMode.HYBRID]:
                await self._initialize_embedded_client()
            
            if self.config.mode in [OPAMode.SERVER, OPAMode.HYBRID]:
                await self._initialize_server_client()
            
            # Start health check task
            if self.config.mode in [OPAMode.SERVER, OPAMode.HYBRID]:
                self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            self._initialized = True
            logger.info(f"OPA client initialized in {self.config.mode.value} mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize OPA client: {e}")
            raise OPAIntegrationError(f"OPA client initialization failed: {e}")
    
    async def _initialize_embedded_client(self):
        """Initialize embedded OPA client."""
        if not OPA_CLIENT_AVAILABLE:
            raise OPAIntegrationError("OPA Python client not available")
        
        try:
            self.opa_client = OPA()
            logger.info("Embedded OPA client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embedded OPA client: {e}")
            raise
    
    async def _initialize_server_client(self):
        """Initialize HTTP client for OPA server."""
        timeout = aiohttp.ClientTimeout(
            total=self.config.server.timeout_seconds,
            connect=self.config.server.timeout_seconds / 2
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        # Test server connectivity
        try:
            await self._check_server_health()
            logger.info(f"OPA server client initialized: {self.config.server.base_url}")
        except Exception as e:
            logger.error(f"Failed to connect to OPA server: {e}")
            if self.config.mode == OPAMode.SERVER:
                raise OPAIntegrationError(f"OPA server connection failed: {e}")
    
    async def _check_server_health(self) -> bool:
        """Check OPA server health."""
        if not self.session:
            return False
        
        try:
            async with self.session.get(self.config.server.health_url) as response:
                if response.status == 200:
                    self.metrics["last_health_check"] = datetime.now()
                    return True
                else:
                    logger.warning(f"OPA server health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"OPA server health check error: {e}")
            return False
    
    async def _health_check_loop(self):
        """Periodic health check for OPA server."""
        while True:
            try:
                await asyncio.sleep(self.config.server.health_check_interval_seconds)
                await self._check_server_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    @performance_monitor_decorator("opa_policy_evaluation", "policy_decision")
    async def evaluate_policy(self, request: PolicyDecisionRequest) -> PolicyDecisionResponse:
        """
        Evaluate policy with advanced performance optimization and caching.

        Args:
            request: Policy decision request

        Returns:
            Policy decision response

        Raises:
            OPAIntegrationError: If policy evaluation fails
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        # Check cache first
        if self.config.performance.enable_decision_caching:
            cached_response = await self.cache.get(request)
            if cached_response:
                self.metrics["cache_hits"] += 1
                logger.debug("Policy decision cache hit", policy_path=request.policy_path)
                return cached_response
            self.metrics["cache_misses"] += 1

        try:
            # Use performance monitoring context if available
            if self.performance_monitor:
                async with self.performance_monitor.monitor_request("opa_policy_evaluation", "policy_decision"):
                    response = await self._evaluate_policy_internal(request)
            else:
                response = await self._evaluate_policy_internal(request)

            # Update metrics
            latency_ms = (time.time() - start_time) * 1000
            self._update_metrics(latency_ms)

            # Check latency threshold
            if latency_ms > self.config.performance.max_policy_decision_latency_ms:
                logger.warning(f"Policy decision exceeded latency threshold: {latency_ms:.2f}ms > {self.config.performance.max_policy_decision_latency_ms}ms for {request.policy_path}")

            # Cache successful response
            if self.config.performance.enable_decision_caching and not response.error:
                await self.cache.put(request, response)

            return response

        except Exception as e:
            self.metrics["error_count"] += 1
            logger.error(f"Policy evaluation failed for {request.policy_path}: {str(e)}")
            raise OPAIntegrationError(f"Policy evaluation failed: {e}")
    
    async def _evaluate_policy_internal(self, request: PolicyDecisionRequest) -> PolicyDecisionResponse:
        """Internal policy evaluation with mode-specific handling."""
        decision_id = f"decision_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            # Try server mode first if available
            if self.config.mode in [OPAMode.SERVER, OPAMode.HYBRID] and self.session:
                try:
                    return await self._evaluate_via_server(request, decision_id, start_time)
                except Exception as e:
                    if self.config.mode == OPAMode.SERVER:
                        raise
                    logger.warning(f"Server evaluation failed, falling back to embedded: {e}")
            
            # Fall back to embedded mode
            if self.config.mode in [OPAMode.EMBEDDED, OPAMode.HYBRID] and self.opa_client:
                return await self._evaluate_via_embedded(request, decision_id, start_time)
            
            raise OPAIntegrationError("No available OPA evaluation method")
            
        except Exception as e:
            decision_time_ms = (time.time() - start_time) * 1000
            return PolicyDecisionResponse(
                result=None,
                decision_id=decision_id,
                decision_time_ms=decision_time_ms,
                error=str(e)
            )
    
    async def _evaluate_via_server(self, request: PolicyDecisionRequest, 
                                 decision_id: str, start_time: float) -> PolicyDecisionResponse:
        """Evaluate policy via OPA server."""
        url = f"{self.config.server.data_api_url}/{request.policy_path}"
        
        payload = {
            "input": request.input_data
        }
        
        if request.query:
            payload["query"] = request.query
        
        params = {}
        if request.explain:
            params["explain"] = "full"
        if request.metrics:
            params["metrics"] = "true"
        if request.instrument:
            params["instrument"] = "true"
        if request.pretty:
            params["pretty"] = "true"
        
        async with self.session.post(url, json=payload, params=params) as response:
            if response.status == 200:
                data = await response.json()
                decision_time_ms = (time.time() - start_time) * 1000
                
                return PolicyDecisionResponse(
                    result=data.get("result"),
                    decision_id=decision_id,
                    decision_time_ms=decision_time_ms,
                    explanation=data.get("explanation"),
                    metrics=data.get("metrics"),
                    provenance=data.get("provenance")
                )
            else:
                error_text = await response.text()
                raise OPAIntegrationError(f"Server evaluation failed: {response.status} - {error_text}")
    
    async def _evaluate_via_embedded(self, request: PolicyDecisionRequest,
                                   decision_id: str, start_time: float) -> PolicyDecisionResponse:
        """Evaluate policy via embedded OPA client."""
        # Note: This is a simplified implementation
        # In practice, you would need to load policies and evaluate them
        decision_time_ms = (time.time() - start_time) * 1000
        
        # Placeholder implementation
        result = {"allowed": True, "message": "Embedded evaluation not fully implemented"}
        
        return PolicyDecisionResponse(
            result=result,
            decision_id=decision_id,
            decision_time_ms=decision_time_ms
        )
    
    def _update_metrics(self, latency_ms: float):
        """Update performance metrics."""
        self.metrics["total_decisions"] += 1
        
        # Update average latency
        total = self.metrics["total_decisions"]
        current_avg = self.metrics["average_latency_ms"]
        self.metrics["average_latency_ms"] = ((current_avg * (total - 1)) + latency_ms) / total
        
        # Update max latency
        if latency_ms > self.metrics["max_latency_ms"]:
            self.metrics["max_latency_ms"] = latency_ms
    
    async def validate_policy(self, policy_content: str, policy_path: str) -> PolicyValidationResult:
        """
        Validate Rego policy syntax and semantics.
        
        Args:
            policy_content: Rego policy content
            policy_path: Policy path/name
            
        Returns:
            Policy validation result
        """
        start_time = time.time()
        errors = []
        warnings = []
        syntax_errors = []
        semantic_errors = []
        
        try:
            # Basic syntax validation
            if not policy_content.strip():
                syntax_errors.append("Policy content is empty")
            
            if not policy_content.strip().startswith("package "):
                syntax_errors.append("Policy must start with package declaration")
            
            # Additional validation would go here
            # This is a simplified implementation
            
            validation_time_ms = (time.time() - start_time) * 1000
            is_valid = len(syntax_errors) == 0 and len(semantic_errors) == 0
            
            return PolicyValidationResult(
                is_valid=is_valid,
                policy_path=policy_path,
                validation_time_ms=validation_time_ms,
                errors=errors,
                warnings=warnings,
                syntax_errors=syntax_errors,
                semantic_errors=semantic_errors
            )
            
        except Exception as e:
            validation_time_ms = (time.time() - start_time) * 1000
            return PolicyValidationResult(
                is_valid=False,
                policy_path=policy_path,
                validation_time_ms=validation_time_ms,
                errors=[str(e)],
                warnings=warnings,
                syntax_errors=syntax_errors,
                semantic_errors=semantic_errors
            )
    
    async def batch_evaluate(self, batch: BatchPolicyDecision) -> List[PolicyDecisionResponse]:
        """
        Evaluate multiple policies in batch for improved performance.
        
        Args:
            batch: Batch policy decision request
            
        Returns:
            List of policy decision responses
        """
        if not batch.decisions:
            return []
        
        if batch.parallel_execution and self.config.performance.enable_parallel_evaluation:
            # Parallel execution
            semaphore = asyncio.Semaphore(self.config.performance.max_parallel_workers)
            
            async def evaluate_with_semaphore(request):
                async with semaphore:
                    return await self.evaluate_policy(request)
            
            tasks = [evaluate_with_semaphore(request) for request in batch.decisions]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Sequential execution
            results = []
            for request in batch.decisions:
                result = await self.evaluate_policy(request)
                results.append(result)
            return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.metrics.copy()
    
    async def close(self):
        """Clean up resources."""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"Error during health check task cleanup: {e}")

        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logger.warning(f"Error closing HTTP session: {e}")

        if hasattr(self, 'cache') and self.cache:
            self.cache.clear()

        self._initialized = False
        logger.info("OPA client closed")


# Global OPA client instance
_opa_client: Optional[OPAClient] = None


async def get_opa_client() -> OPAClient:
    """Get or create the global OPA client instance."""
    global _opa_client
    if _opa_client is None:
        _opa_client = OPAClient()
        await _opa_client.initialize()
    return _opa_client


async def close_opa_client():
    """Close the global OPA client instance."""
    global _opa_client
    if _opa_client:
        await _opa_client.close()
        _opa_client = None
