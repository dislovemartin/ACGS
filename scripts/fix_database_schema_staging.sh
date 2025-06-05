#!/bin/bash

# ACGS Phase 3 - Database Schema Fix for Staging
# Fixes UUID/INTEGER datatype mismatch in refresh_tokens table

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed or not in PATH"
        exit 1
    fi
    success "Docker Compose is available"
}

# Check if staging environment is running
check_staging_environment() {
    log "Checking staging environment status..."
    
    if docker-compose -f docker-compose.staging.yml ps | grep -q "acgs-postgres-staging"; then
        success "Staging PostgreSQL container is running"
    else
        warning "Staging PostgreSQL container is not running. Starting it..."
        docker-compose -f docker-compose.staging.yml up -d postgres
        sleep 10
    fi
}

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    log "Waiting for PostgreSQL to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.staging.yml exec -T postgres pg_isready -U acgs_user -d acgs_staging > /dev/null 2>&1; then
            success "PostgreSQL is ready"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: PostgreSQL not ready yet, waiting..."
        sleep 2
        ((attempt++))
    done
    
    error "PostgreSQL failed to become ready after $max_attempts attempts"
    return 1
}

# Backup current database
backup_database() {
    log "Creating database backup before migration..."
    
    local backup_file="backup_staging_$(date +%Y%m%d_%H%M%S).sql"
    
    docker-compose -f docker-compose.staging.yml exec -T postgres pg_dump -U acgs_user -d acgs_staging > "$backup_file"
    
    if [ -f "$backup_file" ]; then
        success "Database backup created: $backup_file"
    else
        error "Failed to create database backup"
        return 1
    fi
}

# Check current database schema
check_current_schema() {
    log "Checking current database schema..."
    
    # Check if users table exists and its structure
    local users_schema=$(docker-compose -f docker-compose.staging.yml exec -T postgres psql -U acgs_user -d acgs_staging -c "\d users" 2>/dev/null || echo "Table not found")
    
    if echo "$users_schema" | grep -q "integer"; then
        warning "Users table uses INTEGER for id column - migration needed"
        return 1
    elif echo "$users_schema" | grep -q "uuid"; then
        success "Users table already uses UUID for id column"
        return 0
    else
        warning "Users table structure unclear or table doesn't exist"
        return 1
    fi
}

# Run Alembic migration
run_migration() {
    log "Running Alembic migration to fix UUID/INTEGER mismatch..."
    
    # First, check if alembic-runner service exists in staging
    if ! docker-compose -f docker-compose.staging.yml config | grep -q "alembic-runner"; then
        warning "Alembic runner not configured in staging. Running migration directly..."
        
        # Run migration using a temporary container
        docker run --rm \
            --network acgs-master_acgs-staging \
            -v "$(pwd)/migrations:/app/migrations" \
            -v "$(pwd)/src/backend/shared:/app/shared" \
            -e DATABASE_URL="postgresql+asyncpg://acgs_user:${POSTGRES_PASSWORD}@acgs-postgres-staging:5432/acgs_staging" \
            python:3.11-slim \
            bash -c "
                pip install alembic asyncpg sqlalchemy[asyncio] psycopg2-binary
                cd /app
                alembic upgrade head
            "
    else
        # Use the configured alembic-runner service
        docker-compose -f docker-compose.staging.yml exec alembic-runner alembic upgrade head
    fi
    
    if [ $? -eq 0 ]; then
        success "Database migration completed successfully"
    else
        error "Database migration failed"
        return 1
    fi
}

# Verify migration success
verify_migration() {
    log "Verifying migration success..."
    
    # Check if users table now uses UUID
    local users_schema=$(docker-compose -f docker-compose.staging.yml exec -T postgres psql -U acgs_user -d acgs_staging -c "\d users")
    
    if echo "$users_schema" | grep -q "uuid"; then
        success "Users table now uses UUID for id column"
    else
        error "Migration verification failed - users table still uses INTEGER"
        return 1
    fi
    
    # Check if refresh_tokens table has UUID foreign key
    local refresh_tokens_schema=$(docker-compose -f docker-compose.staging.yml exec -T postgres psql -U acgs_user -d acgs_staging -c "\d refresh_tokens")
    
    if echo "$refresh_tokens_schema" | grep -q "uuid"; then
        success "Refresh tokens table now uses UUID for user_id column"
    else
        error "Migration verification failed - refresh_tokens table still uses INTEGER"
        return 1
    fi
    
    # Test foreign key constraint
    log "Testing foreign key constraint..."
    local constraint_test=$(docker-compose -f docker-compose.staging.yml exec -T postgres psql -U acgs_user -d acgs_staging -c "
        SELECT conname, contype 
        FROM pg_constraint 
        WHERE conrelid = 'refresh_tokens'::regclass 
        AND contype = 'f'
    " 2>/dev/null || echo "")
    
    if echo "$constraint_test" | grep -q "refresh_tokens_user_id_fkey"; then
        success "Foreign key constraint is properly configured"
    else
        warning "Foreign key constraint may need manual verification"
    fi
}

# Main execution
main() {
    log "Starting ACGS Phase 3 Database Schema Fix for Staging"
    log "=================================================="
    
    # Load environment variables
    if [ -f "config/env/staging.env" ]; then
        source config/env/staging.env
        success "Loaded staging environment variables"
    else
        error "Staging environment file not found: config/env/staging.env"
        exit 1
    fi
    
    # Execute steps
    check_docker_compose
    check_staging_environment
    wait_for_postgres
    
    # Check if migration is needed
    if check_current_schema; then
        success "Database schema is already correct - no migration needed"
        exit 0
    fi
    
    backup_database
    run_migration
    verify_migration
    
    success "Database schema fix completed successfully!"
    log "Next steps:"
    log "1. Restart Integrity service to test database connectivity"
    log "2. Enable and deploy FV, GS, and PGC services"
    log "3. Run comprehensive staging validation"
}

# Execute main function
main "$@"
