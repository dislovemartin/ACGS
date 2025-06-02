"""
GS Service client for EC Service integration.

Provides interface for communicating with the Governance Synthesis service
for AlphaEvolve integration and constitutional governance operations.
"""

import logging
import httpx
from typing import Dict, List, Any, Optional
from shared import get_config

logger = logging.getLogger(__name__)
config = get_config()


class GSServiceClient:
    """Client for communicating with GS Service."""
    
    def __init__(self):
        self.base_url = config.get('gs_service_url', 'http://localhost:8004')
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={'Content-Type': 'application/json'}
        )
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def evaluate_ec_governance(
        self,
        proposals: List[Dict[str, Any]],
        context: str,
        optimization_hints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate EC proposals for constitutional compliance.
        
        Args:
            proposals: List of EC proposals to evaluate
            context: Context for the evaluation
            optimization_hints: Optional WINA optimization hints
            
        Returns:
            Governance evaluation response
        """
        try:
            request_data = {
                "proposals": proposals,
                "context": context,
                "optimization_hints": optimization_hints or {}
            }
            
            response = await self.client.post(
                "/api/v1/alphaevolve/governance-evaluation",
                json=request_data
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"GS Service governance evaluation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in governance evaluation: {e}")
            raise
    
    async def synthesize_ec_rules(
        self,
        ec_context: str,
        optimization_objective: str,
        constitutional_constraints: List[str],
        target_format: str = "rego"
    ) -> Dict[str, Any]:
        """
        Synthesize governance rules for EC systems.
        
        Args:
            ec_context: EC system context
            optimization_objective: Optimization objective
            constitutional_constraints: Constitutional constraints
            target_format: Target format for rules
            
        Returns:
            Synthesized rules response
        """
        try:
            request_data = {
                "ec_context": ec_context,
                "optimization_objective": optimization_objective,
                "constitutional_constraints": constitutional_constraints,
                "target_format": target_format
            }
            
            response = await self.client.post(
                "/api/v1/alphaevolve/synthesize-rules",
                json=request_data
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"GS Service rule synthesis failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in rule synthesis: {e}")
            raise
    
    async def get_wina_synthesis_metrics(self) -> Dict[str, Any]:
        """
        Get WINA synthesis performance metrics.
        
        Returns:
            WINA synthesis metrics
        """
        try:
            response = await self.client.get("/api/v1/wina-rego-synthesis/metrics")
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get WINA synthesis metrics: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting WINA metrics: {e}")
            raise


# Global client instance
gs_service_client = GSServiceClient()
