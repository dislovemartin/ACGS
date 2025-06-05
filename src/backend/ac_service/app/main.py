from app.api.v1.conflict_resolution import router as conflict_resolution_router
from app.api.v1.constitutional_council import router as constitutional_council_router
from app.api.v1.democratic_governance import router as democratic_governance_router
from app.api.v1.fidelity_monitor import router as fidelity_monitor_router
from app.api.v1.principles import router as principles_router
from app.api.v1.stakeholder_engagement import router as stakeholder_engagement_router
from app.api.v1.voting import router as voting_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.dashboard_websocket import router as dashboard_websocket_router
from app.api.hitl_sampling import router as hitl_sampling_router
from app.api.public_consultation import router as public_consultation_router
from fastapi import FastAPI

from shared.metrics import create_metrics_endpoint, get_metrics, metrics_middleware
from shared.security_middleware import (
    SecurityHeadersMiddleware,
)  # Import the shared middleware

app = FastAPI(title="Artificial Constitution (AC) Service")

# Initialize metrics for AC service
metrics = get_metrics("ac_service")

# Add metrics middleware
app.middleware("http")(metrics_middleware("ac_service"))

# Apply the security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Include the API routers
app.include_router(principles_router, prefix="/api/v1/principles", tags=["Principles"])
app.include_router(
    constitutional_council_router,
    prefix="/api/v1/constitutional-council",
    tags=["Constitutional Council"],
)
app.include_router(
    conflict_resolution_router,
    prefix="/api/v1/conflict-resolution",
    tags=["Conflict Resolution"],
)
app.include_router(
    fidelity_monitor_router, prefix="/api/v1/fidelity", tags=["Constitutional Fidelity"]
)
app.include_router(
    stakeholder_engagement_router, prefix="/api/v1", tags=["Stakeholder Engagement"]
)
app.include_router(voting_router, prefix="/api/v1", tags=["Voting Mechanism"])
app.include_router(workflows_router, prefix="/api/v1", tags=["LangGraph Workflows"])
app.include_router(democratic_governance_router, prefix="/api/v1")
app.include_router(hitl_sampling_router, prefix="/api/v1")
app.include_router(public_consultation_router, prefix="/api/v1")
app.include_router(dashboard_websocket_router, prefix="/api/v1", tags=["Real-time Dashboard"])


@app.on_event("startup")
def on_startup():
    print("AC Service startup: Service initialized.")


@app.get("/")
async def root():
    return {
        "message": "Artificial Constitution Service is running. Use /api/v1/principles/docs for API documentation."
    }


# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Add Prometheus metrics endpoint
app.get("/metrics")(create_metrics_endpoint())
