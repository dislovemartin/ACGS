#!/usr/bin/env python3
"""
Phase 2 AlphaEvolve Integration - Service Deployment Script

This script deploys and validates the Phase 2 services required for
AlphaEvolve integration with WINA optimization.
"""

import asyncio
import subprocess
import time
import httpx
import json
from pathlib import Path

# Service configuration
SERVICES = {
    "gs_service": {"port": 8014, "name": "GS Service (Governance Synthesis)"},
    "fv_service": {"port": 8013, "name": "FV Service (Formal Verification)"},
    "pgc_service": {"port": 8015, "name": "PGC Service (Policy Governance Compiler)"},
    "integrity_service": {"port": 8012, "name": "Integrity Service"}
}

async def check_service_health(service_name: str, port: int, timeout: int = 5) -> bool:
    """Check if a service is healthy."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:{port}/health", timeout=timeout)
            return response.status_code == 200
    except:
        return False

async def wait_for_service(service_name: str, port: int, max_wait: int = 60) -> bool:
    """Wait for a service to become healthy."""
    print(f"   ⏳ Waiting for {service_name} on port {port}...")
    
    for i in range(max_wait):
        if await check_service_health(service_name, port):
            print(f"   ✅ {service_name} is healthy")
            return True
        await asyncio.sleep(1)
    
    print(f"   ❌ {service_name} failed to start within {max_wait} seconds")
    return False

def start_docker_services():
    """Start the required Docker services."""
    print("🚀 Starting Phase 2 Docker Services...")
    
    try:
        # Start services using docker-compose
        cmd = [
            "docker-compose", "-f", "docker-compose.staging.yml", 
            "up", "-d", "gs_service", "fv_service", "pgc_service", "integrity_service"
        ]
        
        print(f"   📋 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("   ✅ Docker services started successfully")
            return True
        else:
            print(f"   ❌ Docker services failed to start:")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ Docker services startup timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error starting Docker services: {e}")
        return False

async def validate_service_deployment():
    """Validate that all services are properly deployed."""
    print("🔧 Validating Service Deployment...")
    
    healthy_services = []
    
    for service_name, config in SERVICES.items():
        port = config["port"]
        name = config["name"]
        
        print(f"   📋 Checking {name}...")
        
        if await wait_for_service(service_name, port, max_wait=30):
            healthy_services.append(service_name)
        else:
            print(f"   ⚠️  {name} is not responding")
    
    success_rate = len(healthy_services) / len(SERVICES)
    print(f"🎯 Service Deployment: {len(healthy_services)}/{len(SERVICES)} services healthy ({success_rate:.1%})")
    
    return healthy_services, success_rate >= 0.8

async def test_phase2_integration():
    """Test Phase 2 integration capabilities."""
    print("🔧 Testing Phase 2 Integration...")
    
    integration_tests = []
    
    # Test AC service (should already be running)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8011/health", timeout=5)
            if response.status_code == 200:
                integration_tests.append("AC Service")
                print("   ✅ AC Service: healthy")
            else:
                print("   ❌ AC Service: unhealthy")
    except:
        print("   ❌ AC Service: unreachable")
    
    # Test GS service Phase 2 endpoints
    try:
        async with httpx.AsyncClient() as client:
            # Test if Phase 2 synthesis endpoint exists
            response = await client.get("http://localhost:8014/api/v1/synthesis/capabilities", timeout=5)
            if response.status_code == 200:
                capabilities = response.json()
                if capabilities.get("wina_optimization_available", False):
                    integration_tests.append("GS WINA Integration")
                    print("   ✅ GS Service: WINA optimization available")
                else:
                    print("   ⚠️  GS Service: WINA optimization not available")
            else:
                print("   ⚠️  GS Service: capabilities endpoint not found")
    except:
        print("   ❌ GS Service: unreachable for integration test")
    
    # Test multi-model coordination
    try:
        # This would test the multi-model coordinator directly
        import sys
        sys.path.append("src/backend/gs_service/app")
        from core.multi_model_coordinator import MultiModelCoordinator, EnsembleStrategy
        
        config = {
            "primary_model": "gemini-2.5-pro",
            "fallback_models": ["gemini-2.0-flash"],
            "ensemble_strategy": "weighted_voting"
        }
        coordinator = MultiModelCoordinator(config)
        await coordinator.initialize()
        
        integration_tests.append("Multi-Model Coordination")
        print("   ✅ Multi-Model Coordination: initialized")
        
    except Exception as e:
        print(f"   ❌ Multi-Model Coordination: {e}")
    
    # Test WINA components
    try:
        sys.path.append("src/backend/shared")
        from wina.core import WINACore
        from wina.config import WINAConfig
        
        config = WINAConfig(
            svd_rank_reduction=0.6,
            accuracy_threshold=0.95,
            enable_runtime_gating=True
        )
        wina_core = WINACore(config)
        
        integration_tests.append("WINA Core")
        print("   ✅ WINA Core: functional")
        
    except Exception as e:
        print(f"   ❌ WINA Core: {e}")
    
    integration_success = len(integration_tests) >= 2  # At least 2 components working
    print(f"🎯 Integration Tests: {len(integration_tests)} components functional")
    
    return integration_tests, integration_success

async def generate_deployment_report(healthy_services, integration_tests):
    """Generate a deployment report."""
    print("\n" + "=" * 80)
    print("📊 PHASE 2 DEPLOYMENT REPORT")
    print("=" * 80)
    
    # Service status
    print("🔧 Service Status:")
    for service_name, config in SERVICES.items():
        status = "✅ HEALTHY" if service_name in healthy_services else "❌ UNHEALTHY"
        print(f"   {status} {config['name']} (port {config['port']})")
    
    # Integration status
    print("\n🔗 Integration Status:")
    for test in integration_tests:
        print(f"   ✅ {test}")
    
    # Overall status
    service_health = len(healthy_services) / len(SERVICES)
    integration_health = len(integration_tests) >= 2
    
    print(f"\n🎯 Overall Status:")
    print(f"   Services: {len(healthy_services)}/{len(SERVICES)} healthy ({service_health:.1%})")
    print(f"   Integration: {'✅ FUNCTIONAL' if integration_health else '❌ NEEDS ATTENTION'}")
    
    if service_health >= 0.8 and integration_health:
        print("\n🎉 Phase 2 AlphaEvolve Integration: DEPLOYMENT SUCCESSFUL")
        deployment_status = "SUCCESS"
    else:
        print("\n⚠️  Phase 2 AlphaEvolve Integration: DEPLOYMENT NEEDS ATTENTION")
        deployment_status = "PARTIAL"
    
    # Save report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "deployment_status": deployment_status,
        "services": {
            service: service in healthy_services 
            for service in SERVICES.keys()
        },
        "integration_tests": integration_tests,
        "service_health_rate": service_health,
        "integration_functional": integration_health
    }
    
    with open("phase2_deployment_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Deployment report saved to: phase2_deployment_report.json")
    
    return deployment_status == "SUCCESS"

async def main():
    """Main deployment function."""
    print("🚀 Phase 2 AlphaEvolve Integration - Service Deployment")
    print("=" * 80)
    
    start_time = time.time()
    
    # Step 1: Start Docker services
    docker_success = start_docker_services()
    if not docker_success:
        print("❌ Docker service startup failed. Exiting.")
        return False
    
    # Step 2: Validate service deployment
    healthy_services, deployment_success = await validate_service_deployment()
    
    # Step 3: Test Phase 2 integration
    integration_tests, integration_success = await test_phase2_integration()
    
    # Step 4: Generate deployment report
    overall_success = await generate_deployment_report(healthy_services, integration_tests)
    
    execution_time = time.time() - start_time
    print(f"\n⏱️  Total Deployment Time: {execution_time:.2f} seconds")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
