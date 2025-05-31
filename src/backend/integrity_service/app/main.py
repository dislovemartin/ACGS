from fastapi import FastAPI
from app.api.v1 import policies as policies_router
from app.api.v1 import audit as audit_router
from app.api.v1 import appeals as appeals_router  # Phase 3: Appeals and Explainability
from app.api.v1 import crypto as crypto_router  # Phase 3: Cryptographic Operations
from app.api.v1 import integrity as integrity_router  # Phase 3: Integrity Verification
from app.api.v1 import pgp_assurance as pgp_router  # Phase 3: PGP Assurance
from shared.database import create_db_and_tables
from shared.security_middleware import SecurityHeadersMiddleware # Import the shared middleware
from shared.metrics import get_metrics, metrics_middleware, create_metrics_endpoint

app = FastAPI(
    title="Integrity and Verifiability Service",
    description="ACGS-PGP Cryptographic Integrity and Audit Service with PGP Assurance",
    version="3.0.0"
)

# Initialize metrics for integrity service
metrics = get_metrics("integrity_service")

# Add metrics middleware
app.middleware("http")(metrics_middleware("integrity_service"))

# Apply the security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Include the API routers
app.include_router(policies_router.router, prefix="/api/v1/policies", tags=["Policy Rules"])
app.include_router(audit_router.router, prefix="/api/v1/audit", tags=["Audit Logs"])
app.include_router(appeals_router.router, prefix="/api/v1", tags=["Appeals & Explainability"])  # Phase 3
app.include_router(crypto_router.router, prefix="/api/v1/crypto", tags=["Cryptographic Operations"])  # Phase 3
app.include_router(integrity_router.router, prefix="/api/v1/integrity", tags=["Integrity Verification"])  # Phase 3
app.include_router(pgp_router.router, prefix="/api/v1/pgp-assurance", tags=["PGP Assurance"])  # Phase 3

@app.on_event("startup")
async def on_startup():
    # Create database tables if they don't exist
    # Import models to ensure they're registered with Base
    from app import models  # This imports the integrity service models
    await create_db_and_tables()
    print("Integrity Service startup: Database tables check/creation initiated.")

@app.get("/")
async def root():
    return {"message": "Integrity and Verifiability Service is running. Use /docs for API documentation."}

# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Add Prometheus metrics endpoint
app.get("/metrics")(create_metrics_endpoint())
