from fastapi import Request, Response

async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    
    # Default, more restrictive CSP
    csp_policy = "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none';"

    # Check if the request path is for API docs, which might need less restrictive CSP
    # This is a simple check; a more robust solution might use tags or specific router knowledge.
    doc_path_prefixes = [
        "/auth/docs", "/auth/redoc",
        "/api/v1/principles/docs", "/api/v1/principles/redoc",
        "/api/v1/synthesize/docs", "/api/v1/synthesize/redoc",
        "/api/v1/verify/docs", "/api/v1/verify/redoc",
        "/api/v1/enforcement/docs", "/api/v1/enforcement/redoc",
        "/api/v1/policies/docs", "/api/v1/policies/redoc",
        "/api/v1/audit/docs", "/api/v1/audit/redoc",
        "/docs", "/redoc"  # Generic /docs for services at root path
    ]
    if any(request.url.path.startswith(prefix) for prefix in doc_path_prefixes):
        # Less restrictive CSP for API docs (Swagger UI/ReDoc)
        # Swagger UI requires 'unsafe-inline' for scripts and styles.
        # It may also load fonts or images from CDNs depending on configuration.
        # This example allows 'unsafe-inline' for scripts/styles and data URIs for images.
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; " # 'unsafe-inline' for Swagger UI scripts
            "style-src 'self' 'unsafe-inline'; "  # 'unsafe-inline' for Swagger UI styles
            "img-src 'self' data:; " # Allow data URIs for images (Swagger UI uses this)
            "object-src 'none'; "
            "frame-ancestors 'none';"
        )

    response.headers["Content-Security-Policy"] = csp_policy
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY" # Replaces 'frame-ancestors' in CSP for older browsers
    response.headers["X-XSS-Protection"] = "1; mode=block" # Modern browsers might ignore this if CSP is strong
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Optional: Permissions-Policy - can be quite restrictive and application-specific
    # response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response
