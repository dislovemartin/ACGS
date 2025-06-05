"""
Consolidated error handling utilities for ACGS-PGP services.

This module provides standardized error handling patterns that eliminate
duplicate error handling logic across services.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    SERVICE_ERROR = "service_error"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class ACGSException(Exception):
    """
    Base exception class for ACGS services with structured error information.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.category = category
        self.severity = severity
        self.user_message = user_message or message
        self.suggestions = suggestions or []
        self.timestamp = datetime.now(timezone.utc)
        
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "message": self.message,
                "code": self.error_code,
                "category": self.category.value,
                "severity": self.severity.value,
                "user_message": self.user_message,
                "suggestions": self.suggestions,
                "details": self.details,
                "timestamp": self.timestamp.isoformat()
            }
        }
    
    def to_json(self) -> str:
        """Convert exception to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class ValidationError(ACGSException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            **kwargs
        )


class AuthenticationError(ACGSException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            user_message="Please check your credentials and try again.",
            **kwargs
        )


class AuthorizationError(ACGSException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            user_message="You don't have permission to perform this action.",
            **kwargs
        )


class NotFoundError(ACGSException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, identifier: str = None, **kwargs):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        
        details = kwargs.get("details", {})
        details["resource"] = resource
        if identifier:
            details["identifier"] = identifier
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details=details,
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            user_message=f"The requested {resource.lower()} could not be found.",
            **kwargs
        )


class ConflictError(ACGSException):
    """Exception for resource conflict errors."""
    
    def __init__(self, message: str, resource: str = None, **kwargs):
        details = kwargs.get("details", {})
        if resource:
            details["resource"] = resource
        
        super().__init__(
            message=message,
            error_code="CONFLICT",
            details=details,
            category=ErrorCategory.CONFLICT,
            severity=ErrorSeverity.MEDIUM,
            user_message="The operation conflicts with existing data.",
            **kwargs
        )


class ServiceUnavailableError(ACGSException):
    """Exception for service unavailability errors."""
    
    def __init__(self, message: str, service_name: str = None, **kwargs):
        details = kwargs.get("details", {})
        if service_name:
            details["service"] = service_name
        
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
            category=ErrorCategory.SERVICE_ERROR,
            severity=ErrorSeverity.HIGH,
            user_message="The service is temporarily unavailable. Please try again later.",
            suggestions=["Check service status", "Retry after a few minutes"],
            **kwargs
        )


class DatabaseError(ACGSException):
    """Exception for database errors."""
    
    def __init__(self, message: str, operation: str = None, **kwargs):
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            user_message="A database error occurred. Please try again.",
            **kwargs
        )


class ConfigurationError(ACGSException):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            user_message="A configuration error occurred. Please contact support.",
            **kwargs
        )


def handle_service_error(
    error: Exception,
    service_name: str,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> ACGSException:
    """
    Handle and convert service errors to standardized ACGS exceptions.
    
    Args:
        error: Original exception
        service_name: Name of the service where error occurred
        operation: Operation being performed when error occurred
        context: Additional context information
        
    Returns:
        Standardized ACGSException
    """
    context = context or {}
    
    # If already an ACGS exception, add context and return
    if isinstance(error, ACGSException):
        error.details.update({
            "service": service_name,
            "operation": operation,
            **context
        })
        return error
    
    # Convert common exception types
    error_message = str(error)
    error_type = type(error).__name__
    
    details = {
        "service": service_name,
        "operation": operation,
        "original_error": error_type,
        "traceback": traceback.format_exc(),
        **context
    }
    
    # Map common exceptions to ACGS exceptions
    if "connection" in error_message.lower() or "timeout" in error_message.lower():
        return ServiceUnavailableError(
            f"Service connection error in {service_name}: {error_message}",
            service_name=service_name,
            details=details
        )
    
    if "permission" in error_message.lower() or "access" in error_message.lower():
        return AuthorizationError(
            f"Access error in {service_name}: {error_message}",
            details=details
        )
    
    if "not found" in error_message.lower():
        return NotFoundError(
            "Resource",
            details=details
        )
    
    # Default to generic service error
    return ACGSException(
        f"Service error in {service_name}: {error_message}",
        error_code="SERVICE_ERROR",
        details=details,
        category=ErrorCategory.SERVICE_ERROR,
        severity=ErrorSeverity.HIGH
    )


def log_error(
    error: Exception,
    service_name: str,
    operation: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None
):
    """
    Log error with standardized format and context.
    
    Args:
        error: Exception to log
        service_name: Service where error occurred
        operation: Operation being performed
        user_id: ID of user associated with error (if any)
        request_id: Request ID for tracing
        extra_context: Additional context to log
    """
    context = {
        "service": service_name,
        "operation": operation,
        "error_type": type(error).__name__,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if user_id:
        context["user_id"] = user_id
    if request_id:
        context["request_id"] = request_id
    if extra_context:
        context.update(extra_context)
    
    if isinstance(error, ACGSException):
        context.update({
            "error_code": error.error_code,
            "category": error.category.value,
            "severity": error.severity.value
        })
        
        # Log based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error.message}", extra=context)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {error.message}", extra=context)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error.message}", extra=context)
        else:
            logger.info(f"Low severity error: {error.message}", extra=context)
    else:
        logger.error(f"Unhandled error: {str(error)}", extra=context, exc_info=True)


def create_error_response(
    error: Exception,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Create standardized error response for API endpoints.
    
    Args:
        error: Exception to convert to response
        include_traceback: Whether to include traceback in response
        
    Returns:
        Standardized error response dictionary
    """
    if isinstance(error, ACGSException):
        response = error.to_dict()
        if not include_traceback and "traceback" in response["error"].get("details", {}):
            del response["error"]["details"]["traceback"]
        return response
    
    # Handle non-ACGS exceptions
    return {
        "error": {
            "message": str(error),
            "code": "INTERNAL_ERROR",
            "category": ErrorCategory.UNKNOWN.value,
            "severity": ErrorSeverity.HIGH.value,
            "user_message": "An unexpected error occurred. Please try again.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
