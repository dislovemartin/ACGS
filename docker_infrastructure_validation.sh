#!/bin/bash

# ACGS-PGP Phase 1 Infrastructure Stabilization
# Docker-based Service Validation Strategy
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
    ["postgres_db"]="5433"
    ["auth_service"]="8000"
    ["ac_service"]="8001"
    ["integrity_service"]="8002"
    ["fv_service"]="8003"
    ["gs_service"]="8004"
    ["pgc_service"]="8005"
    ["ec_service"]="8006"
)

declare -A SERVICE_HEALTH_ENDPOINTS=(
    ["auth_service"]="/health"
    ["ac_service"]="/health"
    ["integrity_service"]="/health"
    ["fv_service"]="/health"
    ["gs_service"]="/health"
    ["pgc_service"]="/health"
    ["ec_service"]="/health"
)

# Initialize report structure
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
    "phases": {
        "docker_startup": {},
        "health_endpoints": {},
        "cross_service_communication": {},
        "performance_assessment": {}
    },
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

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Update JSON report
update_report() {
    local path=$1
    local value=$2
    jq "$path = $value" "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
}

# Phase 1: Docker Service Startup Validation
validate_docker_startup() {
    log "INFO" "${BLUE}Phase 1: Docker Service Startup Validation${NC}"
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        log "ERROR" "${RED}Docker daemon is not running${NC}"
        update_report '.phases.docker_startup.docker_daemon' '"failed"'
        return 1
    fi
    
    log "INFO" "${GREEN}Docker daemon is running${NC}"
    update_report '.phases.docker_startup.docker_daemon' '"healthy"'
    
    # Check current containers
    log "INFO" "Checking current container status..."
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | tee -a "$LOG_FILE"
    
    # Validate each service container
    local startup_results="{}"
    for service in "${!SERVICES[@]}"; do
        local port=${SERVICES[$service]}
        log "INFO" "Validating $service (port $port)..."
        
        # Check if container exists and is running
        local container_status=$(docker ps --filter "name=acgs_${service}" --format "{{.Status}}" 2>/dev/null || echo "not_found")
        
        if [[ "$container_status" == "not_found" ]]; then
            log "WARN" "${YELLOW}Container acgs_${service} not found${NC}"
            startup_results=$(echo "$startup_results" | jq ". + {\"$service\": {\"status\": \"not_found\", \"container_status\": \"missing\"}}")
        elif [[ "$container_status" =~ ^Up ]]; then
            log "INFO" "${GREEN}Container acgs_${service} is running: $container_status${NC}"
            startup_results=$(echo "$startup_results" | jq ". + {\"$service\": {\"status\": \"running\", \"container_status\": \"$container_status\"}}")
        else
            log "WARN" "${YELLOW}Container acgs_${service} exists but not running: $container_status${NC}"
            startup_results=$(echo "$startup_results" | jq ". + {\"$service\": {\"status\": \"stopped\", \"container_status\": \"$container_status\"}}")
        fi
    done
    
    update_report '.phases.docker_startup.services' "$startup_results"
    log "INFO" "${BLUE}Phase 1 completed${NC}"
}

# Phase 2: HTTP Health Endpoint Validation
validate_health_endpoints() {
    log "INFO" "${BLUE}Phase 2: HTTP Health Endpoint Validation${NC}"
    
    local health_results="{}"
    local healthy_count=0
    local failed_count=0
    
    for service in "${!SERVICE_HEALTH_ENDPOINTS[@]}"; do
        local port=${SERVICES[$service]}
        local endpoint=${SERVICE_HEALTH_ENDPOINTS[$service]}
        local url="http://localhost:${port}${endpoint}"
        
        log "INFO" "Testing health endpoint: $url"
        
        # Test with curl and measure response time
        local response_time=$(curl -w "%{time_total}" -s -o /tmp/health_response_${service}.json \
            --max-time 5 --connect-timeout 2 "$url" 2>/dev/null || echo "timeout")
        
        if [[ "$response_time" == "timeout" ]]; then
            log "ERROR" "${RED}Health check failed for $service: timeout${NC}"
            health_results=$(echo "$health_results" | jq ". + {\"$service\": {\"status\": \"failed\", \"error\": \"timeout\", \"response_time_ms\": null}}")
            ((failed_count++))
        else
            local response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)
            local http_status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
            
            if [[ "$http_status" == "200" ]]; then
                local response_content=$(cat /tmp/health_response_${service}.json 2>/dev/null || echo "{}")
                log "INFO" "${GREEN}Health check passed for $service: ${response_time_ms}ms${NC}"
                health_results=$(echo "$health_results" | jq ". + {\"$service\": {\"status\": \"healthy\", \"response_time_ms\": $response_time_ms, \"http_status\": $http_status, \"response\": $response_content}}")
                ((healthy_count++))
                
                # Check if response time meets target (<200ms)
                if [[ $response_time_ms -lt 200 ]]; then
                    log "INFO" "${GREEN}Response time target met for $service${NC}"
                else
                    log "WARN" "${YELLOW}Response time target missed for $service: ${response_time_ms}ms > 200ms${NC}"
                fi
            else
                log "ERROR" "${RED}Health check failed for $service: HTTP $http_status${NC}"
                health_results=$(echo "$health_results" | jq ". + {\"$service\": {\"status\": \"failed\", \"http_status\": $http_status, \"response_time_ms\": $response_time_ms}}")
                ((failed_count++))
            fi
        fi
        
        # Cleanup temp file
        rm -f /tmp/health_response_${service}.json
    done
    
    update_report '.phases.health_endpoints.services' "$health_results"
    update_report '.phases.health_endpoints.healthy_count' "$healthy_count"
    update_report '.phases.health_endpoints.failed_count' "$failed_count"
    update_report '.summary.services_healthy' "$healthy_count"
    update_report '.summary.services_failed' "$failed_count"
    
    log "INFO" "${BLUE}Phase 2 completed: $healthy_count healthy, $failed_count failed${NC}"
}

# Phase 3: Cross-Service Communication Testing
validate_cross_service_communication() {
    log "INFO" "${BLUE}Phase 3: Cross-Service Communication Testing${NC}"
    
    local comm_results="{}"
    
    # Test authentication workflow
    log "INFO" "Testing authentication workflow..."
    local auth_test_result=$(test_auth_workflow)
    comm_results=$(echo "$comm_results" | jq ". + {\"authentication_workflow\": $auth_test_result}")
    
    # Test inter-service API communication
    log "INFO" "Testing inter-service API communication..."
    local api_test_result=$(test_inter_service_apis)
    comm_results=$(echo "$comm_results" | jq ". + {\"inter_service_apis\": $api_test_result}")
    
    update_report '.phases.cross_service_communication' "$comm_results"
    log "INFO" "${BLUE}Phase 3 completed${NC}"
}

# Test authentication workflow
test_auth_workflow() {
    local result='{"status": "unknown", "steps": {}}'
    
    # Test login endpoint
    local login_response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"username": "test_user", "password": "test_password"}' \
        http://localhost:8000/auth/login 2>/dev/null || echo "000")
    
    if [[ "${login_response: -3}" == "200" ]] || [[ "${login_response: -3}" == "422" ]]; then
        result=$(echo "$result" | jq '.steps.login = {"status": "accessible", "http_code": "'"${login_response: -3}"'"}')
        result=$(echo "$result" | jq '.status = "accessible"')
    else
        result=$(echo "$result" | jq '.steps.login = {"status": "failed", "http_code": "'"${login_response: -3}"'"}')
        result=$(echo "$result" | jq '.status = "failed"')
    fi
    
    echo "$result"
}

# Test inter-service APIs
test_inter_service_apis() {
    local result='{"status": "unknown", "services": {}}'
    
    # Test AC service principles endpoint
    if curl -s --max-time 3 http://localhost:8001/api/v1/principles >/dev/null 2>&1; then
        result=$(echo "$result" | jq '.services.ac_principles = {"status": "accessible"}')
    else
        result=$(echo "$result" | jq '.services.ac_principles = {"status": "failed"}')
    fi
    
    # Test Integrity service policies endpoint
    if curl -s --max-time 3 http://localhost:8002/api/v1/policies >/dev/null 2>&1; then
        result=$(echo "$result" | jq '.services.integrity_policies = {"status": "accessible"}')
    else
        result=$(echo "$result" | jq '.services.integrity_policies = {"status": "failed"}')
    fi
    
    echo "$result"
}

# Phase 4: Performance and Stability Assessment
validate_performance_stability() {
    log "INFO" "${BLUE}Phase 4: Performance and Stability Assessment${NC}"
    
    local perf_results="{}"
    
    # Monitor Docker container resource usage
    log "INFO" "Monitoring container resource usage..."
    local container_stats=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null || echo "failed")
    
    if [[ "$container_stats" != "failed" ]]; then
        perf_results=$(echo "$perf_results" | jq '. + {"container_stats": "available"}')
        echo "$container_stats" | tee -a "$LOG_FILE"
    else
        perf_results=$(echo "$perf_results" | jq '. + {"container_stats": "failed"}')
    fi
    
    # Basic load test using curl (simple concurrent requests)
    log "INFO" "Performing basic load test..."
    local load_test_result=$(perform_basic_load_test)
    perf_results=$(echo "$perf_results" | jq ". + {\"load_test\": $load_test_result}")
    
    update_report '.phases.performance_assessment' "$perf_results"
    log "INFO" "${BLUE}Phase 4 completed${NC}"
}

# Perform basic load test
perform_basic_load_test() {
    local result='{"status": "unknown", "concurrent_requests": 10, "results": {}}'
    
    # Test with 10 concurrent requests to auth service health endpoint
    local start_time=$(date +%s.%N)
    for i in {1..10}; do
        curl -s http://localhost:8000/health >/dev/null &
    done
    wait
    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc -l)
    
    result=$(echo "$result" | jq ".results.auth_service = {\"total_time_seconds\": $total_time, \"requests\": 10}")
    result=$(echo "$result" | jq '.status = "completed"')
    
    echo "$result"
}

# Generate final report
generate_final_report() {
    log "INFO" "${BLUE}Generating Final Infrastructure Status Report${NC}"
    
    # Calculate overall status
    local healthy_services=$(jq -r '.summary.services_healthy' "$REPORT_FILE")
    local total_services=$(jq -r '.summary.total_services' "$REPORT_FILE")
    local uptime_percent=$(echo "scale=2; $healthy_services * 100 / $total_services" | bc -l)
    
    update_report '.summary.uptime_percent' "$uptime_percent"
    
    if [[ $healthy_services -eq $total_services ]]; then
        update_report '.summary.overall_status' '"healthy"'
        update_report '.summary.infrastructure_ready' 'true'
        log "INFO" "${GREEN}Infrastructure Status: HEALTHY - All services operational${NC}"
    elif [[ $healthy_services -gt 0 ]]; then
        update_report '.summary.overall_status' '"degraded"'
        update_report '.summary.infrastructure_ready' 'false'
        log "WARN" "${YELLOW}Infrastructure Status: DEGRADED - Some services operational${NC}"
    else
        update_report '.summary.overall_status' '"failed"'
        update_report '.summary.infrastructure_ready' 'false'
        log "ERROR" "${RED}Infrastructure Status: FAILED - No services operational${NC}"
    fi
    
    # Add recommendations
    local recommendations='[]'
    if [[ $healthy_services -lt $total_services ]]; then
        recommendations=$(echo "$recommendations" | jq '. + ["Start missing Docker services using docker-compose up"]')
        recommendations=$(echo "$recommendations" | jq '. + ["Check Docker logs for failed services"]')
        recommendations=$(echo "$recommendations" | jq '. + ["Verify database connectivity and migrations"]')
    fi
    
    if [[ $(echo "$uptime_percent < 99.5" | bc -l) -eq 1 ]]; then
        recommendations=$(echo "$recommendations" | jq '. + ["Infrastructure does not meet >99.5% uptime target"]')
    fi
    
    update_report '.summary.recommendations' "$recommendations"
    
    # Display summary
    echo -e "\n${BLUE}=== ACGS-PGP Infrastructure Validation Summary ===${NC}"
    echo -e "Timestamp: $(jq -r '.timestamp' "$REPORT_FILE")"
    echo -e "Services Healthy: $healthy_services/$total_services (${uptime_percent}%)"
    echo -e "Overall Status: $(jq -r '.summary.overall_status' "$REPORT_FILE")"
    echo -e "Infrastructure Ready: $(jq -r '.summary.infrastructure_ready' "$REPORT_FILE")"
    echo -e "Report File: $REPORT_FILE"
    echo -e "Log File: $LOG_FILE"
    
    if [[ $(jq -r '.summary.infrastructure_ready' "$REPORT_FILE") == "true" ]]; then
        echo -e "\n${GREEN}✓ Infrastructure is ready for Phase 2 AlphaEvolve integration${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Infrastructure requires fixes before Phase 2 integration${NC}"
        echo -e "\nRecommendations:"
        jq -r '.summary.recommendations[]' "$REPORT_FILE" | while read -r rec; do
            echo -e "  - $rec"
        done
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}ACGS-PGP Phase 1 Infrastructure Stabilization${NC}"
    echo -e "${BLUE}Docker-based Service Validation Strategy${NC}"
    echo -e "Target: <200ms response times, >99.5% uptime, 50+ concurrent users\n${NC}"
    
    # Initialize report
    init_report
    
    # Execute validation phases
    validate_docker_startup
    validate_health_endpoints
    validate_cross_service_communication
    validate_performance_stability
    
    # Generate final report
    generate_final_report
}

# Check dependencies
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed${NC}"
    exit 1
fi

if ! command -v bc &> /dev/null; then
    echo -e "${RED}Error: bc is required but not installed${NC}"
    exit 1
fi

# Run main function
main "$@"
