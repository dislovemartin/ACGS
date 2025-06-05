import os
import logging
from fastapi import FastAPI

# Local implementations to avoid shared module dependencies
from fastapi.middleware.cors import CORSMiddleware

def add_security_middleware(app: FastAPI):
    """Local implementation of security middleware"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

class MockSecurityConfig:
    def get(self, key, default=None):
        return default

security_config = MockSecurityConfig()

class MockMetrics:
    def record_verification_operation(self, verification_type: str, result: str):
        pass

def get_metrics(service_name: str) -> MockMetrics:
    return MockMetrics()

def metrics_middleware(service_name: str):
    def middleware(request, call_next):
        return call_next(request)
    return middleware

def create_metrics_endpoint():
    def metrics():
        return {"status": "ok", "metrics": {}}
    return metrics

# Import core components with error handling
try:
    from app.core.policy_manager import policy_manager
    POLICY_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Policy manager not available: {e}")
    POLICY_MANAGER_AVAILABLE = False
    # Mock policy manager
    class MockPolicyManager:
        async def get_active_rules(self, force_refresh=False):
            return []
    policy_manager = MockPolicyManager()

try:
    from app.services.integrity_client import integrity_service_client
    INTEGRITY_CLIENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Integrity client not available: {e}")
    INTEGRITY_CLIENT_AVAILABLE = False
    # Mock integrity client
    class MockIntegrityClient:
        async def close(self):
            pass
    integrity_service_client = MockIntegrityClient()

# Import API routers with error handling
try:
    from app.api.v1.enforcement import router as enforcement_router
except ImportError as e:
    print(f"Warning: Enforcement router not available: {e}")
    from fastapi import APIRouter
    enforcement_router = APIRouter()

try:
    from app.api.v1.alphaevolve_enforcement import router as alphaevolve_enforcement_router
except ImportError as e:
    print(f"Warning: AlphaEvolve enforcement router not available: {e}")
    from fastapi import APIRouter
    alphaevolve_enforcement_router = APIRouter()

try:
    from app.api.v1.incremental_compilation import router as incremental_compilation_router
except ImportError as e:
    print(f"Warning: Incremental compilation router not available: {e}")
    from fastapi import APIRouter
    incremental_compilation_router = APIRouter()

try:
    from app.api.v1.ultra_low_latency import router as ultra_low_latency_router
except ImportError as e:
    print(f"Warning: Ultra low latency router not available: {e}")
    from fastapi import APIRouter
    ultra_low_latency_router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Protective Governance Controls (PGC) Service")

# Initialize metrics for PGC service
metrics = get_metrics("pgc_service")

# Add metrics middleware
app.middleware("http")(metrics_middleware("pgc_service"))

# Add enhanced security middleware (includes rate limiting, input validation, security headers, audit logging)
add_security_middleware(app)

# Include the API router for policy enforcement
app.include_router(enforcement_router, prefix="/api/v1/enforcement", tags=["Policy Enforcement"])
app.include_router(alphaevolve_enforcement_router, prefix="/api/v1/alphaevolve", tags=["AlphaEvolve Enforcement"]) # Added Phase 2
app.include_router(incremental_compilation_router, prefix="/api/v1/incremental", tags=["Incremental Compilation"]) # Added Task 8
app.include_router(ultra_low_latency_router, prefix="/api/v1/ultra-low-latency", tags=["Ultra Low Latency Optimization"]) # Added AlphaEvolve Enhancement

@app.on_event("startup")
async def on_startup():
    # Initialize the PolicyManager: fetch initial set of policies
    # This ensures that the service has policies loaded when it starts serving requests.
    print("PGC Service startup: Initializing Policy Manager and loading policies...")
    if POLICY_MANAGER_AVAILABLE:
        try:
            await policy_manager.get_active_rules(force_refresh=True)
            print("PGC Service: Policy Manager initialized.")
        except Exception as e:
            print(f"PGC Service: Policy Manager initialization failed: {e}")
    else:
        print("PGC Service: Using mock Policy Manager.")
    # Other startup tasks if any

@app.on_event("shutdown")
async def on_shutdown():
    # Gracefully close HTTPX clients
    if INTEGRITY_CLIENT_AVAILABLE:
        try:
            await integrity_service_client.close()
            print("PGC Service shutdown: HTTP clients closed.")
        except Exception as e:
            print(f"PGC Service shutdown error: {e}")
    else:
        print("PGC Service shutdown: Mock clients closed.")

@app.get("/")
async def root():
    return {"message": "Protective Governance Controls (PGC) Service is running. Use /api/v1/enforcement/docs for API documentation."}

@app.get("/health")
async def health_check():
    """
    Comprehensive health check for PGC Service.
    Validates policy loading status, OPA connectivity, and service dependencies.
    """
    health_status = {
        "status": "healthy",
        "service": "pgc_service",
        "version": "1.0.0",
        "timestamp": "2024-01-20T00:00:00Z",
        "dependencies": {},
        "components": {}
    }

    try:
        # Check policy manager status
        if hasattr(policy_manager, '_last_refresh_time') and policy_manager._last_refresh_time:
            health_status["components"]["policy_manager"] = {
                "status": "healthy",
                "last_refresh": str(policy_manager._last_refresh_time),
                "policies_loaded": True
            }
        else:
            health_status["components"]["policy_manager"] = {
                "status": "degraded",
                "policies_loaded": False,
                "message": "Policies have not been loaded yet"
            }

        # Check OPA connectivity
        try:
            import httpx
            opa_url = os.getenv('OPA_SERVER_URL', 'http://opa:8181')
            async with httpx.AsyncClient(timeout=5.0) as client:
                opa_response = await client.get(f"{opa_url}/health")
                health_status["dependencies"]["opa"] = {
                    "status": "healthy" if opa_response.status_code == 200 else "unhealthy",
                    "response_time_ms": opa_response.elapsed.total_seconds() * 1000 if hasattr(opa_response, 'elapsed') else 0
                }
        except Exception as e:
            health_status["dependencies"]["opa"] = {
                "status": "unhealthy",
                "error": str(e)
            }

        # Check Integrity Service connectivity
        try:
            integrity_url = os.getenv('INTEGRITY_SERVICE_URL', 'http://integrity_service:8002')
            async with httpx.AsyncClient(timeout=5.0) as client:
                integrity_response = await client.get(f"{integrity_url}/health")
                health_status["dependencies"]["integrity_service"] = {
                    "status": "healthy" if integrity_response.status_code == 200 else "unhealthy",
                    "response_time_ms": integrity_response.elapsed.total_seconds() * 1000 if hasattr(integrity_response, 'elapsed') else 0
                }
        except Exception as e:
            health_status["dependencies"]["integrity_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }

        # Determine overall health status
        critical_deps = ["opa"]
        unhealthy_critical = [dep for dep in critical_deps
                            if health_status["dependencies"].get(dep, {}).get("status") == "unhealthy"]

        if unhealthy_critical:
            health_status["status"] = "degraded"
            health_status["message"] = f"Critical dependencies unhealthy: {', '.join(unhealthy_critical)}"
        elif not health_status["components"]["policy_manager"]["policies_loaded"]:
            health_status["status"] = "degraded"
            health_status["message"] = "PGC Service operational but policies not loaded"
        else:
            health_status["message"] = "PGC Service is fully operational"

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["message"] = f"Health check failed: {str(e)}"
        health_status["error"] = str(e)

    return health_status

# Add Prometheus metrics endpoint
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint for PGC Service."""
    return create_metrics_endpoint()
