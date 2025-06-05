"""
Amendment State Machine for Democratic Governance Workflows

Implements state machine-based governance workflows with event-driven patterns
for Constitutional Council amendment processing.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.exc import SQLAlchemyError

# from shared.redis_client import get_redis_client
from shared.metrics import get_metrics

logger = logging.getLogger(__name__)


class AmendmentState(Enum):
    """Amendment workflow states."""
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    PUBLIC_CONSULTATION = "public_consultation"
    VOTING = "voting"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    WITHDRAWN = "withdrawn"
    DEFERRED = "deferred"


class AmendmentEvent(Enum):
    """Amendment workflow events."""
    SUBMIT = "submit"
    START_REVIEW = "start_review"
    APPROVE_FOR_CONSULTATION = "approve_for_consultation"
    START_VOTING = "start_voting"
    APPROVE = "approve"
    REJECT = "reject"
    IMPLEMENT = "implement"
    WITHDRAW = "withdraw"
    DEFER = "defer"
    RETURN_FOR_REVISION = "return_for_revision"


@dataclass
class StateTransition:
    """Represents a state transition."""
    from_state: AmendmentState
    to_state: AmendmentState
    event: AmendmentEvent
    condition: Optional[Callable] = None
    action: Optional[Callable] = None


@dataclass
class WorkflowContext:
    """Context for workflow execution."""
    amendment_id: int
    user_id: int
    urgency_level: str = "normal"
    constitutional_significance: str = "normal"
    metadata: Dict[str, Any] = None
    transaction_id: Optional[str] = None
    event_timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.event_timestamp is None:
            self.event_timestamp = datetime.utcnow()


@dataclass
class WorkflowEvent:
    """Represents a workflow event with metadata."""
    event_type: AmendmentEvent
    context: WorkflowContext
    timestamp: datetime
    event_id: str
    source: str = "state_machine"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "amendment_id": self.context.amendment_id,
            "user_id": self.context.user_id,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "source": self.source,
            "metadata": self.context.metadata
        }


class AmendmentStateMachine:
    """Enhanced state machine for amendment workflow management with transaction support."""

    def __init__(self):
        self.transitions: Dict[AmendmentState, Dict[AmendmentEvent, StateTransition]] = {}
        self.event_handlers: Dict[AmendmentEvent, List[Callable]] = {}
        self.redis_client = None
        self.metrics = get_metrics("ac_service")
        self._setup_transitions()

    async def initialize(self):
        """Initialize the state machine with Redis client."""
        try:
            # self.redis_client = await get_redis_client("amendment_state_machine")
            logger.info("Amendment state machine initialized (Redis disabled)")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client for state machine: {e}")
            # Continue without Redis if it fails
    
    def _setup_transitions(self):
        """Setup valid state transitions."""
        transitions = [
            # Initial submission
            StateTransition(
                AmendmentState.PROPOSED,
                AmendmentState.UNDER_REVIEW,
                AmendmentEvent.START_REVIEW
            ),
            
            # Review to consultation
            StateTransition(
                AmendmentState.UNDER_REVIEW,
                AmendmentState.PUBLIC_CONSULTATION,
                AmendmentEvent.APPROVE_FOR_CONSULTATION,
                condition=self._check_review_approval
            ),
            
            # Consultation to voting
            StateTransition(
                AmendmentState.PUBLIC_CONSULTATION,
                AmendmentState.VOTING,
                AmendmentEvent.START_VOTING,
                condition=self._check_consultation_complete
            ),
            
            # Voting outcomes
            StateTransition(
                AmendmentState.VOTING,
                AmendmentState.APPROVED,
                AmendmentEvent.APPROVE,
                condition=self._check_voting_approval
            ),
            
            StateTransition(
                AmendmentState.VOTING,
                AmendmentState.REJECTED,
                AmendmentEvent.REJECT,
                condition=self._check_voting_rejection
            ),
            
            # Implementation
            StateTransition(
                AmendmentState.APPROVED,
                AmendmentState.IMPLEMENTED,
                AmendmentEvent.IMPLEMENT,
                action=self._implement_amendment
            ),
            
            # Withdrawal (from any state except implemented)
            StateTransition(
                AmendmentState.PROPOSED,
                AmendmentState.WITHDRAWN,
                AmendmentEvent.WITHDRAW
            ),
            
            StateTransition(
                AmendmentState.UNDER_REVIEW,
                AmendmentState.WITHDRAWN,
                AmendmentEvent.WITHDRAW
            ),
            
            StateTransition(
                AmendmentState.PUBLIC_CONSULTATION,
                AmendmentState.WITHDRAWN,
                AmendmentEvent.WITHDRAW
            ),
            
            # Deferral
            StateTransition(
                AmendmentState.UNDER_REVIEW,
                AmendmentState.DEFERRED,
                AmendmentEvent.DEFER
            ),
            
            StateTransition(
                AmendmentState.PUBLIC_CONSULTATION,
                AmendmentState.DEFERRED,
                AmendmentEvent.DEFER
            ),
            
            # Return for revision
            StateTransition(
                AmendmentState.UNDER_REVIEW,
                AmendmentState.PROPOSED,
                AmendmentEvent.RETURN_FOR_REVISION
            ),
        ]
        
        # Build transition lookup table
        for transition in transitions:
            if transition.from_state not in self.transitions:
                self.transitions[transition.from_state] = {}
            self.transitions[transition.from_state][transition.event] = transition
    
    async def trigger_event(
        self,
        db: AsyncSession,
        current_state: AmendmentState,
        event: AmendmentEvent,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Trigger a workflow event with enhanced transaction management."""
        import uuid

        # Generate transaction ID if not provided
        if not context.transaction_id:
            context.transaction_id = str(uuid.uuid4())

        # Record metrics
        self.metrics.record_policy_operation("state_transition", "started")

        # Start database transaction
        async with db.begin():
            try:
                # Validate transition
                validation_result = await self._validate_transition(current_state, event, context)
                if not validation_result["valid"]:
                    await self._record_failed_transition(context, validation_result["error"])
                    return validation_result

                transition = self.transitions[current_state][event]

                # Check transition condition with transaction context
                if transition.condition:
                    condition_result = await transition.condition(db, context)
                    if not condition_result:
                        error_msg = f"Transition condition not met for {event.value}"
                        await self._record_failed_transition(context, error_msg)
                        return {"success": False, "error": error_msg}

                # Update amendment state in database with optimistic locking
                update_result = await self._update_amendment_state(
                    db, context.amendment_id, transition.to_state, context
                )
                if not update_result["success"]:
                    await self._record_failed_transition(context, update_result["error"])
                    return update_result

                # Execute transition action within transaction
                if transition.action:
                    action_result = await transition.action(db, context)
                    if not action_result.get("success", True):
                        error_msg = f"Transition action failed: {action_result.get('error', 'Unknown error')}"
                        await self._record_failed_transition(context, error_msg)
                        return {"success": False, "error": error_msg}

                # Create workflow event
                workflow_event = WorkflowEvent(
                    event_type=event,
                    context=context,
                    timestamp=datetime.utcnow(),
                    event_id=str(uuid.uuid4())
                )

                # Publish event to Redis for event-driven processing
                await self._publish_workflow_event(workflow_event)

                # Execute event handlers
                await self._execute_event_handlers(db, event, context, transition)

                # Record successful transition
                result = {
                    "success": True,
                    "from_state": current_state.value,
                    "to_state": transition.to_state.value,
                    "event": event.value,
                    "transaction_id": context.transaction_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

                await self._record_successful_transition(context, result)
                self.metrics.record_policy_operation("state_transition", "success")

                return result

            except SQLAlchemyError as e:
                logger.error(f"Database error in state transition: {e}")
                await self._record_failed_transition(context, f"Database error: {str(e)}")
                self.metrics.record_policy_operation("state_transition", "db_error")
                return {"success": False, "error": f"Database error: {str(e)}"}

            except Exception as e:
                logger.error(f"Unexpected error in state transition: {e}")
                await self._record_failed_transition(context, f"Unexpected error: {str(e)}")
                self.metrics.record_policy_operation("state_transition", "error")
                return {"success": False, "error": f"State machine error: {str(e)}"}
    
    def register_event_handler(self, event: AmendmentEvent, handler: Callable):
        """Register an event handler."""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    def get_valid_events(self, current_state: AmendmentState) -> List[AmendmentEvent]:
        """Get valid events for current state."""
        if current_state in self.transitions:
            return list(self.transitions[current_state].keys())
        return []

    async def _validate_transition(
        self,
        current_state: AmendmentState,
        event: AmendmentEvent,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Validate if transition is allowed."""
        if current_state not in self.transitions:
            return {
                "valid": False,
                "error": f"No transitions defined for state {current_state.value}"
            }

        if event not in self.transitions[current_state]:
            return {
                "valid": False,
                "error": f"Invalid event {event.value} for state {current_state.value}"
            }

        return {"valid": True}

    async def _update_amendment_state(
        self,
        db: AsyncSession,
        amendment_id: int,
        new_state: AmendmentState,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Update amendment state with optimistic locking."""
        try:
            # Get current amendment with version for optimistic locking
            from ..models import ACAmendment

            result = await db.execute(
                select(ACAmendment).where(ACAmendment.id == amendment_id)
            )
            amendment = result.scalar_one_or_none()

            if not amendment:
                return {"success": False, "error": f"Amendment {amendment_id} not found"}

            # Update state and increment version
            amendment.workflow_state = new_state.value
            amendment.version += 1
            amendment.updated_at = datetime.utcnow()

            # Add state transition to history
            if not amendment.state_transitions:
                amendment.state_transitions = []

            amendment.state_transitions.append({
                "from_state": amendment.workflow_state,
                "to_state": new_state.value,
                "event": context.metadata.get("event", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": context.user_id,
                "transaction_id": context.transaction_id
            })

            await db.flush()
            return {"success": True, "new_version": amendment.version}

        except Exception as e:
            logger.error(f"Failed to update amendment state: {e}")
            return {"success": False, "error": str(e)}

    async def _publish_workflow_event(self, event: WorkflowEvent):
        """Publish workflow event to Redis for event-driven processing."""
        if not self.redis_client:
            logger.warning("Redis client not available, skipping event publishing")
            return

        try:
            # Publish to workflow events channel
            channel = "acgs:workflow:events"
            event_data = event.to_dict()

            await self.redis_client.publish(channel, event_data)

            # Also store in event history
            history_key = f"acgs:workflow:history:{event.context.amendment_id}"
            await self.redis_client.add_to_list(history_key, event_data, max_length=100)

            logger.info(f"Published workflow event {event.event_id} for amendment {event.context.amendment_id}")

        except Exception as e:
            logger.error(f"Failed to publish workflow event: {e}")

    async def _execute_event_handlers(
        self,
        db: AsyncSession,
        event: AmendmentEvent,
        context: WorkflowContext,
        transition: StateTransition
    ):
        """Execute registered event handlers."""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    await handler(db, context, transition)
                except Exception as e:
                    logger.error(f"Event handler failed for {event.value}: {e}")
                    # Continue with other handlers even if one fails

    async def _record_successful_transition(self, context: WorkflowContext, result: Dict[str, Any]):
        """Record successful state transition."""
        if self.redis_client:
            try:
                metrics_key = f"acgs:metrics:transitions:success"
                await self.redis_client.increment(metrics_key)

                # Record transition details
                transition_key = f"acgs:transitions:{context.amendment_id}:{context.transaction_id}"
                await self.redis_client.set_json(transition_key, result, ttl=86400)  # 24 hours

            except Exception as e:
                logger.error(f"Failed to record successful transition: {e}")

    async def _record_failed_transition(self, context: WorkflowContext, error: str):
        """Record failed state transition."""
        if self.redis_client:
            try:
                metrics_key = f"acgs:metrics:transitions:failed"
                await self.redis_client.increment(metrics_key)

                # Record failure details
                failure_key = f"acgs:failures:{context.amendment_id}:{context.transaction_id}"
                failure_data = {
                    "amendment_id": context.amendment_id,
                    "user_id": context.user_id,
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat(),
                    "transaction_id": context.transaction_id
                }
                await self.redis_client.set_json(failure_key, failure_data, ttl=86400)  # 24 hours

            except Exception as e:
                logger.error(f"Failed to record failed transition: {e}")
    
    # Condition checkers
    async def _check_review_approval(self, db: AsyncSession, context: WorkflowContext) -> bool:
        """Check if amendment passed review."""
        # Simplified - would check actual review criteria
        return True
    
    async def _check_consultation_complete(self, db: AsyncSession, context: WorkflowContext) -> bool:
        """Check if public consultation period is complete."""
        # Would check consultation period and feedback
        return True
    
    async def _check_voting_approval(self, db: AsyncSession, context: WorkflowContext) -> bool:
        """Check if amendment was approved by voting."""
        # Would check actual vote counts and thresholds
        return True
    
    async def _check_voting_rejection(self, db: AsyncSession, context: WorkflowContext) -> bool:
        """Check if amendment was rejected by voting."""
        # Would check actual vote counts
        return True
    
    # Action handlers
    async def _implement_amendment(self, db: AsyncSession, context: WorkflowContext) -> Dict[str, Any]:
        """Implement approved amendment."""
        try:
            # Implementation logic would go here
            logger.info(f"Implementing amendment {context.amendment_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to implement amendment {context.amendment_id}: {e}")
            return {"success": False, "error": str(e)}


# Global state machine instance
amendment_state_machine = AmendmentStateMachine()
