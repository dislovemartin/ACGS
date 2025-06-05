"""
Real-time Constitutional Fidelity Monitoring WebSocket

This module provides WebSocket endpoints for real-time constitutional fidelity
monitoring with automated alerts, QEC-inspired error correction, and performance
dashboard integration.

Task 19: Real-time Constitutional Fidelity Monitoring
- ConstitutionalFidelityMonitor component for real-time score tracking
- Constitutional violation detection with alert thresholds
- QEC-inspired error correction workflows
- Performance dashboard integration
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
from pydantic import BaseModel

from src.backend.gs_service.app.workflows.multi_model_manager import get_multi_model_manager
from src.backend.gs_service.app.workflows.structured_output_models import (
    ConstitutionalFidelityScore,
    ConstitutionalComplianceLevel,
    ConstitutionalViolation
)

# Import violation detection services
from src.backend.gs_service.app.services.violation_detection_service import (
    ViolationDetectionService,
    ViolationType,
    ViolationSeverity,
    ViolationDetectionResult
)
from src.backend.gs_service.app.services.violation_escalation_service import (
    ViolationEscalationService,
    EscalationLevel,
    EscalationResult
)
from src.backend.gs_service.app.services.violation_audit_service import (
    ViolationAuditService,
    AuditEventType
)
from src.backend.gs_service.app.services.qec_error_correction_service import (
    QECErrorCorrectionService,
    ConflictDetectionResult,
    ErrorCorrectionResult,
    ErrorCorrectionStatus
)

logger = logging.getLogger(__name__)
router = APIRouter()


class FidelityAlert(BaseModel):
    """Alert for constitutional fidelity violations."""
    alert_id: str
    alert_type: str  # "violation", "threshold", "performance", "escalation"
    severity: str    # "green", "amber", "red", "critical"
    message: str
    fidelity_score: Optional[float] = None
    violations: int = 0
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class ViolationAlert(BaseModel):
    """Alert for specific constitutional violations."""
    alert_id: str
    violation_id: str
    violation_type: str  # ViolationType enum value
    severity: str        # ViolationSeverity enum value
    title: str
    description: str
    fidelity_score: Optional[float] = None
    distance_score: Optional[float] = None
    recommended_actions: List[str] = []
    escalated: bool = False
    escalation_level: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class ErrorCorrectionAlert(BaseModel):
    """Alert for QEC error correction activities."""
    alert_id: str
    correction_id: str
    alert_type: str  # "conflict_detected", "correction_applied", "escalation_required"
    status: str      # ErrorCorrectionStatus enum value
    conflict_type: Optional[str] = None  # ConflictType enum value
    resolution_strategy: Optional[str] = None  # ResolutionStrategy enum value
    title: str
    description: str
    response_time_seconds: float = 0.0
    fidelity_improvement: Optional[float] = None
    escalation_required: bool = False
    recommended_actions: List[str] = []
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class FidelityMonitoringSession:
    """Manages a WebSocket session for fidelity monitoring."""
    
    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.subscribed_workflows: Set[str] = set()
        self.alert_thresholds = {
            "green": 0.85,   # Above this is green
            "amber": 0.70,   # Between amber and green is amber
            "red": 0.55      # Below this is red
        }
        self.last_alert_time: Optional[datetime] = None
        self.alert_cooldown_seconds = 30  # Minimum time between alerts
        
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the WebSocket client."""
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
    
    async def send_fidelity_update(self, workflow_id: str, fidelity_score: ConstitutionalFidelityScore):
        """Send a fidelity score update to the client."""
        if workflow_id not in self.subscribed_workflows:
            return
        
        message = {
            "type": "fidelity_update",
            "workflow_id": workflow_id,
            "fidelity_score": {
                "overall_score": fidelity_score.overall_score,
                "principle_coverage_score": fidelity_score.principle_coverage_score,
                "logical_consistency_score": fidelity_score.logical_consistency_score,
                "fairness_score": fidelity_score.fairness_score,
                "bias_mitigation_score": fidelity_score.bias_mitigation_score,
                "compliance_level": fidelity_score.compliance_level,
                "violations_count": len(fidelity_score.violations),
                "evaluation_timestamp": fidelity_score.evaluation_timestamp.isoformat(),
                "evaluator_model": fidelity_score.evaluator_model
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_message(message)
        
        # Check if alert should be sent
        await self._check_and_send_alert(workflow_id, fidelity_score)
    
    async def send_performance_metrics(self, metrics: Dict[str, Any]):
        """Send performance metrics update to the client."""
        message = {
            "type": "performance_metrics",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_message(message)
    
    async def send_alert(self, alert: FidelityAlert):
        """Send an alert to the client."""
        # Check cooldown
        if (self.last_alert_time and 
            (datetime.utcnow() - self.last_alert_time).seconds < self.alert_cooldown_seconds):
            return
        
        message = {
            "type": "alert",
            "alert": {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "fidelity_score": alert.fidelity_score,
                "violations": alert.violations,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
        }
        
        await self.send_message(message)
        self.last_alert_time = datetime.utcnow()

    async def send_violation_alert(self, alert: ViolationAlert):
        """Send violation-specific alert to client."""
        message = {
            "type": "violation_alert",
            "alert": {
                "alert_id": alert.alert_id,
                "violation_id": alert.violation_id,
                "violation_type": alert.violation_type,
                "severity": alert.severity,
                "title": alert.title,
                "description": alert.description,
                "fidelity_score": alert.fidelity_score,
                "distance_score": alert.distance_score,
                "recommended_actions": alert.recommended_actions,
                "escalated": alert.escalated,
                "escalation_level": alert.escalation_level,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
        }

        await self.send_message(message)

    async def send_error_correction_alert(self, alert: ErrorCorrectionAlert):
        """Send error correction alert to client."""
        message = {
            "type": "error_correction_alert",
            "alert": {
                "alert_id": alert.alert_id,
                "correction_id": alert.correction_id,
                "alert_type": alert.alert_type,
                "status": alert.status,
                "conflict_type": alert.conflict_type,
                "resolution_strategy": alert.resolution_strategy,
                "title": alert.title,
                "description": alert.description,
                "response_time_seconds": alert.response_time_seconds,
                "fidelity_improvement": alert.fidelity_improvement,
                "escalation_required": alert.escalation_required,
                "recommended_actions": alert.recommended_actions,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
        }

        await self.send_message(message)

    async def send_escalation_notification(self, escalation_result: EscalationResult, violation_id: str):
        """Send escalation notification to client."""
        message = {
            "type": "escalation_notification",
            "escalation": {
                "escalation_id": escalation_result.escalation_id,
                "violation_id": violation_id,
                "escalated": escalation_result.escalated,
                "escalation_level": escalation_result.escalation_level.value,
                "assigned_to": escalation_result.assigned_to,
                "notification_sent": escalation_result.notification_sent,
                "response_time_target": escalation_result.response_time_target,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": escalation_result.escalation_metadata
            }
        }

        await self.send_message(message)
    
    async def _check_and_send_alert(self, workflow_id: str, fidelity_score: ConstitutionalFidelityScore):
        """Check if an alert should be sent based on fidelity score."""
        score = fidelity_score.overall_score
        violations_count = len(fidelity_score.violations)
        
        # Determine alert severity
        if score >= self.alert_thresholds["green"]:
            severity = "green"
        elif score >= self.alert_thresholds["amber"]:
            severity = "amber"
        else:
            severity = "red"
        
        # Only send alerts for amber and red conditions
        if severity in ["amber", "red"]:
            alert = FidelityAlert(
                alert_id=f"fidelity_{uuid.uuid4().hex[:8]}",
                alert_type="threshold",
                severity=severity,
                message=f"Constitutional fidelity score {score:.3f} below threshold for workflow {workflow_id}",
                fidelity_score=score,
                violations=violations_count,
                timestamp=datetime.utcnow(),
                metadata={
                    "workflow_id": workflow_id,
                    "compliance_level": fidelity_score.compliance_level,
                    "threshold": self.alert_thresholds[severity]
                }
            )
            
            await self.send_alert(alert)
    
    def subscribe_to_workflow(self, workflow_id: str):
        """Subscribe to updates for a specific workflow."""
        self.subscribed_workflows.add(workflow_id)
    
    def unsubscribe_from_workflow(self, workflow_id: str):
        """Unsubscribe from updates for a specific workflow."""
        self.subscribed_workflows.discard(workflow_id)


class FidelityMonitoringManager:
    """Manages all active fidelity monitoring sessions."""
    
    def __init__(self):
        self.active_sessions: Dict[str, FidelityMonitoringSession] = {}
        self.workflow_subscribers: Dict[str, Set[str]] = {}  # workflow_id -> session_ids
        
    def add_session(self, session: FidelityMonitoringSession):
        """Add a new monitoring session."""
        self.active_sessions[session.session_id] = session
        logger.info(f"Added fidelity monitoring session: {session.session_id}")
    
    def remove_session(self, session_id: str):
        """Remove a monitoring session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Remove from workflow subscriptions
            for workflow_id in session.subscribed_workflows:
                if workflow_id in self.workflow_subscribers:
                    self.workflow_subscribers[workflow_id].discard(session_id)
                    if not self.workflow_subscribers[workflow_id]:
                        del self.workflow_subscribers[workflow_id]
            
            del self.active_sessions[session_id]
            logger.info(f"Removed fidelity monitoring session: {session_id}")
    
    def subscribe_session_to_workflow(self, session_id: str, workflow_id: str):
        """Subscribe a session to workflow updates."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.subscribe_to_workflow(workflow_id)
            
            if workflow_id not in self.workflow_subscribers:
                self.workflow_subscribers[workflow_id] = set()
            self.workflow_subscribers[workflow_id].add(session_id)
    
    async def broadcast_fidelity_update(self, workflow_id: str, fidelity_score: ConstitutionalFidelityScore):
        """Broadcast fidelity update to all subscribed sessions."""
        if workflow_id in self.workflow_subscribers:
            for session_id in self.workflow_subscribers[workflow_id]:
                if session_id in self.active_sessions:
                    session = self.active_sessions[session_id]
                    await session.send_fidelity_update(workflow_id, fidelity_score)
    
    async def broadcast_performance_metrics(self, metrics: Dict[str, Any]):
        """Broadcast performance metrics to all active sessions."""
        for session in self.active_sessions.values():
            await session.send_performance_metrics(metrics)
    
    async def broadcast_alert(self, alert: FidelityAlert):
        """Broadcast alert to all active sessions."""
        for session in self.active_sessions.values():
            await session.send_alert(alert)

    async def broadcast_violation_alert(self, alert: ViolationAlert):
        """Broadcast violation alert to all active sessions."""
        for session in self.active_sessions.values():
            await session.send_violation_alert(alert)

    async def broadcast_escalation_notification(self, escalation_result: EscalationResult, violation_id: str):
        """Broadcast escalation notification to all active sessions."""
        for session in self.active_sessions.values():
            await session.send_escalation_notification(escalation_result, violation_id)

    async def broadcast_error_correction_alert(self, alert: ErrorCorrectionAlert):
        """Broadcast error correction alert to all active sessions."""
        for session in self.active_sessions.values():
            await session.send_error_correction_alert(alert)


# Global monitoring manager
monitoring_manager = FidelityMonitoringManager()


@router.websocket("/ws/fidelity-monitor")
async def fidelity_monitoring_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time constitutional fidelity monitoring.
    
    Provides real-time updates for:
    - Constitutional fidelity scores
    - Violation detection and alerts
    - Performance metrics
    - System health status
    """
    await websocket.accept()
    
    session_id = f"fidelity_monitor_{uuid.uuid4().hex[:8]}"
    session = FidelityMonitoringSession(websocket, session_id)
    monitoring_manager.add_session(session)
    
    try:
        # Send initial connection confirmation
        await session.send_message({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "capabilities": [
                "fidelity_updates",
                "performance_metrics",
                "alerts",
                "workflow_subscription",
                "error_correction_monitoring",
                "conflict_detection",
                "automatic_resolution"
            ]
        })
        
        # Handle incoming messages
        while True:
            try:
                message = await websocket.receive_text()
                await handle_websocket_message(session, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {session_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await session.send_message({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    finally:
        monitoring_manager.remove_session(session_id)


async def handle_websocket_message(session: FidelityMonitoringSession, message: str):
    """Handle incoming WebSocket messages."""
    try:
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "subscribe_workflow":
            workflow_id = data.get("workflow_id")
            if workflow_id:
                monitoring_manager.subscribe_session_to_workflow(session.session_id, workflow_id)
                await session.send_message({
                    "type": "subscription_confirmed",
                    "workflow_id": workflow_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        elif message_type == "unsubscribe_workflow":
            workflow_id = data.get("workflow_id")
            if workflow_id:
                session.unsubscribe_from_workflow(workflow_id)
                await session.send_message({
                    "type": "unsubscription_confirmed",
                    "workflow_id": workflow_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        elif message_type == "get_performance_metrics":
            # Send current performance metrics
            manager = get_multi_model_manager()
            metrics = manager.get_performance_metrics()
            await session.send_performance_metrics(metrics)

        elif message_type == "get_fidelity_status":
            # Send comprehensive fidelity status
            try:
                from alphaevolve_gs_engine.services.qec_enhancement import ConstitutionalFidelityMonitor

                # Initialize fidelity monitor if not already done
                if not hasattr(session, 'fidelity_monitor'):
                    session.fidelity_monitor = ConstitutionalFidelityMonitor()

                # Get current fidelity status
                current_fidelity = session.fidelity_monitor.get_current_fidelity()

                if current_fidelity:
                    await session.send_message({
                        "type": "fidelity_status",
                        "current_fidelity_score": current_fidelity.composite_score,
                        "alert_level": "green" if current_fidelity.composite_score >= 0.85 else
                                     "amber" if current_fidelity.composite_score >= 0.70 else "red",
                        "violation_count": len(session.fidelity_monitor.get_active_alerts()),
                        "fidelity_components": {
                            "principle_coverage": current_fidelity.principle_coverage,
                            "synthesis_success": current_fidelity.synthesis_success,
                            "enforcement_reliability": current_fidelity.enforcement_reliability,
                            "adaptation_speed": current_fidelity.adaptation_speed,
                            "stakeholder_satisfaction": current_fidelity.stakeholder_satisfaction,
                            "appeal_frequency": current_fidelity.appeal_frequency
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    await session.send_message({
                        "type": "fidelity_status",
                        "current_fidelity_score": None,
                        "alert_level": "unknown",
                        "violation_count": 0,
                        "message": "No fidelity data available",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error getting fidelity status: {e}")
                await session.send_message({
                    "type": "error",
                    "message": f"Failed to get fidelity status: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })

        elif message_type == "start_error_correction":
            # Start error correction workflow
            try:
                principle_ids = data.get("principle_ids", [])
                policy_ids = data.get("policy_ids", [])
                context_data = data.get("context_data", {})

                # Initialize QEC service if not already done
                if not hasattr(session, 'qec_service'):
                    session.qec_service = QECErrorCorrectionService()

                # Send acknowledgment
                await session.send_message({
                    "type": "error_correction_started",
                    "workflow_id": f"qec_workflow_{uuid.uuid4().hex[:8]}",
                    "message": "Error correction workflow initiated",
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Note: Actual workflow execution would be handled by the API endpoint
                # This is just for real-time monitoring acknowledgment

            except Exception as e:
                logger.error(f"Error starting error correction: {e}")
                await session.send_message({
                    "type": "error",
                    "message": f"Failed to start error correction: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })

        elif message_type == "get_error_correction_status":
            # Get current error correction performance
            try:
                if not hasattr(session, 'qec_service'):
                    session.qec_service = QECErrorCorrectionService()

                performance_summary = session.qec_service.get_performance_summary()

                await session.send_message({
                    "type": "error_correction_status",
                    "performance_summary": performance_summary,
                    "timestamp": datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.error(f"Error getting error correction status: {e}")
                await session.send_message({
                    "type": "error",
                    "message": f"Failed to get error correction status: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })

        elif message_type == "ping":
            await session.send_message({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        else:
            await session.send_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    except json.JSONDecodeError:
        await session.send_message({
            "type": "error",
            "message": "Invalid JSON message",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await session.send_message({
            "type": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })


# Background task for periodic performance monitoring
async def start_performance_monitoring():
    """Start background task for periodic performance monitoring."""
    while True:
        try:
            manager = get_multi_model_manager()
            metrics = manager.get_performance_metrics()
            
            # Broadcast metrics to all connected clients
            await monitoring_manager.broadcast_performance_metrics(metrics)
            
            # Check for performance alerts
            overall_metrics = metrics.get("overall", {})
            reliability_target_met = overall_metrics.get("reliability_target_met", False)
            
            if not reliability_target_met:
                alert = FidelityAlert(
                    alert_id=f"performance_{uuid.uuid4().hex[:8]}",
                    alert_type="performance",
                    severity="red",
                    message="System reliability target not being met",
                    fidelity_score=overall_metrics.get("overall_success_rate", 0.0),
                    violations=0,
                    timestamp=datetime.utcnow(),
                    metadata=overall_metrics
                )
                await monitoring_manager.broadcast_alert(alert)
            
            # Wait 30 seconds before next check
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
            await asyncio.sleep(60)  # Wait longer on error


# Function to be called from workflow to broadcast fidelity updates
async def broadcast_fidelity_update(workflow_id: str, fidelity_score: ConstitutionalFidelityScore):
    """Broadcast fidelity update to monitoring clients."""
    await monitoring_manager.broadcast_fidelity_update(workflow_id, fidelity_score)
