"""
Enhanced Voting Client for Constitutional Council
Implements httpx async client with proper error handling, rate limiting, and retry logic.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import ACAmendment, ACAmendmentVote, User
from ..schemas import ACAmendmentVoteCreate
# from shared.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class VotingClientError(Exception):
    """Custom exception for voting client errors."""
    pass


class RetryStrategy(Enum):
    """Retry strategies for failed requests."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE_RETRY = "immediate_retry"


@dataclass
class VotingClientConfig:
    """Configuration for the voting client."""
    base_url: str = "http://localhost:8001"
    timeout: float = 30.0
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    rate_limit_requests_per_minute: int = 60
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class EnhancedVotingClient:
    """Enhanced voting client with httpx, error handling, and rate limiting."""
    
    def __init__(self, config: VotingClientConfig):
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        self.redis_client = None
        
        # Rate limiting
        self.request_timestamps: List[float] = []
        
        # Circuit breaker
        self.circuit_breaker_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        
        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
    async def initialize(self):
        """Initialize the voting client."""
        try:
            # Initialize httpx client
            timeout = httpx.Timeout(self.config.timeout)
            self.client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=timeout,
                headers={"User-Agent": "ACGS-PGP-VotingClient/1.0"}
            )
            
            # Initialize Redis client for caching
            if self.config.enable_caching:
                # self.redis_client = await get_redis_client("voting_client")
                logger.info("Redis caching disabled for voting client")
            
            logger.info("Enhanced voting client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize voting client: {e}")
            raise VotingClientError(f"Initialization failed: {e}")
    
    async def close(self):
        """Close the voting client."""
        if self.client:
            await self.client.aclose()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Enhanced voting client closed")
    
    async def submit_vote(
        self,
        amendment_id: int,
        vote_data: ACAmendmentVoteCreate,
        auth_token: str
    ) -> Dict[str, Any]:
        """Submit a vote with enhanced error handling and retry logic."""
        if not await self._check_circuit_breaker():
            raise VotingClientError("Circuit breaker is open")
        
        if not await self._check_rate_limit():
            raise VotingClientError("Rate limit exceeded")
        
        for attempt in range(self.config.max_retries + 1):
            try:
                result = await self._submit_vote_attempt(amendment_id, vote_data, auth_token)
                await self._record_success()
                return result
                
            except Exception as e:
                await self._record_failure()
                
                if attempt == self.config.max_retries:
                    logger.error(f"Vote submission failed after {self.config.max_retries} retries: {e}")
                    raise VotingClientError(f"Vote submission failed: {e}")
                
                # Calculate retry delay
                delay = await self._calculate_retry_delay(attempt)
                logger.warning(f"Vote submission attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
        
        raise VotingClientError("Vote submission failed after all retries")
    
    async def _submit_vote_attempt(
        self,
        amendment_id: int,
        vote_data: ACAmendmentVoteCreate,
        auth_token: str
    ) -> Dict[str, Any]:
        """Single attempt to submit a vote."""
        if not self.client:
            raise VotingClientError("Client not initialized")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        endpoint = f"/api/v1/constitutional-council/amendments/{amendment_id}/votes"
        
        # Check cache first
        if self.config.enable_caching and self.redis_client:
            cache_key = f"vote_submission:{amendment_id}:{vote_data.voter_id}"
            cached_result = await self.redis_client.get_json(cache_key)
            if cached_result:
                logger.info(f"Returning cached vote result for amendment {amendment_id}")
                return cached_result
        
        self.total_requests += 1
        
        response = await self.client.post(
            endpoint,
            json=vote_data.model_dump(),
            headers=headers
        )
        
        if response.status_code == 201:
            result = {
                "success": True,
                "vote_id": response.json().get("id"),
                "amendment_id": amendment_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache successful result
            if self.config.enable_caching and self.redis_client:
                cache_key = f"vote_submission:{amendment_id}:{vote_data.voter_id}"
                await self.redis_client.set_json(cache_key, result, self.config.cache_ttl)
            
            return result
        
        elif response.status_code == 400:
            error_detail = response.json().get("detail", "Bad request")
            raise VotingClientError(f"Invalid vote data: {error_detail}")
        
        elif response.status_code == 403:
            raise VotingClientError("Insufficient permissions to vote")
        
        elif response.status_code == 404:
            raise VotingClientError(f"Amendment {amendment_id} not found")
        
        elif response.status_code == 409:
            raise VotingClientError("Vote already exists for this amendment")
        
        else:
            response.raise_for_status()
    
    async def get_amendment_votes(
        self,
        amendment_id: int,
        auth_token: str
    ) -> List[Dict[str, Any]]:
        """Get all votes for an amendment."""
        if not self.client:
            raise VotingClientError("Client not initialized")
        
        # Check cache first
        if self.config.enable_caching and self.redis_client:
            cache_key = f"amendment_votes:{amendment_id}"
            cached_votes = await self.redis_client.get_json(cache_key)
            if cached_votes:
                logger.info(f"Returning cached votes for amendment {amendment_id}")
                return cached_votes
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        endpoint = f"/api/v1/constitutional-council/amendments/{amendment_id}/votes"
        
        response = await self.client.get(endpoint, headers=headers)
        response.raise_for_status()
        
        votes = response.json()
        
        # Cache the result
        if self.config.enable_caching and self.redis_client:
            cache_key = f"amendment_votes:{amendment_id}"
            await self.redis_client.set_json(cache_key, votes, self.config.cache_ttl)
        
        return votes
    
    async def _check_rate_limit(self) -> bool:
        """Check if request is within rate limit."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        # Check if we're within the rate limit
        if len(self.request_timestamps) >= self.config.rate_limit_requests_per_minute:
            return False
        
        # Add current timestamp
        self.request_timestamps.append(current_time)
        return True
    
    async def _check_circuit_breaker(self) -> bool:
        """Check circuit breaker state."""
        current_time = time.time()
        
        if self.circuit_breaker_state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if current_time - self.last_failure_time > self.config.circuit_breaker_recovery_timeout:
                self.circuit_breaker_state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker moved to HALF_OPEN state")
                return True
            return False
        
        return True
    
    async def _record_success(self):
        """Record a successful request."""
        self.successful_requests += 1
        
        if self.circuit_breaker_state == CircuitBreakerState.HALF_OPEN:
            self.circuit_breaker_state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            logger.info("Circuit breaker moved to CLOSED state")
    
    async def _record_failure(self):
        """Record a failed request."""
        self.failed_requests += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.circuit_breaker_failure_threshold:
            self.circuit_breaker_state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker moved to OPEN state")
    
    async def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay based on strategy."""
        if self.config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return min(2 ** attempt, 30)  # Max 30 seconds
        elif self.config.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            return min(attempt * 2, 30)  # Max 30 seconds
        else:  # IMMEDIATE_RETRY
            return 0.1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics."""
        success_rate = (
            self.successful_requests / self.total_requests 
            if self.total_requests > 0 else 0
        )
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "circuit_breaker_state": self.circuit_breaker_state.value,
            "failure_count": self.failure_count
        }


# Global voting client instance
voting_client_config = VotingClientConfig()
enhanced_voting_client = EnhancedVotingClient(voting_client_config)
