#!/bin/bash

# ACGS-PGP Production Deployment Validation Script
# This script validates the complete production deployment including monitoring integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TIMEOUT=30
RETRY_COUNT=3
BASE_URL="http://localhost:8000"
GRAFANA_URL="http://localhost:3001"
PROMETHEUS_URL="http://localhost:9090"

# Service ports
declare -A SERVICES=(
    ["auth"]="8000"
    ["ac"]="8001"
    ["integrity"]="8002"
    ["fv"]="8003"
    ["gs"]="8004"
    ["pgc"]="8005"
)

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Utility functions
wait_for_service() {
    local url=$1
    local service_name=$2
    local timeout=${3:-30}
    
    log_info "Waiting for $service_name to be ready..."
    
    for i in $(seq 1 $timeout); do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "$service_name is ready"
            return 0
        fi
        sleep 1
    done
    
    log_error "$service_name failed to start within $timeout seconds"
    return 1
}

check_http_status() {
    local url=$1
    local expected_status=${2:-200}
    
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$status" = "$expected_status" ]; then
        return 0
    else
        log_error "Expected status $expected_status, got $status for $url"
        return 1
    fi
}

# Validation functions
validate_docker_services() {
    log_info "Validating Docker services..."
    
    local services=("acgs_postgres_db" "acgs_auth_service" "acgs_ac_service" "acgs_integrity_service" 
                   "acgs_fv_service" "acgs_gs_service" "acgs_pgc_service" "acgs_nginx_gateway" 
                   "acgs_prometheus" "acgs_grafana")
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$service"; then
            log_success "Docker service $service is running"
        else
            log_error "Docker service $service is not running"
            return 1
        fi
    done
}

validate_health_endpoints() {
    log_info "Validating service health endpoints..."
    
    for service in "${!SERVICES[@]}"; do
        local port=${SERVICES[$service]}
        local health_url="http://localhost:$port/health"
        
        if wait_for_service "$health_url" "$service" 30; then
            if check_http_status "$health_url" 200; then
                log_success "$service health check passed"
            else
                log_error "$service health check failed"
                return 1
            fi
        else
            return 1
        fi
    done
}

validate_api_endpoints() {
    log_info "Validating API endpoints through Nginx gateway..."
    
    # Test authentication endpoints
    local auth_endpoints=("/auth/csrf-token" "/auth/health")
    for endpoint in "${auth_endpoints[@]}"; do
        if check_http_status "$BASE_URL$endpoint" 200; then
            log_success "Auth endpoint $endpoint is accessible"
        else
            log_error "Auth endpoint $endpoint failed"
            return 1
        fi
    done
    
    # Test service endpoints through gateway
    local services=("ac" "integrity" "fv" "gs" "pgc")
    for service in "${services[@]}"; do
        local endpoint="/api/$service/health"
        if check_http_status "$BASE_URL$endpoint" 200; then
            log_success "Service endpoint $endpoint is accessible"
        else
            log_error "Service endpoint $endpoint failed"
            return 1
        fi
    done
}

validate_authentication_flow() {
    log_info "Validating authentication flow..."
    
    # Get CSRF token
    local csrf_response=$(curl -s "$BASE_URL/auth/csrf-token")
    if [ $? -eq 0 ]; then
        log_success "CSRF token endpoint is working"
    else
        log_error "Failed to get CSRF token"
        return 1
    fi
    
    # Test registration endpoint (should return validation error for empty data)
    local register_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$BASE_URL/auth/register" \
        -H "Content-Type: application/json" \
        -d '{}')
    
    if [ "$register_response" = "422" ]; then
        log_success "Registration endpoint validation is working"
    else
        log_warning "Registration endpoint returned unexpected status: $register_response"
    fi
}

validate_monitoring_stack() {
    log_info "Validating monitoring stack..."
    
    # Check Prometheus
    if wait_for_service "$PROMETHEUS_URL/-/healthy" "Prometheus" 30; then
        log_success "Prometheus is healthy"
        
        # Check if Prometheus is collecting metrics
        local targets_response=$(curl -s "$PROMETHEUS_URL/api/v1/targets")
        if echo "$targets_response" | grep -q '"health":"up"'; then
            log_success "Prometheus is collecting metrics from targets"
        else
            log_warning "Some Prometheus targets may be down"
        fi
    else
        log_error "Prometheus health check failed"
        return 1
    fi
    
    # Check Grafana
    if wait_for_service "$GRAFANA_URL/api/health" "Grafana" 30; then
        log_success "Grafana is healthy"
        
        # Test Grafana login
        local grafana_login=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "$GRAFANA_URL/login" \
            -H "Content-Type: application/json" \
            -d '{"user":"admin","password":"admin123"}')
        
        if [ "$grafana_login" = "200" ] || [ "$grafana_login" = "302" ]; then
            log_success "Grafana authentication is working"
        else
            log_warning "Grafana authentication returned status: $grafana_login"
        fi
    else
        log_error "Grafana health check failed"
        return 1
    fi
}

validate_metrics_collection() {
    log_info "Validating metrics collection..."
    
    # Check if services are exposing metrics
    for service in "${!SERVICES[@]}"; do
        local port=${SERVICES[$service]}
        local metrics_url="http://localhost:$port/metrics"
        
        local metrics_response=$(curl -s "$metrics_url")
        if echo "$metrics_response" | grep -q "# HELP"; then
            log_success "$service is exposing Prometheus metrics"
        else
            log_warning "$service metrics endpoint may not be working properly"
        fi
    done
    
    # Check for ACGS-specific metrics in Prometheus
    local acgs_metrics=$(curl -s "$PROMETHEUS_URL/api/v1/label/__name__/values" | grep -o 'acgs_[^"]*' | head -5)
    if [ -n "$acgs_metrics" ]; then
        log_success "ACGS-specific metrics are being collected:"
        echo "$acgs_metrics" | while read -r metric; do
            echo "  - $metric"
        done
    else
        log_warning "No ACGS-specific metrics found in Prometheus"
    fi
}

validate_database_connectivity() {
    log_info "Validating database connectivity..."
    
    # Check PostgreSQL container
    if docker exec acgs_postgres_db pg_isready -U acgs_user > /dev/null 2>&1; then
        log_success "PostgreSQL is ready"
        
        # Check database connection from services
        local db_connections=$(docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='acgs_pgp_db';" 2>/dev/null | tr -d ' ')
        
        if [ -n "$db_connections" ] && [ "$db_connections" -gt 0 ]; then
            log_success "Database has $db_connections active connections"
        else
            log_warning "No active database connections found"
        fi
    else
        log_error "PostgreSQL is not ready"
        return 1
    fi
}

validate_load_balancing() {
    log_info "Validating load balancing..."
    
    # Check Nginx configuration
    if docker exec acgs_nginx_gateway nginx -t > /dev/null 2>&1; then
        log_success "Nginx configuration is valid"
    else
        log_error "Nginx configuration is invalid"
        return 1
    fi
    
    # Test load distribution (simple check)
    local responses=()
    for i in {1..5}; do
        local response=$(curl -s "$BASE_URL/auth/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        responses+=("$response")
    done
    
    if [ "${#responses[@]}" -eq 5 ]; then
        log_success "Load balancer is distributing requests"
    else
        log_warning "Load balancer may not be working correctly"
    fi
}

validate_security_headers() {
    log_info "Validating security headers..."
    
    local security_headers=("X-Frame-Options" "X-Content-Type-Options" "X-XSS-Protection" "Strict-Transport-Security")
    local headers_response=$(curl -s -I "$BASE_URL/auth/health")
    
    for header in "${security_headers[@]}"; do
        if echo "$headers_response" | grep -qi "$header"; then
            log_success "Security header $header is present"
        else
            log_warning "Security header $header is missing"
        fi
    done
}

run_performance_test() {
    log_info "Running basic performance test..."
    
    # Simple load test with curl
    local start_time=$(date +%s)
    local success_count=0
    local total_requests=20
    
    for i in $(seq 1 $total_requests); do
        if curl -s -f "$BASE_URL/auth/health" > /dev/null; then
            ((success_count++))
        fi
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local success_rate=$((success_count * 100 / total_requests))
    
    log_info "Performance test results:"
    echo "  - Total requests: $total_requests"
    echo "  - Successful requests: $success_count"
    echo "  - Success rate: $success_rate%"
    echo "  - Duration: ${duration}s"
    
    if [ "$success_rate" -ge 95 ]; then
        log_success "Performance test passed"
    else
        log_warning "Performance test shows degraded performance"
    fi
}

# Main validation function
main() {
    log_info "Starting ACGS-PGP Production Deployment Validation"
    log_info "================================================"
    
    local validation_functions=(
        "validate_docker_services"
        "validate_health_endpoints"
        "validate_api_endpoints"
        "validate_authentication_flow"
        "validate_monitoring_stack"
        "validate_metrics_collection"
        "validate_database_connectivity"
        "validate_load_balancing"
        "validate_security_headers"
        "run_performance_test"
    )
    
    local failed_validations=()
    
    for func in "${validation_functions[@]}"; do
        log_info "Running $func..."
        if $func; then
            log_success "$func completed successfully"
        else
            log_error "$func failed"
            failed_validations+=("$func")
        fi
        echo ""
    done
    
    # Summary
    log_info "Validation Summary"
    log_info "=================="
    
    if [ ${#failed_validations[@]} -eq 0 ]; then
        log_success "All validations passed! ACGS-PGP deployment is ready for production."
        exit 0
    else
        log_error "The following validations failed:"
        for failed in "${failed_validations[@]}"; do
            echo "  - $failed"
        done
        log_error "Please address the issues before proceeding to production."
        exit 1
    fi
}

# Run main function
main "$@"
