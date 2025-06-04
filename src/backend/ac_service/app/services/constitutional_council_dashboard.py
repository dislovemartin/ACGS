"""
Constitutional Council Real-time Dashboard Service

This module provides real-time dashboard functionality for monitoring
Constitutional Council workflows, amendment processing, and stakeholder engagement.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app import crud
from app.models import ACAmendment, ACAmendmentVote, ACAmendmentComment, User
from shared.constitutional_metrics import get_constitutional_metrics
from shared.metrics import get_metrics

logger = logging.getLogger(__name__)


class ConstitutionalCouncilDashboard:
    """
    Real-time dashboard for Constitutional Council operations.
    
    Provides WebSocket-based real-time updates for amendment workflows,
    stakeholder engagement, and voting progress monitoring.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.dashboard_active = False
        self.update_interval = 5  # seconds
        
        # Metrics collectors
        self.metrics = get_metrics("constitutional_council_dashboard")
        self.constitutional_metrics = get_constitutional_metrics("constitutional_council_dashboard")
        
        # Dashboard state tracking
        self.last_update = datetime.utcnow()
        self.active_amendments: Set[int] = set()
        self.stakeholder_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Constitutional Council Dashboard initialized")

    async def start_dashboard(self) -> None:
        """Start the real-time dashboard updates."""
        if self.dashboard_active:
            logger.warning("Dashboard already active")
            return

        self.dashboard_active = True
        logger.info("Started Constitutional Council real-time dashboard")

        # Start dashboard update loop
        asyncio.create_task(self._dashboard_update_loop())

    async def stop_dashboard(self) -> None:
        """Stop the dashboard and close all connections."""
        self.dashboard_active = False

        # Close all websocket connections
        for connection_id, websocket in list(self.websocket_connections.items()):
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket {connection_id}: {e}")

        self.websocket_connections.clear()
        logger.info("Stopped Constitutional Council dashboard")

    async def add_websocket_connection(self, websocket: WebSocket, user_id: Optional[int] = None) -> str:
        """Add a new WebSocket connection and return connection ID."""
        await websocket.accept()
        
        connection_id = str(uuid4())
        self.websocket_connections[connection_id] = websocket
        
        # Track stakeholder session
        if user_id:
            self.stakeholder_sessions[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
        
        # Update WebSocket connections metric
        self.metrics.update_websocket_connections("constitutional_council", len(self.websocket_connections))
        
        logger.info(f"Added WebSocket connection {connection_id}, total: {len(self.websocket_connections)}")

        # Send initial dashboard data
        try:
            initial_data = await self.get_dashboard_data()
            await websocket.send_text(json.dumps(initial_data))
        except Exception as e:
            logger.error(f"Error sending initial dashboard data: {e}")

        return connection_id

    async def remove_websocket_connection(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        if connection_id in self.websocket_connections:
            del self.websocket_connections[connection_id]
            
        if connection_id in self.stakeholder_sessions:
            del self.stakeholder_sessions[connection_id]
            
        # Update WebSocket connections metric
        self.metrics.update_websocket_connections("constitutional_council", len(self.websocket_connections))
        
        logger.info(f"Removed WebSocket connection {connection_id}, total: {len(self.websocket_connections)}")

    async def _dashboard_update_loop(self) -> None:
        """Main dashboard update loop for real-time data streaming."""
        while self.dashboard_active:
            try:
                if self.websocket_connections:
                    # Get current dashboard data
                    dashboard_data = await self.get_dashboard_data()
                    
                    # Broadcast to all connected clients
                    await self._broadcast_to_websockets(dashboard_data)
                    
                    # Update last update timestamp
                    self.last_update = datetime.utcnow()

                await asyncio.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(5)

    async def _broadcast_to_websockets(self, data: Dict[str, Any]) -> None:
        """Broadcast data to all connected WebSocket clients."""
        if not self.websocket_connections:
            return

        message = json.dumps(data)
        disconnected_clients = []

        for connection_id, websocket in self.websocket_connections.items():
            try:
                await websocket.send_text(message)
                
                # Update last activity for stakeholder sessions
                if connection_id in self.stakeholder_sessions:
                    self.stakeholder_sessions[connection_id]["last_activity"] = datetime.utcnow()
                    
            except WebSocketDisconnect:
                disconnected_clients.append(connection_id)
            except Exception as e:
                logger.error(f"Error sending WebSocket message to {connection_id}: {e}")
                disconnected_clients.append(connection_id)

        # Remove disconnected clients
        for connection_id in disconnected_clients:
            await self.remove_websocket_connection(connection_id)

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive real-time dashboard data."""
        try:
            # Get amendment workflow metrics
            amendment_metrics = await self._get_amendment_workflow_metrics()
            
            # Get stakeholder engagement metrics
            stakeholder_metrics = await self._get_stakeholder_engagement_metrics()
            
            # Get voting progress data
            voting_progress = await self._get_voting_progress_data()
            
            # Get system performance metrics
            performance_metrics = await self._get_performance_metrics()
            
            # Get real-time alerts
            alerts = await self._get_real_time_alerts()

            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "amendment_workflows": amendment_metrics,
                "stakeholder_engagement": stakeholder_metrics,
                "voting_progress": voting_progress,
                "performance_metrics": performance_metrics,
                "alerts": alerts,
                "active_connections": len(self.websocket_connections),
                "dashboard_status": "active" if self.dashboard_active else "inactive"
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Failed to generate dashboard data: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "dashboard_status": "error"
            }

    async def _get_amendment_workflow_metrics(self) -> Dict[str, Any]:
        """Get real-time amendment workflow metrics."""
        try:
            # Get amendments by status
            amendments_query = select(
                ACAmendment.status,
                func.count(ACAmendment.id).label('count')
            ).group_by(ACAmendment.status)
            
            result = await self.db.execute(amendments_query)
            status_counts = {row.status: row.count for row in result}

            # Get recent amendments (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_amendments_query = select(ACAmendment).where(
                ACAmendment.created_at >= recent_cutoff
            ).order_by(ACAmendment.created_at.desc()).limit(10)
            
            recent_result = await self.db.execute(recent_amendments_query)
            recent_amendments = recent_result.scalars().all()

            # Calculate workflow efficiency metrics
            total_amendments = sum(status_counts.values())
            completed_amendments = status_counts.get('approved', 0) + status_counts.get('rejected', 0)
            completion_rate = completed_amendments / total_amendments if total_amendments > 0 else 0

            return {
                "status_distribution": status_counts,
                "recent_amendments": [
                    {
                        "id": amendment.id,
                        "title": amendment.proposed_changes.get("title", "Untitled") if amendment.proposed_changes else "Untitled",
                        "status": amendment.status,
                        "created_at": amendment.created_at.isoformat(),
                        "principle_id": amendment.principle_id
                    }
                    for amendment in recent_amendments
                ],
                "workflow_efficiency": {
                    "total_amendments": total_amendments,
                    "completion_rate": completion_rate,
                    "active_workflows": status_counts.get('under_review', 0) + status_counts.get('voting', 0),
                    "pending_amendments": status_counts.get('proposed', 0)
                }
            }

        except Exception as e:
            logger.error(f"Failed to get amendment workflow metrics: {e}")
            return {"error": str(e)}

    async def _get_stakeholder_engagement_metrics(self) -> Dict[str, Any]:
        """Get real-time stakeholder engagement metrics."""
        try:
            # Get active stakeholder sessions
            active_sessions = len(self.stakeholder_sessions)
            
            # Calculate session duration statistics
            session_durations = []
            current_time = datetime.utcnow()
            
            for session_data in self.stakeholder_sessions.values():
                duration = (current_time - session_data["connected_at"]).total_seconds() / 60  # minutes
                session_durations.append(duration)
            
            avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0

            # Get recent comments and votes (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            
            recent_comments_query = select(func.count(ACAmendmentComment.id)).where(
                ACAmendmentComment.created_at >= recent_cutoff
            )
            recent_votes_query = select(func.count(ACAmendmentVote.id)).where(
                ACAmendmentVote.created_at >= recent_cutoff
            )
            
            comments_result = await self.db.execute(recent_comments_query)
            votes_result = await self.db.execute(recent_votes_query)
            
            recent_comments = comments_result.scalar() or 0
            recent_votes = votes_result.scalar() or 0

            return {
                "active_sessions": active_sessions,
                "average_session_duration_minutes": round(avg_session_duration, 2),
                "recent_activity": {
                    "comments_24h": recent_comments,
                    "votes_24h": recent_votes,
                    "engagement_rate": (recent_comments + recent_votes) / max(active_sessions, 1)
                },
                "real_time_participation": {
                    "connected_stakeholders": active_sessions,
                    "active_discussions": len([s for s in self.stakeholder_sessions.values() 
                                             if (current_time - s["last_activity"]).total_seconds() < 300])  # Active in last 5 minutes
                }
            }

        except Exception as e:
            logger.error(f"Failed to get stakeholder engagement metrics: {e}")
            return {"error": str(e)}

    async def _get_voting_progress_data(self) -> Dict[str, Any]:
        """Get real-time voting progress data."""
        try:
            # Get amendments currently in voting phase
            voting_amendments_query = select(ACAmendment).where(
                ACAmendment.status == 'voting'
            )

            voting_result = await self.db.execute(voting_amendments_query)
            voting_amendments = voting_result.scalars().all()

            voting_progress = []
            for amendment in voting_amendments:
                # Get votes for this amendment
                votes_query = select(
                    ACAmendmentVote.vote_type,
                    func.count(ACAmendmentVote.id).label('count')
                ).where(
                    ACAmendmentVote.amendment_id == amendment.id
                ).group_by(ACAmendmentVote.vote_type)

                votes_result = await self.db.execute(votes_query)
                vote_counts = {row.vote_type: row.count for row in votes_result}

                total_votes = sum(vote_counts.values())
                votes_for = vote_counts.get('for', 0)
                votes_against = vote_counts.get('against', 0)
                votes_abstain = vote_counts.get('abstain', 0)

                approval_rate = votes_for / total_votes if total_votes > 0 else 0

                voting_progress.append({
                    "amendment_id": amendment.id,
                    "title": amendment.proposed_changes.get("title", "Untitled") if amendment.proposed_changes else "Untitled",
                    "vote_counts": {
                        "for": votes_for,
                        "against": votes_against,
                        "abstain": votes_abstain,
                        "total": total_votes
                    },
                    "approval_rate": approval_rate,
                    "voting_deadline": amendment.voting_deadline.isoformat() if amendment.voting_deadline else None,
                    "quorum_met": total_votes >= 3,  # Assuming quorum of 3
                    "status": "passing" if approval_rate > 0.5 else "failing" if approval_rate < 0.5 else "tied"
                })

            return {
                "active_votes": len(voting_amendments),
                "voting_progress": voting_progress,
                "overall_participation": {
                    "total_eligible_voters": 10,  # This would come from stakeholder count
                    "average_participation_rate": sum(vp["vote_counts"]["total"] for vp in voting_progress) / (len(voting_progress) * 10) if voting_progress else 0
                }
            }

        except Exception as e:
            logger.error(f"Failed to get voting progress data: {e}")
            return {"error": str(e)}

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get real-time system performance metrics."""
        try:
            # Calculate workflow processing times
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)

            # Get completed amendments from last 24 hours
            completed_amendments_query = select(ACAmendment).where(
                and_(
                    or_(ACAmendment.status == 'approved', ACAmendment.status == 'rejected'),
                    ACAmendment.updated_at >= recent_cutoff
                )
            )

            completed_result = await self.db.execute(completed_amendments_query)
            completed_amendments = completed_result.scalars().all()

            processing_times = []
            for amendment in completed_amendments:
                if amendment.created_at and amendment.updated_at:
                    processing_time = (amendment.updated_at - amendment.created_at).total_seconds() / 3600  # hours
                    processing_times.append(processing_time)

            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

            return {
                "workflow_performance": {
                    "average_processing_time_hours": round(avg_processing_time, 2),
                    "completed_amendments_24h": len(completed_amendments),
                    "processing_efficiency": min(1.0, 24 / max(avg_processing_time, 1))  # Efficiency score
                },
                "system_health": {
                    "dashboard_uptime_minutes": (datetime.utcnow() - self.last_update).total_seconds() / 60,
                    "active_connections": len(self.websocket_connections),
                    "update_frequency_seconds": self.update_interval,
                    "last_update": self.last_update.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}

    async def _get_real_time_alerts(self) -> Dict[str, Any]:
        """Get real-time alerts and notifications."""
        try:
            alerts = []
            current_time = datetime.utcnow()

            # Check for stalled amendments (no activity in 48 hours)
            stall_cutoff = current_time - timedelta(hours=48)
            stalled_query = select(ACAmendment).where(
                and_(
                    ACAmendment.status.in_(['under_review', 'public_consultation']),
                    ACAmendment.updated_at < stall_cutoff
                )
            )

            stalled_result = await self.db.execute(stalled_query)
            stalled_amendments = stalled_result.scalars().all()

            for amendment in stalled_amendments:
                alerts.append({
                    "id": f"stalled_{amendment.id}",
                    "type": "workflow_stalled",
                    "severity": "warning",
                    "message": f"Amendment {amendment.id} has been stalled for over 48 hours",
                    "amendment_id": amendment.id,
                    "timestamp": current_time.isoformat()
                })

            # Check for voting deadlines approaching (within 24 hours)
            deadline_cutoff = current_time + timedelta(hours=24)
            deadline_query = select(ACAmendment).where(
                and_(
                    ACAmendment.status == 'voting',
                    ACAmendment.voting_deadline.isnot(None),
                    ACAmendment.voting_deadline <= deadline_cutoff
                )
            )

            deadline_result = await self.db.execute(deadline_query)
            deadline_amendments = deadline_result.scalars().all()

            for amendment in deadline_amendments:
                time_remaining = (amendment.voting_deadline - current_time).total_seconds() / 3600  # hours
                alerts.append({
                    "id": f"deadline_{amendment.id}",
                    "type": "voting_deadline",
                    "severity": "critical" if time_remaining < 6 else "warning",
                    "message": f"Voting deadline for Amendment {amendment.id} in {time_remaining:.1f} hours",
                    "amendment_id": amendment.id,
                    "time_remaining_hours": time_remaining,
                    "timestamp": current_time.isoformat()
                })

            # Check for low participation rates
            if len(self.websocket_connections) < 3:  # Minimum expected stakeholders
                alerts.append({
                    "id": "low_participation",
                    "type": "low_participation",
                    "severity": "warning",
                    "message": f"Low stakeholder participation: only {len(self.websocket_connections)} active sessions",
                    "active_sessions": len(self.websocket_connections),
                    "timestamp": current_time.isoformat()
                })

            return {
                "total_alerts": len(alerts),
                "alerts_by_severity": {
                    "critical": len([a for a in alerts if a["severity"] == "critical"]),
                    "warning": len([a for a in alerts if a["severity"] == "warning"]),
                    "info": len([a for a in alerts if a["severity"] == "info"])
                },
                "active_alerts": alerts
            }

        except Exception as e:
            logger.error(f"Failed to get real-time alerts: {e}")
            return {"error": str(e)}

    async def broadcast_amendment_update(self, amendment_id: int, update_type: str, data: Dict[str, Any]) -> None:
        """Broadcast amendment-specific updates to connected clients."""
        try:
            update_message = {
                "type": "amendment_update",
                "amendment_id": amendment_id,
                "update_type": update_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }

            await self._broadcast_to_websockets(update_message)

            # Record metrics
            self.constitutional_metrics.record_constitutional_council_operations(
                operation_type="amendment_update_broadcast",
                council_member_role="system",
                status="success"
            )

        except Exception as e:
            logger.error(f"Failed to broadcast amendment update: {e}")

    async def broadcast_voting_update(self, amendment_id: int, vote_data: Dict[str, Any]) -> None:
        """Broadcast voting updates to connected clients."""
        try:
            voting_message = {
                "type": "voting_update",
                "amendment_id": amendment_id,
                "vote_data": vote_data,
                "timestamp": datetime.utcnow().isoformat()
            }

            await self._broadcast_to_websockets(voting_message)

        except Exception as e:
            logger.error(f"Failed to broadcast voting update: {e}")

    async def broadcast_stakeholder_activity(self, activity_type: str, data: Dict[str, Any]) -> None:
        """Broadcast stakeholder activity updates to connected clients."""
        try:
            activity_message = {
                "type": "stakeholder_activity",
                "activity_type": activity_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }

            await self._broadcast_to_websockets(activity_message)

        except Exception as e:
            logger.error(f"Failed to broadcast stakeholder activity: {e}")


# Global dashboard instance
dashboard_instance: Optional[ConstitutionalCouncilDashboard] = None

def get_constitutional_council_dashboard(db: AsyncSession) -> ConstitutionalCouncilDashboard:
    """Get or create the Constitutional Council dashboard instance."""
    global dashboard_instance
    if dashboard_instance is None:
        dashboard_instance = ConstitutionalCouncilDashboard(db)
    return dashboard_instance
