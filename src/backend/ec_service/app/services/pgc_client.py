"""
PGC Service client for EC Service integration.

Provides interface for communicating with the Policy Governance & Compliance service
for policy enforcement and WINA optimization insights.
"""

import logging
import httpx
from typing import Dict, List, Any, Optional
from shared import get_config

logger = logging.getLogger(__name__)
config = get_config()


class PGCServiceClient:
    """Client for communicating with PGC Service."""
    
    def __init__(self):
        self.base_url = config.get('pgc_service_url', 'http://localhost:8005')
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={'Content-Type': 'application/json'}
        )
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def evaluate_policy_compliance(
        self,
        proposal: Dict[str, Any],
        policies: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate policy compliance for EC proposal.
        
        Args:
            proposal: EC proposal to evaluate
            policies: Applicable policies
            context: Optional evaluation context
            
        Returns:
            Policy compliance evaluation result
        """
        try:
            request_data = {
                "proposal": proposal,
                "policies": policies,
                "context": context or {},
                "source": "ec_service"
            }
            
            response = await self.client.post(
                "/api/v1/enforcement/evaluate",
                json=request_data
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Policy compliance evaluation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in policy evaluation: {e}")
            raise
    
    async def get_wina_enforcement_metrics(self) -> Dict[str, Any]:
        """
        Get WINA enforcement optimization metrics.
        
        Returns:
            WINA enforcement metrics
        """
        try:
            response = await self.client.get("/api/v1/enforcement/wina-metrics")
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get WINA enforcement metrics: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting WINA metrics: {e}")
            raise
    
    async def enforce_alphaevolve_policies(
        self,
        proposals: List[Dict[str, Any]],
        enforcement_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enforce AlphaEvolve policies with WINA optimization.
        
        Args:
            proposals: EC proposals for enforcement
            enforcement_context: Enforcement context
            
        Returns:
            Enforcement result
        """
        try:
            request_data = {
                "proposals": proposals,
                "context": enforcement_context,
                "optimization_enabled": True,
                "source": "ec_service"
            }
            
            response = await self.client.post(
                "/api/v1/alphaevolve/enforce",
                json=request_data
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"AlphaEvolve policy enforcement failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in policy enforcement: {e}")
            raise
    
    async def get_enforcement_strategies(
        self,
        context: str,
        optimization_hints: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available enforcement strategies for context.
        
        Args:
            context: Enforcement context
            optimization_hints: Optional WINA optimization hints
            
        Returns:
            List of available enforcement strategies
        """
        try:
            params = {"context": context}
            if optimization_hints:
                params["optimization_hints"] = optimization_hints
                
            response = await self.client.get(
                "/api/v1/enforcement/strategies",
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get enforcement strategies: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting strategies: {e}")
            raise


# Global client instance
pgc_service_client = PGCServiceClient()
