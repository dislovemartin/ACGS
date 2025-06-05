#!/bin/bash

# ACGS Phase 3 - Fixed Staging Deployment Script
# Addresses database authentication and environment variable issues

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.staging.yml"
ENV_FILE="$PROJECT_ROOT/.env.staging"

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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Load environment variables
    set -a
    source "$ENV_FILE"
    set +a
    
    # Validate critical environment variables
    if [ -z "${POSTGRES_PASSWORD:-}" ]; then
        error "POSTGRES_PASSWORD not set in environment file"
        exit 1
    fi
    
    if [ -z "${JWT_SECRET_KEY:-}" ]; then
        error "JWT_SECRET_KEY not set in environment file"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Clean up any existing containers
cleanup_existing() {
    log "Cleaning up existing containers..."
    
    # Use explicit env file
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans || true
    docker system prune -f || true
    
    success "Cleanup completed"
}

# Deploy infrastructure services
deploy_infrastructure() {
    log "Deploying infrastructure services (PostgreSQL, Redis, OPA)..."
    
    # Deploy with explicit env file
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis opa
    
    # Wait for PostgreSQL to be ready
    log "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        log "Attempt $i/30: Waiting for PostgreSQL..."
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-acgs_user}" -d "${POSTGRES_DB:-acgs_staging}" >/dev/null 2>&1; then
            success "PostgreSQL is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            error "PostgreSQL failed to start after 30 attempts"
            exit 1
        fi
        sleep 5
    done
    
    # Check Redis
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli ping >/dev/null 2>&1; then
        success "Redis is healthy"
    else
        warning "Redis health check failed, but continuing..."
    fi
    
    success "Infrastructure services deployed successfully"
}

# Deploy core services
deploy_core_services() {
    log "Deploying core services (AC, Integrity)..."
    
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d ac_service integrity_service
    
    # Wait for services to be healthy
    log "Waiting for core services to be healthy..."
    sleep 30
    
    # Check AC service health
    for i in {1..10}; do
        if curl -f http://localhost:8011/health >/dev/null 2>&1; then
            success "AC Service is healthy"
            break
        fi
        if [ $i -eq 10 ]; then
            warning "AC Service health check failed"
        fi
        sleep 5
    done
    
    # Check Integrity service health
    for i in {1..10}; do
        if curl -f http://localhost:8012/health >/dev/null 2>&1; then
            success "Integrity Service is healthy"
            break
        fi
        if [ $i -eq 10 ]; then
            warning "Integrity Service health check failed"
        fi
        sleep 5
    done
    
    success "Core services deployed"
}

# Deploy remaining services
deploy_remaining_services() {
    log "Deploying remaining services (FV, GS, PGC)..."
    
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d fv_service gs_service pgc_service
    
    # Wait for services to be healthy
    log "Waiting for remaining services to be healthy..."
    sleep 30
    
    success "All services deployed"
}

# Validate deployment
validate_deployment() {
    log "Validating deployment..."
    
    # Check all containers are running
    local containers=(
        "acgs-postgres-staging"
        "acgs-redis-staging"
        "acgs-opa-staging"
        "acgs-ac-service-staging"
        "acgs-integrity-service-staging"
        "acgs-fv-service-staging"
        "acgs-gs-service-staging"
        "acgs-pgc-service-staging"
    )
    
    local healthy_count=0
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
            success "$container is running"
            ((healthy_count++))
        else
            error "$container is not running"
        fi
    done
    
    log "Deployment validation: $healthy_count/${#containers[@]} services running"
    
    if [ $healthy_count -eq ${#containers[@]} ]; then
        success "All services are running successfully!"
        return 0
    else
        error "Some services failed to start"
        return 1
    fi
}

# Generate deployment report
generate_report() {
    log "Generating deployment report..."
    
    local report_file="$PROJECT_ROOT/logs/staging_deployment_report_$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p "$(dirname "$report_file")"
    
    {
        echo "ACGS Phase 3 Staging Deployment Report"
        echo "======================================"
        echo "Timestamp: $(date)"
        echo ""
        echo "Container Status:"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
        echo ""
        echo "Service Health Checks:"
        echo "- AC Service: http://localhost:8011/health"
        echo "- Integrity Service: http://localhost:8012/health"
        echo "- FV Service: http://localhost:8013/health"
        echo "- GS Service: http://localhost:8014/health"
        echo "- PGC Service: http://localhost:8015/health"
        echo ""
        echo "Database Connection Test:"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres psql -U "${POSTGRES_USER:-acgs_user}" -d "${POSTGRES_DB:-acgs_staging}" -c "SELECT version();" || echo "Database connection failed"
    } > "$report_file"
    
    success "Deployment report generated: $report_file"
}

# Main deployment function
main() {
    log "Starting ACGS Phase 3 Complete Staging Deployment"
    log "================================================="
    
    check_prerequisites
    cleanup_existing
    deploy_infrastructure
    deploy_core_services
    deploy_remaining_services
    
    if validate_deployment; then
        generate_report
        success "Staging deployment completed successfully!"
        log "Next steps:"
        log "1. Deploy monitoring infrastructure (Prometheus/Grafana)"
        log "2. Run load testing to validate performance requirements"
        log "3. Execute security compliance checks"
        exit 0
    else
        error "Staging deployment failed. Check logs for details."
        exit 1
    fi
}

# Run main function
main "$@"
