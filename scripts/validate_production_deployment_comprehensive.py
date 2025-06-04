#!/usr/bin/env python3
"""
ACGS-PGP Production Deployment Validation Script

This script validates that all production deployment components are properly configured
and meet the requirements for 99.9% uptime, <200ms response times, and 100+ concurrent users.
"""

import asyncio
import json
import subprocess
import time
import sys
from typing import Dict, List, Tuple, Any
import aiohttp
import yaml

class ProductionValidator:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "UNKNOWN",
            "checks": {},
            "sla_compliance": {},
            "performance_metrics": {},
            "security_status": {},
            "recommendations": []
        }
        
    async def validate_all(self) -> Dict[str, Any]:
        """Run all production validation checks"""
        print("🚀 Starting ACGS-PGP Production Deployment Validation")
        print("=" * 60)
        
        # Infrastructure checks
        await self.check_kubernetes_cluster()
        await self.check_ingress_configuration()
        await self.check_ssl_certificates()
        await self.check_monitoring_stack()
        await self.check_backup_system()
        
        # Service health checks
        await self.check_service_health()
        await self.check_database_connectivity()
        await self.check_cross_service_communication()
        
        # Performance validation
        await self.check_response_times()
        await self.check_auto_scaling()
        await self.check_load_balancing()
        
        # Security validation
        await self.check_network_policies()
        await self.check_rbac_configuration()
        await self.check_pod_security()
        
        # SLA compliance
        await self.check_sla_compliance()
        
        # Generate final report
        self.generate_final_report()
        return self.results
    
    async def check_kubernetes_cluster(self):
        """Validate Kubernetes cluster configuration"""
        print("🔍 Checking Kubernetes cluster...")
        
        try:
            # Check cluster info
            result = subprocess.run(
                ["kubectl", "cluster-info"], 
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                self.results["checks"]["kubernetes_cluster"] = {
                    "status": "PASS",
                    "message": "Kubernetes cluster is accessible"
                }
            else:
                self.results["checks"]["kubernetes_cluster"] = {
                    "status": "FAIL",
                    "message": f"Cluster access failed: {result.stderr}"
                }
                
            # Check node status
            result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "json"], 
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                nodes = json.loads(result.stdout)
                ready_nodes = sum(1 for node in nodes["items"] 
                                if any(condition["type"] == "Ready" and condition["status"] == "True" 
                                      for condition in node["status"]["conditions"]))
                
                self.results["checks"]["node_status"] = {
                    "status": "PASS" if ready_nodes >= 3 else "WARN",
                    "message": f"{ready_nodes} nodes ready",
                    "ready_nodes": ready_nodes
                }
                
        except Exception as e:
            self.results["checks"]["kubernetes_cluster"] = {
                "status": "FAIL",
                "message": f"Error checking cluster: {str(e)}"
            }
    
    async def check_service_health(self):
        """Check health of all ACGS-PGP services"""
        print("🏥 Checking service health...")
        
        services = [
            ("auth-service", 8000),
            ("ac-service", 8001),
            ("integrity-service", 8002),
            ("fv-service", 8003),
            ("gs-service", 8004),
            ("pgc-service", 8005),
            ("ec-service", 8006)
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            for service_name, port in services:
                try:
                    # Try internal cluster communication first
                    url = f"http://{service_name}.acgs-pgp.svc.cluster.local:{port}/health"
                    async with session.get(url) as response:
                        if response.status == 200:
                            self.results["checks"][f"{service_name}_health"] = {
                                "status": "PASS",
                                "message": "Service healthy",
                                "response_time": response.headers.get("X-Response-Time", "N/A")
                            }
                        else:
                            self.results["checks"][f"{service_name}_health"] = {
                                "status": "FAIL",
                                "message": f"Health check failed: HTTP {response.status}"
                            }
                            
                except Exception as e:
                    self.results["checks"][f"{service_name}_health"] = {
                        "status": "FAIL",
                        "message": f"Health check error: {str(e)}"
                    }
    
    async def check_response_times(self):
        """Validate API response times meet SLA (<200ms)"""
        print("⏱️  Checking response times...")
        
        endpoints = [
            "https://api.acgs-pgp.com/api/v1/auth/health",
            "https://api.acgs-pgp.com/api/v1/ac/health",
            "https://api.acgs-pgp.com/api/v1/integrity/health",
            "https://api.acgs-pgp.com/api/v1/fv/health",
            "https://api.acgs-pgp.com/api/v1/gs/health",
            "https://api.acgs-pgp.com/api/v1/pgc/health"
        ]
        
        response_times = []
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # Convert to ms
                        response_times.append(response_time)
                        
                        service_name = endpoint.split("/")[-2]  # Extract service name
                        self.results["performance_metrics"][f"{service_name}_response_time"] = {
                            "value": response_time,
                            "unit": "ms",
                            "sla_target": 200,
                            "status": "PASS" if response_time < 200 else "FAIL"
                        }
                        
                except Exception as e:
                    service_name = endpoint.split("/")[-2]
                    self.results["performance_metrics"][f"{service_name}_response_time"] = {
                        "value": None,
                        "unit": "ms",
                        "sla_target": 200,
                        "status": "FAIL",
                        "error": str(e)
                    }
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            self.results["performance_metrics"]["average_response_time"] = {
                "value": avg_response_time,
                "unit": "ms",
                "sla_target": 200,
                "status": "PASS" if avg_response_time < 200 else "FAIL"
            }
    
    async def check_auto_scaling(self):
        """Validate auto-scaling configuration"""
        print("📈 Checking auto-scaling configuration...")
        
        try:
            result = subprocess.run(
                ["kubectl", "get", "hpa", "-n", "acgs-pgp", "-o", "json"], 
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                hpas = json.loads(result.stdout)
                
                for hpa in hpas["items"]:
                    name = hpa["metadata"]["name"]
                    min_replicas = hpa["spec"]["minReplicas"]
                    max_replicas = hpa["spec"]["maxReplicas"]
                    
                    # Check if configuration supports 100+ concurrent users
                    capacity_check = max_replicas >= 10 and min_replicas >= 2
                    
                    self.results["checks"][f"{name}_autoscaling"] = {
                        "status": "PASS" if capacity_check else "WARN",
                        "message": f"Min: {min_replicas}, Max: {max_replicas}",
                        "min_replicas": min_replicas,
                        "max_replicas": max_replicas
                    }
                    
        except Exception as e:
            self.results["checks"]["autoscaling"] = {
                "status": "FAIL",
                "message": f"Error checking HPA: {str(e)}"
            }
    
    async def check_monitoring_stack(self):
        """Validate monitoring and alerting"""
        print("📊 Checking monitoring stack...")
        
        try:
            # Check Prometheus
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "acgs-pgp", "-l", "app=prometheus", "-o", "json"], 
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                pods = json.loads(result.stdout)
                running_pods = sum(1 for pod in pods["items"] 
                                 if pod["status"]["phase"] == "Running")
                
                self.results["checks"]["prometheus"] = {
                    "status": "PASS" if running_pods > 0 else "FAIL",
                    "message": f"{running_pods} Prometheus pods running"
                }
            
            # Check Grafana
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "acgs-pgp", "-l", "app=grafana", "-o", "json"], 
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                pods = json.loads(result.stdout)
                running_pods = sum(1 for pod in pods["items"] 
                                 if pod["status"]["phase"] == "Running")
                
                self.results["checks"]["grafana"] = {
                    "status": "PASS" if running_pods > 0 else "FAIL",
                    "message": f"{running_pods} Grafana pods running"
                }
                
        except Exception as e:
            self.results["checks"]["monitoring"] = {
                "status": "FAIL",
                "message": f"Error checking monitoring: {str(e)}"
            }
    
    async def check_sla_compliance(self):
        """Check overall SLA compliance"""
        print("📋 Checking SLA compliance...")
        
        # Calculate uptime from service health checks
        healthy_services = sum(1 for check in self.results["checks"].values() 
                             if check.get("status") == "PASS" and "health" in str(check))
        total_services = sum(1 for check in self.results["checks"].keys() 
                           if "health" in check)
        
        if total_services > 0:
            uptime_percentage = (healthy_services / total_services) * 100
            self.results["sla_compliance"]["uptime"] = {
                "current": uptime_percentage,
                "target": 99.9,
                "status": "PASS" if uptime_percentage >= 99.9 else "FAIL"
            }
        
        # Calculate average response time compliance
        response_times = [metric["value"] for metric in self.results["performance_metrics"].values() 
                         if metric.get("value") is not None and "response_time" in str(metric)]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            self.results["sla_compliance"]["response_time"] = {
                "current": avg_response_time,
                "target": 200,
                "status": "PASS" if avg_response_time < 200 else "FAIL"
            }
    
    def generate_final_report(self):
        """Generate final validation report"""
        print("\n" + "=" * 60)
        print("📊 PRODUCTION DEPLOYMENT VALIDATION REPORT")
        print("=" * 60)
        
        # Calculate overall status
        failed_checks = sum(1 for check in self.results["checks"].values() 
                          if check.get("status") == "FAIL")
        warning_checks = sum(1 for check in self.results["checks"].values() 
                           if check.get("status") == "WARN")
        
        if failed_checks == 0 and warning_checks == 0:
            self.results["overall_status"] = "PASS"
            print("✅ Overall Status: PASS - Production Ready")
        elif failed_checks == 0:
            self.results["overall_status"] = "WARN"
            print("⚠️  Overall Status: WARN - Minor Issues Detected")
        else:
            self.results["overall_status"] = "FAIL"
            print("❌ Overall Status: FAIL - Critical Issues Found")
        
        # Print summary
        print(f"\n📈 Summary:")
        print(f"   Total Checks: {len(self.results['checks'])}")
        print(f"   Passed: {len(self.results['checks']) - failed_checks - warning_checks}")
        print(f"   Warnings: {warning_checks}")
        print(f"   Failed: {failed_checks}")
        
        # Print SLA compliance
        if self.results["sla_compliance"]:
            print(f"\n🎯 SLA Compliance:")
            for metric, data in self.results["sla_compliance"].items():
                status_icon = "✅" if data["status"] == "PASS" else "❌"
                print(f"   {status_icon} {metric.title()}: {data['current']:.2f} (Target: {data['target']})")
        
        # Save detailed report
        with open("production_validation_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: production_validation_report.json")

async def main():
    """Main validation function"""
    validator = ProductionValidator()
    results = await validator.validate_all()
    
    # Exit with appropriate code
    if results["overall_status"] == "FAIL":
        sys.exit(1)
    elif results["overall_status"] == "WARN":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
