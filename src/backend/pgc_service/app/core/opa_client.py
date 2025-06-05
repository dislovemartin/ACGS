"""
OPA REST API Client for ACGS-PGP Task 8: Incremental Policy Compilation

Provides high-performance REST API integration with OPA server for policy
evaluation, bundle management, and incremental compilation capabilities.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import httpx
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class PolicyOperation(Enum):
    """Types of policy operations for incremental compilation."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EVALUATE = "evaluate"


@dataclass
class PolicyBundle:
    """Represents a policy bundle for OPA."""
    name: str
    policies: Dict[str, str]
    data: Dict[str, Any] = field(default_factory=dict)
    manifest: Dict[str, Any] = field(default_factory=dict)
    revision: str = ""
    etag: str = ""


@dataclass
class PolicyEvaluationRequest:
    """Request for policy evaluation."""
    input_data: Dict[str, Any]
    query: str
    unknowns: List[str] = field(default_factory=list)
    explain: str = "off"  # off, full, notes, fails
    metrics: bool = True
    instrument: bool = False
    strict_builtin_errors: bool = False


@dataclass
class PolicyEvaluationResponse:
    """Response from policy evaluation."""
    result: Any
    decision_id: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    explanation: List[Dict[str, Any]] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompilationMetrics:
    """Metrics for policy compilation performance."""
    compilation_time_ms: float
    policy_count: int
    incremental: bool
    cache_hit_ratio: float
    memory_usage_mb: float


class OPAClient:
    """
    High-performance OPA REST API client with incremental compilation support.
    
    Features:
    - Async HTTP client with connection pooling
    - Policy bundle management
    - Incremental compilation optimization
    - Performance metrics collection
    - Caching and cache invalidation
    """
    
    def __init__(
        self,
        server_url: str = "http://localhost:8181",
        bundle_name: str = "authz",
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20
    ):
        self.server_url = server_url.rstrip('/')
        self.bundle_name = bundle_name
        self.timeout = timeout
        
        # HTTP client configuration for high performance
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections
            ),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "ACGS-PGP-OPA-Client/1.0"
            }
        )
        
        # State tracking for incremental compilation
        self._policy_cache: Dict[str, str] = {}
        self._policy_etags: Dict[str, str] = {}
        self._bundle_revision: str = ""
        self._last_compilation_time: float = 0
        
        # Performance metrics
        self._metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "compilation_count": 0,
            "incremental_compilations": 0,
            "average_response_time_ms": 0.0
        }
    
    async def health_check(self) -> bool:
        """Check if OPA server is healthy and responsive."""
        try:
            response = await self.client.get(f"{self.server_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OPA health check failed: {e}")
            return False
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get OPA server information and capabilities."""
        try:
            response = await self.client.get(f"{self.server_url}/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get OPA server info: {e}")
            return {}
    
    async def evaluate_policy(
        self,
        request: PolicyEvaluationRequest
    ) -> PolicyEvaluationResponse:
        """
        Evaluate a policy query against the current policy set.
        
        Uses OPA's POST /v1/data/{path} endpoint for high-performance evaluation.
        """
        start_time = time.time()
        self._metrics["total_requests"] += 1
        
        try:
            # Prepare request payload
            payload = {
                "input": request.input_data
            }
            
            # Add optional parameters
            params = {}
            if request.explain != "off":
                params["explain"] = request.explain
            if request.metrics:
                params["metrics"] = "true"
            if request.instrument:
                params["instrument"] = "true"
            if request.strict_builtin_errors:
                params["strict-builtin-errors"] = "true"
            
            # Execute query
            url = f"{self.server_url}/v1/data/{request.query.lstrip('/')}"
            response = await self.client.post(
                url,
                json=payload,
                params=params
            )
            response.raise_for_status()
            
            # Parse response
            result_data = response.json()
            
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            self._update_response_time_metric(response_time)
            
            return PolicyEvaluationResponse(
                result=result_data.get("result"),
                decision_id=response.headers.get("x-opa-decision-id", ""),
                metrics=result_data.get("metrics", {}),
                explanation=result_data.get("explanation", []),
                provenance=result_data.get("provenance", {})
            )
            
        except Exception as e:
            logger.error(f"Policy evaluation failed: {e}")
            raise
    
    async def upload_policy_bundle(
        self,
        bundle: PolicyBundle,
        incremental: bool = True
    ) -> CompilationMetrics:
        """
        Upload a policy bundle to OPA with incremental compilation optimization.
        
        If incremental=True, only uploads changed policies to minimize compilation time.
        """
        start_time = time.time()
        
        try:
            if incremental:
                # Determine what has changed
                changed_policies = self._detect_policy_changes(bundle)
                if not changed_policies:
                    logger.info("No policy changes detected, skipping upload")
                    return CompilationMetrics(
                        compilation_time_ms=0,
                        policy_count=len(bundle.policies),
                        incremental=True,
                        cache_hit_ratio=1.0,
                        memory_usage_mb=0
                    )
                
                # Upload only changed policies
                await self._upload_incremental_policies(changed_policies)
                self._metrics["incremental_compilations"] += 1
                
            else:
                # Full bundle upload
                await self._upload_full_bundle(bundle)
                self._metrics["compilation_count"] += 1
            
            # Update cache
            self._update_policy_cache(bundle)
            
            # Calculate metrics
            compilation_time = (time.time() - start_time) * 1000
            cache_hit_ratio = (
                self._metrics["cache_hits"] / 
                max(1, self._metrics["cache_hits"] + self._metrics["cache_misses"])
            )
            
            return CompilationMetrics(
                compilation_time_ms=compilation_time,
                policy_count=len(bundle.policies),
                incremental=incremental,
                cache_hit_ratio=cache_hit_ratio,
                memory_usage_mb=0  # Would need system monitoring for actual value
            )
            
        except Exception as e:
            logger.error(f"Policy bundle upload failed: {e}")
            raise
    
    async def delete_policy(self, policy_path: str) -> bool:
        """Delete a specific policy from OPA."""
        try:
            url = f"{self.server_url}/v1/policies/{policy_path}"
            response = await self.client.delete(url)
            response.raise_for_status()
            
            # Update cache
            if policy_path in self._policy_cache:
                del self._policy_cache[policy_path]
            if policy_path in self._policy_etags:
                del self._policy_etags[policy_path]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete policy {policy_path}: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get OPA server metrics and client metrics."""
        try:
            # Get server metrics
            response = await self.client.get(f"{self.server_url}/metrics")
            server_metrics = {}
            if response.status_code == 200:
                # Parse Prometheus format metrics (simplified)
                server_metrics = {"raw_metrics": response.text}
            
            # Combine with client metrics
            return {
                "server": server_metrics,
                "client": self._metrics.copy(),
                "cache_stats": {
                    "policy_count": len(self._policy_cache),
                    "etag_count": len(self._policy_etags),
                    "bundle_revision": self._bundle_revision
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"client": self._metrics.copy()}
    
    def _detect_policy_changes(self, bundle: PolicyBundle) -> Dict[str, str]:
        """Detect which policies have changed since last upload."""
        changed_policies = {}
        
        for policy_name, policy_content in bundle.policies.items():
            # Check if policy is new or changed
            if (policy_name not in self._policy_cache or 
                self._policy_cache[policy_name] != policy_content):
                changed_policies[policy_name] = policy_content
                self._metrics["cache_misses"] += 1
            else:
                self._metrics["cache_hits"] += 1
        
        return changed_policies
    
    async def _upload_incremental_policies(self, policies: Dict[str, str]) -> None:
        """Upload only changed policies for incremental compilation."""
        try:
            for policy_name, policy_content in policies.items():
                policy_path = f"{self.bundle_name}/{policy_name}"
                url = f"{self.server_url}/v1/policies/{policy_path}"

                response = await self.client.put(
                    url,
                    content=policy_content,
                    headers={"Content-Type": "text/plain"}
                )
                response.raise_for_status()
                logger.debug(f"Uploaded incremental policy: {policy_path}")

            logger.info(f"Uploaded {len(policies)} incremental policies")

        except Exception as e:
            logger.error(f"Failed to upload incremental policies: {e}")
            raise
    
    async def _upload_full_bundle(self, bundle: PolicyBundle) -> None:
        """Upload complete policy bundle using individual policy uploads."""
        try:
            # Upload each policy individually using the /v1/policies endpoint
            for policy_name, policy_content in bundle.policies.items():
                policy_path = f"{self.bundle_name}/{policy_name}"
                url = f"{self.server_url}/v1/policies/{policy_path}"

                response = await self.client.put(
                    url,
                    content=policy_content,
                    headers={"Content-Type": "text/plain"}
                )
                response.raise_for_status()
                logger.debug(f"Uploaded policy: {policy_path}")

            logger.info(f"Uploaded full bundle: {self.bundle_name} ({len(bundle.policies)} policies)")

        except Exception as e:
            logger.error(f"Failed to upload full bundle: {e}")
            raise
    
    def _update_policy_cache(self, bundle: PolicyBundle) -> None:
        """Update internal policy cache."""
        self._policy_cache.update(bundle.policies)
        self._bundle_revision = bundle.revision
        self._last_compilation_time = time.time()
    
    def _update_response_time_metric(self, response_time_ms: float) -> None:
        """Update average response time metric."""
        current_avg = self._metrics["average_response_time_ms"]
        total_requests = self._metrics["total_requests"]
        
        # Calculate new average
        self._metrics["average_response_time_ms"] = (
            (current_avg * (total_requests - 1) + response_time_ms) / total_requests
        )
    
    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        await self.client.aclose()
        logger.info("OPA client closed")


# Global OPA client instance
_opa_client: Optional[OPAClient] = None


async def get_opa_client() -> OPAClient:
    """Get or create the global OPA client instance."""
    global _opa_client
    
    if _opa_client is None:
        import os
        server_url = os.getenv("OPA_SERVER_URL", "http://localhost:8181")
        bundle_name = os.getenv("OPA_BUNDLE_NAME", "authz")
        
        _opa_client = OPAClient(
            server_url=server_url,
            bundle_name=bundle_name
        )
        
        # Verify connection
        if not await _opa_client.health_check():
            logger.warning("OPA server health check failed")
    
    return _opa_client


async def close_opa_client() -> None:
    """Close the global OPA client."""
    global _opa_client
    if _opa_client:
        await _opa_client.close()
        _opa_client = None
