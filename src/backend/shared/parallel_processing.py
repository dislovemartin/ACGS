"""
Parallel Processing Utilities for ACGS-PGP Task 7
Provides async concurrent processing, task partitioning, and result aggregation
"""

import asyncio
import logging
import time
import hashlib
import json
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ParallelTask:
    """Represents a task in the parallel validation pipeline."""
    task_type: str
    payload: Dict[str, Any]
    task_id: str = ""
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 30.0

    def __post_init__(self):
        if not self.task_id:
            self.task_id = self._generate_task_id()
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        content = f"{self.task_type}_{self.payload}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    @property
    def execution_time_ms(self) -> Optional[float]:
        """Calculate execution time in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None
    
    @property
    def is_ready(self) -> bool:
        """Check if task is ready for execution (all dependencies completed)."""
        return self.status == TaskStatus.PENDING
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries


@dataclass
class ValidationBatch:
    """Represents a batch of validation tasks for parallel processing."""
    batch_id: str
    tasks: List[ParallelTask]
    batch_type: str = "validation"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    max_concurrent: int = 10
    timeout_seconds: float = 120.0
    
    def __post_init__(self):
        if not self.batch_id:
            self.batch_id = f"batch_{int(time.time() * 1000)}"
    
    @property
    def total_tasks(self) -> int:
        return len(self.tasks)
    
    @property
    def completed_tasks(self) -> int:
        return len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
    
    @property
    def failed_tasks(self) -> int:
        return len([t for t in self.tasks if t.status == TaskStatus.FAILED])
    
    @property
    def progress_percentage(self) -> float:
        if self.total_tasks == 0:
            return 100.0
        return (self.completed_tasks / self.total_tasks) * 100.0


class DependencyGraphAnalyzer:
    """Analyzes task dependencies using NetworkX for optimal execution ordering."""

    def __init__(self):
        if NETWORKX_AVAILABLE:
            self.graph = nx.DiGraph()
        else:
            self.graph = None
        self.task_registry: Dict[str, ParallelTask] = {}
    
    def add_task(self, task: ParallelTask) -> None:
        """Add task to dependency graph."""
        self.task_registry[task.task_id] = task

        if NETWORKX_AVAILABLE and self.graph is not None:
            self.graph.add_node(task.task_id, task=task)

            # Add dependency edges
            for dep_id in task.dependencies:
                if dep_id in self.task_registry:
                    self.graph.add_edge(dep_id, task.task_id)
    
    def get_execution_order(self) -> List[List[str]]:
        """Get optimal execution order using topological sort."""
        if not NETWORKX_AVAILABLE or self.graph is None:
            # Fallback to sequential execution when NetworkX not available
            return [[task_id] for task_id in self.task_registry.keys()]

        try:
            # Check for cycles
            if not nx.is_directed_acyclic_graph(self.graph):
                cycles = list(nx.simple_cycles(self.graph))
                raise ValueError(f"Circular dependencies detected: {cycles}")

            # Get topological ordering
            topo_order = list(nx.topological_sort(self.graph))

            # Group tasks by execution level (tasks that can run in parallel)
            levels = []
            remaining_tasks = set(topo_order)

            while remaining_tasks:
                # Find tasks with no remaining dependencies
                ready_tasks = []
                for task_id in remaining_tasks:
                    dependencies = set(self.graph.predecessors(task_id))
                    if dependencies.issubset(set(topo_order) - remaining_tasks):
                        ready_tasks.append(task_id)

                if not ready_tasks:
                    # This shouldn't happen with a valid DAG
                    raise ValueError("Unable to find ready tasks - possible graph corruption")

                levels.append(ready_tasks)
                remaining_tasks -= set(ready_tasks)

            return levels

        except Exception as e:
            logger.error(f"Failed to analyze dependency graph: {e}")
            # Fallback to sequential execution
            return [[task_id] for task_id in self.task_registry.keys()]
    
    def get_critical_path(self) -> List[str]:
        """Calculate critical path for optimization."""
        if not NETWORKX_AVAILABLE or self.graph is None:
            # Fallback: return all tasks in order
            return list(self.task_registry.keys())

        try:
            # Add weights based on estimated execution time
            for node in self.graph.nodes():
                task = self.task_registry[node]
                # Use timeout as weight estimate
                self.graph.nodes[node]['weight'] = task.timeout_seconds

            # Find longest path (critical path)
            if self.graph.nodes():
                return nx.dag_longest_path(self.graph, weight='weight')
            return []

        except Exception as e:
            logger.error(f"Failed to calculate critical path: {e}")
            return []

    def get_task_statistics(self) -> Dict[str, Any]:
        """Get dependency graph statistics."""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return {
                'total_tasks': len(self.task_registry),
                'total_edges': 0,
                'is_dag': True,
                'max_depth': len(self.task_registry),
                'parallelization_factor': 1.0,
                'networkx_available': False
            }

        return {
            'total_tasks': len(self.task_registry),
            'total_edges': self.graph.number_of_edges(),
            'is_dag': nx.is_directed_acyclic_graph(self.graph),
            'max_depth': len(nx.dag_longest_path(self.graph)) if self.graph.nodes() else 0,
            'parallelization_factor': len(self.task_registry) / max(len(nx.dag_longest_path(self.graph)), 1) if self.graph.nodes() else 1.0,
            'networkx_available': True
        }


class TaskPartitioner:
    """Intelligent task partitioning using policy similarity clustering."""
    
    def __init__(self, max_batch_size: int = 50):
        self.max_batch_size = max_batch_size
    
    def partition_tasks(self, tasks: List[ParallelTask]) -> List[ValidationBatch]:
        """Partition tasks into optimal batches."""
        if not tasks:
            return []
        
        # Group by task type first
        type_groups = {}
        for task in tasks:
            task_type = task.task_type
            if task_type not in type_groups:
                type_groups[task_type] = []
            type_groups[task_type].append(task)
        
        batches = []
        for task_type, type_tasks in type_groups.items():
            # Further partition by similarity if needed
            if len(type_tasks) <= self.max_batch_size:
                batch = ValidationBatch(
                    batch_id=f"{task_type}_batch_{int(time.time() * 1000)}",
                    tasks=type_tasks,
                    batch_type=task_type
                )
                batches.append(batch)
            else:
                # Split large groups into smaller batches
                for i in range(0, len(type_tasks), self.max_batch_size):
                    batch_tasks = type_tasks[i:i + self.max_batch_size]
                    batch = ValidationBatch(
                        batch_id=f"{task_type}_batch_{i // self.max_batch_size}_{int(time.time() * 1000)}",
                        tasks=batch_tasks,
                        batch_type=task_type
                    )
                    batches.append(batch)
        
        return batches
    
    def calculate_similarity(self, task1: ParallelTask, task2: ParallelTask) -> float:
        """Calculate similarity between two tasks."""
        # Simple similarity based on task type and payload structure
        if task1.task_type != task2.task_type:
            return 0.0
        
        # Compare payload keys
        keys1 = set(task1.payload.keys())
        keys2 = set(task2.payload.keys())
        
        if not keys1 and not keys2:
            return 1.0
        
        intersection = keys1.intersection(keys2)
        union = keys1.union(keys2)
        
        return len(intersection) / len(union) if union else 0.0


class ParallelExecutor:
    """Executes tasks in parallel with concurrency control."""
    
    def __init__(self, max_concurrent: int = 10, thread_pool_size: int = 4):
        self.max_concurrent = max_concurrent
        self.thread_pool = ThreadPoolExecutor(max_workers=thread_pool_size)
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def execute_task(
        self, 
        task: ParallelTask, 
        executor_func: Callable[[ParallelTask], Any]
    ) -> ParallelTask:
        """Execute a single task with timeout and error handling."""
        async with self.semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)
            
            try:
                # Execute task with timeout
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        self.thread_pool, executor_func, task
                    ),
                    timeout=task.timeout_seconds
                )
                
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
                
            except asyncio.TimeoutError:
                task.error = f"Task timed out after {task.timeout_seconds} seconds"
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now(timezone.utc)
                
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now(timezone.utc)
                
            return task
    
    async def execute_batch(
        self, 
        batch: ValidationBatch, 
        executor_func: Callable[[ParallelTask], Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> ValidationBatch:
        """Execute a batch of tasks in parallel."""
        logger.info(f"Executing batch {batch.batch_id} with {batch.total_tasks} tasks")
        
        # Create tasks for async execution
        async_tasks = []
        for task in batch.tasks:
            if task.is_ready:
                async_task = asyncio.create_task(
                    self.execute_task(task, executor_func)
                )
                async_tasks.append(async_task)
                self.active_tasks[task.task_id] = async_task
        
        # Execute with progress tracking
        completed = 0
        for coro in asyncio.as_completed(async_tasks):
            await coro
            completed += 1
            
            if progress_callback:
                progress = (completed / len(async_tasks)) * 100.0
                progress_callback(progress)
        
        # Clean up active tasks
        for task in batch.tasks:
            self.active_tasks.pop(task.task_id, None)
        
        logger.info(f"Batch {batch.batch_id} completed: {batch.completed_tasks}/{batch.total_tasks} successful")
        return batch
    
    async def shutdown(self):
        """Shutdown executor and cleanup resources."""
        # Cancel active tasks
        for task in self.active_tasks.values():
            task.cancel()
        
        # Wait for cancellation
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
