#!/usr/bin/env python3
"""
ACGS-PGP Service Integration Test Suite
Tests cross-service communication and health endpoints
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Service endpoints configuration
SERVICES = {
    "auth": {"url": "http://localhost:8000/auth", "health": "/health"},
    "ac": {"url": "http://localhost:8001", "health": "/health"},
    "gs": {"url": "http://localhost:8004", "health": "/health"},
    "fv": {"url": "http://localhost:8003", "health": "/health"},
    "integrity": {"url": "http://localhost:8002", "health": "/health"},
    "pgc": {"url": "http://localhost:8005", "health": "/health"}
}

class ServiceIntegrationTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_service_health(self, service_name: str, config: Dict) -> bool:
        """Test individual service health endpoint"""
        try:
            url = f"{config['url']}{config['health']}"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ {service_name.upper()} Service: {data.get('status', 'ok')}")
                    return True
                else:
                    print(f"❌ {service_name.upper()} Service: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ {service_name.upper()} Service: Connection failed - {str(e)}")
            return False
    
    async def test_cross_service_communication(self) -> bool:
        """Test communication between services"""
        print("\n🔗 Testing Cross-Service Communication...")
        
        # Test AC -> GS communication (constitutional prompting)
        try:
            # First get principles from AC service
            ac_url = f"{SERVICES['ac']['url']}/api/v1/principles"
            async with self.session.get(ac_url) as response:
                if response.status == 200:
                    principles = await response.json()
                    print(f"✅ AC Service: Retrieved {len(principles)} principles")
                    
                    # Test GS service constitutional synthesis
                    gs_url = f"{SERVICES['gs']['url']}/api/v1/constitutional/synthesize"
                    test_request = {
                        "context": "test_integration",
                        "category": "safety",
                        "synthesis_request": "Generate a test policy for data protection",
                        "target_format": "rego"
                    }
                    
                    async with self.session.post(gs_url, json=test_request) as gs_response:
                        if gs_response.status == 200:
                            synthesis_result = await gs_response.json()
                            print("✅ GS Service: Constitutional synthesis successful")
                            return True
                        else:
                            print(f"❌ GS Service: Synthesis failed - HTTP {gs_response.status}")
                            return False
                else:
                    print(f"❌ AC Service: Failed to retrieve principles - HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Cross-service communication failed: {str(e)}")
            return False
    
    async def test_database_connectivity(self) -> bool:
        """Test database connectivity through services"""
        print("\n🗄️ Testing Database Connectivity...")
        
        try:
            # Test AC service database operations
            ac_url = f"{SERVICES['ac']['url']}/api/v1/principles"
            async with self.session.get(ac_url) as response:
                if response.status == 200:
                    print("✅ AC Service: Database connectivity confirmed")
                    
                    # Test Integrity service database operations
                    integrity_url = f"{SERVICES['integrity']['url']}/api/v1/audit/logs"
                    async with self.session.get(integrity_url) as int_response:
                        if int_response.status == 200:
                            print("✅ Integrity Service: Database connectivity confirmed")
                            return True
                        else:
                            print(f"❌ Integrity Service: Database connection failed - HTTP {int_response.status}")
                            return False
                else:
                    print(f"❌ AC Service: Database connection failed - HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Database connectivity test failed: {str(e)}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run comprehensive service integration tests"""
        print("🚀 ACGS-PGP Service Integration Test Suite")
        print("=" * 60)
        print(f"Test started at: {datetime.now().isoformat()}")
        
        results = {}
        
        # Test individual service health
        print("\n🏥 Testing Service Health Endpoints...")
        health_results = []
        for service_name, config in SERVICES.items():
            health_ok = await self.test_service_health(service_name, config)
            health_results.append(health_ok)
            results[f"{service_name}_health"] = health_ok
        
        # Only proceed with integration tests if all services are healthy
        if all(health_results):
            print("\n✅ All services are healthy, proceeding with integration tests...")
            
            # Test cross-service communication
            comm_result = await self.test_cross_service_communication()
            results["cross_service_communication"] = comm_result
            
            # Test database connectivity
            db_result = await self.test_database_connectivity()
            results["database_connectivity"] = db_result
            
        else:
            print("\n❌ Some services are unhealthy, skipping integration tests")
            results["cross_service_communication"] = False
            results["database_connectivity"] = False
        
        return results

async def main():
    """Main test execution function"""
    async with ServiceIntegrationTester() as tester:
        results = await tester.run_all_tests()
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All integration tests passed!")
            return 0
        else:
            print("⚠️ Some integration tests failed - check service configurations")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
