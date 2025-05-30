from fastapi import APIRouter
from app.api.v1.endpoints import router as auth_router # Import the router from endpoints.py
from app.api.v1.endpoints.users import router as users_router # Import the users router

api_router = APIRouter()

# Include the authentication router
# The prefix "/auth" here, combined with API_V1_STR in main.py, will make routes like /api/v1/auth/token
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Authorization"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
