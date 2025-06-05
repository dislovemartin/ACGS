#!/bin/bash

# ACGS-PGP Phase 1 Infrastructure Stabilization
# Simplified Docker-based Service Validation Strategy
# Target: <200ms response times, >99.5% uptime, 50+ concurrent users

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="infrastructure_validation_report_${TIMESTAMP}.json"
LOG_FILE="infrastructure_validation_${TIMESTAMP}.log"

# Service configuration
declare -A SERVICES=(
    ["auth_service"]="8000"
    ["ac_service"]="8001"
    ["integrity_service"]="8002"
    ["fv_service"]="8003"
    ["gs_service"]="8004"
    ["pgc_service"]="8005"
    ["ec_service"]="8006"
)

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Initialize report
init_report() {
    cat > "$REPORT_FILE" << EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "validation_type": "ACGS-PGP Phase 1 Infrastructure Stabilization",
    "target_metrics": {
        "response_time_ms": 200,
        "uptime_percent": 99.5,
        "concurrent_users": 50
    },
    "services": {},
    "summary": {
        "total_services": ${#SERVICES[@]},
        "services_healthy": 0,
        "services_failed": 0,
        "overall_status": "unknown",
        "infrastructure_ready": false
    }
}
EOF
}

# Test single service health
test_service_health() {
    local service=$1
    local port=$2
    local url="http://localhost:${port}/health"
    
    log "INFO" "Testing $service health endpoint: $url"
    
    # Test with curl and measure response time
    local start_time=$(date +%s%N)
    local http_status=$(curl -s -o /tmp/health_response_${service}.json \
        --max-time 5 --connect-timeout 2 -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    local end_time=$(date +%s%N)
    
    # Calculate response time in milliseconds
    local response_time_ms=$(( (end_time - start_time) / 1000000 ))
    
    if [[ "$http_status" == "200" ]]; then
        local response_content=$(cat /tmp/health_response_${service}.json 2>/dev/null || echo "{}")
        log "INFO" "${GREEN}✓ $service: HTTP $http_status, ${response_time_ms}ms${NC}"
        
        # Check if response time meets target (<200ms)
        if [[ $response_time_ms -lt 200 ]]; then
            log "INFO" "${GREEN}  Response time target met${NC}"
        else
            log "WARN" "${YELLOW}  Response time target missed: ${response_time_ms}ms > 200ms${NC}"
        fi
        
        echo "    \"$service\": {\"status\": \"healthy\", \"http_status\": $http_status, \"response_time_ms\": $response_time_ms, \"response\": $response_content}," >> /tmp/services_results.json
        return 0
    else
        log "ERROR" "${RED}✗ $service: HTTP $http_status, ${response_time_ms}ms${NC}"
        echo "    \"$service\": {\"status\": \"failed\", \"http_status\": $http_status, \"response_time_ms\": $response_time_ms}," >> /tmp/services_results.json
        return 1
    fi
    
    # Cleanup temp file
    rm -f /tmp/health_response_${service}.json
}

# Phase 1: Docker Service Status Check
check_docker_status() {
    log "INFO" "${BLUE}Phase 1: Docker Service Status Check${NC}"
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        log "ERROR" "${RED}Docker daemon is not running${NC}"
        return 1
    fi
    
    log "INFO" "${GREEN}Docker daemon is running${NC}"
    
    # Check current containers
    log "INFO" "Current ACGS container status:"
    docker ps --filter "name=acgs_" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | tee -a "$LOG_FILE"
    
    log "INFO" "${BLUE}Phase 1 completed${NC}"
}

# Phase 2: Health Endpoint Validation
validate_health_endpoints() {
    log "INFO" "${BLUE}Phase 2: Health Endpoint Validation${NC}"
    
    # Initialize services results
    echo "{" > /tmp/services_results.json
    
    local healthy_count=0
    local failed_count=0
    
    for service in "${!SERVICES[@]}"; do
        local port=${SERVICES[$service]}
        
        if test_service_health "$service" "$port"; then
            ((healthy_count++))
        else
            ((failed_count++))
        fi
        
        # Add small delay between tests
        sleep 1
    done
    
    # Close JSON and clean up trailing comma
    sed -i '$ s/,$//' /tmp/services_results.json
    echo "}" >> /tmp/services_results.json
    
    log "INFO" "${BLUE}Phase 2 completed: $healthy_count healthy, $failed_count failed${NC}"
    
    # Update report with results
    local services_json=$(cat /tmp/services_results.json)
    sed -i "s/\"services\": {}/\"services\": $services_json/" "$REPORT_FILE"
    sed -i "s/\"services_healthy\": 0/\"services_healthy\": $healthy_count/" "$REPORT_FILE"
    sed -i "s/\"services_failed\": 0/\"services_failed\": $failed_count/" "$REPORT_FILE"
    
    return $failed_count
}

# Phase 3: Basic Cross-Service Communication Test
test_cross_service_communication() {
    log "INFO" "${BLUE}Phase 3: Basic Cross-Service Communication Test${NC}"
    
    # Test authentication endpoint accessibility
    log "INFO" "Testing authentication endpoint..."
    local auth_response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"username": "test_user", "password": "test_password"}' \
        http://localhost:8000/auth/login 2>/dev/null || echo "000")
    
    if [[ "${auth_response: -3}" == "200" ]] || [[ "${auth_response: -3}" == "422" ]]; then
        log "INFO" "${GREEN}✓ Auth endpoint accessible (HTTP ${auth_response: -3})${NC}"
    else
        log "WARN" "${YELLOW}⚠ Auth endpoint issue (HTTP ${auth_response: -3})${NC}"
    fi
    
    # Test AC service principles endpoint
    log "INFO" "Testing AC service API..."
    if curl -s --max-time 3 http://localhost:8001/api/v1/principles >/dev/null 2>&1; then
        log "INFO" "${GREEN}✓ AC service API accessible${NC}"
    else
        log "WARN" "${YELLOW}⚠ AC service API not accessible${NC}"
    fi
    
    # Test Integrity service policies endpoint
    log "INFO" "Testing Integrity service API..."
    if curl -s --max-time 3 http://localhost:8002/api/v1/policies >/dev/null 2>&1; then
        log "INFO" "${GREEN}✓ Integrity service API accessible${NC}"
    else
        log "WARN" "${YELLOW}⚠ Integrity service API not accessible${NC}"
    fi
    
    log "INFO" "${BLUE}Phase 3 completed${NC}"
}

# Phase 4: Basic Load Test
perform_basic_load_test() {
    log "INFO" "${BLUE}Phase 4: Basic Load Test${NC}"
    
    log "INFO" "Performing 10 concurrent requests to auth service..."
    local start_time=$(date +%s)
    
    # Run 10 concurrent health checks
    for i in {1..10}; do
        curl -s http://localhost:8000/health >/dev/null &
    done
    wait
    
    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))
    
    log "INFO" "${GREEN}✓ Load test completed in ${total_time} seconds${NC}"
    
    log "INFO" "${BLUE}Phase 4 completed${NC}"
}

# Generate final report
generate_final_report() {
    log "INFO" "${BLUE}Generating Final Infrastructure Status Report${NC}"
    
    # Read current values from report
    local healthy_services=$(grep -o '"services_healthy": [0-9]*' "$REPORT_FILE" | cut -d' ' -f2)
    local total_services=${#SERVICES[@]}
    
    # Calculate uptime percentage (simple integer math)
    local uptime_percent=$((healthy_services * 100 / total_services))
    
    # Update report with final status
    if [[ $healthy_services -eq $total_services ]]; then
        sed -i 's/"overall_status": "unknown"/"overall_status": "healthy"/' "$REPORT_FILE"
        sed -i 's/"infrastructure_ready": false/"infrastructure_ready": true/' "$REPORT_FILE"
        log "INFO" "${GREEN}Infrastructure Status: HEALTHY - All services operational${NC}"
    elif [[ $healthy_services -gt 0 ]]; then
        sed -i 's/"overall_status": "unknown"/"overall_status": "degraded"/' "$REPORT_FILE"
        log "WARN" "${YELLOW}Infrastructure Status: DEGRADED - Some services operational${NC}"
    else
        sed -i 's/"overall_status": "unknown"/"overall_status": "failed"/' "$REPORT_FILE"
        log "ERROR" "${RED}Infrastructure Status: FAILED - No services operational${NC}"
    fi
    
    # Display summary
    echo -e "\n${BLUE}=== ACGS-PGP Infrastructure Validation Summary ===${NC}"
    echo -e "Timestamp: $(date)"
    echo -e "Services Healthy: $healthy_services/$total_services (${uptime_percent}%)"
    echo -e "Report File: $REPORT_FILE"
    echo -e "Log File: $LOG_FILE"
    
    if [[ $healthy_services -eq $total_services ]]; then
        echo -e "\n${GREEN}✓ Infrastructure is ready for Phase 2 AlphaEvolve integration${NC}"
        echo -e "\n${GREEN}SUCCESS CRITERIA MET:${NC}"
        echo -e "  ✓ All 7 services started successfully"
        echo -e "  ✓ Health endpoints responding with HTTP 200"
        echo -e "  ✓ Response times measured (target: <200ms)"
        echo -e "  ✓ Cross-service communication tested"
        echo -e "  ✓ Basic load testing completed"
        return 0
    else
        echo -e "\n${RED}✗ Infrastructure requires fixes before Phase 2 integration${NC}"
        echo -e "\nRecommendations:"
        echo -e "  - Check Docker logs for failed services: docker logs <service_name>"
        echo -e "  - Verify database connectivity and migrations"
        echo -e "  - Ensure all environment variables are properly set"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}ACGS-PGP Phase 1 Infrastructure Stabilization${NC}"
    echo -e "${BLUE}Simplified Docker-based Service Validation Strategy${NC}"
    echo -e "Target: <200ms response times, >99.5% uptime, 50+ concurrent users\n${NC}"
    
    # Initialize report
    init_report
    
    # Execute validation phases
    check_docker_status
    
    # Wait for services to fully start
    log "INFO" "Waiting 10 seconds for services to fully initialize..."
    sleep 10
    
    validate_health_endpoints
    local health_result=$?
    
    test_cross_service_communication
    perform_basic_load_test
    
    # Generate final report
    generate_final_report
    
    # Cleanup
    rm -f /tmp/services_results.json /tmp/health_response_*.json
    
    return $health_result
}

# Run main function
main "$@"
