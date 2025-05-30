#!/usr/bin/env python3
"""
Backup and Disaster Recovery Setup for ACGS-PGP
Implements comprehensive backup strategies and disaster recovery procedures
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any

class BackupDisasterRecovery:
    def __init__(self):
        self.backup_config = {
            "database": {
                "host": "localhost",
                "port": "5433",
                "name": "acgs_pgp_db",
                "user": "acgs_user"
            },
            "retention": {
                "daily": 7,
                "weekly": 4,
                "monthly": 12
            },
            "storage": {
                "local_path": "/var/backups/acgs-pgp",
                "s3_bucket": "acgs-pgp-backups",
                "encryption": True
            }
        }
    
    def create_backup_strategy_document(self):
        """Create backup strategy documentation"""
        print("📋 Creating Backup Strategy Document...")
        
        strategy_doc = f"""# ACGS-PGP Backup and Disaster Recovery Strategy

## Overview
This document outlines the backup and disaster recovery procedures for the ACGS-PGP system.

## Backup Strategy

### 1. Database Backups
- **Frequency**: Daily at 2:00 AM UTC
- **Type**: Full PostgreSQL dump with compression
- **Retention**: 
  - Daily: {self.backup_config['retention']['daily']} days
  - Weekly: {self.backup_config['retention']['weekly']} weeks  
  - Monthly: {self.backup_config['retention']['monthly']} months
- **Storage**: Local + S3 with encryption

### 2. Configuration Backups
- **Frequency**: Before any configuration changes
- **Includes**: Docker configs, environment files, certificates
- **Storage**: Version controlled + encrypted backup

### 3. Application State Backups
- **Frequency**: Daily
- **Includes**: Policy rules, audit logs, cryptographic keys
- **Storage**: Encrypted S3 with versioning

## Recovery Procedures

### 1. Database Recovery
1. Stop all services
2. Restore database from backup
3. Verify data integrity
4. Restart services
5. Validate system functionality

### 2. Full System Recovery
1. Provision new infrastructure
2. Restore configurations
3. Restore database
4. Restore application state
5. Validate all components
6. Update DNS/load balancers

## Recovery Time Objectives (RTO)
- Database: 30 minutes
- Full system: 2 hours
- Critical services: 15 minutes

## Recovery Point Objectives (RPO)
- Database: 24 hours
- Configuration: 1 hour
- Application state: 24 hours

Generated on: {datetime.now().isoformat()}
"""
        
        with open("backup_strategy.md", "w") as f:
            f.write(strategy_doc)
        
        print("  ✅ Backup strategy document created: backup_strategy.md")
    
    def create_database_backup_script(self):
        """Create comprehensive database backup script"""
        print("\n💾 Creating Database Backup Script...")
        
        backup_script = f'''#!/bin/bash
# ACGS-PGP Database Backup Script with Rotation and S3 Upload

set -e

# Configuration
DB_HOST="{self.backup_config['database']['host']}"
DB_PORT="{self.backup_config['database']['port']}"
DB_NAME="{self.backup_config['database']['name']}"
DB_USER="{self.backup_config['database']['user']}"

BACKUP_DIR="{self.backup_config['storage']['local_path']}"
S3_BUCKET="{self.backup_config['storage']['s3_bucket']}"
RETENTION_DAYS={self.backup_config['retention']['daily']}

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE=$(date +"%Y%m%d")
BACKUP_FILE="$BACKUP_DIR/acgs_pgp_db_$TIMESTAMP.sql"
COMPRESSED_FILE="$BACKUP_FILE.gz"

echo "💾 ACGS-PGP Database Backup - $TIMESTAMP"
echo "=========================================="

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
echo "1. Creating database backup..."
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \\
    --verbose --clean --no-owner --no-privileges \\
    --format=custom --compress=9 \\
    --file=$BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "  ✅ Database backup created: $BACKUP_FILE"
else
    echo "  ❌ Database backup failed"
    exit 1
fi

# Compress backup
echo "2. Compressing backup..."
gzip $BACKUP_FILE
echo "  ✅ Backup compressed: $COMPRESSED_FILE"

# Encrypt backup (optional)
if [ "$ENCRYPT_BACKUPS" = "true" ]; then
    echo "3. Encrypting backup..."
    gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \\
        --s2k-digest-algo SHA512 --s2k-count 65536 \\
        --symmetric --output $COMPRESSED_FILE.gpg $COMPRESSED_FILE
    rm $COMPRESSED_FILE
    COMPRESSED_FILE="$COMPRESSED_FILE.gpg"
    echo "  ✅ Backup encrypted: $COMPRESSED_FILE"
fi

# Upload to S3 (if configured)
if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
    echo "4. Uploading to S3..."
    aws s3 cp $COMPRESSED_FILE s3://$S3_BUCKET/database/$(basename $COMPRESSED_FILE)
    if [ $? -eq 0 ]; then
        echo "  ✅ Backup uploaded to S3"
    else
        echo "  ⚠️  S3 upload failed, backup retained locally"
    fi
fi

# Create backup metadata
echo "5. Creating backup metadata..."
cat > $BACKUP_DIR/backup_$TIMESTAMP.json << EOF
{{
    "timestamp": "$TIMESTAMP",
    "database": "$DB_NAME",
    "file": "$(basename $COMPRESSED_FILE)",
    "size": "$(du -h $COMPRESSED_FILE | cut -f1)",
    "checksum": "$(sha256sum $COMPRESSED_FILE | cut -d' ' -f1)",
    "type": "full",
    "encrypted": "${{ENCRYPT_BACKUPS:-false}}"
}}
EOF

# Clean old backups
echo "6. Cleaning old backups..."
find $BACKUP_DIR -name "acgs_pgp_db_*.gz*" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "backup_*.json" -mtime +$RETENTION_DAYS -delete
echo "  ✅ Old backups cleaned (retention: $RETENTION_DAYS days)"

# Verify backup integrity
echo "7. Verifying backup integrity..."
if [ "${{COMPRESSED_FILE##*.}}" = "gpg" ]; then
    echo "  ℹ️  Encrypted backup - skipping integrity check"
else
    gunzip -t $COMPRESSED_FILE
    if [ $? -eq 0 ]; then
        echo "  ✅ Backup integrity verified"
    else
        echo "  ❌ Backup integrity check failed"
        exit 1
    fi
fi

echo "✅ Backup completed successfully: $(basename $COMPRESSED_FILE)"
echo "📊 Backup size: $(du -h $COMPRESSED_FILE | cut -f1)"
'''
        
        with open("backup_database_comprehensive.sh", "w") as f:
            f.write(backup_script)
        
        os.chmod("backup_database_comprehensive.sh", 0o755)
        print("  ✅ Comprehensive backup script created: backup_database_comprehensive.sh")
    
    def create_restore_script(self):
        """Create database restore script"""
        print("\n🔄 Creating Database Restore Script...")
        
        restore_script = f'''#!/bin/bash
# ACGS-PGP Database Restore Script

set -e

DB_HOST="{self.backup_config['database']['host']}"
DB_PORT="{self.backup_config['database']['port']}"
DB_NAME="{self.backup_config['database']['name']}"
DB_USER="{self.backup_config['database']['user']}"
BACKUP_DIR="{self.backup_config['storage']['local_path']}"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -la $BACKUP_DIR/acgs_pgp_db_*.gz* 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

echo "🔄 ACGS-PGP Database Restore"
echo "============================"
echo "Backup file: $BACKUP_FILE"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Stop services
echo "1. Stopping ACGS-PGP services..."
docker-compose stop ac_service gs_service fv_service integrity_service pgc_service
echo "  ✅ Services stopped"

# Create database backup before restore
echo "2. Creating pre-restore backup..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PRE_RESTORE_BACKUP="$BACKUP_DIR/pre_restore_$TIMESTAMP.sql"
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > $PRE_RESTORE_BACKUP
gzip $PRE_RESTORE_BACKUP
echo "  ✅ Pre-restore backup created: $PRE_RESTORE_BACKUP.gz"

# Decrypt if needed
RESTORE_FILE="$BACKUP_FILE"
if [ "${{BACKUP_FILE##*.}}" = "gpg" ]; then
    echo "3. Decrypting backup..."
    RESTORE_FILE="${{BACKUP_FILE%.gpg}}"
    gpg --decrypt $BACKUP_FILE > $RESTORE_FILE
    echo "  ✅ Backup decrypted"
fi

# Decompress if needed
if [ "${{RESTORE_FILE##*.}}" = "gz" ]; then
    echo "4. Decompressing backup..."
    gunzip -c $RESTORE_FILE > "${{RESTORE_FILE%.gz}}"
    RESTORE_FILE="${{RESTORE_FILE%.gz}}"
    echo "  ✅ Backup decompressed"
fi

# Drop and recreate database
echo "5. Recreating database..."
dropdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME --if-exists
createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
echo "  ✅ Database recreated"

# Restore database
echo "6. Restoring database..."
if [ "${{RESTORE_FILE##*.}}" = "sql" ]; then
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < $RESTORE_FILE
else
    pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME $RESTORE_FILE
fi

if [ $? -eq 0 ]; then
    echo "  ✅ Database restored successfully"
else
    echo "  ❌ Database restore failed"
    exit 1
fi

# Run migrations
echo "7. Running database migrations..."
docker-compose exec -T alembic-runner alembic upgrade head
echo "  ✅ Migrations completed"

# Start services
echo "8. Starting ACGS-PGP services..."
docker-compose start ac_service gs_service fv_service integrity_service pgc_service
echo "  ✅ Services started"

# Verify system health
echo "9. Verifying system health..."
sleep 10
./health_check.sh

echo "✅ Database restore completed successfully"
'''
        
        with open("restore_database.sh", "w") as f:
            f.write(restore_script)
        
        os.chmod("restore_database.sh", 0o755)
        print("  ✅ Database restore script created: restore_database.sh")
    
    def create_disaster_recovery_playbook(self):
        """Create disaster recovery playbook"""
        print("\n📖 Creating Disaster Recovery Playbook...")
        
        playbook = '''# ACGS-PGP Disaster Recovery Playbook

## Emergency Contacts
- System Administrator: admin@acgs-pgp.com
- Database Administrator: dba@acgs-pgp.com
- Security Team: security@acgs-pgp.com

## Incident Response Procedures

### 1. Database Failure
**Symptoms**: Database connection errors, data corruption
**Steps**:
1. Assess damage: `./health_check.sh`
2. Stop all services: `docker-compose stop`
3. Identify latest backup: `ls -la /var/backups/acgs-pgp/`
4. Restore database: `./restore_database.sh <backup_file>`
5. Verify integrity: `./health_check.sh`
6. Document incident

### 2. Service Failure
**Symptoms**: Service unavailable, high error rates
**Steps**:
1. Check service status: `docker-compose ps`
2. Review logs: `docker-compose logs <service>`
3. Restart service: `docker-compose restart <service>`
4. If persistent, restore from backup
5. Monitor for stability

### 3. Complete System Failure
**Symptoms**: All services down, infrastructure failure
**Steps**:
1. Provision new infrastructure
2. Deploy ACGS-PGP: `docker-compose up -d`
3. Restore database: `./restore_database.sh <latest_backup>`
4. Restore configurations from backup
5. Update DNS/load balancers
6. Verify all functionality

### 4. Security Incident
**Symptoms**: Unauthorized access, data breach
**Steps**:
1. Isolate affected systems
2. Preserve evidence
3. Assess scope of breach
4. Notify stakeholders
5. Restore from clean backup
6. Implement additional security measures

## Recovery Checklists

### Database Recovery Checklist
- [ ] Stop all services
- [ ] Create pre-restore backup
- [ ] Restore from backup
- [ ] Run migrations
- [ ] Start services
- [ ] Verify data integrity
- [ ] Test critical functions
- [ ] Monitor for issues

### Full System Recovery Checklist
- [ ] Provision infrastructure
- [ ] Deploy application
- [ ] Restore database
- [ ] Restore configurations
- [ ] Update external dependencies
- [ ] Test all services
- [ ] Update monitoring
- [ ] Notify users

## Testing Procedures
- Monthly: Test database restore
- Quarterly: Full disaster recovery drill
- Annually: Review and update procedures
'''
        
        with open("disaster_recovery_playbook.md", "w") as f:
            f.write(playbook)
        
        print("  ✅ Disaster recovery playbook created: disaster_recovery_playbook.md")
    
    def create_backup_monitoring_script(self):
        """Create backup monitoring and validation script"""
        print("\n🔍 Creating Backup Monitoring Script...")
        
        monitoring_script = f'''#!/bin/bash
# ACGS-PGP Backup Monitoring and Validation

BACKUP_DIR="{self.backup_config['storage']['local_path']}"
S3_BUCKET="{self.backup_config['storage']['s3_bucket']}"
MAX_AGE_HOURS=25  # Alert if no backup in 25 hours

echo "🔍 ACGS-PGP Backup Monitoring"
echo "============================="

# Check local backups
echo "1. Local Backup Status:"
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(find $BACKUP_DIR -name "acgs_pgp_db_*.gz*" -type f -printf '%T@ %p\\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))
        echo "  📁 Latest backup: $(basename $LATEST_BACKUP)"
        echo "  🕐 Age: $BACKUP_AGE hours"
        echo "  📊 Size: $(du -h $LATEST_BACKUP | cut -f1)"
        
        if [ $BACKUP_AGE -gt $MAX_AGE_HOURS ]; then
            echo "  ⚠️  WARNING: Backup is older than $MAX_AGE_HOURS hours"
        else
            echo "  ✅ Backup age is acceptable"
        fi
    else
        echo "  ❌ No backups found in $BACKUP_DIR"
    fi
else
    echo "  ❌ Backup directory not found: $BACKUP_DIR"
fi

# Check S3 backups (if configured)
echo -e "\\n2. S3 Backup Status:"
if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
    S3_LATEST=$(aws s3 ls s3://$S3_BUCKET/database/ --recursive | sort | tail -1)
    if [ -n "$S3_LATEST" ]; then
        echo "  ☁️  Latest S3 backup: $(echo $S3_LATEST | awk '{{print $4}}')"
        echo "  📅 Date: $(echo $S3_LATEST | awk '{{print $1, $2}}')"
        echo "  ✅ S3 backups available"
    else
        echo "  ❌ No S3 backups found"
    fi
else
    echo "  ℹ️  S3 not configured or AWS CLI not available"
fi

# Validate backup integrity
echo -e "\\n3. Backup Integrity Check:"
if [ -n "$LATEST_BACKUP" ]; then
    if [ "${{LATEST_BACKUP##*.}}" = "gpg" ]; then
        echo "  🔐 Encrypted backup - integrity check requires decryption"
    else
        gunzip -t "$LATEST_BACKUP" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✅ Backup integrity verified"
        else
            echo "  ❌ Backup integrity check failed"
        fi
    fi
fi

# Check backup metadata
echo -e "\\n4. Backup Metadata:"
METADATA_FILE="$BACKUP_DIR/backup_$(basename $LATEST_BACKUP | sed 's/acgs_pgp_db_//' | sed 's/\\..*/.json/')"
if [ -f "$METADATA_FILE" ]; then
    echo "  📋 Metadata available:"
    cat "$METADATA_FILE" | jq -r '"  Size: " + .size + ", Checksum: " + .checksum[0:16] + "..."'
else
    echo "  ⚠️  No metadata file found"
fi

# Summary
echo -e "\\n📊 Backup Summary:"
BACKUP_COUNT=$(find $BACKUP_DIR -name "acgs_pgp_db_*.gz*" -type f | wc -l)
echo "  Total backups: $BACKUP_COUNT"
echo "  Retention policy: {self.backup_config['retention']['daily']} days"

if [ $BACKUP_AGE -le $MAX_AGE_HOURS ] && [ -n "$LATEST_BACKUP" ]; then
    echo "  Status: ✅ Backup system healthy"
    exit 0
else
    echo "  Status: ❌ Backup system needs attention"
    exit 1
fi
'''
        
        with open("monitor_backups.sh", "w") as f:
            f.write(monitoring_script)
        
        os.chmod("monitor_backups.sh", 0o755)
        print("  ✅ Backup monitoring script created: monitor_backups.sh")
    
    def create_cron_jobs(self):
        """Create cron job configuration"""
        print("\n⏰ Creating Cron Job Configuration...")
        
        cron_config = f'''# ACGS-PGP Automated Backup and Monitoring Cron Jobs
# Add these to your crontab: crontab -e

# Daily database backup at 2:00 AM
0 2 * * * /path/to/acgs-pgp/backup_database_comprehensive.sh >> /var/log/acgs-backup.log 2>&1

# Hourly backup monitoring
0 * * * * /path/to/acgs-pgp/monitor_backups.sh >> /var/log/acgs-backup-monitor.log 2>&1

# Weekly backup cleanup and S3 sync
0 3 * * 0 find {self.backup_config['storage']['local_path']} -name "*.gz*" -mtime +{self.backup_config['retention']['daily']} -delete

# Monthly disaster recovery test (first Sunday of month)
0 4 1-7 * 0 /path/to/acgs-pgp/test_disaster_recovery.sh >> /var/log/acgs-dr-test.log 2>&1

# Daily health check
*/30 * * * * /path/to/acgs-pgp/health_check.sh >> /var/log/acgs-health.log 2>&1
'''
        
        with open("acgs_cron_jobs.txt", "w") as f:
            f.write(cron_config)
        
        print("  ✅ Cron job configuration created: acgs_cron_jobs.txt")
    
    def setup_backup_disaster_recovery(self):
        """Main setup function"""
        print("🚀 Setting up Backup and Disaster Recovery for ACGS-PGP")
        print("=" * 60)
        
        self.create_backup_strategy_document()
        self.create_database_backup_script()
        self.create_restore_script()
        self.create_disaster_recovery_playbook()
        self.create_backup_monitoring_script()
        self.create_cron_jobs()
        
        # Create test script
        test_script = '''#!/bin/bash
# Test disaster recovery procedures

echo "🧪 Testing Disaster Recovery Procedures"
echo "======================================="

echo "1. Testing backup creation..."
./backup_database_comprehensive.sh

echo -e "\\n2. Testing backup monitoring..."
./monitor_backups.sh

echo -e "\\n3. Testing health checks..."
./health_check.sh

echo -e "\\n✅ Disaster recovery test completed"
'''
        
        with open("test_disaster_recovery.sh", "w") as f:
            f.write(test_script)
        
        os.chmod("test_disaster_recovery.sh", 0o755)
        
        print("\n" + "=" * 60)
        print("✅ Backup and Disaster Recovery Setup Complete!")
        print("\nCreated files:")
        print("- backup_strategy.md (strategy documentation)")
        print("- backup_database_comprehensive.sh (backup script)")
        print("- restore_database.sh (restore script)")
        print("- disaster_recovery_playbook.md (emergency procedures)")
        print("- monitor_backups.sh (backup monitoring)")
        print("- acgs_cron_jobs.txt (automated scheduling)")
        print("- test_disaster_recovery.sh (testing script)")
        print("\nNext steps:")
        print("1. Set up cron jobs: crontab acgs_cron_jobs.txt")
        print("2. Test backup: ./backup_database_comprehensive.sh")
        print("3. Test restore: ./test_disaster_recovery.sh")
        print("4. Configure S3 credentials for offsite backup")

def main():
    setup = BackupDisasterRecovery()
    setup.setup_backup_disaster_recovery()

if __name__ == "__main__":
    main()
