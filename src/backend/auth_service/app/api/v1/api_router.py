from fastapi import APIRouter
# Import the router from endpoints.py file (now that endpoints directory is removed)
from .endpoints import router as auth_router
# Note: users router was in the endpoints directory which we removed
# For now, we'll just use the main auth router

api_router = APIRouter()

# Include the authentication router
# The prefix "/auth" here, combined with API_V1_STR in main.py, will make routes like /api/v1/auth/token
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Authorization"])
# Users router was removed with the endpoints directory - can be added back later if needed
