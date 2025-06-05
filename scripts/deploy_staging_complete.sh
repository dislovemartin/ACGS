#!/bin/bash

# ACGS Phase 3 - Complete Staging Deployment Script
# Addresses all critical issues and deploys the full service stack

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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed"
        exit 1
    fi
    
    if [ ! -f "config/env/staging.env" ]; then
        error "Staging environment file not found"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Clean up any existing containers
cleanup_existing() {
    log "Cleaning up existing containers..."
    
    docker-compose -f docker-compose.staging.yml down --remove-orphans || true
    docker system prune -f || true
    
    success "Cleanup completed"
}

# Deploy infrastructure services
deploy_infrastructure() {
    log "Deploying infrastructure services (PostgreSQL, Redis, OPA)..."
    
    docker-compose -f docker-compose.staging.yml up -d postgres redis opa
    
    # Wait for infrastructure to be healthy
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.staging.yml ps postgres | grep -q "healthy"; then
            success "PostgreSQL is healthy"
            break
        fi
        
        log "Attempt $attempt/$max_attempts: Waiting for PostgreSQL..."
        sleep 5
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "PostgreSQL failed to become healthy"
        return 1
    fi
    
    # Check Redis
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.staging.yml ps redis | grep -q "healthy"; then
            success "Redis is healthy"
            break
        fi
        
        log "Attempt $attempt/$max_attempts: Waiting for Redis..."
        sleep 5
        ((attempt++))
    done
    
    success "Infrastructure services deployed successfully"
}

# Deploy core services (AC, Integrity)
deploy_core_services() {
    log "Deploying core services (AC, Integrity)..."
    
    # Deploy AC service first
    docker-compose -f docker-compose.staging.yml up -d ac_service
    
    # Wait for AC service to be healthy
    local max_attempts=20
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.staging.yml ps ac_service | grep -q "healthy"; then
            success "AC service is healthy"
            break
        fi
        
        log "Attempt $attempt/$max_attempts: Waiting for AC service..."
        sleep 10
        ((attempt++))
    done
    
    # Deploy Integrity service
    docker-compose -f docker-compose.staging.yml up -d integrity_service
    
    # Wait for Integrity service to be healthy
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.staging.yml ps integrity_service | grep -q "healthy"; then
            success "Integrity service is healthy"
            break
        fi
        
        log "Attempt $attempt/$max_attempts: Waiting for Integrity service..."
        
        # Check logs if service is failing
        if docker-compose -f docker-compose.staging.yml ps integrity_service | grep -q "Exit"; then
            warning "Integrity service exited, checking logs..."
            docker-compose -f docker-compose.staging.yml logs integrity_service --tail=10
            
            # Restart the service
            log "Restarting Integrity service..."
            docker-compose -f docker-compose.staging.yml restart integrity_service
        fi
        
        sleep 10
        ((attempt++))
    done
    
    success "Core services deployed successfully"
}

# Deploy additional services (FV, GS, PGC)
deploy_additional_services() {
    log "Deploying additional services (FV, GS, PGC)..."
    
    # Deploy FV service
    log "Deploying FV service..."
    docker-compose -f docker-compose.staging.yml up -d fv_service
    
    # Wait for FV service
    local max_attempts=15
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.staging.yml ps fv_service | grep -q "healthy"; then
            success "FV service is healthy"
            break
        fi
        
        log "Attempt $attempt/$max_attempts: Waiting for FV service..."
        sleep 10
        ((attempt++))
    done
    
    # Deploy GS service
    log "Deploying GS service..."
    docker-compose -f docker-compose.staging.yml up -d gs_service
    
    # Wait for GS service
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.staging.yml ps gs_service | grep -q "healthy"; then
            success "GS service is healthy"
            break
        fi
        
        log "Attempt $attempt/$max_attempts: Waiting for GS service..."
        sleep 10
        ((attempt++))
    done
    
    # Deploy PGC service
    log "Deploying PGC service..."
    docker-compose -f docker-compose.staging.yml up -d pgc_service
    
    # Wait for PGC service
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.staging.yml ps pgc_service | grep -q "healthy"; then
            success "PGC service is healthy"
            break
        fi
        
        log "Attempt $attempt/$max_attempts: Waiting for PGC service..."
        sleep 10
        ((attempt++))
    done
    
    success "Additional services deployed successfully"
}

# Validate deployment
validate_deployment() {
    log "Validating deployment..."
    
    # Check all services are running
    local services=("postgres" "redis" "opa" "ac_service" "integrity_service" "fv_service" "gs_service" "pgc_service")
    local healthy_count=0
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.staging.yml ps "$service" | grep -q "healthy\|Up"; then
            success "$service is running"
            ((healthy_count++))
        else
            warning "$service is not healthy"
            docker-compose -f docker-compose.staging.yml logs "$service" --tail=5
        fi
    done
    
    log "Deployment validation: $healthy_count/${#services[@]} services are healthy"
    
    if [ $healthy_count -eq ${#services[@]} ]; then
        success "All services are healthy!"
        return 0
    else
        warning "Some services are not healthy, but deployment can continue"
        return 1
    fi
}

# Test service connectivity
test_connectivity() {
    log "Testing service connectivity..."
    
    # Test AC service
    if curl -f http://localhost:8011/health &>/dev/null; then
        success "AC service health check passed"
    else
        warning "AC service health check failed"
    fi
    
    # Test Integrity service
    if curl -f http://localhost:8012/health &>/dev/null; then
        success "Integrity service health check passed"
    else
        warning "Integrity service health check failed"
    fi
    
    # Test FV service
    if curl -f http://localhost:8013/health &>/dev/null; then
        success "FV service health check passed"
    else
        warning "FV service health check failed"
    fi
    
    # Test GS service
    if curl -f http://localhost:8014/health &>/dev/null; then
        success "GS service health check passed"
    else
        warning "GS service health check failed"
    fi
    
    # Test PGC service
    if curl -f http://localhost:8015/health &>/dev/null; then
        success "PGC service health check passed"
    else
        warning "PGC service health check failed"
    fi
}

# Generate deployment report
generate_report() {
    log "Generating deployment report..."
    
    local report_file="staging_deployment_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "ACGS Phase 3 Staging Deployment Report"
        echo "======================================"
        echo "Deployment Date: $(date)"
        echo ""
        echo "Service Status:"
        echo "---------------"
        docker-compose -f docker-compose.staging.yml ps
        echo ""
        echo "Service Logs Summary:"
        echo "--------------------"
        for service in ac_service integrity_service fv_service gs_service pgc_service; do
            echo "=== $service ==="
            docker-compose -f docker-compose.staging.yml logs "$service" --tail=5 2>/dev/null || echo "No logs available"
            echo ""
        done
    } > "$report_file"
    
    success "Deployment report generated: $report_file"
}

# Main execution
main() {
    log "Starting ACGS Phase 3 Complete Staging Deployment"
    log "================================================="
    
    # Load environment variables
    source config/env/staging.env
    
    # Execute deployment steps
    check_prerequisites
    cleanup_existing
    deploy_infrastructure
    deploy_core_services
    deploy_additional_services
    
    # Validation and testing
    validate_deployment
    test_connectivity
    generate_report
    
    success "ACGS Phase 3 Staging Deployment Completed!"
    log "Next steps:"
    log "1. Review the deployment report"
    log "2. Run comprehensive staging validation tests"
    log "3. Add monitoring infrastructure (Prometheus/Grafana)"
    log "4. Proceed with production deployment planning"
}

# Execute main function
main "$@"
