# ACGS/backend/ac_service/app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

# Assuming shared modules are accessible via PYTHONPATH adjustments in Dockerfile or run command
try:
    from shared.database import async_engine, Base # Use Base from shared
    from shared.security_middleware import add_security_headers
    # Import shared models to ensure they are registered with Base.metadata before create_all
    import shared.models # noqa
except ImportError:
    logging.error("AC Service: Failed to import shared modules. Ensure PYTHONPATH is set correctly.")
    # Fallback for local dev if PYTHONPATH is tricky, assuming 'shared' is two levels up
    import sys
    import os
    # Adjust path to point to ACGS root directory
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from shared.database import async_engine, Base
    from shared.security_middleware import add_security_headers
    import shared.models # noqa


from .api.v1 import principles as principles_router # Relative import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AC Service: Starting up...")
    # Create database tables if they don't exist using shared Base.metadata
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 
    logger.info("AC Service: Database tables (from shared.models) checked/created if necessary.")
    yield
    logger.info("AC Service: Shutting down...")
    if async_engine:
        await async_engine.dispose()
    logger.info("AC Service: Database engine disposed.")


app = FastAPI(
    title="Artificial Constitution (AC) Service",
    description="Manages AI governance principles and guidelines.",
    version="0.1.0",
    lifespan=lifespan
)

# Apply the security headers middleware
app.middleware("http")(add_security_headers)

# Include the API router for principles
app.include_router(principles_router.router, prefix="/api/v1/principles", tags=["Principles"])

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint for the AC Service.
    """
    return {"message": "Welcome to the Artificial Constitution (AC) Service. Visit /docs for API documentation."}

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

# To run locally (from ACGS/backend/ac_service):
# PYTHONPATH=../.. uvicorn app.main:app --reload --port 8001
