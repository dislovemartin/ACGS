"""
Constitutional Council Scalability Framework

Enhances Constitutional Council implementation to handle rapid co-evolution
scenarios and improve scalability for real-world deployment.

Based on AlphaEvolve-ACGS Integration System research paper improvements.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from prometheus_client import Counter, Histogram, Gauge

from ..models import ACAmendment, ACAmendmentVote, ACAmendmentComment, User
from ..schemas import ACAmendmentCreate, ACAmendmentVoteCreate, ACAmendmentCommentCreate
# from shared.redis_client import get_redis_client
from shared.metrics import ACGSMetrics

logger = logging.getLogger(__name__)


class CoEvolutionMode(Enum):
    """Co-evolution modes for different scenarios."""
    STANDARD = "standard"  # Normal amendment process
    RAPID = "rapid"  # Fast-track for urgent changes
    EMERGENCY = "emergency"  # Emergency constitutional changes
    CONTINUOUS = "continuous"  # Continuous adaptation mode


class VotingStrategy(Enum):
    """Voting strategies for different scenarios."""
    SYNCHRONOUS = "synchronous"  # All votes at once
    ASYNCHRONOUS = "asynchronous"  # Rolling votes
    WEIGHTED = "weighted"  # Weighted by expertise
    DELEGATED = "delegated"  # Delegated voting


@dataclass
class ScalabilityConfig:
    """Configuration for Constitutional Council scalability."""
    max_concurrent_amendments: int = 10
    rapid_voting_window_hours: int = 24
    emergency_voting_window_hours: int = 6
    async_voting_enabled: bool = True
    caching_enabled: bool = True
    load_balancing_enabled: bool = True
    batch_processing_size: int = 50
    performance_monitoring_enabled: bool = True


@dataclass
class CoEvolutionMetrics:
    """Metrics for co-evolution performance."""
    amendment_throughput: float  # Amendments per hour
    average_voting_time: float  # Average time to complete voting
    consensus_rate: float  # Rate of achieving consensus
    participation_rate: float  # Council member participation
    scalability_score: float  # Overall scalability metric
    bottleneck_indicators: List[str]  # Identified bottlenecks


class RapidCoEvolutionHandler:
    """Handles rapid co-evolution scenarios for Constitutional Council."""

    def __init__(self, config: ScalabilityConfig):
        self.config = config
        self.active_amendments = {}
        self.voting_queues = {}
        self.performance_cache = {}

        # Redis client for caching and metrics
        self.redis_client = None

        # Prometheus metrics - use global registry to avoid duplicates
        try:
            self.amendment_processing_time = Histogram(
                'acgs_amendment_processing_seconds',
                'Time spent processing amendments',
                ['urgency_level', 'constitutional_significance']
            )
        except ValueError:
            # Metric already exists, get existing one
            from prometheus_client import REGISTRY
            for collector in REGISTRY._collector_to_names:
                if hasattr(collector, '_name') and collector._name == 'acgs_amendment_processing_seconds':
                    self.amendment_processing_time = collector
                    break

        try:
            self.active_amendments_gauge = Gauge(
                'acgs_active_amendments_total',
                'Number of active amendments'
            )
        except ValueError:
            # Metric already exists, get existing one
            from prometheus_client import REGISTRY
            for collector in REGISTRY._collector_to_names:
                if hasattr(collector, '_name') and collector._name == 'acgs_active_amendments_total':
                    self.active_amendments_gauge = collector
                    break

        try:
            self.co_evolution_events = Counter(
                'acgs_co_evolution_events_total',
                'Total co-evolution events',
                ['event_type', 'urgency_level']
            )
        except ValueError:
            # Metric already exists, get existing one
            from prometheus_client import REGISTRY
            for collector in REGISTRY._collector_to_names:
                if hasattr(collector, '_name') and collector._name == 'acgs_co_evolution_events_total':
                    self.co_evolution_events = collector
                    break

    async def initialize(self):
        """Initialize Redis client and metrics collection."""
        try:
            # self.redis_client = await get_redis_client("constitutional_council")
            logger.info("Rapid co-evolution handler initialized (Redis disabled)")
        except Exception as e:
            logger.error(f"Failed to initialize rapid co-evolution handler: {e}")
            # Continue without Redis if it fails
            pass
        
    async def process_rapid_amendment(
        self,
        db: AsyncSession,
        amendment_data: ACAmendmentCreate,
        urgency_level: CoEvolutionMode = CoEvolutionMode.RAPID
    ) -> Dict[str, Any]:
        """Process amendment with rapid co-evolution handling."""
        start_time = time.time()
        
        # Validate amendment for rapid processing
        validation_result = await self._validate_rapid_amendment(db, amendment_data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["error"],
                "processing_time": time.time() - start_time
            }
        
        # Create amendment with rapid processing flags
        amendment = await self._create_rapid_amendment(db, amendment_data, urgency_level)
        
        # Initialize rapid voting process
        voting_result = await self._initialize_rapid_voting(db, amendment, urgency_level)
        
        # Monitor and optimize performance
        if self.config.performance_monitoring_enabled:
            await self._monitor_amendment_performance(amendment.id, start_time)
        
        return {
            "success": True,
            "amendment_id": amendment.id,
            "voting_window_hours": self._get_voting_window(urgency_level),
            "expected_completion": datetime.utcnow() + timedelta(hours=self._get_voting_window(urgency_level)),
            "processing_time": time.time() - start_time
        }
    
    async def _validate_rapid_amendment(
        self,
        db: AsyncSession,
        amendment_data: ACAmendmentCreate
    ) -> Dict[str, Any]:
        """Validate amendment for rapid processing eligibility."""
        # Check concurrent amendment limit
        active_count = await self._get_active_amendment_count(db)
        if active_count >= self.config.max_concurrent_amendments:
            return {
                "valid": False,
                "error": f"Maximum concurrent amendments ({self.config.max_concurrent_amendments}) reached"
            }
        
        # Check for conflicting amendments
        conflicts = await self._check_amendment_conflicts(db, amendment_data)
        if conflicts:
            return {
                "valid": False,
                "error": f"Conflicting amendments detected: {conflicts}"
            }
        
        # Validate amendment content
        content_validation = await self._validate_amendment_content(amendment_data)
        if not content_validation["valid"]:
            return content_validation
        
        return {"valid": True}
    
    async def _get_active_amendment_count(self, db: AsyncSession) -> int:
        """Get count of currently active amendments."""
        result = await db.execute(
            select(func.count(ACAmendment.id)).where(
                ACAmendment.status.in_(["proposed", "voting", "discussion"])
            )
        )
        return result.scalar() or 0
    
    async def _check_amendment_conflicts(
        self,
        db: AsyncSession,
        amendment_data: ACAmendmentCreate
    ) -> List[str]:
        """Check for conflicting amendments."""
        # Simplified conflict detection - would be more sophisticated in practice
        conflicts = []
        
        # Check for amendments affecting same principles
        if hasattr(amendment_data, 'affected_principle_ids'):
            result = await db.execute(
                select(ACAmendment.id, ACAmendment.title).where(
                    and_(
                        ACAmendment.status.in_(["proposed", "voting"]),
                        ACAmendment.affected_principle_ids.op('&&')(amendment_data.affected_principle_ids)
                    )
                )
            )
            conflicting_amendments = result.fetchall()
            conflicts.extend([f"Amendment {a.id}: {a.proposed_changes[:50]}..." for a in conflicting_amendments])
        
        return conflicts
    
    async def _validate_amendment_content(self, amendment_data: ACAmendmentCreate) -> Dict[str, Any]:
        """Validate amendment content for completeness and safety."""
        # Use proposed_changes as title equivalent
        if not amendment_data.proposed_changes or len(amendment_data.proposed_changes.strip()) < 10:
            return {"valid": False, "error": "Amendment proposed changes too short"}

        # Use justification as description equivalent
        if not amendment_data.justification or len(amendment_data.justification.strip()) < 20:
            return {"valid": False, "error": "Amendment justification too short"}

        # Check for dangerous keywords (simplified)
        dangerous_keywords = ["delete all", "remove everything", "disable system"]
        content = f"{amendment_data.proposed_changes} {amendment_data.justification}".lower()
        for keyword in dangerous_keywords:
            if keyword in content:
                return {"valid": False, "error": f"Potentially dangerous content detected: {keyword}"}

        return {"valid": True}
    
    async def _create_rapid_amendment(
        self,
        db: AsyncSession,
        amendment_data: ACAmendmentCreate,
        urgency_level: CoEvolutionMode
    ) -> ACAmendment:
        """Create amendment with rapid processing metadata and optimistic locking."""
        start_time = time.time()

        try:
            # Create amendment with enhanced co-evolution fields
            amendment = ACAmendment(
                principle_id=amendment_data.principle_id,
                amendment_type=amendment_data.amendment_type,
                proposed_changes=amendment_data.proposed_changes,
                justification=amendment_data.justification,
                proposed_content=amendment_data.proposed_content,
                proposed_status=amendment_data.proposed_status,
                consultation_period_days=amendment_data.consultation_period_days,
                public_comment_enabled=amendment_data.public_comment_enabled,
                stakeholder_groups=amendment_data.stakeholder_groups,

                # Co-evolution fields
                urgency_level=urgency_level.value,
                co_evolution_context=amendment_data.co_evolution_context,
                expected_impact=amendment_data.expected_impact,
                rapid_processing_requested=amendment_data.rapid_processing_requested,
                constitutional_significance=amendment_data.constitutional_significance,

                # Optimistic locking and workflow
                version=1,
                workflow_state="proposed",
                state_transitions=[{
                    "from_state": None,
                    "to_state": "proposed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "urgency_level": urgency_level.value
                }],
                processing_metrics={
                    "creation_time": time.time() - start_time,
                    "urgency_level": urgency_level.value,
                    "rapid_processing": amendment_data.rapid_processing_requested
                },

                status="proposed",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                proposed_by_user_id=1  # Mock user ID for testing
            )

            db.add(amendment)
            await db.commit()
            await db.refresh(amendment)

            # Cache amendment in Redis for rapid access
            if self.redis_client:
                await self._cache_amendment(amendment)

            # Update metrics
            self.co_evolution_events.labels(
                event_type="amendment_created",
                urgency_level=urgency_level.value
            ).inc()

            self.amendment_processing_time.labels(
                urgency_level=urgency_level.value,
                constitutional_significance=amendment_data.constitutional_significance
            ).observe(time.time() - start_time)

            return amendment

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create rapid amendment: {e}")
            raise
    
    def _get_voting_window(self, urgency_level: CoEvolutionMode) -> int:
        """Get voting window hours based on urgency level."""
        windows = {
            CoEvolutionMode.STANDARD: 168,  # 1 week
            CoEvolutionMode.RAPID: self.config.rapid_voting_window_hours,
            CoEvolutionMode.EMERGENCY: self.config.emergency_voting_window_hours,
            CoEvolutionMode.CONTINUOUS: 24  # 1 day for continuous mode
        }
        return windows.get(urgency_level, 168)
    
    async def _initialize_rapid_voting(
        self,
        db: AsyncSession,
        amendment: ACAmendment,
        urgency_level: CoEvolutionMode
    ) -> Dict[str, Any]:
        """Initialize rapid voting process."""
        # Get Constitutional Council members
        council_members = await self._get_council_members(db)
        
        # Create voting queue
        voting_queue = {
            "amendment_id": amendment.id,
            "urgency_level": urgency_level.value,
            "voting_deadline": datetime.utcnow() + timedelta(hours=self._get_voting_window(urgency_level)),
            "required_votes": len(council_members),
            "received_votes": 0,
            "strategy": VotingStrategy.ASYNCHRONOUS.value if self.config.async_voting_enabled else VotingStrategy.SYNCHRONOUS.value
        }
        
        self.voting_queues[amendment.id] = voting_queue
        
        # Notify council members (would integrate with notification system)
        await self._notify_council_members(council_members, amendment, urgency_level)
        
        return {
            "voting_initialized": True,
            "council_members_notified": len(council_members),
            "voting_deadline": voting_queue["voting_deadline"]
        }
    
    async def _get_council_members(self, db: AsyncSession) -> List[User]:
        """Get active Constitutional Council members."""
        result = await db.execute(
            select(User).where(
                and_(
                    User.role == "constitutional_council",
                    User.is_active == True
                )
            )
        )
        return result.scalars().all()
    
    async def _notify_council_members(
        self,
        members: List[User],
        amendment: ACAmendment,
        urgency_level: CoEvolutionMode
    ):
        """Notify council members of new amendment (placeholder)."""
        # In practice, this would integrate with notification system
        logger.info(f"Notifying {len(members)} council members of {urgency_level.value} amendment {amendment.id}")
    
    async def _monitor_amendment_performance(self, amendment_id: int, start_time: float):
        """Monitor amendment processing performance."""
        processing_time = time.time() - start_time
        
        if amendment_id not in self.performance_cache:
            self.performance_cache[amendment_id] = {
                "creation_time": processing_time,
                "milestones": []
            }
        
        self.performance_cache[amendment_id]["milestones"].append({
            "milestone": "created",
            "timestamp": time.time(),
            "processing_time": processing_time
        })

    async def _cache_amendment(self, amendment: ACAmendment):
        """Cache amendment in Redis for rapid access."""
        if not self.redis_client:
            return

        try:
            cache_key = self.redis_client.generate_key("amendment", str(amendment.id))
            amendment_data = {
                "id": amendment.id,
                "principle_id": amendment.principle_id,
                "amendment_type": amendment.amendment_type,
                "proposed_changes": amendment.proposed_changes,
                "urgency_level": amendment.urgency_level,
                "workflow_state": amendment.workflow_state,
                "version": amendment.version,
                "status": amendment.status,
                "created_at": amendment.created_at.isoformat(),
                "processing_metrics": amendment.processing_metrics
            }

            # Cache for 1 hour for rapid amendments, 24 hours for normal
            ttl = 3600 if amendment.urgency_level in ["rapid", "emergency"] else 86400
            await self.redis_client.set_json(cache_key, amendment_data, ttl)

            # Add to active amendments set
            active_key = self.redis_client.generate_key("active_amendments")
            await self.redis_client.add_to_list(active_key, amendment.id, max_length=100)

        except Exception as e:
            logger.error(f"Failed to cache amendment {amendment.id}: {e}")

    async def update_amendment_with_optimistic_locking(
        self,
        db: AsyncSession,
        amendment_id: int,
        updates: Dict[str, Any],
        expected_version: int
    ) -> Dict[str, Any]:
        """Update amendment with optimistic locking to prevent conflicts."""
        try:
            # Get current amendment
            amendment = await db.get(ACAmendment, amendment_id)
            if not amendment:
                return {"success": False, "error": "Amendment not found"}

            # Check version for optimistic locking
            if amendment.version != expected_version:
                return {
                    "success": False,
                    "error": f"Version conflict: expected {expected_version}, got {amendment.version}",
                    "current_version": amendment.version
                }

            # Apply updates
            for key, value in updates.items():
                if hasattr(amendment, key):
                    setattr(amendment, key, value)

            # Increment version and update timestamp
            amendment.version += 1
            amendment.updated_at = datetime.utcnow()

            # Add state transition if workflow_state changed
            if "workflow_state" in updates:
                if not amendment.state_transitions:
                    amendment.state_transitions = []

                amendment.state_transitions.append({
                    "from_state": amendment.workflow_state,
                    "to_state": updates["workflow_state"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": amendment.version
                })

            await db.commit()
            await db.refresh(amendment)

            # Update cache
            if self.redis_client:
                await self._cache_amendment(amendment)

            return {
                "success": True,
                "new_version": amendment.version,
                "updated_at": amendment.updated_at.isoformat()
            }

        except OptimisticLockError:
            await db.rollback()
            return {
                "success": False,
                "error": "Optimistic lock error: amendment was modified by another process"
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update amendment {amendment_id}: {e}")
            return {"success": False, "error": str(e)}


class AsyncVotingManager:
    """Manages asynchronous voting processes for scalability."""
    
    def __init__(self, config: ScalabilityConfig):
        self.config = config
        self.vote_processors = {}
        
    async def process_async_vote(
        self,
        db: AsyncSession,
        amendment_id: int,
        vote_data: ACAmendmentVoteCreate,
        voter_id: int
    ) -> Dict[str, Any]:
        """Process vote asynchronously for better scalability."""
        start_time = time.time()
        
        # Validate vote
        validation = await self._validate_vote(db, amendment_id, voter_id)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        # Process vote in background if enabled
        if self.config.async_voting_enabled:
            task = asyncio.create_task(
                self._process_vote_background(db, amendment_id, vote_data, voter_id)
            )
            self.vote_processors[f"{amendment_id}_{voter_id}"] = task
            
            return {
                "success": True,
                "vote_queued": True,
                "processing_time": time.time() - start_time
            }
        else:
            # Process synchronously
            result = await self._process_vote_background(db, amendment_id, vote_data, voter_id)
            return {
                "success": result["success"],
                "vote_recorded": True,
                "processing_time": time.time() - start_time
            }
    
    async def _validate_vote(self, db: AsyncSession, amendment_id: int, voter_id: int) -> Dict[str, Any]:
        """Validate vote eligibility."""
        # Check if amendment exists and is in voting state
        amendment = await db.get(ACAmendment, amendment_id)
        if not amendment:
            return {"valid": False, "error": "Amendment not found"}
        
        if amendment.status not in ["proposed", "voting"]:
            return {"valid": False, "error": f"Amendment not in voting state: {amendment.status}"}
        
        # Check if voter already voted
        existing_vote = await db.execute(
            select(ACAmendmentVote).where(
                and_(
                    ACAmendmentVote.amendment_id == amendment_id,
                    ACAmendmentVote.voter_id == voter_id
                )
            )
        )
        if existing_vote.scalar():
            return {"valid": False, "error": "Voter has already voted on this amendment"}
        
        return {"valid": True}
    
    async def _process_vote_background(
        self,
        db: AsyncSession,
        amendment_id: int,
        vote_data: ACAmendmentVoteCreate,
        voter_id: int
    ) -> Dict[str, Any]:
        """Process vote in background."""
        try:
            # Create vote record
            vote = ACAmendmentVote(
                amendment_id=amendment_id,
                voter_id=voter_id,
                vote=vote_data.vote,
                reasoning=vote_data.reasoning,
                created_at=datetime.utcnow()
            )
            
            db.add(vote)
            await db.commit()
            
            # Check if voting is complete
            await self._check_voting_completion(db, amendment_id)
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error processing vote: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}
    
    async def _check_voting_completion(self, db: AsyncSession, amendment_id: int):
        """Check if voting is complete and process results."""
        # Get vote counts
        vote_counts = await db.execute(
            select(
                ACAmendmentVote.vote,
                func.count(ACAmendmentVote.id).label('count')
            ).where(
                ACAmendmentVote.amendment_id == amendment_id
            ).group_by(ACAmendmentVote.vote)
        )
        
        counts = {row.vote: row.count for row in vote_counts}
        total_votes = sum(counts.values())
        
        # Get required quorum (simplified)
        required_quorum = 5  # From Constitutional Council charter
        
        if total_votes >= required_quorum:
            # Calculate results
            for_votes = counts.get("for", 0)
            against_votes = counts.get("against", 0)
            abstain_votes = counts.get("abstain", 0)
            
            # 60% supermajority required
            if for_votes / total_votes >= 0.6:
                await self._finalize_amendment(db, amendment_id, "approved")
            elif against_votes / total_votes > 0.4:
                await self._finalize_amendment(db, amendment_id, "rejected")
    
    async def _finalize_amendment(self, db: AsyncSession, amendment_id: int, status: str):
        """Finalize amendment with given status."""
        amendment = await db.get(ACAmendment, amendment_id)
        if amendment:
            amendment.status = status
            amendment.finalized_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Amendment {amendment_id} finalized with status: {status}")


class ConstitutionalCouncilScalabilityFramework:
    """Main framework for Constitutional Council scalability."""
    
    def __init__(self, config: ScalabilityConfig = None):
        self.config = config or ScalabilityConfig()
        self.rapid_handler = RapidCoEvolutionHandler(self.config)
        self.async_voting_manager = AsyncVotingManager(self.config)
        self.performance_metrics = []
    
    async def get_scalability_metrics(self, db: AsyncSession) -> CoEvolutionMetrics:
        """Calculate current scalability metrics."""
        # Get recent amendments (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_amendments = await db.execute(
            select(ACAmendment).where(ACAmendment.created_at >= thirty_days_ago)
        )
        amendments = recent_amendments.scalars().all()
        
        if not amendments:
            return CoEvolutionMetrics(
                amendment_throughput=0.0,
                average_voting_time=0.0,
                consensus_rate=0.0,
                participation_rate=0.0,
                scalability_score=0.0,
                bottleneck_indicators=["No recent amendments"]
            )
        
        # Calculate metrics
        throughput = len(amendments) / (30 * 24)  # Amendments per hour
        
        # Calculate average voting time for completed amendments
        completed = [a for a in amendments if a.status in ["approved", "rejected"]]
        avg_voting_time = 0.0
        if completed:
            voting_times = []
            for amendment in completed:
                if amendment.finalized_at and amendment.created_at:
                    voting_time = (amendment.finalized_at - amendment.created_at).total_seconds() / 3600
                    voting_times.append(voting_time)
            avg_voting_time = sum(voting_times) / len(voting_times) if voting_times else 0.0
        
        # Calculate consensus rate (approved / total completed)
        consensus_rate = len([a for a in completed if a.status == "approved"]) / len(completed) if completed else 0.0
        
        # Calculate participation rate (placeholder)
        participation_rate = 0.85  # Would calculate from actual voting data
        
        # Overall scalability score
        scalability_score = (
            min(throughput * 10, 1.0) * 0.3 +  # Throughput component
            (1.0 - min(avg_voting_time / 168, 1.0)) * 0.3 +  # Speed component
            consensus_rate * 0.2 +  # Consensus component
            participation_rate * 0.2  # Participation component
        )
        
        # Identify bottlenecks
        bottlenecks = []
        if throughput < 0.1:
            bottlenecks.append("Low amendment throughput")
        if avg_voting_time > 72:
            bottlenecks.append("Slow voting process")
        if consensus_rate < 0.5:
            bottlenecks.append("Low consensus rate")
        if participation_rate < 0.7:
            bottlenecks.append("Low participation rate")
        
        return CoEvolutionMetrics(
            amendment_throughput=throughput,
            average_voting_time=avg_voting_time,
            consensus_rate=consensus_rate,
            participation_rate=participation_rate,
            scalability_score=scalability_score,
            bottleneck_indicators=bottlenecks
        )
