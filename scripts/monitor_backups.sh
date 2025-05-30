#!/bin/bash
# ACGS-PGP Backup Monitoring and Validation

BACKUP_DIR="/var/backups/acgs-pgp"
S3_BUCKET="acgs-pgp-backups"
MAX_AGE_HOURS=25  # Alert if no backup in 25 hours

echo "🔍 ACGS-PGP Backup Monitoring"
echo "============================="

# Check local backups
echo "1. Local Backup Status:"
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(find $BACKUP_DIR -name "acgs_pgp_db_*.gz*" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
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
echo -e "\n2. S3 Backup Status:"
if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
    S3_LATEST=$(aws s3 ls s3://$S3_BUCKET/database/ --recursive | sort | tail -1)
    if [ -n "$S3_LATEST" ]; then
        echo "  ☁️  Latest S3 backup: $(echo $S3_LATEST | awk '{print $4}')"
        echo "  📅 Date: $(echo $S3_LATEST | awk '{print $1, $2}')"
        echo "  ✅ S3 backups available"
    else
        echo "  ❌ No S3 backups found"
    fi
else
    echo "  ℹ️  S3 not configured or AWS CLI not available"
fi

# Validate backup integrity
echo -e "\n3. Backup Integrity Check:"
if [ -n "$LATEST_BACKUP" ]; then
    if [ "${LATEST_BACKUP##*.}" = "gpg" ]; then
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
echo -e "\n4. Backup Metadata:"
METADATA_FILE="$BACKUP_DIR/backup_$(basename $LATEST_BACKUP | sed 's/acgs_pgp_db_//' | sed 's/\..*/.json/')"
if [ -f "$METADATA_FILE" ]; then
    echo "  📋 Metadata available:"
    cat "$METADATA_FILE" | jq -r '"  Size: " + .size + ", Checksum: " + .checksum[0:16] + "..."'
else
    echo "  ⚠️  No metadata file found"
fi

# Summary
echo -e "\n📊 Backup Summary:"
BACKUP_COUNT=$(find $BACKUP_DIR -name "acgs_pgp_db_*.gz*" -type f | wc -l)
echo "  Total backups: $BACKUP_COUNT"
echo "  Retention policy: 7 days"

if [ $BACKUP_AGE -le $MAX_AGE_HOURS ] && [ -n "$LATEST_BACKUP" ]; then
    echo "  Status: ✅ Backup system healthy"
    exit 0
else
    echo "  Status: ❌ Backup system needs attention"
    exit 1
fi
