# backend/auth_service/app/main.py
import logging
import sys

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
# Temporarily create a simple test router to debug the issue
from fastapi import APIRouter
test_router = APIRouter()

@test_router.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint working"}

# Import the auth router directly from endpoints to avoid double prefix issue
from app.api.v1.endpoints import router as auth_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(settings.PROJECT_NAME)

# Initialize Limiter - temporarily disabled for debugging
# limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/openapi.json",
)

# Store limiter in app state - temporarily disabled for debugging
# app.state.limiter = limiter

# Add exception handlers - temporarily disabled for debugging
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CSRF Protection Settings
class CsrfSettings(BaseModel):
    secret_key: str = settings.CSRF_SECRET_KEY
    cookie_samesite: str = "lax"
    # cookie_secure: bool = settings.ENVIRONMENT != "development" # Handled by SECURE_COOKIE in endpoints.py for token cookies
    # header_name: str = "X-CSRF-Token" # Default is "X-CSRF-Token"

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

@app.exception_handler(CsrfProtectError)
async def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    logger.warning(f"CSRF protection error: {exc.message} for request: {request.url}")
    return JSONResponse(
        status_code=exc.status_code, # Typically 403
        content={"detail": exc.message},
    )

# Add CORS middleware
cors_origins = settings.cors_origins_list
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True, # Crucial for cookies, including CSRF and auth tokens
        allow_methods=["*"],
        allow_headers=["*", "X-CSRF-Token"], # Ensure "X-CSRF-Token" or custom CSRF header is allowed
    )

# Include the test router to debug the issue
app.include_router(
    test_router,
    prefix="/auth",
    tags=["Test"]
)

# Include the authentication router
# The prefix here should match the path used for refresh token cookie
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication & Authorization"]
)

# If api_v1_router from app.api.v1.api_router.py was for other general v1 routes,
# it could be included as well, e.g.:
# from app.api.v1.api_router import api_router as other_v1_router
# app.include_router(other_v1_router, prefix=settings.API_V1_STR)
# For this task, we are focusing on the auth_router.
# The original line was: app.include_router(api_v1_router, prefix=settings.API_V1_STR)
# This is removed as auth_router is now more specific.


@app.get("/", status_code=status.HTTP_200_OK)
async def root(request: Request) -> dict:
    """
    Root GET endpoint. Provides basic service information.
    """
    # await request.state.limiter.hit(request.url.path, request.client.host) # Example of applying limiter - temporarily disabled
    logger.info("Root endpoint was called.")
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """
    Health check endpoint for service monitoring.
    """
    return {"status": "ok", "message": "Auth Service is operational."}

# Reminder for production deployment:
# Uvicorn behind a reverse proxy (Nginx, Traefik) for HTTPS/TLS.
# Ensure CSRF_SECRET_KEY is strong and managed securely.
# Ensure SECRET_KEY (for JWTs) is strong and managed securely.
# Review rate limits based on expected traffic.
# Ensure POSTGRES_PASSWORD and other sensitive env vars are managed via secrets.
