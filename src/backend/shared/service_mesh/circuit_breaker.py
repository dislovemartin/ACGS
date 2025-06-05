"""
Circuit breaker implementation for ACGS-PGP service resilience.

Provides circuit breaker pattern to prevent cascading failures
and improve system resilience in microservices architecture.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast, not allowing requests
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    state_changes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    time_in_open_state: float = 0.0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return 100.0 - self.failure_rate


class CircuitBreaker:
    """
    Circuit breaker implementation for service resilience.
    
    Implements the circuit breaker pattern to prevent cascading failures
    by monitoring service health and failing fast when necessary.
    """
    
    def __init__(
        self,
        threshold: int = 5,
        timeout: float = 60.0,
        recovery_timeout: float = 30.0,
        minimum_requests: int = 10
    ):
        """
        Initialize circuit breaker.
        
        Args:
            threshold: Number of failures before opening circuit
            timeout: Time to wait before attempting recovery (seconds)
            recovery_timeout: Time to wait in half-open state (seconds)
            minimum_requests: Minimum requests before calculating failure rate
        """
        self.threshold = threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.minimum_requests = minimum_requests
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.last_state_change = time.time()
        self.half_open_start_time = 0.0
        
        self.metrics = CircuitBreakerMetrics()
        self._state_change_callbacks: Dict[CircuitBreakerState, list] = {
            state: [] for state in CircuitBreakerState
        }
    
    def can_execute(self) -> bool:
        """
        Check if request can be executed based on circuit breaker state.
        
        Returns:
            True if request can proceed, False otherwise
        """
        current_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        elif self.state == CircuitBreakerState.OPEN:
            # Check if timeout has elapsed to move to half-open
            if current_time - self.last_failure_time >= self.timeout:
                self._transition_to_half_open()
                return True
            return False
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Check if recovery timeout has elapsed
            if current_time - self.half_open_start_time >= self.recovery_timeout:
                # If no failures during recovery period, close circuit
                self._transition_to_closed()
                return True
            return True
        
        return False
    
    def record_success(self):
        """Record successful request."""
        current_time = time.time()
        
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.last_success_time = current_time
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Success in half-open state, transition to closed
            self._transition_to_closed()
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed request."""
        current_time = time.time()
        
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.last_failure_time = current_time
        
        self.failure_count += 1
        self.last_failure_time = current_time
        
        if self.state == CircuitBreakerState.CLOSED:
            # Check if we should open the circuit
            if self._should_open_circuit():
                self._transition_to_open()
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Failure in half-open state, go back to open
            self._transition_to_open()
    
    def _should_open_circuit(self) -> bool:
        """
        Determine if circuit should be opened based on failure threshold.
        
        Returns:
            True if circuit should be opened
        """
        # Need minimum number of requests to make decision
        if self.metrics.total_requests < self.minimum_requests:
            return False
        
        # Check if failure count exceeds threshold
        if self.failure_count >= self.threshold:
            return True
        
        # Check failure rate (alternative threshold)
        failure_rate_threshold = 50.0  # 50% failure rate
        if self.metrics.failure_rate >= failure_rate_threshold:
            return True
        
        return False
    
    def _transition_to_open(self):
        """Transition circuit breaker to open state."""
        if self.state != CircuitBreakerState.OPEN:
            old_state = self.state
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = time.time()
            self.metrics.state_changes += 1
            
            logger.warning(
                f"Circuit breaker opened: {self.failure_count} failures, "
                f"failure rate: {self.metrics.failure_rate:.1f}%"
            )
            
            self._notify_state_change(old_state, CircuitBreakerState.OPEN)
    
    def _transition_to_half_open(self):
        """Transition circuit breaker to half-open state."""
        if self.state != CircuitBreakerState.HALF_OPEN:
            old_state = self.state
            self.state = CircuitBreakerState.HALF_OPEN
            self.half_open_start_time = time.time()
            self.last_state_change = time.time()
            self.metrics.state_changes += 1
            
            logger.info("Circuit breaker moved to half-open state for testing")
            
            self._notify_state_change(old_state, CircuitBreakerState.HALF_OPEN)
    
    def _transition_to_closed(self):
        """Transition circuit breaker to closed state."""
        if self.state != CircuitBreakerState.CLOSED:
            old_state = self.state
            
            # Calculate time spent in open state
            if old_state == CircuitBreakerState.OPEN:
                self.metrics.time_in_open_state += time.time() - self.last_state_change
            
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.last_state_change = time.time()
            self.metrics.state_changes += 1
            
            logger.info("Circuit breaker closed - service recovered")
            
            self._notify_state_change(old_state, CircuitBreakerState.CLOSED)
    
    def _notify_state_change(self, old_state: CircuitBreakerState, new_state: CircuitBreakerState):
        """Notify registered callbacks of state change."""
        for callback in self._state_change_callbacks.get(new_state, []):
            try:
                callback(old_state, new_state, self.get_status())
            except Exception as e:
                logger.error(f"Error in circuit breaker callback: {e}")
    
    def add_state_change_callback(self, state: CircuitBreakerState, callback: Callable):
        """
        Add callback for state change notifications.
        
        Args:
            state: State to listen for
            callback: Function to call on state change
        """
        self._state_change_callbacks[state].append(callback)
    
    def force_open(self):
        """Force circuit breaker to open state."""
        self._transition_to_open()
        logger.warning("Circuit breaker manually forced to open state")
    
    def force_close(self):
        """Force circuit breaker to closed state."""
        self._transition_to_closed()
        logger.info("Circuit breaker manually forced to closed state")
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.last_state_change = time.time()
        self.half_open_start_time = 0.0
        
        # Reset metrics
        self.metrics = CircuitBreakerMetrics()
        
        logger.info("Circuit breaker reset to initial state")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current circuit breaker status.
        
        Returns:
            Status information dictionary
        """
        current_time = time.time()
        
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "threshold": self.threshold,
            "timeout": self.timeout,
            "last_failure_time": self.last_failure_time,
            "time_since_last_failure": current_time - self.last_failure_time if self.last_failure_time > 0 else None,
            "time_in_current_state": current_time - self.last_state_change,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "failure_rate": self.metrics.failure_rate,
                "success_rate": self.metrics.success_rate,
                "state_changes": self.metrics.state_changes,
                "time_in_open_state": self.metrics.time_in_open_state
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def is_healthy(self) -> bool:
        """
        Check if circuit breaker indicates healthy service.
        
        Returns:
            True if service appears healthy
        """
        return (
            self.state == CircuitBreakerState.CLOSED and
            self.metrics.failure_rate < 10.0  # Less than 10% failure rate
        )


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    
    Provides centralized management of circuit breakers for different
    services or operations.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(
        self,
        name: str,
        threshold: int = 5,
        timeout: float = 60.0,
        recovery_timeout: float = 30.0,
        minimum_requests: int = 10
    ) -> CircuitBreaker:
        """
        Get or create circuit breaker for a named service/operation.
        
        Args:
            name: Name of the service/operation
            threshold: Failure threshold
            timeout: Recovery timeout
            recovery_timeout: Half-open timeout
            minimum_requests: Minimum requests for failure rate calculation
            
        Returns:
            Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                threshold=threshold,
                timeout=timeout,
                recovery_timeout=recovery_timeout,
                minimum_requests=minimum_requests
            )
        
        return self.circuit_breakers[name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all circuit breakers.
        
        Returns:
            Status information for all circuit breakers
        """
        return {
            name: breaker.get_status()
            for name, breaker in self.circuit_breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self.circuit_breakers.values():
            breaker.reset()
    
    def get_unhealthy_services(self) -> List[str]:
        """
        Get list of services with unhealthy circuit breakers.
        
        Returns:
            List of service names with unhealthy circuit breakers
        """
        return [
            name for name, breaker in self.circuit_breakers.items()
            if not breaker.is_healthy()
        ]


# Global circuit breaker manager
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """
    Get the global circuit breaker manager.
    
    Returns:
        Circuit breaker manager instance
    """
    global _circuit_breaker_manager
    
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    
    return _circuit_breaker_manager
