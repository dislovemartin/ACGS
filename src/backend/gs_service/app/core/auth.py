# Import shared authentication utilities
from shared.auth import (
    get_current_user_from_token,
    get_current_active_user,
    require_admin,
    require_gs_admin,
    require_internal_service,
    RoleChecker,
    User
)

# GS service specific role checkers
require_gs_admin = require_gs_admin
require_synthesis_triggerer = RoleChecker(allowed_roles=["gs_admin", "internal_service", "admin"])

# Backward compatibility aliases for existing code
get_current_user_placeholder = get_current_user_from_token
get_current_active_user_placeholder = get_current_active_user

# Role checkers are imported from shared.auth above
