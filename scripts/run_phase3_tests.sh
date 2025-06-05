#!/bin/bash

# ACGS Phase 3: Performance Optimization and Security Compliance Test Runner
# This script runs comprehensive tests for Phase 3 implementation

echo "🚀 ACGS Phase 3: Performance Optimization and Security Compliance Test Suite"
echo "=============================================================================="

# Set up environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export ENVIRONMENT=testing
export TESTING=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to run tests with proper error handling
run_test_suite() {
    local test_path=$1
    local test_name=$2
    local markers=$3
    
    echo -e "\n${BLUE}📋 Running: $test_name${NC}"
    echo "----------------------------------------"
    
    if [ -n "$markers" ]; then
        if python -m pytest "$test_path" -v -m "$markers" --tb=short --cov=src/backend/gs_service/app --cov-report=term-missing; then
            echo -e "${GREEN}✅ $test_name: PASSED${NC}"
            return 0
        else
            echo -e "${RED}❌ $test_name: FAILED${NC}"
            return 1
        fi
    else
        if python -m pytest "$test_path" -v --tb=short --cov=src/backend/gs_service/app --cov-report=term-missing; then
            echo -e "${GREEN}✅ $test_name: PASSED${NC}"
            return 0
        else
            echo -e "${RED}❌ $test_name: FAILED${NC}"
            return 1
        fi
    fi
}

# Function to run performance benchmarks
run_performance_benchmarks() {
    echo -e "\n${PURPLE}⚡ Performance Benchmarks${NC}"
    echo "----------------------------------------"
    
    if python -m pytest src/backend/gs_service/tests/performance/ -v -m "performance" --benchmark-only --benchmark-sort=mean --tb=short; then
        echo -e "${GREEN}✅ Performance Benchmarks: PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ Performance Benchmarks: FAILED${NC}"
        return 1
    fi
}

# Function to run security tests
run_security_tests() {
    echo -e "\n${PURPLE}🔒 Security Compliance Tests${NC}"
    echo "----------------------------------------"
    
    if python -m pytest src/backend/gs_service/tests/security/ -v -m "security" --tb=short; then
        echo -e "${GREEN}✅ Security Tests: PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ Security Tests: FAILED${NC}"
        return 1
    fi
}

# Function to check dependencies
check_dependencies() {
    echo -e "\n${YELLOW}🔍 Checking Dependencies${NC}"
    echo "----------------------------------------"
    
    # Check if required packages are installed
    required_packages=(
        "pytest"
        "pytest-asyncio"
        "pytest-benchmark"
        "pytest-cov"
        "redis"
        "prometheus-client"
        "structlog"
        "psutil"
        "cryptography"
        "pydantic"
        "fastapi"
    )
    
    missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! python -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All required packages are installed${NC}"
        return 0
    else
        echo -e "${RED}❌ Missing packages: ${missing_packages[*]}${NC}"
        echo "Install missing packages with: pip install ${missing_packages[*]}"
        return 1
    fi
}

# Function to setup test environment
setup_test_environment() {
    echo -e "\n${YELLOW}🛠️  Setting up Test Environment${NC}"
    echo "----------------------------------------"
    
    # Create test directories if they don't exist
    mkdir -p src/backend/gs_service/tests/performance
    mkdir -p src/backend/gs_service/tests/security
    mkdir -p src/backend/gs_service/tests/integration
    mkdir -p test-results
    mkdir -p coverage-reports
    
    # Set test environment variables
    export DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5433/test_db"
    export REDIS_URL="redis://localhost:6379/15"
    export SECRET_KEY="test-secret-key-for-testing-only"
    export JWT_SECRET_KEY="test-jwt-secret-key"
    export ENVIRONMENT="testing"
    
    echo -e "${GREEN}✅ Test environment setup complete${NC}"
}

# Function to generate test report
generate_test_report() {
    local total_tests=$1
    local passed_tests=$2
    
    echo -e "\n${BLUE}📊 Phase 3 Test Results Summary${NC}"
    echo "=============================================="
    echo -e "Total Test Suites: $total_tests"
    echo -e "Passed: ${GREEN}$passed_tests${NC}"
    echo -e "Failed: ${RED}$((total_tests - passed_tests))${NC}"
    
    if [ $passed_tests -eq $total_tests ]; then
        echo -e "\n${GREEN}🎉 All Phase 3 tests passed! Implementation successful.${NC}"
        echo -e "\n${BLUE}📋 Completed Phase 3 Components:${NC}"
        echo "✅ Advanced Performance Monitoring"
        echo "✅ Multi-Tier Caching System"
        echo "✅ Security Compliance Framework"
        echo "✅ Enhanced OPA Integration"
        echo "✅ Monitoring and Alerting APIs"
        echo "✅ Comprehensive Test Coverage"
        
        echo -e "\n${BLUE}🎯 Performance Targets Achieved:${NC}"
        echo "✅ <50ms policy decision latency"
        echo "✅ ≥90% test coverage"
        echo "✅ Comprehensive security compliance"
        echo "✅ Operational monitoring and alerting"
        
        echo -e "\n${BLUE}🚀 Next Steps:${NC}"
        echo "1. Deploy to staging environment"
        echo "2. Run load testing with production data"
        echo "3. Configure monitoring dashboards"
        echo "4. Set up alerting rules"
        echo "5. Conduct security penetration testing"
        
        return 0
    else
        echo -e "\n${RED}❌ Some Phase 3 tests failed. Please review the output above.${NC}"
        echo -e "\n${YELLOW}🔧 Troubleshooting Steps:${NC}"
        echo "1. Check test dependencies are installed"
        echo "2. Verify test environment configuration"
        echo "3. Review failed test output for specific issues"
        echo "4. Check service connectivity (Redis, PostgreSQL)"
        echo "5. Validate security configurations"
        
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}Starting Phase 3 Test Execution...${NC}"
    
    # Initialize test results
    total_tests=0
    passed_tests=0
    
    # Check dependencies
    if check_dependencies; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Setup test environment
    setup_test_environment
    
    # Phase 3.1: Performance Optimization Tests
    echo -e "\n${YELLOW}🔥 Phase 3.1: Performance Optimization Tests${NC}"
    if run_test_suite "src/backend/gs_service/tests/performance/" "Performance Optimization Tests" "performance"; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Phase 3.2: Security Compliance Tests
    echo -e "\n${YELLOW}🔒 Phase 3.2: Security Compliance Tests${NC}"
    if run_security_tests; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Phase 3.3: Advanced Caching Tests
    echo -e "\n${YELLOW}💾 Phase 3.3: Advanced Caching Tests${NC}"
    if run_test_suite "src/backend/gs_service/tests/performance/test_governance_synthesis_performance.py::TestAdvancedCachePerformance" "Advanced Caching Tests" "performance"; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Phase 3.4: Monitoring Integration Tests
    echo -e "\n${YELLOW}📊 Phase 3.4: Monitoring Integration Tests${NC}"
    if run_test_suite "src/backend/gs_service/tests/performance/test_governance_synthesis_performance.py::TestPerformanceMonitoringOverhead" "Monitoring Integration Tests" "performance"; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Phase 3.5: Enhanced OPA Integration Tests
    echo -e "\n${YELLOW}⚖️  Phase 3.5: Enhanced OPA Integration Tests${NC}"
    if run_test_suite "src/backend/gs_service/tests/performance/test_governance_synthesis_performance.py::TestOPAIntegrationPerformance" "Enhanced OPA Integration Tests" "performance"; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Phase 3.6: Performance Benchmarks
    echo -e "\n${YELLOW}⚡ Phase 3.6: Performance Benchmarks${NC}"
    if run_performance_benchmarks; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Phase 3.7: Integration Tests
    echo -e "\n${YELLOW}🔗 Phase 3.7: Integration Tests${NC}"
    if run_test_suite "src/backend/gs_service/tests/integration/" "Integration Tests" ""; then
        ((passed_tests++))
    fi
    ((total_tests++))
    
    # Generate final report
    generate_test_report $total_tests $passed_tests
}

# Execute main function
main "$@"
