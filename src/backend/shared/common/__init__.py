"""
Consolidated common utilities for ACGS-PGP services.

This module provides shared utilities that eliminate code duplication
across the ACGS microservices architecture.
"""

from .http_clients import ACGSHttpClient, ServiceClient
from .validation import validate_request, validate_response, ValidationError
from .formatting import format_response, format_error, standardize_timestamps
from .error_handling import ACGSException, handle_service_error, log_error

__all__ = [
    "ACGSHttpClient",
    "ServiceClient", 
    "validate_request",
    "validate_response",
    "ValidationError",
    "format_response",
    "format_error",
    "standardize_timestamps",
    "ACGSException",
    "handle_service_error",
    "log_error"
]
