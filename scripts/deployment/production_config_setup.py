#!/usr/bin/env python3
"""
ACGS-PGP Production Configuration Setup
Validates and configures production-ready environment settings
"""

import os
import sys
import json
import secrets
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ProductionConfigManager:
    def __init__(self):
        self.config_issues = []
        self.required_env_vars = {
            # Database configuration
            "DATABASE_URL": "postgresql://user:password@localhost:5432/acgs_pgp_db",
            "POSTGRES_USER": "acgs_user",
            "POSTGRES_PASSWORD": None,  # Must be generated
            "POSTGRES_DB": "acgs_pgp_db",
            
            # Redis configuration
            "REDIS_URL": "redis://localhost:6379/0",
            
            # JWT and Security
            "SECRET_KEY": None,  # Must be generated
            "CSRF_SECRET_KEY": None,  # Must be generated
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "REFRESH_TOKEN_EXPIRE_DAYS": "7",
            
            # LLM Integration
            "OPENAI_API_KEY": None,  # Must be provided
            "LLM_MODEL": "gpt-4",
            "LLM_MAX_TOKENS": "2048",
            
            # Service URLs
            "AUTH_SERVICE_URL": "http://auth-service:8001",
            "AC_SERVICE_URL": "http://ac-service:8002",
            "GS_SERVICE_URL": "http://gs-service:8003",
            "FV_SERVICE_URL": "http://fv-service:8004",
            "INTEGRITY_SERVICE_URL": "http://integrity-service:8005",
            "PGC_SERVICE_URL": "http://pgc-service:8006",
            
            # Cryptographic settings
            "CRYPTO_KEY_SIZE": "2048",
            "HASH_ALGORITHM": "SHA3-256",
            "SIGNATURE_ALGORITHM": "RSA-PSS-SHA256",
            
            # Performance settings
            "MAX_WORKERS": "4",
            "DB_POOL_SIZE": "20",
            "DB_MAX_OVERFLOW": "30",
            
            # Monitoring and logging
            "LOG_LEVEL": "INFO",
            "ENABLE_METRICS": "true",
            "SENTRY_DSN": None,  # Optional
        }
        
    def generate_secure_key(self, length: int = 32) -> str:
        """Generate a cryptographically secure random key"""
        return secrets.token_urlsafe(length)
    
    def check_environment_variables(self) -> Dict[str, str]:
        """Check and validate environment variables"""
        print("🔍 Checking Environment Variables...")
        
        env_config = {}
        missing_vars = []
        
        for var_name, default_value in self.required_env_vars.items():
            env_value = os.getenv(var_name)
            
            if env_value is None:
                if default_value is None:
                    # Generate secure keys for security-related variables
                    if "SECRET" in var_name or "PASSWORD" in var_name:
                        if var_name == "POSTGRES_PASSWORD":
                            generated_value = self.generate_secure_key(16)
                        else:
                            generated_value = self.generate_secure_key(32)
                        env_config[var_name] = generated_value
                        print(f"🔑 Generated {var_name}: {generated_value[:8]}...")
                    elif var_name == "OPENAI_API_KEY":
                        missing_vars.append(var_name)
                        print(f"❌ Missing required: {var_name}")
                    else:
                        missing_vars.append(var_name)
                        print(f"⚠️ Missing optional: {var_name}")
                else:
                    env_config[var_name] = default_value
                    print(f"✅ Using default: {var_name}")
            else:
                env_config[var_name] = env_value
                print(f"✅ Found: {var_name}")
        
        if missing_vars:
            self.config_issues.extend(missing_vars)
        
        return env_config
    
    def create_env_file(self, config: Dict[str, str], filename: str = ".env.production") -> None:
        """Create production environment file"""
        print(f"\n📝 Creating {filename}...")
        
        env_content = [
            "# ACGS-PGP Production Environment Configuration",
            f"# Generated on {datetime.now().isoformat()}",
            "",
            "# Database Configuration",
            f"DATABASE_URL={config.get('DATABASE_URL', '')}",
            f"POSTGRES_USER={config.get('POSTGRES_USER', '')}",
            f"POSTGRES_PASSWORD={config.get('POSTGRES_PASSWORD', '')}",
            f"POSTGRES_DB={config.get('POSTGRES_DB', '')}",
            "",
            "# Redis Configuration", 
            f"REDIS_URL={config.get('REDIS_URL', '')}",
            "",
            "# Security Configuration",
            f"SECRET_KEY={config.get('SECRET_KEY', '')}",
            f"CSRF_SECRET_KEY={config.get('CSRF_SECRET_KEY', '')}",
            f"ACCESS_TOKEN_EXPIRE_MINUTES={config.get('ACCESS_TOKEN_EXPIRE_MINUTES', '')}",
            f"REFRESH_TOKEN_EXPIRE_DAYS={config.get('REFRESH_TOKEN_EXPIRE_DAYS', '')}",
            "",
            "# LLM Integration",
            f"OPENAI_API_KEY={config.get('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY_HERE')}",
            f"LLM_MODEL={config.get('LLM_MODEL', '')}",
            f"LLM_MAX_TOKENS={config.get('LLM_MAX_TOKENS', '')}",
            "",
            "# Service URLs",
            f"AUTH_SERVICE_URL={config.get('AUTH_SERVICE_URL', '')}",
            f"AC_SERVICE_URL={config.get('AC_SERVICE_URL', '')}",
            f"GS_SERVICE_URL={config.get('GS_SERVICE_URL', '')}",
            f"FV_SERVICE_URL={config.get('FV_SERVICE_URL', '')}",
            f"INTEGRITY_SERVICE_URL={config.get('INTEGRITY_SERVICE_URL', '')}",
            f"PGC_SERVICE_URL={config.get('PGC_SERVICE_URL', '')}",
            "",
            "# Cryptographic Settings",
            f"CRYPTO_KEY_SIZE={config.get('CRYPTO_KEY_SIZE', '')}",
            f"HASH_ALGORITHM={config.get('HASH_ALGORITHM', '')}",
            f"SIGNATURE_ALGORITHM={config.get('SIGNATURE_ALGORITHM', '')}",
            "",
            "# Performance Settings",
            f"MAX_WORKERS={config.get('MAX_WORKERS', '')}",
            f"DB_POOL_SIZE={config.get('DB_POOL_SIZE', '')}",
            f"DB_MAX_OVERFLOW={config.get('DB_MAX_OVERFLOW', '')}",
            "",
            "# Monitoring and Logging",
            f"LOG_LEVEL={config.get('LOG_LEVEL', '')}",
            f"ENABLE_METRICS={config.get('ENABLE_METRICS', '')}",
            f"SENTRY_DSN={config.get('SENTRY_DSN', '')}",
        ]
        
        with open(filename, 'w') as f:
            f.write('\n'.join(env_content))
        
        print(f"✅ Created {filename}")
    
    def validate_database_migration(self) -> bool:
        """Validate that database migrations are up to date"""
        print("\n🗄️ Validating Database Migrations...")
        
        try:
            # Check if alembic is available
            result = subprocess.run(
                ["alembic", "current"], 
                capture_output=True, 
                text=True, 
                cwd="."
            )
            
            if result.returncode == 0:
                print("✅ Alembic is available")
                
                # Check migration status
                history_result = subprocess.run(
                    ["alembic", "history", "--verbose"],
                    capture_output=True,
                    text=True,
                    cwd="."
                )
                
                if "head" in history_result.stdout:
                    print("✅ Database migrations are up to date")
                    return True
                else:
                    print("⚠️ Database migrations may need to be applied")
                    self.config_issues.append("database_migrations")
                    return False
            else:
                print("❌ Alembic not available or configured")
                self.config_issues.append("alembic_setup")
                return False
                
        except FileNotFoundError:
            print("❌ Alembic not installed")
            self.config_issues.append("alembic_missing")
            return False
    
    def check_docker_setup(self) -> bool:
        """Check Docker and Docker Compose setup"""
        print("\n🐳 Checking Docker Setup...")
        
        try:
            # Check Docker
            docker_result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            
            if docker_result.returncode == 0:
                print("✅ Docker is available")
                
                # Check Docker Compose
                compose_result = subprocess.run(
                    ["docker-compose", "--version"],
                    capture_output=True,
                    text=True
                )
                
                if compose_result.returncode == 0:
                    print("✅ Docker Compose is available")
                    return True
                else:
                    print("❌ Docker Compose not available")
                    self.config_issues.append("docker_compose_missing")
                    return False
            else:
                print("❌ Docker not available")
                self.config_issues.append("docker_missing")
                return False
                
        except FileNotFoundError:
            print("❌ Docker not installed")
            self.config_issues.append("docker_not_installed")
            return False
    
    def run_production_setup(self) -> bool:
        """Run complete production setup validation"""
        print("🚀 ACGS-PGP Production Configuration Setup")
        print("=" * 60)
        print(f"Setup started at: {datetime.now().isoformat()}")
        
        # Check environment variables
        env_config = self.check_environment_variables()
        
        # Create production environment file
        self.create_env_file(env_config)
        
        # Validate database migrations
        self.validate_database_migration()
        
        # Check Docker setup
        self.check_docker_setup()
        
        # Print summary
        print("\n" + "=" * 60)
        print("PRODUCTION SETUP SUMMARY")
        print("=" * 60)
        
        if self.config_issues:
            print("⚠️ Issues found that need attention:")
            for issue in self.config_issues:
                print(f"  - {issue}")
            print("\n📋 Next Steps:")
            print("1. Set missing environment variables")
            print("2. Run database migrations: alembic upgrade head")
            print("3. Configure LLM API keys")
            print("4. Test service connectivity")
            return False
        else:
            print("✅ Production configuration is ready!")
            print("\n📋 Next Steps:")
            print("1. Review .env.production file")
            print("2. Start services: docker-compose up -d")
            print("3. Run integration tests: python test_service_integration.py")
            return True

def main():
    """Main setup function"""
    manager = ProductionConfigManager()
    success = manager.run_production_setup()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
