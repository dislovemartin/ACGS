#!/bin/bash
# ACGS-PGP Database Backup Script

DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="acgs_pgp_db"
DB_USER="acgs_user"

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
