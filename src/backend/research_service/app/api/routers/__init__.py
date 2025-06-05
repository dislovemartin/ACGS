"""
API routers for Research Infrastructure Service
"""

from .experiment_tracking import router as experiment_tracking_router
from .data_collection import router as data_collection_router
from .analysis import router as analysis_router
from .automation import router as automation_router
from .reproducibility import router as reproducibility_router

__all__ = [
    "experiment_tracking_router",
    "data_collection_router", 
    "analysis_router",
    "automation_router",
    "reproducibility_router"
]
