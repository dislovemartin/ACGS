from fastapi import FastAPI
from app.api.v1.synthesize import router as synthesize_router
from app.api.v1.policy_management import router as policy_management_router # Added
from app.api.v1.constitutional_synthesis import router as constitutional_synthesis_router # Added Phase 1
from app.api.v1.alphaevolve_integration import router as alphaevolve_router # Added Phase 2
from app.api.v1.mab_optimization import router as mab_router # Added Task 5 MAB
from app.api.v1.wina_rego_synthesis import router as wina_rego_router # Added Task 17.5 WINA Rego
from app.services.ac_client import ac_service_client
from app.services.integrity_client import integrity_service_client
from app.services.fv_client import fv_service_client # Added FV client for shutdown
from shared.security_middleware import SecurityHeadersMiddleware # Import the shared middleware
# from shared.metrics import get_metrics, metrics_middleware, create_metrics_endpoint

app = FastAPI(title="Governance Synthesis (GS) Service")

# Initialize metrics for GS service
# metrics = get_metrics("gs_service")

# Add metrics middleware
# app.middleware("http")(metrics_middleware("gs_service"))

# Apply the security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Include the API router for synthesis
app.include_router(synthesize_router, prefix="/api/v1/synthesize", tags=["Governance Synthesis"])
app.include_router(policy_management_router, prefix="/api/v1/policy-management", tags=["Policy and Template Management"]) # Added
app.include_router(constitutional_synthesis_router, prefix="/api/v1/constitutional", tags=["Constitutional Synthesis"]) # Added Phase 1
app.include_router(alphaevolve_router, prefix="/api/v1/alphaevolve", tags=["AlphaEvolve Integration"]) # Added Phase 2
app.include_router(mab_router, prefix="/api/v1/mab", tags=["Multi-Armed Bandit Optimization"]) # Added Task 5
app.include_router(wina_rego_router, prefix="/api/v1", tags=["WINA Rego Synthesis"]) # Added Task 17.5

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

# Add Prometheus metrics endpoint
# app.get("/metrics")(create_metrics_endpoint())
