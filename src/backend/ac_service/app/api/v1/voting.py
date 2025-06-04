"""
Voting Mechanism API Endpoints

This module provides REST API endpoints for the voting mechanism integration
with the Autonomous Constitution Service, enabling real-time governance
decision processing, consensus algorithms, and vote management.

Key Features:
- Create and manage voting sessions
- Cast and validate votes
- Real-time vote status and results
- Multiple consensus algorithm support
- Vote tallying and result calculation
- WebSocket support for real-time updates
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db_session
from ...services.voting_mechanism import (
    ConsensusAlgorithm,
    VoteType,
    VotingStatus,
    get_voting_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voting", tags=["voting"])


# Request/Response Models
class CreateVotingSessionRequest(BaseModel):
    """Request model for creating a voting session."""

    amendment_id: int = Field(..., description="ID of amendment to vote on")
    algorithm: ConsensusAlgorithm = Field(
        default=ConsensusAlgorithm.SIMPLE_MAJORITY,
        description="Consensus algorithm to use",
    )
    duration_hours: int = Field(
        default=72, ge=1, le=168, description="Voting duration in hours"
    )
    eligible_voters: Optional[List[int]] = Field(
        default=None, description="List of eligible voter IDs"
    )
    custom_threshold: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Custom consensus threshold"
    )
    metadata: Optional[Dict] = Field(
        default=None, description="Additional session metadata"
    )


class CastVoteRequest(BaseModel):
    """Request model for casting a vote."""

    vote: VoteType = Field(..., description="Vote choice")
    reasoning: Optional[str] = Field(
        default=None, description="Optional vote reasoning"
    )
    signature: Optional[str] = Field(
        default=None, description="Optional cryptographic signature"
    )


class VotingSessionResponse(BaseModel):
    """Response model for voting session information."""

    session_id: str
    amendment_id: int
    algorithm: ConsensusAlgorithm
    status: VotingStatus
    start_time: str
    end_time: str
    threshold: float
    eligible_voters_count: int
    current_votes_count: int
    time_remaining_seconds: float
    metadata: Dict


class VoteStatusResponse(BaseModel):
    """Response model for vote status."""

    session_id: str
    amendment_id: int
    status: VotingStatus
    algorithm: str
    time_remaining_seconds: float
    participation_rate: float
    current_result: str
    consensus_reached: bool
    votes: Dict
    weighted_votes: Dict
    threshold: Dict


class VotingResultResponse(BaseModel):
    """Response model for voting results."""

    votes_for: int
    votes_against: int
    votes_abstain: int
    total_votes: int
    total_eligible_voters: int
    weighted_votes_for: float
    weighted_votes_against: float
    weighted_votes_abstain: float
    consensus_reached: bool
    required_threshold: float
    actual_threshold: float
    algorithm_used: str
    result: str
    metadata: Dict


# WebSocket connection manager
class VotingWebSocketManager:
    """Manages WebSocket connections for real-time voting updates."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a WebSocket to a voting session."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Disconnect a WebSocket from a voting session."""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)

    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast a message to all connections for a session."""
        if session_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[session_id].remove(connection)


websocket_manager = VotingWebSocketManager()


# API Endpoints


@router.post("/sessions", response_model=VotingSessionResponse)
async def create_voting_session(
    request: CreateVotingSessionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> VotingSessionResponse:
    """
    Create a new voting session for an amendment.

    Creates a new voting session with the specified consensus algorithm
    and configuration, notifies eligible voters, and returns session
    details.
    """
    try:
        voting_service = await get_voting_service(db)

        session_id = await voting_service.create_voting_session(
            amendment_id=request.amendment_id,
            algorithm=request.algorithm,
            duration_hours=request.duration_hours,
            eligible_voters=request.eligible_voters,
            custom_threshold=request.custom_threshold,
            metadata=request.metadata,
        )

        # Get session details
        session = voting_service.active_sessions[session_id]

        return VotingSessionResponse(
            session_id=session_id,
            amendment_id=session.amendment_id,
            algorithm=session.algorithm,
            status=session.status,
            start_time=session.start_time.isoformat(),
            end_time=session.end_time.isoformat(),
            threshold=session.threshold,
            eligible_voters_count=len(session.eligible_voters),
            current_votes_count=len(session.current_votes),
            time_remaining_seconds=max(
                0, (session.end_time - session.start_time).total_seconds()
            ),
            metadata=session.metadata,
        )

    except Exception as e:
        logger.error(f"Failed to create voting session: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/votes")
async def cast_vote(
    session_id: str,
    request: CastVoteRequest,
    voter_id: int = Query(..., description="ID of the voter"),
    db: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    """
    Cast a vote in an active voting session.

    Records a vote for the specified voter in the given session,
    validates eligibility and fraud detection, and triggers
    real-time updates to connected clients.
    """
    try:
        voting_service = await get_voting_service(db)

        success = await voting_service.cast_vote(
            session_id=session_id,
            voter_id=voter_id,
            vote=request.vote,
            reasoning=request.reasoning,
            vote_signature=request.signature,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Vote casting failed")

        # Get updated status for broadcast
        status = await voting_service.get_voting_status(session_id)

        # Broadcast update to WebSocket connections
        await websocket_manager.broadcast_to_session(
            session_id,
            {
                "type": "vote_cast",
                "session_id": session_id,
                "voter_id": voter_id,
                "vote": request.vote.value,
                "status": status,
            },
        )

        return JSONResponse(
            content={
                "success": True,
                "message": "Vote cast successfully",
                "session_id": session_id,
                "voter_id": voter_id,
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Failed to cast vote: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/status", response_model=VoteStatusResponse)
async def get_voting_status(
    session_id: str, db: AsyncSession = Depends(get_db_session)
) -> VoteStatusResponse:
    """
    Get current status of a voting session.

    Returns comprehensive voting statistics including vote counts,
    participation rate, consensus status, and time remaining.
    """
    try:
        voting_service = await get_voting_service(db)
        status = await voting_service.get_voting_status(session_id)

        return VoteStatusResponse(
            session_id=status["session_id"],
            amendment_id=status["amendment_id"],
            status=VotingStatus(status["status"]),
            algorithm=status["algorithm"],
            time_remaining_seconds=status["time_remaining_seconds"],
            participation_rate=status["participation_rate"],
            current_result=status["current_result"],
            consensus_reached=status["consensus_reached"],
            votes=status["votes"],
            weighted_votes=status["weighted_votes"],
            threshold=status["threshold"],
        )

    except Exception as e:
        logger.error(f"Failed to get voting status: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sessions/{session_id}/finalize", response_model=VotingResultResponse)
async def finalize_voting_session(
    session_id: str, db: AsyncSession = Depends(get_db_session)
) -> VotingResultResponse:
    """
    Finalize a voting session and calculate final results.

    Ends the voting period, calculates final results using the
    configured consensus algorithm, updates amendment status,
    and sends completion notifications.
    """
    try:
        voting_service = await get_voting_service(db)
        result = await voting_service.finalize_voting_session(session_id)

        # Broadcast finalization to WebSocket connections
        await websocket_manager.broadcast_to_session(
            session_id,
            {
                "type": "session_finalized",
                "session_id": session_id,
                "result": result.result,
                "consensus_reached": result.consensus_reached,
            },
        )

        return VotingResultResponse(
            votes_for=result.votes_for,
            votes_against=result.votes_against,
            votes_abstain=result.votes_abstain,
            total_votes=result.total_votes,
            total_eligible_voters=result.total_eligible_voters,
            weighted_votes_for=result.weighted_votes_for,
            weighted_votes_against=result.weighted_votes_against,
            weighted_votes_abstain=result.weighted_votes_abstain,
            consensus_reached=result.consensus_reached,
            required_threshold=result.required_threshold,
            actual_threshold=result.actual_threshold,
            algorithm_used=result.algorithm_used.value,
            result=result.result,
            metadata=result.metadata,
        )

    except Exception as e:
        logger.error(f"Failed to finalize voting session: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=List[VotingSessionResponse])
async def list_voting_sessions(
    status_filter: Optional[VotingStatus] = Query(
        default=None, description="Filter by voting status"
    ),
    amendment_id: Optional[int] = Query(
        default=None, description="Filter by amendment ID"
    ),
    db: AsyncSession = Depends(get_db_session),
) -> List[VotingSessionResponse]:
    """
    List all voting sessions with optional filtering.

    Returns a list of voting sessions, optionally filtered by
    status or amendment ID, including current progress information.
    """
    try:
        voting_service = await get_voting_service(db)
        sessions = []

        for session in voting_service.active_sessions.values():
            # Apply filters
            if status_filter and session.status != status_filter:
                continue
            if amendment_id and session.amendment_id != amendment_id:
                continue

            sessions.append(
                VotingSessionResponse(
                    session_id=session.session_id,
                    amendment_id=session.amendment_id,
                    algorithm=session.algorithm,
                    status=session.status,
                    start_time=session.start_time.isoformat(),
                    end_time=session.end_time.isoformat(),
                    threshold=session.threshold,
                    eligible_voters_count=len(session.eligible_voters),
                    current_votes_count=len(session.current_votes),
                    time_remaining_seconds=max(
                        0,
                        (session.end_time - session.start_time).total_seconds(),
                    ),
                    metadata=session.metadata,
                )
            )

        return sessions

    except Exception as e:
        logger.error(f"Failed to list voting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/algorithms", response_model=List[Dict])
async def get_available_algorithms() -> List[Dict]:
    """
    Get list of available consensus algorithms.

    Returns information about all supported consensus algorithms
    including their default thresholds and descriptions.
    """
    algorithms = [
        {
            "name": ConsensusAlgorithm.SIMPLE_MAJORITY.value,
            "display_name": "Simple Majority",
            "default_threshold": 0.50,
            "description": "Requires more than 50% of votes to be 'for'",
        },
        {
            "name": ConsensusAlgorithm.SUPERMAJORITY.value,
            "display_name": "Supermajority",
            "default_threshold": 0.67,
            "description": "Requires at least 67% of votes to be 'for'",
        },
        {
            "name": ConsensusAlgorithm.QUALIFIED_MAJORITY.value,
            "display_name": "Qualified Majority",
            "default_threshold": 0.75,
            "description": "Requires at least 75% of votes to be 'for'",
        },
        {
            "name": ConsensusAlgorithm.UNANIMITY.value,
            "display_name": "Unanimity",
            "default_threshold": 1.0,
            "description": "Requires all votes to be 'for' with no 'against'",
        },
        {
            "name": ConsensusAlgorithm.QUADRATIC_VOTING.value,
            "display_name": "Quadratic Voting",
            "default_threshold": 0.50,
            "description": "Uses quadratic scaling of vote weights",
        },
        {
            "name": ConsensusAlgorithm.WEIGHTED_VOTING.value,
            "display_name": "Weighted Voting",
            "default_threshold": 0.60,
            "description": "Uses role and expertise-based vote weights",
        },
    ]

    return algorithms


@router.websocket("/sessions/{session_id}/ws")
async def voting_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    WebSocket endpoint for real-time voting updates.

    Provides real-time updates for voting session progress,
    including new votes, status changes, and session completion.
    """
    try:
        # Verify session exists
        voting_service = await get_voting_service(db)
        if session_id not in voting_service.active_sessions:
            await websocket.close(code=4004, reason="Session not found")
            return

        # Connect WebSocket
        await websocket_manager.connect(websocket, session_id)

        # Send initial status
        try:
            status = await voting_service.get_voting_status(session_id)
            await websocket.send_json({"type": "initial_status", "status": status})
        except Exception as e:
            logger.error(f"Failed to send initial status: {e}")

        # Keep connection alive and handle client messages
        try:
            while True:
                # Wait for client messages (ping/pong, etc.)
                message = await websocket.receive_text()

                # Handle ping messages
                if message == "ping":
                    await websocket.send_text("pong")

        except Exception as e:
            logger.info(f"WebSocket connection closed: {e}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Disconnect WebSocket
        websocket_manager.disconnect(websocket, session_id)


@router.get("/sessions/{session_id}/results", response_model=VotingResultResponse)
async def get_voting_results(
    session_id: str, db: AsyncSession = Depends(get_db_session)
) -> VotingResultResponse:
    """
    Get voting results for a session.

    Returns detailed voting results including vote counts,
    weighted votes, consensus determination, and metadata.
    Can be called during or after voting period.
    """
    try:
        voting_service = await get_voting_service(db)
        result = await voting_service.calculate_voting_result(session_id)

        return VotingResultResponse(
            votes_for=result.votes_for,
            votes_against=result.votes_against,
            votes_abstain=result.votes_abstain,
            total_votes=result.total_votes,
            total_eligible_voters=result.total_eligible_voters,
            weighted_votes_for=result.weighted_votes_for,
            weighted_votes_against=result.weighted_votes_against,
            weighted_votes_abstain=result.weighted_votes_abstain,
            consensus_reached=result.consensus_reached,
            required_threshold=result.required_threshold,
            actual_threshold=result.actual_threshold,
            algorithm_used=result.algorithm_used.value,
            result=result.result,
            metadata=result.metadata,
        )

    except Exception as e:
        logger.error(f"Failed to get voting results: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/sessions/{session_id}")
async def cancel_voting_session(
    session_id: str, db: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    """
    Cancel an active voting session.

    Cancels an ongoing voting session, preventing further votes
    and setting the session status to cancelled. This action
    cannot be undone.
    """
    try:
        voting_service = await get_voting_service(db)

        if session_id not in voting_service.active_sessions:
            raise HTTPException(status_code=404, detail="Voting session not found")

        session = voting_service.active_sessions[session_id]
        session.status = VotingStatus.CANCELLED

        # Broadcast cancellation to WebSocket connections
        await websocket_manager.broadcast_to_session(
            session_id,
            {
                "type": "session_cancelled",
                "session_id": session_id,
                "message": "Voting session has been cancelled",
            },
        )

        return JSONResponse(
            content={
                "success": True,
                "message": "Voting session cancelled successfully",
                "session_id": session_id,
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Failed to cancel voting session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
