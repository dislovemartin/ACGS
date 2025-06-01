"""
Result Aggregation and WebSocket Streaming for ACGS-PGP Task 7
Provides real-time result aggregation with Byzantine fault tolerance
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Set, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import statistics
from collections import defaultdict, Counter

from fastapi import WebSocket, WebSocketDisconnect
import numpy as np

logger = logging.getLogger(__name__)


class AggregationStrategy(str, Enum):
    """Result aggregation strategies."""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    BYZANTINE_FAULT_TOLERANT = "byzantine_fault_tolerant"
    CONSENSUS_THRESHOLD = "consensus_threshold"
    FIRST_VALID = "first_valid"


class ConflictResolution(str, Enum):
    """Conflict resolution methods for disagreeing results."""
    HIGHEST_CONFIDENCE = "highest_confidence"
    MOST_RECENT = "most_recent"
    WEIGHTED_CONSENSUS = "weighted_consensus"
    EXPERT_OVERRIDE = "expert_override"


@dataclass
class ValidationResult:
    """Individual validation result from a parallel task."""
    task_id: str
    validator_id: str
    result: Dict[str, Any]
    confidence_score: float
    execution_time_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_valid(self) -> bool:
        """Check if result is valid."""
        return (
            self.confidence_score > 0.0 and
            self.result is not None and
            'status' in self.result
        )


@dataclass
class AggregatedResult:
    """Aggregated result from multiple validation results."""
    task_id: str
    aggregation_strategy: AggregationStrategy
    final_result: Dict[str, Any]
    confidence_score: float
    individual_results: List[ValidationResult]
    consensus_level: float
    conflicts_detected: List[str] = field(default_factory=list)
    resolution_method: Optional[ConflictResolution] = None
    aggregation_time_ms: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def total_validators(self) -> int:
        return len(self.individual_results)
    
    @property
    def valid_results(self) -> List[ValidationResult]:
        return [r for r in self.individual_results if r.is_valid]
    
    @property
    def average_execution_time(self) -> float:
        if not self.valid_results:
            return 0.0
        return statistics.mean([r.execution_time_ms for r in self.valid_results])


class ByzantineFaultTolerantAggregator:
    """Byzantine fault-tolerant result aggregation."""
    
    def __init__(self, fault_tolerance: float = 0.33):
        """
        Initialize aggregator.
        
        Args:
            fault_tolerance: Maximum fraction of faulty validators (default: 1/3)
        """
        self.fault_tolerance = fault_tolerance
        self.outlier_threshold = 2.0  # Standard deviations for outlier detection
    
    def aggregate_results(
        self, 
        results: List[ValidationResult],
        strategy: AggregationStrategy = AggregationStrategy.BYZANTINE_FAULT_TOLERANT
    ) -> AggregatedResult:
        """Aggregate multiple validation results."""
        start_time = time.time()
        
        if not results:
            return self._create_empty_result("no_results", strategy)
        
        # Filter valid results
        valid_results = [r for r in results if r.is_valid]
        if not valid_results:
            return self._create_empty_result("no_valid_results", strategy)
        
        # Apply aggregation strategy
        if strategy == AggregationStrategy.MAJORITY_VOTE:
            aggregated = self._majority_vote_aggregation(valid_results)
        elif strategy == AggregationStrategy.WEIGHTED_AVERAGE:
            aggregated = self._weighted_average_aggregation(valid_results)
        elif strategy == AggregationStrategy.BYZANTINE_FAULT_TOLERANT:
            aggregated = self._byzantine_fault_tolerant_aggregation(valid_results)
        elif strategy == AggregationStrategy.CONSENSUS_THRESHOLD:
            aggregated = self._consensus_threshold_aggregation(valid_results)
        elif strategy == AggregationStrategy.FIRST_VALID:
            aggregated = self._first_valid_aggregation(valid_results)
        else:
            aggregated = self._majority_vote_aggregation(valid_results)
        
        aggregated.aggregation_time_ms = (time.time() - start_time) * 1000
        return aggregated
    
    def _majority_vote_aggregation(self, results: List[ValidationResult]) -> AggregatedResult:
        """Aggregate using majority vote."""
        if not results:
            return self._create_empty_result("no_results", AggregationStrategy.MAJORITY_VOTE)
        
        # Count votes for each status
        status_votes = Counter()
        confidence_by_status = defaultdict(list)
        
        for result in results:
            status = result.result.get('status', 'unknown')
            status_votes[status] += 1
            confidence_by_status[status].append(result.confidence_score)
        
        # Get majority status
        majority_status = status_votes.most_common(1)[0][0]
        majority_count = status_votes[majority_status]
        
        # Calculate consensus level
        consensus_level = majority_count / len(results)
        
        # Calculate average confidence for majority status
        avg_confidence = statistics.mean(confidence_by_status[majority_status])
        
        # Create final result
        final_result = {
            'status': majority_status,
            'vote_count': majority_count,
            'total_votes': len(results),
            'consensus_level': consensus_level
        }
        
        return AggregatedResult(
            task_id=results[0].task_id,
            aggregation_strategy=AggregationStrategy.MAJORITY_VOTE,
            final_result=final_result,
            confidence_score=avg_confidence,
            individual_results=results,
            consensus_level=consensus_level
        )
    
    def _weighted_average_aggregation(self, results: List[ValidationResult]) -> AggregatedResult:
        """Aggregate using confidence-weighted average."""
        if not results:
            return self._create_empty_result("no_results", AggregationStrategy.WEIGHTED_AVERAGE)
        
        # Calculate weighted averages for numeric fields
        total_weight = sum(r.confidence_score for r in results)
        
        if total_weight == 0:
            return self._create_empty_result("zero_weight", AggregationStrategy.WEIGHTED_AVERAGE)
        
        # Aggregate numeric scores
        weighted_scores = {}
        for result in results:
            weight = result.confidence_score / total_weight
            for key, value in result.result.items():
                if isinstance(value, (int, float)):
                    if key not in weighted_scores:
                        weighted_scores[key] = 0.0
                    weighted_scores[key] += value * weight
        
        # Calculate consensus level based on confidence variance
        confidences = [r.confidence_score for r in results]
        confidence_variance = statistics.variance(confidences) if len(confidences) > 1 else 0.0
        consensus_level = max(0.0, 1.0 - confidence_variance)
        
        final_result = {
            'aggregation_method': 'weighted_average',
            'weighted_scores': weighted_scores,
            'total_weight': total_weight
        }
        
        avg_confidence = statistics.mean(confidences)
        
        return AggregatedResult(
            task_id=results[0].task_id,
            aggregation_strategy=AggregationStrategy.WEIGHTED_AVERAGE,
            final_result=final_result,
            confidence_score=avg_confidence,
            individual_results=results,
            consensus_level=consensus_level
        )
    
    def _byzantine_fault_tolerant_aggregation(self, results: List[ValidationResult]) -> AggregatedResult:
        """Byzantine fault-tolerant aggregation with outlier detection."""
        if not results:
            return self._create_empty_result("no_results", AggregationStrategy.BYZANTINE_FAULT_TOLERANT)
        
        # Check if we have enough results for Byzantine fault tolerance
        min_results = int(3 * self.fault_tolerance * len(results)) + 1
        if len(results) < min_results:
            logger.warning(f"Insufficient results for Byzantine fault tolerance: {len(results)} < {min_results}")
            return self._majority_vote_aggregation(results)
        
        # Detect outliers based on confidence scores
        confidences = [r.confidence_score for r in results]
        if len(confidences) > 2:
            mean_confidence = statistics.mean(confidences)
            std_confidence = statistics.stdev(confidences)
            
            # Filter outliers
            filtered_results = []
            outliers = []
            
            for result in results:
                z_score = abs(result.confidence_score - mean_confidence) / std_confidence if std_confidence > 0 else 0
                if z_score <= self.outlier_threshold:
                    filtered_results.append(result)
                else:
                    outliers.append(result.validator_id)
            
            if filtered_results:
                results = filtered_results
        
        # Apply majority vote on filtered results
        aggregated = self._majority_vote_aggregation(results)
        aggregated.aggregation_strategy = AggregationStrategy.BYZANTINE_FAULT_TOLERANT
        
        if outliers:
            aggregated.conflicts_detected.append(f"Outliers detected: {outliers}")
            aggregated.resolution_method = ConflictResolution.WEIGHTED_CONSENSUS
        
        return aggregated
    
    def _consensus_threshold_aggregation(self, results: List[ValidationResult], threshold: float = 0.67) -> AggregatedResult:
        """Aggregate requiring consensus threshold."""
        majority_result = self._majority_vote_aggregation(results)
        
        if majority_result.consensus_level >= threshold:
            majority_result.aggregation_strategy = AggregationStrategy.CONSENSUS_THRESHOLD
            return majority_result
        else:
            # Consensus not reached
            final_result = {
                'status': 'consensus_not_reached',
                'consensus_level': majority_result.consensus_level,
                'required_threshold': threshold,
                'message': f"Consensus threshold {threshold} not met (actual: {majority_result.consensus_level:.3f})"
            }
            
            return AggregatedResult(
                task_id=results[0].task_id,
                aggregation_strategy=AggregationStrategy.CONSENSUS_THRESHOLD,
                final_result=final_result,
                confidence_score=0.0,
                individual_results=results,
                consensus_level=majority_result.consensus_level,
                conflicts_detected=["consensus_threshold_not_met"]
            )
    
    def _first_valid_aggregation(self, results: List[ValidationResult]) -> AggregatedResult:
        """Return first valid result (for fast response)."""
        if not results:
            return self._create_empty_result("no_results", AggregationStrategy.FIRST_VALID)
        
        # Sort by timestamp to get truly first result
        sorted_results = sorted(results, key=lambda r: r.timestamp)
        first_result = sorted_results[0]
        
        return AggregatedResult(
            task_id=first_result.task_id,
            aggregation_strategy=AggregationStrategy.FIRST_VALID,
            final_result=first_result.result,
            confidence_score=first_result.confidence_score,
            individual_results=results,
            consensus_level=1.0 / len(results)  # Only one result used
        )
    
    def _create_empty_result(self, reason: str, strategy: AggregationStrategy) -> AggregatedResult:
        """Create empty result for error cases."""
        return AggregatedResult(
            task_id="unknown",
            aggregation_strategy=strategy,
            final_result={'status': 'error', 'reason': reason},
            confidence_score=0.0,
            individual_results=[],
            consensus_level=0.0,
            conflicts_detected=[reason]
        )


class WebSocketStreamer:
    """WebSocket streaming for real-time progress updates."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None) -> None:
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = {
            'client_id': client_id or f"client_{int(time.time() * 1000)}",
            'connected_at': datetime.now(timezone.utc),
            'message_count': 0
        }
        logger.info(f"WebSocket connected: {client_id}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnection."""
        self.active_connections.discard(websocket)
        metadata = self.connection_metadata.pop(websocket, {})
        client_id = metadata.get('client_id', 'unknown')
        logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_progress_update(
        self, 
        task_id: str, 
        progress: float, 
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send progress update to all connected clients."""
        message = {
            'type': 'progress_update',
            'task_id': task_id,
            'progress': progress,
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'details': details or {}
        }
        
        await self._broadcast_message(message)
    
    async def send_result_update(self, result: AggregatedResult) -> None:
        """Send aggregated result to all connected clients."""
        message = {
            'type': 'result_update',
            'task_id': result.task_id,
            'result': result.final_result,
            'confidence_score': result.confidence_score,
            'consensus_level': result.consensus_level,
            'aggregation_strategy': result.aggregation_strategy,
            'timestamp': result.created_at.isoformat(),
            'conflicts': result.conflicts_detected
        }
        
        await self._broadcast_message(message)
    
    async def send_batch_completion(
        self, 
        batch_id: str, 
        total_tasks: int, 
        completed_tasks: int,
        failed_tasks: int,
        execution_time_ms: float
    ) -> None:
        """Send batch completion notification."""
        message = {
            'type': 'batch_completion',
            'batch_id': batch_id,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': completed_tasks / total_tasks if total_tasks > 0 else 0.0,
            'execution_time_ms': execution_time_ms,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        await self._broadcast_message(message)
    
    async def _broadcast_message(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message, default=str)
        disconnected = set()
        
        for websocket in self.active_connections.copy():
            try:
                await websocket.send_text(message_json)
                self.connection_metadata[websocket]['message_count'] += 1
            except WebSocketDisconnect:
                disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        total_messages = sum(
            metadata.get('message_count', 0) 
            for metadata in self.connection_metadata.values()
        )
        
        return {
            'active_connections': len(self.active_connections),
            'total_messages_sent': total_messages,
            'connections': [
                {
                    'client_id': metadata.get('client_id'),
                    'connected_at': metadata.get('connected_at'),
                    'message_count': metadata.get('message_count', 0)
                }
                for metadata in self.connection_metadata.values()
            ]
        }


# Global WebSocket streamer instance
websocket_streamer = WebSocketStreamer()
