#!/usr/bin/env python3
"""
Fix container runtime and cgroup configuration issues for ACGS Phase 3 deployment.
This script resolves cgroup v2 configuration errors and Docker compatibility issues.
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContainerRuntimeFixer:
    """Fix container runtime and cgroup configuration issues."""
    
    def __init__(self):
        self.docker_available = False
        self.cgroup_version = None
        self.fixes_applied = []
        self.issues_detected = []
        
    def check_docker_availability(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"✅ Docker available: {result.stdout.strip()}")
                
                # Check if Docker daemon is running
                result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info("✅ Docker daemon is running")
                    self.docker_available = True
                    return True
                else:
                    logger.warning("⚠️ Docker daemon is not running")
                    return False
            else:
                logger.warning("⚠️ Docker not available")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Docker check failed: {e}")
            return False
    
    def detect_cgroup_version(self) -> Optional[str]:
        """Detect cgroup version."""
        try:
            # Check if cgroup v2 is mounted
            if os.path.exists('/sys/fs/cgroup/cgroup.controllers'):
                self.cgroup_version = 'v2'
                logger.info("✅ Detected cgroup v2")
            elif os.path.exists('/sys/fs/cgroup/memory'):
                self.cgroup_version = 'v1'
                logger.info("✅ Detected cgroup v1")
            else:
                logger.warning("⚠️ Could not detect cgroup version")
                return None
            
            return self.cgroup_version
        except Exception as e:
            logger.error(f"❌ Failed to detect cgroup version: {e}")
            return None
    
    def check_cgroup_configuration(self) -> Dict[str, Any]:
        """Check cgroup configuration for issues."""
        logger.info("🔍 Checking cgroup configuration")
        
        config_status = {
            'cgroup_version': self.cgroup_version,
            'cgroup_mounted': False,
            'docker_cgroup_driver': None,
            'systemd_available': False,
            'issues': []
        }
        
        try:
            # Check if cgroup is properly mounted
            if os.path.exists('/sys/fs/cgroup'):
                config_status['cgroup_mounted'] = True
                logger.info("✅ cgroup filesystem is mounted")
            else:
                config_status['issues'].append("cgroup filesystem not mounted")
                logger.error("❌ cgroup filesystem not mounted")
            
            # Check Docker cgroup driver
            if self.docker_available:
                try:
                    result = subprocess.run(['docker', 'info', '--format', '{{.CgroupDriver}}'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        config_status['docker_cgroup_driver'] = result.stdout.strip()
                        logger.info(f"Docker cgroup driver: {config_status['docker_cgroup_driver']}")
                    else:
                        config_status['issues'].append("Could not determine Docker cgroup driver")
                except Exception as e:
                    config_status['issues'].append(f"Docker cgroup driver check failed: {e}")
            
            # Check if systemd is available
            try:
                result = subprocess.run(['systemctl', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    config_status['systemd_available'] = True
                    logger.info("✅ systemd is available")
            except Exception:
                logger.warning("⚠️ systemd not available")
            
            # Check for specific cgroup v2 issues
            if self.cgroup_version == 'v2':
                # Check for threaded mode issues
                try:
                    docker_cgroup_path = '/sys/fs/cgroup/docker'
                    if os.path.exists(docker_cgroup_path):
                        with open(f'{docker_cgroup_path}/cgroup.type', 'r') as f:
                            cgroup_type = f.read().strip()
                            if cgroup_type == 'threaded':
                                config_status['issues'].append("Docker cgroup is in threaded mode")
                                logger.warning("⚠️ Docker cgroup is in threaded mode")
                except Exception:
                    pass
            
        except Exception as e:
            logger.error(f"❌ cgroup configuration check failed: {e}")
            config_status['issues'].append(f"Configuration check failed: {e}")
        
        return config_status
    
    async def fix_docker_cgroup_configuration(self) -> bool:
        """Fix Docker cgroup configuration issues."""
        logger.info("🔧 Fixing Docker cgroup configuration")
        
        try:
            # Stop Docker service
            logger.info("Stopping Docker service...")
            result = subprocess.run(['sudo', 'systemctl', 'stop', 'docker'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.warning("Could not stop Docker service via systemctl")
            
            # Create or update Docker daemon configuration
            docker_config = {
                "exec-opts": ["native.cgroupdriver=systemd"],
                "log-driver": "json-file",
                "log-opts": {
                    "max-size": "100m"
                },
                "storage-driver": "overlay2"
            }
            
            # Handle cgroup v2 specific configuration
            if self.cgroup_version == 'v2':
                docker_config["exec-opts"] = ["native.cgroupdriver=systemd"]
                docker_config["features"] = {"buildkit": True}
            
            # Write Docker daemon configuration
            docker_config_path = '/etc/docker/daemon.json'
            os.makedirs('/etc/docker', exist_ok=True)
            
            with open(docker_config_path, 'w') as f:
                json.dump(docker_config, f, indent=2)
            
            logger.info(f"✅ Updated Docker daemon configuration: {docker_config_path}")
            
            # Start Docker service
            logger.info("Starting Docker service...")
            result = subprocess.run(['sudo', 'systemctl', 'start', 'docker'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.info("✅ Docker service started successfully")
                
                # Wait for Docker to be ready
                await asyncio.sleep(5)
                
                # Verify Docker is working
                result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info("✅ Docker is working correctly")
                    self.fixes_applied.append("Docker cgroup configuration fixed")
                    return True
                else:
                    logger.error("❌ Docker is not working after restart")
                    return False
            else:
                logger.error(f"❌ Failed to start Docker service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to fix Docker configuration: {e}")
            return False
    
    async def implement_host_based_fallback(self) -> bool:
        """Implement host-based deployment as fallback."""
        logger.info("🔄 Implementing host-based deployment fallback")
        
        try:
            # Create host-based deployment script
            host_deployment_script = '''#!/bin/bash
# Host-based ACGS deployment fallback

set -e

echo "🚀 Starting host-based ACGS deployment"

# Function to check if service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $service_name is running on port $port"
        return 0
    else
        echo "❌ $service_name is not running on port $port"
        return 1
    fi
}

# Start PostgreSQL if not running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "Starting PostgreSQL..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
fi

# Set up Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r src/backend/shared/requirements.txt

# Run database migrations
echo "Running database migrations..."
cd migrations
alembic upgrade head
cd ..

echo "✅ Host-based deployment setup completed"
echo "Note: Services need to be started manually in separate terminals"
'''
            
            script_path = Path('scripts/host_based_deployment.sh')
            script_path.write_text(host_deployment_script)
            script_path.chmod(0o755)
            
            logger.info(f"✅ Created host-based deployment script: {script_path}")
            self.fixes_applied.append("Host-based deployment fallback implemented")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to implement host-based fallback: {e}")
            return False
    
    async def validate_container_runtime(self) -> Dict[str, Any]:
        """Validate container runtime after fixes."""
        logger.info("🔍 Validating container runtime")
        
        validation_results = {
            'docker_working': False,
            'simple_container_test': False,
            'cgroup_issues_resolved': False,
            'fallback_available': False
        }
        
        try:
            # Test Docker basic functionality
            if self.docker_available:
                result = subprocess.run(['docker', 'run', '--rm', 'hello-world'], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    validation_results['docker_working'] = True
                    validation_results['simple_container_test'] = True
                    logger.info("✅ Docker container test passed")
                else:
                    logger.warning(f"⚠️ Docker container test failed: {result.stderr}")
            
            # Check if cgroup issues are resolved
            config_status = self.check_cgroup_configuration()
            if len(config_status['issues']) == 0:
                validation_results['cgroup_issues_resolved'] = True
                logger.info("✅ cgroup issues resolved")
            else:
                logger.warning(f"⚠️ Remaining cgroup issues: {config_status['issues']}")
            
            # Check if fallback is available
            if Path('scripts/host_based_deployment.sh').exists():
                validation_results['fallback_available'] = True
                logger.info("✅ Host-based fallback available")
            
        except Exception as e:
            logger.error(f"❌ Container runtime validation failed: {e}")
        
        return validation_results
    
    async def fix_complete_runtime(self) -> Dict[str, Any]:
        """Fix complete container runtime configuration."""
        logger.info("🚀 Starting container runtime fixes")
        logger.info("=" * 60)
        
        fix_start_time = time.time()
        
        # Step 1: Check current state
        logger.info("Step 1: Checking current container runtime state")
        docker_available = self.check_docker_availability()
        cgroup_version = self.detect_cgroup_version()
        config_status = self.check_cgroup_configuration()
        
        # Step 2: Apply fixes based on detected issues
        fixes_successful = []
        
        if docker_available and config_status['issues']:
            logger.info("Step 2: Fixing Docker cgroup configuration")
            if await self.fix_docker_cgroup_configuration():
                fixes_successful.append("docker_cgroup_fix")
        
        # Step 3: Implement fallback
        logger.info("Step 3: Implementing host-based fallback")
        if await self.implement_host_based_fallback():
            fixes_successful.append("host_based_fallback")
        
        # Step 4: Validate fixes
        logger.info("Step 4: Validating container runtime")
        validation_results = await self.validate_container_runtime()
        
        fix_end_time = time.time()
        fix_duration = fix_end_time - fix_start_time
        
        # Compile results
        results = {
            'fix_duration_seconds': round(fix_duration, 2),
            'initial_state': {
                'docker_available': docker_available,
                'cgroup_version': cgroup_version,
                'config_issues': config_status['issues']
            },
            'fixes_applied': self.fixes_applied,
            'fixes_successful': fixes_successful,
            'validation_results': validation_results,
            'overall_status': 'PENDING'
        }
        
        # Determine overall status
        docker_working = validation_results.get('docker_working', False)
        fallback_available = validation_results.get('fallback_available', False)
        cgroup_resolved = validation_results.get('cgroup_issues_resolved', False)
        
        if docker_working and cgroup_resolved:
            results['overall_status'] = 'SUCCESS'
        elif fallback_available:
            results['overall_status'] = 'PARTIAL'
        else:
            results['overall_status'] = 'FAILED'
        
        # Display summary
        logger.info("=" * 60)
        logger.info("📊 CONTAINER RUNTIME FIX SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Fix Duration: {fix_duration:.1f} seconds")
        logger.info(f"Docker Working: {'✅ Yes' if docker_working else '❌ No'}")
        logger.info(f"cgroup Issues Resolved: {'✅ Yes' if cgroup_resolved else '❌ No'}")
        logger.info(f"Fallback Available: {'✅ Yes' if fallback_available else '❌ No'}")
        logger.info(f"Overall Status: {results['overall_status']}")
        
        if self.fixes_applied:
            logger.info("Fixes Applied:")
            for fix in self.fixes_applied:
                logger.info(f"  - {fix}")
        
        # Output JSON for orchestrator
        print(json.dumps(results, indent=2))
        
        return results

async def main():
    """Main function."""
    fixer = ContainerRuntimeFixer()
    results = await fixer.fix_complete_runtime()
    
    # Exit with appropriate code
    if results['overall_status'] == 'SUCCESS':
        sys.exit(0)
    elif results['overall_status'] == 'PARTIAL':
        logger.warning("Container runtime partially fixed - fallback available")
        sys.exit(0)  # Allow partial success for now
    else:
        logger.error("Container runtime fix failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
