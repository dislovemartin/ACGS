from fastapi import FastAPI, Request, status # Added Request, status
from fastapi.responses import JSONResponse
from app.api.endpoints import router as api_router
from app.db.database import create_db_tables, engine
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic_settings import BaseSettings
import os

from app.core.limiter import limiter # Import limiter instance
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

class CsrfSettings(BaseSettings):
    secret_key: str = os.getenv("CSRF_SECRET_KEY", "your-default-csrf-secret-key-if-not-set")
    cookie_samesite: str = "lax"
    header_name: str = "X-CSRF-Token" 
    cookie_key: str = "csrf_access_token" 

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

app = FastAPI(title="Authentication Service")

# Initialize rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply the security headers middleware
from shared.security_middleware import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN, # Using 403 for CSRF failure
        content={"detail": exc.message}
    )

# Include the API router
app.include_router(api_router, prefix="/auth", tags=["authentication"])

@app.on_event("startup")
async def on_startup():
    # This is a good place for operations that need to happen once the application starts.
    # For example, creating database tables.
    # Make sure all models are imported so Base knows about them.
    # from .app import models # Ensure models are imported if not already by other imports

    # The create_db_tables function in database.py should handle importing models
    # and calling Base.metadata.create_all(engine)
    await create_db_tables()
    print("Auth service startup: Database tables check/creation initiated.")


@app.get("/")
async def root():
    return {"message": "Authentication Service is running. Use /auth/docs for API documentation."}

# If you need to test database connection or model creation directly for debugging:
# from sqlalchemy.orm import Session
# from auth_service.app.db.database import SessionLocal
# from auth_service.app.models import User  # Assuming User model
# @app.get("/test-db")
# def test_db_connection():
#     try:
#         db: Session = SessionLocal()
#         # Perform a simple query
#         user_count = db.query(User).count()
#         db.close()
#         return {"status": "success", "message": "Database connection successful", "user_count": user_count}
#     except Exception as e:
#         return {"status": "error", "message": f"Database connection failed: {str(e)}"}
