"""
Research Infrastructure Service for ACGS-PGP

Provides comprehensive research infrastructure for ongoing constitutional AI research
and development including experiment tracking, data collection, analysis, and
automated research workflows.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import get_settings
from .core.database import get_db_session
from .api.routers import (
    experiment_tracking_router,
    data_collection_router,
    analysis_router,
    automation_router,
    reproducibility_router
)
from .services.experiment_tracker import ExperimentTracker
from .services.research_automation import ResearchAutomationService

# Import security middleware
from shared.security_middleware import add_security_middleware
from shared.security_config import security_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Research Infrastructure Service...")
    
    # Initialize research automation service
    automation_service = ResearchAutomationService()
    await automation_service.initialize()
    
    # Store in app state
    app.state.automation_service = automation_service
    
    yield
    
    logger.info("Shutting down Research Infrastructure Service...")
    await automation_service.cleanup()

# Create FastAPI application
app = FastAPI(
    title="ACGS-PGP Research Infrastructure Service",
    description="Comprehensive research infrastructure for constitutional AI research and development",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add enhanced security middleware (includes rate limiting, input validation, security headers, audit logging)
add_security_middleware(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "research_infrastructure",
        "version": "1.0.0",
        "timestamp": "2024-01-20T00:00:00Z"
    }

# Include API routers
app.include_router(
    experiment_tracking_router,
    prefix="/api/v1/experiments",
    tags=["Experiment Tracking"]
)

app.include_router(
    data_collection_router,
    prefix="/api/v1/data",
    tags=["Data Collection"]
)

app.include_router(
    analysis_router,
    prefix="/api/v1/analysis",
    tags=["Statistical Analysis"]
)

app.include_router(
    automation_router,
    prefix="/api/v1/automation",
    tags=["Research Automation"]
)

app.include_router(
    reproducibility_router,
    prefix="/api/v1/reproducibility",
    tags=["Reproducibility"]
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8007,
        reload=True,
        log_level="info"
    )
