"""
Shared Prometheus metrics collection module for ACGS-PGP microservices.
Provides standardized metrics collection across all services.
"""

import time
from typing import Dict, Any, Optional
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
import logging

logger = logging.getLogger(__name__)

# Global metrics registry to prevent duplicate registrations
metrics_registry: Dict[str, "ACGSMetrics"] = {}

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

        # LLM specific metrics
        self.llm_response_time = Histogram(
            'acgs_llm_response_time_seconds',
            'LLM response time in seconds',
            ['service', 'model_name', 'request_type'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0)
        )
        self.llm_error_rate = Counter(
            'acgs_llm_errors_total',
            'Total LLM errors',
            ['service', 'model_name', 'error_type']
        )
        self.llm_output_quality_score = Gauge(
            'acgs_llm_output_quality_score',
            'LLM output quality score (e.g., semantic faithfulness, factual accuracy)',
            ['service', 'model_name', 'quality_metric']
        )
        self.llm_bias_score = Gauge(
            'acgs_llm_bias_score',
            'LLM output bias score',
            ['service', 'model_name', 'bias_type']
        )
        self.llm_fallback_count = Counter(
            'acgs_llm_fallbacks_total',
            'Total LLM fallback occurrences',
            ['service', 'fallback_reason']
        )
        self.llm_human_escalation_count = Counter(
            'acgs_llm_human_escalations_total',
            'Total LLM human review escalations',
            ['service', 'escalation_reason']
        )

        # Task 7: Parallel processing metrics
        self.parallel_tasks_total = Counter(
            'acgs_parallel_tasks_total',
            'Total parallel tasks executed',
            ['service', 'task_type', 'status']
        )

        self.parallel_batch_duration = Histogram(
            'acgs_parallel_batch_duration_seconds',
            'Parallel batch execution duration',
            ['service', 'batch_type'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 60.0)
        )

        self.parallel_task_queue_size = Gauge(
            'acgs_parallel_task_queue_size',
            'Number of tasks in parallel processing queue',
            ['service', 'queue_type']
        )

        self.parallel_workers_active = Gauge(
            'acgs_parallel_workers_active',
            'Number of active parallel workers',
            ['service', 'worker_type']
        )

        self.websocket_connections = Gauge(
            'acgs_websocket_connections_active',
            'Number of active WebSocket connections',
            ['service', 'connection_type']
        )

        self.cache_operations = Counter(
            'acgs_cache_operations_total',
            'Total cache operations',
            ['service', 'operation', 'result']
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

    # Task 7: Parallel processing metrics methods
    def record_parallel_task(self, task_type: str, status: str):
        """Record parallel task execution."""
        self.parallel_tasks_total.labels(
            service=self.service_name,
            task_type=task_type,
            status=status
        ).inc()

    def record_parallel_batch_duration(self, batch_type: str, duration: float):
        """Record parallel batch execution duration."""
        self.parallel_batch_duration.labels(
            service=self.service_name,
            batch_type=batch_type
        ).observe(duration)

    def update_parallel_queue_size(self, queue_type: str, size: int):
        """Update parallel task queue size."""
        self.parallel_task_queue_size.labels(
            service=self.service_name,
            queue_type=queue_type
        ).set(size)

    def update_parallel_workers(self, worker_type: str, count: int):
        """Update active parallel workers count."""
        self.parallel_workers_active.labels(
            service=self.service_name,
            worker_type=worker_type
        ).set(count)

    def update_websocket_connections(self, connection_type: str, count: int):
        """Update WebSocket connections count."""
        self.websocket_connections.labels(
            service=self.service_name,
            connection_type=connection_type
        ).set(count)

    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation."""
        self.cache_operations.labels(
            service=self.service_name,
            operation=operation,
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

    def record_llm_response_time(self, model_name: str, request_type: str, duration: float):
        """Record LLM response time."""
        self.llm_response_time.labels(
            service=self.service_name,
            model_name=model_name,
            request_type=request_type
        ).observe(duration)

    def record_llm_error(self, model_name: str, error_type: str):
        """Record LLM error."""
        self.llm_error_rate.labels(
            service=self.service_name,
            model_name=model_name,
            error_type=error_type
        ).inc()

    def set_llm_output_quality_score(self, model_name: str, quality_metric: str, score: float):
        """Set LLM output quality score."""
        self.llm_output_quality_score.labels(
            service=self.service_name,
            model_name=model_name,
            quality_metric=quality_metric
        ).set(score)

    def set_llm_bias_score(self, model_name: str, bias_type: str, score: float):
        """Set LLM bias score."""
        self.llm_bias_score.labels(
            service=self.service_name,
            model_name=model_name,
            bias_type=bias_type
        ).set(score)

    def record_llm_fallback(self, fallback_reason: str):
        """Record LLM fallback."""
        self.llm_fallback_count.labels(
            service=self.service_name,
            fallback_reason=fallback_reason
        ).inc()

    def record_llm_human_escalation(self, escalation_reason: str):
        """Record LLM human escalation."""
        self.llm_human_escalation_count.labels(
            service=self.service_name,
            escalation_reason=escalation_reason
        ).inc()

def get_metrics(service_name: str) -> ACGSMetrics:
    """Get or create metrics instance for a service."""
    if service_name not in metrics_registry:
        try:
            metrics_registry[service_name] = ACGSMetrics(service_name)
        except ValueError as e:
            if "Duplicated timeseries" in str(e):
                # Registry already has these metrics, create a simple placeholder
                logger.warning(f"Metrics already registered for {service_name}, using existing registry")
                # Return a dummy metrics object that doesn't register new metrics
                class DummyMetrics:
                    def __init__(self, service_name):
                        self.service_name = service_name
                    def __getattr__(self, name):
                        # Return a no-op function for any metric method
                        return lambda *args, **kwargs: None
                metrics_registry[service_name] = DummyMetrics(service_name)
            else:
                raise
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
        # Use the default registry which should have all metrics
        return PlainTextResponse(
            generate_latest(REGISTRY),
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
