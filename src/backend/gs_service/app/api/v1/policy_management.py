# backend/gs_service/app/api/v1/policy_management.py (New file)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Import schemas and CRUD functions using relative paths
from ... import schemas as gs_schemas # Goes up 3 levels from v1 to app
from ...crud_gs import ( # Goes up 3 levels from v1 to app for crud_gs
    create_policy_template, get_policy_template, get_policy_templates, count_policy_templates,
    update_policy_template, delete_policy_template,
    create_policy_from_template_logic, create_direct_policy,
    get_policy, get_policies, count_policies,
    update_policy as update_policy_crud, delete_policy as delete_policy_crud
)


from src.backend.shared.database import get_async_db
# from src.backend.shared.models import User # For auth dependency if needed
# from src.backend.app.core.auth import require_gs_admin # Placeholder for auth

router = APIRouter()

# --- Policy Template Endpoints ---
@router.post("/templates/", response_model=gs_schemas.GSTemplateResponse, status_code=status.HTTP_201_CREATED)
async def api_create_policy_template(
    template_in: gs_schemas.GSTemplateCreate,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_gs_admin) # Protect endpoint
):
    user_id = 1 # Placeholder, replace with authenticated user ID
    # Consider adding a check for existing template name if it should be unique
    # existing_template = await get_template_by_name(db, name=template_in.name) # Requires get_template_by_name in crud
    # if existing_template:
    #     raise HTTPException(status_code=400, detail="PolicyTemplate with this name already exists.")
    created_template = await create_policy_template(db, template_data=template_in.model_dump(), user_id=user_id)
    return created_template

@router.get("/templates/{template_id}", response_model=gs_schemas.GSTemplateResponse)
async def api_read_policy_template(template_id: int, db: AsyncSession = Depends(get_async_db)):
    db_template = await get_policy_template(db, template_id)
    if db_template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PolicyTemplate not found")
    return db_template

@router.get("/templates/", response_model=gs_schemas.GSTemplateListResponse)
async def api_list_policy_templates(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)):
    templates = await get_policy_templates(db, skip=skip, limit=limit)
    total = await count_policy_templates(db)
    return gs_schemas.GSTemplateListResponse(templates=templates, total=total)

@router.put("/templates/{template_id}", response_model=gs_schemas.GSTemplateResponse)
async def api_update_policy_template(
    template_id: int,
    template_update: gs_schemas.GSTemplateUpdate, # Use a specific update schema
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_gs_admin)
):
    # Ensure template_update does not contain fields that shouldn't be updated (e.g. id, user_id)
    update_data = template_update.model_dump(exclude_unset=True)
    updated_template = await update_policy_template(db, template_id=template_id, update_data=update_data)
    if not updated_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PolicyTemplate not found or update failed")
    return updated_template

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_policy_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_gs_admin)
):
    success = await delete_policy_template(db, template_id=template_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PolicyTemplate not found")
    return None # For 204 No Content

# --- Policy Instance Endpoints ---
@router.post("/policies/", response_model=gs_schemas.GSPolicyResponse, status_code=status.HTTP_201_CREATED)
async def api_create_policy(
    policy_req: gs_schemas.GSPolicyCreate,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_gs_admin)
):
    user_id = 1 # Placeholder
    new_policy = None
    
    # Validate GSPolicyCreate (done by Pydantic based on schema's validator)
    # policy_req_dict = policy_req.model_dump() # No longer needed due to validator in schema

    if policy_req.template_id:
        # Ensure customization_parameters are passed if template expects them
        new_policy = await create_policy_from_template_logic(db, policy_data=policy_req.model_dump(), user_id=user_id)
        if not new_policy: # Could be due to template_id not found
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"PolicyTemplate with ID {policy_req.template_id} not found or policy creation failed.")
    elif policy_req.content: # Direct content creation
        # Ensure 'name' is provided for direct creation, as it's not from a template
        if not policy_req.name: # Name is not optional in GSPolicyBase, so Pydantic handles this. This is redundant.
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Policy name is required for direct creation.")
        new_policy = await create_direct_policy(db, policy_data=policy_req.model_dump(), user_id=user_id)
    else:
        # This case should be caught by GSPolicyCreate's validator, but as a fallback:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either template_id (with parameters) or direct content (with name) must be provided.")
    
    if not new_policy: # General fallback if creation failed for other reasons
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create policy.")
        
    return new_policy
    
@router.get("/policies/{policy_id}", response_model=gs_schemas.GSPolicyResponse)
async def api_read_policy(policy_id: int, db: AsyncSession = Depends(get_async_db)):
    db_policy = await get_policy(db, policy_id)
    if db_policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return db_policy

@router.get("/policies/", response_model=gs_schemas.GSPolicyListResponse)
async def api_list_policies(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)):
    policies = await get_policies(db, skip=skip, limit=limit)
    total = await count_policies(db)
    return gs_schemas.GSPolicyListResponse(policies=policies, total=total)

@router.put("/policies/{policy_id}", response_model=gs_schemas.GSPolicyResponse)
async def api_update_policy(
    policy_id: int,
    policy_update: gs_schemas.GSPolicyUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_gs_admin)
):
    update_data = policy_update.model_dump(exclude_unset=True)
    # Prevent changing template_id if it's part of the model and set during creation
    if 'template_id' in update_data and update_data['template_id'] is not None:
        # Check if the existing policy has a different template_id or if it was None
        existing_policy = await get_policy(db, policy_id)
        if existing_policy and existing_policy.template_id != update_data['template_id']:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change template_id of an existing policy.")
        # If template_id was None and now is being set, that's also usually not allowed post-creation.
        # However, if the policy was created directly and now being linked, it's a design choice.
        # For now, assume template_id is immutable post-creation if it was set.

    updated_policy = await update_policy_crud(db, policy_id=policy_id, update_data=update_data)
    if not updated_policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found or update failed")
    return updated_policy

@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_gs_admin)
):
    success = await delete_policy_crud(db, policy_id=policy_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return None
