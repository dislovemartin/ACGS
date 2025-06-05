#!/usr/bin/env python3
"""
ACGS-PGP Input Validation Fix Script
Phase 2.1: Security Hardening - Input Validation Enhancement

This script fixes input validation issues across all ACGS-PGP services
by implementing proper HTTP method and content type validation middleware.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class InputValidationFixer:
    """Fix input validation issues across ACGS-PGP services."""
    
    def __init__(self):
        self.services = {
            "auth_service": "http://localhost:8000",
            "ac_service": "http://localhost:8001", 
            "integrity_service": "http://localhost:8002",
            "fv_service": "http://localhost:8003",
            "gs_service": "http://localhost:8004",
            "pgc_service": "http://localhost:8005",
            "ec_service": "http://localhost:8006"
        }
        self.results = []
    
    async def test_current_validation(self) -> Dict[str, Any]:
        """Test current input validation status."""
        print("🔍 Testing Current Input Validation Status...")
        print("=" * 60)
        
        validation_results = {}
        
        async with aiohttp.ClientSession() as session:
            for service_name, base_url in self.services.items():
                print(f"Testing {service_name}...")
                
                try:
                    # Test POST to health endpoint with invalid content type
                    headers = {'Content-Type': 'text/plain'}
                    data = "invalid data"
                    
                    async with session.post(f"{base_url}/health", headers=headers, data=data) as response:
                        status_code = response.status
                        response_text = await response.text()
                        
                        validation_results[service_name] = {
                            "status_code": status_code,
                            "expected": [405, 415],
                            "validation_working": status_code in [405, 415],
                            "response_preview": response_text[:200] if response_text else "No response"
                        }
                        
                        status_emoji = "✅" if status_code in [405, 415] else "❌"
                        print(f"  {status_emoji} {service_name}: {status_code} ({'PASS' if status_code in [405, 415] else 'FAIL'})")
                        
                except Exception as e:
                    validation_results[service_name] = {
                        "error": str(e),
                        "validation_working": False
                    }
                    print(f"  ❌ {service_name}: ERROR - {str(e)}")
        
        return validation_results
    
    def generate_middleware_code(self) -> str:
        """Generate enhanced security middleware code."""
        return '''
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
'''
    
    def create_service_patches(self) -> Dict[str, str]:
        """Create patches for each service to add enhanced middleware."""
        patches = {}
        
        service_paths = {
            "auth_service": "src/backend/auth_service/app/main.py",
            "ac_service": "src/backend/ac_service/app/main.py",
            "integrity_service": "src/backend/integrity_service/app/main.py", 
            "fv_service": "src/backend/fv_service/app/main.py",
            "gs_service": "src/backend/gs_service/app/main.py",
            "pgc_service": "src/backend/pgc_service/app/main.py",
            "ec_service": "src/backend/ec_service/app/main.py"
        }
        
        for service_name, service_path in service_paths.items():
            patches[service_name] = {
                "path": service_path,
                "middleware_import": "from app.middleware.enhanced_security import EnhancedSecurityMiddleware",
                "middleware_registration": "app.add_middleware(EnhancedSecurityMiddleware)"
            }
        
        return patches
    
    async def apply_fixes(self) -> Dict[str, Any]:
        """Apply input validation fixes to all services."""
        print("\n🔧 Applying Input Validation Fixes...")
        print("=" * 60)
        
        # 1. Generate middleware code
        middleware_code = self.generate_middleware_code()
        
        # 2. Create service patches
        patches = self.create_service_patches()
        
        # 3. Save middleware code to each service
        for service_name, patch_info in patches.items():
            service_dir = Path(patch_info["path"]).parent
            middleware_dir = service_dir / "middleware"
            middleware_dir.mkdir(exist_ok=True)
            
            # Create __init__.py
            (middleware_dir / "__init__.py").write_text("")
            
            # Create enhanced_security.py
            middleware_file = middleware_dir / "enhanced_security.py"
            middleware_file.write_text(middleware_code)
            
            print(f"✅ Created middleware for {service_name}")
        
        return {
            "middleware_created": True,
            "services_updated": list(patches.keys()),
            "next_steps": [
                "Update main.py files to import and register middleware",
                "Restart services to apply changes",
                "Re-run validation tests"
            ]
        }
    
    async def generate_fix_report(self) -> Dict[str, Any]:
        """Generate comprehensive fix report."""
        print("\n📊 Generating Input Validation Fix Report...")
        
        # Test current status
        current_status = await self.test_current_validation()
        
        # Apply fixes
        fix_results = await self.apply_fixes()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "2.1 Security Hardening - Input Validation Fix",
            "current_validation_status": current_status,
            "fixes_applied": fix_results,
            "summary": {
                "services_tested": len(self.services),
                "services_failing_validation": len([s for s, r in current_status.items() if not r.get("validation_working", False)]),
                "middleware_files_created": len(fix_results.get("services_updated", [])),
                "fix_success": fix_results.get("middleware_created", False)
            },
            "recommendations": [
                "Update each service's main.py to import and register EnhancedSecurityMiddleware",
                "Restart all Docker services to apply middleware changes", 
                "Re-run security validation tests to verify fixes",
                "Monitor service logs for any middleware-related issues",
                "Consider implementing additional input sanitization for specific endpoints"
            ]
        }
        
        return report

async def main():
    """Main function to fix input validation issues."""
    print("🛡️ ACGS-PGP Input Validation Fix")
    print("Phase 2.1: Security Hardening Enhancement")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    fixer = InputValidationFixer()
    report = await fixer.generate_fix_report()
    
    # Save report
    report_file = f"input_validation_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Fix report saved to: {report_file}")
    print("\n🎯 Next Steps:")
    for step in report["recommendations"]:
        print(f"  • {step}")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())
