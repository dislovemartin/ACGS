from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.verify import router as verify_router
from app.services.ac_client import ac_service_client
from app.services.integrity_client import integrity_service_client
from shared.security_middleware import SecurityHeadersMiddleware # Import the shared middleware
from shared import get_config
# from shared.metrics import get_metrics, metrics_middleware, create_metrics_endpoint

# Load centralized configuration
config = get_config()

app = FastAPI(
    title="Formal Verification (FV) Service",
    version=config.get('api_version', 'v1'),
    debug=config.get('debug', False)
)

# Initialize metrics for FV service
# metrics = get_metrics("fv_service")

# Add CORS middleware with centralized configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get('cors_origins', ['*']),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    print(f"FV Service startup: Ready for formal verification tasks.")
    print(f"Environment: {config.get('environment')}")
    print(f"API Version: {config.get('api_version')}")
    print(f"Debug Mode: {config.get('debug')}")

@app.on_event("shutdown")
async def on_shutdown():
    # Gracefully close HTTPX clients
    await ac_service_client.close()
    await integrity_service_client.close()
    print("FV Service shutdown: HTTP clients closed.")

@app.get("/")
async def root():
    return {
        "message": "Formal Verification Service is running. Use /api/v1/verify/docs for API documentation.",
        "version": config.get('api_version'),
        "environment": config.get('environment')
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check with configuration validation."""
    try:
        # Test configuration access
        env = config.get('environment')

        # Test service URL configuration
        ac_url = config.get_service_url('ac')
        integrity_url = config.get_service_url('integrity')

        return {
            "status": "ok",
            "message": "FV Service is operational.",
            "environment": env,
            "configuration": {
                "ac_service_url": ac_url,
                "integrity_service_url": integrity_url,
                "api_version": config.get('api_version')
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Configuration error: {str(e)}"
        }

# Add Prometheus metrics endpoint
# app.get("/metrics")(create_metrics_endpoint())
