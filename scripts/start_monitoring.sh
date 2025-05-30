#!/bin/bash
# Start ACGS-PGP monitoring stack

echo "🚀 Starting ACGS-PGP Monitoring Stack..."

# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

echo "✅ Monitoring stack started!"
echo "📊 Prometheus: http://localhost:9090"
echo "📈 Grafana: http://localhost:3001 (admin/admin123)"
echo "🚨 Alertmanager: http://localhost:9093"

# Wait for services to start
sleep 10

# Run initial health check
./health_check.sh
