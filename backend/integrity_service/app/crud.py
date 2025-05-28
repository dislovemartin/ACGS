from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional, Any

from . import models, schemas
from datetime import datetime

# --- PolicyRule CRUD operations ---

async def create_policy_rule(db: AsyncSession, policy_rule: schemas.PolicyRuleCreate) -> models.PolicyRule:
    db_policy_rule = models.PolicyRule(
        rule_content=policy_rule.rule_content,
        source_principle_ids=policy_rule.source_principle_ids,
        version=1, # Initial version
        verification_status="pending" # Initial status
    )
    db.add(db_policy_rule)
    await db.commit()
    await db.refresh(db_policy_rule)
    return db_policy_rule

async def get_policy_rule(db: AsyncSession, rule_id: int) -> Optional[models.PolicyRule]:
    result = await db.execute(select(models.PolicyRule).filter(models.PolicyRule.id == rule_id))
    return result.scalars().first()

async def get_policy_rules(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.PolicyRule]:
    result = await db.execute(select(models.PolicyRule).offset(skip).limit(limit))
    return result.scalars().all()

async def get_policy_rules_by_status(db: AsyncSession, status: str, skip: int = 0, limit: int = 100) -> List[models.PolicyRule]:
    result = await db.execute(
        select(models.PolicyRule).filter(models.PolicyRule.verification_status == status).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def update_policy_rule_status(db: AsyncSession, rule_id: int, status: str, new_version: bool = False) -> Optional[models.PolicyRule]:
    db_rule = await get_policy_rule(db, rule_id)
    if db_rule:
        db_rule.verification_status = status
        db_rule.verified_at = datetime.utcnow() # Set verification time when status changes
        if new_version: # Optionally increment version if status update implies a new version
            db_rule.version += 1
        await db.commit()
        await db.refresh(db_rule)
    return db_rule

async def update_policy_rule_content(db: AsyncSession, rule_id: int, rule_update: schemas.PolicyRuleUpdate) -> Optional[models.PolicyRule]:
    db_rule = await get_policy_rule(db, rule_id)
    if db_rule:
        update_data = rule_update.model_dump(exclude_unset=True)
        
        if "rule_content" in update_data and update_data["rule_content"] != db_rule.rule_content:
            db_rule.version += 1 # Increment version if content changes
            db_rule.verification_status = "pending" # Reset status if content changes
            db_rule.verified_at = None

        for key, value in update_data.items():
            setattr(db_rule, key, value)
            
        await db.commit()
        await db.refresh(db_rule)
    return db_rule

async def delete_policy_rule(db: AsyncSession, rule_id: int) -> Optional[models.PolicyRule]:
    db_rule = await get_policy_rule(db, rule_id)
    if db_rule:
        await db.delete(db_rule)
        await db.commit()
    return db_rule
    
async def count_policy_rules(db: AsyncSession, status: Optional[str] = None) -> int:
    stmt = select(func.count()).select_from(models.PolicyRule)
    if status:
        stmt = stmt.where(models.PolicyRule.verification_status == status)
    result = await db.execute(stmt)
    return result.scalar_one()

# --- AuditLog CRUD operations ---

async def create_audit_log(db: AsyncSession, log_entry: schemas.AuditLogCreate) -> models.AuditLog:
    db_log_entry = models.AuditLog(
        **log_entry.model_dump() # Pydantic v2+
    )
    db.add(db_log_entry)
    await db.commit()
    await db.refresh(db_log_entry)
    return db_log_entry

async def get_audit_log(db: AsyncSession, log_id: int) -> Optional[models.AuditLog]:
    result = await db.execute(select(models.AuditLog).filter(models.AuditLog.id == log_id))
    return result.scalars().first()

async def get_audit_logs(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100, 
    service_name: Optional[str] = None, 
    user_id: Optional[str] = None, 
    action: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[models.AuditLog]:
    stmt = select(models.AuditLog)
    if service_name:
        stmt = stmt.where(models.AuditLog.service_name == service_name)
    if user_id:
        stmt = stmt.where(models.AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(models.AuditLog.action == action)
    if start_time:
        stmt = stmt.where(models.AuditLog.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(models.AuditLog.timestamp <= end_time)
        
    result = await db.execute(stmt.order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit))
    return result.scalars().all()

async def count_audit_logs(
    db: AsyncSession,
    service_name: Optional[str] = None, 
    user_id: Optional[str] = None, 
    action: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> int:
    stmt = select(func.count()).select_from(models.AuditLog)
    if service_name:
        stmt = stmt.where(models.AuditLog.service_name == service_name)
    if user_id:
        stmt = stmt.where(models.AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(models.AuditLog.action == action)
    if start_time:
        stmt = stmt.where(models.AuditLog.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(models.AuditLog.timestamp <= end_time)
    result = await db.execute(stmt)
    return result.scalar_one()
