from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.verify import router as verify_router
from app.services.ac_client import ac_service_client
from app.services.integrity_client import integrity_service_client
# from shared.security_middleware import add_security_middleware # Import the shared middleware
# from shared import get_config
# from shared.metrics import get_metrics, metrics_middleware, create_metrics_endpoint

# Local configuration to avoid shared module dependencies
class LocalConfig:
    def get(self, key, default=None):
        defaults = {
            'api_version': 'v1',
            'debug': False,
            'environment': 'development'
        }
        return defaults.get(key, default)

    def get_service_url(self, service):
        urls = {
            'ac': 'http://localhost:8000',
            'integrity': 'http://localhost:8002'
        }
        return urls.get(service, 'http://localhost:8000')

config = LocalConfig()

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
    title="Formal Verification (FV) Service",
    version=config.get('api_version', 'v1'),
    debug=config.get('debug', False)
)

# Initialize metrics for FV service
# metrics = get_metrics("fv_service")

# Add local security middleware
add_local_security_middleware(app)

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

    # Task 7: Initialize parallel validation pipeline
    try:
        from app.core.parallel_validation_pipeline import parallel_pipeline
        # from shared.celery_integration import initialize_celery_integration

        # Mock Celery integration for now
        celery_available = False
        if celery_available:
            print("Celery integration initialized for parallel processing")
        else:
            print("Celery not available - using local parallel processing")

        print("Parallel validation pipeline initialized")

    except Exception as e:
        print(f"Warning: Failed to initialize parallel pipeline: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    # Gracefully close HTTPX clients
    await ac_service_client.close()
    await integrity_service_client.close()

    # Task 7: Shutdown parallel validation pipeline
    try:
        from app.core.parallel_validation_pipeline import parallel_pipeline
        from shared.celery_integration import shutdown_celery_integration

        await parallel_pipeline.shutdown()
        await shutdown_celery_integration()
        print("Parallel validation pipeline shutdown complete")

    except Exception as e:
        print(f"Warning: Error during parallel pipeline shutdown: {e}")

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
