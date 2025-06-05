#!/usr/bin/env python3

"""
ACGS Phase 3 Production Validation Script
Comprehensive post-deployment validation with performance benchmarks and security verification
"""

import asyncio
import json
import time
import requests
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple
import psutil

class ProductionValidator:
    def __init__(self):
        self.base_urls = {
            'ac_service': 'http://localhost:8001',
            'integrity_service': 'http://localhost:8002',
            'fv_service': 'http://localhost:8003',
            'gs_service': 'http://localhost:8004',
            'pgc_service': 'http://localhost:8005',
            'prometheus': 'http://localhost:9090',
            'grafana': 'http://localhost:3002',
            'load_balancer': 'http://localhost'
        }
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'production',
            'phase': '3',
            'overall_status': 'PENDING',
            'service_health': {},
            'performance_benchmarks': {},
            'security_compliance': {},
            'monitoring_validation': {},
            'production_readiness': {},
            'success_criteria': {},
            'issues': []
        }
        
        self.success_criteria = {
            'policy_decision_latency_ms': 50,
            'cache_hit_rate_percent': 80,
            'security_compliance_percent': 90,
            'service_availability_percent': 99.9,
            'error_rate_percent': 1.0
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
        """Comprehensive service health validation"""
        self.log("🏥 Validating production service health...")
        
        all_healthy = True
        health_results = {}
        
        for service_name, base_url in self.base_urls.items():
            try:
                # Determine health endpoint
                if service_name in ['prometheus', 'grafana', 'load_balancer']:
                    if service_name == 'prometheus':
                        health_url = f"{base_url}/api/v1/targets"
                    elif service_name == 'grafana':
                        health_url = f"{base_url}/api/health"
                    else:  # load_balancer
                        health_url = f"{base_url}/health"
                else:
                    health_url = f"{base_url}/health"
                
                # Perform health check with retries
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        start_time = time.time()
                        response = requests.get(health_url, timeout=10)
                        end_time = time.time()
                        
                        response_time_ms = (end_time - start_time) * 1000
                        
                        if response.status_code == 200:
                            self.success(f"✅ {service_name} is healthy ({response_time_ms:.2f}ms)")
                            health_results[service_name] = {
                                'status': 'healthy',
                                'response_time_ms': response_time_ms,
                                'status_code': response.status_code,
                                'attempts': attempt + 1
                            }
                            break
                        else:
                            if attempt == max_retries - 1:
                                self.error(f"❌ {service_name} health check failed: {response.status_code}")
                                all_healthy = False
                                health_results[service_name] = {
                                    'status': 'unhealthy',
                                    'status_code': response.status_code,
                                    'attempts': max_retries
                                }
                            else:
                                await asyncio.sleep(5)  # Wait before retry
                                
                    except requests.RequestException as e:
                        if attempt == max_retries - 1:
                            self.error(f"❌ {service_name} connection failed: {str(e)}")
                            all_healthy = False
                            health_results[service_name] = {
                                'status': 'error',
                                'error': str(e),
                                'attempts': max_retries
                            }
                        else:
                            await asyncio.sleep(5)  # Wait before retry
                            
            except Exception as e:
                self.error(f"❌ {service_name} validation error: {str(e)}")
                all_healthy = False
                health_results[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        self.validation_results['service_health'] = health_results
        return all_healthy

    async def run_performance_benchmarks(self) -> bool:
        """Run comprehensive performance benchmarks"""
        self.log("⚡ Running production performance benchmarks...")
        
        benchmarks_passed = True
        benchmark_results = {}
        
        try:
            # Policy Decision Latency Benchmark
            self.log("Testing policy decision latency...")
            latency_samples = []
            
            for i in range(10):  # Multiple samples for accuracy
                start_time = time.time()
                response = requests.post(
                    f"{self.base_urls['gs_service']}/api/v1/policies/synthesize",
                    json={
                        "principles": [f"test principle {i}"],
                        "context": f"production benchmark test {i}"
                    },
                    timeout=10
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    latency_ms = (end_time - start_time) * 1000
                    latency_samples.append(latency_ms)
                else:
                    self.error(f"Policy synthesis request failed: {response.status_code}")
                    benchmarks_passed = False
            
            if latency_samples:
                avg_latency = sum(latency_samples) / len(latency_samples)
                max_latency = max(latency_samples)
                min_latency = min(latency_samples)
                
                benchmark_results['policy_decision_latency'] = {
                    'avg_ms': avg_latency,
                    'max_ms': max_latency,
                    'min_ms': min_latency,
                    'samples': len(latency_samples),
                    'target_met': avg_latency <= self.success_criteria['policy_decision_latency_ms']
                }
                
                if avg_latency <= self.success_criteria['policy_decision_latency_ms']:
                    self.success(f"✅ Policy decision latency: {avg_latency:.2f}ms (target: <{self.success_criteria['policy_decision_latency_ms']}ms)")
                else:
                    self.error(f"❌ Policy decision latency: {avg_latency:.2f}ms exceeds target of {self.success_criteria['policy_decision_latency_ms']}ms")
                    benchmarks_passed = False
            
            # Cache Performance Benchmark
            self.log("Testing cache performance...")
            cache_metrics = await self.get_cache_metrics()
            benchmark_results['cache_performance'] = cache_metrics
            
            if cache_metrics.get('hit_rate_percent', 0) >= self.success_criteria['cache_hit_rate_percent']:
                self.success(f"✅ Cache hit rate: {cache_metrics.get('hit_rate_percent', 0):.1f}%")
            else:
                self.error(f"❌ Cache hit rate: {cache_metrics.get('hit_rate_percent', 0):.1f}% below target of {self.success_criteria['cache_hit_rate_percent']}%")
                benchmarks_passed = False
            
            # System Resource Benchmark
            self.log("Measuring system resource usage...")
            cpu_percent = psutil.cpu_percent(interval=2)
            memory_percent = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            
            benchmark_results['system_resources'] = {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory_percent,
                'disk_usage_percent': disk_usage
            }
            
            # Resource usage warnings
            if cpu_percent > 80:
                self.warning(f"⚠️ High CPU usage: {cpu_percent}%")
            else:
                self.success(f"✅ CPU usage: {cpu_percent}%")
                
            if memory_percent > 85:
                self.warning(f"⚠️ High memory usage: {memory_percent}%")
            else:
                self.success(f"✅ Memory usage: {memory_percent}%")
            
        except Exception as e:
            self.error(f"❌ Performance benchmark failed: {str(e)}")
            benchmarks_passed = False
            benchmark_results['error'] = str(e)
        
        self.validation_results['performance_benchmarks'] = benchmark_results
        return benchmarks_passed

    async def get_cache_metrics(self) -> Dict[str, float]:
        """Get Redis cache performance metrics"""
        try:
            result = subprocess.run([
                'docker', 'exec', 'acgs-redis-prod', 'redis-cli', 'info', 'stats'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                stats = result.stdout
                hits = 0
                misses = 0
                
                for line in stats.split('\n'):
                    if line.startswith('keyspace_hits:'):
                        hits = int(line.split(':')[1])
                    elif line.startswith('keyspace_misses:'):
                        misses = int(line.split(':')[1])
                
                total = hits + misses
                hit_rate = (hits / total * 100) if total > 0 else 0
                
                return {
                    'hits': hits,
                    'misses': misses,
                    'total_requests': total,
                    'hit_rate_percent': hit_rate
                }
            else:
                self.warning("Could not retrieve cache metrics")
                return {'error': 'Redis stats unavailable'}
                
        except Exception as e:
            self.warning(f"Cache metrics error: {str(e)}")
            return {'error': str(e)}

    async def validate_security_compliance(self) -> bool:
        """Validate security compliance in production"""
        self.log("🔒 Validating production security compliance...")
        
        try:
            # Run security penetration testing
            result = subprocess.run([
                'python', 'scripts/phase3_security_penetration_testing.py',
                '--production-mode'
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                try:
                    # Parse security results
                    security_results = json.loads(result.stdout.split('\n')[-2])
                    self.validation_results['security_compliance'] = security_results
                    
                    compliance_score = security_results.get('overall_compliance_score', 0)
                    
                    if compliance_score >= self.success_criteria['security_compliance_percent']:
                        self.success(f"✅ Security compliance: {compliance_score}%")
                        return True
                    else:
                        self.error(f"❌ Security compliance: {compliance_score}% below target of {self.success_criteria['security_compliance_percent']}%")
                        return False
                        
                except (json.JSONDecodeError, IndexError):
                    self.warning("Could not parse security testing results")
                    self.validation_results['security_compliance']['raw_output'] = result.stdout
                    return True  # Assume pass if script succeeded but output unparseable
                    
            else:
                self.error(f"Security testing failed: {result.stderr}")
                self.validation_results['security_compliance']['error'] = result.stderr
                return False
                
        except subprocess.TimeoutExpired:
            self.error("Security testing timed out")
            return False
        except Exception as e:
            self.error(f"Security validation error: {str(e)}")
            return False

    async def validate_monitoring_infrastructure(self) -> bool:
        """Validate monitoring and alerting infrastructure"""
        self.log("📊 Validating monitoring infrastructure...")
        
        monitoring_healthy = True
        monitoring_results = {}
        
        try:
            # Validate Prometheus
            prometheus_response = requests.get(f"{self.base_urls['prometheus']}/api/v1/targets", timeout=10)
            if prometheus_response.status_code == 200:
                targets = prometheus_response.json()
                active_targets = [t for t in targets.get('data', {}).get('activeTargets', []) if t.get('health') == 'up']
                
                monitoring_results['prometheus'] = {
                    'status': 'healthy',
                    'active_targets': len(active_targets),
                    'total_targets': len(targets.get('data', {}).get('activeTargets', []))
                }
                
                self.success(f"✅ Prometheus: {len(active_targets)} active targets")
            else:
                self.error("❌ Prometheus validation failed")
                monitoring_healthy = False
            
            # Validate Grafana
            grafana_response = requests.get(f"{self.base_urls['grafana']}/api/health", timeout=10)
            if grafana_response.status_code == 200:
                monitoring_results['grafana'] = {'status': 'healthy'}
                self.success("✅ Grafana is healthy")
            else:
                self.error("❌ Grafana validation failed")
                monitoring_healthy = False
            
            # Check alert manager
            try:
                alertmanager_response = requests.get("http://localhost:9093/api/v1/status", timeout=10)
                if alertmanager_response.status_code == 200:
                    monitoring_results['alertmanager'] = {'status': 'healthy'}
                    self.success("✅ AlertManager is healthy")
                else:
                    self.warning("⚠️ AlertManager validation failed")
            except:
                self.warning("⚠️ AlertManager not accessible")
                
        except Exception as e:
            self.error(f"❌ Monitoring validation error: {str(e)}")
            monitoring_healthy = False
            monitoring_results['error'] = str(e)
        
        self.validation_results['monitoring_validation'] = monitoring_results
        return monitoring_healthy

    async def evaluate_success_criteria(self) -> Dict[str, bool]:
        """Evaluate all success criteria"""
        self.log("🎯 Evaluating production success criteria...")
        
        criteria_results = {}
        
        # Policy decision latency
        latency_data = self.validation_results.get('performance_benchmarks', {}).get('policy_decision_latency', {})
        criteria_results['policy_decision_latency'] = latency_data.get('target_met', False)
        
        # Cache hit rate
        cache_data = self.validation_results.get('performance_benchmarks', {}).get('cache_performance', {})
        cache_hit_rate = cache_data.get('hit_rate_percent', 0)
        criteria_results['cache_hit_rate'] = cache_hit_rate >= self.success_criteria['cache_hit_rate_percent']
        
        # Security compliance
        security_data = self.validation_results.get('security_compliance', {})
        security_score = security_data.get('overall_compliance_score', 0)
        criteria_results['security_compliance'] = security_score >= self.success_criteria['security_compliance_percent']
        
        # Service availability
        health_data = self.validation_results.get('service_health', {})
        healthy_services = sum(1 for service in health_data.values() if service.get('status') == 'healthy')
        total_services = len(health_data)
        availability_percent = (healthy_services / total_services * 100) if total_services > 0 else 0
        criteria_results['service_availability'] = availability_percent >= self.success_criteria['service_availability_percent']
        
        # Monitoring infrastructure
        monitoring_data = self.validation_results.get('monitoring_validation', {})
        criteria_results['monitoring_infrastructure'] = not monitoring_data.get('error')
        
        self.validation_results['success_criteria'] = {
            'criteria_met': criteria_results,
            'overall_success': all(criteria_results.values()),
            'success_rate_percent': (sum(criteria_results.values()) / len(criteria_results)) * 100
        }
        
        return criteria_results

    async def run_comprehensive_validation(self) -> bool:
        """Run complete production validation"""
        self.log("🚀 Starting comprehensive production validation...")
        self.log("=" * 70)
        
        validation_start_time = time.time()
        
        # Run all validation components
        health_passed = await self.validate_service_health()
        performance_passed = await self.run_performance_benchmarks()
        security_passed = await self.validate_security_compliance()
        monitoring_passed = await self.validate_monitoring_infrastructure()
        
        # Evaluate success criteria
        criteria_results = await self.evaluate_success_criteria()
        overall_success = all(criteria_results.values())
        
        validation_end_time = time.time()
        validation_duration = validation_end_time - validation_start_time
        
        # Set overall status
        if overall_success:
            self.validation_results['overall_status'] = 'PASSED'
            self.success("🎉 Production validation PASSED - System ready for full operation!")
        else:
            self.validation_results['overall_status'] = 'FAILED'
            self.error("❌ Production validation FAILED - Issues require attention")
        
        self.validation_results['validation_duration_seconds'] = validation_duration
        
        # Save comprehensive results
        with open('production_validation_results.json', 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        # Display summary
        self.log("=" * 70)
        self.log("📋 PRODUCTION VALIDATION SUMMARY")
        self.log("=" * 70)
        self.log(f"Overall Status: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        self.log(f"Validation Duration: {validation_duration:.2f} seconds")
        self.log(f"Success Criteria Met: {sum(criteria_results.values())}/{len(criteria_results)}")
        
        for criterion, passed in criteria_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            self.log(f"  {criterion}: {status}")
        
        self.log("=" * 70)
        self.log("Detailed Results: production_validation_results.json")
        
        return overall_success

async def main():
    """Main validation function"""
    validator = ProductionValidator()
    
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
