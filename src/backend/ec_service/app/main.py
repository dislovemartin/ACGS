"""
ACGS-PGP Evolutionary Computation (EC) Service

This service provides WINA-optimized oversight and governance for evolutionary computation
systems within the AlphaEvolve-ACGS framework. It integrates constitutional principles
with EC algorithms to ensure democratic oversight and efficiency optimization.

Key Features:
- WINA-optimized EC layer oversight coordination
- AlphaEvolve integration for constitutional governance
- Real-time performance monitoring and reporting
- Constitutional compliance verification for EC processes
- Adaptive learning and feedback mechanisms
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1.oversight import router as oversight_router
from app.api.v1.alphaevolve import router as alphaevolve_router
from app.api.v1.reporting import router as reporting_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.wina_oversight import router as wina_oversight_router
from shared.wina.performance_api import router as wina_performance_router, set_collector_getter
from app.core.wina_oversight_coordinator import WINAECOversightCoordinator
from app.services.gs_client import gs_service_client
from app.services.ac_client import ac_service_client
from app.services.pgc_client import pgc_service_client
from shared.security_middleware import add_security_middleware
from shared.security_config import security_config
from shared.metrics import get_metrics, metrics_middleware, create_metrics_endpoint
from shared import get_config

# Load centralized configuration
config = get_config()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global WINA oversight coordinator instance
wina_coordinator: WINAECOversightCoordinator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global wina_coordinator
    
    logger.info("Starting ACGS-PGP Evolutionary Computation Service...")
    
    try:
        # Initialize WINA oversight coordinator
        wina_coordinator = WINAECOversightCoordinator(enable_wina=True)
        await wina_coordinator.initialize_constitutional_principles()
        
        # Configure performance API to use coordinator's collector
        set_collector_getter(get_wina_performance_collector)
        logger.info("Performance API configured with WINA coordinator collector")
        
        # Initialize service clients
        logger.info("Initializing service clients...")
        
        # Start background monitoring tasks
        monitoring_task = asyncio.create_task(background_monitoring())
        
        logger.info("EC Service started successfully with WINA optimization enabled")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start EC Service: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down ACGS-PGP Evolutionary Computation Service...")
        
        # Cancel background tasks
        if 'monitoring_task' in locals():
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Close service clients
        await gs_service_client.close()
        await ac_service_client.close()
        await pgc_service_client.close()
        
        logger.info("EC Service shutdown complete")


async def background_monitoring():
    """Background task for continuous monitoring and optimization."""
    while True:
        try:
            if wina_coordinator:
                # Perform periodic health checks and optimization
                await wina_coordinator._perform_health_check()
            
            # Sleep for monitoring interval
            await asyncio.sleep(30)  # 30 seconds
            
        except asyncio.CancelledError:
            logger.info("Background monitoring task cancelled")
            break
        except Exception as e:
            logger.error(f"Background monitoring error: {e}")
            await asyncio.sleep(60)  # Wait longer on error


app = FastAPI(
    title="ACGS-PGP Evolutionary Computation (EC) Service",
    description="WINA-optimized oversight and governance for evolutionary computation systems",
    version=config.get('api_version', 'v1'),
    debug=config.get('debug', False),
    lifespan=lifespan
)

# Initialize metrics for EC service
metrics = get_metrics("ec_service")

# Add enhanced security middleware (clean pattern like fv_service)
add_security_middleware(app)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add metrics middleware - commented out to avoid conflicts
# app.middleware("http")(metrics_middleware("ec_service"))

# Include API routers
app.include_router(oversight_router, prefix="/api/v1/oversight", tags=["WINA Oversight"])
app.include_router(wina_oversight_router, prefix="/api/v1", tags=["WINA EC Oversight"])
app.include_router(alphaevolve_router, prefix="/api/v1/alphaevolve", tags=["AlphaEvolve Integration"])
app.include_router(reporting_router, prefix="/api/v1/reporting", tags=["Reporting & Analytics"])
app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["Performance Monitoring"])
app.include_router(wina_performance_router, prefix="/api/v1/wina/performance", tags=["WINA Performance Monitoring"])

# Add metrics endpoint
app.get("/metrics")(create_metrics_endpoint())


@app.get("/health")
async def health_check():
    """Health check endpoint with WINA coordinator status."""
    global wina_coordinator
    
    coordinator_status = "unknown"
    if wina_coordinator:
        try:
            # Check coordinator health
            coordinator_status = "healthy" if wina_coordinator.enable_wina else "disabled"
        except Exception as e:
            coordinator_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "evolutionary_computation",
        "timestamp": datetime.utcnow().isoformat(),
        "version": config.get('api_version', 'v1'),
        "wina_coordinator": coordinator_status,
        "features": {
            "wina_optimization": wina_coordinator.enable_wina if wina_coordinator else False,
            "constitutional_oversight": True,
            "alphaevolve_integration": True,
            "performance_monitoring": True,
            "wina_performance_api": True,
            "real_time_metrics": True,
            "performance_dashboard": True
        },
        "performance_monitoring": {
            "collector_available": hasattr(wina_coordinator, 'performance_collector') if wina_coordinator else False,
            "monitoring_active": wina_coordinator.performance_collector.monitoring_active if (
                wina_coordinator and hasattr(wina_coordinator, 'performance_collector')
            ) else False,
            "monitoring_level": wina_coordinator.performance_collector.monitoring_level.value if (
                wina_coordinator and hasattr(wina_coordinator, 'performance_collector')
            ) else "unknown"
        }
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "message": "ACGS-PGP Evolutionary Computation Service",
        "description": "WINA-optimized oversight and governance for evolutionary computation systems",
        "version": config.get('api_version', 'v1'),
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "features": [
            "WINA-optimized EC oversight",
            "AlphaEvolve constitutional integration",
            "Real-time performance monitoring",
            "Constitutional compliance verification",
            "Adaptive learning mechanisms",
            "Comprehensive WINA performance metrics",
            "REST API for performance data access",
            "Prometheus metrics export",
            "Performance dashboard and alerts"
        ],
        "api_endpoints": {
            "oversight": "/api/v1/oversight/*",
            "wina_oversight": "/api/v1/wina-oversight/*",
            "alphaevolve": "/api/v1/alphaevolve/*",
            "reporting": "/api/v1/reporting/*",
            "monitoring": "/api/v1/monitoring/*",
            "wina_performance": "/api/v1/wina/performance/*"
        }
    }


def get_wina_coordinator() -> WINAECOversightCoordinator:
    """Get the global WINA oversight coordinator instance."""
    global wina_coordinator
    if not wina_coordinator:
        raise RuntimeError("WINA oversight coordinator not initialized")
    return wina_coordinator


def get_wina_performance_collector():
    """Get the WINA performance collector from the coordinator."""
    coordinator = get_wina_coordinator()
    return getattr(coordinator, 'performance_collector', None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8007,  # EC service port (matches docker-compose internal port)
        reload=True,
        log_level="info"
    )
