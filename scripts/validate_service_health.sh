#!/bin/bash
# ACGS-PGP Service Health Validation Script
# Tests the improved health check endpoints and service connectivity

echo "🏥 ACGS-PGP Service Health Validation"
echo "====================================="

# Service configuration
declare -A services=(
    ["auth_service"]="8000"
    ["ac_service"]="8001"
    ["integrity_service"]="8002"
    ["fv_service"]="8003"
    ["gs_service"]="8004"
    ["pgc_service"]="8005"
    ["ec_service"]="8006"
    ["research_service"]="8007"
)

# Counters
healthy_count=0
total_count=0
failed_services=()

echo "1. Testing Service Health Endpoints:"
echo "-----------------------------------"

for service in "${!services[@]}"; do
    port=${services[$service]}
    total_count=$((total_count + 1))
    
    echo -n "Testing $service (port $port): "
    
    # Test health endpoint with timeout
    response=$(curl -s -w "%{http_code}" -m 5 "http://localhost:$port/health" -o /tmp/health_response.json 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "✅ Healthy"
        healthy_count=$((healthy_count + 1))
        
        # Check if response contains detailed health information
        if [ -f /tmp/health_response.json ]; then
            if grep -q "dependencies" /tmp/health_response.json 2>/dev/null; then
                echo "   📊 Enhanced health check detected"
            fi
            if grep -q "components" /tmp/health_response.json 2>/dev/null; then
                echo "   🔧 Component status available"
            fi
        fi
    elif [ "$response" = "000" ]; then
        echo "❌ Connection Failed"
        failed_services+=("$service")
    else
        echo "⚠️  HTTP $response"
        failed_services+=("$service")
    fi
done

echo ""
echo "2. Testing Metrics Endpoints:"
echo "----------------------------"

for service in "${!services[@]}"; do
    port=${services[$service]}
    
    echo -n "Testing $service metrics: "
    
    # Test metrics endpoint
    response=$(curl -s -w "%{http_code}" -m 5 "http://localhost:$port/metrics" -o /dev/null 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "✅ Available"
    elif [ "$response" = "000" ]; then
        echo "❌ Connection Failed"
    else
        echo "⚠️  HTTP $response"
    fi
done

echo ""
echo "3. Testing Cross-Service Dependencies:"
echo "------------------------------------"

# Test if GS service can reach AC service (if both are running)
if curl -s -m 3 "http://localhost:8004/health" > /dev/null 2>&1 && curl -s -m 3 "http://localhost:8001/health" > /dev/null 2>&1; then
    echo "✅ GS Service → AC Service: Connectivity available"
else
    echo "❌ GS Service → AC Service: Connectivity issue"
fi

# Test if PGC service can reach Integrity service
if curl -s -m 3 "http://localhost:8005/health" > /dev/null 2>&1 && curl -s -m 3 "http://localhost:8002/health" > /dev/null 2>&1; then
    echo "✅ PGC Service → Integrity Service: Connectivity available"
else
    echo "❌ PGC Service → Integrity Service: Connectivity issue"
fi

echo ""
echo "4. Infrastructure Health Check:"
echo "------------------------------"

# Test PostgreSQL
echo -n "PostgreSQL (port 5433): "
if nc -z localhost 5433 2>/dev/null; then
    echo "✅ Accessible"
else
    echo "❌ Not accessible"
fi

# Test Redis
echo -n "Redis (port 6379): "
if nc -z localhost 6379 2>/dev/null; then
    echo "✅ Accessible"
else
    echo "❌ Not accessible"
fi

# Test OPA
echo -n "OPA (port 8181): "
response=$(curl -s -w "%{http_code}" -m 3 "http://localhost:8181/health" -o /dev/null 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "✅ Healthy"
else
    echo "❌ Not healthy (HTTP $response)"
fi

# Test Prometheus
echo -n "Prometheus (port 9090): "
response=$(curl -s -w "%{http_code}" -m 3 "http://localhost:9090/-/healthy" -o /dev/null 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "✅ Healthy"
else
    echo "❌ Not healthy (HTTP $response)"
fi

# Test Grafana
echo -n "Grafana (port 3001): "
response=$(curl -s -w "%{http_code}" -m 3 "http://localhost:3001/api/health" -o /dev/null 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "✅ Healthy"
else
    echo "❌ Not healthy (HTTP $response)"
fi

echo ""
echo "5. Performance Analysis:"
echo "----------------------"

# Calculate response times for healthy services
total_response_time=0
response_count=0

for service in "${!services[@]}"; do
    port=${services[$service]}
    
    # Measure response time
    start_time=$(date +%s%N)
    response=$(curl -s -w "%{http_code}" -m 5 "http://localhost:$port/health" -o /dev/null 2>/dev/null)
    end_time=$(date +%s%N)
    
    if [ "$response" = "200" ]; then
        response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
        total_response_time=$((total_response_time + response_time))
        response_count=$((response_count + 1))
        
        if [ $response_time -lt 200 ]; then
            echo "✅ $service: ${response_time}ms (Good)"
        elif [ $response_time -lt 500 ]; then
            echo "⚠️  $service: ${response_time}ms (Acceptable)"
        else
            echo "❌ $service: ${response_time}ms (Slow)"
        fi
    fi
done

# Calculate average response time
if [ $response_count -gt 0 ]; then
    avg_response_time=$((total_response_time / response_count))
    echo "Average response time: ${avg_response_time}ms"
else
    echo "No healthy services to measure response time"
fi

echo ""
echo "6. Summary Report:"
echo "=================="

# Calculate availability percentage
availability_percentage=$((healthy_count * 100 / total_count))

echo "Service Availability: $healthy_count/$total_count ($availability_percentage%)"

if [ $response_count -gt 0 ]; then
    echo "Average Response Time: ${avg_response_time}ms"
    
    # Performance grade
    if [ $availability_percentage -ge 99 ] && [ $avg_response_time -lt 100 ]; then
        echo "Performance Grade: A+"
    elif [ $availability_percentage -ge 95 ] && [ $avg_response_time -lt 200 ]; then
        echo "Performance Grade: A"
    elif [ $availability_percentage -ge 90 ] && [ $avg_response_time -lt 500 ]; then
        echo "Performance Grade: B"
    else
        echo "Performance Grade: C"
    fi
fi

# Overall status
if [ $healthy_count -eq $total_count ]; then
    echo "Overall Status: 🟢 HEALTHY"
    exit_code=0
elif [ $healthy_count -ge $((total_count * 80 / 100)) ]; then
    echo "Overall Status: 🟡 DEGRADED"
    exit_code=1
else
    echo "Overall Status: 🔴 UNHEALTHY"
    exit_code=2
fi

# List failed services
if [ ${#failed_services[@]} -gt 0 ]; then
    echo ""
    echo "Failed Services:"
    for service in "${failed_services[@]}"; do
        echo "  - $service"
    done
fi

echo ""
echo "7. Recommendations:"
echo "==================="

if [ $availability_percentage -lt 100 ]; then
    echo "- Investigate and fix failed services"
fi

if [ $response_count -gt 0 ] && [ $avg_response_time -gt 200 ]; then
    echo "- Optimize service response times"
fi

echo "- Monitor service health continuously"
echo "- Implement automated alerting for service failures"
echo "- Set up load balancing for high availability"

# Cleanup
rm -f /tmp/health_response.json

exit $exit_code
