#!/bin/bash
# ACGS-PGP Comprehensive Health Check Script

echo "🏥 ACGS-PGP System Health Check"
echo "==============================="

# Service health checks
services=("ac_service:8001" "integrity_service:8002" "fv_service:8003" "gs_service:8004" "pgc_service:8005")
healthy_services=0
total_services=${#services[@]}

echo "1. Service Health Status:"
for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health)
    
    if [ "$response" = "200" ]; then
        echo "  ✅ $name: Healthy"
        ((healthy_services++))
    else
        echo "  ❌ $name: Unhealthy (HTTP $response)"
    fi
done

echo -e "\n2. Database Health:"
if pg_isready -h localhost -p 5433 -U acgs_user -d acgs_pgp_db; then
    echo "  ✅ PostgreSQL: Healthy"
    ((healthy_services++))
    ((total_services++))
else
    echo "  ❌ PostgreSQL: Unhealthy"
    ((total_services++))
fi

echo -e "\n3. System Resources:"
echo "  CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "  Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "  Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo -e "\n4. Docker Container Status:"
docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}"

echo -e "\n5. Recent Logs (last 10 lines):"
docker-compose logs --tail=10 ac_service | head -5
docker-compose logs --tail=10 gs_service | head -5

echo -e "\n📊 Health Summary:"
echo "  Services: $healthy_services/$total_services healthy"
health_percentage=$((healthy_services * 100 / total_services))

if [ $health_percentage -eq 100 ]; then
    echo "  Status: ✅ All systems operational"
    exit 0
elif [ $health_percentage -ge 80 ]; then
    echo "  Status: ⚠️  Mostly operational ($health_percentage%)"
    exit 1
else
    echo "  Status: ❌ System degraded ($health_percentage%)"
    exit 2
fi
