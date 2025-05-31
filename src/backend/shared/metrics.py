"""
Shared Prometheus metrics collection module for ACGS-PGP microservices.
Provides standardized metrics collection across all services.
"""

import time
from typing import Dict, Any, Optional
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
import logging

logger = logging.getLogger(__name__)

# Global metrics registry for all ACGS-PGP services
class ACGSMetrics:
    """Centralized metrics collection for ACGS-PGP microservices."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        
        # Request metrics
        self.request_count = Counter(
            'acgs_http_requests_total',
            'Total HTTP requests',
            ['service', 'method', 'endpoint', 'status_code']
        )
        
        self.request_duration = Histogram(
            'acgs_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['service', 'method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
        )
        
        # Service health metrics
        self.service_info = Info(
            'acgs_service_info',
            'Service information',
            ['service', 'version']
        )
        
        self.active_connections = Gauge(
            'acgs_active_connections',
            'Number of active connections',
            ['service']
        )
        
        # Authentication specific metrics
        self.auth_attempts = Counter(
            'acgs_auth_attempts_total',
            'Total authentication attempts',
            ['service', 'auth_type', 'status']
        )
        
        # Database metrics
        self.db_connections = Gauge(
            'acgs_database_connections',
            'Number of database connections',
            ['service', 'pool_status']
        )
        
        self.db_query_duration = Histogram(
            'acgs_database_query_duration_seconds',
            'Database query duration in seconds',
            ['service', 'operation'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )
        
        # Cross-service communication metrics
        self.service_calls = Counter(
            'acgs_service_calls_total',
            'Total inter-service calls',
            ['source_service', 'target_service', 'endpoint', 'status_code']
        )
        
        self.service_call_duration = Histogram(
            'acgs_service_call_duration_seconds',
            'Inter-service call duration in seconds',
            ['source_service', 'target_service', 'endpoint'],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        # Error metrics
        self.error_count = Counter(
            'acgs_errors_total',
            'Total errors by type',
            ['service', 'error_type', 'severity']
        )
        
        # Business logic metrics
        self.policy_operations = Counter(
            'acgs_policy_operations_total',
            'Total policy operations',
            ['service', 'operation_type', 'status']
        )
        
        self.verification_operations = Counter(
            'acgs_verification_operations_total',
            'Total verification operations',
            ['service', 'verification_type', 'result']
        )
        
        # Initialize service info (commented out due to prometheus_client compatibility)
        # self.service_info.info({
        #     'service': self.service_name,
        #     'version': '3.0.0'
        # })
        
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.request_count.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        self.request_duration.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
    def record_auth_attempt(self, auth_type: str, status: str):
        """Record authentication attempt."""
        self.auth_attempts.labels(
            service=self.service_name,
            auth_type=auth_type,
            status=status
        ).inc()
        
    def record_db_query(self, operation: str, duration: float):
        """Record database query metrics."""
        self.db_query_duration.labels(
            service=self.service_name,
            operation=operation
        ).observe(duration)
        
    def record_service_call(self, target_service: str, endpoint: str, status_code: int, duration: float):
        """Record inter-service call metrics."""
        self.service_calls.labels(
            source_service=self.service_name,
            target_service=target_service,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        self.service_call_duration.labels(
            source_service=self.service_name,
            target_service=target_service,
            endpoint=endpoint
        ).observe(duration)
        
    def record_error(self, error_type: str, severity: str = "error"):
        """Record error occurrence."""
        self.error_count.labels(
            service=self.service_name,
            error_type=error_type,
            severity=severity
        ).inc()
        
    def record_policy_operation(self, operation_type: str, status: str):
        """Record policy operation."""
        self.policy_operations.labels(
            service=self.service_name,
            operation_type=operation_type,
            status=status
        ).inc()
        
    def record_verification_operation(self, verification_type: str, result: str):
        """Record verification operation."""
        self.verification_operations.labels(
            service=self.service_name,
            verification_type=verification_type,
            result=result
        ).inc()
        
    def update_active_connections(self, count: int):
        """Update active connections gauge."""
        self.active_connections.labels(service=self.service_name).set(count)
        
    def update_db_connections(self, pool_status: str, count: int):
        """Update database connections gauge."""
        self.db_connections.labels(
            service=self.service_name,
            pool_status=pool_status
        ).set(count)

# Global metrics instances (will be initialized by each service)
metrics_registry: Dict[str, ACGSMetrics] = {}

def get_metrics(service_name: str) -> ACGSMetrics:
    """Get or create metrics instance for a service."""
    if service_name not in metrics_registry:
        metrics_registry[service_name] = ACGSMetrics(service_name)
    return metrics_registry[service_name]

def metrics_middleware(service_name: str):
    """FastAPI middleware for automatic metrics collection."""
    
    async def middleware(request: Request, call_next):
        start_time = time.time()
        metrics = get_metrics(service_name)
        
        # Update active connections
        metrics.update_active_connections(len(metrics_registry))
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record request metrics
            metrics.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            metrics.record_error(
                error_type=type(e).__name__,
                severity="error"
            )
            
            # Record failed request
            metrics.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=duration
            )
            
            raise
    
    return middleware

def create_metrics_endpoint():
    """Create /metrics endpoint for Prometheus scraping."""
    
    async def metrics_endpoint():
        """Prometheus metrics endpoint."""
        return PlainTextResponse(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    return metrics_endpoint

def database_metrics_decorator(operation: str):
    """Decorator for database operations to collect metrics."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            service_name = getattr(wrapper, '_service_name', 'unknown')
            metrics = get_metrics(service_name)
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_db_query(operation, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_db_query(f"{operation}_failed", duration)
                metrics.record_error(f"db_{operation}_error")
                raise
        
        return wrapper
    return decorator

def service_call_decorator(target_service: str, endpoint: str):
    """Decorator for inter-service calls to collect metrics."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            service_name = getattr(wrapper, '_service_name', 'unknown')
            metrics = get_metrics(service_name)
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Extract status code from result if available
                status_code = getattr(result, 'status_code', 200)
                
                metrics.record_service_call(
                    target_service=target_service,
                    endpoint=endpoint,
                    status_code=status_code,
                    duration=duration
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_service_call(
                    target_service=target_service,
                    endpoint=endpoint,
                    status_code=500,
                    duration=duration
                )
                metrics.record_error(f"service_call_{target_service}_error")
                raise
        
        return wrapper
    return decorator
