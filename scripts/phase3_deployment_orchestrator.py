#!/usr/bin/env python3

"""
ACGS Phase 3 Deployment Orchestrator
Coordinates the complete Phase 3 production deployment workflow
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Any
import argparse

class DeploymentOrchestrator:
    def __init__(self, environment: str = "staging"):
        self.environment = environment
        self.deployment_log = {
            'start_time': datetime.now().isoformat(),
            'environment': environment,
            'phase': '3',
            'workflow_status': 'PENDING',
            'steps_completed': [],
            'performance_metrics': {},
            'issues': [],
            'final_status': None
        }
        
        self.workflow_steps = [
            {
                'name': 'staging_deployment',
                'description': 'Deploy to staging environment',
                'script': 'scripts/phase3_staging_deployment.sh',
                'required': True,
                'environment': 'staging'
            },
            {
                'name': 'staging_validation',
                'description': 'Validate staging deployment',
                'script': 'python scripts/phase3_staging_validation.py',
                'required': True,
                'environment': 'staging'
            },
            {
                'name': 'load_testing',
                'description': 'Run comprehensive load testing',
                'script': 'python scripts/phase3_load_testing.py --staging-mode',
                'required': True,
                'environment': 'staging'
            },
            {
                'name': 'security_testing',
                'description': 'Run security penetration testing',
                'script': 'python scripts/phase3_security_penetration_testing.py --staging-mode',
                'required': True,
                'environment': 'staging'
            },
            {
                'name': 'production_infrastructure',
                'description': 'Setup production infrastructure',
                'script': 'sudo scripts/phase3_production_infrastructure.sh',
                'required': True,
                'environment': 'production'
            },
            {
                'name': 'production_rollout',
                'description': 'Execute production rollout',
                'script': 'python scripts/phase3_production_rollout.py',
                'required': True,
                'environment': 'production'
            },
            {
                'name': 'production_validation',
                'description': 'Validate production deployment',
                'script': 'python scripts/phase3_production_validation.py',
                'required': True,
                'environment': 'production'
            }
        ]

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def error(self, message: str):
        """Log error message"""
        self.log(message, "ERROR")
        self.deployment_log['issues'].append({
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
        self.deployment_log['issues'].append({
            'timestamp': datetime.now().isoformat(),
            'level': 'WARNING',
            'message': message
        })

    async def execute_step(self, step: Dict[str, Any]) -> bool:
        """Execute a single deployment step"""
        step_name = step['name']
        description = step['description']
        script = step['script']
        
        self.log(f"🚀 Executing: {description}")
        self.log(f"Command: {script}")
        
        step_start_time = time.time()
        
        try:
            # Execute the script
            result = subprocess.run(
                script.split(),
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            
            step_result = {
                'name': step_name,
                'description': description,
                'script': script,
                'duration_seconds': step_duration,
                'return_code': result.returncode,
                'timestamp': datetime.now().isoformat()
            }
            
            if result.returncode == 0:
                self.success(f"✅ {description} completed successfully ({step_duration:.1f}s)")
                step_result['status'] = 'SUCCESS'
                step_result['stdout'] = result.stdout[-1000:]  # Last 1000 chars
                
                # Try to extract metrics from output
                try:
                    if 'validation' in step_name or 'testing' in step_name:
                        # Look for JSON output in the last few lines
                        lines = result.stdout.strip().split('\n')
                        for line in reversed(lines[-5:]):
                            try:
                                metrics = json.loads(line)
                                step_result['metrics'] = metrics
                                break
                            except json.JSONDecodeError:
                                continue
                except Exception:
                    pass  # Metrics extraction is optional
                
                self.deployment_log['steps_completed'].append(step_result)
                return True
            else:
                self.error(f"❌ {description} failed (exit code: {result.returncode})")
                step_result['status'] = 'FAILED'
                step_result['stderr'] = result.stderr[-1000:]  # Last 1000 chars
                self.deployment_log['steps_completed'].append(step_result)
                return False
                
        except subprocess.TimeoutExpired:
            self.error(f"❌ {description} timed out after 30 minutes")
            step_result = {
                'name': step_name,
                'description': description,
                'status': 'TIMEOUT',
                'duration_seconds': 1800,
                'timestamp': datetime.now().isoformat()
            }
            self.deployment_log['steps_completed'].append(step_result)
            return False
        except Exception as e:
            self.error(f"❌ {description} failed with exception: {str(e)}")
            step_result = {
                'name': step_name,
                'description': description,
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.deployment_log['steps_completed'].append(step_result)
            return False

    async def execute_workflow(self, start_from: str = None, stop_at: str = None) -> bool:
        """Execute the complete deployment workflow"""
        self.log("🚀 Starting ACGS Phase 3 Deployment Workflow")
        self.log("=" * 80)
        self.log(f"Environment: {self.environment}")
        self.log(f"Workflow Steps: {len(self.workflow_steps)}")
        
        if start_from:
            self.log(f"Starting from step: {start_from}")
        if stop_at:
            self.log(f"Stopping at step: {stop_at}")
        
        self.log("=" * 80)
        
        workflow_start_time = time.time()
        self.deployment_log['workflow_status'] = 'IN_PROGRESS'
        
        # Filter steps based on environment and start/stop parameters
        steps_to_execute = []
        start_executing = start_from is None
        
        for step in self.workflow_steps:
            # Skip steps not for current environment
            if self.environment == "staging" and step['environment'] == 'production':
                continue
            if self.environment == "production" and step['environment'] == 'staging':
                continue
            
            # Handle start_from parameter
            if not start_executing:
                if step['name'] == start_from:
                    start_executing = True
                else:
                    continue
            
            steps_to_execute.append(step)
            
            # Handle stop_at parameter
            if stop_at and step['name'] == stop_at:
                break
        
        self.log(f"Executing {len(steps_to_execute)} steps for {self.environment} environment")
        
        # Execute steps sequentially
        all_steps_passed = True
        
        for i, step in enumerate(steps_to_execute, 1):
            self.log(f"\n📋 Step {i}/{len(steps_to_execute)}: {step['description']}")
            self.log("-" * 60)
            
            step_passed = await self.execute_step(step)
            
            if not step_passed:
                if step['required']:
                    self.error(f"Required step failed: {step['name']}")
                    all_steps_passed = False
                    break
                else:
                    self.warning(f"Optional step failed: {step['name']}")
            
            # Brief pause between steps
            if i < len(steps_to_execute):
                await asyncio.sleep(5)
        
        workflow_end_time = time.time()
        workflow_duration = workflow_end_time - workflow_start_time
        
        # Update deployment log
        self.deployment_log['end_time'] = datetime.now().isoformat()
        self.deployment_log['workflow_duration_seconds'] = workflow_duration
        self.deployment_log['steps_executed'] = len(steps_to_execute)
        self.deployment_log['steps_passed'] = len([s for s in self.deployment_log['steps_completed'] if s.get('status') == 'SUCCESS'])
        
        if all_steps_passed:
            self.deployment_log['workflow_status'] = 'COMPLETED'
            self.deployment_log['final_status'] = 'SUCCESS'
            self.success("🎉 ACGS Phase 3 Deployment Workflow COMPLETED SUCCESSFULLY!")
        else:
            self.deployment_log['workflow_status'] = 'FAILED'
            self.deployment_log['final_status'] = 'FAILED'
            self.error("❌ ACGS Phase 3 Deployment Workflow FAILED")
        
        # Save deployment log
        log_filename = f"phase3_deployment_log_{self.environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_filename, 'w') as f:
            json.dump(self.deployment_log, f, indent=2)
        
        # Display summary
        self.log("=" * 80)
        self.log("📊 DEPLOYMENT WORKFLOW SUMMARY")
        self.log("=" * 80)
        self.log(f"Environment: {self.environment}")
        self.log(f"Total Duration: {workflow_duration:.1f} seconds ({workflow_duration/60:.1f} minutes)")
        self.log(f"Steps Executed: {len(steps_to_execute)}")
        self.log(f"Steps Passed: {self.deployment_log['steps_passed']}")
        self.log(f"Steps Failed: {len(steps_to_execute) - self.deployment_log['steps_passed']}")
        self.log(f"Final Status: {'✅ SUCCESS' if all_steps_passed else '❌ FAILED'}")
        self.log(f"Deployment Log: {log_filename}")
        
        if self.deployment_log['issues']:
            self.log(f"Issues Encountered: {len(self.deployment_log['issues'])}")
            for issue in self.deployment_log['issues'][-5:]:  # Show last 5 issues
                self.log(f"  [{issue['level']}] {issue['message']}")
        
        self.log("=" * 80)
        
        return all_steps_passed

def main():
    """Main orchestrator function"""
    parser = argparse.ArgumentParser(description='ACGS Phase 3 Deployment Orchestrator')
    parser.add_argument('--environment', choices=['staging', 'production'], default='staging',
                       help='Deployment environment (default: staging)')
    parser.add_argument('--start-from', help='Start workflow from specific step')
    parser.add_argument('--stop-at', help='Stop workflow at specific step')
    parser.add_argument('--list-steps', action='store_true', help='List available workflow steps')
    
    args = parser.parse_args()
    
    orchestrator = DeploymentOrchestrator(args.environment)
    
    if args.list_steps:
        print("Available workflow steps:")
        for i, step in enumerate(orchestrator.workflow_steps, 1):
            print(f"  {i}. {step['name']} ({step['environment']}) - {step['description']}")
        return
    
    try:
        success = asyncio.run(orchestrator.execute_workflow(args.start_from, args.stop_at))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        orchestrator.error("Deployment workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        orchestrator.error(f"Deployment workflow failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
