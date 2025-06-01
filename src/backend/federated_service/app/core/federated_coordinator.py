"""
Federated Coordinator for ACGS-PGP

Coordinates federated evaluation tasks across multiple nodes and manages
the overall federated evaluation lifecycle.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from .federated_evaluator import federated_evaluator
from .secure_aggregation import secure_aggregator
from .privacy_metrics import differential_privacy_manager

logger = logging.getLogger(__name__)


class FederatedCoordinator:
    """
    Central coordinator for federated evaluation framework.
    
    Manages the lifecycle of federated evaluations and coordinates
    between different components.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.coordinator_metrics = {
            "total_coordinated_evaluations": 0,
            "successful_coordinations": 0,
            "failed_coordinations": 0,
            "average_coordination_time": 0.0
        }
        
        logger.info("Initialized Federated Coordinator")
    
    async def initialize(self):
        """Initialize the federated coordinator."""
        try:
            if self.is_initialized:
                return
            
            # Initialize core components
            await federated_evaluator.initialize()
            await secure_aggregator.initialize()
            await differential_privacy_manager.initialize()
            
            self.is_initialized = True
            logger.info("Federated Coordinator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Federated Coordinator: {e}")
            raise
    
    async def coordinate_evaluation(
        self,
        evaluation_request: Dict[str, Any]
    ) -> str:
        """
        Coordinate a federated evaluation across multiple nodes.
        
        Args:
            evaluation_request: Evaluation request parameters
            
        Returns:
            Task ID for the coordinated evaluation
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Submit to federated evaluator
            task_id = await federated_evaluator.submit_evaluation(evaluation_request)
            
            # Update coordination metrics
            self.coordinator_metrics["total_coordinated_evaluations"] += 1
            
            logger.info(f"Coordinated federated evaluation: {task_id}")
            return task_id
            
        except Exception as e:
            self.coordinator_metrics["failed_coordinations"] += 1
            logger.error(f"Failed to coordinate evaluation: {e}")
            raise
    
    async def get_coordination_status(self) -> Dict[str, Any]:
        """Get the status of the federated coordinator."""
        return {
            "is_initialized": self.is_initialized,
            "metrics": self.coordinator_metrics.copy(),
            "component_status": {
                "federated_evaluator": "initialized" if federated_evaluator else "not_initialized",
                "secure_aggregator": "initialized" if secure_aggregator else "not_initialized",
                "privacy_manager": "initialized" if differential_privacy_manager else "not_initialized"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def shutdown(self):
        """Shutdown the federated coordinator."""
        try:
            logger.info("Shutting down Federated Coordinator...")
            
            # Shutdown components
            if federated_evaluator:
                await federated_evaluator.shutdown()
            
            if secure_aggregator:
                await secure_aggregator.shutdown()
            
            if differential_privacy_manager:
                await differential_privacy_manager.shutdown()
            
            self.is_initialized = False
            logger.info("Federated Coordinator shutdown complete")
            
        except Exception as e:
            logger.error(f"Failed to shutdown Federated Coordinator: {e}")


# Global federated coordinator instance
federated_coordinator = FederatedCoordinator()
