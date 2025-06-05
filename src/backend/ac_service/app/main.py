from fastapi import FastAPI
import logging
import asyncio

# Import shared modules first
from shared.security_middleware import add_security_middleware
from shared.security_config import security_config
from shared.metrics import create_metrics_endpoint, get_metrics, metrics_middleware

# Phase 3: Memory optimization and cache warming
from shared.memory_optimizer import initialize_memory_optimization, get_memory_optimizer
from shared.cache_warming_service import get_cache_warming_service, CacheWarmingConfig
from shared.redis_client import ACGSRedisClient

# Import API routers
from app.api.v1.principles import router as principles_router
from app.api.v1.constitutional_council import router as constitutional_council_router
from app.api.v1.conflict_resolution import router as conflict_resolution_router
from app.api.v1.fidelity_monitor import router as fidelity_monitor_router
from app.api.v1.stakeholder_engagement import router as stakeholder_engagement_router
from app.api.v1.voting import router as voting_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.democratic_governance import router as democratic_governance_router
from app.api.v1.dashboard_websocket import router as dashboard_websocket_router
from app.api.v1.collective_constitutional_ai import router as collective_constitutional_ai_router
from app.api.hitl_sampling import router as hitl_sampling_router
from app.api.public_consultation import router as public_consultation_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Artificial Constitution (AC) Service")

# Initialize metrics for AC service
metrics = get_metrics("ac_service")

# Add enhanced security middleware (clean pattern like fv_service)
add_security_middleware(app)

# Add metrics middleware
app.middleware("http")(metrics_middleware("ac_service"))

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
app.include_router(collective_constitutional_ai_router, prefix="/api/v1/ccai", tags=["Collective Constitutional AI"])
app.include_router(hitl_sampling_router, prefix="/api/v1")
app.include_router(public_consultation_router, prefix="/api/v1")
app.include_router(dashboard_websocket_router, prefix="/api/v1", tags=["Real-time Dashboard"])


# Phase 3: Global instances for memory optimization and cache warming
memory_optimizer = None
cache_warming_service = None
redis_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize Phase 3 optimizations on startup."""
    global memory_optimizer, cache_warming_service, redis_client

    try:
        logger.info("AC Service startup: Initializing Phase 3 optimizations...")

        # Initialize memory optimization
        memory_optimizer = await initialize_memory_optimization("ac_service")
        logger.info("✅ Memory optimization initialized")

        # Initialize Redis client for caching
        redis_client = ACGSRedisClient("ac_service")
        await redis_client.initialize()
        logger.info("✅ Redis client initialized")

        # Initialize cache warming service
        cache_warming_service = get_cache_warming_service(redis_client)
        await cache_warming_service.initialize()
        logger.info("✅ Cache warming service initialized")

        logger.info("🚀 AC Service startup completed with Phase 3 optimizations")

    except Exception as e:
        logger.error(f"Failed to initialize Phase 3 optimizations: {e}")
        # Continue without optimizations rather than failing startup
        logger.warning("AC Service starting without Phase 3 optimizations")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup Phase 3 optimizations on shutdown."""
    global memory_optimizer, cache_warming_service, redis_client

    try:
        logger.info("AC Service shutdown: Cleaning up Phase 3 optimizations...")

        if memory_optimizer:
            await memory_optimizer.stop_monitoring()
            logger.info("✅ Memory optimizer stopped")

        if cache_warming_service:
            await cache_warming_service.stop_scheduled_warming()
            logger.info("✅ Cache warming service stopped")

        if redis_client:
            await redis_client.close()
            logger.info("✅ Redis client closed")

        logger.info("🛑 AC Service shutdown completed")

    except Exception as e:
        logger.error(f"Error during Phase 3 cleanup: {e}")


@app.get("/")
async def root():
    return {
        "message": "Artificial Constitution Service is running. Use /api/v1/principles/docs for API documentation."
    }


# Enhanced health check endpoint with Phase 3 optimizations
@app.get("/health")
async def health_check():
    """Enhanced health check with memory and cache status."""
    global memory_optimizer, cache_warming_service

    health_status = {"status": "ok", "service": "ac_service"}

    # Add memory optimization status
    if memory_optimizer:
        try:
            memory_stats = memory_optimizer.get_memory_stats()
            health_status["memory_optimization"] = {
                "enabled": True,
                "memory_percent": memory_stats["current_metrics"]["memory_percent"],
                "within_threshold": memory_stats["compliance"]["production_ready"],
                "monitoring_active": memory_stats["optimization_status"]["monitoring_active"]
            }
        except Exception as e:
            health_status["memory_optimization"] = {"enabled": False, "error": str(e)}
    else:
        health_status["memory_optimization"] = {"enabled": False}

    # Add cache warming status
    if cache_warming_service:
        try:
            warming_stats = cache_warming_service.get_warming_stats()
            health_status["cache_warming"] = {
                "enabled": True,
                "last_warming": warming_stats.get("last_warming"),
                "warming_active": warming_stats["configuration"]["warming_active"]
            }
        except Exception as e:
            health_status["cache_warming"] = {"enabled": False, "error": str(e)}
    else:
        health_status["cache_warming"] = {"enabled": False}

    return health_status

# Phase 3: Memory and cache monitoring endpoint
@app.get("/api/v1/monitoring/performance")
async def get_performance_monitoring():
    """Get comprehensive performance monitoring data."""
    global memory_optimizer, cache_warming_service

    monitoring_data = {
        "timestamp": "2024-01-01T00:00:00Z",  # Would use datetime.now().isoformat()
        "service": "ac_service"
    }

    # Memory optimization metrics
    if memory_optimizer:
        try:
            memory_stats = memory_optimizer.get_memory_stats()
            monitoring_data["memory_optimization"] = memory_stats
        except Exception as e:
            monitoring_data["memory_optimization"] = {"error": str(e)}
    else:
        monitoring_data["memory_optimization"] = {"status": "not_initialized"}

    # Cache warming metrics
    if cache_warming_service:
        try:
            warming_stats = cache_warming_service.get_warming_stats()
            monitoring_data["cache_warming"] = warming_stats
        except Exception as e:
            monitoring_data["cache_warming"] = {"error": str(e)}
    else:
        monitoring_data["cache_warming"] = {"status": "not_initialized"}

    return monitoring_data

# Add Prometheus metrics endpoint
app.get("/metrics")(create_metrics_endpoint())
