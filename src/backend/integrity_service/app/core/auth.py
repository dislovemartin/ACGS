# Import shared authentication utilities
from shared.auth import (
    get_current_user_from_token,
    get_current_active_user,
    require_admin,
    require_auditor,
    require_integrity_admin,
    require_internal_service,
    RoleChecker,
    User
)

# Integrity service specific role checkers
require_integrity_admin = require_integrity_admin
require_auditor = require_auditor
require_internal_service = require_internal_service

# Backward compatibility aliases for existing code
get_current_user_placeholder = get_current_user_from_token
get_current_active_user_placeholder = get_current_active_user

# Role checkers are imported from shared.auth above
