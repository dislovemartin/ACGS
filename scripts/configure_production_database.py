#!/usr/bin/env python3
"""
Production Database Configuration for ACGS-PGP
Sets up production-ready database connections, migrations, and monitoring
"""

import asyncio
import os
import sys
import subprocess
import json
import psycopg2
from datetime import datetime
from typing import Dict, Any, Optional

class ProductionDatabaseConfig:
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5433"),
            "database": os.getenv("DB_NAME", "acgs_pgp_db"),
            "username": os.getenv("DB_USER", "acgs_user"),
            "password": os.getenv("DB_PASSWORD", "acgs_password")
        }
        
        self.database_url = f"postgresql+asyncpg://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        self.sync_database_url = f"postgresql://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
    
    def test_database_connection(self) -> bool:
        """Test database connectivity"""
        print("🔌 Testing Database Connection...")
        
        try:
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["username"],
                password=self.db_config["password"]
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            print(f"  ✅ Database connection successful")
            print(f"  📊 PostgreSQL version: {version[0]}")
            return True
            
        except Exception as e:
            print(f"  ❌ Database connection failed: {str(e)}")
            return False
    
    def create_production_env_file(self):
        """Create production environment configuration"""
        print("\n📝 Creating Production Environment Configuration...")
        
        env_content = f"""# ACGS-PGP Production Database Configuration
# Generated on {datetime.now().isoformat()}

# Database Configuration
DATABASE_URL="{self.database_url}"
DB_HOST={self.db_config["host"]}
DB_PORT={self.db_config["port"]}
DB_NAME={self.db_config["database"]}
DB_USER={self.db_config["username"]}
DB_PASSWORD={self.db_config["password"]}

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# SSL Configuration (for production)
DB_SSL_MODE=require
DB_SSL_CERT_PATH=/path/to/client-cert.pem
DB_SSL_KEY_PATH=/path/to/client-key.pem
DB_SSL_CA_PATH=/path/to/ca-cert.pem

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=acgs-pgp-backups

# Monitoring Configuration
MONITORING_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# Performance Settings
STATEMENT_TIMEOUT=30000
IDLE_IN_TRANSACTION_SESSION_TIMEOUT=60000
"""
        
        with open(".env.production", "w") as f:
            f.write(env_content)
        
        print("  ✅ Production environment file created: .env.production")
    
    def run_database_migrations(self) -> bool:
        """Run Alembic database migrations"""
        print("\n🔄 Running Database Migrations...")
        
        try:
            # Set environment variable for migrations
            os.environ["DATABASE_URL"] = self.sync_database_url
            
            # Check current migration status
            result = subprocess.run([
                "docker-compose", "exec", "-T", "alembic-runner",
                "alembic", "current"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"  📊 Current migration: {result.stdout.strip()}")
            
            # Run migrations
            result = subprocess.run([
                "docker-compose", "exec", "-T", "alembic-runner", 
                "alembic", "upgrade", "head"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("  ✅ Database migrations completed successfully")
                print(f"  📝 Migration output: {result.stdout}")
                return True
            else:
                print("  ❌ Database migrations failed")
                print(f"  📝 Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ❌ Migration timeout - database may be slow")
            return False
        except Exception as e:
            print(f"  ❌ Migration error: {str(e)}")
            return False
    
    def create_database_monitoring_script(self):
        """Create database monitoring script"""
        print("\n📊 Creating Database Monitoring Script...")
        
        monitoring_script = f'''#!/bin/bash
# ACGS-PGP Database Monitoring Script

DB_HOST="{self.db_config["host"]}"
DB_PORT="{self.db_config["port"]}"
DB_NAME="{self.db_config["database"]}"
DB_USER="{self.db_config["username"]}"

echo "🔍 ACGS-PGP Database Health Check"
echo "================================="

# Connection test
echo "1. Testing database connection..."
if pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME; then
    echo "  ✅ Database is accepting connections"
else
    echo "  ❌ Database connection failed"
    exit 1
fi

# Database size
echo -e "\\n2. Database size information..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
    pg_database.datname as database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) as size
FROM pg_database 
WHERE datname = '$DB_NAME';"

# Table information
echo -e "\\n3. Table information..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_stat_get_tuples_inserted(c.oid) as inserts,
    pg_stat_get_tuples_updated(c.oid) as updates,
    pg_stat_get_tuples_deleted(c.oid) as deletes
FROM pg_tables pt
JOIN pg_class c ON c.relname = pt.tablename
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Active connections
echo -e "\\n4. Active connections..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
    count(*) as active_connections,
    state,
    application_name
FROM pg_stat_activity 
WHERE datname = '$DB_NAME'
GROUP BY state, application_name
ORDER BY active_connections DESC;"

# Migration status
echo -e "\\n5. Migration status..."
docker-compose exec -T alembic-runner alembic current

echo -e "\\n✅ Database health check complete"
'''
        
        with open("monitor_database.sh", "w") as f:
            f.write(monitoring_script)
        
        os.chmod("monitor_database.sh", 0o755)
        print("  ✅ Database monitoring script created: monitor_database.sh")
    
    def create_backup_script(self):
        """Create database backup script"""
        print("\n💾 Creating Database Backup Script...")
        
        backup_script = f'''#!/bin/bash
# ACGS-PGP Database Backup Script

DB_HOST="{self.db_config["host"]}"
DB_PORT="{self.db_config["port"]}"
DB_NAME="{self.db_config["database"]}"
DB_USER="{self.db_config["username"]}"

BACKUP_DIR="/var/backups/acgs-pgp"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/acgs_pgp_backup_$TIMESTAMP.sql"

echo "💾 ACGS-PGP Database Backup"
echo "==========================="

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
echo "Creating backup: $BACKUP_FILE"
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully"
    
    # Compress backup
    gzip $BACKUP_FILE
    echo "✅ Backup compressed: $BACKUP_FILE.gz"
    
    # Clean old backups (keep last 30 days)
    find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
    echo "✅ Old backups cleaned"
    
    # Show backup info
    ls -lh $BACKUP_FILE.gz
else
    echo "❌ Backup failed"
    exit 1
fi
'''
        
        with open("backup_database.sh", "w") as f:
            f.write(backup_script)
        
        os.chmod("backup_database.sh", 0o755)
        print("  ✅ Database backup script created: backup_database.sh")
    
    def create_performance_tuning_config(self):
        """Create PostgreSQL performance tuning configuration"""
        print("\n⚡ Creating Performance Tuning Configuration...")
        
        perf_config = '''# PostgreSQL Performance Tuning for ACGS-PGP
# Add these settings to postgresql.conf

# Memory Settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoint Settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Connection Settings
max_connections = 100
shared_preload_libraries = 'pg_stat_statements'

# Logging Settings
log_statement = 'mod'
log_duration = on
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on

# Monitoring
track_activities = on
track_counts = on
track_io_timing = on
track_functions = all
'''
        
        with open("postgresql_performance.conf", "w") as f:
            f.write(perf_config)
        
        print("  ✅ Performance tuning config created: postgresql_performance.conf")
    
    async def configure_production_database(self):
        """Main configuration function"""
        print("🚀 Configuring Production Database for ACGS-PGP")
        print("=" * 60)
        
        # Test connection
        if not self.test_database_connection():
            print("❌ Cannot proceed without database connection")
            return False
        
        # Create configuration files
        self.create_production_env_file()
        self.create_database_monitoring_script()
        self.create_backup_script()
        self.create_performance_tuning_config()
        
        # Run migrations
        migration_success = self.run_database_migrations()
        
        print("\n" + "=" * 60)
        print("✅ Production Database Configuration Complete!")
        print("\nCreated files:")
        print("- .env.production (environment configuration)")
        print("- monitor_database.sh (health monitoring)")
        print("- backup_database.sh (backup script)")
        print("- postgresql_performance.conf (performance tuning)")
        print("\nNext steps:")
        print("1. Review and customize .env.production")
        print("2. Set up automated backups: crontab -e")
        print("3. Apply performance settings to PostgreSQL")
        print("4. Monitor database: ./monitor_database.sh")
        
        return migration_success

async def main():
    config = ProductionDatabaseConfig()
    await config.configure_production_database()

if __name__ == "__main__":
    asyncio.run(main())
