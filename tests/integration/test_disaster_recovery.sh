#!/bin/bash
# Test disaster recovery procedures

echo "🧪 Testing Disaster Recovery Procedures"
echo "======================================="

echo "1. Testing backup creation..."
./backup_database_comprehensive.sh

echo -e "\n2. Testing backup monitoring..."
./monitor_backups.sh

echo -e "\n3. Testing health checks..."
./health_check.sh

echo -e "\n✅ Disaster recovery test completed"
