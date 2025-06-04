from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from . import models, schemas

# Principle CRUD operations

async def create_principle(db: AsyncSession, principle: schemas.PrincipleCreate, user_id: Optional[int] = None) -> models.Principle:
    db_principle = models.Principle(
        **principle.model_dump(),  # Use model_dump() for Pydantic v2+
        created_by_user_id=user_id,
        version=1, # Initial version
        status="draft" # Initial status
    )
    db.add(db_principle)
    await db.commit()
    await db.refresh(db_principle)
    return db_principle

async def get_principle(db: AsyncSession, principle_id: int) -> Optional[models.Principle]:
    result = await db.execute(select(models.Principle).filter(models.Principle.id == principle_id))
    return result.scalars().first()

async def get_principle_by_name(db: AsyncSession, name: str) -> Optional[models.Principle]:
    # This simple version gets the first principle with this name.
    # For versioning, you might want the latest version or a specific one.
    result = await db.execute(select(models.Principle).filter(models.Principle.name == name).order_by(models.Principle.version.desc()))
    return result.scalars().first()

async def get_principles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Principle]:
    result = await db.execute(select(models.Principle).offset(skip).limit(limit))
    return result.scalars().all()

async def update_principle(db: AsyncSession, principle_id: int, principle_update: schemas.PrincipleUpdate) -> Optional[models.Principle]:
    db_principle = await get_principle(db, principle_id)
    if db_principle:
        update_data = principle_update.model_dump(exclude_unset=True) # Pydantic v2+
        
        # Simple version increment if content changes, or could be more complex
        if "content" in update_data and update_data["content"] != db_principle.content:
            # Increment version using instance attribute, not class attribute
            db_principle.version = db_principle.version + 1
            # Optionally, reset status to 'draft' or handle as per business logic
            # db_principle.status = "draft"

        for key, value in update_data.items():
            setattr(db_principle, key, value)
        
        await db.commit()
        await db.refresh(db_principle)
    return db_principle

async def delete_principle(db: AsyncSession, principle_id: int) -> Optional[models.Principle]:
    db_principle = await get_principle(db, principle_id)
    if db_principle:
        # Instead of deleting, we can mark as "deprecated" or "deleted"
        # db_principle.status = "deleted" 
        # await db.commit()
        # await db.refresh(db_principle)
        # For actual deletion:
        await db.delete(db_principle)
        await db.commit()
    return db_principle

async def count_principles(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(models.Principle))
    return result.scalar_one()

# Enhanced Principle CRUD operations for Phase 1 Constitutional Features

async def get_principles_by_category(db: AsyncSession, category: str, skip: int = 0, limit: int = 100) -> List[models.Principle]:
    """Get principles filtered by category."""
    result = await db.execute(
        select(models.Principle)
        .filter(models.Principle.category == category)
        .offset(skip)
        .limit(limit)
        .order_by(models.Principle.priority_weight.desc().nulls_last())
    )
    return result.scalars().all()

async def get_principles_by_scope(db: AsyncSession, scope_context: str, skip: int = 0, limit: int = 100) -> List[models.Principle]:
    """Get principles that apply to a specific scope context."""
    result = await db.execute(
        select(models.Principle)
        .filter(models.Principle.scope.contains([scope_context]))
        .offset(skip)
        .limit(limit)
        .order_by(models.Principle.priority_weight.desc().nulls_last())
    )
    return result.scalars().all()

async def get_principles_by_priority_range(db: AsyncSession, min_priority: float = 0.0, max_priority: float = 1.0, skip: int = 0, limit: int = 100) -> List[models.Principle]:
    """Get principles within a specific priority weight range."""
    result = await db.execute(
        select(models.Principle)
        .filter(
            models.Principle.priority_weight >= min_priority,
            models.Principle.priority_weight <= max_priority
        )
        .offset(skip)
        .limit(limit)
        .order_by(models.Principle.priority_weight.desc())
    )
    return result.scalars().all()

async def search_principles_by_keywords(db: AsyncSession, keywords: List[str], skip: int = 0, limit: int = 100) -> List[models.Principle]:
    """Search principles by keywords."""
    # Use PostgreSQL JSONB contains operator to find principles with any of the keywords
    result = await db.execute(
        select(models.Principle)
        .filter(models.Principle.keywords.op('?|')(keywords))
        .offset(skip)
        .limit(limit)
        .order_by(models.Principle.priority_weight.desc().nulls_last())
    )
    return result.scalars().all()

async def get_active_principles_for_context(db: AsyncSession, context: str, category: Optional[str] = None) -> List[models.Principle]:
    """Get active principles applicable to a specific context, optionally filtered by category."""
    query = select(models.Principle).filter(
        models.Principle.status == "active",
        models.Principle.scope.contains([context])
    )

    if category:
        query = query.filter(models.Principle.category == category)

    query = query.order_by(models.Principle.priority_weight.desc().nulls_last())

    result = await db.execute(query)
    return result.scalars().all()

# Constitutional Council CRUD operations

# AC Meta-Rules CRUD
async def create_ac_meta_rule(db: AsyncSession, meta_rule: schemas.ACMetaRuleCreate, user_id: Optional[int] = None) -> models.ACMetaRule:
    db_meta_rule = models.ACMetaRule(
        **meta_rule.model_dump(),
        created_by_user_id=user_id,
        status="active"
    )
    db.add(db_meta_rule)
    await db.commit()
    await db.refresh(db_meta_rule)
    return db_meta_rule

async def get_ac_meta_rule(db: AsyncSession, meta_rule_id: int) -> Optional[models.ACMetaRule]:
    result = await db.execute(select(models.ACMetaRule).filter(models.ACMetaRule.id == meta_rule_id))
    return result.scalars().first()

async def get_ac_meta_rules(db: AsyncSession, rule_type: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.ACMetaRule]:
    query = select(models.ACMetaRule)
    if rule_type:
        query = query.filter(models.ACMetaRule.rule_type == rule_type)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def update_ac_meta_rule(db: AsyncSession, meta_rule_id: int, meta_rule_update: schemas.ACMetaRuleUpdate) -> Optional[models.ACMetaRule]:
    db_meta_rule = await get_ac_meta_rule(db, meta_rule_id)
    if db_meta_rule:
        update_data = meta_rule_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_meta_rule, key, value)
        await db.commit()
        await db.refresh(db_meta_rule)
    return db_meta_rule

# AC Amendments CRUD with enhanced scalability support
async def create_ac_amendment(db: AsyncSession, amendment: schemas.ACAmendmentCreate, user_id: int) -> models.ACAmendment:
    """Create AC amendment with co-evolution and scalability support."""
    from .core.constitutional_council_scalability import RapidCoEvolutionHandler, ScalabilityConfig, CoEvolutionMode
    from .core.amendment_state_machine import amendment_state_machine, WorkflowContext, AmendmentEvent

    # Determine urgency level
    urgency_level = CoEvolutionMode.RAPID if amendment.rapid_processing_requested else CoEvolutionMode.STANDARD

    # Initialize scalability handler if needed
    config = ScalabilityConfig()
    handler = RapidCoEvolutionHandler(config)
    await handler.initialize()

    # Use rapid processing if requested
    if amendment.rapid_processing_requested:
        result = await handler.process_rapid_amendment(db, amendment, urgency_level)
        if result["success"]:
            return await get_ac_amendment(db, result["amendment_id"])
        else:
            raise ValueError(f"Failed to create rapid amendment: {result['error']}")

    # Standard amendment creation with enhanced fields
    db_amendment = models.ACAmendment(
        **amendment.model_dump(),
        proposed_by_user_id=user_id,
        status="proposed",
        version=1,
        workflow_state="proposed",
        state_transitions=[{
            "from_state": None,
            "to_state": "proposed",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id
        }]
    )
    db.add(db_amendment)
    await db.commit()
    await db.refresh(db_amendment)

    # Initialize workflow
    context = WorkflowContext(
        amendment_id=db_amendment.id,
        user_id=user_id,
        urgency_level=amendment.urgency_level or "normal",
        constitutional_significance=amendment.constitutional_significance or "normal",
        metadata={"created_via": "standard_process"}
    )

    return db_amendment

async def get_ac_amendment(db: AsyncSession, amendment_id: int) -> Optional[models.ACAmendment]:
    result = await db.execute(select(models.ACAmendment).filter(models.ACAmendment.id == amendment_id))
    return result.scalars().first()

async def get_ac_amendments(db: AsyncSession, status: Optional[str] = None, principle_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models.ACAmendment]:
    query = select(models.ACAmendment)
    if status:
        query = query.filter(models.ACAmendment.status == status)
    if principle_id:
        query = query.filter(models.ACAmendment.principle_id == principle_id)
    query = query.offset(skip).limit(limit).order_by(models.ACAmendment.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def update_ac_amendment(db: AsyncSession, amendment_id: int, amendment_update: schemas.ACAmendmentUpdate) -> Optional[models.ACAmendment]:
    db_amendment = await get_ac_amendment(db, amendment_id)
    if db_amendment:
        update_data = amendment_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_amendment, key, value)
        await db.commit()
        await db.refresh(db_amendment)
    return db_amendment

# AC Amendment Votes CRUD
async def create_ac_amendment_vote(db: AsyncSession, vote: schemas.ACAmendmentVoteCreate, voter_id: int) -> models.ACAmendmentVote:
    # Check if user already voted on this amendment
    existing_vote = await db.execute(
        select(models.ACAmendmentVote).filter(
            models.ACAmendmentVote.amendment_id == vote.amendment_id,
            models.ACAmendmentVote.voter_id == voter_id
        )
    )
    if existing_vote.scalars().first():
        raise ValueError("User has already voted on this amendment")

    db_vote = models.ACAmendmentVote(
        **vote.model_dump(),
        voter_id=voter_id
    )
    db.add(db_vote)

    # Update vote counts on the amendment
    amendment = await get_ac_amendment(db, vote.amendment_id)
    if amendment:
        if vote.vote == "for":
            amendment.votes_for += 1
        elif vote.vote == "against":
            amendment.votes_against += 1
        elif vote.vote == "abstain":
            amendment.votes_abstain += 1

    await db.commit()
    await db.refresh(db_vote)
    return db_vote

async def get_ac_amendment_votes(db: AsyncSession, amendment_id: int) -> List[models.ACAmendmentVote]:
    result = await db.execute(
        select(models.ACAmendmentVote).filter(models.ACAmendmentVote.amendment_id == amendment_id)
    )
    return result.scalars().all()

# AC Amendment Comments CRUD
async def create_ac_amendment_comment(db: AsyncSession, comment: schemas.ACAmendmentCommentCreate, commenter_id: Optional[int] = None) -> models.ACAmendmentComment:
    db_comment = models.ACAmendmentComment(
        **comment.model_dump(),
        commenter_id=commenter_id
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment

async def get_ac_amendment_comments(db: AsyncSession, amendment_id: int, is_public: bool = True) -> List[models.ACAmendmentComment]:
    query = select(models.ACAmendmentComment).filter(models.ACAmendmentComment.amendment_id == amendment_id)
    if is_public:
        query = query.filter(models.ACAmendmentComment.is_public == True)
    query = query.order_by(models.ACAmendmentComment.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

# AC Conflict Resolution CRUD
async def create_ac_conflict_resolution(db: AsyncSession, conflict: schemas.ACConflictResolutionCreate, user_id: Optional[int] = None) -> models.ACConflictResolution:
    db_conflict = models.ACConflictResolution(
        **conflict.model_dump(),
        identified_by_user_id=user_id,
        status="identified"
    )
    db.add(db_conflict)
    await db.commit()
    await db.refresh(db_conflict)
    return db_conflict

async def get_ac_conflict_resolution(db: AsyncSession, conflict_id: int) -> Optional[models.ACConflictResolution]:
    result = await db.execute(select(models.ACConflictResolution).filter(models.ACConflictResolution.id == conflict_id))
    return result.scalars().first()

async def get_ac_conflict_resolutions(db: AsyncSession, status: Optional[str] = None, severity: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[models.ACConflictResolution]:
    query = select(models.ACConflictResolution)
    if status:
        query = query.filter(models.ACConflictResolution.status == status)
    if severity:
        query = query.filter(models.ACConflictResolution.severity == severity)
    query = query.offset(skip).limit(limit).order_by(models.ACConflictResolution.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def update_ac_conflict_resolution(db: AsyncSession, conflict_id: int, conflict_update: schemas.ACConflictResolutionUpdate) -> Optional[models.ACConflictResolution]:
    db_conflict = await get_ac_conflict_resolution(db, conflict_id)
    if db_conflict:
        update_data = conflict_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_conflict, key, value)
        await db.commit()
        await db.refresh(db_conflict)
    return db_conflict

async def delete_ac_conflict_resolution(db: AsyncSession, conflict_id: int) -> bool:
    """Delete a conflict resolution by ID."""
    db_conflict = await get_ac_conflict_resolution(db, conflict_id)
    if db_conflict:
        await db.delete(db_conflict)
        await db.commit()
        return True
    return False

async def get_ac_principles_by_ids(db: AsyncSession, principle_ids: List[int]) -> List[models.Principle]:
    """Get multiple AC principles by their IDs."""
    result = await db.execute(
        select(models.Principle).filter(models.Principle.id.in_(principle_ids))
    )
    return result.scalars().all()
