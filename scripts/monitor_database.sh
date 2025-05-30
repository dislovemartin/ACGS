#!/bin/bash
# ACGS-PGP Database Monitoring Script

DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="acgs_pgp_db"
DB_USER="acgs_user"

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
echo -e "\n2. Database size information..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
    pg_database.datname as database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) as size
FROM pg_database 
WHERE datname = '$DB_NAME';"

# Table information
echo -e "\n3. Table information..."
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
echo -e "\n4. Active connections..."
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
echo -e "\n5. Migration status..."
docker-compose exec -T alembic-runner alembic current

echo -e "\n✅ Database health check complete"
