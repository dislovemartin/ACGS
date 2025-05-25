# ACGS/backend/auth_service/app/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel # For CsrfSettings

# Assuming shared modules are accessible
try:
    from shared.database import async_engine, Base # For lifespan DB operations
    from shared.security_middleware import add_security_headers
    import shared.models # noqa To ensure models are registered with Base
except ImportError:
    logging.error("Auth Service: Failed to import shared modules. Ensure PYTHONPATH is set correctly.")
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from shared.database import async_engine, Base
    from shared.security_middleware import add_security_headers
    import shared.models # noqa

from .api.v1.api_router import api_router as v1_api_router # Main router for v1
from .core.config import settings
from .core.limiter import limiter, RateLimitExceeded, _rate_limit_exceeded_handler # Rate limiting

# CSRF Protection
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError

# Configure logging
# logging.basicConfig(level=settings.LOG_LEVEL.upper() if hasattr(settings, 'LOG_LEVEL') else logging.INFO) # settings.LOG_LEVEL might not be upper()
numeric_log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=numeric_log_level)
logger = logging.getLogger(settings.PROJECT_NAME)


class CsrfSettings(BaseModel):
    secret_key: str = settings.CSRF_SECRET_KEY
    cookie_samesite: str = "lax" 
    header_name: str = "X-CSRF-Token" 
    cookie_key: str = "fastapi-csrf-token"


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.PROJECT_NAME}: Starting up...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"{settings.PROJECT_NAME}: Database tables checked/created.")
    yield
    logger.info(f"{settings.PROJECT_NAME}: Shutting down...")
    if async_engine:
        await async_engine.dispose()
    logger.info(f"{settings.PROJECT_NAME}: Database engine disposed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(CsrfProtectError)
async def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    logger.warning(f"CSRF protection error: {exc.message} for request: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code, 
        content={"detail": exc.message},
    )

if settings.BACKEND_CORS_ORIGINS:
    origins = []
    if isinstance(settings.BACKEND_CORS_ORIGINS, str):
        origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(',') if origin.strip()]
    elif isinstance(settings.BACKEND_CORS_ORIGINS, list):
        origins = [str(origin).strip() for origin in settings.BACKEND_CORS_ORIGINS if str(origin).strip()]

    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True, 
            allow_methods=["*"],
            allow_headers=["*", "X-CSRF-Token"], 
        )
        logger.info(f"CORS enabled for origins: {origins}")
else:
    logger.info("CORS not configured or no origins specified.")

app.middleware("http")(add_security_headers)
app.include_router(v1_api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def root(request: Request):
    logger.info(f"Root endpoint of {settings.PROJECT_NAME} was called.")
    return {"message": f"Welcome to {settings.PROJECT_NAME}. Visit {settings.API_V1_STR}/docs for API documentation."}
