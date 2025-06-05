#!/usr/bin/env python3
"""
ACGS Phase 3 Comprehensive Health Check and Service Deployment
Systematic health assessment and deployment orchestration for staging environment
"""

import asyncio
import aiohttp
import json
import time
import subprocess
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase3_deployment_health_check.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Phase3HealthDeploymentOrchestrator:
    """Comprehensive health check and deployment orchestrator for ACGS Phase 3"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.services = {
            'ac_service': {'port': 8011, 'critical': True, 'status': 'unknown'},
            'integrity_service': {'port': 8012, 'critical': True, 'status': 'unknown'},
            'fv_service': {'port': 8013, 'critical': True, 'status': 'unknown'},
            'gs_service': {'port': 8014, 'critical': True, 'status': 'unknown'},
            'pgc_service': {'port': 8015, 'critical': True, 'status': 'unknown'}
        }
        
        self.infrastructure = {
            'postgres': {'port': 5435, 'critical': True, 'status': 'unknown'},
            'redis': {'port': 6382, 'critical': True, 'status': 'unknown'},
            'opa': {'port': 8191, 'critical': True, 'status': 'unknown'}
        }
        
        self.monitoring = {
            'prometheus': {'port': 9090, 'critical': False, 'status': 'unknown'},
            'grafana': {'port': 3002, 'critical': False, 'status': 'unknown'}
        }
        
        self.health_report = {
            'timestamp': self.start_time.isoformat(),
            'phase': 'Phase 3 Staging Deployment',
            'services': {},
            'infrastructure': {},
            'monitoring': {},
            'performance_metrics': {},
            'security_compliance': {},
            'deployment_actions': [],
            'issues': [],
            'recommendations': []
        }
    
    def log_action(self, action: str, status: str = "INFO", details: str = ""):
        """Log deployment action with timestamp"""
        timestamp = datetime.now().isoformat()
        action_record = {
            'timestamp': timestamp,
            'action': action,
            'status': status,
            'details': details
        }
        self.health_report['deployment_actions'].append(action_record)
        
        if status == "ERROR":
            logger.error(f"❌ {action}: {details}")
        elif status == "WARNING":
            logger.warning(f"⚠️  {action}: {details}")
        elif status == "SUCCESS":
            logger.info(f"✅ {action}: {details}")
        else:
            logger.info(f"ℹ️  {action}: {details}")
    
    async def check_docker_environment(self) -> bool:
        """Check if Docker environment is ready"""
        self.log_action("Checking Docker Environment", "INFO")
        
        try:
            # Check if Docker is running
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log_action("Docker Check", "ERROR", "Docker is not running or accessible")
                return False
            
            # Check for existing containers
            result = subprocess.run(['docker', 'ps', '-a', '--format', 'table {{.Names}}\t{{.Status}}'], 
                                  capture_output=True, text=True)
            
            container_info = result.stdout.strip()
            self.log_action("Docker Container Status", "INFO", f"Current containers:\n{container_info}")
            
            return True
            
        except Exception as e:
            self.log_action("Docker Environment Check", "ERROR", str(e))
            return False
    
    async def check_infrastructure_health(self) -> Dict[str, Any]:
        """Check health of infrastructure components"""
        self.log_action("Infrastructure Health Assessment", "INFO")
        
        infrastructure_results = {}
        
        for component, config in self.infrastructure.items():
            port = config['port']
            
            try:
                if component == 'postgres':
                    # Check PostgreSQL connectivity
                    result = subprocess.run([
                        'docker', 'exec', '-i', 'acgs-postgres-staging', 
                        'pg_isready', '-U', 'acgs_user', '-d', 'acgs_staging'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        status = "healthy"
                        self.log_action(f"{component.upper()} Health", "SUCCESS", f"Database accessible on port {port}")
                    else:
                        status = "unhealthy"
                        self.log_action(f"{component.upper()} Health", "ERROR", f"Database not accessible: {result.stderr}")
                
                elif component == 'redis':
                    # Check Redis connectivity
                    result = subprocess.run([
                        'docker', 'exec', '-i', 'acgs-redis-staging',
                        'redis-cli', 'ping'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0 and 'PONG' in result.stdout:
                        status = "healthy"
                        self.log_action(f"{component.upper()} Health", "SUCCESS", f"Cache accessible on port {port}")
                    else:
                        status = "unhealthy"
                        self.log_action(f"{component.upper()} Health", "ERROR", f"Cache not accessible")
                
                elif component == 'opa':
                    # Check OPA health endpoint
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                        async with session.get(f'http://localhost:{port}/health') as response:
                            if response.status == 200:
                                status = "healthy"
                                self.log_action(f"{component.upper()} Health", "SUCCESS", f"Policy agent accessible on port {port}")
                            else:
                                status = "unhealthy"
                                self.log_action(f"{component.upper()} Health", "ERROR", f"Policy agent returned HTTP {response.status}")
                
                infrastructure_results[component] = {
                    'status': status,
                    'port': port,
                    'critical': config['critical']
                }
                
            except Exception as e:
                status = "error"
                infrastructure_results[component] = {
                    'status': status,
                    'port': port,
                    'critical': config['critical'],
                    'error': str(e)
                }
                self.log_action(f"{component.upper()} Health", "ERROR", str(e))
        
        self.health_report['infrastructure'] = infrastructure_results
        return infrastructure_results
    
    async def check_service_health(self) -> Dict[str, Any]:
        """Check health of ACGS services"""
        self.log_action("ACGS Services Health Assessment", "INFO")
        
        service_results = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for service_name, config in self.services.items():
                port = config['port']
                
                try:
                    start_time = time.time()
                    async with session.get(f'http://localhost:{port}/health') as response:
                        response_time = (time.time() - start_time) * 1000  # Convert to ms
                        
                        if response.status == 200:
                            response_data = await response.json()
                            status = "healthy"
                            self.log_action(f"{service_name.upper()} Health", "SUCCESS", 
                                          f"Service healthy on port {port} ({response_time:.2f}ms)")
                        else:
                            status = "unhealthy"
                            self.log_action(f"{service_name.upper()} Health", "ERROR", 
                                          f"Service returned HTTP {response.status}")
                            response_time = None
                            response_data = None
                
                except asyncio.TimeoutError:
                    status = "timeout"
                    response_time = None
                    response_data = None
                    self.log_action(f"{service_name.upper()} Health", "ERROR", "Health check timeout")
                
                except Exception as e:
                    status = "error"
                    response_time = None
                    response_data = None
                    self.log_action(f"{service_name.upper()} Health", "ERROR", str(e))
                
                service_results[service_name] = {
                    'status': status,
                    'port': port,
                    'response_time_ms': response_time,
                    'critical': config['critical'],
                    'response_data': response_data
                }
        
        self.health_report['services'] = service_results
        return service_results
    
    async def deploy_infrastructure(self) -> bool:
        """Deploy infrastructure components if not running"""
        self.log_action("Infrastructure Deployment", "INFO")
        
        try:
            # Start infrastructure services using Docker Compose
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.staging.yml',
                'up', '-d', 'postgres', 'redis', 'opa'
            ], capture_output=True, text=True, cwd='/mnt/persist/workspace')
            
            if result.returncode == 0:
                self.log_action("Infrastructure Deployment", "SUCCESS", "Infrastructure services started")
                
                # Wait for services to be ready
                await asyncio.sleep(30)
                return True
            else:
                self.log_action("Infrastructure Deployment", "ERROR", result.stderr)
                return False
                
        except Exception as e:
            self.log_action("Infrastructure Deployment", "ERROR", str(e))
            return False
    
    async def deploy_acgs_services(self, service_order: List[str] = None) -> Dict[str, bool]:
        """Deploy ACGS services in dependency order"""
        if service_order is None:
            service_order = ['ac_service', 'integrity_service', 'fv_service', 'gs_service', 'pgc_service']
        
        self.log_action("ACGS Services Deployment", "INFO", f"Deploying services in order: {service_order}")
        
        deployment_results = {}
        
        for service_name in service_order:
            try:
                self.log_action(f"Deploying {service_name.upper()}", "INFO")
                
                # Deploy individual service
                result = subprocess.run([
                    'docker-compose', '-f', 'docker-compose.staging.yml',
                    'up', '-d', service_name
                ], capture_output=True, text=True, cwd='/mnt/persist/workspace')
                
                if result.returncode == 0:
                    self.log_action(f"{service_name.upper()} Deployment", "SUCCESS", "Service container started")
                    
                    # Wait for service to be ready
                    await asyncio.sleep(15)
                    
                    # Verify service health
                    port = self.services[service_name]['port']
                    try:
                        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                            async with session.get(f'http://localhost:{port}/health') as response:
                                if response.status == 200:
                                    deployment_results[service_name] = True
                                    self.log_action(f"{service_name.upper()} Verification", "SUCCESS", 
                                                  f"Service healthy on port {port}")
                                else:
                                    deployment_results[service_name] = False
                                    self.log_action(f"{service_name.upper()} Verification", "ERROR", 
                                                  f"Service unhealthy: HTTP {response.status}")
                    except Exception as e:
                        deployment_results[service_name] = False
                        self.log_action(f"{service_name.upper()} Verification", "ERROR", str(e))
                else:
                    deployment_results[service_name] = False
                    self.log_action(f"{service_name.upper()} Deployment", "ERROR", result.stderr)
                    
            except Exception as e:
                deployment_results[service_name] = False
                self.log_action(f"{service_name.upper()} Deployment", "ERROR", str(e))
        
        return deployment_results
    
    async def generate_comprehensive_report(self) -> str:
        """Generate comprehensive health and deployment report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.health_report['completion_time'] = end_time.isoformat()
        self.health_report['total_duration_seconds'] = duration
        
        # Calculate overall health metrics
        total_services = len(self.services)
        healthy_services = sum(1 for s in self.health_report['services'].values() if s['status'] == 'healthy')
        service_health_percentage = (healthy_services / total_services) * 100 if total_services > 0 else 0
        
        total_infrastructure = len(self.infrastructure)
        healthy_infrastructure = sum(1 for i in self.health_report['infrastructure'].values() if i['status'] == 'healthy')
        infrastructure_health_percentage = (healthy_infrastructure / total_infrastructure) * 100 if total_infrastructure > 0 else 0
        
        self.health_report['summary'] = {
            'overall_health_percentage': (service_health_percentage + infrastructure_health_percentage) / 2,
            'services_health_percentage': service_health_percentage,
            'infrastructure_health_percentage': infrastructure_health_percentage,
            'healthy_services': healthy_services,
            'total_services': total_services,
            'healthy_infrastructure': healthy_infrastructure,
            'total_infrastructure': total_infrastructure
        }
        
        # Save report to file
        report_filename = f"phase3_health_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.health_report, f, indent=2)
        
        self.log_action("Report Generation", "SUCCESS", f"Comprehensive report saved to {report_filename}")
        
        return report_filename

async def main():
    """Main execution function for Phase 3 health check and deployment"""
    orchestrator = Phase3HealthDeploymentOrchestrator()
    
    logger.info("🚀 Starting ACGS Phase 3 Comprehensive Health Check and Deployment")
    logger.info("=" * 80)
    
    # Step 1: Check Docker environment
    docker_ready = await orchestrator.check_docker_environment()
    if not docker_ready:
        logger.error("❌ Docker environment not ready. Exiting.")
        return
    
    # Step 2: Check current infrastructure health
    infrastructure_health = await orchestrator.check_infrastructure_health()
    
    # Step 3: Check current service health
    service_health = await orchestrator.check_service_health()
    
    # Step 4: Deploy infrastructure if needed
    infrastructure_unhealthy = any(
        comp['status'] != 'healthy' for comp in infrastructure_health.values()
    )
    
    if infrastructure_unhealthy:
        logger.info("🔧 Infrastructure components need deployment...")
        infrastructure_deployed = await orchestrator.deploy_infrastructure()
        if infrastructure_deployed:
            # Re-check infrastructure health
            infrastructure_health = await orchestrator.check_infrastructure_health()
    
    # Step 5: Deploy ACGS services systematically
    services_unhealthy = any(
        svc['status'] != 'healthy' for svc in service_health.values()
    )
    
    if services_unhealthy:
        logger.info("🔧 ACGS services need deployment...")
        deployment_results = await orchestrator.deploy_acgs_services()
        
        # Re-check service health after deployment
        service_health = await orchestrator.check_service_health()
    
    # Step 6: Generate comprehensive report
    report_file = await orchestrator.generate_comprehensive_report()
    
    logger.info("=" * 80)
    logger.info("🎉 Phase 3 Health Check and Deployment Complete")
    logger.info(f"📊 Report saved to: {report_file}")
    
    # Display summary
    summary = orchestrator.health_report['summary']
    logger.info(f"📈 Overall Health: {summary['overall_health_percentage']:.1f}%")
    logger.info(f"🔧 Services: {summary['healthy_services']}/{summary['total_services']} healthy")
    logger.info(f"🏗️  Infrastructure: {summary['healthy_infrastructure']}/{summary['total_infrastructure']} healthy")

if __name__ == "__main__":
    asyncio.run(main())
