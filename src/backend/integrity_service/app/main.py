from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import policies as policies_router
from app.api.v1 import audit as audit_router
from app.api.v1 import appeals as appeals_router  # Phase 3: Appeals and Explainability
from app.api.v1 import crypto as crypto_router  # Phase 3: Cryptographic Operations
from app.api.v1 import integrity as integrity_router  # Phase 3: Integrity Verification
from app.api.v1 import pgp_assurance as pgp_router  # Phase 3: PGP Assurance
from app.api.v1 import research_data as research_data_router  # Task 13: Research Data Pipeline
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
# from shared.metrics import get_metrics, metrics_middleware, create_metrics_endpoint

# Local database configuration to avoid shared module import issues
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://acgs_user:acgs_password@localhost:5434/acgs_db")
async_engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def create_local_db_and_tables():
    """Local implementation of database table creation"""
    from app.models import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"Integrity Service: Database tables checked/created for {DATABASE_URL}")

async def get_local_async_db():
    """Local implementation of async database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def add_local_security_middleware(app: FastAPI):
    """Local implementation of security middleware"""
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app = FastAPI(
    title="Integrity and Verifiability Service",
    description="ACGS-PGP Cryptographic Integrity and Audit Service with PGP Assurance",
    version="3.0.0"
)

# Initialize metrics for integrity service
# metrics = get_metrics("integrity_service")

# Add metrics middleware
# app.middleware("http")(metrics_middleware("integrity_service"))

# Add local security middleware
add_local_security_middleware(app)

# Include the API routers
app.include_router(policies_router.router, prefix="/api/v1/policies", tags=["Policy Rules"])
app.include_router(audit_router.router, prefix="/api/v1/audit", tags=["Audit Logs"])
app.include_router(appeals_router.router, prefix="/api/v1", tags=["Appeals & Explainability"])  # Phase 3
app.include_router(crypto_router.router, prefix="/api/v1/crypto", tags=["Cryptographic Operations"])  # Phase 3
app.include_router(integrity_router.router, prefix="/api/v1/integrity", tags=["Integrity Verification"])  # Phase 3
app.include_router(pgp_router.router, prefix="/api/v1/pgp-assurance", tags=["PGP Assurance"])  # Phase 3
app.include_router(research_data_router.router, prefix="/api/v1/research", tags=["Research Data Pipeline"])  # Task 13

@app.on_event("startup")
async def on_startup():
    # Create database tables if they don't exist
    # Import models to ensure they're registered with Base
    from app import models  # This imports the integrity service models
    try:
        await create_local_db_and_tables()
        print("Integrity Service startup: Database tables check/creation initiated.")
    except Exception as e:
        print(f"Integrity Service startup: Database connection failed: {e}")
        print("Integrity Service startup: Continuing without database connection for testing.")

@app.get("/")
async def root():
    return {"message": "Integrity and Verifiability Service is running. Use /docs for API documentation."}

# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Add Prometheus metrics endpoint
# app.get("/metrics")(create_metrics_endpoint())
