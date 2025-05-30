#!/usr/bin/env python3
"""
Complete Production Setup for ACGS-PGP
Master script that orchestrates all production setup components
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime

class ProductionSetupOrchestrator:
    def __init__(self):
        self.setup_steps = [
            ("Authentication Setup", "setup_production_auth.py"),
            ("Test Data Loading", "load_test_data.py"),
            ("Database Configuration", "configure_production_database.py"),
            ("Monitoring & Alerting", "setup_monitoring_alerting.py"),
            ("Backup & Disaster Recovery", "setup_backup_disaster_recovery.py")
        ]
        
        self.results = {}
    
    def print_banner(self):
        """Print setup banner"""
        print("=" * 80)
        print("🚀 ACGS-PGP COMPLETE PRODUCTION SETUP")
        print("=" * 80)
        print("AI Compliance Governance System - Policy Generation Platform")
        print("Production-Ready Deployment Configuration")
        print(f"Setup initiated: {datetime.now().isoformat()}")
        print("=" * 80)
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites"""
        print("\n🔍 Checking Prerequisites...")
        
        prerequisites = [
            ("Docker", "docker --version"),
            ("Docker Compose", "docker-compose --version"),
            ("Python 3", "python3 --version"),
            ("PostgreSQL Client", "psql --version"),
            ("curl", "curl --version")
        ]
        
        all_good = True
        for name, command in prerequisites:
            try:
                result = subprocess.run(command.split(), capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.split('\n')[0]
                    print(f"  ✅ {name}: {version}")
                else:
                    print(f"  ❌ {name}: Not found")
                    all_good = False
            except Exception as e:
                print(f"  ❌ {name}: Error - {str(e)}")
                all_good = False
        
        return all_good
    
    def check_services_running(self) -> bool:
        """Check if ACGS-PGP services are running"""
        print("\n🔍 Checking ACGS-PGP Services...")
        
        try:
            result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True, timeout=10)
            if "Up" in result.stdout:
                print("  ✅ ACGS-PGP services are running")
                return True
            else:
                print("  ⚠️  ACGS-PGP services not running - starting them...")
                subprocess.run(["docker-compose", "up", "-d"], timeout=60)
                return True
        except Exception as e:
            print(f"  ❌ Error checking services: {str(e)}")
            return False
    
    async def run_setup_step(self, step_name: str, script_name: str) -> bool:
        """Run individual setup step"""
        print(f"\n{'='*20} {step_name.upper()} {'='*20}")
        
        try:
            # Run the setup script
            process = await asyncio.create_subprocess_exec(
                "python3", script_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(stdout.decode())
                print(f"✅ {step_name} completed successfully")
                self.results[step_name] = "SUCCESS"
                return True
            else:
                print(f"❌ {step_name} failed:")
                print(stderr.decode())
                self.results[step_name] = "FAILED"
                return False
                
        except Exception as e:
            print(f"❌ Error running {step_name}: {str(e)}")
            self.results[step_name] = "ERROR"
            return False
    
    def create_production_checklist(self):
        """Create production deployment checklist"""
        print("\n📋 Creating Production Deployment Checklist...")
        
        checklist = f"""# ACGS-PGP Production Deployment Checklist

## Pre-Deployment
- [ ] All setup scripts executed successfully
- [ ] Authentication tokens generated and tested
- [ ] Test data loaded and validated
- [ ] Database migrations applied
- [ ] Monitoring stack deployed
- [ ] Backup procedures tested

## Security Configuration
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Database access restricted
- [ ] API rate limiting enabled
- [ ] Audit logging configured

## Performance Optimization
- [ ] Database performance tuning applied
- [ ] Connection pooling configured
- [ ] Caching mechanisms enabled
- [ ] Load balancing configured
- [ ] Resource limits set

## Monitoring & Alerting
- [ ] Prometheus metrics collection
- [ ] Grafana dashboards imported
- [ ] Alert rules configured
- [ ] Notification channels tested
- [ ] Health checks automated

## Backup & Recovery
- [ ] Automated backups scheduled
- [ ] Backup integrity verified
- [ ] Restore procedures tested
- [ ] Disaster recovery plan documented
- [ ] Recovery time objectives met

## Testing & Validation
- [ ] End-to-end testing completed
- [ ] Performance testing passed
- [ ] Security testing conducted
- [ ] User acceptance testing done
- [ ] Documentation updated

## Go-Live
- [ ] DNS records updated
- [ ] Load balancer configured
- [ ] Monitoring alerts enabled
- [ ] Support team notified
- [ ] Rollback plan ready

Generated: {datetime.now().isoformat()}
"""
        
        with open("production_deployment_checklist.md", "w") as f:
            f.write(checklist)
        
        print("  ✅ Production checklist created: production_deployment_checklist.md")
    
    def create_quick_start_guide(self):
        """Create quick start guide for production"""
        print("\n📖 Creating Quick Start Guide...")
        
        guide = """# ACGS-PGP Production Quick Start Guide

## 1. Start All Services
```bash
# Start main services
docker-compose up -d

# Start monitoring stack
./start_monitoring.sh
```

## 2. Load Authentication Tokens
```bash
# Source authentication tokens
source auth_tokens.env

# Test authentication
./test_rbac.sh
```

## 3. Run Comprehensive Tests
```bash
# Test all workflows
./test_comprehensive_workflow.sh

# Check system health
./health_check.sh
```

## 4. Monitor System
- **Grafana Dashboard**: http://localhost:3001 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090
- **Service Health**: ./health_check.sh

## 5. Backup Operations
```bash
# Create backup
./backup_database_comprehensive.sh

# Monitor backups
./monitor_backups.sh

# Test restore (if needed)
./restore_database.sh <backup_file>
```

## 6. Emergency Procedures
- **Service Issues**: Check `disaster_recovery_playbook.md`
- **Database Problems**: Run `./restore_database.sh`
- **Security Incidents**: Follow incident response procedures

## Key URLs
- AC Service: http://localhost:8001
- GS Service: http://localhost:8004
- FV Service: http://localhost:8003
- Integrity Service: http://localhost:8002
- PGC Service: http://localhost:8005
- Monitoring: http://localhost:3001

## Support
- Documentation: `backup_strategy.md`, `disaster_recovery_playbook.md`
- Health Checks: `./health_check.sh`
- Logs: `docker-compose logs <service>`
"""
        
        with open("production_quick_start.md", "w") as f:
            f.write(guide)
        
        print("  ✅ Quick start guide created: production_quick_start.md")
    
    def print_final_summary(self):
        """Print final setup summary"""
        print("\n" + "=" * 80)
        print("📊 PRODUCTION SETUP SUMMARY")
        print("=" * 80)
        
        success_count = 0
        total_count = len(self.setup_steps)
        
        for step_name, _ in self.setup_steps:
            status = self.results.get(step_name, "NOT RUN")
            if status == "SUCCESS":
                print(f"✅ {step_name}: {status}")
                success_count += 1
            elif status == "FAILED":
                print(f"❌ {step_name}: {status}")
            else:
                print(f"⚠️  {step_name}: {status}")
        
        print(f"\n📈 Success Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            print("\n🎉 PRODUCTION SETUP COMPLETE!")
            print("✅ All components configured successfully")
            print("🚀 ACGS-PGP is ready for production deployment")
        elif success_count >= total_count * 0.8:
            print("\n✅ PRODUCTION SETUP MOSTLY COMPLETE")
            print("⚠️  Some components need attention")
            print("📋 Review failed steps and retry if needed")
        else:
            print("\n⚠️  PRODUCTION SETUP NEEDS ATTENTION")
            print("❌ Multiple components failed")
            print("🔧 Review errors and fix issues before deployment")
        
        print("\n📁 Generated Files:")
        files = [
            "auth_tokens.json", "auth_tokens.env", "test_rbac.sh",
            "test_comprehensive_workflow.sh", ".env.production",
            "monitor_database.sh", "backup_database_comprehensive.sh",
            "prometheus.yml", "acgs_pgp_dashboard.json", "health_check.sh",
            "backup_strategy.md", "disaster_recovery_playbook.md",
            "production_deployment_checklist.md", "production_quick_start.md"
        ]
        
        for file in files:
            if os.path.exists(file):
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file} (missing)")
        
        print("\n🎯 Next Steps:")
        print("1. Review production_deployment_checklist.md")
        print("2. Follow production_quick_start.md")
        print("3. Test all components thoroughly")
        print("4. Configure SSL/TLS for production")
        print("5. Set up external monitoring")
    
    async def run_complete_setup(self):
        """Run complete production setup"""
        self.print_banner()
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites not met. Please install missing components.")
            return False
        
        # Check services
        if not self.check_services_running():
            print("❌ Cannot start ACGS-PGP services. Please check Docker setup.")
            return False
        
        # Run setup steps
        print(f"\n🚀 Running {len(self.setup_steps)} setup steps...")
        
        for step_name, script_name in self.setup_steps:
            success = await self.run_setup_step(step_name, script_name)
            if not success:
                print(f"⚠️  {step_name} failed, but continuing with other steps...")
        
        # Create additional documentation
        self.create_production_checklist()
        self.create_quick_start_guide()
        
        # Print final summary
        self.print_final_summary()
        
        return True

async def main():
    orchestrator = ProductionSetupOrchestrator()
    await orchestrator.run_complete_setup()

if __name__ == "__main__":
    asyncio.run(main())
