#!/bin/bash
# ACGS-PGP Database Backup Script with Rotation and S3 Upload

set -e

# Configuration
DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="acgs_pgp_db"
DB_USER="acgs_user"

BACKUP_DIR="/var/backups/acgs-pgp"
S3_BUCKET="acgs-pgp-backups"
RETENTION_DAYS=7

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
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --verbose --clean --no-owner --no-privileges \
    --format=custom --compress=9 \
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
    gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
        --s2k-digest-algo SHA512 --s2k-count 65536 \
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
{
    "timestamp": "$TIMESTAMP",
    "database": "$DB_NAME",
    "file": "$(basename $COMPRESSED_FILE)",
    "size": "$(du -h $COMPRESSED_FILE | cut -f1)",
    "checksum": "$(sha256sum $COMPRESSED_FILE | cut -d' ' -f1)",
    "type": "full",
    "encrypted": "${ENCRYPT_BACKUPS:-false}"
}
EOF

# Clean old backups
echo "6. Cleaning old backups..."
find $BACKUP_DIR -name "acgs_pgp_db_*.gz*" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "backup_*.json" -mtime +$RETENTION_DAYS -delete
echo "  ✅ Old backups cleaned (retention: $RETENTION_DAYS days)"

# Verify backup integrity
echo "7. Verifying backup integrity..."
if [ "${COMPRESSED_FILE##*.}" = "gpg" ]; then
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
