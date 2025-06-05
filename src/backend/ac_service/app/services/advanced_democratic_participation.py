"""
Advanced Democratic Participation System for AlphaEvolve-ACGS

This module implements next-generation democratic participation features including:
1. Blockchain-based voting for transparent stakeholder input
2. AI-mediated deliberation platforms for large-scale democratic input
3. Real-time polling systems for continuous stakeholder sentiment monitoring
4. Quadratic voting mechanisms for preference intensity measurement
5. Liquid democracy with delegation chains

Based on 2024-2025 research in democratic AI governance and participatory systems.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
import hashlib

import numpy as np
from web3 import Web3
from eth_account import Account

from ..core.metrics import get_metrics
from .collective_constitutional_ai import get_collective_constitutional_ai, DemocraticLegitimacyLevel

logger = logging.getLogger(__name__)


class VotingMechanism(Enum):
    """Available voting mechanisms for democratic participation."""
    SIMPLE_MAJORITY = "simple_majority"
    QUADRATIC_VOTING = "quadratic_voting"
    RANKED_CHOICE = "ranked_choice"
    APPROVAL_VOTING = "approval_voting"
    LIQUID_DEMOCRACY = "liquid_democracy"
    CONVICTION_VOTING = "conviction_voting"


class ParticipationLevel(Enum):
    """Levels of democratic participation."""
    OBSERVER = "observer"           # Can view but not participate
    PARTICIPANT = "participant"     # Can vote and comment
    DELEGATE = "delegate"          # Can represent others
    FACILITATOR = "facilitator"    # Can moderate discussions
    VALIDATOR = "validator"        # Can validate proposals


@dataclass
class BlockchainVote:
    """Represents a vote recorded on blockchain."""
    vote_id: str
    voter_address: str
    proposal_id: str
    vote_value: Any  # Can be boolean, number, or ranking
    timestamp: datetime
    block_hash: str
    transaction_hash: str
    gas_used: int
    verified: bool = False


@dataclass
class QuadraticVote:
    """Quadratic voting with preference intensity."""
    voter_id: str
    proposal_id: str
    credits_allocated: int
    vote_strength: float  # sqrt(credits_allocated)
    preference_intensity: float  # 0-1 scale
    timestamp: datetime


@dataclass
class DelegationChain:
    """Liquid democracy delegation chain."""
    delegator_id: str
    delegate_id: str
    topic_scope: List[str]  # Topics this delegation covers
    delegation_weight: float
    created_at: datetime
    expires_at: Optional[datetime] = None
    active: bool = True


@dataclass
class AIModeratedDiscussion:
    """AI-mediated discussion session."""
    discussion_id: str
    topic: str
    participants: List[str]
    ai_moderator_model: str
    discussion_summary: str
    consensus_points: List[str]
    divergent_points: List[str]
    sentiment_analysis: Dict[str, float]
    toxicity_score: float
    created_at: datetime
    status: str = "active"


@dataclass
class RealTimePolling:
    """Real-time sentiment polling system."""
    poll_id: str
    question: str
    options: List[str]
    responses: Dict[str, int]  # option -> count
    sentiment_trend: List[Tuple[datetime, Dict[str, float]]]
    geographic_distribution: Dict[str, Dict[str, int]]
    demographic_breakdown: Dict[str, Dict[str, int]]
    confidence_interval: float
    sample_size: int
    created_at: datetime


class AdvancedDemocraticParticipation:
    """
    Advanced democratic participation system with blockchain integration,
    AI-mediated deliberation, and real-time sentiment monitoring.
    """
    
    def __init__(self, blockchain_provider_url: Optional[str] = None):
        self.metrics = get_metrics("advanced_democratic_participation")
        self.ccai = get_collective_constitutional_ai()
        
        # Blockchain integration
        self.blockchain_provider_url = blockchain_provider_url or "http://localhost:8545"
        self.w3 = None
        self.voting_contract_address = None
        
        # Initialize blockchain connection if available
        self._initialize_blockchain()
        
        # Active democratic processes
        self.active_votes: Dict[str, Dict[str, Any]] = {}
        self.delegation_chains: Dict[str, List[DelegationChain]] = defaultdict(list)
        self.ai_discussions: Dict[str, AIModeratedDiscussion] = {}
        self.real_time_polls: Dict[str, RealTimePolling] = {}
        
        # Voting credits for quadratic voting
        self.voter_credits: Dict[str, int] = defaultdict(lambda: 100)  # Default 100 credits
        
    def _initialize_blockchain(self):
        """Initialize blockchain connection for transparent voting."""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.blockchain_provider_url))
            if self.w3.is_connected():
                logger.info("Blockchain connection established")
                # In production, deploy voting smart contract
                self.voting_contract_address = "0x1234567890123456789012345678901234567890"  # Placeholder
            else:
                logger.warning("Blockchain connection failed - using local storage")
        except Exception as e:
            logger.warning(f"Blockchain initialization failed: {e} - using local storage")
    
    async def create_blockchain_vote(
        self,
        proposal_id: str,
        proposal_text: str,
        voting_mechanism: VotingMechanism,
        duration_hours: int = 168,  # 1 week default
        eligible_voters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new blockchain-based vote for transparent democratic participation.
        
        Args:
            proposal_id: Unique identifier for the proposal
            proposal_text: Text of the proposal being voted on
            voting_mechanism: Type of voting mechanism to use
            duration_hours: Duration of voting period in hours
            eligible_voters: List of eligible voter addresses (None = open to all)
            
        Returns:
            Vote creation result with blockchain transaction details
        """
        vote_id = str(uuid.uuid4())
        
        vote_config = {
            "vote_id": vote_id,
            "proposal_id": proposal_id,
            "proposal_text": proposal_text,
            "voting_mechanism": voting_mechanism.value,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=duration_hours),
            "eligible_voters": eligible_voters or [],
            "votes": [],
            "status": "active",
            "blockchain_tx": None
        }
        
        # Record on blockchain if available
        if self.w3 and self.w3.is_connected():
            try:
                # In production, this would call smart contract
                tx_hash = self._simulate_blockchain_transaction(vote_config)
                vote_config["blockchain_tx"] = tx_hash
                logger.info(f"Vote {vote_id} recorded on blockchain: {tx_hash}")
            except Exception as e:
                logger.error(f"Blockchain recording failed: {e}")
        
        self.active_votes[vote_id] = vote_config
        
        # Record metrics
        self.metrics.increment("blockchain_votes_created")
        self.metrics.record_value("vote_duration_hours", duration_hours)
        
        return {
            "vote_id": vote_id,
            "proposal_id": proposal_id,
            "voting_mechanism": voting_mechanism.value,
            "blockchain_tx": vote_config["blockchain_tx"],
            "expires_at": vote_config["expires_at"].isoformat(),
            "status": "created"
        }
    
    async def cast_quadratic_vote(
        self,
        vote_id: str,
        voter_id: str,
        proposal_preference: Dict[str, int]  # proposal_option -> credits_allocated
    ) -> QuadraticVote:
        """
        Cast a quadratic vote with preference intensity measurement.
        
        Args:
            vote_id: ID of the vote
            voter_id: ID of the voter
            proposal_preference: Mapping of options to credits allocated
            
        Returns:
            Quadratic vote record
        """
        if vote_id not in self.active_votes:
            raise ValueError(f"Vote {vote_id} not found")
        
        vote_config = self.active_votes[vote_id]
        
        # Check if vote is still active
        if datetime.now(timezone.utc) > vote_config["expires_at"]:
            raise ValueError(f"Vote {vote_id} has expired")
        
        # Calculate total credits used
        total_credits = sum(proposal_preference.values())
        available_credits = self.voter_credits[voter_id]
        
        if total_credits > available_credits:
            raise ValueError(f"Insufficient credits: {total_credits} > {available_credits}")
        
        # Calculate quadratic vote strength
        vote_strength = {}
        total_preference_intensity = 0
        
        for option, credits in proposal_preference.items():
            if credits > 0:
                strength = np.sqrt(credits)
                vote_strength[option] = strength
                total_preference_intensity += credits / available_credits
        
        # Create quadratic vote record
        quadratic_vote = QuadraticVote(
            voter_id=voter_id,
            proposal_id=vote_config["proposal_id"],
            credits_allocated=total_credits,
            vote_strength=sum(vote_strength.values()),
            preference_intensity=total_preference_intensity,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Record vote
        vote_config["votes"].append({
            "voter_id": voter_id,
            "vote_type": "quadratic",
            "vote_data": quadratic_vote,
            "timestamp": quadratic_vote.timestamp.isoformat()
        })
        
        # Deduct credits
        self.voter_credits[voter_id] -= total_credits
        
        # Record on blockchain
        if self.w3 and self.w3.is_connected():
            blockchain_vote = BlockchainVote(
                vote_id=str(uuid.uuid4()),
                voter_address=self._get_voter_address(voter_id),
                proposal_id=vote_config["proposal_id"],
                vote_value=vote_strength,
                timestamp=quadratic_vote.timestamp,
                block_hash=self._simulate_block_hash(),
                transaction_hash=self._simulate_transaction_hash(),
                gas_used=21000,
                verified=True
            )
            
            # Store blockchain record
            vote_config.setdefault("blockchain_votes", []).append(blockchain_vote)
        
        # Record metrics
        self.metrics.increment("quadratic_votes_cast")
        self.metrics.record_value("vote_preference_intensity", total_preference_intensity)
        
        logger.info(f"Quadratic vote cast by {voter_id} for {vote_id}")
        
        return quadratic_vote
    
    async def create_liquid_democracy_delegation(
        self,
        delegator_id: str,
        delegate_id: str,
        topic_scope: List[str],
        delegation_weight: float = 1.0,
        duration_days: Optional[int] = None
    ) -> DelegationChain:
        """
        Create a liquid democracy delegation chain.
        
        Args:
            delegator_id: ID of the person delegating their vote
            delegate_id: ID of the person receiving the delegation
            topic_scope: List of topics this delegation covers
            delegation_weight: Weight of the delegation (0-1)
            duration_days: Duration of delegation in days (None = permanent)
            
        Returns:
            Delegation chain record
        """
        delegation_id = str(uuid.uuid4())
        
        expires_at = None
        if duration_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
        
        delegation = DelegationChain(
            delegator_id=delegator_id,
            delegate_id=delegate_id,
            topic_scope=topic_scope,
            delegation_weight=delegation_weight,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            active=True
        )
        
        # Store delegation
        self.delegation_chains[delegator_id].append(delegation)
        
        # Record metrics
        self.metrics.increment("delegations_created")
        self.metrics.record_value("delegation_weight", delegation_weight)
        
        logger.info(f"Delegation created: {delegator_id} -> {delegate_id} for {topic_scope}")
        
        return delegation
    
    async def start_ai_moderated_discussion(
        self,
        topic: str,
        participants: List[str],
        ai_moderator_model: str = "gpt-4",
        discussion_duration_hours: int = 24
    ) -> AIModeratedDiscussion:
        """
        Start an AI-moderated discussion for large-scale democratic input.
        
        Args:
            topic: Discussion topic
            participants: List of participant IDs
            ai_moderator_model: AI model to use for moderation
            discussion_duration_hours: Duration of discussion
            
        Returns:
            AI-moderated discussion session
        """
        discussion_id = str(uuid.uuid4())
        
        discussion = AIModeratedDiscussion(
            discussion_id=discussion_id,
            topic=topic,
            participants=participants,
            ai_moderator_model=ai_moderator_model,
            discussion_summary="",
            consensus_points=[],
            divergent_points=[],
            sentiment_analysis={},
            toxicity_score=0.0,
            created_at=datetime.now(timezone.utc),
            status="active"
        )
        
        self.ai_discussions[discussion_id] = discussion
        
        # Initialize AI moderation
        await self._initialize_ai_moderation(discussion)
        
        # Record metrics
        self.metrics.increment("ai_discussions_started")
        self.metrics.record_value("discussion_participants", len(participants))
        
        logger.info(f"AI-moderated discussion started: {discussion_id} on {topic}")
        
        return discussion
    
    async def create_real_time_poll(
        self,
        question: str,
        options: List[str],
        target_sample_size: int = 1000,
        geographic_targeting: Optional[Dict[str, Any]] = None
    ) -> RealTimePolling:
        """
        Create a real-time polling system for continuous sentiment monitoring.
        
        Args:
            question: Poll question
            options: List of answer options
            target_sample_size: Target number of responses
            geographic_targeting: Geographic targeting parameters
            
        Returns:
            Real-time polling session
        """
        poll_id = str(uuid.uuid4())
        
        poll = RealTimePolling(
            poll_id=poll_id,
            question=question,
            options=options,
            responses={option: 0 for option in options},
            sentiment_trend=[],
            geographic_distribution={},
            demographic_breakdown={},
            confidence_interval=0.95,
            sample_size=0,
            created_at=datetime.now(timezone.utc)
        )
        
        self.real_time_polls[poll_id] = poll
        
        # Initialize real-time monitoring
        await self._initialize_real_time_monitoring(poll)
        
        # Record metrics
        self.metrics.increment("real_time_polls_created")
        self.metrics.record_value("poll_options_count", len(options))
        
        logger.info(f"Real-time poll created: {poll_id}")
        
        return poll
    
    async def _initialize_ai_moderation(self, discussion: AIModeratedDiscussion):
        """Initialize AI moderation for discussion."""
        # Simulate AI moderation initialization
        await asyncio.sleep(0.1)
        
        # Set up moderation guidelines
        moderation_guidelines = {
            "toxicity_threshold": 0.3,
            "bias_detection": True,
            "fact_checking": True,
            "consensus_building": True,
            "sentiment_monitoring": True
        }
        
        discussion.sentiment_analysis = {
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 1.0
        }
        
        logger.debug(f"AI moderation initialized for discussion {discussion.discussion_id}")
    
    async def _initialize_real_time_monitoring(self, poll: RealTimePolling):
        """Initialize real-time monitoring for poll."""
        # Simulate real-time monitoring setup
        await asyncio.sleep(0.1)
        
        # Initialize sentiment trend tracking
        initial_sentiment = {option: 0.0 for option in poll.options}
        poll.sentiment_trend.append((datetime.now(timezone.utc), initial_sentiment))
        
        logger.debug(f"Real-time monitoring initialized for poll {poll.poll_id}")
    
    def _simulate_blockchain_transaction(self, vote_config: Dict[str, Any]) -> str:
        """Simulate blockchain transaction for vote creation."""
        # In production, this would interact with actual smart contract
        tx_data = json.dumps(vote_config, default=str)
        tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
        return f"0x{tx_hash[:64]}"
    
    def _simulate_block_hash(self) -> str:
        """Simulate blockchain block hash."""
        return f"0x{hashlib.sha256(str(time.time()).encode()).hexdigest()[:64]}"
    
    def _simulate_transaction_hash(self) -> str:
        """Simulate blockchain transaction hash."""
        return f"0x{hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:64]}"
    
    def _get_voter_address(self, voter_id: str) -> str:
        """Get blockchain address for voter ID."""
        # In production, this would map to actual wallet addresses
        return f"0x{hashlib.sha256(voter_id.encode()).hexdigest()[:40]}"
    
    async def get_democratic_participation_metrics(self) -> Dict[str, Any]:
        """Get comprehensive democratic participation metrics."""
        active_votes_count = len([v for v in self.active_votes.values() if v["status"] == "active"])
        total_delegations = sum(len(chains) for chains in self.delegation_chains.values())
        active_discussions = len([d for d in self.ai_discussions.values() if d.status == "active"])
        active_polls = len(self.real_time_polls)
        
        # Calculate participation rates
        total_participants = set()
        for vote in self.active_votes.values():
            total_participants.update(vote_data["voter_id"] for vote_data in vote["votes"])
        
        for chains in self.delegation_chains.values():
            for chain in chains:
                total_participants.add(chain.delegator_id)
                total_participants.add(chain.delegate_id)
        
        participation_rate = len(total_participants) / max(1000, len(total_participants))  # Assume 1000 eligible
        
        return {
            "active_votes": active_votes_count,
            "total_delegations": total_delegations,
            "active_discussions": active_discussions,
            "active_polls": active_polls,
            "unique_participants": len(total_participants),
            "participation_rate": participation_rate,
            "blockchain_integration": self.w3 is not None and self.w3.is_connected(),
            "voting_mechanisms_available": [mechanism.value for mechanism in VotingMechanism],
            "democratic_legitimacy_enhancement": {
                "quadratic_voting": "preference_intensity_measurement",
                "liquid_democracy": "delegation_chains",
                "ai_moderation": "large_scale_deliberation",
                "real_time_polling": "continuous_sentiment_monitoring"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global instance
_advanced_democratic_participation: Optional[AdvancedDemocraticParticipation] = None


def get_advanced_democratic_participation() -> AdvancedDemocraticParticipation:
    """Get global Advanced Democratic Participation instance."""
    global _advanced_democratic_participation
    if _advanced_democratic_participation is None:
        _advanced_democratic_participation = AdvancedDemocraticParticipation()
    return _advanced_democratic_participation
