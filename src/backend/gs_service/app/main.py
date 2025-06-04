import os
import httpx
from fastapi import FastAPI
from app.api.v1.synthesize import router as synthesize_router
from app.api.v1.policy_management import router as policy_management_router # Added
from app.api.v1.constitutional_synthesis import router as constitutional_synthesis_router # Added Phase 1
from app.api.v1.alphaevolve_integration import router as alphaevolve_router # Added Phase 2
from app.api.v1.mab_optimization import router as mab_router # Added Task 5 MAB
from app.api.v1.wina_rego_synthesis import router as wina_rego_router # Added Task 17.5 WINA Rego
from app.api.v1.reliability_metrics import router as reliability_metrics_router, llm_reliability_framework_instance # Added for LLM Reliability Dashboard
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
app.include_router(reliability_metrics_router, prefix="/api/v1/reliability", tags=["LLM Reliability Metrics"]) # Added for LLM Reliability Dashboard

@app.on_event("startup")
async def on_startup():
    # Typically, you might initialize resources here.
    # For gs_service, http clients are initialized when their modules are imported.
    # You could add a health check ping to dependent services here if needed.
    print("GS Service startup: Ready to synthesize governance rules.")
    await llm_reliability_framework_instance.initialize()
    print("LLM Reliability Framework initialized.")

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
    """
    Comprehensive health check for GS Service.
    Validates service dependencies and operational status.
    """
    health_status = {
        "status": "healthy",
        "service": "gs_service",
        "version": "1.0.0",
        "timestamp": "2024-01-20T00:00:00Z",
        "dependencies": {},
        "components": {}
    }

    try:
        # Check LLM Reliability Framework
        if hasattr(llm_reliability_framework_instance, 'get_health_status'):
            health_status["components"]["llm_reliability"] = await llm_reliability_framework_instance.get_health_status()
        else:
            health_status["components"]["llm_reliability"] = {"status": "initialized"}

        # Check service clients connectivity
        try:
            # Test AC Service connectivity
            async with httpx.AsyncClient(timeout=5.0) as client:
                ac_response = await client.get(f"{os.getenv('AC_SERVICE_URL', 'http://ac_service:8001')}/health")
                health_status["dependencies"]["ac_service"] = {
                    "status": "healthy" if ac_response.status_code == 200 else "unhealthy",
                    "response_time_ms": ac_response.elapsed.total_seconds() * 1000 if hasattr(ac_response, 'elapsed') else 0
                }
        except Exception as e:
            health_status["dependencies"]["ac_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }

        try:
            # Test Integrity Service connectivity
            async with httpx.AsyncClient(timeout=5.0) as client:
                integrity_response = await client.get(f"{os.getenv('INTEGRITY_SERVICE_URL', 'http://integrity_service:8002')}/health")
                health_status["dependencies"]["integrity_service"] = {
                    "status": "healthy" if integrity_response.status_code == 200 else "unhealthy",
                    "response_time_ms": integrity_response.elapsed.total_seconds() * 1000 if hasattr(integrity_response, 'elapsed') else 0
                }
        except Exception as e:
            health_status["dependencies"]["integrity_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }

        # Check if any critical dependencies are unhealthy
        critical_deps = ["ac_service"]
        unhealthy_critical = [dep for dep in critical_deps
                            if health_status["dependencies"].get(dep, {}).get("status") == "unhealthy"]

        if unhealthy_critical:
            health_status["status"] = "degraded"
            health_status["message"] = f"Critical dependencies unhealthy: {', '.join(unhealthy_critical)}"
        else:
            health_status["message"] = "GS Service is operational with all dependencies healthy."

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["message"] = f"Health check failed: {str(e)}"
        health_status["error"] = str(e)

    return health_status

# Add Prometheus metrics endpoint
from shared.metrics import get_metrics, create_metrics_endpoint

# Initialize metrics for GS service
metrics = get_metrics("gs_service")

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint for GS Service."""
    return create_metrics_endpoint()
