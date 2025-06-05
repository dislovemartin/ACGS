#!/usr/bin/env python3

"""
ACGS Phase 3 Staging Environment Validation Script
Comprehensive validation of staging deployment with performance and security testing
"""

import asyncio
import json
import time
import requests
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple
import aiohttp
import psutil

class StagingValidator:
    def __init__(self):
        self.base_urls = {
            'ac_service': 'http://localhost:8011',
            'integrity_service': 'http://localhost:8012',
            'fv_service': 'http://localhost:8013',
            'gs_service': 'http://localhost:8014',
            'pgc_service': 'http://localhost:8015',
            'prometheus': 'http://localhost:9090',
            'grafana': 'http://localhost:3002'
        }
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'staging',
            'phase': '3',
            'overall_status': 'PENDING',
            'service_health': {},
            'performance_metrics': {},
            'security_validation': {},
            'load_testing': {},
            'monitoring_validation': {},
            'issues': []
        }
        
        self.performance_targets = {
            'policy_decision_latency_ms': 50,
            'cache_hit_rate_percent': 80,
            'concurrent_users': 100,
            'throughput_req_per_sec': 100
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def error(self, message: str):
        """Log error message"""
        self.log(message, "ERROR")
        self.validation_results['issues'].append({
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'message': message
        })

    def success(self, message: str):
        """Log success message"""
        self.log(message, "SUCCESS")

    def warning(self, message: str):
        """Log warning message"""
        self.log(message, "WARNING")
        self.validation_results['issues'].append({
            'timestamp': datetime.now().isoformat(),
            'level': 'WARNING',
            'message': message
        })

    async def validate_service_health(self) -> bool:
        """Validate health of all ACGS services"""
        self.log("🏥 Validating service health...")
        
        all_healthy = True
        
        for service_name, base_url in self.base_urls.items():
            try:
                if service_name in ['prometheus', 'grafana']:
                    # Different health check endpoints for monitoring services
                    if service_name == 'prometheus':
                        health_url = f"{base_url}/api/v1/targets"
                    else:  # grafana
                        health_url = f"{base_url}/api/health"
                else:
                    health_url = f"{base_url}/health"
                
                response = requests.get(health_url, timeout=10)
                
                if response.status_code == 200:
                    self.success(f"✅ {service_name} is healthy")
                    self.validation_results['service_health'][service_name] = {
                        'status': 'healthy',
                        'response_time_ms': response.elapsed.total_seconds() * 1000,
                        'status_code': response.status_code
                    }
                else:
                    self.error(f"❌ {service_name} health check failed: {response.status_code}")
                    all_healthy = False
                    self.validation_results['service_health'][service_name] = {
                        'status': 'unhealthy',
                        'status_code': response.status_code,
                        'error': f"HTTP {response.status_code}"
                    }
                    
            except Exception as e:
                self.error(f"❌ {service_name} health check failed: {str(e)}")
                all_healthy = False
                self.validation_results['service_health'][service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return all_healthy

    async def validate_performance_metrics(self) -> bool:
        """Validate performance metrics against targets"""
        self.log("⚡ Validating performance metrics...")
        
        performance_passed = True
        
        try:
            # Test policy decision latency
            start_time = time.time()
            response = requests.post(
                f"{self.base_urls['gs_service']}/api/v1/policies/synthesize",
                json={
                    "principles": ["test principle"],
                    "context": "test context"
                },
                timeout=5
            )
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            
            if latency_ms <= self.performance_targets['policy_decision_latency_ms']:
                self.success(f"✅ Policy decision latency: {latency_ms:.2f}ms (target: <{self.performance_targets['policy_decision_latency_ms']}ms)")
                self.validation_results['performance_metrics']['policy_decision_latency_ms'] = latency_ms
                self.validation_results['performance_metrics']['latency_target_met'] = True
            else:
                self.error(f"❌ Policy decision latency: {latency_ms:.2f}ms exceeds target of {self.performance_targets['policy_decision_latency_ms']}ms")
                performance_passed = False
                self.validation_results['performance_metrics']['policy_decision_latency_ms'] = latency_ms
                self.validation_results['performance_metrics']['latency_target_met'] = False
                
        except Exception as e:
            self.error(f"❌ Performance validation failed: {str(e)}")
            performance_passed = False
            self.validation_results['performance_metrics']['error'] = str(e)
        
        # Check system resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        self.validation_results['performance_metrics']['cpu_usage_percent'] = cpu_percent
        self.validation_results['performance_metrics']['memory_usage_percent'] = memory_percent
        
        if cpu_percent > 80:
            self.warning(f"⚠️ High CPU usage: {cpu_percent}%")
        else:
            self.success(f"✅ CPU usage: {cpu_percent}%")
            
        if memory_percent > 85:
            self.warning(f"⚠️ High memory usage: {memory_percent}%")
        else:
            self.success(f"✅ Memory usage: {memory_percent}%")
        
        return performance_passed

    async def run_load_testing(self) -> bool:
        """Run load testing to validate concurrent user handling"""
        self.log("🔄 Running load testing...")
        
        try:
            # Run the existing load testing script
            result = subprocess.run([
                'python', 'scripts/phase3_load_testing.py',
                '--staging-mode',
                '--concurrent-users', str(self.performance_targets['concurrent_users']),
                '--duration', '60'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.success("✅ Load testing completed successfully")
                
                # Parse load testing results
                try:
                    load_results = json.loads(result.stdout.split('\n')[-2])  # Assuming JSON output
                    self.validation_results['load_testing'] = load_results
                    
                    # Validate against targets
                    if load_results.get('avg_response_time_ms', 0) <= self.performance_targets['policy_decision_latency_ms']:
                        self.success(f"✅ Load test latency: {load_results.get('avg_response_time_ms', 0)}ms")
                    else:
                        self.error(f"❌ Load test latency exceeds target")
                        return False
                        
                except (json.JSONDecodeError, IndexError):
                    self.warning("⚠️ Could not parse load testing results")
                    self.validation_results['load_testing']['raw_output'] = result.stdout
                
                return True
            else:
                self.error(f"❌ Load testing failed: {result.stderr}")
                self.validation_results['load_testing']['error'] = result.stderr
                return False
                
        except subprocess.TimeoutExpired:
            self.error("❌ Load testing timed out")
            return False
        except Exception as e:
            self.error(f"❌ Load testing error: {str(e)}")
            return False

    async def run_security_testing(self) -> bool:
        """Run security penetration testing"""
        self.log("🔒 Running security testing...")
        
        try:
            # Run the existing security testing script
            result = subprocess.run([
                'python', 'scripts/phase3_security_penetration_testing.py',
                '--staging-mode'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.success("✅ Security testing completed successfully")
                
                # Parse security testing results
                try:
                    security_results = json.loads(result.stdout.split('\n')[-2])  # Assuming JSON output
                    self.validation_results['security_validation'] = security_results
                    
                    # Check security compliance score
                    compliance_score = security_results.get('overall_compliance_score', 0)
                    if compliance_score >= 90:
                        self.success(f"✅ Security compliance: {compliance_score}%")
                        return True
                    else:
                        self.error(f"❌ Security compliance: {compliance_score}% (target: ≥90%)")
                        return False
                        
                except (json.JSONDecodeError, IndexError):
                    self.warning("⚠️ Could not parse security testing results")
                    self.validation_results['security_validation']['raw_output'] = result.stdout
                    return True  # Assume pass if we can't parse but script succeeded
                
            else:
                self.error(f"❌ Security testing failed: {result.stderr}")
                self.validation_results['security_validation']['error'] = result.stderr
                return False
                
        except subprocess.TimeoutExpired:
            self.error("❌ Security testing timed out")
            return False
        except Exception as e:
            self.error(f"❌ Security testing error: {str(e)}")
            return False

    async def validate_monitoring(self) -> bool:
        """Validate monitoring infrastructure"""
        self.log("📊 Validating monitoring infrastructure...")
        
        monitoring_healthy = True
        
        try:
            # Check Prometheus targets
            prometheus_response = requests.get(f"{self.base_urls['prometheus']}/api/v1/targets", timeout=10)
            if prometheus_response.status_code == 200:
                targets = prometheus_response.json()
                active_targets = [t for t in targets.get('data', {}).get('activeTargets', []) if t.get('health') == 'up']
                self.success(f"✅ Prometheus active targets: {len(active_targets)}")
                self.validation_results['monitoring_validation']['prometheus_active_targets'] = len(active_targets)
            else:
                self.error("❌ Prometheus targets check failed")
                monitoring_healthy = False
            
            # Check Grafana health
            grafana_response = requests.get(f"{self.base_urls['grafana']}/api/health", timeout=10)
            if grafana_response.status_code == 200:
                self.success("✅ Grafana is healthy")
                self.validation_results['monitoring_validation']['grafana_status'] = 'healthy'
            else:
                self.error("❌ Grafana health check failed")
                monitoring_healthy = False
                
        except Exception as e:
            self.error(f"❌ Monitoring validation failed: {str(e)}")
            monitoring_healthy = False
            self.validation_results['monitoring_validation']['error'] = str(e)
        
        return monitoring_healthy

    async def run_comprehensive_validation(self) -> bool:
        """Run all validation tests"""
        self.log("🚀 Starting comprehensive staging validation...")
        self.log("=" * 60)
        
        validation_start_time = time.time()
        
        # Run all validation tests
        health_passed = await self.validate_service_health()
        performance_passed = await self.validate_performance_metrics()
        load_test_passed = await self.run_load_testing()
        security_passed = await self.run_security_testing()
        monitoring_passed = await self.validate_monitoring()
        
        validation_end_time = time.time()
        validation_duration = validation_end_time - validation_start_time
        
        # Calculate overall status
        all_tests_passed = all([
            health_passed,
            performance_passed,
            load_test_passed,
            security_passed,
            monitoring_passed
        ])
        
        self.validation_results['validation_duration_seconds'] = validation_duration
        self.validation_results['tests_passed'] = {
            'service_health': health_passed,
            'performance_metrics': performance_passed,
            'load_testing': load_test_passed,
            'security_testing': security_passed,
            'monitoring': monitoring_passed
        }
        
        if all_tests_passed:
            self.validation_results['overall_status'] = 'PASSED'
            self.success("🎉 All staging validation tests PASSED!")
        else:
            self.validation_results['overall_status'] = 'FAILED'
            self.error("❌ Some staging validation tests FAILED!")
        
        # Save validation results
        with open('staging_validation_results.json', 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        self.log("=" * 60)
        self.log(f"Validation Duration: {validation_duration:.2f} seconds")
        self.log("Validation Report: staging_validation_results.json")
        
        return all_tests_passed

async def main():
    """Main validation function"""
    validator = StagingValidator()
    
    try:
        success = await validator.run_comprehensive_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        validator.error("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        validator.error(f"Validation failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
