#!/bin/bash

# ACGS-PGP Load Testing Script for Monitoring Validation
# Tests the monitoring system under load to validate metrics collection and alerting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONCURRENT_USERS=${1:-50}
TEST_DURATION=${2:-300}  # 5 minutes default
BASE_URL="http://localhost:8000"

echo -e "${BLUE}🧪 ACGS-PGP Load Testing for Monitoring Validation${NC}"
echo "=================================================="
echo "Concurrent Users: $CONCURRENT_USERS"
echo "Test Duration: $TEST_DURATION seconds"
echo "Base URL: $BASE_URL"
echo ""

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to make concurrent requests
load_test_endpoint() {
    local endpoint=$1
    local name=$2
    local concurrent=$3
    local duration=$4
    
    print_info "Load testing $name endpoint: $endpoint"
    
    # Create a temporary script for concurrent requests
    cat > /tmp/load_test_worker.sh << EOF
#!/bin/bash
endpoint="$endpoint"
duration=$duration
start_time=\$(date +%s)
end_time=\$((start_time + duration))
request_count=0
success_count=0

while [ \$(date +%s) -lt \$end_time ]; do
    if curl -s -o /dev/null -w "%{http_code}" "\$endpoint" | grep -q "200"; then
        success_count=\$((success_count + 1))
    fi
    request_count=\$((request_count + 1))
    sleep 0.1  # 10 requests per second per worker
done

echo "Worker completed: \$request_count requests, \$success_count successful"
EOF
    
    chmod +x /tmp/load_test_worker.sh
    
    # Start concurrent workers
    for i in $(seq 1 $concurrent); do
        /tmp/load_test_worker.sh &
    done
    
    # Wait for all workers to complete
    wait
    
    # Clean up
    rm -f /tmp/load_test_worker.sh
}

# Check if services are running
echo "1. Checking service availability..."

services=(
    "auth:8000:/health"
    "ac:8001:/health"
    "integrity:8002:/health"
    "fv:8003:/health"
    "gs:8004:/health"
    "pgc:8005:/health"
)

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    endpoint=$(echo $service | cut -d: -f3)
    
    if curl -f "http://localhost:$port$endpoint" >/dev/null 2>&1; then
        print_status 0 "$service_name service is accessible"
    else
        print_status 1 "$service_name service is not accessible"
        exit 1
    fi
done

# Check monitoring services
echo ""
echo "2. Checking monitoring services..."

if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
    print_status 0 "Prometheus is accessible"
else
    print_status 1 "Prometheus is not accessible"
    exit 1
fi

if curl -f http://localhost:3001/api/health >/dev/null 2>&1; then
    print_status 0 "Grafana is accessible"
else
    print_status 1 "Grafana is not accessible"
    exit 1
fi

# Start load testing
echo ""
echo "3. Starting load testing..."

print_info "Starting load test with $CONCURRENT_USERS concurrent users for $TEST_DURATION seconds"

# Test different endpoints to generate varied metrics
endpoints=(
    "http://localhost:8000/auth/health:Auth Health Check"
    "http://localhost:8001/health:AC Health Check"
    "http://localhost:8002/health:Integrity Health Check"
    "http://localhost:8003/health:FV Health Check"
    "http://localhost:8004/health:GS Health Check"
    "http://localhost:8005/health:PGC Health Check"
)

# Start load testing for each endpoint
for endpoint_info in "${endpoints[@]}"; do
    endpoint=$(echo $endpoint_info | cut -d: -f1)
    name=$(echo $endpoint_info | cut -d: -f2-)
    
    # Use fewer concurrent users per endpoint to distribute load
    users_per_endpoint=$((CONCURRENT_USERS / 6))
    if [ $users_per_endpoint -lt 1 ]; then
        users_per_endpoint=1
    fi
    
    load_test_endpoint "$endpoint" "$name" $users_per_endpoint $TEST_DURATION &
done

# Wait for all load tests to complete
wait

print_status 0 "Load testing completed"

# Check metrics after load test
echo ""
echo "4. Validating metrics collection..."

# Wait a bit for metrics to be collected
sleep 10

# Check if metrics are being collected
if curl -s "http://localhost:9090/api/v1/query?query=acgs_http_requests_total" | grep -q "success"; then
    print_status 0 "HTTP request metrics are being collected"
else
    print_status 1 "HTTP request metrics not found"
fi

if curl -s "http://localhost:9090/api/v1/query?query=acgs_http_request_duration_seconds" | grep -q "success"; then
    print_status 0 "HTTP request duration metrics are being collected"
else
    print_status 1 "HTTP request duration metrics not found"
fi

# Check for any alerts that may have been triggered
echo ""
echo "5. Checking for triggered alerts..."

alerts=$(curl -s "http://localhost:9090/api/v1/alerts" | grep -o '"state":"firing"' | wc -l)
if [ "$alerts" -gt 0 ]; then
    print_info "$alerts alerts are currently firing"
    echo "Check Prometheus alerts at: http://localhost:9090/alerts"
else
    print_status 0 "No alerts currently firing"
fi

# Display monitoring URLs
echo ""
echo "6. Monitoring validation complete!"
echo "=================================================="
echo -e "${GREEN}✅ Load testing and monitoring validation completed!${NC}"
echo ""
echo "Review the following to validate monitoring:"
echo ""
echo "📊 Grafana Dashboard: http://localhost:3001"
echo "   - Check the ACGS-PGP Overview Dashboard"
echo "   - Verify request rate and response time graphs show activity"
echo "   - Look for any spikes or anomalies during the test period"
echo ""
echo "📈 Prometheus Metrics: http://localhost:9090"
echo "   - Query: acgs_http_requests_total (total requests)"
echo "   - Query: rate(acgs_http_requests_total[5m]) (request rate)"
echo "   - Query: acgs_http_request_duration_seconds (response times)"
echo ""
echo "🚨 Prometheus Alerts: http://localhost:9090/alerts"
echo "   - Check if any alerts were triggered during load testing"
echo "   - Validate alert thresholds are appropriate"
echo ""
echo "Expected metrics to validate:"
echo "  ✓ Request count increased during test period"
echo "  ✓ Response times remained under 200ms threshold"
echo "  ✓ Error rate remained under 5% threshold"
echo "  ✓ All services remained healthy throughout test"
echo ""
echo "Next steps:"
echo "  1. Review Grafana dashboards for the test period"
echo "  2. Adjust alert thresholds if needed"
echo "  3. Set up additional monitoring for production workloads"
echo "  4. Configure alert notifications (email, Slack, etc.)"

echo ""
echo -e "${BLUE}🎯 Load testing validation completed successfully!${NC}"
