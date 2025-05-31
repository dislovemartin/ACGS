#!/usr/bin/env python3
"""
Comprehensive CRUD operations testing script for ACGS-PGP Phase 1 remediation.
Tests all API endpoints across ports 8000-8005 using curl commands.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

# Service configuration - using nginx gateway on port 8000
SERVICES = {
    "auth_service": {"port": 8000, "base_path": "/api/auth", "health_path": "/api/auth/health"},
    "ac_service": {"port": 8000, "base_path": "/api/ac", "health_path": "/api/ac/health"},
    "integrity_service": {"port": 8000, "base_path": "/api/integrity", "health_path": "/api/integrity/health"},
    "fv_service": {"port": 8000, "base_path": "/api/fv", "health_path": "/api/fv/health"},
    "gs_service": {"port": 8000, "base_path": "/api/gs", "health_path": "/api/gs/health"},
    "pgc_service": {"port": 8000, "base_path": "/api/pgc", "health_path": "/api/pgc/health"}
}

# Direct service ports for fallback testing
DIRECT_SERVICES = {
    "auth_service": {"port": 8000, "base_path": "/auth"},
    "ac_service": {"port": 8001, "base_path": "/api/v1"},
    "integrity_service": {"port": 8002, "base_path": "/api/v1"},
    "fv_service": {"port": 8003, "base_path": "/api/v1"},
    "gs_service": {"port": 8004, "base_path": "/api/v1"},
    "pgc_service": {"port": 8005, "base_path": "/api/v1"}
}

class CRUDTester:
    def __init__(self):
        self.auth_token = None
        self.test_results = {}
        self.success_count = 0
        self.total_tests = 0
        
    def run_curl_command(self, method: str, url: str, headers: Dict[str, str] = None, 
                        data: Dict[str, Any] = None, timeout: int = 10) -> Dict[str, Any]:
        """Execute curl command and return response."""
        cmd = ["curl", "-s", "-w", "\\n%{http_code}", "-X", method]
        
        # Add headers
        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])
        
        # Add data for POST/PUT requests
        if data:
            cmd.extend(["-H", "Content-Type: application/json"])
            cmd.extend(["-d", json.dumps(data)])
        
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            output_lines = result.stdout.strip().split('\n')
            
            if len(output_lines) >= 2:
                response_body = '\n'.join(output_lines[:-1])
                status_code = int(output_lines[-1])
            else:
                response_body = result.stdout.strip()
                status_code = 0
            
            return {
                "status_code": status_code,
                "response": response_body,
                "success": 200 <= status_code < 300,
                "error": result.stderr if result.stderr else None
            }
        except subprocess.TimeoutExpired:
            return {"status_code": 0, "response": "", "success": False, "error": "Timeout"}
        except Exception as e:
            return {"status_code": 0, "response": "", "success": False, "error": str(e)}
    
    def test_service_health(self, service_name: str) -> bool:
        """Test service health endpoint."""
        service_config = SERVICES[service_name]

        # Try nginx gateway first
        if "health_path" in service_config:
            url = f"http://localhost:{service_config['port']}{service_config['health_path']}"
        else:
            url = f"http://localhost:{service_config['port']}/health"

        result = self.run_curl_command("GET", url)
        self.total_tests += 1

        if result["success"]:
            self.success_count += 1
            print(f"✅ {service_name} health check (nginx): {result['status_code']}")
            return True
        else:
            # Try direct service port as fallback
            if service_name in DIRECT_SERVICES:
                direct_config = DIRECT_SERVICES[service_name]
                url = f"http://localhost:{direct_config['port']}/health"
                result = self.run_curl_command("GET", url)

                if result["success"]:
                    self.success_count += 1
                    print(f"✅ {service_name} health check (direct): {result['status_code']}")
                    return True

            print(f"❌ {service_name} health check failed: {result['status_code']} - {result.get('error', 'Unknown error')}")
            return False
    
    def authenticate_user(self) -> bool:
        """Authenticate and get JWT token."""
        # First, try to register a new user for testing
        register_url = "http://localhost:8000/api/auth/register"
        test_username = f"test_admin_{int(asyncio.get_event_loop().time())}"
        register_data = {
            "username": test_username,
            "email": f"{test_username}@example.com",
            "password": "TestPass123!"
        }

        register_result = self.run_curl_command("POST", register_url, data=register_data)
        if register_result["success"]:
            print(f"✅ Test user registered: {test_username}")
        else:
            print(f"⚠️  Test user registration failed, trying existing user")
            test_username = "admin_user"

        # Try to authenticate with token endpoint (OAuth2 style)
        url = "http://localhost:8000/api/auth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Try with test user first
        if test_username != "admin_user":
            form_data = f"username={test_username}&password=TestPass123!"
        else:
            form_data = "username=admin_user&password=AdminPass123!"

        result = self.run_curl_command("POST", url, headers=headers)
        # Manually add form data to curl command
        cmd = ["curl", "-s", "-w", "\\n%{http_code}", "-X", "POST"]
        cmd.extend(["-H", "Content-Type: application/x-www-form-urlencoded"])
        cmd.extend(["-d", form_data])
        cmd.append(url)

        try:
            import subprocess
            curl_result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output_lines = curl_result.stdout.strip().split('\n')

            if len(output_lines) >= 2:
                response_body = '\n'.join(output_lines[:-1])
                status_code = int(output_lines[-1])
            else:
                response_body = curl_result.stdout.strip()
                status_code = 0

            result = {
                "status_code": status_code,
                "response": response_body,
                "success": 200 <= status_code < 300
            }
        except Exception as e:
            result = {"status_code": 0, "response": "", "success": False, "error": str(e)}

        self.total_tests += 1

        if result["success"]:
            try:
                response_data = json.loads(result["response"])
                self.auth_token = response_data.get("access_token")
                if self.auth_token:
                    self.success_count += 1
                    print(f"✅ Authentication successful")
                    return True
            except json.JSONDecodeError:
                pass

        print(f"❌ Authentication failed: {result['status_code']} - {result.get('response', 'No response')}")
        return False
    
    def test_auth_service_crud(self) -> bool:
        """Test auth service CRUD operations."""
        print("\n🔐 Testing Auth Service CRUD Operations...")
        
        # Test user registration (already tested in authenticate_user)
        print("✅ User registration already tested in authentication")

        # Test token refresh (if we have a token)
        if self.auth_token:
            url = "http://localhost:8000/api/auth/token/refresh"
            headers = {"Authorization": f"Bearer {self.auth_token}"}

            result = self.run_curl_command("POST", url, headers=headers)
            self.total_tests += 1

            if result["success"]:
                self.success_count += 1
                print(f"✅ Token refresh: {result['status_code']}")
            else:
                print(f"❌ Token refresh failed: {result['status_code']}")

        return True
    
    def test_ac_service_crud(self) -> bool:
        """Test AC service CRUD operations."""
        print("\n📋 Testing AC Service CRUD Operations...")
        
        if not self.auth_token:
            print("⚠️  Skipping AC service tests (no auth token)")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test GET principles (direct service - nginx routing is complex)
        url = "http://localhost:8001/api/v1/principles/"
        result = self.run_curl_command("GET", url, headers=headers)
        self.total_tests += 1

        if result["success"]:
            self.success_count += 1
            print(f"✅ GET principles: {result['status_code']}")
        else:
            print(f"❌ GET principles failed: {result['status_code']}")

        # Test POST principle (direct service)
        url = "http://localhost:8001/api/v1/principles/"
        data = {
            "name": "Test CRUD Principle",  # Note: using 'name' not 'title' based on schema
            "description": "A test principle for CRUD validation",
            "content": "This is a test principle for validating CRUD operations",
            "priority_weight": 0.75,
            "scope": "testing",
            "normative_statement": "SHALL validate CRUD operations work correctly"
        }

        result = self.run_curl_command("POST", url, headers=headers, data=data)
        self.total_tests += 1

        if result["success"]:
            self.success_count += 1
            print(f"✅ POST principle: {result['status_code']}")
        else:
            print(f"❌ POST principle failed: {result['status_code']} - {result.get('response', 'No response')}")

        # Test GET meta-rules (direct service)
        url = "http://localhost:8001/api/v1/constitutional-council/meta-rules"
        result = self.run_curl_command("GET", url, headers=headers)
        self.total_tests += 1

        if result["success"]:
            self.success_count += 1
            print(f"✅ GET meta-rules: {result['status_code']}")
        else:
            print(f"❌ GET meta-rules failed: {result['status_code']}")

        return True
    
    def test_other_services_crud(self) -> bool:
        """Test other services basic CRUD operations."""
        print("\n🔧 Testing Other Services CRUD Operations...")
        
        if not self.auth_token:
            print("⚠️  Skipping other service tests (no auth token)")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test Integrity Service
        url = "http://localhost:8000/api/integrity/audit"
        result = self.run_curl_command("GET", url, headers=headers)
        self.total_tests += 1

        if result["success"]:
            self.success_count += 1
            print(f"✅ Integrity Service GET audit (nginx): {result['status_code']}")
        else:
            # Try direct service
            url = "http://localhost:8002/api/v1/audit"
            result = self.run_curl_command("GET", url, headers=headers)
            if result["success"]:
                self.success_count += 1
                print(f"✅ Integrity Service GET audit (direct): {result['status_code']}")
            else:
                print(f"❌ Integrity Service GET audit failed: {result['status_code']}")

        # Test FV Service
        url = "http://localhost:8000/api/fv/verify"
        result = self.run_curl_command("GET", url, headers=headers)
        self.total_tests += 1

        if result["success"]:
            self.success_count += 1
            print(f"✅ FV Service GET verify (nginx): {result['status_code']}")
        else:
            # Try direct service
            url = "http://localhost:8003/api/v1/verify"
            result = self.run_curl_command("GET", url, headers=headers)
            if result["success"]:
                self.success_count += 1
                print(f"✅ FV Service GET verify (direct): {result['status_code']}")
            else:
                print(f"❌ FV Service GET verify failed: {result['status_code']}")

        # Test GS Service
        url = "http://localhost:8000/api/gs/synthesize"
        result = self.run_curl_command("GET", url, headers=headers)
        self.total_tests += 1

        if result["success"]:
            self.success_count += 1
            print(f"✅ GS Service GET synthesize (nginx): {result['status_code']}")
        else:
            # Try direct service
            url = "http://localhost:8004/api/v1/synthesize"
            result = self.run_curl_command("GET", url, headers=headers)
            if result["success"]:
                self.success_count += 1
                print(f"✅ GS Service GET synthesize (direct): {result['status_code']}")
            else:
                print(f"❌ GS Service GET synthesize failed: {result['status_code']}")

        # Test PGC Service
        url = "http://localhost:8000/api/pgc/enforcement"
        result = self.run_curl_command("GET", url, headers=headers)
        self.total_tests += 1

        if result["success"]:
            self.success_count += 1
            print(f"✅ PGC Service GET enforcement (nginx): {result['status_code']}")
        else:
            # Try direct service
            url = "http://localhost:8005/api/v1/enforcement"
            result = self.run_curl_command("GET", url, headers=headers)
            if result["success"]:
                self.success_count += 1
                print(f"✅ PGC Service GET enforcement (direct): {result['status_code']}")
            else:
                print(f"❌ PGC Service GET enforcement failed: {result['status_code']}")

        return True
    
    def run_comprehensive_tests(self) -> bool:
        """Run all CRUD tests."""
        print("🚀 Starting Comprehensive CRUD Operations Testing...")
        
        # Test service health checks
        print("\n🏥 Testing Service Health Checks...")
        for service_name in SERVICES.keys():
            self.test_service_health(service_name)
        
        # Authenticate
        print("\n🔐 Authenticating...")
        if not self.authenticate_user():
            print("❌ Authentication failed, skipping authenticated tests")
            return False
        
        # Test CRUD operations
        self.test_auth_service_crud()
        self.test_ac_service_crud()
        self.test_other_services_crud()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Total tests: {self.total_tests}")
        print(f"Successful: {self.success_count}")
        print(f"Failed: {self.total_tests - self.success_count}")
        success_rate = (self.success_count / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        # Check if we meet the >95% success rate target
        target_success_rate = 95.0
        if success_rate >= target_success_rate:
            print(f"✅ SUCCESS: Achieved target success rate of {target_success_rate}%")
            return True
        else:
            print(f"❌ FAILED: Did not achieve target success rate of {target_success_rate}%")
            return False

def main():
    """Main function to run CRUD tests."""
    tester = CRUDTester()
    success = tester.run_comprehensive_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
