#!/usr/bin/env python3
"""
Direct middleware testing script to debug input validation issues.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_single_service(service_name: str, port: int):
    """Test a single service with detailed error reporting."""
    print(f"\n🔍 Testing {service_name} on port {port}")
    print("-" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test 1: GET /health (should work)
        try:
            async with session.get(f"http://localhost:{port}/health") as response:
                print(f"GET /health: {response.status} - {'✅ PASS' if response.status == 200 else '❌ FAIL'}")
                if response.status != 200:
                    text = await response.text()
                    print(f"  Response: {text[:200]}")
        except Exception as e:
            print(f"GET /health: ERROR - {str(e)}")
        
        # Test 2: POST /health with valid content type (should be 405 - Method Not Allowed)
        try:
            headers = {'Content-Type': 'application/json'}
            data = '{"test": "data"}'
            async with session.post(f"http://localhost:{port}/health", headers=headers, data=data) as response:
                print(f"POST /health (valid content): {response.status} - {'✅ PASS' if response.status == 405 else '❌ FAIL'}")
                if response.status not in [405, 415]:
                    text = await response.text()
                    print(f"  Response: {text[:200]}")
        except Exception as e:
            print(f"POST /health (valid content): ERROR - {str(e)}")
        
        # Test 3: POST /health with invalid content type (should be 415 - Unsupported Media Type)
        try:
            headers = {'Content-Type': 'text/plain'}
            data = 'invalid data'
            async with session.post(f"http://localhost:{port}/health", headers=headers, data=data) as response:
                print(f"POST /health (invalid content): {response.status} - {'✅ PASS' if response.status in [405, 415] else '❌ FAIL'}")
                if response.status not in [405, 415]:
                    text = await response.text()
                    print(f"  Response: {text[:200]}")
        except Exception as e:
            print(f"POST /health (invalid content): ERROR - {str(e)}")
        
        # Test 4: Check if middleware is loaded by looking at headers
        try:
            async with session.get(f"http://localhost:{port}/health") as response:
                headers = dict(response.headers)
                middleware_headers = [
                    'x-request-id', 'x-powered-by', 'content-security-policy',
                    'x-content-type-options', 'x-frame-options'
                ]
                middleware_active = all(h in headers for h in middleware_headers)
                print(f"Security middleware active: {'✅ YES' if middleware_active else '❌ NO'}")
                if not middleware_active:
                    missing = [h for h in middleware_headers if h not in headers]
                    print(f"  Missing headers: {missing}")
        except Exception as e:
            print(f"Header check: ERROR - {str(e)}")

async def main():
    """Test all services."""
    print("🛡️ ACGS-PGP Middleware Direct Testing")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    services = [
        ("auth_service", 8000),
        ("ac_service", 8001),
        ("integrity_service", 8002),
        ("fv_service", 8003),
        ("gs_service", 8004),
        ("pgc_service", 8005),
        ("ec_service", 8006)
    ]
    
    for service_name, port in services:
        await test_single_service(service_name, port)
    
    print("\n" + "=" * 60)
    print("Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())
