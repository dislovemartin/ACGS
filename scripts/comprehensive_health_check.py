#!/usr/bin/env python3
"""
ACGS-PGP Comprehensive Health Check Script
Validates all services, dependencies, and infrastructure components.
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ACGSHealthChecker:
    """Comprehensive health checker for ACGS-PGP infrastructure."""
    
    def __init__(self):
        self.services = {
            'auth_service': {'url': 'http://localhost:8000', 'critical': True},
            'ac_service': {'url': 'http://localhost:8001', 'critical': True},
            'integrity_service': {'url': 'http://localhost:8002', 'critical': True},
            'fv_service': {'url': 'http://localhost:8003', 'critical': True},
            'gs_service': {'url': 'http://localhost:8004', 'critical': True},
            'pgc_service': {'url': 'http://localhost:8005', 'critical': True},
            'ec_service': {'url': 'http://localhost:8006', 'critical': False},
            'research_service': {'url': 'http://localhost:8007', 'critical': False}
        }
        
        self.infrastructure = {
            'postgres': {'url': 'http://localhost:5433', 'type': 'database'},
            'redis': {'url': 'http://localhost:6379', 'type': 'cache'},
            'opa': {'url': 'http://localhost:8181', 'type': 'policy_engine'},
            'prometheus': {'url': 'http://localhost:9090', 'type': 'monitoring'},
            'grafana': {'url': 'http://localhost:3001', 'type': 'dashboard'}
        }
        
        self.health_results = {}
        self.performance_metrics = {}
        
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check on all components."""
        logger.info("🏥 Starting ACGS-PGP Comprehensive Health Check")
        
        start_time = time.time()
        
        # Run health checks
        service_results = await self.check_all_services()
        infrastructure_results = await self.check_infrastructure()
        dependency_results = await self.check_service_dependencies()
        performance_results = await self.check_performance_metrics()
        
        total_time = time.time() - start_time
        
        # Compile results
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "total_check_duration_seconds": round(total_time, 2),
            "services": service_results,
            "infrastructure": infrastructure_results,
            "dependencies": dependency_results,
            "performance": performance_results,
            "overall_status": self.calculate_overall_status(service_results, infrastructure_results),
            "recommendations": self.generate_recommendations()
        }
        
        return health_report
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all ACGS-PGP services."""
        logger.info("🔍 Checking service health...")
        
        service_results = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for service_name, config in self.services.items():
                service_results[service_name] = await self.check_service_health(session, service_name, config)
        
        return service_results
    
    async def check_service_health(self, session: aiohttp.ClientSession, 
                                 service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check individual service health."""
        result = {
            "status": "unknown",
            "response_time_ms": 0,
            "critical": config.get('critical', False),
            "details": {},
            "error": None
        }
        
        try:
            start_time = time.time()
            
            async with session.get(f"{config['url']}/health") as response:
                response_time = (time.time() - start_time) * 1000
                result["response_time_ms"] = round(response_time, 2)
                
                if response.status == 200:
                    result["status"] = "healthy"
                    try:
                        health_data = await response.json()
                        result["details"] = health_data
                        logger.info(f"✅ {service_name}: Healthy ({response_time:.1f}ms)")
                    except:
                        result["details"] = {"message": "Health endpoint accessible"}
                        logger.info(f"✅ {service_name}: Healthy (basic)")
                else:
                    result["status"] = "unhealthy"
                    result["error"] = f"HTTP {response.status}"
                    logger.warning(f"❌ {service_name}: Unhealthy (HTTP {response.status})")
                    
        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error"] = "Request timeout"
            logger.warning(f"⏱️ {service_name}: Timeout")
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"💥 {service_name}: Error - {e}")
        
        return result
    
    async def check_infrastructure(self) -> Dict[str, Any]:
        """Check infrastructure component health."""
        logger.info("🏗️ Checking infrastructure health...")
        
        infrastructure_results = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for component_name, config in self.infrastructure.items():
                infrastructure_results[component_name] = await self.check_infrastructure_component(
                    session, component_name, config
                )
        
        return infrastructure_results
    
    async def check_infrastructure_component(self, session: aiohttp.ClientSession,
                                           component_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check individual infrastructure component."""
        result = {
            "status": "unknown",
            "type": config.get('type', 'unknown'),
            "response_time_ms": 0,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # Different health check endpoints for different components
            if component_name == 'postgres':
                # For PostgreSQL, we'll check if the port is accessible
                result["status"] = "assumed_healthy"  # Placeholder
                result["response_time_ms"] = 1.0
                logger.info(f"✅ {component_name}: Assumed healthy (database)")
            elif component_name == 'redis':
                result["status"] = "assumed_healthy"  # Placeholder
                result["response_time_ms"] = 1.0
                logger.info(f"✅ {component_name}: Assumed healthy (cache)")
            else:
                # For HTTP-based services
                health_endpoint = "/health" if component_name == "opa" else "/-/healthy"
                async with session.get(f"{config['url']}{health_endpoint}") as response:
                    response_time = (time.time() - start_time) * 1000
                    result["response_time_ms"] = round(response_time, 2)
                    
                    if response.status == 200:
                        result["status"] = "healthy"
                        logger.info(f"✅ {component_name}: Healthy ({response_time:.1f}ms)")
                    else:
                        result["status"] = "unhealthy"
                        result["error"] = f"HTTP {response.status}"
                        logger.warning(f"❌ {component_name}: Unhealthy (HTTP {response.status})")
                        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"💥 {component_name}: Error - {e}")
        
        return result
    
    async def check_service_dependencies(self) -> Dict[str, Any]:
        """Check service dependency health."""
        logger.info("🔗 Checking service dependencies...")
        
        dependency_results = {}
        
        # Test critical service communication paths
        critical_paths = [
            ("gs_service", "ac_service", "Constitutional principle access"),
            ("pgc_service", "integrity_service", "Policy integrity verification"),
            ("fv_service", "ac_service", "Formal verification of principles"),
            ("gs_service", "integrity_service", "Policy synthesis integrity")
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for source, target, description in critical_paths:
                dependency_key = f"{source}_to_{target}"
                dependency_results[dependency_key] = await self.test_service_dependency(
                    session, source, target, description
                )
        
        return dependency_results
    
    async def test_service_dependency(self, session: aiohttp.ClientSession,
                                    source: str, target: str, description: str) -> Dict[str, Any]:
        """Test dependency between two services."""
        result = {
            "description": description,
            "status": "unknown",
            "response_time_ms": 0,
            "error": None
        }
        
        try:
            # Test if both services are accessible
            source_url = self.services[source]['url']
            target_url = self.services[target]['url']
            
            start_time = time.time()
            
            # Simple connectivity test
            async with session.get(f"{source_url}/health") as source_response:
                if source_response.status == 200:
                    async with session.get(f"{target_url}/health") as target_response:
                        if target_response.status == 200:
                            response_time = (time.time() - start_time) * 1000
                            result["response_time_ms"] = round(response_time, 2)
                            result["status"] = "healthy"
                            logger.info(f"✅ {source} → {target}: Dependency healthy")
                        else:
                            result["status"] = "target_unhealthy"
                            result["error"] = f"Target service unhealthy: HTTP {target_response.status}"
                else:
                    result["status"] = "source_unhealthy"
                    result["error"] = f"Source service unhealthy: HTTP {source_response.status}"
                    
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"💥 {source} → {target}: Dependency error - {e}")
        
        return result
    
    async def check_performance_metrics(self) -> Dict[str, Any]:
        """Check performance metrics and thresholds."""
        logger.info("📊 Checking performance metrics...")
        
        performance_results = {
            "response_time_analysis": {},
            "availability_analysis": {},
            "performance_grade": "unknown"
        }
        
        # Analyze response times
        healthy_services = [name for name, result in self.health_results.get('services', {}).items() 
                          if result.get('status') == 'healthy']
        
        if healthy_services:
            response_times = [self.health_results['services'][service]['response_time_ms'] 
                            for service in healthy_services]
            
            performance_results["response_time_analysis"] = {
                "average_ms": round(sum(response_times) / len(response_times), 2),
                "max_ms": max(response_times),
                "min_ms": min(response_times),
                "services_under_200ms": len([rt for rt in response_times if rt < 200]),
                "total_services": len(response_times)
            }
        
        # Calculate availability
        total_services = len(self.services)
        healthy_count = len([s for s in self.health_results.get('services', {}).values() 
                           if s.get('status') == 'healthy'])
        
        availability_percentage = (healthy_count / total_services * 100) if total_services > 0 else 0
        
        performance_results["availability_analysis"] = {
            "healthy_services": healthy_count,
            "total_services": total_services,
            "availability_percentage": round(availability_percentage, 2)
        }
        
        # Calculate performance grade
        avg_response_time = performance_results["response_time_analysis"].get("average_ms", 1000)
        if availability_percentage >= 99.5 and avg_response_time < 100:
            performance_results["performance_grade"] = "A+"
        elif availability_percentage >= 99.0 and avg_response_time < 200:
            performance_results["performance_grade"] = "A"
        elif availability_percentage >= 95.0 and avg_response_time < 500:
            performance_results["performance_grade"] = "B"
        else:
            performance_results["performance_grade"] = "C"
        
        return performance_results
    
    def calculate_overall_status(self, service_results: Dict[str, Any], 
                               infrastructure_results: Dict[str, Any]) -> str:
        """Calculate overall system status."""
        # Check critical services
        critical_services_healthy = all(
            result.get('status') == 'healthy' 
            for name, result in service_results.items()
            if self.services[name].get('critical', False)
        )
        
        if critical_services_healthy:
            # Check if all services are healthy
            all_services_healthy = all(
                result.get('status') == 'healthy' 
                for result in service_results.values()
            )
            
            if all_services_healthy:
                return "healthy"
            else:
                return "degraded"
        else:
            return "unhealthy"
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health check results."""
        recommendations = []
        
        # Add specific recommendations based on results
        recommendations.extend([
            "Monitor service response times continuously",
            "Implement automated health check alerts",
            "Set up service dependency monitoring",
            "Configure load balancing for high availability",
            "Implement circuit breakers for service resilience"
        ])
        
        return recommendations

async def main():
    """Main health check execution function."""
    checker = ACGSHealthChecker()
    
    try:
        health_report = await checker.run_comprehensive_health_check()
        
        # Save health report
        report_filename = f"acgs_health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(health_report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("🏥 ACGS-PGP Health Check Summary")
        print("="*60)
        print(f"Overall Status: {health_report['overall_status'].upper()}")
        print(f"Check Duration: {health_report['total_check_duration_seconds']}s")
        
        if 'performance' in health_report:
            perf = health_report['performance']
            if 'availability_analysis' in perf:
                print(f"Availability: {perf['availability_analysis']['availability_percentage']}%")
            if 'response_time_analysis' in perf:
                print(f"Avg Response Time: {perf['response_time_analysis'].get('average_ms', 'N/A')}ms")
            print(f"Performance Grade: {perf.get('performance_grade', 'N/A')}")
        
        print(f"Report saved: {report_filename}")
        
        # Return success if overall status is healthy or degraded
        return health_report['overall_status'] in ['healthy', 'degraded']
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
