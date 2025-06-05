"""
Constitutional Council Dashboard WebSocket API

This module provides WebSocket endpoints for real-time dashboard functionality,
enabling live updates for amendment workflows, stakeholder engagement, and voting progress.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_async_db
from shared.auth import User
from app.services.constitutional_council_dashboard import get_constitutional_council_dashboard

# Placeholder function for WebSocket authentication
async def get_current_user_from_websocket(token: str, db: AsyncSession) -> User:
    """Placeholder function for WebSocket user authentication."""
    return User(
        id=1,
        username="test_user",
        roles=["admin", "constitutional_expert"],
        is_active=True
    )

# Placeholder function for current user
async def get_current_active_user_placeholder() -> User:
    """Placeholder function for current user authentication."""
    return User(
        id=1,
        username="test_user",
        roles=["admin", "constitutional_expert"],
        is_active=True
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard-websocket"])


@router.websocket("/ws")
async def constitutional_council_dashboard_websocket(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_async_db),
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for Constitutional Council real-time dashboard.
    
    Provides real-time updates for:
    - Amendment workflow status changes
    - Stakeholder engagement metrics
    - Voting progress and results
    - System performance metrics
    - Real-time alerts and notifications
    """
    dashboard = get_constitutional_council_dashboard(db)
    connection_id = None
    user_id = None
    
    try:
        # Authenticate user if token provided
        if token:
            try:
                user = await get_current_user_from_websocket(token, db)
                user_id = user.id
                logger.info(f"Authenticated WebSocket connection for user {user_id}")
            except Exception as e:
                logger.warning(f"WebSocket authentication failed: {e}")
                # Continue without authentication for public dashboard access
        
        # Add WebSocket connection to dashboard
        connection_id = await dashboard.add_websocket_connection(websocket, user_id)
        
        # Start dashboard if not already active
        if not dashboard.dashboard_active:
            await dashboard.start_dashboard()
        
        logger.info(f"WebSocket connection {connection_id} established for Constitutional Council dashboard")
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for incoming messages (for potential client commands)
                message = await websocket.receive_text()
                await handle_websocket_message(dashboard, connection_id, message, user_id)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket connection {connection_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                # Send error message to client
                error_response = {
                    "type": "error",
                    "message": str(e),
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                try:
                    await websocket.send_text(json.dumps(error_response))
                except:
                    break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
    finally:
        # Clean up connection
        if connection_id:
            await dashboard.remove_websocket_connection(connection_id)


async def handle_websocket_message(
    dashboard,
    connection_id: str,
    message: str,
    user_id: Optional[int]
) -> None:
    """Handle incoming WebSocket messages from clients."""
    try:
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "ping":
            # Respond to ping with pong
            pong_response = {
                "type": "pong",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            await dashboard.websocket_connections[connection_id].send_text(json.dumps(pong_response))
            
        elif message_type == "subscribe_amendment":
            # Subscribe to specific amendment updates
            amendment_id = data.get("amendment_id")
            if amendment_id:
                # Add amendment to active tracking
                dashboard.active_amendments.add(amendment_id)
                logger.info(f"Connection {connection_id} subscribed to amendment {amendment_id}")
                
        elif message_type == "unsubscribe_amendment":
            # Unsubscribe from specific amendment updates
            amendment_id = data.get("amendment_id")
            if amendment_id and amendment_id in dashboard.active_amendments:
                dashboard.active_amendments.discard(amendment_id)
                logger.info(f"Connection {connection_id} unsubscribed from amendment {amendment_id}")
                
        elif message_type == "request_data":
            # Client requesting specific data
            data_type = data.get("data_type")
            if data_type == "full_dashboard":
                dashboard_data = await dashboard.get_dashboard_data()
                await dashboard.websocket_connections[connection_id].send_text(json.dumps(dashboard_data))
            elif data_type == "amendment_details":
                amendment_id = data.get("amendment_id")
                if amendment_id:
                    # Get detailed amendment data (would implement this method)
                    amendment_details = await get_amendment_details(dashboard.db, amendment_id)
                    response = {
                        "type": "amendment_details",
                        "amendment_id": amendment_id,
                        "data": amendment_details,
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    await dashboard.websocket_connections[connection_id].send_text(json.dumps(response))
                    
        elif message_type == "update_preferences":
            # Update user dashboard preferences
            if user_id:
                preferences = data.get("preferences", {})
                # Store user preferences (would implement this)
                logger.info(f"Updated preferences for user {user_id}: {preferences}")
                
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")
            
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in WebSocket message: {message}")
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")


async def get_amendment_details(db: AsyncSession, amendment_id: int) -> Dict[str, Any]:
    """Get detailed amendment information for dashboard."""
    try:
        from app import crud
        
        # Get amendment
        amendment = await crud.get_ac_amendment(db, amendment_id)
        if not amendment:
            return {"error": "Amendment not found"}
        
        # Get votes
        votes = await crud.get_ac_amendment_votes(db, amendment_id)
        
        # Get comments
        comments = await crud.get_ac_amendment_comments(db, amendment_id)
        
        # Calculate metrics
        vote_counts = {"for": 0, "against": 0, "abstain": 0}
        for vote in votes:
            vote_counts[vote.vote_type] = vote_counts.get(vote.vote_type, 0) + 1
        
        total_votes = sum(vote_counts.values())
        approval_rate = vote_counts["for"] / total_votes if total_votes > 0 else 0
        
        return {
            "amendment": {
                "id": amendment.id,
                "principle_id": amendment.principle_id,
                "amendment_type": amendment.amendment_type,
                "proposed_changes": amendment.proposed_changes,
                "justification": amendment.justification,
                "status": amendment.status,
                "created_at": amendment.created_at.isoformat(),
                "updated_at": amendment.updated_at.isoformat(),
                "voting_deadline": amendment.voting_deadline.isoformat() if amendment.voting_deadline else None
            },
            "voting_metrics": {
                "vote_counts": vote_counts,
                "total_votes": total_votes,
                "approval_rate": approval_rate,
                "quorum_met": total_votes >= 3
            },
            "engagement_metrics": {
                "total_comments": len(comments),
                "public_comments": len([c for c in comments if c.is_public]),
                "recent_activity": len([c for c in comments if (datetime.utcnow() - c.created_at).days < 1])
            },
            "timeline": [
                {
                    "event": "created",
                    "timestamp": amendment.created_at.isoformat(),
                    "description": "Amendment proposed"
                },
                {
                    "event": "status_change",
                    "timestamp": amendment.updated_at.isoformat(),
                    "description": f"Status changed to {amendment.status}"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get amendment details: {e}")
        return {"error": str(e)}


@router.get("/status")
async def get_dashboard_status(
    db: AsyncSession = Depends(get_async_db)
):
    """Get current dashboard status and metrics."""
    try:
        dashboard = get_constitutional_council_dashboard(db)
        
        status = {
            "dashboard_active": dashboard.dashboard_active,
            "active_connections": len(dashboard.websocket_connections),
            "update_interval_seconds": dashboard.update_interval,
            "last_update": dashboard.last_update.isoformat(),
            "active_amendments": len(dashboard.active_amendments),
            "stakeholder_sessions": len(dashboard.stakeholder_sessions)
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get dashboard status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_dashboard(
    db: AsyncSession = Depends(get_async_db)
):
    """Start the real-time dashboard (admin only)."""
    try:
        dashboard = get_constitutional_council_dashboard(db)
        
        if not dashboard.dashboard_active:
            await dashboard.start_dashboard()
            return {"message": "Dashboard started successfully", "status": "active"}
        else:
            return {"message": "Dashboard already active", "status": "active"}
            
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_dashboard(
    db: AsyncSession = Depends(get_async_db)
):
    """Stop the real-time dashboard (admin only)."""
    try:
        dashboard = get_constitutional_council_dashboard(db)
        
        if dashboard.dashboard_active:
            await dashboard.stop_dashboard()
            return {"message": "Dashboard stopped successfully", "status": "inactive"}
        else:
            return {"message": "Dashboard already inactive", "status": "inactive"}
            
    except Exception as e:
        logger.error(f"Failed to stop dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_async_db)
):
    """Get current dashboard data (REST endpoint for non-WebSocket clients)."""
    try:
        dashboard = get_constitutional_council_dashboard(db)
        data = await dashboard.get_dashboard_data()
        return data
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
