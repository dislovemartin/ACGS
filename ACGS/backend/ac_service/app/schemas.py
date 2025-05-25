# ACGS/backend/ac_service/app/schemas.py
# This service primarily uses schemas from the `shared` directory (shared.schemas).
# This file can be used for service-specific request/response models or
# for re-exporting shared schemas for local clarity if desired.

from pydantic import BaseModel # For local User placeholder
from typing import List, Optional # For local User placeholder

# Re-exporting from shared for clarity within this service's context,
# or define service-specific variations if needed.
try:
    # Import specific principle schemas from shared.schemas
    from shared.schemas import (
        PrincipleBase, PrincipleCreate, PrincipleUpdate, PrincipleResponse, PrincipleListResponse
    )
except ImportError:
    # Fallback for local dev
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from shared.schemas import (
        PrincipleBase, PrincipleCreate, PrincipleUpdate, PrincipleResponse, PrincipleListResponse
    )


# Placeholder User schema for core.auth.py dependencies
# This is a minimal User schema for the purpose of internal auth checking within ac_service.
# It does NOT represent the full User schema used by auth_service or stored in the DB.
class User(BaseModel): 
    id: int # Or str, depending on what core.auth.py expects
    username: str
    roles: List[str] = []


# Expose the imported/defined schemas for use within ac_service's modules (e.g., api, crud)
__all__ = [
    "PrincipleBase",
    "PrincipleCreate",
    "PrincipleUpdate",
    "PrincipleResponse",
    "PrincipleListResponse",
    "User", # Expose the local User placeholder for auth dependencies
]
