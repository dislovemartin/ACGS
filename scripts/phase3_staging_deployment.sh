#!/bin/bash

# ACGS Phase 3 Staging Environment Deployment Script
# Deploys validated Phase 3 implementation to staging environment
# Mirrors production specifications for final validation

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STAGING_ENV_FILE="$PROJECT_ROOT/.env.staging"
DEPLOYMENT_LOG="$PROJECT_ROOT/logs/staging_deployment_$(date +%Y%m%d_%H%M%S).log"
VALIDATION_REPORT="$PROJECT_ROOT/staging_validation_report.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Initialize deployment metrics
DEPLOYMENT_START_TIME=$(date +%s)
DEPLOYMENT_METRICS="{
    \"deployment_start\": \"$(date -Iseconds)\",
    \"environment\": \"staging\",
    \"phase\": \"3\",
    \"services_deployed\": [],
    \"performance_metrics\": {},
    \"security_validation\": {},
    \"log_directory\": \"\",
    \"log_files\": [],
    \"issues_encountered\": []
}"

# Function to update metrics
update_metrics() {
    local key="$1"
    local value="$2"
    echo "$DEPLOYMENT_METRICS" | jq ".$key = $value" > /tmp/metrics.json
    DEPLOYMENT_METRICS=$(cat /tmp/metrics.json)
}

# Capture docker logs when deployment fails
collect_docker_logs() {
    LOG_CAPTURE_DIR="$PROJECT_ROOT/logs/staging/docker_logs_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$LOG_CAPTURE_DIR"
    local services
    services=$(docker-compose -f docker-compose.prod.yml --env-file "$STAGING_ENV_FILE" ps --services 2>/dev/null || true)
    if [ -z "$services" ]; then
        echo "No services found" > "$LOG_CAPTURE_DIR/no_services.log"
    else
        for svc in $services; do
            docker-compose -f docker-compose.prod.yml --env-file "$STAGING_ENV_FILE" logs "$svc" > "$LOG_CAPTURE_DIR/${svc}.log" 2>&1 || true
        done
    fi

    local file_list
    file_list=$(ls -1 "$LOG_CAPTURE_DIR" | sed 's/.*/"&"/' | paste -sd ',' -)
    update_metrics "log_directory" "\"$LOG_CAPTURE_DIR\""
    update_metrics "log_files" "[$file_list]"
}

# Trap any error to collect logs before exiting
handle_failure() {
    local exit_code=$?
    error "Deployment failed with exit code $exit_code"
    collect_docker_logs
    log "Docker logs saved to $LOG_CAPTURE_DIR"
    exit $exit_code
}

trap handle_failure ERR

# Function to check system requirements
check_system_requirements() {
    log "🔍 Checking staging system requirements..."
    
    # Check CPU cores
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt 8 ]; then
        warning "CPU cores: $CPU_CORES (recommended: 8+)"
    else
        success "CPU cores: $CPU_CORES ✅"
    fi
    
    # Check memory
    MEMORY_GB=$(LANG=C free -g | awk '/^Mem:/{print $2}')
    if [ -z "$MEMORY_GB" ]; then
        MEMORY_GB=$(LANG=C free -m | awk '/^Mem:/{print int($2/1024)}')
    fi
    if [ -z "$MEMORY_GB" ] || [ "$MEMORY_GB" -lt 16 ]; then
        warning "Memory: ${MEMORY_GB:-Unknown}GB (recommended: 16GB+)"
    else
        success "Memory: ${MEMORY_GB}GB ✅"
    fi
    
    # Check disk space
    DISK_SPACE=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$DISK_SPACE" -lt 100 ]; then
        warning "Disk space: ${DISK_SPACE}GB (recommended: 100GB+)"
    else
        success "Disk space: ${DISK_SPACE}GB ✅"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker not found. Please install Docker."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    success "System requirements validation completed"
}

# Function to setup staging environment
setup_staging_environment() {
    log "🏗️ Setting up staging environment..."
    
    # Check if staging environment file exists
    if [ ! -f "$STAGING_ENV_FILE" ]; then
        error "Staging environment file not found: $STAGING_ENV_FILE"
        error "Please create the staging environment file first."
        exit 1
    fi

    # Export staging environment variables for Docker Compose
    export $(grep -v '^#' "$STAGING_ENV_FILE" | xargs)
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/data/staging"
    mkdir -p "$PROJECT_ROOT/logs/staging"
    mkdir -p "$PROJECT_ROOT/backups/staging"
    
    success "Staging environment setup completed"
}

# Function to deploy infrastructure services
deploy_infrastructure() {
    log "🚀 Deploying infrastructure services..."
    
    # Stop any existing services
    docker-compose -f docker-compose.prod.yml --env-file "$STAGING_ENV_FILE" down --remove-orphans || true

    # Deploy database and cache first
    log "Starting PostgreSQL and Redis..."
    docker-compose -f docker-compose.prod.yml --env-file "$STAGING_ENV_FILE" up -d postgres redis
    
    # Wait for infrastructure to be ready
    log "Waiting for infrastructure services to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.prod.yml --env-file "$STAGING_ENV_FILE" exec -T postgres pg_isready -U acgs_user -d acgs_staging > /dev/null 2>&1; then
            success "PostgreSQL is ready"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error "PostgreSQL failed to start within timeout"
            exit 1
        fi
        
        log "Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    # Check Redis
    if docker-compose -f docker-compose.prod.yml --env-file "$STAGING_ENV_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        success "Redis is ready"
    else
        error "Redis failed to start"
        exit 1
    fi
    
    update_metrics "services_deployed" '["postgres", "redis"]'
    success "Infrastructure services deployed successfully"
}

# Function to deploy ACGS services
deploy_acgs_services() {
    log "🔧 Deploying ACGS services..."
    
    # Deploy OPA first
    log "Starting OPA server..."
    docker-compose -f docker-compose.prod.yml --env-file "$STAGING_ENV_FILE" up -d opa
    
    # Wait for OPA to be ready
    sleep 30
    if ! curl -f http://localhost:8191/health > /dev/null 2>&1; then
        error "OPA server failed to start"
        exit 1
    fi
    success "OPA server is ready"
    
    # Deploy core services in dependency order
    local services=("ac_service" "integrity_service" "fv_service" "gs_service" "pgc_service")
    
    for service in "${services[@]}"; do
        log "Starting $service..."
        docker-compose -f docker-compose.prod.yml --env-file "$STAGING_ENV_FILE" up -d "$service"
        
        # Wait for service to be healthy
        local port=""
        case $service in
            "ac_service") port="8011" ;;
            "integrity_service") port="8012" ;;
            "fv_service") port="8013" ;;
            "gs_service") port="8014" ;;
            "pgc_service") port="8015" ;;
        esac
        
        local max_attempts=20
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -f "http://localhost:$port/health" > /dev/null 2>&1; then
                success "$service is ready on port $port"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                error "$service failed to start within timeout"
                exit 1
            fi
            
            log "Waiting for $service... (attempt $attempt/$max_attempts)"
            sleep 15
            ((attempt++))
        done
    done
    
    # Deploy Nginx load balancer
    log "Starting Nginx load balancer..."
    docker-compose -f docker-compose.prod.yml --env-file "$STAGING_ENV_FILE" up -d nginx
    
    update_metrics "services_deployed" '["postgres", "redis", "opa", "ac_service", "integrity_service", "fv_service", "gs_service", "pgc_service", "nginx"]'
    success "All ACGS services deployed successfully"
}

# Function to deploy monitoring stack
deploy_monitoring() {
    log "📊 Deploying monitoring stack..."
    
    # Deploy monitoring services
    docker-compose -f docker-compose-monitoring.yml up -d
    
    # Wait for monitoring services
    sleep 60
    
    # Verify Prometheus
    if curl -f http://localhost:9090/api/v1/targets > /dev/null 2>&1; then
        success "Prometheus is ready"
    else
        error "Prometheus failed to start"
        exit 1
    fi
    
    # Verify Grafana
    if curl -f http://localhost:3002/api/health > /dev/null 2>&1; then
        success "Grafana is ready"
    else
        error "Grafana failed to start"
        exit 1
    fi
    
    success "Monitoring stack deployed successfully"
}

# Main deployment function
main() {
    log "🚀 Starting ACGS Phase 3 Staging Deployment"
    log "=============================================="
    
    check_system_requirements
    setup_staging_environment
    deploy_infrastructure
    deploy_acgs_services
    deploy_monitoring
    
    local deployment_end_time=$(date +%s)
    local deployment_duration=$((deployment_end_time - DEPLOYMENT_START_TIME))
    
    update_metrics "deployment_end" "\"$(date -Iseconds)\""
    update_metrics "deployment_duration_seconds" "$deployment_duration"
    
    # Save deployment metrics
    echo "$DEPLOYMENT_METRICS" > "$VALIDATION_REPORT"
    
    success "🎉 ACGS Phase 3 Staging Deployment Complete!"
    log "=============================================="
    log "Deployment Duration: ${deployment_duration} seconds"
    log "Validation Report: $VALIDATION_REPORT"
    log "Next Step: Run comprehensive validation tests"
    
    # Display service URLs
    echo ""
    log "📋 Service Endpoints:"
    log "  AC Service:        http://localhost:8011"
    log "  Integrity Service: http://localhost:8012"
    log "  FV Service:        http://localhost:8013"
    log "  GS Service:        http://localhost:8014"
    log "  PGC Service:       http://localhost:8015"
    log "  Prometheus:        http://localhost:9090"
    log "  Grafana:           http://localhost:3002"
    log "  Load Balancer:     http://localhost:8080"
}

# Run main function
main "$@"
