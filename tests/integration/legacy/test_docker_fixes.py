import os, pytest
if not os.environ.get("ACGS_INTEGRATION"):
    pytest.skip("integration test requires running services", allow_module_level=True)

#!/usr/bin/env python3
"""
ACGS-PGP Docker Container Import Path Fix Verification
Tests that all services can start and shared modules are accessible
"""

import asyncio
import subprocess
import time
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Service endpoints configuration
SERVICES = {
    "auth": {"url": "http://localhost:8000", "health": "/health"},
    "ac": {"url": "http://localhost:8001", "health": "/health"},
    "gs": {"url": "http://localhost:8004", "health": "/health"},
    "fv": {"url": "http://localhost:8003", "health": "/health"},
    "integrity": {"url": "http://localhost:8002", "health": "/health"},
    "pgc": {"url": "http://localhost:8005", "health": "/health"}
}

class DockerFixTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def run_docker_compose_command(self, command: str) -> bool:
        """Run docker-compose command and return success status"""
        try:
            print(f"Running: docker-compose {command}")
            result = subprocess.run(
                f"docker-compose -f config/docker/docker-compose.yml {command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"✅ Command succeeded: docker-compose {command}")
                return True
            else:
                print(f"❌ Command failed: docker-compose {command}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"❌ Command timed out: docker-compose {command}")
            return False
        except Exception as e:
            print(f"❌ Command error: docker-compose {command} - {str(e)}")
            return False
    
    def check_docker_compose_syntax(self) -> bool:
        """Check docker-compose.yml syntax"""
        print("\n🔍 Checking docker-compose.yml syntax...")
        return self.run_docker_compose_command("config --quiet")
    
    def build_services(self) -> bool:
        """Build all Docker services"""
        print("\n🏗️ Building Docker services...")
        return self.run_docker_compose_command("build --no-cache")
    
    def start_services(self) -> bool:
        """Start all Docker services"""
        print("\n🚀 Starting Docker services...")
        return self.run_docker_compose_command("up -d")
    
    def stop_services(self) -> bool:
        """Stop all Docker services"""
        print("\n🛑 Stopping Docker services...")
        return self.run_docker_compose_command("down")
    
    def check_service_logs(self, service_name: str) -> bool:
        """Check service logs for import errors"""
        try:
            print(f"📋 Checking logs for {service_name}...")
            result = subprocess.run(
                f"docker-compose -f config/docker/docker-compose.yml logs {service_name}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            logs = result.stdout + result.stderr
            
            # Check for import errors
            import_errors = [
                "ModuleNotFoundError: No module named 'shared",
                "ImportError",
                "ModuleNotFoundError",
                "No module named"
            ]
            
            for error in import_errors:
                if error in logs:
                    print(f"❌ {service_name}: Found import error - {error}")
                    print(f"Logs excerpt: {logs[-500:]}")  # Last 500 chars
                    return False
            
            print(f"✅ {service_name}: No import errors found")
            return True
            
        except Exception as e:
            print(f"❌ {service_name}: Error checking logs - {str(e)}")
            return False
    
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
    
    async def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run comprehensive Docker fix verification"""
        print("🔧 ACGS-PGP Docker Container Import Path Fix Verification")
        print("=" * 70)
        print(f"Test started at: {datetime.now().isoformat()}")
        
        results = {}
        
        # Step 1: Check docker-compose syntax
        syntax_ok = self.check_docker_compose_syntax()
        results["docker_compose_syntax"] = syntax_ok
        
        if not syntax_ok:
            print("❌ Docker Compose syntax check failed. Stopping tests.")
            return results
        
        # Step 2: Build services
        build_ok = self.build_services()
        results["docker_build"] = build_ok
        
        if not build_ok:
            print("❌ Docker build failed. Stopping tests.")
            return results
        
        # Step 3: Start services
        start_ok = self.start_services()
        results["docker_start"] = start_ok
        
        if not start_ok:
            print("❌ Docker start failed. Stopping tests.")
            return results
        
        # Wait for services to initialize
        print("\n⏳ Waiting 30 seconds for services to initialize...")
        time.sleep(30)
        
        # Step 4: Check service logs for import errors
        print("\n📋 Checking service logs for import errors...")
        log_results = []
        for service_name in ["auth_service", "ac_service", "integrity_service", "fv_service", "gs_service", "pgc_service"]:
            log_ok = self.check_service_logs(service_name)
            log_results.append(log_ok)
            results[f"{service_name}_logs"] = log_ok
        
        # Step 5: Test service health endpoints
        print("\n🏥 Testing service health endpoints...")
        health_results = []
        for service_name, config in SERVICES.items():
            health_ok = await self.test_service_health(service_name, config)
            health_results.append(health_ok)
            results[f"{service_name}_health"] = health_ok
        
        # Step 6: Stop services
        stop_ok = self.stop_services()
        results["docker_stop"] = stop_ok
        
        return results

async def main():
    """Main test execution function"""
    async with DockerFixTester() as tester:
        results = await tester.run_comprehensive_test()
        
        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Docker fix verification tests passed!")
            print("✅ Services can start successfully with shared module imports")
            return 0
        else:
            print("⚠️ Some tests failed - check Docker configurations and logs")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

import os
import asyncio
import pytest

@pytest.mark.skipif(not os.environ.get("ACGS_INTEGRATION"), reason="Integration test requires running services")
def test_main_wrapper():
    if 'main' in globals():
        if asyncio.iscoroutinefunction(main):
            asyncio.run(main())
        else:
            main()
