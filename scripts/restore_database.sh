#!/bin/bash
# ACGS-PGP Database Restore Script

set -e

DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="acgs_pgp_db"
DB_USER="acgs_user"
BACKUP_DIR="/var/backups/acgs-pgp"

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
if [ "${BACKUP_FILE##*.}" = "gpg" ]; then
    echo "3. Decrypting backup..."
    RESTORE_FILE="${BACKUP_FILE%.gpg}"
    gpg --decrypt $BACKUP_FILE > $RESTORE_FILE
    echo "  ✅ Backup decrypted"
fi

# Decompress if needed
if [ "${RESTORE_FILE##*.}" = "gz" ]; then
    echo "4. Decompressing backup..."
    gunzip -c $RESTORE_FILE > "${RESTORE_FILE%.gz}"
    RESTORE_FILE="${RESTORE_FILE%.gz}"
    echo "  ✅ Backup decompressed"
fi

# Drop and recreate database
echo "5. Recreating database..."
dropdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME --if-exists
createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
echo "  ✅ Database recreated"

# Restore database
echo "6. Restoring database..."
if [ "${RESTORE_FILE##*.}" = "sql" ]; then
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
