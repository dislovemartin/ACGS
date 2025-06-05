"""
Consolidated formatting utilities for ACGS-PGP services.

This module provides standardized data formatting functions that eliminate
duplicate formatting logic across services.
"""

import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"


class DateTimeFormat(Enum):
    """Standard datetime format options."""
    ISO = "iso"
    TIMESTAMP = "timestamp"
    HUMAN = "human"


def standardize_timestamps(data: Any) -> Any:
    """
    Recursively standardize datetime objects to ISO format strings.
    
    Args:
        data: Data structure containing datetime objects
        
    Returns:
        Data structure with standardized timestamp strings
    """
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: standardize_timestamps(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [standardize_timestamps(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(standardize_timestamps(item) for item in data)
    else:
        return data


def format_datetime(
    dt: datetime,
    format_type: DateTimeFormat = DateTimeFormat.ISO,
    timezone_aware: bool = True
) -> str:
    """
    Format datetime object according to specified format.
    
    Args:
        dt: Datetime object to format
        format_type: Format type to use
        timezone_aware: Whether to include timezone information
        
    Returns:
        Formatted datetime string
    """
    if not isinstance(dt, datetime):
        raise ValueError(f"Expected datetime object, got {type(dt)}")
    
    # Ensure timezone awareness
    if timezone_aware and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    if format_type == DateTimeFormat.ISO:
        return dt.isoformat()
    elif format_type == DateTimeFormat.TIMESTAMP:
        return str(int(dt.timestamp()))
    elif format_type == DateTimeFormat.HUMAN:
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        return dt.isoformat()


def format_response(
    data: Any = None,
    status: ResponseStatus = ResponseStatus.SUCCESS,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    pagination: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format standardized API response.
    
    Args:
        data: Response data
        status: Response status
        message: Optional message
        metadata: Optional metadata
        pagination: Optional pagination information
        
    Returns:
        Standardized response dictionary
    """
    response = {
        "status": status.value,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if data is not None:
        response["data"] = standardize_timestamps(data)
    
    if message:
        response["message"] = message
    
    if metadata:
        response["metadata"] = standardize_timestamps(metadata)
    
    if pagination:
        response["pagination"] = pagination
    
    return response


def format_error(
    error_message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Format standardized error response.
    
    Args:
        error_message: Error message
        error_code: Error code
        details: Optional error details
        suggestions: Optional suggestions for resolution
        
    Returns:
        Standardized error response dictionary
    """
    error_response = {
        "status": ResponseStatus.ERROR.value,
        "error": {
            "message": error_message,
            "code": error_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    
    if details:
        error_response["error"]["details"] = standardize_timestamps(details)
    
    if suggestions:
        error_response["error"]["suggestions"] = suggestions
    
    return error_response


def format_pagination(
    page: int,
    size: int,
    total_items: int,
    total_pages: Optional[int] = None
) -> Dict[str, Any]:
    """
    Format pagination information.
    
    Args:
        page: Current page number (1-based)
        size: Page size
        total_items: Total number of items
        total_pages: Total number of pages (calculated if not provided)
        
    Returns:
        Pagination information dictionary
    """
    if total_pages is None:
        total_pages = (total_items + size - 1) // size  # Ceiling division
    
    return {
        "page": page,
        "size": size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }


def format_list_response(
    items: List[Any],
    page: int = 1,
    size: int = 10,
    total_items: Optional[int] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format paginated list response.
    
    Args:
        items: List of items for current page
        page: Current page number
        size: Page size
        total_items: Total number of items (defaults to len(items))
        message: Optional message
        
    Returns:
        Formatted list response with pagination
    """
    if total_items is None:
        total_items = len(items)
    
    pagination = format_pagination(page, size, total_items)
    
    return format_response(
        data=items,
        message=message,
        pagination=pagination
    )


def format_health_check(
    service_name: str,
    status: str = "healthy",
    version: Optional[str] = None,
    dependencies: Optional[Dict[str, str]] = None,
    metrics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format health check response.
    
    Args:
        service_name: Name of the service
        status: Health status (healthy, unhealthy, degraded)
        version: Service version
        dependencies: Status of service dependencies
        metrics: Service metrics
        
    Returns:
        Formatted health check response
    """
    health_data = {
        "service": service_name,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if version:
        health_data["version"] = version
    
    if dependencies:
        health_data["dependencies"] = dependencies
    
    if metrics:
        health_data["metrics"] = standardize_timestamps(metrics)
    
    return format_response(data=health_data)


def format_metrics(
    metrics: Dict[str, Any],
    service_name: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Format metrics response.
    
    Args:
        metrics: Metrics data
        service_name: Name of the service
        time_range: Time range for metrics
        
    Returns:
        Formatted metrics response
    """
    metadata = {}
    
    if service_name:
        metadata["service"] = service_name
    
    if time_range:
        metadata["time_range"] = time_range
    
    return format_response(
        data=standardize_timestamps(metrics),
        metadata=metadata
    )


def sanitize_for_json(data: Any) -> Any:
    """
    Sanitize data for JSON serialization.
    
    Args:
        data: Data to sanitize
        
    Returns:
        JSON-serializable data
    """
    if isinstance(data, (str, int, float, bool, type(None))):
        return data
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, Enum):
        return data.value
    elif isinstance(data, dict):
        return {key: sanitize_for_json(value) for key, value in data.items()}
    elif isinstance(data, (list, tuple)):
        return [sanitize_for_json(item) for item in data]
    elif hasattr(data, "__dict__"):
        return sanitize_for_json(data.__dict__)
    else:
        return str(data)


def safe_json_dumps(data: Any, indent: Optional[int] = None) -> str:
    """
    Safely serialize data to JSON string.
    
    Args:
        data: Data to serialize
        indent: JSON indentation
        
    Returns:
        JSON string
    """
    try:
        sanitized_data = sanitize_for_json(data)
        return json.dumps(sanitized_data, indent=indent, ensure_ascii=False)
    except Exception as e:
        logger.error(f"JSON serialization error: {e}")
        return json.dumps({"error": "Serialization failed", "message": str(e)})


def format_validation_errors(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format validation errors for API response.
    
    Args:
        errors: List of validation error dictionaries
        
    Returns:
        Formatted validation error response
    """
    formatted_errors = []
    
    for error in errors:
        formatted_error = {
            "field": error.get("field", "unknown"),
            "message": error.get("message", "Validation failed"),
            "value": error.get("value")
        }
        formatted_errors.append(formatted_error)
    
    return format_error(
        error_message="Validation failed",
        error_code="VALIDATION_ERROR",
        details={"validation_errors": formatted_errors}
    )


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
