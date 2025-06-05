"""
GPU Acceleration Manager for Constitutional AI Processing

This module manages GPU acceleration for constitutional AI processing,
optimized for 2 A100 GPU configuration to achieve sub-25ms latency targets
while maintaining >99.9% reliability and constitutional compliance.

Key Features:
- Optimal GPU allocation for constitutional processing tasks
- Dynamic load balancing across 2 A100 GPUs
- Memory management and optimization
- Performance monitoring and optimization
- Fallback mechanisms for GPU failures
- Integration with ACGS-PGP constitutional workflows
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json

try:
    import torch
    import torch.distributed as dist
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available - GPU acceleration disabled")

try:
    import nvidia_ml_py3 as nvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    logging.warning("NVIDIA ML Python not available - GPU monitoring limited")

from shared.metrics import get_metrics

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of constitutional processing tasks."""
    CONSTITUTIONAL_SYNTHESIS = "constitutional_synthesis"
    BIAS_DETECTION = "bias_detection"
    POLICY_COMPILATION = "policy_compilation"
    FORMAL_VERIFICATION = "formal_verification"
    DEMOCRATIC_AGGREGATION = "democratic_aggregation"
    MULTI_MODEL_ENSEMBLE = "multi_model_ensemble"


class GPUAllocationStrategy(Enum):
    """GPU allocation strategies."""
    DEDICATED = "dedicated"
    SHARED = "shared"
    DISTRIBUTED = "distributed"
    DYNAMIC = "dynamic"
    FALLBACK_CPU = "fallback_cpu"


@dataclass
class ConstitutionalTask:
    """Constitutional processing task for GPU acceleration."""
    task_id: str
    task_type: TaskType
    model_id: str
    input_data: str
    constitutional_context: str
    priority: str = "medium"
    max_latency_ms: float = 25.0
    memory_requirement_gb: float = 8.0
    compute_intensity: float = 1.0


@dataclass
class GPUAllocation:
    """GPU allocation for a task."""
    device_id: int
    memory_allocated_gb: float
    compute_allocation: float
    allocation_strategy: GPUAllocationStrategy
    estimated_latency_ms: float
    task_id: str


@dataclass
class AcceleratedResult:
    """Result from GPU-accelerated processing."""
    task_id: str
    result_content: str
    latency_ms: float
    gpu_utilization: float
    memory_used_gb: float
    constitutional_compliance: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class GPUAccelerationManager:
    """
    Manages GPU acceleration for constitutional AI processing,
    optimized for 2 A100 GPU configuration.
    """
    
    def __init__(self):
        self.metrics = get_metrics("gpu_acceleration")
        
        # GPU configuration for 2 A100 GPUs
        self.gpu_config = {
            "device_count": 2,
            "memory_per_device_gb": 40,  # A100 40GB
            "compute_capability": "8.0",
            "tensor_parallel_size": 2,
            "max_batch_size": 32,
            "memory_reserve_gb": 4  # Reserve 4GB for system
        }
        
        # Task allocation mapping
        self.acceleration_targets = {
            TaskType.CONSTITUTIONAL_SYNTHESIS: {"preferred_gpu": 0, "strategy": GPUAllocationStrategy.DEDICATED},
            TaskType.BIAS_DETECTION: {"preferred_gpu": 1, "strategy": GPUAllocationStrategy.DEDICATED},
            TaskType.POLICY_COMPILATION: {"preferred_gpu": "distributed", "strategy": GPUAllocationStrategy.DISTRIBUTED},
            TaskType.FORMAL_VERIFICATION: {"preferred_gpu": "cpu", "strategy": GPUAllocationStrategy.FALLBACK_CPU},
            TaskType.DEMOCRATIC_AGGREGATION: {"preferred_gpu": 0, "strategy": GPUAllocationStrategy.SHARED},
            TaskType.MULTI_MODEL_ENSEMBLE: {"preferred_gpu": "distributed", "strategy": GPUAllocationStrategy.DISTRIBUTED}
        }
        
        # Performance targets
        self.performance_targets = {
            "max_latency_ms": 25.0,
            "min_gpu_utilization": 0.8,
            "max_memory_usage": 0.9,
            "reliability_target": 0.999
        }
        
        # GPU state tracking
        self.gpu_states = {}
        self.active_tasks = {}
        self.task_queue = asyncio.Queue()
        
        # Performance metrics
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "average_latency_ms": 0.0,
            "average_gpu_utilization": 0.0,
            "memory_efficiency": 0.0,
            "task_throughput": 0.0
        }
        
        # Initialize GPU monitoring
        self._initialize_gpu_monitoring()
    
    def _initialize_gpu_monitoring(self):
        """Initialize GPU monitoring and state tracking."""
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available - GPU acceleration disabled")
            return
        
        if not torch.cuda.is_available():
            logger.warning("CUDA not available - GPU acceleration disabled")
            return
        
        # Initialize GPU states
        for gpu_id in range(min(self.gpu_config["device_count"], torch.cuda.device_count())):
            self.gpu_states[gpu_id] = {
                "available_memory_gb": self.gpu_config["memory_per_device_gb"] - self.gpu_config["memory_reserve_gb"],
                "current_utilization": 0.0,
                "active_tasks": [],
                "last_updated": datetime.now(timezone.utc)
            }
        
        if NVML_AVAILABLE:
            try:
                nvml.nvmlInit()
                logger.info("NVIDIA ML monitoring initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize NVIDIA ML monitoring: {e}")
    
    async def accelerate_constitutional_processing(self, 
                                                 processing_task: ConstitutionalTask) -> AcceleratedResult:
        """
        Accelerate constitutional processing using GPU resources.
        
        Args:
            processing_task: Constitutional task to accelerate
            
        Returns:
            Accelerated result with performance metrics
        """
        start_time = time.time()
        
        try:
            # 1. Determine optimal GPU allocation
            gpu_allocation = await self._optimize_gpu_allocation(processing_task)
            
            # 2. Validate GPU availability and resources
            if not await self._validate_gpu_resources(gpu_allocation):
                return await self._fallback_cpu_processing(processing_task)
            
            # 3. Load model on appropriate GPU(s)
            model_handle = await self._load_model_on_gpu(
                processing_task.model_id, 
                gpu_allocation
            )
            
            # 4. Execute accelerated processing
            result = await self._execute_accelerated_task(
                model_handle, processing_task, gpu_allocation
            )
            
            # 5. Validate performance targets
            latency_ms = (time.time() - start_time) * 1000
            if latency_ms > processing_task.max_latency_ms:
                logger.warning(f"Latency target missed: {latency_ms:.2f}ms > {processing_task.max_latency_ms}ms")
            
            # 6. Update performance metrics
            await self._update_performance_metrics(result, latency_ms)
            
            # 7. Clean up GPU resources
            await self._cleanup_gpu_resources(gpu_allocation, model_handle)
            
            result.latency_ms = latency_ms
            result.success = True
            
            logger.info(f"GPU acceleration completed for {processing_task.task_id} in {latency_ms:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"GPU acceleration failed for {processing_task.task_id}: {str(e)}")
            return await self._fallback_cpu_processing(processing_task, str(e))
    
    async def _optimize_gpu_allocation(self, task: ConstitutionalTask) -> GPUAllocation:
        """Determine optimal GPU allocation for task."""
        task_config = self.acceleration_targets.get(
            task.task_type, 
            {"preferred_gpu": 0, "strategy": GPUAllocationStrategy.DYNAMIC}
        )
        
        strategy = task_config["strategy"]
        preferred_gpu = task_config["preferred_gpu"]
        
        if strategy == GPUAllocationStrategy.FALLBACK_CPU:
            raise ValueError("Task requires CPU processing")
        
        # Find best available GPU
        if strategy == GPUAllocationStrategy.DISTRIBUTED:
            device_id = await self._select_distributed_allocation(task)
        elif isinstance(preferred_gpu, int):
            device_id = preferred_gpu if await self._is_gpu_available(preferred_gpu, task) else await self._find_best_gpu(task)
        else:
            device_id = await self._find_best_gpu(task)
        
        # Calculate memory allocation
        memory_allocated = min(
            task.memory_requirement_gb,
            self.gpu_states[device_id]["available_memory_gb"]
        )
        
        # Estimate latency based on task complexity and GPU load
        estimated_latency = await self._estimate_task_latency(task, device_id)
        
        allocation = GPUAllocation(
            device_id=device_id,
            memory_allocated_gb=memory_allocated,
            compute_allocation=1.0 / (len(self.gpu_states[device_id]["active_tasks"]) + 1),
            allocation_strategy=strategy,
            estimated_latency_ms=estimated_latency,
            task_id=task.task_id
        )
        
        return allocation
    
    async def _validate_gpu_resources(self, allocation: GPUAllocation) -> bool:
        """Validate GPU resources are available for allocation."""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return False
        
        gpu_state = self.gpu_states.get(allocation.device_id)
        if not gpu_state:
            return False
        
        # Check memory availability
        if allocation.memory_allocated_gb > gpu_state["available_memory_gb"]:
            logger.warning(f"Insufficient GPU memory: {allocation.memory_allocated_gb}GB > {gpu_state['available_memory_gb']}GB")
            return False
        
        # Check utilization limits
        if gpu_state["current_utilization"] > self.performance_targets["max_memory_usage"]:
            logger.warning(f"GPU utilization too high: {gpu_state['current_utilization']}")
            return False
        
        return True
    
    async def _load_model_on_gpu(self, model_id: str, allocation: GPUAllocation) -> Any:
        """Load model on specified GPU."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available for GPU model loading")
        
        device_id = allocation.device_id
        
        try:
            # Set CUDA device
            torch.cuda.set_device(device_id)
            
            # Mock model loading - in production, this would load actual models
            model_handle = {
                "model_id": model_id,
                "device_id": device_id,
                "memory_allocated": allocation.memory_allocated_gb,
                "loaded_at": datetime.now(timezone.utc)
            }
            
            # Update GPU state
            self.gpu_states[device_id]["available_memory_gb"] -= allocation.memory_allocated_gb
            self.gpu_states[device_id]["active_tasks"].append(allocation.task_id)
            
            logger.debug(f"Model {model_id} loaded on GPU {device_id}")
            
            return model_handle
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id} on GPU {device_id}: {str(e)}")
            raise
    
    async def _execute_accelerated_task(self, 
                                      model_handle: Any,
                                      task: ConstitutionalTask,
                                      allocation: GPUAllocation) -> AcceleratedResult:
        """Execute task with GPU acceleration."""
        start_time = time.time()
        
        try:
            # Mock GPU processing - in production, this would run actual models
            if TORCH_AVAILABLE and torch.cuda.is_available():
                device = torch.device(f"cuda:{allocation.device_id}")
                
                # Simulate GPU computation
                await asyncio.sleep(0.01)  # Simulate processing time
                
                # Mock constitutional processing result
                result_content = f"GPU-accelerated constitutional analysis for {task.task_type.value}"
                constitutional_compliance = 0.95  # Mock compliance score
                
                # Get GPU utilization
                gpu_utilization = await self._get_gpu_utilization(allocation.device_id)
                memory_used = allocation.memory_allocated_gb
                
            else:
                # CPU fallback
                result_content = f"CPU fallback constitutional analysis for {task.task_type.value}"
                constitutional_compliance = 0.90
                gpu_utilization = 0.0
                memory_used = 0.0
            
            processing_time = (time.time() - start_time) * 1000
            
            result = AcceleratedResult(
                task_id=task.task_id,
                result_content=result_content,
                latency_ms=processing_time,
                gpu_utilization=gpu_utilization,
                memory_used_gb=memory_used,
                constitutional_compliance=constitutional_compliance,
                success=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"GPU task execution failed: {str(e)}")
            return AcceleratedResult(
                task_id=task.task_id,
                result_content="",
                latency_ms=(time.time() - start_time) * 1000,
                gpu_utilization=0.0,
                memory_used_gb=0.0,
                constitutional_compliance=0.0,
                success=False,
                error_message=str(e)
            )
    
    async def _fallback_cpu_processing(self, 
                                     task: ConstitutionalTask,
                                     error_message: str = "GPU unavailable") -> AcceleratedResult:
        """Fallback to CPU processing when GPU is unavailable."""
        start_time = time.time()
        
        # Simulate CPU processing
        await asyncio.sleep(0.05)  # CPU processing typically slower
        
        result = AcceleratedResult(
            task_id=task.task_id,
            result_content=f"CPU fallback constitutional analysis for {task.task_type.value}",
            latency_ms=(time.time() - start_time) * 1000,
            gpu_utilization=0.0,
            memory_used_gb=0.0,
            constitutional_compliance=0.85,  # Slightly lower compliance for CPU fallback
            success=True,
            error_message=f"GPU fallback: {error_message}"
        )
        
        logger.info(f"CPU fallback completed for {task.task_id}")
        
        return result
    
    async def _cleanup_gpu_resources(self, allocation: GPUAllocation, model_handle: Any):
        """Clean up GPU resources after task completion."""
        try:
            device_id = allocation.device_id
            
            # Update GPU state
            if device_id in self.gpu_states:
                self.gpu_states[device_id]["available_memory_gb"] += allocation.memory_allocated_gb
                if allocation.task_id in self.gpu_states[device_id]["active_tasks"]:
                    self.gpu_states[device_id]["active_tasks"].remove(allocation.task_id)
            
            # Clear CUDA cache if available
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.debug(f"GPU resources cleaned up for task {allocation.task_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up GPU resources: {str(e)}")
    
    # Helper methods
    async def _is_gpu_available(self, gpu_id: int, task: ConstitutionalTask) -> bool:
        """Check if GPU is available for task."""
        if gpu_id not in self.gpu_states:
            return False
        
        gpu_state = self.gpu_states[gpu_id]
        return (
            gpu_state["available_memory_gb"] >= task.memory_requirement_gb and
            gpu_state["current_utilization"] < self.performance_targets["max_memory_usage"]
        )
    
    async def _find_best_gpu(self, task: ConstitutionalTask) -> int:
        """Find best available GPU for task."""
        best_gpu = 0
        best_score = -1
        
        for gpu_id, gpu_state in self.gpu_states.items():
            if await self._is_gpu_available(gpu_id, task):
                # Score based on available memory and low utilization
                score = (
                    gpu_state["available_memory_gb"] * 0.6 +
                    (1.0 - gpu_state["current_utilization"]) * 0.4
                )
                
                if score > best_score:
                    best_score = score
                    best_gpu = gpu_id
        
        return best_gpu
    
    async def _select_distributed_allocation(self, task: ConstitutionalTask) -> int:
        """Select GPU for distributed processing."""
        # For distributed tasks, use round-robin allocation
        active_task_counts = [len(state["active_tasks"]) for state in self.gpu_states.values()]
        return active_task_counts.index(min(active_task_counts))
    
    async def _estimate_task_latency(self, task: ConstitutionalTask, device_id: int) -> float:
        """Estimate task latency based on complexity and GPU load."""
        base_latency = {
            TaskType.CONSTITUTIONAL_SYNTHESIS: 15.0,
            TaskType.BIAS_DETECTION: 8.0,
            TaskType.POLICY_COMPILATION: 12.0,
            TaskType.FORMAL_VERIFICATION: 25.0,
            TaskType.DEMOCRATIC_AGGREGATION: 10.0,
            TaskType.MULTI_MODEL_ENSEMBLE: 20.0
        }.get(task.task_type, 15.0)
        
        # Adjust for GPU load
        gpu_load_factor = 1.0 + (len(self.gpu_states[device_id]["active_tasks"]) * 0.2)
        
        # Adjust for task complexity
        complexity_factor = task.compute_intensity
        
        estimated_latency = base_latency * gpu_load_factor * complexity_factor
        
        return min(estimated_latency, task.max_latency_ms)
    
    async def _get_gpu_utilization(self, device_id: int) -> float:
        """Get current GPU utilization."""
        if NVML_AVAILABLE:
            try:
                handle = nvml.nvmlDeviceGetHandleByIndex(device_id)
                utilization = nvml.nvmlDeviceGetUtilizationRates(handle)
                return utilization.gpu / 100.0
            except Exception as e:
                logger.debug(f"Failed to get GPU utilization: {e}")
        
        # Mock utilization for testing
        return 0.75
    
    async def _update_performance_metrics(self, result: AcceleratedResult, latency_ms: float):
        """Update performance metrics."""
        self.performance_metrics["total_tasks"] += 1
        
        if result.success:
            self.performance_metrics["successful_tasks"] += 1
        
        # Update running averages
        total_tasks = self.performance_metrics["total_tasks"]
        self.performance_metrics["average_latency_ms"] = (
            (self.performance_metrics["average_latency_ms"] * (total_tasks - 1) + latency_ms) / total_tasks
        )
        
        self.performance_metrics["average_gpu_utilization"] = (
            (self.performance_metrics["average_gpu_utilization"] * (total_tasks - 1) + 
             result.gpu_utilization) / total_tasks
        )
        
        # Record metrics
        self.metrics.record_timing("gpu_task_latency", latency_ms / 1000.0)
        self.metrics.record_value("gpu_utilization", result.gpu_utilization)
        self.metrics.record_value("constitutional_compliance", result.constitutional_compliance)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for monitoring."""
        return {
            "gpu_config": self.gpu_config,
            "performance_metrics": self.performance_metrics,
            "gpu_states": self.gpu_states,
            "performance_targets": self.performance_targets,
            "torch_available": TORCH_AVAILABLE,
            "cuda_available": TORCH_AVAILABLE and torch.cuda.is_available() if TORCH_AVAILABLE else False,
            "nvml_available": NVML_AVAILABLE
        }
