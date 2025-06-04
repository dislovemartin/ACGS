"""
Conflict Resolution Orchestrator for ACGS-PGP

This module orchestrates the complete intelligent conflict resolution process,
integrating detection, automated resolution, human escalation, and audit systems.

Key Features:
- Orchestrates complete conflict resolution workflow
- Integrates all conflict resolution components
- Manages 80% auto-resolution target
- Ensures 5-minute escalation target
- Provides comprehensive monitoring and reporting
- Maintains full audit trail with cryptographic integrity
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import ACConflictResolution, Principle
from ..schemas import ACConflictResolutionCreate, ACConflictResolutionUpdate
from .intelligent_conflict_detector import IntelligentConflictDetector, ConflictDetectionResult
from .automated_resolution_engine import AutomatedResolutionEngine, ResolutionResult, ResolutionStatus
from .human_escalation_system import HumanEscalationSystem, EscalationRequest, EscalationResponse
from .conflict_audit_system import ConflictAuditSystem, AuditLevel, PerformanceMetrics

logger = logging.getLogger(__name__)


class ConflictResolutionOrchestrator:
    """
    Main orchestrator for intelligent conflict resolution system.
    
    Coordinates detection, automated resolution, human escalation, and audit
    systems to achieve target performance metrics.
    """
    
    def __init__(self):
        """Initialize the orchestrator with all subsystems."""
        # Initialize subsystems
        self.detector = IntelligentConflictDetector()
        self.resolver = AutomatedResolutionEngine()
        self.escalator = HumanEscalationSystem()
        self.auditor = ConflictAuditSystem()
        
        # Performance targets
        self.auto_resolution_target = 0.80  # 80% auto-resolution target
        self.escalation_timeout = timedelta(minutes=5)  # 5-minute escalation target
        
        # System configuration
        self.max_resolution_attempts = 3
        self.monitoring_enabled = True
        
        logger.info("Conflict Resolution Orchestrator initialized")

    async def run_conflict_detection_scan(
        self,
        db: AsyncSession,
        principle_ids: Optional[List[int]] = None,
        user_id: Optional[int] = None
    ) -> List[ConflictDetectionResult]:
        """
        Run comprehensive conflict detection scan.
        
        Args:
            db: Database session
            principle_ids: Specific principles to scan (None for all)
            user_id: User initiating the scan
            
        Returns:
            List of detected conflicts
        """
        try:
            logger.info(f"Starting conflict detection scan for {len(principle_ids) if principle_ids else 'all'} principles")
            
            # Run detection
            detected_conflicts = await self.detector.detect_conflicts(
                db, principle_ids, real_time_monitoring=True
            )
            
            logger.info(f"Detected {len(detected_conflicts)} conflicts")
            
            # Create conflict resolution entries for each detected conflict
            created_conflicts = []
            for detection_result in detected_conflicts:
                try:
                    # Create conflict resolution entry
                    conflict_entry = await self.detector.create_conflict_resolution_entry(
                        db, detection_result, user_id
                    )
                    
                    # Log detection event
                    await self.auditor.log_conflict_detection(
                        db, conflict_entry, detection_result, user_id
                    )
                    
                    created_conflicts.append((conflict_entry, detection_result))
                    
                except Exception as e:
                    logger.error(f"Failed to create conflict entry: {e}")
                    continue
            
            # Automatically attempt resolution for high-confidence conflicts
            for conflict_entry, detection_result in created_conflicts:
                if detection_result.confidence_score >= 0.8:  # High confidence threshold
                    # Schedule automatic resolution
                    asyncio.create_task(
                        self.resolve_conflict_automatically(
                            db, conflict_entry.id, detection_result, user_id
                        )
                    )
            
            return detected_conflicts
            
        except Exception as e:
            logger.error(f"Conflict detection scan failed: {e}")
            raise

    async def resolve_conflict_automatically(
        self,
        db: AsyncSession,
        conflict_id: int,
        detection_result: Optional[ConflictDetectionResult] = None,
        user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[ResolutionResult], Optional[EscalationRequest]]:
        """
        Attempt automatic resolution of a conflict.
        
        Args:
            db: Database session
            conflict_id: ID of conflict to resolve
            detection_result: Original detection result (if available)
            user_id: User initiating resolution
            
        Returns:
            Tuple of (success, resolution_result, escalation_request)
        """
        try:
            logger.info(f"Starting automatic resolution for conflict {conflict_id}")
            
            # Get conflict from database
            from ..crud import get_ac_conflict_resolution
            conflict = await get_ac_conflict_resolution(db, conflict_id)
            
            if not conflict:
                logger.error(f"Conflict {conflict_id} not found")
                return False, None, None
            
            # Track resolution attempts
            attempts = 0
            resolution_result = None
            
            while attempts < self.max_resolution_attempts:
                attempts += 1
                logger.info(f"Resolution attempt {attempts} for conflict {conflict_id}")
                
                # Attempt automated resolution
                resolution_result = await self.resolver.resolve_conflict(
                    db, conflict, detection_result
                )
                
                # Log resolution attempt
                await self.auditor.log_resolution_attempt(
                    db, conflict, resolution_result, user_id
                )
                
                # Check if resolution was successful
                if resolution_result.success and resolution_result.validation_passed:
                    logger.info(f"Conflict {conflict_id} resolved successfully")
                    
                    # Update conflict status
                    await self._update_conflict_status(
                        db, conflict, "resolved", resolution_result, user_id
                    )
                    
                    return True, resolution_result, None
                
                # Check if escalation is required
                if resolution_result.escalation_required:
                    break
                
                # Update attempt count in conflict metadata
                await self._update_resolution_attempts(db, conflict, attempts)
            
            # If we reach here, automatic resolution failed
            logger.info(f"Automatic resolution failed for conflict {conflict_id}, evaluating escalation")
            
            # Evaluate escalation need
            escalation_request = await self.escalator.evaluate_escalation_need(
                db, conflict, resolution_result, detection_result
            )
            
            if escalation_request:
                # Trigger escalation
                escalation_response = await self.trigger_escalation(
                    db, escalation_request, user_id
                )
                
                # Update conflict status to escalated
                await self._update_conflict_status(
                    db, conflict, "escalated", resolution_result, user_id
                )
                
                return False, resolution_result, escalation_request
            else:
                # Mark as failed
                await self._update_conflict_status(
                    db, conflict, "failed", resolution_result, user_id
                )
                
                return False, resolution_result, None
            
        except Exception as e:
            logger.error(f"Automatic resolution failed for conflict {conflict_id}: {e}")
            
            # Create emergency escalation
            if conflict:
                emergency_escalation = await self.escalator._create_emergency_escalation(
                    db, conflict, f"Resolution error: {str(e)}"
                )
                await self.trigger_escalation(db, emergency_escalation, user_id)
            
            return False, None, None

    async def trigger_escalation(
        self,
        db: AsyncSession,
        escalation_request: EscalationRequest,
        user_id: Optional[int] = None
    ) -> EscalationResponse:
        """
        Trigger human escalation for a conflict.
        
        Args:
            db: Database session
            escalation_request: Escalation request details
            user_id: User triggering escalation
            
        Returns:
            EscalationResponse with escalation results
        """
        try:
            logger.info(f"Triggering escalation for conflict {escalation_request.conflict_id}")
            
            # Get conflict
            from ..crud import get_ac_conflict_resolution
            conflict = await get_ac_conflict_resolution(db, escalation_request.conflict_id)
            
            if not conflict:
                raise ValueError(f"Conflict {escalation_request.conflict_id} not found")
            
            # Find users with required roles
            assigned_users = await self._find_users_with_roles(
                db, escalation_request.required_roles
            )
            
            if not assigned_users:
                logger.warning(f"No users found with required roles: {escalation_request.required_roles}")
                assigned_users = await self._find_fallback_users(db)
            
            # Send notifications
            notification_results = await self._send_escalation_notifications(
                escalation_request, assigned_users
            )
            
            # Estimate response time based on escalation level and urgency
            estimated_response_time = self._estimate_response_time(escalation_request)
            
            # Create escalation response
            escalation_response = EscalationResponse(
                success=True,
                escalation_id=f"ESC_{escalation_request.conflict_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                assigned_users=[u.id for u in assigned_users],
                notification_results=notification_results,
                estimated_response_time=estimated_response_time,
                escalation_metadata={
                    "escalation_level": escalation_request.escalation_level.value,
                    "urgency_score": escalation_request.urgency_score,
                    "timeout_deadline": escalation_request.timeout_deadline.isoformat()
                }
            )
            
            # Log escalation event
            await self.auditor.log_escalation_event(
                db, conflict, escalation_request, escalation_response, user_id
            )
            
            # Track escalation in system
            self.escalator.active_escalations[escalation_request.conflict_id] = escalation_request
            
            logger.info(f"Escalation triggered successfully for conflict {escalation_request.conflict_id}")
            
            return escalation_response
            
        except Exception as e:
            logger.error(f"Escalation failed for conflict {escalation_request.conflict_id}: {e}")
            
            # Return failure response
            return EscalationResponse(
                success=False,
                escalation_id="",
                assigned_users=[],
                notification_results={},
                estimated_response_time=timedelta(hours=24),  # Default fallback
                escalation_metadata={"error": str(e)}
            )

    async def handle_human_intervention(
        self,
        db: AsyncSession,
        conflict_id: int,
        intervention_data: Dict[str, Any],
        user_id: int
    ) -> bool:
        """
        Handle human intervention in conflict resolution.
        
        Args:
            db: Database session
            conflict_id: ID of conflict being resolved
            intervention_data: Human decision and reasoning
            user_id: ID of user making intervention
            
        Returns:
            True if intervention was successful
        """
        try:
            logger.info(f"Processing human intervention for conflict {conflict_id}")
            
            # Get conflict
            from ..crud import get_ac_conflict_resolution, update_ac_conflict_resolution
            conflict = await get_ac_conflict_resolution(db, conflict_id)
            
            if not conflict:
                raise ValueError(f"Conflict {conflict_id} not found")
            
            # Log human intervention
            await self.auditor.log_human_intervention(
                db, conflict, intervention_data, user_id
            )
            
            # Update conflict based on human decision
            decision = intervention_data.get("decision")
            if decision == "resolve":
                # Mark as resolved with human intervention
                update_data = ACConflictResolutionUpdate(
                    status="resolved",
                    resolution_details={
                        **conflict.resolution_details,
                        "human_intervention": True,
                        "human_decision": intervention_data,
                        "resolved_by": user_id,
                        "resolved_at": datetime.now().isoformat()
                    }
                )
                
                await update_ac_conflict_resolution(db, conflict_id, update_data)
                
                # Log status change
                await self.auditor.log_status_change(
                    db, conflict, conflict.status, "resolved", user_id
                )
                
            elif decision == "escalate_further":
                # Create higher-level escalation
                # This would involve more senior roles or emergency procedures
                pass
                
            elif decision == "defer":
                # Defer resolution to later time
                update_data = ACConflictResolutionUpdate(
                    status="deferred",
                    resolution_details={
                        **conflict.resolution_details,
                        "deferred_reason": intervention_data.get("reasoning"),
                        "deferred_by": user_id,
                        "deferred_until": intervention_data.get("defer_until")
                    }
                )
                
                await update_ac_conflict_resolution(db, conflict_id, update_data)
            
            # Remove from active escalations
            if conflict_id in self.escalator.active_escalations:
                del self.escalator.active_escalations[conflict_id]
            
            logger.info(f"Human intervention processed successfully for conflict {conflict_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Human intervention failed for conflict {conflict_id}: {e}")
            return False

    async def get_system_performance_report(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Generate comprehensive system performance report.
        
        Args:
            db: Database session
            
        Returns:
            Performance report with metrics and analysis
        """
        try:
            # Collect current metrics
            current_metrics = await self.auditor.collect_performance_metrics(db)
            
            # Get detector performance
            detector_metrics = self.detector.get_performance_metrics()
            
            # Get resolver performance
            resolver_stats = self.resolver.resolution_stats
            
            # Get escalation performance
            escalation_stats = self.escalator.escalation_stats
            
            # Calculate target achievement
            auto_resolution_achievement = (
                current_metrics.auto_resolution_rate / (self.auto_resolution_target * 100)
            ) * 100
            
            escalation_time_achievement = 100.0  # This would be calculated from actual escalation times
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "performance_summary": {
                    "auto_resolution_rate": current_metrics.auto_resolution_rate,
                    "auto_resolution_target": self.auto_resolution_target * 100,
                    "target_achievement": auto_resolution_achievement,
                    "average_resolution_time": current_metrics.average_resolution_time,
                    "escalation_rate": current_metrics.escalation_rate,
                    "system_availability": current_metrics.system_availability
                },
                "detection_metrics": detector_metrics,
                "resolution_metrics": {
                    "total_attempts": resolver_stats["total_attempts"],
                    "successful_resolutions": resolver_stats["successful_resolutions"],
                    "auto_resolution_rate": resolver_stats["auto_resolution_rate"],
                    "average_processing_time": resolver_stats["average_processing_time"]
                },
                "escalation_metrics": {
                    "total_escalations": escalation_stats["total_escalations"],
                    "successful_escalations": escalation_stats["successful_escalations"],
                    "escalation_success_rate": escalation_stats["escalation_success_rate"],
                    "average_escalation_time": escalation_stats["average_escalation_time"]
                },
                "targets": {
                    "auto_resolution_target": self.auto_resolution_target * 100,
                    "escalation_timeout_minutes": self.escalation_timeout.total_seconds() / 60,
                    "detection_accuracy_target": 80.0
                },
                "recommendations": self._generate_performance_recommendations(current_metrics)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            raise
