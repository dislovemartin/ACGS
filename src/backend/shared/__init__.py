# ACGS/shared/__init__.py
# This file makes 'shared' a Python package.

# Import legacy components for backward compatibility
try:
    from . import models
    from . import schemas
    from . import utils
    from .utils import ACGSConfig, get_config, reset_config
except ImportError:
    # Handle missing legacy modules gracefully
    pass

# Import new Phase 2 components
from . import common
from . import di
from . import events
from . import service_mesh

# You can optionally define __all__ to control what `from shared import *` imports
__all__ = [
    "models",
    "schemas",
    "utils",
    "ACGSConfig",
    "get_config",
    "reset_config",
    "common",
    "di",
    "events",
    "service_mesh",
]
