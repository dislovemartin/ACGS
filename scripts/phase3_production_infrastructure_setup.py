#!/usr/bin/env python3
"""
ACGS Phase 3 Production Infrastructure Setup Script
Sets up production environment with monitoring, alerting, and deployment validation.

Production Requirements:
- 16GB+ RAM, 100GB+ SSD storage
- Blue-green deployment strategy
- Prometheus/Grafana/AlertManager monitoring
- SSL/TLS configuration and firewall hardening
- Alerting thresholds: 25ms latency, 80% cache hit rate, 85% memory/80% CPU
"""

import asyncio
import subprocess
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import argparse
import logging
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/phase3_production_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ACGSProductionInfrastructure:
    def __init__(self):
        self.services = {
            'auth_service': {'port': 8000, 'name': 'Auth Service'},
            'ac_service': {'port': 8001, 'name': 'AC Service'},
            'integrity_service': {'port': 8002, 'name': 'Integrity Service'},
            'fv_service': {'port': 8003, 'name': 'FV Service'},
            'gs_service': {'port': 8004, 'name': 'GS Service'},
            'pgc_service': {'port': 8005, 'name': 'PGC Service'}
        }
        
        self.production_requirements = {
            'min_memory_gb': 16,
            'min_storage_gb': 100,
            'min_cpu_cores': 4,
            'max_latency_ms': 25,
            'min_cache_hit_rate': 0.80,
            'max_memory_usage': 0.85,
            'max_cpu_usage': 0.80
        }
        
        self.monitoring_config = {
            'prometheus_port': 9090,
            'grafana_port': 3002,
            'alertmanager_port': 9093,
            'metrics_scrape_interval': '15s',
            'alert_evaluation_interval': '15s'
        }
        
        self.results = {
            'setup_start': datetime.now(timezone.utc).isoformat(),
            'infrastructure_checks': {},
            'monitoring_setup': {},
            'security_hardening': {},
            'deployment_validation': {},
            'production_readiness': {},
            'overall_status': 'PENDING'
        }

    def check_system_requirements(self) -> bool:
        """Check if system meets production requirements."""
        logger.info("🔍 Checking production system requirements...")
        
        checks = {}
        all_passed = True
        
        # Check CPU cores
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_passed = cpu_cores >= self.production_requirements['min_cpu_cores']
        checks['cpu_cores'] = {
            'required': self.production_requirements['min_cpu_cores'],
            'actual': cpu_cores,
            'passed': cpu_passed
        }
        all_passed &= cpu_passed
        logger.info(f"CPU Cores: {cpu_cores} (Required: ≥{self.production_requirements['min_cpu_cores']}) - {'✅ PASSED' if cpu_passed else '❌ FAILED'}")
        
        # Check memory
        memory_info = psutil.virtual_memory()
        memory_gb = memory_info.total / (1024**3)
        memory_passed = memory_gb >= self.production_requirements['min_memory_gb']
        checks['memory_gb'] = {
            'required': self.production_requirements['min_memory_gb'],
            'actual': round(memory_gb, 1),
            'passed': memory_passed
        }
        all_passed &= memory_passed
        logger.info(f"Memory: {memory_gb:.1f}GB (Required: ≥{self.production_requirements['min_memory_gb']}GB) - {'✅ PASSED' if memory_passed else '❌ FAILED'}")
        
        # Check disk space
        disk_info = psutil.disk_usage('/')
        disk_gb = disk_info.free / (1024**3)
        disk_passed = disk_gb >= self.production_requirements['min_storage_gb']
        checks['storage_gb'] = {
            'required': self.production_requirements['min_storage_gb'],
            'actual': round(disk_gb, 1),
            'passed': disk_passed
        }
        all_passed &= disk_passed
        logger.info(f"Available Storage: {disk_gb:.1f}GB (Required: ≥{self.production_requirements['min_storage_gb']}GB) - {'✅ PASSED' if disk_passed else '❌ FAILED'}")
        
        # Check Docker availability
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
            docker_passed = result.returncode == 0
            checks['docker'] = {
                'required': True,
                'actual': docker_passed,
                'passed': docker_passed,
                'version': result.stdout.strip() if docker_passed else 'Not available'
            }
            all_passed &= docker_passed
            logger.info(f"Docker: {'✅ AVAILABLE' if docker_passed else '❌ NOT AVAILABLE'}")
        except Exception as e:
            checks['docker'] = {'required': True, 'actual': False, 'passed': False, 'error': str(e)}
            all_passed = False
            logger.error(f"Docker: ❌ NOT AVAILABLE - {e}")
        
        self.results['infrastructure_checks'] = checks
        return all_passed

    def setup_monitoring_stack(self) -> bool:
        """Set up Prometheus, Grafana, and AlertManager monitoring."""
        logger.info("📊 Setting up monitoring stack...")
        
        monitoring_results = {}
        
        # Create monitoring configuration directories
        try:
            os.makedirs('monitoring/prometheus', exist_ok=True)
            os.makedirs('monitoring/grafana', exist_ok=True)
            os.makedirs('monitoring/alertmanager', exist_ok=True)
            
            # Create Prometheus configuration
            prometheus_config = {
                'global': {
                    'scrape_interval': self.monitoring_config['metrics_scrape_interval'],
                    'evaluation_interval': self.monitoring_config['alert_evaluation_interval']
                },
                'scrape_configs': [
                    {
                        'job_name': 'acgs-services',
                        'static_configs': [
                            {
                                'targets': [f'localhost:{port}' for port in [8000, 8001, 8002, 8003, 8004, 8005]]
                            }
                        ],
                        'metrics_path': '/metrics',
                        'scrape_interval': '15s'
                    },
                    {
                        'job_name': 'node-exporter',
                        'static_configs': [{'targets': ['localhost:9100']}]
                    }
                ],
                'rule_files': ['alert_rules.yml'],
                'alerting': {
                    'alertmanagers': [
                        {
                            'static_configs': [
                                {'targets': [f'localhost:{self.monitoring_config["alertmanager_port"]}']}
                            ]
                        }
                    ]
                }
            }
            
            # Save Prometheus config
            import yaml
            with open('monitoring/prometheus/prometheus.yml', 'w') as f:
                yaml.dump(prometheus_config, f, default_flow_style=False)
            
            monitoring_results['prometheus_config'] = {'status': 'created', 'path': 'monitoring/prometheus/prometheus.yml'}
            logger.info("✅ Prometheus configuration created")
            
        except Exception as e:
            monitoring_results['prometheus_config'] = {'status': 'failed', 'error': str(e)}
            logger.error(f"❌ Failed to create Prometheus config: {e}")
        
        # Create AlertManager configuration
        try:
            alertmanager_config = {
                'global': {
                    'smtp_smarthost': 'localhost:587',
                    'smtp_from': 'alerts@acgs.local'
                },
                'route': {
                    'group_by': ['alertname'],
                    'group_wait': '10s',
                    'group_interval': '10s',
                    'repeat_interval': '1h',
                    'receiver': 'web.hook'
                },
                'receivers': [
                    {
                        'name': 'web.hook',
                        'webhook_configs': [
                            {
                                'url': 'http://localhost:5001/webhook',
                                'send_resolved': True
                            }
                        ]
                    }
                ]
            }
            
            with open('monitoring/alertmanager/alertmanager.yml', 'w') as f:
                yaml.dump(alertmanager_config, f, default_flow_style=False)
            
            monitoring_results['alertmanager_config'] = {'status': 'created', 'path': 'monitoring/alertmanager/alertmanager.yml'}
            logger.info("✅ AlertManager configuration created")
            
        except Exception as e:
            monitoring_results['alertmanager_config'] = {'status': 'failed', 'error': str(e)}
            logger.error(f"❌ Failed to create AlertManager config: {e}")
        
        # Create alert rules
        try:
            alert_rules = {
                'groups': [
                    {
                        'name': 'acgs-alerts',
                        'rules': [
                            {
                                'alert': 'HighLatency',
                                'expr': 'http_request_duration_seconds{quantile="0.95"} > 0.025',
                                'for': '2m',
                                'labels': {'severity': 'warning'},
                                'annotations': {
                                    'summary': 'High latency detected',
                                    'description': '95th percentile latency is above 25ms for {{ $labels.instance }}'
                                }
                            },
                            {
                                'alert': 'HighMemoryUsage',
                                'expr': 'node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.15',
                                'for': '5m',
                                'labels': {'severity': 'warning'},
                                'annotations': {
                                    'summary': 'High memory usage',
                                    'description': 'Memory usage is above 85% for {{ $labels.instance }}'
                                }
                            },
                            {
                                'alert': 'ServiceDown',
                                'expr': 'up == 0',
                                'for': '1m',
                                'labels': {'severity': 'critical'},
                                'annotations': {
                                    'summary': 'Service is down',
                                    'description': 'Service {{ $labels.instance }} is down'
                                }
                            }
                        ]
                    }
                ]
            }
            
            with open('monitoring/prometheus/alert_rules.yml', 'w') as f:
                yaml.dump(alert_rules, f, default_flow_style=False)
            
            monitoring_results['alert_rules'] = {'status': 'created', 'path': 'monitoring/prometheus/alert_rules.yml'}
            logger.info("✅ Alert rules created")
            
        except Exception as e:
            monitoring_results['alert_rules'] = {'status': 'failed', 'error': str(e)}
            logger.error(f"❌ Failed to create alert rules: {e}")
        
        self.results['monitoring_setup'] = monitoring_results
        return all(result.get('status') == 'created' for result in monitoring_results.values())

    def create_production_docker_compose(self) -> bool:
        """Create production Docker Compose configuration."""
        logger.info("🐳 Creating production Docker Compose configuration...")
        
        try:
            docker_compose_prod = {
                'version': '3.8',
                'services': {
                    'prometheus': {
                        'image': 'prom/prometheus:latest',
                        'container_name': 'acgs-prometheus-prod',
                        'ports': [f'{self.monitoring_config["prometheus_port"]}:9090'],
                        'volumes': [
                            './monitoring/prometheus:/etc/prometheus',
                            'prometheus_data:/prometheus'
                        ],
                        'command': [
                            '--config.file=/etc/prometheus/prometheus.yml',
                            '--storage.tsdb.path=/prometheus',
                            '--web.console.libraries=/etc/prometheus/console_libraries',
                            '--web.console.templates=/etc/prometheus/consoles',
                            '--storage.tsdb.retention.time=200h',
                            '--web.enable-lifecycle'
                        ],
                        'restart': 'unless-stopped'
                    },
                    'grafana': {
                        'image': 'grafana/grafana:latest',
                        'container_name': 'acgs-grafana-prod',
                        'ports': [f'{self.monitoring_config["grafana_port"]}:3000'],
                        'volumes': [
                            'grafana_data:/var/lib/grafana',
                            './monitoring/grafana:/etc/grafana/provisioning'
                        ],
                        'environment': [
                            'GF_SECURITY_ADMIN_PASSWORD=acgs_admin_2024',
                            'GF_USERS_ALLOW_SIGN_UP=false'
                        ],
                        'restart': 'unless-stopped'
                    },
                    'alertmanager': {
                        'image': 'prom/alertmanager:latest',
                        'container_name': 'acgs-alertmanager-prod',
                        'ports': [f'{self.monitoring_config["alertmanager_port"]}:9093'],
                        'volumes': [
                            './monitoring/alertmanager:/etc/alertmanager'
                        ],
                        'command': [
                            '--config.file=/etc/alertmanager/alertmanager.yml',
                            '--storage.path=/alertmanager',
                            '--web.external-url=http://localhost:9093'
                        ],
                        'restart': 'unless-stopped'
                    },
                    'node-exporter': {
                        'image': 'prom/node-exporter:latest',
                        'container_name': 'acgs-node-exporter-prod',
                        'ports': ['9100:9100'],
                        'volumes': [
                            '/proc:/host/proc:ro',
                            '/sys:/host/sys:ro',
                            '/:/rootfs:ro'
                        ],
                        'command': [
                            '--path.procfs=/host/proc',
                            '--path.rootfs=/rootfs',
                            '--path.sysfs=/host/sys',
                            '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
                        ],
                        'restart': 'unless-stopped'
                    }
                },
                'volumes': {
                    'prometheus_data': {},
                    'grafana_data': {}
                },
                'networks': {
                    'acgs-monitoring': {
                        'driver': 'bridge'
                    }
                }
            }
            
            import yaml
            with open('docker-compose.monitoring.yml', 'w') as f:
                yaml.dump(docker_compose_prod, f, default_flow_style=False)
            
            logger.info("✅ Production Docker Compose configuration created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Docker Compose config: {e}")
            return False

    def validate_production_deployment(self) -> bool:
        """Validate production deployment readiness."""
        logger.info("🎯 Validating production deployment readiness...")
        
        validation_results = {}
        all_passed = True
        
        # Check service health
        import requests
        healthy_services = 0
        for service_id, config in self.services.items():
            try:
                response = requests.get(f"http://localhost:{config['port']}/health", timeout=5)
                if response.status_code == 200:
                    healthy_services += 1
                    logger.info(f"✅ {config['name']} - Healthy")
                else:
                    logger.warning(f"⚠️ {config['name']} - Unhealthy (Status: {response.status_code})")
            except Exception as e:
                logger.error(f"❌ {config['name']} - Error: {e}")
        
        service_health_passed = healthy_services == len(self.services)
        validation_results['service_health'] = {
            'healthy_services': healthy_services,
            'total_services': len(self.services),
            'passed': service_health_passed
        }
        all_passed &= service_health_passed
        
        # Check system performance
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        cpu_passed = cpu_percent < (self.production_requirements['max_cpu_usage'] * 100)
        memory_passed = memory_percent < (self.production_requirements['max_memory_usage'] * 100)
        
        validation_results['system_performance'] = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'cpu_passed': cpu_passed,
            'memory_passed': memory_passed
        }
        all_passed &= cpu_passed and memory_passed
        
        logger.info(f"CPU Usage: {cpu_percent:.1f}% (Target: <{self.production_requirements['max_cpu_usage']*100:.0f}%) - {'✅ PASSED' if cpu_passed else '❌ FAILED'}")
        logger.info(f"Memory Usage: {memory_percent:.1f}% (Target: <{self.production_requirements['max_memory_usage']*100:.0f}%) - {'✅ PASSED' if memory_passed else '❌ FAILED'}")
        
        self.results['deployment_validation'] = validation_results
        return all_passed

    def generate_production_readiness_report(self) -> bool:
        """Generate comprehensive production readiness report."""
        logger.info("📋 Generating production readiness report...")
        
        readiness_score = 0.0
        max_score = 4.0  # 4 main categories
        
        # Infrastructure checks (25%)
        if self.results.get('infrastructure_checks', {}).get('cpu_cores', {}).get('passed', False):
            readiness_score += 0.25
        if self.results.get('infrastructure_checks', {}).get('memory_gb', {}).get('passed', False):
            readiness_score += 0.25
        if self.results.get('infrastructure_checks', {}).get('storage_gb', {}).get('passed', False):
            readiness_score += 0.25
        if self.results.get('infrastructure_checks', {}).get('docker', {}).get('passed', False):
            readiness_score += 0.25
        
        # Monitoring setup (25%)
        monitoring_setup = self.results.get('monitoring_setup', {})
        monitoring_score = sum(1 for result in monitoring_setup.values() if result.get('status') == 'created')
        readiness_score += (monitoring_score / max(len(monitoring_setup), 1)) * 1.0
        
        # Service health (25%)
        deployment_validation = self.results.get('deployment_validation', {})
        if deployment_validation.get('service_health', {}).get('passed', False):
            readiness_score += 1.0
        
        # System performance (25%)
        if deployment_validation.get('system_performance', {}).get('cpu_passed', False):
            readiness_score += 0.5
        if deployment_validation.get('system_performance', {}).get('memory_passed', False):
            readiness_score += 0.5
        
        readiness_percentage = (readiness_score / max_score) * 100
        production_ready = readiness_percentage >= 90.0
        
        self.results['production_readiness'] = {
            'readiness_score': readiness_score,
            'max_score': max_score,
            'readiness_percentage': readiness_percentage,
            'production_ready': production_ready,
            'requirements_met': {
                'infrastructure': all(
                    check.get('passed', False) 
                    for check in self.results.get('infrastructure_checks', {}).values()
                ),
                'monitoring': len([
                    r for r in self.results.get('monitoring_setup', {}).values() 
                    if r.get('status') == 'created'
                ]) >= 3,
                'services': self.results.get('deployment_validation', {}).get('service_health', {}).get('passed', False),
                'performance': (
                    self.results.get('deployment_validation', {}).get('system_performance', {}).get('cpu_passed', False) and
                    self.results.get('deployment_validation', {}).get('system_performance', {}).get('memory_passed', False)
                )
            }
        }
        
        self.results['overall_status'] = 'READY' if production_ready else 'NOT_READY'
        
        logger.info(f"Production Readiness Score: {readiness_percentage:.1f}%")
        logger.info(f"Production Ready: {'✅ YES' if production_ready else '❌ NO'}")
        
        return production_ready

    async def setup_production_infrastructure(self) -> bool:
        """Run complete production infrastructure setup."""
        logger.info("🚀 Starting ACGS Phase 3 Production Infrastructure Setup")
        logger.info("=" * 80)
        
        try:
            # Step 1: Check system requirements
            if not self.check_system_requirements():
                logger.error("❌ System requirements not met. Cannot proceed with production setup.")
                return False
            
            # Step 2: Set up monitoring stack
            self.setup_monitoring_stack()
            
            # Step 3: Create production Docker Compose
            self.create_production_docker_compose()
            
            # Step 4: Validate deployment
            self.validate_production_deployment()
            
            # Step 5: Generate readiness report
            production_ready = self.generate_production_readiness_report()
            
            # Step 6: Save final report
            self.save_final_report()
            
            return production_ready
            
        except Exception as e:
            logger.error(f"❌ Production infrastructure setup failed: {str(e)}")
            self.results['overall_status'] = 'ERROR'
            self.results['error_message'] = str(e)
            return False

    def save_final_report(self):
        """Save comprehensive production setup report."""
        self.results['setup_end'] = datetime.now(timezone.utc).isoformat()
        
        # Save detailed results to file
        report_file = f"logs/phase3_production_setup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info("=" * 80)
        logger.info("🎉 ACGS Phase 3 Production Infrastructure Setup Complete!")
        logger.info("=" * 80)
        logger.info(f"Overall Status: {'✅ READY' if self.results['overall_status'] == 'READY' else '❌ NOT READY'}")
        
        if self.results['overall_status'] == 'READY':
            logger.info("🚀 Production infrastructure is ready for deployment!")
            logger.info("Next steps:")
            logger.info("  1. Start monitoring stack: docker-compose -f docker-compose.monitoring.yml up -d")
            logger.info("  2. Access Grafana: http://localhost:3002 (admin/acgs_admin_2024)")
            logger.info("  3. Access Prometheus: http://localhost:9090")
            logger.info("  4. Deploy services with blue-green strategy")
        else:
            logger.info("⚠️ Production infrastructure setup incomplete. Review requirements.")
        
        logger.info(f"Detailed Report: {report_file}")

async def main():
    parser = argparse.ArgumentParser(description='ACGS Phase 3 Production Infrastructure Setup')
    parser.add_argument('--validate-only', action='store_true', help='Only validate current setup without changes')
    
    args = parser.parse_args()
    
    infrastructure = ACGSProductionInfrastructure()
    
    if args.validate_only:
        logger.info("🔍 Running validation-only mode...")
        success = infrastructure.validate_production_deployment()
        infrastructure.generate_production_readiness_report()
        infrastructure.save_final_report()
    else:
        success = await infrastructure.setup_production_infrastructure()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
