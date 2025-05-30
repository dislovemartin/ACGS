"""
ACGS-PGP Centralized Workflow Orchestration Engine
Provides state management, coordination, and monitoring for all framework workflows
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class WorkflowType(Enum):
    POLICY_SYNTHESIS = "policy_synthesis"
    CONSTITUTIONAL_AMENDMENT = "constitutional_amendment"
    CONFLICT_RESOLUTION = "conflict_resolution"
    FORMAL_VERIFICATION = "formal_verification"
    CRYPTOGRAPHIC_SIGNING = "cryptographic_signing"
    COMPLIANCE_AUDIT = "compliance_audit"
    ALPHAEVOLVE_INTEGRATION = "alphaevolve_integration"

@dataclass
class WorkflowStep:
    id: str
    name: str
    service: str
    endpoint: str
    input_data: Dict[str, Any]
    dependencies: List[str]
    timeout_seconds: int = 300
    retry_count: int = 3
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class Workflow:
    id: str
    type: WorkflowType
    name: str
    description: str
    steps: List[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

class WorkflowEngine:
    """
    Centralized workflow orchestration engine for ACGS-PGP
    """
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
        self.step_handlers: Dict[str, Callable] = {}
        self.workflow_templates: Dict[WorkflowType, List[WorkflowStep]] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize predefined workflow templates"""
        
        # Policy Synthesis Workflow
        self.workflow_templates[WorkflowType.POLICY_SYNTHESIS] = [
            WorkflowStep(
                id="fetch_principles",
                name="Fetch Constitutional Principles",
                service="ac_service",
                endpoint="/api/v1/principles",
                input_data={},
                dependencies=[]
            ),
            WorkflowStep(
                id="synthesize_policy",
                name="Generate Policy Rules",
                service="gs_service",
                endpoint="/api/v1/synthesize",
                input_data={},
                dependencies=["fetch_principles"]
            ),
            WorkflowStep(
                id="verify_policy",
                name="Formal Verification",
                service="fv_service",
                endpoint="/api/v1/verify",
                input_data={},
                dependencies=["synthesize_policy"]
            ),
            WorkflowStep(
                id="sign_policy",
                name="Cryptographic Signing",
                service="integrity_service",
                endpoint="/api/v1/sign",
                input_data={},
                dependencies=["verify_policy"]
            ),
            WorkflowStep(
                id="deploy_policy",
                name="Deploy to PGC",
                service="pgc_service",
                endpoint="/api/v1/deploy",
                input_data={},
                dependencies=["sign_policy"]
            )
        ]
        
        # Constitutional Amendment Workflow
        self.workflow_templates[WorkflowType.CONSTITUTIONAL_AMENDMENT] = [
            WorkflowStep(
                id="validate_amendment",
                name="Validate Amendment Proposal",
                service="ac_service",
                endpoint="/api/v1/constitutional-council/amendments/validate",
                input_data={},
                dependencies=[]
            ),
            WorkflowStep(
                id="public_consultation",
                name="Public Consultation Period",
                service="ac_service",
                endpoint="/api/v1/constitutional-council/amendments/consultation",
                input_data={},
                dependencies=["validate_amendment"],
                timeout_seconds=86400  # 24 hours
            ),
            WorkflowStep(
                id="council_vote",
                name="Constitutional Council Vote",
                service="ac_service",
                endpoint="/api/v1/constitutional-council/amendments/vote",
                input_data={},
                dependencies=["public_consultation"]
            ),
            WorkflowStep(
                id="implement_amendment",
                name="Implement Amendment",
                service="ac_service",
                endpoint="/api/v1/constitutional-council/amendments/implement",
                input_data={},
                dependencies=["council_vote"]
            )
        ]
        
        # AlphaEvolve Integration Workflow
        self.workflow_templates[WorkflowType.ALPHAEVOLVE_INTEGRATION] = [
            WorkflowStep(
                id="sync_principles",
                name="Synchronize Constitutional Principles",
                service="gs_service",
                endpoint="/api/v1/alphaevolve/sync-principles",
                input_data={},
                dependencies=[]
            ),
            WorkflowStep(
                id="evaluate_governance",
                name="Evaluate Governance Context",
                service="gs_service",
                endpoint="/api/v1/alphaevolve/evaluate",
                input_data={},
                dependencies=["sync_principles"]
            ),
            WorkflowStep(
                id="synthesize_ec_policy",
                name="Synthesize EC-Specific Policy",
                service="gs_service",
                endpoint="/api/v1/alphaevolve/synthesize",
                input_data={},
                dependencies=["evaluate_governance"]
            )
        ]
    
    async def create_workflow(
        self,
        workflow_type: WorkflowType,
        name: str,
        description: str,
        input_data: Dict[str, Any],
        created_by: str,
        custom_steps: Optional[List[WorkflowStep]] = None
    ) -> str:
        """Create a new workflow instance"""
        
        workflow_id = str(uuid.uuid4())
        
        # Use custom steps or template
        if custom_steps:
            steps = custom_steps
        else:
            steps = self.workflow_templates.get(workflow_type, []).copy()
        
        # Inject input data into first step
        if steps:
            steps[0].input_data.update(input_data)
        
        workflow = Workflow(
            id=workflow_id,
            type=workflow_type,
            name=name,
            description=description,
            steps=steps,
            created_by=created_by,
            metadata={"input_data": input_data}
        )
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow {workflow_id}: {name}")
        
        return workflow_id
    
    async def start_workflow(self, workflow_id: str) -> bool:
        """Start workflow execution"""
        
        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.PENDING:
            logger.error(f"Workflow {workflow_id} is not in pending state")
            return False
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        
        # Start workflow execution task
        task = asyncio.create_task(self._execute_workflow(workflow))
        self.running_workflows[workflow_id] = task
        
        logger.info(f"Started workflow {workflow_id}")
        return True
    
    async def _execute_workflow(self, workflow: Workflow):
        """Execute workflow steps with dependency management"""
        
        try:
            completed_steps = set()
            
            while len(completed_steps) < len(workflow.steps):
                # Find steps ready to execute
                ready_steps = [
                    step for step in workflow.steps
                    if (step.status == WorkflowStatus.PENDING and
                        all(dep in completed_steps for dep in step.dependencies))
                ]
                
                if not ready_steps:
                    # Check for deadlock
                    pending_steps = [s for s in workflow.steps if s.status == WorkflowStatus.PENDING]
                    if pending_steps:
                        raise Exception("Workflow deadlock detected")
                    break
                
                # Execute ready steps in parallel
                tasks = []
                for step in ready_steps:
                    task = asyncio.create_task(self._execute_step(workflow, step))
                    tasks.append(task)
                
                # Wait for all steps to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    step = ready_steps[i]
                    if isinstance(result, Exception):
                        step.status = WorkflowStatus.FAILED
                        step.error_message = str(result)
                        workflow.status = WorkflowStatus.FAILED
                        logger.error(f"Step {step.id} failed: {result}")
                        return
                    else:
                        step.status = WorkflowStatus.COMPLETED
                        step.result = result
                        completed_steps.add(step.id)
                        logger.info(f"Step {step.id} completed successfully")
            
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            logger.info(f"Workflow {workflow.id} completed successfully")
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            logger.error(f"Workflow {workflow.id} failed: {e}")
        
        finally:
            # Cleanup
            if workflow.id in self.running_workflows:
                del self.running_workflows[workflow.id]
    
    async def _execute_step(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a single workflow step"""
        
        step.status = WorkflowStatus.RUNNING
        step.started_at = datetime.utcnow()
        
        try:
            # Get step handler
            handler = self.step_handlers.get(step.service)
            if not handler:
                raise Exception(f"No handler found for service {step.service}")
            
            # Execute step with timeout and retry
            for attempt in range(step.retry_count):
                try:
                    result = await asyncio.wait_for(
                        handler(step.endpoint, step.input_data),
                        timeout=step.timeout_seconds
                    )
                    step.completed_at = datetime.utcnow()
                    return result
                
                except asyncio.TimeoutError:
                    if attempt == step.retry_count - 1:
                        raise Exception(f"Step timed out after {step.timeout_seconds} seconds")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
                except Exception as e:
                    if attempt == step.retry_count - 1:
                        raise e
                    await asyncio.sleep(2 ** attempt)
        
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.error_message = str(e)
            raise e
    
    def register_step_handler(self, service: str, handler: Callable):
        """Register a step execution handler for a service"""
        self.step_handlers[service] = handler
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status and progress"""
        
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        
        completed_steps = len([s for s in workflow.steps if s.status == WorkflowStatus.COMPLETED])
        total_steps = len(workflow.steps)
        
        return {
            "id": workflow.id,
            "type": workflow.type.value,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress": f"{completed_steps}/{total_steps}",
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "status": step.status.value,
                    "error": step.error_message
                }
                for step in workflow.steps
            ]
        }
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause workflow execution"""
        
        if workflow_id in self.running_workflows:
            task = self.running_workflows[workflow_id]
            task.cancel()
            
            workflow = self.workflows[workflow_id]
            workflow.status = WorkflowStatus.PAUSED
            
            logger.info(f"Paused workflow {workflow_id}")
            return True
        
        return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume paused workflow"""
        
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.PAUSED:
            return False
        
        workflow.status = WorkflowStatus.RUNNING
        
        # Restart execution
        task = asyncio.create_task(self._execute_workflow(workflow))
        self.running_workflows[workflow_id] = task
        
        logger.info(f"Resumed workflow {workflow_id}")
        return True
    
    def list_workflows(self, status: Optional[WorkflowStatus] = None) -> List[Dict[str, Any]]:
        """List all workflows with optional status filter"""
        
        workflows = list(self.workflows.values())
        
        if status:
            workflows = [w for w in workflows if w.status == status]
        
        return [
            {
                "id": w.id,
                "type": w.type.value,
                "name": w.name,
                "status": w.status.value,
                "created_at": w.created_at.isoformat(),
                "created_by": w.created_by
            }
            for w in workflows
        ]

# Global workflow engine instance
workflow_engine = WorkflowEngine()
