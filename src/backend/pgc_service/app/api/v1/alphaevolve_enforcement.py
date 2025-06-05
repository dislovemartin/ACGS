# backend/pgc_service/app/api/v1/alphaevolve_enforcement.py

"""
AlphaEvolve Real-time Policy Enforcement

This module provides real-time policy enforcement capabilities specifically
designed for evolutionary computation systems, with sub-50ms latency requirements.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import time
import uuid
from datetime import datetime
import asyncio

from ...core.datalog_engine import datalog_engine
from ...core.policy_manager import policy_manager
from ...services.integrity_client import integrity_service_client

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ECProposal:
    """Simplified EC proposal for enforcement evaluation."""
    def __init__(self, proposal_id: str, solution_code: str, generation: int, fitness_context: Dict[str, Any]):
        self.proposal_id = proposal_id
        self.solution_code = solution_code
        self.generation = generation
        self.fitness_context = fitness_context


class ECEnforcementDecision:
    """Real-time enforcement decision for EC proposals."""
    def __init__(self, proposal_id: str, decision: str, latency_ms: float, 
                 governance_penalty: float = 0.0, explanation: str = ""):
        self.proposal_id = proposal_id
        self.decision = decision
        self.latency_ms = latency_ms
        self.governance_penalty = governance_penalty
        self.explanation = explanation
        self.timestamp = datetime.utcnow()


class ECEnforcementCache:
    """High-performance cache for EC enforcement decisions."""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def get(self, key: str) -> Optional[ECEnforcementDecision]:
        """Get cached decision if available and not expired."""
        if key not in self.cache:
            return None
        
        # Check TTL
        if time.time() - self.access_times[key] > self.ttl_seconds:
            del self.cache[key]
            del self.access_times[key]
            return None
        
        # Update access time
        self.access_times[key] = time.time()
        return self.cache[key]
    
    def put(self, key: str, decision: ECEnforcementDecision):
        """Cache enforcement decision."""
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = decision
        self.access_times[key] = time.time()
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_times.clear()


# Global enforcement cache
ec_enforcement_cache = ECEnforcementCache()


@router.post("/evaluate-batch")
async def evaluate_ec_batch(request_data: Dict[str, Any]):
    """
    Evaluate a batch of EC proposals for real-time enforcement.
    
    Optimized for sub-50ms latency with caching and parallel processing.
    """
    start_time = time.time()
    
    try:
        proposals = request_data.get("proposals", [])
        context = request_data.get("context", "default")
        real_time = request_data.get("real_time", True)
        
        if not proposals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No proposals provided for evaluation"
            )
        
        logger.info(f"Evaluating batch of {len(proposals)} EC proposals")
        
        # Convert to ECProposal objects
        ec_proposals = []
        for p in proposals:
            ec_proposal = ECProposal(
                proposal_id=p.get("proposal_id", str(uuid.uuid4())),
                solution_code=p.get("solution_code", ""),
                generation=p.get("generation", 0),
                fitness_context=p.get("fitness_context", {})
            )
            ec_proposals.append(ec_proposal)
        
        # Evaluate proposals with performance optimization
        if real_time and len(ec_proposals) <= 10:
            # Use parallel processing for small batches
            decisions = await _evaluate_proposals_parallel(ec_proposals, context)
        else:
            # Use sequential processing for large batches
            decisions = await _evaluate_proposals_sequential(ec_proposals, context)
        
        total_time_ms = (time.time() - start_time) * 1000
        
        # Calculate batch statistics
        allowed_count = len([d for d in decisions if d.decision == "allow"])
        denied_count = len([d for d in decisions if d.decision == "deny"])
        avg_latency = sum(d.latency_ms for d in decisions) / len(decisions) if decisions else 0
        avg_penalty = sum(d.governance_penalty for d in decisions) / len(decisions) if decisions else 0
        
        response = {
            "evaluation_id": str(uuid.uuid4()),
            "decisions": [
                {
                    "proposal_id": d.proposal_id,
                    "decision": d.decision,
                    "latency_ms": d.latency_ms,
                    "governance_penalty": d.governance_penalty,
                    "explanation": d.explanation,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in decisions
            ],
            "batch_summary": {
                "total_proposals": len(ec_proposals),
                "allowed_proposals": allowed_count,
                "denied_proposals": denied_count,
                "average_latency_ms": avg_latency,
                "average_governance_penalty": avg_penalty,
                "total_processing_time_ms": total_time_ms,
                "cache_hit_rate": _calculate_cache_hit_rate(ec_proposals)
            },
            "performance_metrics": {
                "target_latency_ms": 50,
                "achieved_latency_ms": avg_latency,
                "performance_ratio": 50 / avg_latency if avg_latency > 0 else 1.0,
                "real_time_capable": avg_latency <= 50
            }
        }
        
        logger.info(f"Batch evaluation completed in {total_time_ms:.2f}ms, avg latency: {avg_latency:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error during EC batch evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"EC batch evaluation failed: {str(e)}"
        )


@router.post("/evaluate-single")
async def evaluate_single_proposal(request_data: Dict[str, Any]):
    """
    Evaluate a single EC proposal with maximum performance optimization.
    
    Target: sub-20ms latency for single proposal evaluation.
    """
    start_time = time.time()
    
    try:
        proposal_data = request_data.get("proposal", {})
        context = request_data.get("context", "default")
        
        # Create EC proposal
        ec_proposal = ECProposal(
            proposal_id=proposal_data.get("proposal_id", str(uuid.uuid4())),
            solution_code=proposal_data.get("solution_code", ""),
            generation=proposal_data.get("generation", 0),
            fitness_context=proposal_data.get("fitness_context", {})
        )
        
        # Evaluate with maximum optimization
        decision = await _evaluate_single_proposal_optimized(ec_proposal, context)
        
        total_time_ms = (time.time() - start_time) * 1000
        
        response = {
            "proposal_id": decision.proposal_id,
            "decision": decision.decision,
            "latency_ms": decision.latency_ms,
            "governance_penalty": decision.governance_penalty,
            "explanation": decision.explanation,
            "timestamp": decision.timestamp.isoformat(),
            "performance_metrics": {
                "target_latency_ms": 20,
                "achieved_latency_ms": decision.latency_ms,
                "total_processing_time_ms": total_time_ms,
                "real_time_capable": decision.latency_ms <= 20
            }
        }
        
        logger.debug(f"Single proposal evaluation completed in {decision.latency_ms:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error during single proposal evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Single proposal evaluation failed: {str(e)}"
        )


@router.get("/cache/stats")
async def get_cache_statistics():
    """Get enforcement cache statistics for monitoring."""
    return {
        "cache_size": len(ec_enforcement_cache.cache),
        "max_size": ec_enforcement_cache.max_size,
        "ttl_seconds": ec_enforcement_cache.ttl_seconds,
        "utilization": len(ec_enforcement_cache.cache) / ec_enforcement_cache.max_size,
        "oldest_entry_age": _get_oldest_cache_entry_age(),
        "newest_entry_age": _get_newest_cache_entry_age()
    }


@router.post("/cache/clear")
async def clear_enforcement_cache():
    """Clear the enforcement cache (admin operation)."""
    ec_enforcement_cache.clear()
    logger.info("EC enforcement cache cleared")
    return {"message": "Enforcement cache cleared successfully"}


# Helper functions

async def _evaluate_proposals_parallel(proposals: List[ECProposal], context: str) -> List[ECEnforcementDecision]:
    """Evaluate proposals in parallel for maximum performance."""
    tasks = []
    for proposal in proposals:
        task = asyncio.create_task(_evaluate_single_proposal_optimized(proposal, context))
        tasks.append(task)
    
    decisions = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    valid_decisions = []
    for i, decision in enumerate(decisions):
        if isinstance(decision, Exception):
            logger.error(f"Error evaluating proposal {proposals[i].proposal_id}: {decision}")
            # Create fallback decision
            fallback_decision = ECEnforcementDecision(
                proposal_id=proposals[i].proposal_id,
                decision="deny",
                latency_ms=1.0,
                governance_penalty=1.0,
                explanation=f"Evaluation error: {str(decision)}"
            )
            valid_decisions.append(fallback_decision)
        else:
            valid_decisions.append(decision)
    
    return valid_decisions


async def _evaluate_proposals_sequential(proposals: List[ECProposal], context: str) -> List[ECEnforcementDecision]:
    """Evaluate proposals sequentially for large batches."""
    decisions = []
    for proposal in proposals:
        decision = await _evaluate_single_proposal_optimized(proposal, context)
        decisions.append(decision)
    return decisions


async def _evaluate_single_proposal_optimized(proposal: ECProposal, context: str) -> ECEnforcementDecision:
    """Evaluate a single proposal with maximum optimization."""
    eval_start_time = time.time()
    
    # Generate cache key
    cache_key = _generate_cache_key(proposal, context)
    
    # Check cache first
    cached_decision = ec_enforcement_cache.get(cache_key)
    if cached_decision:
        # Update latency to reflect cache hit
        cached_decision.latency_ms = (time.time() - eval_start_time) * 1000
        return cached_decision
    
    # Perform actual evaluation
    try:
        # Simplified fast evaluation logic
        decision = "allow"
        governance_penalty = 0.0
        explanation = "Fast evaluation passed"
        
        # Quick safety checks
        code = proposal.solution_code.lower()
        if any(keyword in code for keyword in ['unsafe', 'dangerous', 'harmful', 'malicious']):
            decision = "deny"
            governance_penalty = 0.5
            explanation = "Safety violation detected"
        
        # Quick complexity check
        if len(proposal.solution_code) > 5000:
            governance_penalty += 0.1
            explanation += ". Code complexity penalty applied"
        
        # Quick generation check
        if proposal.generation > 1000:
            governance_penalty += 0.05
            explanation += ". High generation penalty applied"
        
        latency_ms = (time.time() - eval_start_time) * 1000
        
        enforcement_decision = ECEnforcementDecision(
            proposal_id=proposal.proposal_id,
            decision=decision,
            latency_ms=latency_ms,
            governance_penalty=governance_penalty,
            explanation=explanation
        )
        
        # Cache the decision
        ec_enforcement_cache.put(cache_key, enforcement_decision)
        
        return enforcement_decision
        
    except Exception as e:
        latency_ms = (time.time() - eval_start_time) * 1000
        logger.error(f"Error evaluating proposal {proposal.proposal_id}: {e}")
        
        return ECEnforcementDecision(
            proposal_id=proposal.proposal_id,
            decision="deny",
            latency_ms=latency_ms,
            governance_penalty=1.0,
            explanation=f"Evaluation error: {str(e)}"
        )


def _generate_cache_key(proposal: ECProposal, context: str) -> str:
    """Generate cache key for proposal evaluation."""
    # Use hash of solution code + context for caching
    import hashlib
    content = f"{proposal.solution_code}:{context}:{proposal.generation}"
    return hashlib.md5(content.encode()).hexdigest()


def _calculate_cache_hit_rate(proposals: List[ECProposal]) -> float:
    """Calculate cache hit rate for the current batch."""
    hits = 0
    for proposal in proposals:
        cache_key = _generate_cache_key(proposal, "default")
        if ec_enforcement_cache.get(cache_key):
            hits += 1
    
    return hits / len(proposals) if proposals else 0.0


def _get_oldest_cache_entry_age() -> float:
    """Get age of oldest cache entry in seconds."""
    if not ec_enforcement_cache.access_times:
        return 0.0
    
    oldest_time = min(ec_enforcement_cache.access_times.values())
    return time.time() - oldest_time


def _get_newest_cache_entry_age() -> float:
    """Get age of newest cache entry in seconds."""
    if not ec_enforcement_cache.access_times:
        return 0.0
    
    newest_time = max(ec_enforcement_cache.access_times.values())
    return time.time() - newest_time
