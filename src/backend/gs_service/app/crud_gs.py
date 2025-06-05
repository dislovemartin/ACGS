from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func as sql_func
from typing import List, Optional, Dict, Any
from shared.models import PolicyTemplate, Policy
from datetime import datetime, timezone, timedelta # For setting timestamps

# Placeholder for actual schema types if needed for validation or data shaping here,
# though typically Pydantic schemas are handled at the API layer.
# from . import schemas as gs_schemas 

async def create_policy_template(db: AsyncSession, template_data: Dict[str, Any], user_id: int) -> PolicyTemplate:
    # Ensure 'version' is handled, e.g., default to 1 or increment if updating
    # Ensure 'created_at' and 'updated_at' are set
    db_template = PolicyTemplate(
        **template_data,
        created_by_user_id=user_id,
        version=template_data.get('version', 1), # Default version or from data
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)
    return db_template

async def get_policy_template(db: AsyncSession, template_id: int) -> Optional[PolicyTemplate]:
    result = await db.execute(select(PolicyTemplate).filter(PolicyTemplate.id == template_id))
    return result.scalars().first()

async def get_policy_templates(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PolicyTemplate]:
    result = await db.execute(select(PolicyTemplate).offset(skip).limit(limit))
    return result.scalars().all()

async def count_policy_templates(db: AsyncSession) -> int:
    result = await db.execute(select(sql_func.count()).select_from(PolicyTemplate))
    return result.scalar_one()

async def update_policy_template(db: AsyncSession, template_id: int, update_data: Dict[str, Any]) -> Optional[PolicyTemplate]:
    # Increment version, update 'updated_at'
    # Exclude 'id', 'created_by_user_id', 'created_at' from update_data if present
    update_data.pop('id', None)
    update_data.pop('created_by_user_id', None)
    update_data.pop('created_at', None)
    
    # Get current template to access instance version
    current_template = await get_policy_template(db, template_id)
    if not current_template:
        return None

    stmt = (
        update(PolicyTemplate)
        .where(PolicyTemplate.id == template_id)
        .values(**update_data, updated_at=datetime.now(timezone.utc), version=current_template.version + 1)
        .returning(PolicyTemplate)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalars().first()

async def delete_policy_template(db: AsyncSession, template_id: int) -> bool:
    stmt = delete(PolicyTemplate).where(PolicyTemplate.id == template_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

async def create_direct_policy(db: AsyncSession, policy_data: Dict[str, Any], user_id: int) -> Policy:
    # Similar to create_policy_template, handles direct Policy creation
    db_policy = Policy(
        **policy_data,
        created_by_user_id=user_id,
        version=policy_data.get('version', 1),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(db_policy)
    await db.commit()
    await db.refresh(db_policy)
    return db_policy
    
async def create_policy_from_template_logic(db: AsyncSession, policy_data: Dict[str, Any], user_id: int) -> Optional[Policy]:
    template_id = policy_data.get("template_id")
    if not template_id:
        # This case should ideally be for direct policy creation, handled by create_direct_policy
        # or validated at API layer. If called here, it's an issue.
        return None 

    template = await get_policy_template(db, template_id)
    if not template:
        return None

    # Basic instantiation: Use template's default_content.
    # Real implementation might involve parameter substitution into template.default_content
    # using policy_data.get("customization_parameters") and template.parameters_schema.
    # For now, a simplified version:
    content = template.default_content 
    # If customization_parameters are provided, they should be used to render the content.
    # This is a complex step, for now, we use default_content.
    # A more advanced version would be:
    # rendered_content = render_template_content(template.default_content, policy_data.get("customization_parameters"), template.parameters_schema)

    # Create the policy instance
    # Name and description for the policy instance should come from policy_data
    new_policy_dict = {
        "name": policy_data.get("name"),
        "description": policy_data.get("description"),
        "content": content, # Use rendered_content in advanced version
        "status": policy_data.get("status", "draft_pending_synthesis"),
        "template_id": template_id,
        "customization_parameters": policy_data.get("customization_parameters"),
        "source_principle_ids": policy_data.get("source_principle_ids"),
        "created_by_user_id": user_id,
        "version": 1, # Initial version for a new policy instance
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Filter out None values to use SQLAlchemy defaults if applicable
    # new_policy_dict_cleaned = {k: v for k, v in new_policy_dict.items() if v is not None}
    
    db_policy = Policy(**new_policy_dict)
    db.add(db_policy)
    await db.commit()
    await db.refresh(db_policy)
    return db_policy

async def get_policy(db: AsyncSession, policy_id: int) -> Optional[Policy]:
    result = await db.execute(select(Policy).filter(Policy.id == policy_id))
    return result.scalars().first()

async def get_policies(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Policy]:
    result = await db.execute(select(Policy).offset(skip).limit(limit))
    return result.scalars().all()

async def count_policies(db: AsyncSession) -> int:
    result = await db.execute(select(sql_func.count()).select_from(Policy))
    return result.scalar_one()

async def update_policy(db: AsyncSession, policy_id: int, update_data: Dict[str, Any]) -> Optional[Policy]:
    # Similar to update_policy_template
    update_data.pop('id', None)
    update_data.pop('created_by_user_id', None)
    update_data.pop('created_at', None)
    update_data.pop('template_id', None) # template_id should not be changed after creation

    # Get current policy to access instance version
    current_policy = await get_policy(db, policy_id)
    if not current_policy:
        return None

    stmt = (
        update(Policy)
        .where(Policy.id == policy_id)
        .values(**update_data, updated_at=datetime.now(timezone.utc), version=current_policy.version + 1)
        .returning(Policy)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalars().first()

async def delete_policy(db: AsyncSession, policy_id: int) -> bool:
    stmt = delete(Policy).where(Policy.id == policy_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

# Helper for rendering content (very basic, placeholder)
# def render_template_content(template_str: str, params: Optional[Dict[str, Any]], schema: Optional[Dict[str, Any]]) -> str:
#     if not params:
#         return template_str
#     # Add simple replacement logic or use a templating engine like Jinja2
#     # This is a placeholder and would need validation against schema
#     rendered = template_str
#     for key, value in params.items():
#         rendered = rendered.replace(f"{{{key}}}", str(value))
#     return rendered
