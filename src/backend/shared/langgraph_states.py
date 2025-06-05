"""
Shared LangGraph State Management for ACGS-PGP

This module provides base state classes and utilities for LangGraph workflows
across the ACGS-PGP microservices architecture. It implements patterns from
the Gemini-LangGraph quickstart for constitutional governance workflows.
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime, timezone
import operator
from enum import Enum

try:
    from langgraph.graph import add_messages
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Fallback for environments without LangGraph
    def add_messages(x, y):
        """Fallback message accumulator when LangGraph is not available."""
        if isinstance(x, list) and isinstance(y, list):
            return x + y
        elif isinstance(x, list):
            return x + [y]
        elif isinstance(y, list):
            return [x] + y
        else:
            return [x, y]
    LANGGRAPH_AVAILABLE = False


class WorkflowStatus(str, Enum):
    """Standard workflow status values for ACGS-PGP workflows."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


class BaseACGSState(TypedDict):
    """
    Base state for all ACGS-PGP LangGraph workflows.
    
    Provides common fields for user context, session management,
    and workflow tracking across all constitutional governance processes.
    """
    # Message handling (LangGraph standard)
    messages: Annotated[list, add_messages]
    
    # User and session context
    user_id: Optional[str]
    session_id: Optional[str]
    workflow_id: Optional[str]
    
    # Temporal tracking
    created_at: Optional[str]
    updated_at: Optional[str]
    
    # Workflow management
    status: Optional[str]  # WorkflowStatus enum value
    error_message: Optional[str]
    retry_count: Optional[int]
    
    # Metadata and configuration
    metadata: Optional[Dict[str, Any]]
    configuration: Optional[Dict[str, Any]]


class ConstitutionalCouncilState(BaseACGSState):
    """
    State for Constitutional Council amendment workflows.
    
    Manages the complete lifecycle of constitutional amendments including
    proposal generation, stakeholder feedback, analysis, and voting.
    """
    # Amendment proposal data
    amendment_proposal: Optional[Dict[str, Any]]
    amendment_id: Optional[str]
    amendment_type: Optional[str]  # "principle_addition", "principle_modification", "meta_rule_change"
    
    # Stakeholder engagement
    stakeholder_feedback: Annotated[List[Dict[str, Any]], operator.add]
    stakeholder_notifications: Annotated[List[Dict[str, Any]], operator.add]
    required_stakeholders: Optional[List[str]]
    
    # Constitutional analysis
    constitutional_analysis: Optional[Dict[str, Any]]
    compliance_score: Optional[float]
    identified_conflicts: Annotated[List[Dict[str, Any]], operator.add]
    
    # Voting and decision process
    voting_results: Optional[Dict[str, Any]]
    voting_deadline: Optional[str]
    quorum_met: Optional[bool]
    
    # Iterative refinement
    refinement_iterations: Optional[int]
    max_refinement_iterations: Optional[int]
    is_constitutional: Optional[bool]
    requires_refinement: Optional[bool]
    escalation_required: Optional[bool]
    
    # Workflow state tracking
    current_phase: Optional[str]  # "proposal", "feedback", "analysis", "voting", "implementation"
    phase_deadlines: Optional[Dict[str, str]]
    automated_processing: Optional[bool]


class PolicySynthesisState(BaseACGSState):
    """
    State for GS Engine policy synthesis workflows.
    
    Manages the translation of constitutional principles into operational
    policies with iterative refinement and constitutional compliance validation.
    """
    # Input constitutional principles
    constitutional_principles: Optional[List[Dict[str, Any]]]
    principle_ids: Optional[List[str]]
    
    # Synthesis context and requirements
    synthesis_context: Optional[Dict[str, Any]]
    target_domain: Optional[str]
    compliance_requirements: Optional[List[str]]
    
    # Generated policies and validation
    generated_policies: Annotated[List[Dict[str, Any]], operator.add]
    policy_templates: Optional[List[Dict[str, Any]]]
    validation_results: Annotated[List[Dict[str, Any]], operator.add]
    
    # Quality and compliance metrics
    synthesis_iterations: Optional[int]
    max_synthesis_iterations: Optional[int]
    constitutional_fidelity_score: Optional[float]
    fidelity_threshold: Optional[float]
    
    # Multi-model LLM tracking
    model_responses: Annotated[List[Dict[str, Any]], operator.add]
    model_performance: Optional[Dict[str, Any]]
    fallback_used: Optional[bool]
    
    # Human oversight and review
    requires_human_review: Optional[bool]
    human_feedback: Annotated[List[Dict[str, Any]], operator.add]
    expert_validation: Optional[Dict[str, Any]]
    
    # Output and deployment
    final_policies: Optional[List[Dict[str, Any]]]
    deployment_ready: Optional[bool]
    rego_policies: Optional[List[str]]


class ConstitutionalFidelityState(BaseACGSState):
    """
    State for constitutional fidelity monitoring and QEC-inspired error correction.
    
    Tracks constitutional compliance in real-time and manages error correction
    workflows for maintaining constitutional integrity.
    """
    # Fidelity monitoring
    current_fidelity_score: Optional[float]
    fidelity_history: Annotated[List[Dict[str, Any]], operator.add]
    fidelity_threshold: Optional[float]
    alert_level: Optional[str]  # "green", "amber", "red"
    
    # Constitutional violations
    detected_violations: Annotated[List[Dict[str, Any]], operator.add]
    violation_severity: Optional[str]  # "low", "medium", "high", "critical"
    violation_categories: Optional[List[str]]
    
    # Error correction and recovery
    corrective_actions: Annotated[List[Dict[str, Any]], operator.add]
    correction_attempts: Optional[int]
    max_correction_attempts: Optional[int]
    recovery_strategies: Optional[List[str]]
    
    # Performance and metrics
    monitoring_metrics: Optional[Dict[str, Any]]
    performance_degradation: Optional[bool]
    system_health: Optional[Dict[str, Any]]
    
    # Escalation and human intervention
    escalation_triggered: Optional[bool]
    human_intervention_required: Optional[bool]
    escalation_reason: Optional[str]


class MultiModelLLMState(BaseACGSState):
    """
    State for multi-model LLM management and reliability tracking.
    
    Manages model selection, fallback mechanisms, and performance monitoring
    for achieving >99.9% reliability targets.
    """
    # Model configuration and selection
    primary_model: Optional[str]
    fallback_models: Optional[List[str]]
    model_roles: Optional[Dict[str, str]]  # role -> model mapping
    
    # Request and response tracking
    model_requests: Annotated[List[Dict[str, Any]], operator.add]
    model_responses: Annotated[List[Dict[str, Any]], operator.add]
    response_times: Annotated[List[float], operator.add]
    
    # Reliability and performance metrics
    success_rate: Optional[float]
    average_response_time: Optional[float]
    error_rate: Optional[float]
    fallback_usage_rate: Optional[float]
    
    # Error handling and recovery
    failed_requests: Annotated[List[Dict[str, Any]], operator.add]
    retry_attempts: Optional[int]
    max_retries: Optional[int]
    circuit_breaker_status: Optional[str]  # "closed", "open", "half_open"
    
    # Quality assessment
    output_quality_scores: Annotated[List[float], operator.add]
    constitutional_compliance_scores: Annotated[List[float], operator.add]
    bias_detection_results: Annotated[List[Dict[str, Any]], operator.add]


def create_workflow_metadata(
    workflow_type: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    configuration: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized metadata for ACGS-PGP workflows.
    
    Args:
        workflow_type: Type of workflow (e.g., "constitutional_council", "policy_synthesis")
        user_id: Optional user identifier
        session_id: Optional session identifier
        configuration: Optional workflow configuration
        
    Returns:
        Standardized metadata dictionary
    """
    now = datetime.now(timezone.utc).isoformat()
    
    return {
        "workflow_type": workflow_type,
        "user_id": user_id,
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        "status": WorkflowStatus.PENDING.value,
        "retry_count": 0,
        "configuration": configuration or {},
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "acgs_version": "1.0.0"
    }


def update_workflow_status(
    state: BaseACGSState,
    status: WorkflowStatus,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update workflow status with timestamp and error handling.
    
    Args:
        state: Current workflow state
        status: New workflow status
        error_message: Optional error message for failed states
        
    Returns:
        State update dictionary
    """
    update = {
        "status": status.value,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if error_message:
        update["error_message"] = error_message
        
    if status == WorkflowStatus.FAILED:
        retry_count = state.get("retry_count", 0)
        update["retry_count"] = retry_count + 1
        
    return update
