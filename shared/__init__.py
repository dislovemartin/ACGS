# ACGS/shared/__init__.py
# This file makes 'shared' a Python package.

from .database import Base, metadata, get_async_db, async_engine, AsyncSessionLocal
from . import models
from . import schemas
from . import utils
from .security_middleware import add_security_headers # Assuming this function exists

# You can optionally define __all__ to control what `from shared import *` imports
__all__ = [
    "Base",
    "metadata",
    "get_async_db",
    "async_engine",
    "AsyncSessionLocal",
    "models",
    "schemas",
    "utils",
    "add_security_headers",
]
