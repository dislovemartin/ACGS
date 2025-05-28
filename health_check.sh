#!/bin/bash

# ACGS-PGP System Health Check Script
# This script performs comprehensive health checks on all ACGS-PGP services

set -e

echo "=== ACGS-PGP System Health Check ==="
echo "Timestamp: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        return 1
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local expected_code=${2:-200}
    local timeout=${3:-10}
    
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $timeout "$url" 2>/dev/null || echo "000")
    
    if [ "$response_code" = "$expected_code" ] || [ "$response_code" = "200" ]; then
        return 0
    else
        echo "Expected: $expected_code, Got: $response_code"
        return 1
    fi
}

echo "1. Checking Docker and Docker Compose..."
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    print_status 0 "Docker and Docker Compose are installed"
else
    print_status 1 "Docker or Docker Compose not found"
    exit 1
fi

echo ""
echo "2. Checking container status..."
CONTAINERS=$(docker-compose ps --services 2>/dev/null || echo "")
if [ -z "$CONTAINERS" ]; then
    print_status 1 "No containers found or docker-compose.yml not accessible"
    exit 1
fi

ALL_UP=true
for container in $CONTAINERS; do
    STATUS=$(docker-compose ps $container 2>/dev/null | tail -n +3 | awk '{print $4}' || echo "Down")
    if [[ "$STATUS" == *"Up"* ]]; then
        print_status 0 "$container is running"
    else
        print_status 1 "$container is not running (Status: $STATUS)"
        ALL_UP=false
    fi
done

if [ "$ALL_UP" = false ]; then
    print_warning "Some containers are not running. Check logs with: docker-compose logs [service_name]"
fi

echo ""
echo "3. Testing gateway access..."
if test_endpoint "http://localhost:8000" "404"; then
    print_status 0 "Nginx gateway is accessible"
else
    print_status 1 "Nginx gateway is not accessible"
fi

echo ""
echo "4. Testing database connectivity..."
DB_TEST=$(docker exec acgs_postgres pg_isready -U youruser 2>/dev/null || echo "failed")
if [[ "$DB_TEST" == *"accepting connections"* ]]; then
    print_status 0 "PostgreSQL is accepting connections"
else
    print_status 1 "PostgreSQL connection failed"
fi

echo ""
echo "5. Testing Redis connectivity..."
REDIS_TEST=$(docker exec acgs_redis redis-cli ping 2>/dev/null || echo "failed")
if [ "$REDIS_TEST" = "PONG" ]; then
    print_status 0 "Redis is responding"
else
    print_status 1 "Redis connection failed"
fi

echo ""
echo "6. Testing service endpoints..."
declare -A SERVICES=(
    ["auth"]="Authentication Service"
    ["ac"]="Access Control Service"
    ["gs"]="Generation Service"
    ["fv"]="Formal Verification Service"
    ["integrity"]="Integrity Service"
    ["pgc"]="Policy Generation Control Service"
)

for service in "${!SERVICES[@]}"; do
    if test_endpoint "http://localhost:8000/$service/" "200"; then
        print_status 0 "${SERVICES[$service]} endpoint is accessible"
    else
        print_status 1 "${SERVICES[$service]} endpoint failed"
    fi
done

echo ""
echo "7. Testing auth service specific endpoints..."
if test_endpoint "http://localhost:8000/auth/docs" "200"; then
    print_status 0 "Auth service documentation is accessible"
else
    print_status 1 "Auth service documentation failed"
fi

echo ""
echo "8. Checking service logs for errors..."
ERROR_COUNT=0
for container in $CONTAINERS; do
    ERRORS=$(docker logs acgs_$container 2>&1 | grep -i "error\|exception\|failed" | wc -l 2>/dev/null || echo "0")
    if [ "$ERRORS" -gt 0 ]; then
        print_warning "$container has $ERRORS error/exception messages in logs"
        ERROR_COUNT=$((ERROR_COUNT + ERRORS))
    fi
done

if [ "$ERROR_COUNT" -eq 0 ]; then
    print_status 0 "No errors found in service logs"
else
    print_warning "Total errors found in logs: $ERROR_COUNT"
fi

echo ""
echo "9. Checking resource usage..."
MEMORY_USAGE=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | tail -n +2)
echo "Memory usage by container:"
echo "$MEMORY_USAGE"

echo ""
echo "10. Testing database tables..."
TABLES=$(docker exec acgs_postgres psql -U youruser -d yourdatabase_auth -t -c "\dt" 2>/dev/null | wc -l || echo "0")
if [ "$TABLES" -gt 0 ]; then
    print_status 0 "Database tables exist ($TABLES tables found)"
else
    print_status 1 "No database tables found or connection failed"
fi

echo ""
echo "=== Health Check Summary ==="
echo "Timestamp: $(date)"

# Final assessment
if [ "$ALL_UP" = true ] && [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ System appears to be healthy${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ System has some issues that need attention${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check container logs: docker-compose logs [service_name]"
    echo "2. Restart failed services: docker-compose restart [service_name]"
    echo "3. Check the DEPLOYMENT_CHECKLIST.md for detailed troubleshooting"
    exit 1
fi
