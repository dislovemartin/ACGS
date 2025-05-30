from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.crud import (
    create_ac_meta_rule, get_ac_meta_rule, get_ac_meta_rules, update_ac_meta_rule,
    create_ac_amendment, get_ac_amendment, get_ac_amendments, update_ac_amendment,
    create_ac_amendment_vote, get_ac_amendment_votes,
    create_ac_amendment_comment, get_ac_amendment_comments,
    create_ac_conflict_resolution, get_ac_conflict_resolution, get_ac_conflict_resolutions, update_ac_conflict_resolution
)
from app import schemas
from shared.database import get_async_db
from app.core.auth import get_current_active_user_placeholder, require_admin_role, require_constitutional_council_role, User

router = APIRouter()

# AC Meta-Rules endpoints
@router.post("/meta-rules", response_model=schemas.ACMetaRule, status_code=status.HTTP_201_CREATED)
async def create_meta_rule_endpoint(
    meta_rule: schemas.ACMetaRuleCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_role)
):
    """Create a new AC meta-rule (requires admin role)"""
    created_meta_rule = await create_ac_meta_rule(db=db, meta_rule=meta_rule, user_id=current_user.id)
    return created_meta_rule

@router.get("/meta-rules", response_model=List[schemas.ACMetaRule])
async def list_meta_rules_endpoint(
    rule_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_placeholder)
):
    """List AC meta-rules with optional filtering by rule type"""
    meta_rules = await get_ac_meta_rules(db, rule_type=rule_type, skip=skip, limit=limit)
    return meta_rules

@router.get("/meta-rules/{meta_rule_id}", response_model=schemas.ACMetaRule)
async def get_meta_rule_endpoint(
    meta_rule_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_placeholder)
):
    """Get a specific AC meta-rule by ID"""
    meta_rule = await get_ac_meta_rule(db, meta_rule_id=meta_rule_id)
    if meta_rule is None:
        raise HTTPException(status_code=404, detail="Meta-rule not found")
    return meta_rule

@router.put("/meta-rules/{meta_rule_id}", response_model=schemas.ACMetaRule)
async def update_meta_rule_endpoint(
    meta_rule_id: int,
    meta_rule_update: schemas.ACMetaRuleUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_role)
):
    """Update an AC meta-rule (requires admin role)"""
    updated_meta_rule = await update_ac_meta_rule(db=db, meta_rule_id=meta_rule_id, meta_rule_update=meta_rule_update)
    if updated_meta_rule is None:
        raise HTTPException(status_code=404, detail="Meta-rule not found")
    return updated_meta_rule

# AC Amendments endpoints
@router.post("/amendments", response_model=schemas.ACAmendment, status_code=status.HTTP_201_CREATED)
async def create_amendment_endpoint(
    amendment: schemas.ACAmendmentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_constitutional_council_role)
):
    """Create a new AC amendment proposal (requires Constitutional Council membership)"""
    created_amendment = await create_ac_amendment(db=db, amendment=amendment, user_id=current_user.id)
    return created_amendment

@router.get("/amendments", response_model=List[schemas.ACAmendment])
async def list_amendments_endpoint(
    status: Optional[str] = None,
    principle_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_placeholder)
):
    """List AC amendments with optional filtering"""
    amendments = await get_ac_amendments(db, status=status, principle_id=principle_id, skip=skip, limit=limit)
    return amendments

@router.get("/amendments/{amendment_id}", response_model=schemas.ACAmendment)
async def get_amendment_endpoint(
    amendment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_placeholder)
):
    """Get a specific AC amendment by ID"""
    amendment = await get_ac_amendment(db, amendment_id=amendment_id)
    if amendment is None:
        raise HTTPException(status_code=404, detail="Amendment not found")
    return amendment

@router.put("/amendments/{amendment_id}", response_model=schemas.ACAmendment)
async def update_amendment_endpoint(
    amendment_id: int,
    amendment_update: schemas.ACAmendmentUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_constitutional_council_role)
):
    """Update an AC amendment (requires Constitutional Council membership)"""
    updated_amendment = await update_ac_amendment(db=db, amendment_id=amendment_id, amendment_update=amendment_update)
    if updated_amendment is None:
        raise HTTPException(status_code=404, detail="Amendment not found")
    return updated_amendment

# AC Amendment Voting endpoints
@router.post("/amendments/{amendment_id}/votes", response_model=schemas.ACAmendmentVote, status_code=status.HTTP_201_CREATED)
async def vote_on_amendment_endpoint(
    amendment_id: int,
    vote_data: schemas.ACAmendmentVoteBase,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_constitutional_council_role)
):
    """Vote on an AC amendment (requires Constitutional Council membership)"""
    vote_create = schemas.ACAmendmentVoteCreate(amendment_id=amendment_id, **vote_data.model_dump())
    try:
        created_vote = await create_ac_amendment_vote(db=db, vote=vote_create, voter_id=current_user.id)
        return created_vote
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/amendments/{amendment_id}/votes", response_model=List[schemas.ACAmendmentVote])
async def get_amendment_votes_endpoint(
    amendment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_placeholder)
):
    """Get all votes for a specific amendment"""
    votes = await get_ac_amendment_votes(db, amendment_id=amendment_id)
    return votes

# AC Amendment Comments endpoints
@router.post("/amendments/{amendment_id}/comments", response_model=schemas.ACAmendmentComment, status_code=status.HTTP_201_CREATED)
async def create_amendment_comment_endpoint(
    amendment_id: int,
    comment_data: schemas.ACAmendmentCommentBase,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[User] = Depends(get_current_active_user_placeholder)
):
    """Create a comment on an AC amendment (public participation)"""
    comment_create = schemas.ACAmendmentCommentCreate(amendment_id=amendment_id, **comment_data.model_dump())
    commenter_id = current_user.id if current_user else None
    created_comment = await create_ac_amendment_comment(db=db, comment=comment_create, commenter_id=commenter_id)
    return created_comment

@router.get("/amendments/{amendment_id}/comments", response_model=List[schemas.ACAmendmentComment])
async def get_amendment_comments_endpoint(
    amendment_id: int,
    is_public: bool = True,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[User] = Depends(get_current_active_user_placeholder)
):
    """Get comments for a specific amendment"""
    comments = await get_ac_amendment_comments(db, amendment_id=amendment_id, is_public=is_public)
    return comments

# AC Conflict Resolution endpoints
@router.post("/conflict-resolutions", response_model=schemas.ACConflictResolution, status_code=status.HTTP_201_CREATED)
async def create_conflict_resolution_endpoint(
    conflict: schemas.ACConflictResolutionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_role)
):
    """Create a new AC conflict resolution (requires admin role)"""
    created_conflict = await create_ac_conflict_resolution(db=db, conflict=conflict, user_id=current_user.id)
    return created_conflict

@router.get("/conflict-resolutions", response_model=List[schemas.ACConflictResolution])
async def list_conflict_resolutions_endpoint(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_placeholder)
):
    """List AC conflict resolutions with optional filtering"""
    conflicts = await get_ac_conflict_resolutions(db, status=status, severity=severity, skip=skip, limit=limit)
    return conflicts

@router.get("/conflict-resolutions/{conflict_id}", response_model=schemas.ACConflictResolution)
async def get_conflict_resolution_endpoint(
    conflict_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_placeholder)
):
    """Get a specific AC conflict resolution by ID"""
    conflict = await get_ac_conflict_resolution(db, conflict_id=conflict_id)
    if conflict is None:
        raise HTTPException(status_code=404, detail="Conflict resolution not found")
    return conflict

@router.put("/conflict-resolutions/{conflict_id}", response_model=schemas.ACConflictResolution)
async def update_conflict_resolution_endpoint(
    conflict_id: int,
    conflict_update: schemas.ACConflictResolutionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin_role)
):
    """Update an AC conflict resolution (requires admin role)"""
    updated_conflict = await update_ac_conflict_resolution(db=db, conflict_id=conflict_id, conflict_update=conflict_update)
    if updated_conflict is None:
        raise HTTPException(status_code=404, detail="Conflict resolution not found")
    return updated_conflict
