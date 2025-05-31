#!/bin/bash

# ACGS-PGP Fix Validation Script
# Validates that all remediation actions have been successful

set -euo pipefail

echo "🔍 ACGS-PGP Fix Validation Script"
echo "=================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to print colored output
print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

# Test 1: Configuration Files
echo -e "\n${BLUE}Testing Configuration Files${NC}"
echo "============================"

print_test "Checking .bandit configuration..."
if [ -f ".bandit" ]; then
    print_pass ".bandit configuration exists"
else
    print_fail ".bandit configuration missing"
fi

print_test "Checking pytest.ini configuration..."
if [ -f "pytest.ini" ]; then
    print_pass "pytest.ini configuration exists"
else
    print_fail "pytest.ini configuration missing"
fi

print_test "Checking Docker Compose configuration..."
if docker-compose -f config/docker/docker-compose.yml config > /dev/null 2>&1; then
    print_pass "Docker Compose configuration is valid"
else
    print_fail "Docker Compose configuration has errors"
fi

# Test 2: Dependencies
echo -e "\n${BLUE}Testing Dependencies${NC}"
echo "===================="

print_test "Checking auth service dependencies..."
if grep -q "prometheus_client" src/backend/auth_service/requirements_simple.txt; then
    print_pass "prometheus_client dependency found in auth service"
else
    print_fail "prometheus_client dependency missing in auth service"
fi

if grep -q "aiofiles" src/backend/auth_service/requirements_simple.txt; then
    print_pass "aiofiles dependency found in auth service"
else
    print_fail "aiofiles dependency missing in auth service"
fi

# Test 3: Shared Module
echo -e "\n${BLUE}Testing Shared Module${NC}"
echo "====================="

print_test "Checking shared module structure..."
if [ -f "src/backend/shared/__init__.py" ]; then
    print_pass "Shared module __init__.py exists"
else
    print_fail "Shared module __init__.py missing"
fi

if [ -f "src/backend/shared/metrics.py" ]; then
    print_pass "Shared metrics module exists"
else
    print_fail "Shared metrics module missing"
fi

# Test 4: Monitoring Configuration
echo -e "\n${BLUE}Testing Monitoring Configuration${NC}"
echo "================================="

print_test "Checking Prometheus configuration..."
if [ -f "config/docker/monitoring/prometheus.yml" ]; then
    print_pass "Prometheus configuration exists"
else
    print_fail "Prometheus configuration missing"
fi

print_test "Checking alert rules..."
if [ -f "config/docker/monitoring/alert_rules.yml" ]; then
    print_pass "Alert rules configuration exists"
else
    print_warn "Alert rules configuration missing (optional)"
fi

# Test 5: CI/CD Configuration
echo -e "\n${BLUE}Testing CI/CD Configuration${NC}"
echo "============================"

print_test "Checking GitHub Actions workflows..."
workflows=(".github/workflows/ci.yml" ".github/workflows/docker-image.yml")
for workflow in "${workflows[@]}"; do
    if [ -f "$workflow" ]; then
        print_pass "Found $workflow"
    else
        print_fail "Missing $workflow"
    fi
done

# Test 6: Security Configuration
echo -e "\n${BLUE}Testing Security Configuration${NC}"
echo "==============================="

print_test "Checking bandit can run..."
if command -v bandit > /dev/null 2>&1; then
    if bandit --help > /dev/null 2>&1; then
        print_pass "Bandit security scanner available"
    else
        print_warn "Bandit available but may have configuration issues"
    fi
else
    print_warn "Bandit not installed (will be installed in CI)"
fi

# Test 7: Database Configuration
echo -e "\n${BLUE}Testing Database Configuration${NC}"
echo "==============================="

print_test "Checking Alembic configuration..."
if [ -f "src/backend/shared/alembic.ini" ]; then
    print_pass "Alembic configuration exists"
else
    print_fail "Alembic configuration missing"
fi

print_test "Checking migration directory..."
if [ -d "src/backend/shared/alembic/versions" ]; then
    print_pass "Alembic versions directory exists"
else
    print_warn "Alembic versions directory missing (will be created)"
fi

# Test 8: Service Health Checks
echo -e "\n${BLUE}Testing Service Configuration${NC}"
echo "============================="

print_test "Checking service Dockerfiles..."
services=("auth_service" "ac_service" "integrity_service" "fv_service" "gs_service" "pgc_service")
for service in "${services[@]}"; do
    if [ -f "src/backend/$service/Dockerfile" ]; then
        print_pass "Dockerfile exists for $service"
    else
        print_fail "Dockerfile missing for $service"
    fi
done

# Test 9: Documentation
echo -e "\n${BLUE}Testing Documentation${NC}"
echo "======================"

print_test "Checking remediation documentation..."
if [ -f "REMEDIATION_REPORT.md" ]; then
    print_pass "Remediation report exists"
else
    print_fail "Remediation report missing"
fi

# Test 10: Script Permissions
echo -e "\n${BLUE}Testing Script Permissions${NC}"
echo "==========================="

print_test "Checking script permissions..."
if [ -x "scripts/fix_ci_failures.sh" ]; then
    print_pass "Fix script is executable"
else
    print_fail "Fix script is not executable"
fi

# Final Summary
echo -e "\n${BLUE}Validation Summary${NC}"
echo "=================="
echo "Tests Passed: $PASSED"
echo "Tests Failed: $FAILED"
echo "Warnings: $WARNINGS"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All critical tests passed! System is ready for deployment.${NC}"
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo "1. Run: docker-compose -f config/docker/docker-compose.yml up --build -d"
    echo "2. Wait for services to start (2-3 minutes)"
    echo "3. Test health endpoints: curl http://localhost:8000/health"
    echo "4. Check monitoring: http://localhost:9090 (Prometheus)"
    echo "5. View logs: docker-compose -f config/docker/docker-compose.yml logs -f"
    exit 0
else
    echo -e "\n${RED}❌ $FAILED critical tests failed. Please review and fix issues.${NC}"
    exit 1
fi
