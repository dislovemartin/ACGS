#!/usr/bin/env python3
"""
Phase 3 Monitoring Validation Script
Validates the monitoring infrastructure and endpoints for ACGS Phase 3 deployment.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class Phase3MonitoringValidator:
    def __init__(self):
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3002"
        self.alertmanager_url = "http://localhost:9093"
        self.results = []
    
    def validate_prometheus(self) -> Dict[str, Any]:
        """Validate Prometheus is running and configured correctly."""
        print("🔍 Validating Prometheus...")
        result = {
            "service": "Prometheus",
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        try:
            # Check Prometheus health
            response = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            if response.status_code == 200:
                result["details"]["health"] = "✅ Healthy"
            else:
                result["issues"].append(f"Health check failed: {response.status_code}")
            
            # Check configuration
            config_response = requests.get(f"{self.prometheus_url}/api/v1/status/config", timeout=5)
            if config_response.status_code == 200:
                result["details"]["config"] = "✅ Configuration loaded"
            else:
                result["issues"].append("Configuration not accessible")
            
            # Check targets
            targets_response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=5)
            if targets_response.status_code == 200:
                targets_data = targets_response.json()
                active_targets = targets_data.get("data", {}).get("activeTargets", [])
                result["details"]["targets"] = f"✅ {len(active_targets)} targets configured"
                
                # Count healthy targets
                healthy_targets = [t for t in active_targets if t.get("health") == "up"]
                result["details"]["healthy_targets"] = f"🔍 {len(healthy_targets)}/{len(active_targets)} targets healthy"
            else:
                result["issues"].append("Targets not accessible")
            
            # Check rules
            rules_response = requests.get(f"{self.prometheus_url}/api/v1/rules", timeout=5)
            if rules_response.status_code == 200:
                rules_data = rules_response.json()
                rule_groups = rules_data.get("data", {}).get("groups", [])
                total_rules = sum(len(group.get("rules", [])) for group in rule_groups)
                result["details"]["alert_rules"] = f"✅ {total_rules} alert rules loaded"
            else:
                result["issues"].append("Alert rules not accessible")
            
            result["status"] = "✅ Operational" if not result["issues"] else "⚠️ Issues detected"
            
        except requests.exceptions.RequestException as e:
            result["status"] = "❌ Not accessible"
            result["issues"].append(f"Connection error: {str(e)}")
        
        return result
    
    def validate_grafana(self) -> Dict[str, Any]:
        """Validate Grafana is running and accessible."""
        print("📊 Validating Grafana...")
        result = {
            "service": "Grafana",
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        try:
            # Check Grafana health
            response = requests.get(f"{self.grafana_url}/api/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                result["details"]["health"] = f"✅ {health_data.get('database', 'unknown')} database"
            else:
                result["issues"].append(f"Health check failed: {response.status_code}")
            
            # Check if login page is accessible
            login_response = requests.get(f"{self.grafana_url}/login", timeout=5)
            if login_response.status_code == 200:
                result["details"]["web_interface"] = "✅ Web interface accessible"
            else:
                result["issues"].append("Web interface not accessible")
            
            result["status"] = "✅ Operational" if not result["issues"] else "⚠️ Issues detected"
            
        except requests.exceptions.RequestException as e:
            result["status"] = "❌ Not accessible"
            result["issues"].append(f"Connection error: {str(e)}")
        
        return result
    
    def validate_alertmanager(self) -> Dict[str, Any]:
        """Validate AlertManager is running and configured."""
        print("🚨 Validating AlertManager...")
        result = {
            "service": "AlertManager",
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        try:
            # Check AlertManager health
            response = requests.get(f"{self.alertmanager_url}/-/healthy", timeout=5)
            if response.status_code == 200:
                result["details"]["health"] = "✅ Healthy"
            else:
                result["issues"].append(f"Health check failed: {response.status_code}")
            
            # Check configuration
            config_response = requests.get(f"{self.alertmanager_url}/api/v1/status", timeout=5)
            if config_response.status_code == 200:
                result["details"]["config"] = "✅ Configuration loaded"
            else:
                result["issues"].append("Configuration not accessible")
            
            # Check receivers
            receivers_response = requests.get(f"{self.alertmanager_url}/api/v1/receivers", timeout=5)
            if receivers_response.status_code == 200:
                receivers_data = receivers_response.json()
                receivers = receivers_data.get("data", [])
                result["details"]["receivers"] = f"✅ {len(receivers)} receivers configured"
            else:
                result["issues"].append("Receivers not accessible")
            
            result["status"] = "✅ Operational" if not result["issues"] else "⚠️ Issues detected"
            
        except requests.exceptions.RequestException as e:
            result["status"] = "❌ Not accessible"
            result["issues"].append(f"Connection error: {str(e)}")
        
        return result
    
    def validate_phase3_configuration(self) -> Dict[str, Any]:
        """Validate Phase 3 specific configuration."""
        print("⚙️ Validating Phase 3 Configuration...")
        result = {
            "service": "Phase 3 Configuration",
            "status": "unknown",
            "details": {},
            "issues": []
        }
        
        try:
            # Check for Phase 3 specific targets in Prometheus
            targets_response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=5)
            if targets_response.status_code == 200:
                targets_data = targets_response.json()
                active_targets = targets_data.get("data", {}).get("activeTargets", [])
                
                # Look for Phase 3 specific jobs
                phase3_jobs = ["acgs-pgp-performance", "acgs-pgp-health"]
                found_jobs = set()
                for target in active_targets:
                    job = target.get("labels", {}).get("job", "")
                    if job in phase3_jobs:
                        found_jobs.add(job)
                
                result["details"]["phase3_jobs"] = f"✅ {len(found_jobs)}/{len(phase3_jobs)} Phase 3 jobs configured"
                if len(found_jobs) < len(phase3_jobs):
                    missing_jobs = set(phase3_jobs) - found_jobs
                    result["issues"].append(f"Missing jobs: {', '.join(missing_jobs)}")
            
            # Check for Phase 3 alert rules
            rules_response = requests.get(f"{self.prometheus_url}/api/v1/rules", timeout=5)
            if rules_response.status_code == 200:
                rules_data = rules_response.json()
                rule_groups = rules_data.get("data", {}).get("groups", [])
                
                phase3_groups = [group for group in rule_groups if "phase3" in group.get("name", "").lower()]
                if phase3_groups:
                    total_phase3_rules = sum(len(group.get("rules", [])) for group in phase3_groups)
                    result["details"]["phase3_rules"] = f"✅ {total_phase3_rules} Phase 3 alert rules loaded"
                else:
                    result["issues"].append("No Phase 3 alert rules found")
            
            result["status"] = "✅ Configured" if not result["issues"] else "⚠️ Partial configuration"
            
        except requests.exceptions.RequestException as e:
            result["status"] = "❌ Validation failed"
            result["issues"].append(f"Validation error: {str(e)}")
        
        return result
    
    def run_validation(self) -> None:
        """Run complete validation suite."""
        print("🚀 Phase 3 Monitoring Validation")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Run all validations
        self.results = [
            self.validate_prometheus(),
            self.validate_grafana(),
            self.validate_alertmanager(),
            self.validate_phase3_configuration()
        ]
        
        # Print results
        print("\n📋 Validation Results")
        print("=" * 50)
        
        for result in self.results:
            print(f"\n{result['service']}: {result['status']}")
            
            for key, value in result["details"].items():
                print(f"  {value}")
            
            if result["issues"]:
                print("  Issues:")
                for issue in result["issues"]:
                    print(f"    ❌ {issue}")
        
        # Summary
        operational_count = sum(1 for r in self.results if "✅" in r["status"])
        total_count = len(self.results)
        
        print(f"\n🎯 Summary")
        print("=" * 50)
        print(f"Operational Services: {operational_count}/{total_count}")
        print(f"Overall Status: {'✅ Ready for Production' if operational_count == total_count else '⚠️ Requires Attention'}")
        
        # Recommendations
        print(f"\n💡 Recommendations")
        print("=" * 50)
        if operational_count == total_count:
            print("✅ All monitoring services operational")
            print("✅ Ready for Phase 3 production deployment")
            print("✅ Proceed with load testing and security validation")
        else:
            print("⚠️ Address identified issues before production deployment")
            print("🔧 Check service configurations and connectivity")
            print("📊 Verify monitoring stack deployment")

if __name__ == "__main__":
    validator = Phase3MonitoringValidator()
    validator.run_validation()
