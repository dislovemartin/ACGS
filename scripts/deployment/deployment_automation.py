#!/usr/bin/env python3
"""
ACGS-PGP Deployment Automation Suite
Automates deployment, validation, and monitoring setup
"""

import subprocess
import sys
import os
import time
import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class DeploymentAutomator:
    def __init__(self):
        self.deployment_status = {}
        self.deployment_issues = []
        
    def run_command(self, command: str, cwd: Optional[str] = None, timeout: int = 300) -> Tuple[bool, str, str]:
        """Run a shell command and return success status, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def check_prerequisites(self) -> bool:
        """Check deployment prerequisites"""
        print("\n🔍 Checking Deployment Prerequisites...")
        
        prerequisites = [
            ("docker", "Docker"),
            ("docker-compose", "Docker Compose"),
            ("python3", "Python 3"),
            ("pip", "Python Package Manager")
        ]
        
        all_good = True
        for command, name in prerequisites:
            success, stdout, stderr = self.run_command(f"{command} --version")
            if success:
                version = stdout.strip().split('\n')[0]
                print(f"✅ {name}: {version}")
                self.deployment_status[f"{command}_available"] = True
            else:
                print(f"❌ {name}: Not available")
                self.deployment_status[f"{command}_available"] = False
                self.deployment_issues.append(f"Missing prerequisite: {name}")
                all_good = False
        
        return all_good
    
    def setup_environment(self) -> bool:
        """Setup deployment environment"""
        print("\n🔧 Setting Up Environment...")
        
        # Create necessary directories
        directories = [
            "logs",
            "data/postgres",
            "data/redis",
            "backups",
            "monitoring"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        
        # Set proper permissions
        success, stdout, stderr = self.run_command("chmod 755 logs data backups monitoring")
        if success:
            print("✅ Set directory permissions")
            self.deployment_status["directories_created"] = True
        else:
            print(f"❌ Failed to set permissions: {stderr}")
            self.deployment_status["directories_created"] = False
            self.deployment_issues.append("Failed to set directory permissions")
            return False
        
        return True
    
    def run_database_migrations(self) -> bool:
        """Run database migrations"""
        print("\n🗄️ Running Database Migrations...")
        
        # Check if Alembic is configured
        if not os.path.exists("alembic.ini"):
            print("❌ Alembic configuration not found")
            self.deployment_issues.append("Alembic not configured")
            return False
        
        # Run migrations
        success, stdout, stderr = self.run_command("alembic upgrade head")
        if success:
            print("✅ Database migrations completed")
            print(f"Migration output: {stdout}")
            self.deployment_status["migrations_completed"] = True
            return True
        else:
            print(f"❌ Database migrations failed: {stderr}")
            self.deployment_status["migrations_completed"] = False
            self.deployment_issues.append(f"Migration failed: {stderr}")
            return False
    
    def build_docker_images(self) -> bool:
        """Build Docker images for all services"""
        print("\n🐳 Building Docker Images...")
        
        services = [
            "auth-service",
            "ac-service", 
            "gs-service",
            "fv-service",
            "integrity-service",
            "pgc-service"
        ]
        
        for service in services:
            print(f"  Building {service}...")
            success, stdout, stderr = self.run_command(
                f"docker-compose build {service}",
                timeout=600  # 10 minutes timeout for builds
            )
            
            if success:
                print(f"✅ {service} built successfully")
                self.deployment_status[f"{service}_built"] = True
            else:
                print(f"❌ {service} build failed: {stderr}")
                self.deployment_status[f"{service}_built"] = False
                self.deployment_issues.append(f"{service} build failed")
                return False
        
        return True
    
    def deploy_services(self) -> bool:
        """Deploy all services using Docker Compose"""
        print("\n🚀 Deploying Services...")
        
        # Start infrastructure services first
        print("  Starting infrastructure services...")
        success, stdout, stderr = self.run_command("docker-compose up -d postgres redis nginx")
        if not success:
            print(f"❌ Infrastructure deployment failed: {stderr}")
            self.deployment_issues.append("Infrastructure deployment failed")
            return False
        
        # Wait for infrastructure to be ready
        print("  Waiting for infrastructure to be ready...")
        time.sleep(30)
        
        # Start application services
        print("  Starting application services...")
        success, stdout, stderr = self.run_command("docker-compose up -d")
        if success:
            print("✅ All services deployed")
            self.deployment_status["services_deployed"] = True
            
            # Wait for services to start
            print("  Waiting for services to start...")
            time.sleep(60)
            return True
        else:
            print(f"❌ Service deployment failed: {stderr}")
            self.deployment_status["services_deployed"] = False
            self.deployment_issues.append("Service deployment failed")
            return False
    
    def validate_deployment(self) -> bool:
        """Validate that all services are running correctly"""
        print("\n✅ Validating Deployment...")
        
        # Check container status
        success, stdout, stderr = self.run_command("docker-compose ps")
        if success:
            print("Container status:")
            print(stdout)
            
            # Check if all services are up
            if "Up" in stdout and "Exit" not in stdout:
                print("✅ All containers are running")
                self.deployment_status["containers_running"] = True
            else:
                print("❌ Some containers are not running properly")
                self.deployment_status["containers_running"] = False
                self.deployment_issues.append("Container health issues")
                return False
        else:
            print(f"❌ Failed to check container status: {stderr}")
            return False
        
        # Test service endpoints
        print("  Testing service endpoints...")
        test_endpoints = [
            "http://localhost:8000/auth/",
            "http://localhost:8000/ac/",
            "http://localhost:8000/gs/",
            "http://localhost:8000/fv/",
            "http://localhost:8000/integrity/",
            "http://localhost:8000/pgc/"
        ]
        
        for endpoint in test_endpoints:
            success, stdout, stderr = self.run_command(f"curl -s -o /dev/null -w '%{{http_code}}' {endpoint}")
            if success and stdout.strip() in ["200", "404"]:  # 404 is acceptable for root endpoints
                service_name = endpoint.split('/')[-2]
                print(f"✅ {service_name} service is accessible")
                self.deployment_status[f"{service_name}_accessible"] = True
            else:
                service_name = endpoint.split('/')[-2]
                print(f"❌ {service_name} service is not accessible")
                self.deployment_status[f"{service_name}_accessible"] = False
                self.deployment_issues.append(f"{service_name} service not accessible")
        
        return len(self.deployment_issues) == 0
    
    def setup_monitoring(self) -> bool:
        """Setup monitoring and logging"""
        print("\n📊 Setting Up Monitoring...")
        
        # Create monitoring configuration
        monitoring_config = {
            "version": "3.8",
            "services": {
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "ports": ["9090:9090"],
                    "volumes": ["./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"]
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "ports": ["3000:3000"],
                    "environment": {
                        "GF_SECURITY_ADMIN_PASSWORD": "admin"
                    }
                }
            }
        }
        
        # Save monitoring configuration
        with open("monitoring/docker-compose.monitoring.yml", "w") as f:
            yaml.dump(monitoring_config, f, default_flow_style=False)
        
        # Create basic Prometheus configuration
        prometheus_config = {
            "global": {
                "scrape_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "acgs-services",
                    "static_configs": [
                        {
                            "targets": [
                                "localhost:8001",
                                "localhost:8002", 
                                "localhost:8003",
                                "localhost:8004",
                                "localhost:8005",
                                "localhost:8006"
                            ]
                        }
                    ]
                }
            ]
        }
        
        with open("monitoring/prometheus.yml", "w") as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        print("✅ Monitoring configuration created")
        self.deployment_status["monitoring_configured"] = True
        return True
    
    def create_backup_scripts(self) -> bool:
        """Create backup and recovery scripts"""
        print("\n💾 Creating Backup Scripts...")
        
        backup_script = """#!/bin/bash
# ACGS-PGP Backup Script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$DATE"

echo "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup database
echo "Backing up PostgreSQL database..."
docker exec acgs_postgres pg_dump -U acgs_user acgs_pgp_db > "$BACKUP_DIR/database_backup.sql"

# Backup configuration files
echo "Backing up configuration files..."
cp .env* "$BACKUP_DIR/" 2>/dev/null || true
cp docker-compose.yml "$BACKUP_DIR/"
cp -r alembic/ "$BACKUP_DIR/"

# Backup logs
echo "Backing up logs..."
cp -r logs/ "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
"""
        
        with open("backup.sh", "w") as f:
            f.write(backup_script)
        
        # Make backup script executable
        success, stdout, stderr = self.run_command("chmod +x backup.sh")
        if success:
            print("✅ Backup script created")
            self.deployment_status["backup_script_created"] = True
            return True
        else:
            print(f"❌ Failed to create backup script: {stderr}")
            return False
    
    def run_deployment(self) -> bool:
        """Run complete deployment process"""
        print("🚀 ACGS-PGP Deployment Automation Suite")
        print("=" * 60)
        print(f"Deployment started at: {datetime.now().isoformat()}")
        
        deployment_steps = [
            ("Prerequisites Check", self.check_prerequisites),
            ("Environment Setup", self.setup_environment),
            ("Database Migrations", self.run_database_migrations),
            ("Docker Image Build", self.build_docker_images),
            ("Service Deployment", self.deploy_services),
            ("Deployment Validation", self.validate_deployment),
            ("Monitoring Setup", self.setup_monitoring),
            ("Backup Scripts", self.create_backup_scripts)
        ]
        
        for step_name, step_function in deployment_steps:
            print(f"\n{'='*20} {step_name} {'='*20}")
            success = step_function()
            
            if not success:
                print(f"\n❌ Deployment failed at step: {step_name}")
                self.print_deployment_summary()
                return False
        
        print(f"\n✅ Deployment completed successfully!")
        self.print_deployment_summary()
        return True
    
    def print_deployment_summary(self):
        """Print deployment summary"""
        print("\n" + "=" * 60)
        print("DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        if self.deployment_issues:
            print("⚠️ Issues encountered:")
            for issue in self.deployment_issues:
                print(f"  - {issue}")
        else:
            print("✅ No issues encountered!")
        
        print("\n📋 Next Steps:")
        print("1. Run integration tests: python scripts/tests/test_service_integration.py")
        print("2. Run feature tests: python scripts/tests/test_comprehensive_features.py")
        print("3. Run performance analysis: python scripts/performance_optimization.py")
        print("4. Run security assessment: python scripts/security_hardening.py")
        print("5. Access services at: http://localhost:8000")
        print("6. Monitor with Grafana: http://localhost:3000 (admin/admin)")
        
        # Save deployment status
        deployment_report = {
            "timestamp": datetime.now().isoformat(),
            "status": self.deployment_status,
            "issues": self.deployment_issues
        }
        
        with open("deployment_report.json", "w") as f:
            json.dump(deployment_report, f, indent=2)
        
        print(f"\n📊 Deployment report saved to: deployment_report.json")

def main():
    """Main deployment function"""
    automator = DeploymentAutomator()
    success = automator.run_deployment()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
