"""
Consolidated validation utilities for ACGS-PGP services.

This module provides common validation functions that eliminate
duplicate validation logic across services.
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime
from pydantic import BaseModel, ValidationError as PydanticValidationError
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error for ACGS services."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)


class ValidationResult:
    """Result of validation operation."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        """Add validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning."""
        self.warnings.append(warning)


def validate_uuid(value: str, field_name: str = "id") -> str:
    """
    Validate UUID format.
    
    Args:
        value: UUID string to validate
        field_name: Name of the field being validated
        
    Returns:
        Validated UUID string
        
    Raises:
        ValidationError: If UUID is invalid
    """
    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid UUID format for {field_name}: {value}",
            field=field_name,
            value=value
        )


def validate_email(email: str) -> str:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Validated email address
        
    Raises:
        ValidationError: If email is invalid
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError(
            f"Invalid email format: {email}",
            field="email",
            value=email
        )
    return email.lower()


def validate_username(username: str) -> str:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        Validated username
        
    Raises:
        ValidationError: If username is invalid
    """
    if not username or len(username) < 3:
        raise ValidationError(
            "Username must be at least 3 characters long",
            field="username",
            value=username
        )
    
    if len(username) > 50:
        raise ValidationError(
            "Username must be less than 50 characters",
            field="username", 
            value=username
        )
    
    username_pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(username_pattern, username):
        raise ValidationError(
            "Username can only contain letters, numbers, underscores, and hyphens",
            field="username",
            value=username
        )
    
    return username


def validate_password(password: str) -> ValidationResult:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        ValidationResult with validation status and messages
    """
    result = ValidationResult(True)
    
    if not password:
        result.add_error("Password is required")
        return result
    
    if len(password) < 8:
        result.add_error("Password must be at least 8 characters long")
    
    if len(password) > 128:
        result.add_error("Password must be less than 128 characters")
    
    if not re.search(r'[A-Z]', password):
        result.add_warning("Password should contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        result.add_warning("Password should contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        result.add_warning("Password should contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result.add_warning("Password should contain at least one special character")
    
    return result


def validate_json_data(data: Any, required_fields: List[str] = None) -> ValidationResult:
    """
    Validate JSON data structure.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(True)
    
    if not isinstance(data, dict):
        result.add_error("Data must be a JSON object")
        return result
    
    if required_fields:
        for field in required_fields:
            if field not in data:
                result.add_error(f"Required field missing: {field}")
            elif data[field] is None:
                result.add_error(f"Required field cannot be null: {field}")
    
    return result


def validate_pagination_params(page: int = 1, size: int = 10, max_size: int = 100) -> Dict[str, int]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (1-based)
        size: Page size
        max_size: Maximum allowed page size
        
    Returns:
        Validated pagination parameters
        
    Raises:
        ValidationError: If parameters are invalid
    """
    if page < 1:
        raise ValidationError(
            "Page number must be greater than 0",
            field="page",
            value=page
        )
    
    if size < 1:
        raise ValidationError(
            "Page size must be greater than 0",
            field="size",
            value=size
        )
    
    if size > max_size:
        raise ValidationError(
            f"Page size cannot exceed {max_size}",
            field="size",
            value=size
        )
    
    return {"page": page, "size": size}


def validate_request(data: Dict[str, Any], schema: Type[BaseModel]) -> BaseModel:
    """
    Validate request data against Pydantic schema.
    
    Args:
        data: Request data to validate
        schema: Pydantic model schema
        
    Returns:
        Validated model instance
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        return schema(**data)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")
        
        raise ValidationError(
            f"Validation failed: {'; '.join(error_messages)}",
            field="request_body",
            value=data
        )


def validate_response(data: Any) -> Dict[str, Any]:
    """
    Validate response data format.
    
    Args:
        data: Response data to validate
        
    Returns:
        Validated response data
        
    Raises:
        ValidationError: If response format is invalid
    """
    if data is None:
        return {}
    
    if isinstance(data, dict):
        return data
    
    if isinstance(data, (list, str, int, float, bool)):
        return {"data": data}
    
    # Try to convert to dict if it has dict-like attributes
    if hasattr(data, "__dict__"):
        return data.__dict__
    
    raise ValidationError(
        f"Invalid response data type: {type(data)}",
        field="response",
        value=data
    )


def validate_service_name(service_name: str) -> str:
    """
    Validate ACGS service name.
    
    Args:
        service_name: Service name to validate
        
    Returns:
        Validated service name
        
    Raises:
        ValidationError: If service name is invalid
    """
    valid_services = {
        "auth_service", "ac_service", "fv_service", 
        "gs_service", "pgc_service", "integrity_service", "ec_service"
    }
    
    if service_name not in valid_services:
        raise ValidationError(
            f"Invalid service name: {service_name}. Valid services: {', '.join(valid_services)}",
            field="service_name",
            value=service_name
        )
    
    return service_name


def validate_timestamp(timestamp: Union[str, datetime]) -> datetime:
    """
    Validate and parse timestamp.
    
    Args:
        timestamp: Timestamp to validate (ISO format string or datetime)
        
    Returns:
        Validated datetime object
        
    Raises:
        ValidationError: If timestamp is invalid
    """
    if isinstance(timestamp, datetime):
        return timestamp
    
    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError(
                f"Invalid timestamp format: {timestamp}. Expected ISO format.",
                field="timestamp",
                value=timestamp
            )
    
    raise ValidationError(
        f"Invalid timestamp type: {type(timestamp)}",
        field="timestamp",
        value=timestamp
    )
