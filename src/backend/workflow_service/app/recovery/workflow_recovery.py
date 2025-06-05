"""
Workflow Recovery and Rollback Mechanisms for ACGS-PGP
Provides automated recovery, rollback, and state restoration capabilities
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from ..core.workflow_engine import Workflow, WorkflowStatus, WorkflowStep, workflow_engine

logger = logging.getLogger(__name__)

class RecoveryAction(Enum):
    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP = "skip"
    MANUAL_INTERVENTION = "manual_intervention"
    ALTERNATIVE_PATH = "alternative_path"

class CheckpointType(Enum):
    STEP_COMPLETION = "step_completion"
    WORKFLOW_START = "workflow_start"
    CRITICAL_POINT = "critical_point"
    USER_DEFINED = "user_defined"

@dataclass
class Checkpoint:
    id: str
    workflow_id: str
    step_id: Optional[str]
    checkpoint_type: CheckpointType
    state_data: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class RecoveryPlan:
    id: str
    workflow_id: str
    failed_step_id: str
    recovery_action: RecoveryAction
    rollback_to_checkpoint: Optional[str] = None
    alternative_steps: List[WorkflowStep] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.alternative_steps is None:
            self.alternative_steps = []

class WorkflowRecoveryManager:
    """
    Manages workflow recovery, rollback, and state restoration
    """
    
    def __init__(self):
        self.checkpoints: Dict[str, List[Checkpoint]] = {}
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        self.rollback_handlers: Dict[str, Callable] = {}
        self._initialize_recovery_strategies()
    
    def _initialize_recovery_strategies(self):
        """Initialize default recovery strategies"""
        
        # Register default recovery handlers
        self.recovery_handlers["network_timeout"] = self._handle_network_timeout
        self.recovery_handlers["service_unavailable"] = self._handle_service_unavailable
        self.recovery_handlers["validation_failure"] = self._handle_validation_failure
        self.recovery_handlers["constitutional_violation"] = self._handle_constitutional_violation
        self.recovery_handlers["cryptographic_failure"] = self._handle_cryptographic_failure
        
        # Register default rollback handlers
        self.rollback_handlers["policy_deployment"] = self._rollback_policy_deployment
        self.rollback_handlers["constitutional_amendment"] = self._rollback_constitutional_amendment
        self.rollback_handlers["cryptographic_signing"] = self._rollback_cryptographic_signing
    
    async def create_checkpoint(
        self,
        workflow_id: str,
        step_id: Optional[str] = None,
        checkpoint_type: CheckpointType = CheckpointType.STEP_COMPLETION,
        state_data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a workflow checkpoint"""
        
        checkpoint_id = str(uuid.uuid4())
        
        checkpoint = Checkpoint(
            id=checkpoint_id,
            workflow_id=workflow_id,
            step_id=step_id,
            checkpoint_type=checkpoint_type,
            state_data=state_data or {},
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        if workflow_id not in self.checkpoints:
            self.checkpoints[workflow_id] = []
        
        self.checkpoints[workflow_id].append(checkpoint)
        
        logger.info(f"Created checkpoint {checkpoint_id} for workflow {workflow_id}")
        
        return checkpoint_id
    
    async def create_recovery_plan(
        self,
        workflow_id: str,
        failed_step_id: str,
        error_type: str,
        error_message: str
    ) -> RecoveryPlan:
        """Create a recovery plan based on failure analysis"""
        
        plan_id = str(uuid.uuid4())
        
        # Analyze failure and determine recovery action
        recovery_action = await self._analyze_failure(error_type, error_message)
        
        # Find appropriate rollback checkpoint
        rollback_checkpoint = await self._find_rollback_checkpoint(workflow_id, failed_step_id)
        
        # Generate alternative steps if needed
        alternative_steps = await self._generate_alternative_steps(workflow_id, failed_step_id, error_type)
        
        recovery_plan = RecoveryPlan(
            id=plan_id,
            workflow_id=workflow_id,
            failed_step_id=failed_step_id,
            recovery_action=recovery_action,
            rollback_to_checkpoint=rollback_checkpoint,
            alternative_steps=alternative_steps
        )
        
        self.recovery_plans[plan_id] = recovery_plan
        
        logger.info(f"Created recovery plan {plan_id} for workflow {workflow_id}: {recovery_action.value}")
        
        return recovery_plan
    
    async def execute_recovery(self, recovery_plan_id: str) -> bool:
        """Execute a recovery plan"""
        
        if recovery_plan_id not in self.recovery_plans:
            logger.error(f"Recovery plan {recovery_plan_id} not found")
            return False
        
        plan = self.recovery_plans[recovery_plan_id]
        
        try:
            if plan.recovery_action == RecoveryAction.RETRY:
                return await self._execute_retry(plan)
            
            elif plan.recovery_action == RecoveryAction.ROLLBACK:
                return await self._execute_rollback(plan)
            
            elif plan.recovery_action == RecoveryAction.ALTERNATIVE_PATH:
                return await self._execute_alternative_path(plan)
            
            elif plan.recovery_action == RecoveryAction.SKIP:
                return await self._execute_skip(plan)
            
            elif plan.recovery_action == RecoveryAction.MANUAL_INTERVENTION:
                return await self._request_manual_intervention(plan)
            
            else:
                logger.error(f"Unknown recovery action: {plan.recovery_action}")
                return False
                
        except Exception as e:
            logger.error(f"Recovery execution failed for plan {recovery_plan_id}: {e}")
            return False
    
    async def _analyze_failure(self, error_type: str, error_message: str) -> RecoveryAction:
        """Analyze failure and determine appropriate recovery action"""
        
        # Network-related failures
        if "timeout" in error_message.lower() or "connection" in error_message.lower():
            return RecoveryAction.RETRY
        
        # Service unavailability
        if "service unavailable" in error_message.lower() or "503" in error_message:
            return RecoveryAction.RETRY
        
        # Validation failures
        if "validation" in error_message.lower() or "invalid" in error_message.lower():
            return RecoveryAction.ALTERNATIVE_PATH
        
        # Constitutional violations
        if "constitutional" in error_message.lower() or "principle" in error_message.lower():
            return RecoveryAction.ROLLBACK
        
        # Cryptographic failures
        if "signature" in error_message.lower() or "crypto" in error_message.lower():
            return RecoveryAction.ROLLBACK
        
        # Default to manual intervention for unknown errors
        return RecoveryAction.MANUAL_INTERVENTION
    
    async def _find_rollback_checkpoint(self, workflow_id: str, failed_step_id: str) -> Optional[str]:
        """Find the most appropriate checkpoint for rollback"""
        
        if workflow_id not in self.checkpoints:
            return None
        
        checkpoints = self.checkpoints[workflow_id]
        
        # Find the latest checkpoint before the failed step
        for checkpoint in reversed(checkpoints):
            if checkpoint.checkpoint_type in [CheckpointType.CRITICAL_POINT, CheckpointType.STEP_COMPLETION]:
                return checkpoint.id
        
        return None
    
    async def _generate_alternative_steps(
        self,
        workflow_id: str,
        failed_step_id: str,
        error_type: str
    ) -> List[WorkflowStep]:
        """Generate alternative workflow steps"""
        
        alternative_steps = []
        
        # Get the original workflow
        workflow = workflow_engine.workflows.get(workflow_id)
        if not workflow:
            return alternative_steps
        
        # Find the failed step
        failed_step = None
        for step in workflow.steps:
            if step.id == failed_step_id:
                failed_step = step
                break
        
        if not failed_step:
            return alternative_steps
        
        # Generate alternatives based on error type and step
        if failed_step.service == "gs_service" and "validation" in error_type:
            # Alternative policy synthesis with different parameters
            alt_step = WorkflowStep(
                id=f"{failed_step.id}_alt_validation",
                name=f"Alternative {failed_step.name}",
                service=failed_step.service,
                endpoint=failed_step.endpoint,
                input_data={**failed_step.input_data, "validation_mode": "relaxed"},
                dependencies=failed_step.dependencies,
                timeout_seconds=failed_step.timeout_seconds * 2
            )
            alternative_steps.append(alt_step)
        
        elif failed_step.service == "fv_service":
            # Alternative verification with different solver
            alt_step = WorkflowStep(
                id=f"{failed_step.id}_alt_solver",
                name=f"Alternative {failed_step.name}",
                service=failed_step.service,
                endpoint=failed_step.endpoint,
                input_data={**failed_step.input_data, "solver": "alternative"},
                dependencies=failed_step.dependencies,
                timeout_seconds=failed_step.timeout_seconds * 3
            )
            alternative_steps.append(alt_step)
        
        return alternative_steps
    
    async def _execute_retry(self, plan: RecoveryPlan) -> bool:
        """Execute retry recovery action"""
        
        if plan.retry_count >= plan.max_retries:
            logger.error(f"Max retries exceeded for recovery plan {plan.id}")
            return False
        
        plan.retry_count += 1
        
        # Get the workflow and failed step
        workflow = workflow_engine.workflows.get(plan.workflow_id)
        if not workflow:
            return False
        
        failed_step = None
        for step in workflow.steps:
            if step.id == plan.failed_step_id:
                failed_step = step
                break
        
        if not failed_step:
            return False
        
        # Reset step status and retry
        failed_step.status = WorkflowStatus.PENDING
        failed_step.error_message = None
        failed_step.started_at = None
        failed_step.completed_at = None
        
        logger.info(f"Retrying step {plan.failed_step_id} (attempt {plan.retry_count})")
        
        # Resume workflow execution
        return await workflow_engine.resume_workflow(plan.workflow_id)
    
    async def _execute_rollback(self, plan: RecoveryPlan) -> bool:
        """Execute rollback recovery action"""
        
        if not plan.rollback_to_checkpoint:
            logger.error(f"No rollback checkpoint specified for plan {plan.id}")
            return False
        
        # Find the checkpoint
        checkpoint = None
        if plan.workflow_id in self.checkpoints:
            for cp in self.checkpoints[plan.workflow_id]:
                if cp.id == plan.rollback_to_checkpoint:
                    checkpoint = cp
                    break
        
        if not checkpoint:
            logger.error(f"Checkpoint {plan.rollback_to_checkpoint} not found")
            return False
        
        # Restore workflow state
        workflow = workflow_engine.workflows.get(plan.workflow_id)
        if not workflow:
            return False
        
        # Reset steps after the checkpoint
        for step in workflow.steps:
            if step.id == checkpoint.step_id:
                break
            if step.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                # Execute rollback handler if available
                handler = self.rollback_handlers.get(step.service)
                if handler:
                    await handler(step, checkpoint.state_data)
                
                # Reset step status
                step.status = WorkflowStatus.PENDING
                step.result = None
                step.error_message = None
                step.started_at = None
                step.completed_at = None
        
        logger.info(f"Rolled back workflow {plan.workflow_id} to checkpoint {checkpoint.id}")
        
        # Resume workflow execution
        return await workflow_engine.resume_workflow(plan.workflow_id)
    
    async def _execute_alternative_path(self, plan: RecoveryPlan) -> bool:
        """Execute alternative path recovery action"""
        
        if not plan.alternative_steps:
            logger.error(f"No alternative steps provided for plan {plan.id}")
            return False
        
        # Get the workflow
        workflow = workflow_engine.workflows.get(plan.workflow_id)
        if not workflow:
            return False
        
        # Replace failed step with alternative steps
        new_steps = []
        for step in workflow.steps:
            if step.id == plan.failed_step_id:
                # Add alternative steps
                new_steps.extend(plan.alternative_steps)
            else:
                new_steps.append(step)
        
        workflow.steps = new_steps
        
        logger.info(f"Replaced failed step with {len(plan.alternative_steps)} alternative steps")
        
        # Resume workflow execution
        return await workflow_engine.resume_workflow(plan.workflow_id)
    
    async def _execute_skip(self, plan: RecoveryPlan) -> bool:
        """Execute skip recovery action"""
        
        # Get the workflow
        workflow = workflow_engine.workflows.get(plan.workflow_id)
        if not workflow:
            return False
        
        # Mark failed step as skipped
        for step in workflow.steps:
            if step.id == plan.failed_step_id:
                step.status = WorkflowStatus.SKIPPED
                step.error_message = "Skipped due to recovery plan"
                break
        
        logger.info(f"Skipped failed step {plan.failed_step_id}")
        
        # Resume workflow execution
        return await workflow_engine.resume_workflow(plan.workflow_id)
    
    async def _request_manual_intervention(self, plan: RecoveryPlan) -> bool:
        """Request manual intervention"""
        
        # Create manual intervention request
        intervention_data = {
            "recovery_plan_id": plan.id,
            "workflow_id": plan.workflow_id,
            "failed_step_id": plan.failed_step_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending_intervention"
        }
        
        # Store intervention request (in real implementation, this would notify administrators)
        logger.warning(f"Manual intervention requested for workflow {plan.workflow_id}")
        
        # Pause the workflow
        await workflow_engine.pause_workflow(plan.workflow_id)
        
        return True
    
    # Recovery handlers
    async def _handle_network_timeout(self, step: WorkflowStep, error: str) -> RecoveryAction:
        """Handle network timeout errors"""
        return RecoveryAction.RETRY
    
    async def _handle_service_unavailable(self, step: WorkflowStep, error: str) -> RecoveryAction:
        """Handle service unavailable errors"""
        return RecoveryAction.RETRY
    
    async def _handle_validation_failure(self, step: WorkflowStep, error: str) -> RecoveryAction:
        """Handle validation failure errors"""
        return RecoveryAction.ALTERNATIVE_PATH
    
    async def _handle_constitutional_violation(self, step: WorkflowStep, error: str) -> RecoveryAction:
        """Handle constitutional violation errors"""
        return RecoveryAction.ROLLBACK
    
    async def _handle_cryptographic_failure(self, step: WorkflowStep, error: str) -> RecoveryAction:
        """Handle cryptographic failure errors"""
        return RecoveryAction.ROLLBACK
    
    # Rollback handlers
    async def _rollback_policy_deployment(self, step: WorkflowStep, checkpoint_data: Dict[str, Any]):
        """Rollback policy deployment"""
        logger.info(f"Rolling back policy deployment for step {step.id}")
        # Implementation would remove deployed policies
    
    async def _rollback_constitutional_amendment(self, step: WorkflowStep, checkpoint_data: Dict[str, Any]):
        """Rollback constitutional amendment"""
        logger.info(f"Rolling back constitutional amendment for step {step.id}")
        # Implementation would revert constitutional changes
    
    async def _rollback_cryptographic_signing(self, step: WorkflowStep, checkpoint_data: Dict[str, Any]):
        """Rollback cryptographic signing"""
        logger.info(f"Rolling back cryptographic signing for step {step.id}")
        # Implementation would revoke signatures
    
    def get_recovery_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get recovery status for a workflow"""
        
        checkpoints = self.checkpoints.get(workflow_id, [])
        recovery_plans = [p for p in self.recovery_plans.values() if p.workflow_id == workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "checkpoints": len(checkpoints),
            "latest_checkpoint": checkpoints[-1].timestamp.isoformat() if checkpoints else None,
            "recovery_plans": len(recovery_plans),
            "active_recovery": any(p.retry_count < p.max_retries for p in recovery_plans)
        }

# Global recovery manager instance
recovery_manager = WorkflowRecoveryManager()
