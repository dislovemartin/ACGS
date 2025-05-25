from fastapi import FastAPI
from gs_service.app.api.v1.synthesize import router as synthesize_router
from gs_service.app.api.v1.policy_management import router as policy_management_router # Added
from gs_service.app.services.ac_client import ac_service_client 
from gs_service.app.services.integrity_client import integrity_service_client
from gs_service.app.services.fv_client import fv_service_client # Added FV client for shutdown
from shared.security_middleware import add_security_headers # Import the shared middleware

app = FastAPI(title="Governance Synthesis (GS) Service")

# Apply the security headers middleware
app.middleware("http")(add_security_headers)

# Include the API router for synthesis
app.include_router(synthesize_router, prefix="/api/v1/synthesize", tags=["Governance Synthesis"])
app.include_router(policy_management_router, prefix="/api/v1/policy-management", tags=["Policy and Template Management"]) # Added

@app.on_event("startup")
async def on_startup():
    # Typically, you might initialize resources here.
    # For gs_service, http clients are initialized when their modules are imported.
    # You could add a health check ping to dependent services here if needed.
    print("GS Service startup: Ready to synthesize governance rules.")

@app.on_event("shutdown")
async def on_shutdown():
    # Gracefully close HTTPX clients
    await ac_service_client.close()
    await integrity_service_client.close()
    await fv_service_client.close() # Close FV client
    print("GS Service shutdown: HTTP clients closed.")

@app.get("/")
async def root():
    return {"message": "Governance Synthesis Service is running. Use /api/v1/synthesize/docs for API documentation."}

# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    # A more comprehensive health check might try to connect to dependent services.
    return {"status": "ok", "message": "GS Service is operational."}
