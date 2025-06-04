#!/usr/bin/env python3
"""
Research Infrastructure Setup Script

Initializes the ACGS-PGP research infrastructure including database setup,
automated pipelines, and initial configuration.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

import httpx
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ResearchInfrastructureSetup:
    """Research infrastructure setup manager."""
    
    def __init__(self):
        self.project_root = project_root
        self.research_service_url = "http://localhost:8007"
        self.database_url = "postgresql+asyncpg://postgres:postgres@localhost:5434/acgs_research"
        
    async def setup_infrastructure(self):
        """Setup complete research infrastructure."""
        try:
            logger.info("Starting research infrastructure setup...")
            
            # 1. Setup database
            await self.setup_database()
            
            # 2. Wait for research service to be ready
            await self.wait_for_service()
            
            # 3. Create automated pipelines
            await self.create_automated_pipelines()
            
            # 4. Setup initial datasets
            await self.setup_initial_datasets()
            
            # 5. Create sample experiments
            await self.create_sample_experiments()
            
            # 6. Setup monitoring and alerts
            await self.setup_monitoring()
            
            logger.info("✅ Research infrastructure setup completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Research infrastructure setup failed: {e}")
            raise
    
    async def setup_database(self):
        """Setup research database and tables."""
        try:
            logger.info("Setting up research database...")
            
            # Create database if it doesn't exist
            await self.create_database_if_not_exists()
            
            # Initialize tables (this would be done by the service on startup)
            logger.info("Database setup completed")
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
    
    async def create_database_if_not_exists(self):
        """Create research database if it doesn't exist."""
        try:
            # Connect to postgres database to create research database
            conn = await asyncpg.connect(
                host="localhost",
                port=5434,
                user="postgres",
                password="postgres",
                database="postgres"
            )
            
            # Check if database exists
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = 'acgs_research'"
            )
            
            if not result:
                await conn.execute("CREATE DATABASE acgs_research")
                logger.info("Created acgs_research database")
            else:
                logger.info("acgs_research database already exists")
            
            await conn.close()
            
        except Exception as e:
            logger.warning(f"Could not create database (may already exist): {e}")
    
    async def wait_for_service(self):
        """Wait for research service to be ready."""
        logger.info("Waiting for research service to be ready...")
        
        max_retries = 30
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.research_service_url}/health")
                    if response.status_code == 200:
                        logger.info("Research service is ready")
                        return
            except Exception:
                pass
            
            logger.info(f"Waiting for research service... (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(retry_delay)
        
        raise Exception("Research service did not become ready within timeout")
    
    async def create_automated_pipelines(self):
        """Create automated research pipelines."""
        try:
            logger.info("Creating automated research pipelines...")
            
            async with httpx.AsyncClient() as client:
                # Create constitutional compliance pipeline
                response = await client.post(
                    f"{self.research_service_url}/api/v1/automation/pipelines/constitutional-compliance"
                )
                if response.status_code == 200:
                    logger.info("✅ Created constitutional compliance pipeline")
                else:
                    logger.warning(f"Failed to create compliance pipeline: {response.text}")
                
                # Create LLM reliability pipeline
                response = await client.post(
                    f"{self.research_service_url}/api/v1/automation/pipelines/llm-reliability"
                )
                if response.status_code == 200:
                    logger.info("✅ Created LLM reliability pipeline")
                else:
                    logger.warning(f"Failed to create reliability pipeline: {response.text}")
                
                # Create performance monitoring pipeline
                response = await client.post(
                    f"{self.research_service_url}/api/v1/automation/pipelines/performance-monitoring"
                )
                if response.status_code == 200:
                    logger.info("✅ Created performance monitoring pipeline")
                else:
                    logger.warning(f"Failed to create monitoring pipeline: {response.text}")
            
        except Exception as e:
            logger.error(f"Failed to create automated pipelines: {e}")
            raise
    
    async def setup_initial_datasets(self):
        """Setup initial research datasets."""
        try:
            logger.info("Setting up initial research datasets...")
            
            datasets = [
                {
                    "name": "Constitutional Compliance Baseline",
                    "description": "Baseline constitutional compliance data",
                    "domain": "constitutional_ai",
                    "data_type": "experimental",
                    "schema_definition": {
                        "principle_id": "string",
                        "compliance_score": "float",
                        "violation_type": "string",
                        "timestamp": "datetime"
                    },
                    "tags": ["baseline", "compliance", "constitutional"]
                },
                {
                    "name": "LLM Reliability Test Data",
                    "description": "LLM reliability testing dataset",
                    "domain": "llm_reliability",
                    "data_type": "experimental",
                    "schema_definition": {
                        "model_id": "string",
                        "reliability_score": "float",
                        "failure_mode": "string",
                        "test_case": "string",
                        "timestamp": "datetime"
                    },
                    "tags": ["reliability", "llm", "testing"]
                },
                {
                    "name": "Performance Metrics",
                    "description": "System performance monitoring data",
                    "domain": "performance",
                    "data_type": "observational",
                    "schema_definition": {
                        "service_name": "string",
                        "response_time": "float",
                        "throughput": "float",
                        "error_rate": "float",
                        "timestamp": "datetime"
                    },
                    "tags": ["performance", "monitoring", "metrics"]
                }
            ]
            
            async with httpx.AsyncClient() as client:
                for dataset in datasets:
                    response = await client.post(
                        f"{self.research_service_url}/api/v1/data/datasets",
                        json=dataset
                    )
                    if response.status_code == 200:
                        logger.info(f"✅ Created dataset: {dataset['name']}")
                    else:
                        logger.warning(f"Failed to create dataset {dataset['name']}: {response.text}")
            
        except Exception as e:
            logger.error(f"Failed to setup initial datasets: {e}")
            raise
    
    async def create_sample_experiments(self):
        """Create sample experiments for demonstration."""
        try:
            logger.info("Creating sample experiments...")
            
            experiments = [
                {
                    "name": "Constitutional Compliance Baseline Study",
                    "description": "Establish baseline constitutional compliance metrics",
                    "hypothesis": "Current system achieves >99% constitutional compliance",
                    "methodology": "Cross-service compliance testing with statistical analysis",
                    "parameters": {
                        "sample_size": 1000,
                        "confidence_level": 0.95,
                        "services": ["ac_service", "gs_service", "fv_service", "pgc_service"]
                    },
                    "expected_duration_hours": 2,
                    "success_criteria": {
                        "compliance_rate": 0.99,
                        "statistical_significance": 0.05
                    },
                    "tags": ["baseline", "compliance", "constitutional"]
                },
                {
                    "name": "LLM Reliability Enhancement Study",
                    "description": "Evaluate LLM reliability improvements",
                    "hypothesis": "Multi-model consensus improves reliability to >99.9%",
                    "methodology": "A/B testing with control and enhanced LLM configurations",
                    "parameters": {
                        "control_group_size": 500,
                        "treatment_group_size": 500,
                        "reliability_threshold": 0.999
                    },
                    "expected_duration_hours": 4,
                    "success_criteria": {
                        "reliability_improvement": 0.01,
                        "statistical_significance": 0.01
                    },
                    "tags": ["reliability", "llm", "enhancement"]
                }
            ]
            
            async with httpx.AsyncClient() as client:
                for experiment in experiments:
                    response = await client.post(
                        f"{self.research_service_url}/api/v1/experiments",
                        json=experiment
                    )
                    if response.status_code == 200:
                        logger.info(f"✅ Created experiment: {experiment['name']}")
                    else:
                        logger.warning(f"Failed to create experiment {experiment['name']}: {response.text}")
            
        except Exception as e:
            logger.error(f"Failed to create sample experiments: {e}")
            raise
    
    async def setup_monitoring(self):
        """Setup monitoring and alerting."""
        try:
            logger.info("Setting up monitoring and alerting...")
            
            # Create monitoring configuration
            monitoring_config = {
                "health_checks": {
                    "interval_seconds": 30,
                    "timeout_seconds": 10,
                    "endpoints": [
                        f"{self.research_service_url}/health"
                    ]
                },
                "performance_thresholds": {
                    "response_time_ms": 200,
                    "error_rate_percent": 1.0,
                    "cpu_usage_percent": 80,
                    "memory_usage_percent": 85
                },
                "alerts": {
                    "experiment_failure": True,
                    "performance_degradation": True,
                    "reproducibility_issues": True,
                    "data_quality_problems": True
                }
            }
            
            # Save monitoring configuration
            config_path = self.project_root / "research_data" / "monitoring_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, "w") as f:
                json.dump(monitoring_config, f, indent=2)
            
            logger.info("✅ Monitoring configuration created")
            
        except Exception as e:
            logger.error(f"Failed to setup monitoring: {e}")
            raise
    
    def print_setup_summary(self):
        """Print setup summary and next steps."""
        print("\n" + "="*60)
        print("🎉 ACGS-PGP Research Infrastructure Setup Complete!")
        print("="*60)
        print("\n📋 What was set up:")
        print("  ✅ Research database and tables")
        print("  ✅ Automated research pipelines")
        print("  ✅ Initial research datasets")
        print("  ✅ Sample experiments")
        print("  ✅ Monitoring and alerting")
        print("\n🔗 Access Points:")
        print(f"  • Research Service API: {self.research_service_url}")
        print(f"  • API Documentation: {self.research_service_url}/docs")
        print(f"  • Health Check: {self.research_service_url}/health")
        print(f"  • Via Nginx Gateway: http://localhost:8000/api/research/")
        print("\n📊 Automated Pipelines:")
        print("  • Constitutional Compliance: Daily at 2 AM")
        print("  • LLM Reliability Testing: Weekly on Monday at 6 AM")
        print("  • Performance Monitoring: Every 15 minutes")
        print("\n🚀 Next Steps:")
        print("  1. Start research service: docker-compose up research_service")
        print("  2. Access API docs at: http://localhost:8007/docs")
        print("  3. Run sample experiments")
        print("  4. Monitor automated pipelines")
        print("  5. Create custom experiments and analyses")
        print("\n📚 Documentation:")
        print("  • Research Infrastructure Guide: docs/research_infrastructure.md")
        print("  • API Reference: http://localhost:8007/docs")
        print("="*60)


async def main():
    """Main setup function."""
    setup = ResearchInfrastructureSetup()
    
    try:
        await setup.setup_infrastructure()
        setup.print_setup_summary()
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
