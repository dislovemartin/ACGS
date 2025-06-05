"""
Policy Synthesis Workflow using LangGraph StateGraph

This module implements the LangGraph StateGraph workflow for policy synthesis
with multi-model orchestration, constitutional compliance validation, and
reliability enhancement patterns.

Task 18.1: Extended MultiModelManager with LangGraph StateGraph integration
Task 18.4: Reliability Enhancement with circuit breaker patterns
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.state import CompiledStateGraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None
    CompiledStateGraph = None

from .structured_output_models import (
    PolicySynthesisRequest,
    PolicySynthesisResponse,
    WorkflowState,
    RegoPolicy,
    ConstitutionalFidelityScore,
    ConstitutionalComplianceLevel,
    ModelSpecializationConfig
)
from .multi_model_manager import get_multi_model_manager
from shared.langgraph_config import ModelRole

logger = logging.getLogger(__name__)


class PolicySynthesisWorkflow:
    """
    LangGraph StateGraph workflow for policy synthesis with multi-model orchestration.
    
    Implements the following workflow:
    1. Constitutional Analysis - Analyze principles and context
    2. Policy Generation - Generate initial policy draft
    3. Fidelity Assessment - Validate constitutional compliance
    4. Conflict Resolution - Resolve any detected conflicts
    5. Final Validation - Ensure quality meets thresholds
    """
    
    def __init__(self):
        self.multi_model_manager = get_multi_model_manager()
        self.config = ModelSpecializationConfig()
        self.workflow_graph: Optional[CompiledStateGraph] = None
        
        if LANGGRAPH_AVAILABLE:
            self._build_workflow_graph()
        else:
            logger.warning("LangGraph not available. Workflow will use fallback implementation.")
    
    def _build_workflow_graph(self):
        """Build the LangGraph StateGraph for policy synthesis."""
        if not LANGGRAPH_AVAILABLE:
            return
        
        # Create the state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each workflow step (using node_ prefix to avoid state field conflicts)
        workflow.add_node("node_analyze_constitution", self._constitutional_analysis_node)
        workflow.add_node("node_generate_policy", self._policy_generation_node)
        workflow.add_node("node_assess_fidelity", self._fidelity_assessment_node)
        workflow.add_node("node_resolve_conflicts", self._conflict_resolution_node)
        workflow.add_node("node_validate_final", self._final_validation_node)
        workflow.add_node("node_handle_errors", self._error_handling_node)

        # Define the workflow edges
        workflow.set_entry_point("node_analyze_constitution")

        # Normal flow
        workflow.add_edge("node_analyze_constitution", "node_generate_policy")
        workflow.add_edge("node_generate_policy", "node_assess_fidelity")

        # Conditional edges based on fidelity assessment
        workflow.add_conditional_edges(
            "node_assess_fidelity",
            self._should_resolve_conflicts,
            {
                "resolve_conflicts": "node_resolve_conflicts",
                "validate": "node_validate_final",
                "error": "node_handle_errors"
            }
        )

        workflow.add_edge("node_resolve_conflicts", "node_assess_fidelity")  # Re-assess after resolution

        # Final validation outcomes
        workflow.add_conditional_edges(
            "node_validate_final",
            self._should_retry_or_complete,
            {
                "retry": "node_generate_policy",
                "complete": END,
                "error": "node_handle_errors"
            }
        )

        workflow.add_edge("node_handle_errors", END)
        
        # Compile the workflow
        self.workflow_graph = workflow.compile()
        logger.info("Policy synthesis workflow graph compiled successfully")
    
    async def synthesize_policy(self, request: PolicySynthesisRequest) -> PolicySynthesisResponse:
        """
        Execute the policy synthesis workflow.
        
        Args:
            request: Policy synthesis request
            
        Returns:
            Policy synthesis response with generated policy and metrics
        """
        start_time = time.time()
        
        # Initialize workflow state
        workflow_state = WorkflowState(
            request=request,
            current_step="initialization",
            workflow_id=f"synthesis_{request.request_id}_{int(time.time())}"
        )
        
        try:
            if LANGGRAPH_AVAILABLE and self.workflow_graph:
                # Execute LangGraph workflow
                final_state = await self.workflow_graph.ainvoke(workflow_state)
            else:
                # Fallback to sequential execution
                final_state = await self._execute_fallback_workflow(workflow_state)
            
            # Build response
            synthesis_duration = (time.time() - start_time) * 1000
            
            response = PolicySynthesisResponse(
                request_id=request.request_id,
                success=final_state.policy_draft is not None,
                policy=final_state.policy_draft,
                model_used=self._get_primary_model_used(final_state),
                synthesis_duration_ms=synthesis_duration,
                attempt_count=final_state.retry_count + 1,
                constitutional_fidelity=final_state.fidelity_assessment,
                synthesis_confidence=self._calculate_synthesis_confidence(final_state),
                error_message=final_state.errors[-1] if final_state.errors else None,
                fallback_used=not LANGGRAPH_AVAILABLE,
                improvement_suggestions=self._generate_improvement_suggestions(final_state)
            )
            
            logger.info(f"Policy synthesis completed for request {request.request_id} in {synthesis_duration:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Policy synthesis failed for request {request.request_id}: {e}")
            
            return PolicySynthesisResponse(
                request_id=request.request_id,
                success=False,
                model_used="error",
                synthesis_duration_ms=(time.time() - start_time) * 1000,
                synthesis_confidence=0.0,
                error_message=str(e),
                fallback_used=True
            )
    
    async def _constitutional_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze constitutional principles and context."""
        state.add_step("constitutional_analysis")
        
        try:
            # Use specialized constitutional prompting model
            analysis_prompt = self._build_constitutional_analysis_prompt(state.request)
            
            response = await self.multi_model_manager.get_model_response(
                role=ModelRole.CONSTITUTIONAL_PROMPTING,
                prompt=analysis_prompt,
                structured_output_class=None  # We'll parse the response manually
            )
            
            if response["success"]:
                state.constitutional_analysis = {
                    "analysis": response["content"],
                    "model_used": response["model_used"],
                    "response_time": response["response_time"]
                }
                logger.info(f"Constitutional analysis completed for workflow {state.workflow_id}")
            else:
                state.add_error(f"Constitutional analysis failed: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            state.add_error(f"Constitutional analysis error: {str(e)}")
            logger.error(f"Constitutional analysis failed for workflow {state.workflow_id}: {e}")
        
        return state
    
    async def _policy_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Generate policy draft based on constitutional analysis."""
        state.add_step("policy_generation")
        
        try:
            # Use specialized policy synthesis model
            generation_prompt = self._build_policy_generation_prompt(state)
            
            response = await self.multi_model_manager.get_model_response(
                role=ModelRole.POLICY_SYNTHESIS,
                prompt=generation_prompt,
                structured_output_class=RegoPolicy
            )
            
            if response["success"]:
                state.policy_draft = response["content"]
                logger.info(f"Policy generation completed for workflow {state.workflow_id}")
            else:
                state.add_error(f"Policy generation failed: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            state.add_error(f"Policy generation error: {str(e)}")
            logger.error(f"Policy generation failed for workflow {state.workflow_id}: {e}")
        
        return state
    
    async def _fidelity_assessment_node(self, state: WorkflowState) -> WorkflowState:
        """Assess constitutional fidelity of generated policy."""
        state.add_step("fidelity_assessment")
        
        try:
            if not state.policy_draft:
                state.add_error("No policy draft available for fidelity assessment")
                return state
            
            # Use specialized fidelity monitoring model
            assessment_prompt = self._build_fidelity_assessment_prompt(state)
            
            response = await self.multi_model_manager.get_model_response(
                role=ModelRole.FIDELITY_MONITORING,
                prompt=assessment_prompt,
                structured_output_class=ConstitutionalFidelityScore
            )
            
            if response["success"]:
                state.fidelity_assessment = response["content"]
                state.policy_draft.constitutional_fidelity = response["content"]
                logger.info(f"Fidelity assessment completed for workflow {state.workflow_id}")
            else:
                state.add_error(f"Fidelity assessment failed: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            state.add_error(f"Fidelity assessment error: {str(e)}")
            logger.error(f"Fidelity assessment failed for workflow {state.workflow_id}: {e}")
        
        return state
    
    async def _conflict_resolution_node(self, state: WorkflowState) -> WorkflowState:
        """Resolve conflicts detected in fidelity assessment."""
        state.add_step("conflict_resolution")
        
        try:
            if not state.fidelity_assessment or not state.policy_draft:
                state.add_error("Missing fidelity assessment or policy draft for conflict resolution")
                return state
            
            # Use specialized conflict resolution model
            resolution_prompt = self._build_conflict_resolution_prompt(state)
            
            response = await self.multi_model_manager.get_model_response(
                role=ModelRole.CONFLICT_RESOLUTION,
                prompt=resolution_prompt,
                structured_output_class=RegoPolicy
            )
            
            if response["success"]:
                state.policy_draft = response["content"]
                logger.info(f"Conflict resolution completed for workflow {state.workflow_id}")
            else:
                state.add_error(f"Conflict resolution failed: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            state.add_error(f"Conflict resolution error: {str(e)}")
            logger.error(f"Conflict resolution failed for workflow {state.workflow_id}: {e}")
        
        return state
    
    async def _final_validation_node(self, state: WorkflowState) -> WorkflowState:
        """Perform final validation of the synthesized policy."""
        state.add_step("final_validation")
        
        try:
            if not state.policy_draft or not state.fidelity_assessment:
                state.add_error("Missing policy draft or fidelity assessment for final validation")
                return state
            
            # Check if policy meets quality thresholds
            meets_fidelity = state.fidelity_assessment.meets_target_fidelity
            meets_target = state.fidelity_assessment.overall_score >= state.request.target_fidelity_score
            violation_count = len(state.fidelity_assessment.violations)
            
            if meets_fidelity and meets_target and violation_count <= state.request.max_violations:
                logger.info(f"Final validation passed for workflow {state.workflow_id}")
            else:
                state.add_error(
                    f"Final validation failed: fidelity={state.fidelity_assessment.overall_score:.3f}, "
                    f"target={state.request.target_fidelity_score:.3f}, violations={violation_count}"
                )
                
        except Exception as e:
            state.add_error(f"Final validation error: {str(e)}")
            logger.error(f"Final validation failed for workflow {state.workflow_id}: {e}")
        
        return state
    
    async def _error_handling_node(self, state: WorkflowState) -> WorkflowState:
        """Handle errors and determine recovery strategy."""
        state.add_step("error_handling")
        
        logger.warning(f"Error handling activated for workflow {state.workflow_id}: {state.errors}")
        
        # For now, just log the errors. In the future, we could implement
        # more sophisticated error recovery strategies here.
        
        return state

    # Conditional edge functions
    def _should_resolve_conflicts(self, state: WorkflowState) -> str:
        """Determine if conflicts need to be resolved."""
        if state.errors:
            return "error"

        if not state.fidelity_assessment:
            return "error"

        # Check if there are violations that need resolution
        if (len(state.fidelity_assessment.violations) > 0 and
            state.fidelity_assessment.overall_score < state.request.target_fidelity_score):
            return "resolve_conflicts"

        return "validate"

    def _should_retry_or_complete(self, state: WorkflowState) -> str:
        """Determine if workflow should retry, complete, or error."""
        if state.errors:
            if state.retry_count < state.max_retries:
                state.retry_count += 1
                return "retry"
            else:
                return "error"

        if (state.fidelity_assessment and
            state.fidelity_assessment.meets_target_fidelity and
            state.policy_draft):
            return "complete"

        if state.retry_count < state.max_retries:
            state.retry_count += 1
            return "retry"

        return "error"

    # Prompt building methods
    def _build_constitutional_analysis_prompt(self, request: PolicySynthesisRequest) -> str:
        """Build prompt for constitutional analysis."""
        return f"""
Analyze the following constitutional principles and context for policy synthesis:

Principle IDs: {request.principle_ids}
Context: {request.context}
Policy Type: {request.policy_type}

Please provide a comprehensive analysis that includes:
1. Relevant constitutional principles and their implications
2. Key requirements and constraints for the policy
3. Potential conflicts or tensions between principles
4. Recommendations for policy structure and approach

Analysis:
"""

    def _build_policy_generation_prompt(self, state: WorkflowState) -> str:
        """Build prompt for policy generation."""
        analysis = state.constitutional_analysis.get("analysis", "") if state.constitutional_analysis else ""

        return f"""
Generate a {state.request.policy_type} policy based on the following constitutional analysis:

{analysis}

Requirements:
- Target fidelity score: {state.request.target_fidelity_score}
- Maximum violations: {state.request.max_violations}
- Creativity level: {state.request.creativity_level}
- Strictness level: {state.request.strictness_level}
- Bias mitigation: {state.request.bias_mitigation_enabled}

Please generate a well-structured policy that adheres to the constitutional principles
and meets the specified requirements.

Policy:
"""

    def _build_fidelity_assessment_prompt(self, state: WorkflowState) -> str:
        """Build prompt for fidelity assessment."""
        policy_text = state.policy_draft.to_rego_string() if state.policy_draft else ""

        return f"""
Assess the constitutional fidelity of the following policy:

{policy_text}

Original request context: {state.request.context}
Target principles: {state.request.principle_ids}

Please provide a comprehensive fidelity assessment including:
1. Overall fidelity score (0-1)
2. Principle coverage score
3. Logical consistency score
4. Fairness score
5. Bias mitigation score
6. Detailed list of any violations found
7. Compliance level determination

Assessment:
"""


# Global instance for dependency injection
_policy_synthesis_workflow_instance = None


def get_policy_synthesis_workflow() -> PolicySynthesisWorkflow:
    """Get the global policy synthesis workflow instance."""
    global _policy_synthesis_workflow_instance
    if _policy_synthesis_workflow_instance is None:
        _policy_synthesis_workflow_instance = PolicySynthesisWorkflow()
    return _policy_synthesis_workflow_instance
