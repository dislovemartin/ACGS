#!/bin/bash

# ACGS-PGP Production Monitoring Deployment Script
# Deploys Prometheus metrics collection, Grafana dashboards, and alerting system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/config/docker"
MONITORING_DIR="$DOCKER_DIR/monitoring"

echo -e "${BLUE}🚀 ACGS-PGP Production Monitoring Deployment${NC}"
echo "=================================================="

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check prerequisites
echo ""
echo "1. Checking prerequisites..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_status 1 "Docker is not running"
fi
print_status 0 "Docker is running"

# Check if Docker Compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    print_status 1 "Docker Compose is not installed"
fi
print_status 0 "Docker Compose is available"

# Check if monitoring directory exists
if [ ! -d "$MONITORING_DIR" ]; then
    print_status 1 "Monitoring configuration directory not found: $MONITORING_DIR"
fi
print_status 0 "Monitoring configuration directory found"

# Install prometheus-client for all services
echo ""
echo "2. Installing Prometheus client dependencies..."

# Check if pip is available
if command -v pip >/dev/null 2>&1; then
    pip install prometheus-client==0.21.1
    print_status 0 "Prometheus client installed"
else
    print_warning "pip not found, assuming prometheus-client is already installed"
fi

# Create monitoring directories if they don't exist
echo ""
echo "3. Setting up monitoring directories..."

mkdir -p "$MONITORING_DIR/grafana/provisioning/datasources"
mkdir -p "$MONITORING_DIR/grafana/provisioning/dashboards"
mkdir -p "$MONITORING_DIR/grafana/dashboards"

print_status 0 "Monitoring directories created"

# Validate configuration files
echo ""
echo "4. Validating configuration files..."

# Check Prometheus config
if [ ! -f "$MONITORING_DIR/prometheus.yml" ]; then
    print_status 1 "Prometheus configuration file not found"
fi
print_status 0 "Prometheus configuration validated"

# Check Grafana datasource config
if [ ! -f "$MONITORING_DIR/grafana/provisioning/datasources/prometheus.yml" ]; then
    print_status 1 "Grafana datasource configuration not found"
fi
print_status 0 "Grafana datasource configuration validated"

# Check alert rules
if [ ! -f "$MONITORING_DIR/alert_rules.yml" ]; then
    print_status 1 "Alert rules configuration not found"
fi
print_status 0 "Alert rules configuration validated"

# Deploy monitoring stack
echo ""
echo "5. Deploying monitoring stack..."

cd "$DOCKER_DIR"

# Stop existing monitoring services if running
print_info "Stopping existing monitoring services..."
docker-compose stop prometheus grafana 2>/dev/null || true

# Start monitoring services
print_info "Starting Prometheus and Grafana..."
docker-compose up -d prometheus grafana

# Wait for services to be ready
print_info "Waiting for services to be ready..."
sleep 30

# Check if Prometheus is accessible
if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
    print_status 0 "Prometheus is running and healthy"
else
    print_status 1 "Prometheus health check failed"
fi

# Check if Grafana is accessible
if curl -f http://localhost:3001/api/health >/dev/null 2>&1; then
    print_status 0 "Grafana is running and healthy"
else
    print_status 1 "Grafana health check failed"
fi

# Test metrics collection
echo ""
echo "6. Testing metrics collection..."

# Test each service metrics endpoint
services=("auth:8000" "ac:8001" "integrity:8002" "fv:8003" "gs:8004" "pgc:8005")

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -f "http://localhost:$port/metrics" >/dev/null 2>&1; then
        print_status 0 "$service_name service metrics endpoint accessible"
    else
        print_warning "$service_name service metrics endpoint not accessible (service may not be running)"
    fi
done

# Display access information
echo ""
echo "7. Deployment complete!"
echo "=================================================="
echo -e "${GREEN}✅ Monitoring stack deployed successfully!${NC}"
echo ""
echo "Access URLs:"
echo "  📊 Grafana Dashboard: http://localhost:3001"
echo "     Username: admin"
echo "     Password: admin123"
echo ""
echo "  📈 Prometheus: http://localhost:9090"
echo ""
echo "  🔍 Service Metrics:"
echo "     Auth Service: http://localhost:8000/metrics"
echo "     AC Service: http://localhost:8001/metrics"
echo "     Integrity Service: http://localhost:8002/metrics"
echo "     FV Service: http://localhost:8003/metrics"
echo "     GS Service: http://localhost:8004/metrics"
echo "     PGC Service: http://localhost:8005/metrics"
echo ""
echo "Next steps:"
echo "  1. Access Grafana and explore the ACGS-PGP Overview Dashboard"
echo "  2. Configure additional alert channels in Grafana"
echo "  3. Set up load testing to validate monitoring under load"
echo "  4. Review and adjust alert thresholds based on baseline metrics"

# Optional: Open Grafana in browser
if command -v xdg-open >/dev/null 2>&1; then
    echo ""
    read -p "Open Grafana in browser? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open http://localhost:3001
    fi
elif command -v open >/dev/null 2>&1; then
    echo ""
    read -p "Open Grafana in browser? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost:3001
    fi
fi

echo ""
echo -e "${BLUE}🎉 ACGS-PGP monitoring deployment completed successfully!${NC}"
