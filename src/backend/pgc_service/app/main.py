from fastapi import FastAPI
from app.api.v1.enforcement import router as enforcement_router
from app.api.v1.alphaevolve_enforcement import router as alphaevolve_enforcement_router # Added Phase 2
from app.core.policy_manager import policy_manager
from app.services.integrity_client import integrity_service_client
from shared.security_middleware import SecurityHeadersMiddleware # Import the shared middleware

app = FastAPI(title="Protective Governance Controls (PGC) Service")

# Apply the security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Include the API router for policy enforcement
app.include_router(enforcement_router, prefix="/api/v1/enforcement", tags=["Policy Enforcement"])
app.include_router(alphaevolve_enforcement_router, prefix="/api/v1/alphaevolve", tags=["AlphaEvolve Enforcement"]) # Added Phase 2

@app.on_event("startup")
async def on_startup():
    # Initialize the PolicyManager: fetch initial set of policies
    # This ensures that the service has policies loaded when it starts serving requests.
    print("PGC Service startup: Initializing Policy Manager and loading policies...")
    await policy_manager.get_active_rules(force_refresh=True)
    print("PGC Service: Policy Manager initialized.")
    # Other startup tasks if any

@app.on_event("shutdown")
async def on_shutdown():
    # Gracefully close HTTPX clients
    await integrity_service_client.close()
    print("PGC Service shutdown: HTTP clients closed.")

@app.get("/")
async def root():
    return {"message": "Protective Governance Controls (PGC) Service is running. Use /api/v1/enforcement/docs for API documentation."}

# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    # A more comprehensive health check might check policy loading status.
    if policy_manager._last_refresh_time:
        return {"status": "ok", "message": "PGC Service is operational.", "policies_loaded_at": policy_manager._last_refresh_time}
    else:
        return {"status": "degraded", "message": "PGC Service is operational, but policies have not been loaded yet."}
