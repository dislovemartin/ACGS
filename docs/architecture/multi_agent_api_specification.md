# Multi-Agent DGM API Specification

**Version:** 1.0  
**Date:** June 2, 2025  

## API Overview

This document provides detailed API specifications for all components in the Multi-Agent DGM system, including request/response schemas, error handling, and integration patterns.

## Core Data Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned" 
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentType(str, Enum):
    MASTER = "master"
    SUB_MASTER = "sub_master"
    WORKER = "worker"

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class Priority(int, Enum):
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10

# Core Models
class Goal(BaseModel):
    goal_id: Optional[str] = None
    description: str = Field(..., min_length=10, max_length=5000)
    priority: Priority = Priority.MEDIUM
    constraints: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None
    domain_hints: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Task(BaseModel):
    task_id: Optional[str] = None
    goal_id: str
    parent_task_id: Optional[str] = None
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    domain: str
    agent_type: AgentType
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    dependencies: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    estimated_duration: Optional[int] = None  # minutes
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Agent(BaseModel):
    agent_id: str
    agent_type: AgentType
    domain: Optional[str] = None
    specialization: Optional[str] = None
    status: HealthStatus = HealthStatus.UNKNOWN
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    resource_limits: Dict[str, Any] = Field(default_factory=dict)
    last_heartbeat: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskResult(BaseModel):
    task_id: str
    agent_id: str
    status: TaskStatus
    result: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float  # seconds
    quality_score: Optional[float] = None
    error_details: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

## Master Agent API

### Goal Management

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="Multi-Agent DGM Master API", version="1.0.0")
security = HTTPBearer()

@app.post("/api/v1/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal: GoalRequest,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> GoalResponse:
    """
    Create a new goal for multi-agent execution
    
    - **description**: Detailed goal description (10-5000 chars)
    - **priority**: Goal priority (1-10, default 5)
    - **constraints**: Execution constraints (optional)
    - **deadline**: Goal deadline (optional)
    - **domain_hints**: Suggested domains for execution
    
    Returns:
    - **goal_id**: Unique identifier for the goal
    - **status**: Current goal status
    - **estimated_completion**: Estimated completion time
    - **tasks_created**: Number of tasks generated
    """
    
@app.get("/api/v1/goals/{goal_id}", response_model=GoalDetailResponse)
async def get_goal(
    goal_id: str,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> GoalDetailResponse:
    """Get detailed information about a specific goal"""
    
@app.get("/api/v1/goals", response_model=List[GoalSummary])
async def list_goals(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> List[GoalSummary]:
    """List goals with optional filtering"""

@app.patch("/api/v1/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    updates: GoalUpdateRequest,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> GoalResponse:
    """Update goal properties"""

@app.delete("/api/v1/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_goal(
    goal_id: str,
    reason: Optional[str] = None,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Cancel goal execution"""
```

### Task Management

```python
@app.get("/api/v1/goals/{goal_id}/tasks", response_model=List[TaskSummary])
async def get_goal_tasks(
    goal_id: str,
    status: Optional[TaskStatus] = None,
    domain: Optional[str] = None,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> List[TaskSummary]:
    """Get all tasks for a specific goal"""

@app.get("/api/v1/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> TaskDetailResponse:
    """Get detailed task information"""

@app.patch("/api/v1/tasks/{task_id}/assign", response_model=TaskAssignmentResponse)
async def assign_task(
    task_id: str,
    assignment: TaskAssignmentRequest,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> TaskAssignmentResponse:
    """Manually assign task to specific agent"""

@app.post("/api/v1/tasks/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    retry_request: TaskRetryRequest,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> TaskResponse:
    """Retry failed task execution"""
```

### Agent Management

```python
@app.get("/api/v1/agents", response_model=List[AgentSummary])
async def list_agents(
    agent_type: Optional[AgentType] = None,
    domain: Optional[str] = None,
    status: Optional[HealthStatus] = None,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> List[AgentSummary]:
    """List all agents with filtering options"""

@app.get("/api/v1/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: str,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> AgentDetailResponse:
    """Get detailed agent information"""

@app.post("/api/v1/agents/scale", response_model=ScalingResponse)
async def scale_agents(
    scaling_request: AgentScalingRequest,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> ScalingResponse:
    """Scale agent instances for specific domains"""

@app.post("/api/v1/agents/{agent_id}/terminate", status_code=status.HTTP_202_ACCEPTED)
async def terminate_agent(
    agent_id: str,
    termination_request: AgentTerminationRequest,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Gracefully terminate an agent"""
```

### System Health & Monitoring

```python
@app.get("/api/v1/health", response_model=SystemHealthResponse)
async def get_system_health() -> SystemHealthResponse:
    """Get comprehensive system health status"""

@app.get("/api/v1/health/agents", response_model=Dict[str, AgentHealthResponse])
async def get_agents_health(
    token: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, AgentHealthResponse]:
    """Get health status of all agents"""

@app.get("/api/v1/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    time_range: str = "1h",
    token: HTTPAuthorizationCredentials = Depends(security)
) -> SystemMetricsResponse:
    """Get system performance metrics"""

@app.get("/api/v1/metrics/goals", response_model=GoalMetricsResponse)
async def get_goal_metrics(
    time_range: str = "24h",
    token: HTTPAuthorizationCredentials = Depends(security)
) -> GoalMetricsResponse:
    """Get goal execution metrics"""
```

## Worker Agent API

```python
@app.post("/api/v1/tasks/accept", response_model=TaskAcceptanceResponse)
async def accept_task(
    task_assignment: TaskAssignmentMessage,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> TaskAcceptanceResponse:
    """Accept a task assignment from master/sub-master"""

@app.post("/api/v1/tasks/{task_id}/progress", response_model=ProgressUpdateResponse)
async def update_task_progress(
    task_id: str,
    progress_update: TaskProgressUpdate,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> ProgressUpdateResponse:
    """Update task execution progress"""

@app.post("/api/v1/tasks/{task_id}/complete", response_model=TaskCompletionResponse)
async def complete_task(
    task_id: str,
    completion_data: TaskCompletionData,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> TaskCompletionResponse:
    """Mark task as completed with results"""

@app.post("/api/v1/context/request", response_model=ContextResponse)
async def request_context(
    context_request: ContextRequestMessage,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> ContextResponse:
    """Request additional context for task execution"""

@app.get("/api/v1/capabilities", response_model=WorkerCapabilitiesResponse)
async def get_capabilities(
    token: HTTPAuthorizationCredentials = Depends(security)
) -> WorkerCapabilitiesResponse:
    """Get worker capabilities and specializations"""

@app.post("/api/v1/capabilities/update", response_model=CapabilityUpdateResponse)
async def update_capabilities(
    capability_update: WorkerCapabilityUpdate,
    token: HTTPAuthorizationCredentials = Depends(security)
) -> CapabilityUpdateResponse:
    """Update worker capabilities"""

@app.get("/api/v1/health", response_model=WorkerHealthResponse)
async def get_worker_health() -> WorkerHealthResponse:
    """Get worker health status"""

@app.post("/api/v1/heartbeat", status_code=status.HTTP_200_OK)
async def send_heartbeat(
    heartbeat: HeartbeatMessage,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Send heartbeat to master agent"""
```

## Error Handling

```python
from fastapi import HTTPException
from enum import Enum

class ErrorCode(str, Enum):
    # Authentication & Authorization
    INVALID_TOKEN = "INVALID_TOKEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Goal Management
    GOAL_NOT_FOUND = "GOAL_NOT_FOUND"
    INVALID_GOAL_DESCRIPTION = "INVALID_GOAL_DESCRIPTION"
    GOAL_ALREADY_COMPLETED = "GOAL_ALREADY_COMPLETED"
    
    # Task Management
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_ALREADY_ASSIGNED = "TASK_ALREADY_ASSIGNED"
    INVALID_TASK_DEPENDENCY = "INVALID_TASK_DEPENDENCY"
    TASK_EXECUTION_TIMEOUT = "TASK_EXECUTION_TIMEOUT"
    
    # Agent Management
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_UNAVAILABLE = "AGENT_UNAVAILABLE"
    SCALING_LIMIT_EXCEEDED = "SCALING_LIMIT_EXCEEDED"
    
    # System Errors
    DATABASE_ERROR = "DATABASE_ERROR"
    MESSAGE_QUEUE_ERROR = "MESSAGE_QUEUE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # Constitutional Governance
    CONSTITUTIONAL_VIOLATION = "CONSTITUTIONAL_VIOLATION"
    GOVERNANCE_POLICY_VIOLATION = "GOVERNANCE_POLICY_VIOLATION"

class APIError(BaseModel):
    error_code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Error response models
class ErrorResponse(BaseModel):
    error: APIError

# Common HTTP exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=APIError(
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                message=exc.detail,
                trace_id=request.headers.get("X-Trace-ID")
            )
        ).dict()
    )
```

## Request/Response Models

```python
# Goal Management Models
class GoalRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=5000)
    priority: Priority = Priority.MEDIUM
    constraints: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None
    domain_hints: List[str] = Field(default_factory=list)

class GoalResponse(BaseModel):
    goal_id: str
    status: str
    estimated_completion: Optional[datetime]
    tasks_created: int
    agents_allocated: int
    created_at: datetime

class GoalDetailResponse(BaseModel):
    goal: Goal
    tasks: List[TaskSummary]
    progress: GoalProgress
    resource_usage: ResourceUsage
    timeline: List[GoalEvent]

class GoalProgress(BaseModel):
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    percentage_complete: float
    estimated_remaining_time: Optional[int]  # minutes

# Task Management Models
class TaskSummary(BaseModel):
    task_id: str
    title: str
    domain: str
    status: TaskStatus
    assigned_agent: Optional[str]
    progress_percentage: float
    created_at: datetime
    estimated_completion: Optional[datetime]

class TaskDetailResponse(BaseModel):
    task: Task
    execution_history: List[TaskExecution]
    dependencies: List[TaskDependency]
    results: Optional[TaskResult]
    resource_usage: ResourceUsage

class TaskAssignmentRequest(BaseModel):
    agent_id: str
    priority_override: Optional[Priority] = None
    additional_context: Dict[str, Any] = Field(default_factory=dict)

class TaskAssignmentResponse(BaseModel):
    task_id: str
    assigned_agent: str
    assignment_time: datetime
    estimated_start_time: datetime

# Agent Management Models
class AgentSummary(BaseModel):
    agent_id: str
    agent_type: AgentType
    domain: Optional[str]
    status: HealthStatus
    current_tasks: int
    performance_score: float
    last_activity: datetime

class AgentDetailResponse(BaseModel):
    agent: Agent
    current_tasks: List[TaskSummary]
    performance_history: List[PerformanceDataPoint]
    resource_usage: ResourceUsage
    capabilities: AgentCapabilities

class AgentScalingRequest(BaseModel):
    domain: str
    target_instances: int
    scaling_reason: str
    priority: Priority = Priority.MEDIUM

class ScalingResponse(BaseModel):
    scaling_id: str
    domain: str
    current_instances: int
    target_instances: int
    estimated_completion_time: datetime
    status: str

# Health & Monitoring Models
class SystemHealthResponse(BaseModel):
    overall_status: HealthStatus
    components: Dict[str, ComponentHealth]
    active_goals: int
    active_tasks: int
    active_agents: int
    error_rate: float
    response_time_p95: float
    uptime_seconds: int

class ComponentHealth(BaseModel):
    status: HealthStatus
    last_check: datetime
    error_count: int
    response_time: float
    details: Dict[str, Any]

class SystemMetricsResponse(BaseModel):
    time_range: str
    goal_metrics: GoalMetrics
    task_metrics: TaskMetrics
    agent_metrics: AgentMetrics
    system_metrics: SystemMetrics

class GoalMetrics(BaseModel):
    total_goals: int
    completed_goals: int
    failed_goals: int
    avg_completion_time: float
    success_rate: float

class TaskMetrics(BaseModel):
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_execution_time: float
    queue_depth: int

class AgentMetrics(BaseModel):
    total_agents: int
    active_agents: int
    avg_utilization: float
    avg_performance_score: float
    scaling_events: int
```

## Authentication & Authorization

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta

class AuthService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=1)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Dependency for protected endpoints
async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    auth_service = AuthService(settings.SECRET_KEY)
    payload = auth_service.verify_token(token.credentials)
    return payload

# Role-based access control
class Permission(str, Enum):
    READ_GOALS = "read:goals"
    WRITE_GOALS = "write:goals"
    MANAGE_AGENTS = "manage:agents"
    SYSTEM_ADMIN = "system:admin"

async def require_permission(permission: Permission):
    def permission_checker(current_user: dict = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        if permission not in user_permissions and Permission.SYSTEM_ADMIN not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return permission_checker
```

## Rate Limiting & Throttling

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits to endpoints
@app.post("/api/v1/goals")
@limiter.limit("10/minute")
async def create_goal(request: Request, goal: GoalRequest):
    # Implementation
    pass

@app.get("/api/v1/health")
@limiter.limit("100/minute")
async def get_system_health(request: Request):
    # Implementation
    pass
```

## API Versioning Strategy

```python
from fastapi import APIRouter

# Version 1 API
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Version 2 API (future)
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

app.include_router(v1_router)

# Backward compatibility middleware
@app.middleware("http")
async def version_compatibility_middleware(request: Request, call_next):
    # Handle version compatibility logic
    response = await call_next(request)
    response.headers["API-Version"] = "1.0"
    return response
```

This API specification provides a comprehensive foundation for implementing the Multi-Agent DGM system with proper error handling, authentication, and scalability considerations.