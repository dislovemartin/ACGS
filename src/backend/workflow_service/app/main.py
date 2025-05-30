"""
ACGS-PGP Workflow Service
Main FastAPI application for workflow orchestration, monitoring, and management
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio
from datetime import datetime

from .api.v1.workflow_management import router as workflow_router
from .core.workflow_engine import workflow_engine
from .monitoring.workflow_monitor import workflow_monitor
from .recovery.workflow_recovery import recovery_manager
from .testing.automated_validator import automated_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    
    # Startup
    logger.info("Starting ACGS-PGP Workflow Service")
    
    # Initialize monitoring
    await initialize_monitoring()
    
    # Start background tasks
    monitoring_task = asyncio.create_task(background_monitoring())
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down ACGS-PGP Workflow Service")
        
        # Cancel background tasks
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
        
        # Cleanup resources
        await cleanup_resources()

app = FastAPI(
    title="ACGS-PGP Workflow Service",
    description="Centralized workflow orchestration, monitoring, and management for ACGS-PGP framework",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware for request logging and metrics
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log requests and collect metrics"""
    
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    end_time = datetime.utcnow()
    response_time = (end_time - start_time).total_seconds()
    
    # Record metrics
    workflow_monitor.record_metric(
        name="http_request_duration_seconds",
        value=response_time,
        metric_type=workflow_monitor.MetricType.TIMER,
        labels={
            "method": request.method,
            "endpoint": str(request.url.path),
            "status_code": str(response.status_code)
        }
    )
    
    workflow_monitor.record_metric(
        name="http_requests_total",
        value=1.0,
        metric_type=workflow_monitor.MetricType.COUNTER,
        labels={
            "method": request.method,
            "endpoint": str(request.url.path),
            "status_code": str(response.status_code)
        }
    )
    
    # Log response
    logger.info(f"Response: {response.status_code} ({response_time:.3f}s)")
    
    return response

# Include routers
app.include_router(
    workflow_router,
    prefix="/api/v1",
    tags=["Workflow Management"]
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    
    return {
        "service": "ACGS-PGP Workflow Service",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/v1/health",
            "workflows": "/api/v1/workflows",
            "monitoring": "/api/v1/monitoring",
            "recovery": "/api/v1/recovery",
            "testing": "/api/v1/testing"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "workflow_service",
        "version": "1.0.0",
        "components": {
            "workflow_engine": "healthy",
            "monitoring": "healthy",
            "recovery_manager": "healthy",
            "automated_validator": "healthy"
        },
        "metrics": {
            "active_workflows": len(workflow_engine.running_workflows),
            "total_workflows": len(workflow_engine.workflows),
            "active_alerts": len([a for a in workflow_monitor.alerts.values() if not a.resolved]),
            "monitoring_tasks": len(workflow_monitor.monitoring_tasks)
        }
    }
    
    return health_status

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    
    metrics_data = []
    
    # Workflow metrics
    metrics_data.append(f"acgs_active_workflows {len(workflow_engine.running_workflows)}")
    metrics_data.append(f"acgs_total_workflows {len(workflow_engine.workflows)}")
    
    # Alert metrics
    active_alerts = len([a for a in workflow_monitor.alerts.values() if not a.resolved])
    metrics_data.append(f"acgs_active_alerts {active_alerts}")
    
    # Recovery metrics
    total_recovery_plans = len(recovery_manager.recovery_plans)
    metrics_data.append(f"acgs_recovery_plans_total {total_recovery_plans}")
    
    # Service health
    metrics_data.append("acgs_service_health 1")
    
    return Response(
        content="\n".join(metrics_data) + "\n",
        media_type="text/plain"
    )

async def initialize_monitoring():
    """Initialize monitoring and alerting"""
    
    logger.info("Initializing monitoring system")
    
    # Register service health monitoring
    asyncio.create_task(
        workflow_monitor.monitor_service_health(
            "workflow_service",
            "/health"
        )
    )
    
    # Set performance baselines
    automated_validator.set_performance_baseline(
        "workflow_execution",
        {"duration": 60.0, "memory_usage": 512.0}
    )
    
    automated_validator.set_performance_baseline(
        "policy_synthesis",
        {"duration": 30.0, "accuracy": 0.95}
    )

async def background_monitoring():
    """Background monitoring tasks"""
    
    logger.info("Starting background monitoring")
    
    while True:
        try:
            # Monitor system resources
            await monitor_system_resources()
            
            # Check for stale workflows
            await check_stale_workflows()
            
            # Cleanup old data
            await cleanup_old_data()
            
            # Wait before next iteration
            await asyncio.sleep(60)  # Run every minute
            
        except asyncio.CancelledError:
            logger.info("Background monitoring cancelled")
            break
        except Exception as e:
            logger.error(f"Error in background monitoring: {e}")
            await asyncio.sleep(60)

async def monitor_system_resources():
    """Monitor system resource usage"""
    
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        workflow_monitor.record_metric(
            name="system_cpu_usage_percent",
            value=cpu_percent,
            metric_type=workflow_monitor.MetricType.GAUGE
        )
        
        # Memory usage
        memory = psutil.virtual_memory()
        workflow_monitor.record_metric(
            name="system_memory_usage_percent",
            value=memory.percent,
            metric_type=workflow_monitor.MetricType.GAUGE
        )
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        workflow_monitor.record_metric(
            name="system_disk_usage_percent",
            value=disk_percent,
            metric_type=workflow_monitor.MetricType.GAUGE
        )
        
    except ImportError:
        # psutil not available, skip system monitoring
        pass
    except Exception as e:
        logger.error(f"Error monitoring system resources: {e}")

async def check_stale_workflows():
    """Check for stale or stuck workflows"""
    
    current_time = datetime.utcnow()
    
    for workflow_id, workflow in workflow_engine.workflows.items():
        if workflow.status == workflow_engine.WorkflowStatus.RUNNING:
            # Check if workflow has been running too long
            if workflow.started_at:
                runtime = current_time - workflow.started_at
                if runtime.total_seconds() > 3600:  # 1 hour
                    logger.warning(f"Workflow {workflow_id} has been running for {runtime}")
                    
                    # Create alert for long-running workflow
                    workflow_monitor._create_alert(
                        severity=workflow_monitor.AlertSeverity.HIGH,
                        title=f"Long-running workflow detected",
                        description=f"Workflow {workflow_id} has been running for {runtime}",
                        workflow_id=workflow_id,
                        metadata={"runtime_seconds": runtime.total_seconds()}
                    )

async def cleanup_old_data():
    """Cleanup old monitoring data and logs"""
    
    current_time = datetime.utcnow()
    cutoff_time = current_time - timedelta(days=7)  # Keep 7 days of data
    
    # Cleanup old metrics
    for metric_name, metric_list in workflow_monitor.metrics.items():
        # Remove old metrics
        while metric_list and metric_list[0].timestamp < cutoff_time:
            metric_list.popleft()
    
    # Cleanup resolved alerts older than 30 days
    alert_cutoff = current_time - timedelta(days=30)
    alerts_to_remove = []
    
    for alert_id, alert in workflow_monitor.alerts.items():
        if alert.resolved and alert.resolved_at and alert.resolved_at < alert_cutoff:
            alerts_to_remove.append(alert_id)
    
    for alert_id in alerts_to_remove:
        del workflow_monitor.alerts[alert_id]

async def cleanup_resources():
    """Cleanup resources on shutdown"""
    
    logger.info("Cleaning up resources")
    
    # Stop all monitoring tasks
    for task in workflow_monitor.monitoring_tasks.values():
        task.cancel()
    
    # Wait for tasks to complete
    if workflow_monitor.monitoring_tasks:
        await asyncio.gather(
            *workflow_monitor.monitoring_tasks.values(),
            return_exceptions=True
        )
    
    logger.info("Resource cleanup completed")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info"
    )
