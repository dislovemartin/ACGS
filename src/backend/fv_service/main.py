from fastapi import FastAPI
from app.api.v1.verify import router as verify_router
from app.services.ac_client import ac_service_client
from app.services.integrity_client import integrity_service_client
from shared.security_middleware import SecurityHeadersMiddleware # Import the shared middleware
# from shared.metrics import get_metrics, metrics_middleware, create_metrics_endpoint

app = FastAPI(title="Formal Verification (FV) Service")

# Initialize metrics for FV service
# metrics = get_metrics("fv_service")

# Add metrics middleware
# app.middleware("http")(metrics_middleware("fv_service"))

# Apply the security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Include the API router for verification
app.include_router(verify_router, prefix="/api/v1/verify", tags=["Formal Verification"])

@app.on_event("startup")
async def on_startup():
    # HTTP clients are initialized when their modules are imported.
    # Add health check pings to dependent services here if needed.
    print("FV Service startup: Ready for formal verification tasks.")

@app.on_event("shutdown")
async def on_shutdown():
    # Gracefully close HTTPX clients
    await ac_service_client.close()
    await integrity_service_client.close()
    print("FV Service shutdown: HTTP clients closed.")

@app.get("/")
async def root():
    return {"message": "Formal Verification Service is running. Use /api/v1/verify/docs for API documentation."}

# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    # A more comprehensive health check might try to connect to dependent services.
    return {"status": "ok", "message": "FV Service is operational."}

# Add Prometheus metrics endpoint
# app.get("/metrics")(create_metrics_endpoint())
