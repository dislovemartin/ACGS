"""
Celery Integration for ACGS-PGP Task 7 Parallel Validation Pipeline
Provides distributed task queue management with Redis broker
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import asdict

try:
    from celery import Celery, Task
    from celery.result import AsyncResult
    from celery.signals import task_prerun, task_postrun, task_failure
    from kombu import Queue
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None
    Task = None
    AsyncResult = None
    Queue = None

from .parallel_processing import ParallelTask, TaskStatus, ValidationBatch
from .result_aggregation import ValidationResult, AggregatedResult, ByzantineFaultTolerantAggregator
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


class CeleryConfig:
    """Celery configuration for ACGS-PGP."""
    
    # Broker settings
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    
    # Task settings
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    timezone = 'UTC'
    enable_utc = True
    
    # Worker settings
    worker_prefetch_multiplier = 1
    task_acks_late = True
    worker_max_tasks_per_child = 1000
    
    # Task routing
    task_routes = {
        'acgs.validation.*': {'queue': 'validation'},
        'acgs.aggregation.*': {'queue': 'aggregation'},
        'acgs.monitoring.*': {'queue': 'monitoring'},
    }
    
    # Queue definitions
    task_default_queue = 'default'
    if CELERY_AVAILABLE and Queue:
        task_queues = (
            Queue('default', routing_key='default'),
            Queue('validation', routing_key='validation'),
            Queue('aggregation', routing_key='aggregation'),
            Queue('monitoring', routing_key='monitoring'),
            Queue('priority', routing_key='priority'),
        )
    else:
        task_queues = ()
    
    # Task time limits
    task_soft_time_limit = 300  # 5 minutes
    task_time_limit = 600       # 10 minutes
    
    # Result settings
    result_expires = 3600  # 1 hour
    
    # Monitoring
    worker_send_task_events = True
    task_send_sent_event = True


# Initialize Celery app
if CELERY_AVAILABLE:
    celery_app = Celery('acgs_parallel_validation')
    celery_app.config_from_object(CeleryConfig)
else:
    celery_app = None
    logger.warning("Celery not available - falling back to local execution")


if CELERY_AVAILABLE and Task:
    class ACGSTask(Task):
        """Base task class for ACGS-PGP with enhanced error handling."""

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            """Handle task failure."""
            logger.error(f"Task {task_id} failed: {exc}")
            # Update task status in Redis
            asyncio.create_task(self._update_task_status(task_id, TaskStatus.FAILED, str(exc)))

        def on_success(self, retval, task_id, args, kwargs):
            """Handle task success."""
            logger.info(f"Task {task_id} completed successfully")
            # Update task status in Redis
            asyncio.create_task(self._update_task_status(task_id, TaskStatus.COMPLETED))

        async def _update_task_status(self, task_id: str, status: TaskStatus, error: str = None):
            """Update task status in Redis."""
            try:
                redis_client = await get_redis_client('celery_tasks')
                status_data = {
                    'status': status.value,
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'error': error
                }
                await redis_client.set_json(f"task_status:{task_id}", status_data, ttl=3600)
            except Exception as e:
                logger.error(f"Failed to update task status: {e}")
else:
    # Fallback when Celery is not available
    class ACGSTask:
        """Mock task class when Celery is not available."""
        pass


if CELERY_AVAILABLE:
    @celery_app.task(base=ACGSTask, bind=True, name='acgs.validation.execute_parallel_task')
    def execute_parallel_validation_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a parallel validation task."""
        try:
            # Reconstruct task from data
            task = ParallelTask(**task_data)
            
            # Import validation logic
            from ..fv_service.app.core.verification_logic import verify_policy_rules
            from ..fv_service.app.core.bias_detector import bias_detector
            
            # Execute based on task type
            if task.task_type == 'policy_verification':
                result = _execute_policy_verification(task)
            elif task.task_type == 'bias_detection':
                result = _execute_bias_detection(task)
            elif task.task_type == 'safety_check':
                result = _execute_safety_check(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            return {
                'task_id': task.task_id,
                'result': result,
                'execution_time_ms': 0,  # Will be calculated by caller
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                'task_id': task_data.get('task_id', 'unknown'),
                'error': str(e),
                'status': 'failed'
            }


def _execute_policy_verification(task: ParallelTask) -> Dict[str, Any]:
    """Execute policy verification task."""
    # Mock implementation - replace with actual verification logic
    import time
    time.sleep(0.1)  # Simulate processing time
    
    return {
        'verification_status': 'verified',
        'confidence_score': 0.95,
        'violations': [],
        'recommendations': []
    }


def _execute_bias_detection(task: ParallelTask) -> Dict[str, Any]:
    """Execute bias detection task."""
    # Mock implementation - replace with actual bias detection logic
    import time
    time.sleep(0.2)  # Simulate processing time
    
    return {
        'bias_detected': False,
        'bias_score': 0.15,
        'protected_attributes': task.payload.get('protected_attributes', []),
        'fairness_metrics': {
            'demographic_parity': 0.85,
            'equalized_odds': 0.92
        }
    }


def _execute_safety_check(task: ParallelTask) -> Dict[str, Any]:
    """Execute safety property check."""
    # Mock implementation - replace with actual safety check logic
    import time
    time.sleep(0.15)  # Simulate processing time
    
    return {
        'safety_status': 'safe',
        'violations': [],
        'safety_score': 0.98,
        'critical_issues': []
    }


class CeleryTaskManager:
    """Manages Celery tasks for parallel validation pipeline."""
    
    def __init__(self):
        self.aggregator = ByzantineFaultTolerantAggregator()
        self.active_batches: Dict[str, ValidationBatch] = {}
        
    async def submit_batch(
        self, 
        batch: ValidationBatch,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> str:
        """Submit a batch of tasks to Celery."""
        if not CELERY_AVAILABLE:
            raise RuntimeError("Celery not available")
        
        batch_id = batch.batch_id
        self.active_batches[batch_id] = batch
        
        logger.info(f"Submitting batch {batch_id} with {batch.total_tasks} tasks")
        
        # Submit tasks to Celery
        celery_tasks = []
        for task in batch.tasks:
            task_data = asdict(task)
            celery_task = execute_parallel_validation_task.delay(task_data)
            celery_tasks.append((task.task_id, celery_task))
        
        # Store task mapping in Redis
        redis_client = await get_redis_client('celery_batches')
        batch_data = {
            'batch_id': batch_id,
            'task_ids': [task.task_id for task in batch.tasks],
            'celery_task_ids': [ct.id for _, ct in celery_tasks],
            'submitted_at': datetime.now(timezone.utc).isoformat(),
            'status': 'submitted'
        }
        await redis_client.set_json(f"batch:{batch_id}", batch_data, ttl=7200)
        
        # Start monitoring task
        if CELERY_AVAILABLE:
            monitor_batch_progress.delay(batch_id, [ct.id for _, ct in celery_tasks])
        
        return batch_id
    
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get status of a batch."""
        redis_client = await get_redis_client('celery_batches')
        batch_data = await redis_client.get_json(f"batch:{batch_id}")
        
        if not batch_data:
            return {'error': 'Batch not found'}
        
        # Get individual task statuses
        task_statuses = []
        for task_id in batch_data['task_ids']:
            status_data = await redis_client.get_json(f"task_status:{task_id}")
            if status_data:
                task_statuses.append(status_data)
        
        completed = len([s for s in task_statuses if s.get('status') == 'completed'])
        failed = len([s for s in task_statuses if s.get('status') == 'failed'])
        total = len(batch_data['task_ids'])
        
        return {
            'batch_id': batch_id,
            'total_tasks': total,
            'completed_tasks': completed,
            'failed_tasks': failed,
            'progress_percentage': (completed / total * 100) if total > 0 else 0,
            'status': 'completed' if completed == total else 'running',
            'task_statuses': task_statuses
        }
    
    async def get_batch_results(self, batch_id: str) -> Optional[AggregatedResult]:
        """Get aggregated results for a completed batch."""
        batch_status = await self.get_batch_status(batch_id)
        
        if batch_status.get('status') != 'completed':
            return None
        
        # Collect individual results
        redis_client = await get_redis_client('celery_batches')
        validation_results = []
        
        for task_id in batch_status.get('task_ids', []):
            result_data = await redis_client.get_json(f"task_result:{task_id}")
            if result_data:
                validation_result = ValidationResult(
                    task_id=task_id,
                    validator_id=f"celery_worker_{task_id[:8]}",
                    result=result_data.get('result', {}),
                    confidence_score=result_data.get('result', {}).get('confidence_score', 0.0),
                    execution_time_ms=result_data.get('execution_time_ms', 0.0)
                )
                validation_results.append(validation_result)
        
        if not validation_results:
            return None
        
        # Aggregate results
        return self.aggregator.aggregate_results(validation_results)
    
    async def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a running batch."""
        if not CELERY_AVAILABLE:
            return False
        
        redis_client = await get_redis_client('celery_batches')
        batch_data = await redis_client.get_json(f"batch:{batch_id}")
        
        if not batch_data:
            return False
        
        # Revoke Celery tasks
        for celery_task_id in batch_data.get('celery_task_ids', []):
            celery_app.control.revoke(celery_task_id, terminate=True)
        
        # Update batch status
        batch_data['status'] = 'cancelled'
        batch_data['cancelled_at'] = datetime.now(timezone.utc).isoformat()
        await redis_client.set_json(f"batch:{batch_id}", batch_data, ttl=7200)
        
        return True


if CELERY_AVAILABLE:
    @celery_app.task(name='acgs.monitoring.monitor_batch_progress')
    def monitor_batch_progress(batch_id: str, celery_task_ids: List[str]):
        """Monitor batch progress and update status."""
        import time
        
        while True:
            completed = 0
            failed = 0
            
            for task_id in celery_task_ids:
                result = AsyncResult(task_id, app=celery_app)
                if result.ready():
                    if result.successful():
                        completed += 1
                    else:
                        failed += 1
            
            total = len(celery_task_ids)
            if completed + failed >= total:
                break
            
            time.sleep(1)  # Check every second
        
        logger.info(f"Batch {batch_id} monitoring complete: {completed}/{total} successful")


# Global task manager instance
task_manager = CeleryTaskManager() if CELERY_AVAILABLE else None


async def initialize_celery_integration():
    """Initialize Celery integration."""
    if not CELERY_AVAILABLE:
        logger.warning("Celery not available - parallel processing will use local execution")
        return False
    
    try:
        # Test Redis connection
        redis_client = await get_redis_client('celery_test')
        await redis_client.ping()
        
        # Test Celery connection
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            logger.info(f"Celery workers available: {len(stats)}")
            return True
        else:
            logger.warning("No Celery workers available")
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize Celery integration: {e}")
        return False


async def shutdown_celery_integration():
    """Shutdown Celery integration."""
    if CELERY_AVAILABLE and celery_app:
        try:
            # Cancel all active tasks
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    for task in tasks:
                        celery_app.control.revoke(task['id'], terminate=True)
            
            logger.info("Celery integration shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during Celery shutdown: {e}")
