#!/bin/bash

# ACGS-PGP Quick Start Script
# This script executes the immediate next steps to complete the deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ACGS-PGP Quick Start Deployment ===${NC}"
echo "This script will complete the remaining deployment steps."
echo ""

# Function to print status
print_step() {
    echo -e "${BLUE}Step $1: $2${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Step 1: Fix auth service
print_step "1" "Fixing auth service AsyncPG import issue"

echo "Removing old auth service image..."
docker rmi acgs-master-auth_service 2>/dev/null || echo "Image not found, continuing..."

echo "Cleaning up Docker system..."
docker system prune -f

echo "Verifying requirements file..."
if grep -q "asyncpg" backend/auth_service/requirements_simple.txt; then
    print_success "AsyncPG found in requirements"
else
    print_error "AsyncPG not found in requirements file"
    exit 1
fi

echo "Rebuilding auth service without cache..."
if docker-compose build --no-cache auth_service; then
    print_success "Auth service built successfully"
else
    print_error "Failed to build auth service"
    exit 1
fi

echo "Starting auth service..."
if docker-compose up -d auth_service; then
    print_success "Auth service started"
else
    print_error "Failed to start auth service"
    exit 1
fi

# Wait a moment for service to start
echo "Waiting for auth service to initialize..."
sleep 10

# Step 2: Check all services
print_step "2" "Checking all service status"

echo "Current container status:"
docker-compose ps

# Step 3: Start any missing services
print_step "3" "Starting all services"

echo "Starting all services..."
if docker-compose up -d; then
    print_success "All services started"
else
    print_warning "Some services may have failed to start"
fi

# Wait for services to stabilize
echo "Waiting for services to stabilize..."
sleep 15

# Step 4: Test basic connectivity
print_step "4" "Testing basic connectivity"

echo "Testing nginx gateway..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "404\|200"; then
    print_success "Nginx gateway is accessible"
else
    print_error "Nginx gateway is not accessible"
fi

echo "Testing auth service..."
if curl -s http://localhost:8000/auth/ | grep -q "Authentication Service"; then
    print_success "Auth service is responding"
else
    print_error "Auth service is not responding properly"
fi

# Step 5: Run health check
print_step "5" "Running comprehensive health check"

if [ -f "./health_check.sh" ]; then
    echo "Running health check script..."
    if ./health_check.sh; then
        print_success "Health check passed"
    else
        print_warning "Health check found some issues"
        echo ""
        echo "Check the output above for details."
        echo "Refer to DEPLOYMENT_CHECKLIST.md for troubleshooting guidance."
    fi
else
    print_error "Health check script not found"
fi

echo ""
echo -e "${BLUE}=== Quick Start Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Review the health check output above"
echo "2. If issues were found, consult DEPLOYMENT_CHECKLIST.md"
echo "3. Test individual service endpoints:"
echo "   - Auth: http://localhost:8000/auth/"
echo "   - Auth Docs: http://localhost:8000/auth/docs"
echo "   - Other services: http://localhost:8000/{service}/"
echo ""
echo "For detailed testing and validation, follow the complete"
echo "DEPLOYMENT_CHECKLIST.md file."
