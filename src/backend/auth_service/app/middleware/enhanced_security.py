
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import re
from typing import List

class EnhancedSecurityMiddleware:
    """Enhanced security middleware for input validation and HTTP method control."""
    
    def __init__(self, app):
        self.app = app
        
        # Allowed HTTP methods per endpoint pattern
        self.endpoint_methods = {
            r"/health": ["GET"],
            r"/api/v1/.*": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            r"/docs": ["GET"],
            r"/openapi.json": ["GET"],
            r"/": ["GET"]
        }
        
        # Allowed content types for POST/PUT/PATCH requests
        self.allowed_content_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        ]
    
    async def __call__(self, request: Request, call_next):
        """Process request through security middleware."""
        
        # 1. HTTP Method Validation
        method_allowed = self.validate_http_method(request)
        if not method_allowed:
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={
                    "error": "Method Not Allowed",
                    "detail": f"Method {request.method} not allowed for {request.url.path}",
                    "allowed_methods": self.get_allowed_methods(request.url.path)
                }
            )
        
        # 2. Content Type Validation for body-containing methods
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type_valid = self.validate_content_type(request)
            if not content_type_valid:
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "error": "Unsupported Media Type",
                        "detail": f"Content-Type '{request.headers.get('content-type', 'missing')}' not supported",
                        "supported_types": self.allowed_content_types
                    }
                )
        
        # 3. Process request
        response = await call_next(request)
        return response
    
    def validate_http_method(self, request: Request) -> bool:
        """Validate HTTP method for the requested endpoint."""
        path = request.url.path
        method = request.method
        
        for pattern, allowed_methods in self.endpoint_methods.items():
            if re.match(pattern, path):
                return method in allowed_methods
        
        # Default: allow common methods for unmatched patterns
        return method in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
    
    def validate_content_type(self, request: Request) -> bool:
        """Validate content type for requests with body."""
        content_type = request.headers.get("content-type", "").lower()
        
        # Extract base content type (remove charset, boundary, etc.)
        base_content_type = content_type.split(";")[0].strip()
        
        return base_content_type in self.allowed_content_types
    
    def get_allowed_methods(self, path: str) -> List[str]:
        """Get allowed methods for a specific path."""
        for pattern, allowed_methods in self.endpoint_methods.items():
            if re.match(pattern, path):
                return allowed_methods
        
        return ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
