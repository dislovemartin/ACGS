#!/bin/bash

# ACGS Development Tasks - Test Execution Script
# This script runs all tests for the completed development tasks

echo "🧪 Running ACGS Development Tasks Test Suite"
echo "=============================================="

# Set up environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export ENVIRONMENT=testing

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run tests with proper error handling
run_test() {
    local test_file=$1
    local test_name=$2
    
    echo -e "\n${BLUE}📋 Running: $test_name${NC}"
    echo "----------------------------------------"
    
    if python -m pytest "$test_file" -v --tb=short; then
        echo -e "${GREEN}✅ $test_name: PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name: FAILED${NC}"
        return 1
    fi
}

# Initialize test results
total_tests=0
passed_tests=0

# Task 1.2: Constitutional Council Test Fixtures
echo -e "\n${YELLOW}🏛️  Task 1.2: Constitutional Council Test Fixtures${NC}"
if run_test "tests/test_constitutional_council_fixtures.py" "Constitutional Council Fixtures"; then
    ((passed_tests++))
fi
((total_tests++))

# Task 2.1: Pydantic v2.0+ Schema Migration Tests
echo -e "\n${YELLOW}🔄 Task 2.1: Pydantic v2.0+ Schema Migration${NC}"
echo "Testing updated schemas..."

# Test federated service schemas
if python -c "
import sys
sys.path.append('.')
try:
    from src.backend.federated_service.app.schemas import PolicyEvaluationRequest, FederatedLearningRequest
    from pydantic import ValidationError
    
    # Test PolicyEvaluationRequest
    test_data = {
        'policy_content': 'test policy',
        'evaluation_criteria': {'category': 'test'},
        'target_platforms': ['cloud_openai'],
        'privacy_requirements': {'epsilon': 1.0}
    }
    
    request = PolicyEvaluationRequest(**test_data)
    print('✅ PolicyEvaluationRequest validation: PASSED')
    
    # Test FederatedLearningRequest  
    fl_data = {
        'min_participants': 2,
        'max_participants': 5,
        'aggregation_method': 'federated_averaging'
    }
    
    fl_request = FederatedLearningRequest(**fl_data)
    print('✅ FederatedLearningRequest validation: PASSED')
    
    print('✅ Pydantic v2.0+ Schema Migration: PASSED')
except Exception as e:
    print(f'❌ Pydantic v2.0+ Schema Migration: FAILED - {e}')
    sys.exit(1)
"; then
    ((passed_tests++))
fi
((total_tests++))

# Task 1.3: Centralized Configuration Management
echo -e "\n${YELLOW}⚙️  Task 1.3: Centralized Configuration Management${NC}"
if run_test "tests/test_centralized_configuration.py" "Centralized Configuration Management"; then
    ((passed_tests++))
fi
((total_tests++))

# Task 3.1: Enhanced Multi-Model Validation
echo -e "\n${YELLOW}🔍 Task 3.1: Enhanced Multi-Model Validation${NC}"
if run_test "tests/test_enhanced_multi_model_validation.py" "Enhanced Multi-Model Validation"; then
    ((passed_tests++))
fi
((total_tests++))

# Integration Tests
echo -e "\n${YELLOW}🔗 Integration Tests${NC}"
echo "Testing integration between components..."

if python -c "
import sys
sys.path.append('.')
try:
    # Test configuration integration
    from src.backend.shared.utils import ACGSConfig, Environment
    config = ACGSConfig()
    validated_config = config.get_validated_config()
    print('✅ Configuration integration: PASSED')
    
    # Test enhanced validation integration
    from src.backend.fv_service.app.core.enhanced_multi_model_validation import create_enhanced_multi_model_validator, create_validation_context
    validator = create_enhanced_multi_model_validator()
    context = create_validation_context('test', {'policy_rule': []})
    print('✅ Multi-model validation integration: PASSED')
    
    # Test fixtures integration
    from tests.fixtures.constitutional_council import ConstitutionalCouncilTestUtils
    edge_cases = ConstitutionalCouncilTestUtils.create_edge_case_scenarios()
    print('✅ Constitutional Council fixtures integration: PASSED')
    
    print('✅ Integration Tests: PASSED')
except Exception as e:
    print(f'❌ Integration Tests: FAILED - {e}')
    sys.exit(1)
"; then
    ((passed_tests++))
fi
((total_tests++))

# Legacy Integration Scripts converted to pytest
echo -e "\n${YELLOW}🧩 Legacy Integration Scripts${NC}"
pytest tests/integration/legacy -v
exit_code=$?
if [ $exit_code -eq 0 ] || [ $exit_code -eq 5 ]; then
    ((passed_tests++))
else
    echo -e "${RED}❌ Legacy integration scripts failed${NC}"
fi
((total_tests++))

# Summary
echo -e "\n${BLUE}📊 Test Results Summary${NC}"
echo "=============================================="
echo -e "Total Tests: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$((total_tests - passed_tests))${NC}"

if [ $passed_tests -eq $total_tests ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Development tasks completed successfully.${NC}"
    echo -e "\n${BLUE}📋 Completed Tasks:${NC}"
    echo "✅ Task 1.2: Constitutional Council Test Fixtures"
    echo "✅ Task 2.1: Pydantic v2.0+ Schema Migration"  
    echo "✅ Task 1.3: Centralized Configuration Management"
    echo "✅ Task 3.1: Enhanced Multi-Model Validation"
    
    echo -e "\n${BLUE}🚀 Next Steps:${NC}"
    echo "1. Review the implemented features"
    echo "2. Run integration tests with your existing codebase"
    echo "3. Update documentation as needed"
    echo "4. Deploy to staging environment for further testing"
    
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please review the output above.${NC}"
    exit 1
fi
