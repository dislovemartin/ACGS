"""
Verification Completeness Testing

This module addresses the technical review finding that SMT assertions
need verification completeness testing to ensure they properly differentiate
positive vs negative cases.
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
import time

from .smt_solver_integration import verify_rules_against_obligations, SMTSolverOutput

logger = logging.getLogger(__name__)


@dataclass
class VerificationTestCase:
    """A test case for verification completeness."""
    name: str
    description: str
    rules: List[str]
    obligations: List[str]
    expected_result: str  # "verified", "failed", "inconclusive"
    test_type: str  # "positive", "negative", "boundary"
    rationale: str


@dataclass
class CompletenessTestResult:
    """Result of completeness testing."""
    test_case_name: str
    expected_result: str
    actual_result: str
    passed: bool
    execution_time_ms: int
    counter_example: Optional[str]
    error_message: Optional[str]


class VerificationCompletenessTester:
    """Tests verification completeness to ensure proper positive/negative case differentiation."""
    
    def __init__(self):
        self.test_cases = self._create_test_cases()
    
    def _create_test_cases(self) -> List[VerificationTestCase]:
        """Create comprehensive test cases for verification completeness."""
        return [
            # Positive cases (should verify)
            VerificationTestCase(
                name="CP-SAFETY-001-POSITIVE",
                description="Arithmetic safety with proper bounds checking",
                rules=[
                    "safe_arithmetic(X, Y, Op) :- Op = 'add', X >= 0, Y >= 0, X + Y <= 1000.",
                    "safe_arithmetic(X, Y, Op) :- Op = 'multiply', X >= 0, Y >= 0, X * Y <= 1000.",
                    "safe_arithmetic(X, Y, Op) :- Op = 'divide', X >= 0, Y > 0."
                ],
                obligations=[
                    "forall X Y Op: safe_arithmetic(X, Y, Op) -> (Op != 'divide' or Y > 0)"
                ],
                expected_result="verified",
                test_type="positive",
                rationale="Division by zero is properly prevented"
            ),
            
            # Negative cases (should fail verification)
            VerificationTestCase(
                name="CP-SAFETY-001-NEGATIVE",
                description="Arithmetic safety with division by zero vulnerability",
                rules=[
                    "unsafe_arithmetic(X, Y, Op) :- Op = 'add', X >= 0, Y >= 0.",
                    "unsafe_arithmetic(X, Y, Op) :- Op = 'divide', X >= 0."  # Missing Y > 0 check
                ],
                obligations=[
                    "forall X Y Op: unsafe_arithmetic(X, Y, Op) -> (Op != 'divide' or Y > 0)"
                ],
                expected_result="failed",
                test_type="negative",
                rationale="Division by zero is not prevented - should fail verification"
            ),
            
            VerificationTestCase(
                name="CP-ACCESS-001-POSITIVE",
                description="Role-based access control with proper authorization",
                rules=[
                    "access_allowed(User, Resource) :- has_role(User, admin).",
                    "access_allowed(User, Resource) :- has_role(User, owner), owns(User, Resource).",
                    "has_role(alice, admin).",
                    "has_role(bob, owner).",
                    "owns(bob, document1)."
                ],
                obligations=[
                    "forall User Resource: access_allowed(User, Resource) -> (has_role(User, admin) or (has_role(User, owner) and owns(User, Resource)))"
                ],
                expected_result="verified",
                test_type="positive",
                rationale="Access control properly enforces role-based permissions"
            ),
            
            VerificationTestCase(
                name="CP-ACCESS-001-NEGATIVE",
                description="Role-based access control with authorization bypass",
                rules=[
                    "access_allowed(User, Resource) :- true."  # Always allow - security vulnerability
                ],
                obligations=[
                    "forall User Resource: access_allowed(User, Resource) -> has_role(User, admin)"
                ],
                expected_result="failed",
                test_type="negative",
                rationale="Access control bypassed - should fail verification"
            ),
            
            VerificationTestCase(
                name="CP-PRIVACY-001-POSITIVE",
                description="Data privacy with proper encryption enforcement",
                rules=[
                    "data_access_allowed(User, Data) :- is_public(Data).",
                    "data_access_allowed(User, Data) :- is_private(Data), has_permission(User, Data), is_encrypted(Data).",
                    "is_encrypted(Data) :- is_private(Data), has_encryption_key(Data)."
                ],
                obligations=[
                    "forall User Data: (data_access_allowed(User, Data) and is_private(Data)) -> is_encrypted(Data)"
                ],
                expected_result="verified",
                test_type="positive",
                rationale="Private data access requires encryption"
            ),
            
            VerificationTestCase(
                name="CP-PRIVACY-001-NEGATIVE",
                description="Data privacy with missing encryption",
                rules=[
                    "data_access_allowed(User, Data) :- is_public(Data).",
                    "data_access_allowed(User, Data) :- is_private(Data), has_permission(User, Data)."  # Missing encryption check
                ],
                obligations=[
                    "forall User Data: (data_access_allowed(User, Data) and is_private(Data)) -> is_encrypted(Data)"
                ],
                expected_result="failed",
                test_type="negative",
                rationale="Private data access without encryption - should fail verification"
            ),
            
            # Boundary cases
            VerificationTestCase(
                name="CP-BOUNDARY-001",
                description="Edge case with empty rules",
                rules=[],
                obligations=[
                    "forall X: safe_operation(X) -> X > 0"
                ],
                expected_result="inconclusive",
                test_type="boundary",
                rationale="No rules provided - verification should be inconclusive"
            ),
            
            VerificationTestCase(
                name="CP-BOUNDARY-002",
                description="Complex logical dependencies",
                rules=[
                    "complex_rule(X) :- condition_a(X), condition_b(X).",
                    "condition_a(X) :- X > 0, X < 100.",
                    "condition_b(X) :- X % 2 = 0."  # Even numbers
                ],
                obligations=[
                    "forall X: complex_rule(X) -> (X > 0 and X < 100 and X % 2 = 0)"
                ],
                expected_result="verified",
                test_type="boundary",
                rationale="Complex logical dependencies should be properly verified"
            )
        ]
    
    async def run_completeness_tests(self) -> Dict[str, Any]:
        """Run all completeness tests and return comprehensive results."""
        logger.info("Starting verification completeness testing")
        start_time = time.time()
        
        results = []
        passed_count = 0
        failed_count = 0
        error_count = 0
        
        for test_case in self.test_cases:
            try:
                result = await self._run_single_test(test_case)
                results.append(result)
                
                if result.passed:
                    passed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error running test case {test_case.name}: {e}")
                error_result = CompletenessTestResult(
                    test_case_name=test_case.name,
                    expected_result=test_case.expected_result,
                    actual_result="error",
                    passed=False,
                    execution_time_ms=0,
                    counter_example=None,
                    error_message=str(e)
                )
                results.append(error_result)
                error_count += 1
        
        total_time = time.time() - start_time
        
        # Analyze results by test type
        positive_tests = [r for r in results if any(tc.test_type == "positive" and tc.name == r.test_case_name for tc in self.test_cases)]
        negative_tests = [r for r in results if any(tc.test_type == "negative" and tc.name == r.test_case_name for tc in self.test_cases)]
        boundary_tests = [r for r in results if any(tc.test_type == "boundary" and tc.name == r.test_case_name for tc in self.test_cases)]
        
        positive_pass_rate = sum(1 for r in positive_tests if r.passed) / len(positive_tests) if positive_tests else 0
        negative_pass_rate = sum(1 for r in negative_tests if r.passed) / len(negative_tests) if negative_tests else 0
        boundary_pass_rate = sum(1 for r in boundary_tests if r.passed) / len(boundary_tests) if boundary_tests else 0
        
        summary = {
            "total_tests": len(results),
            "passed": passed_count,
            "failed": failed_count,
            "errors": error_count,
            "overall_pass_rate": passed_count / len(results) if results else 0,
            "positive_case_pass_rate": positive_pass_rate,
            "negative_case_pass_rate": negative_pass_rate,
            "boundary_case_pass_rate": boundary_pass_rate,
            "total_execution_time_seconds": total_time,
            "verification_completeness_score": self._calculate_completeness_score(results),
            "detailed_results": [self._result_to_dict(r) for r in results]
        }
        
        logger.info(f"Completeness testing completed: {passed_count}/{len(results)} tests passed")
        return summary
    
    async def _run_single_test(self, test_case: VerificationTestCase) -> CompletenessTestResult:
        """Run a single verification test case."""
        logger.debug(f"Running test case: {test_case.name}")
        start_time = time.time()
        
        try:
            # Run verification
            smt_output = await verify_rules_against_obligations(
                test_case.rules,
                test_case.obligations
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Determine actual result
            if smt_output.error_message:
                actual_result = "error"
            elif smt_output.is_unsatisfiable:
                actual_result = "verified"
            elif smt_output.is_satisfiable:
                actual_result = "failed"
            else:
                actual_result = "inconclusive"
            
            # Check if result matches expectation
            passed = actual_result == test_case.expected_result
            
            return CompletenessTestResult(
                test_case_name=test_case.name,
                expected_result=test_case.expected_result,
                actual_result=actual_result,
                passed=passed,
                execution_time_ms=execution_time,
                counter_example=smt_output.counter_example,
                error_message=smt_output.error_message
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return CompletenessTestResult(
                test_case_name=test_case.name,
                expected_result=test_case.expected_result,
                actual_result="error",
                passed=False,
                execution_time_ms=execution_time,
                counter_example=None,
                error_message=str(e)
            )
    
    def _calculate_completeness_score(self, results: List[CompletenessTestResult]) -> float:
        """Calculate a completeness score based on test results."""
        if not results:
            return 0.0
        
        # Weight different test types
        positive_weight = 0.4  # Correctly verifying valid cases
        negative_weight = 0.4  # Correctly rejecting invalid cases
        boundary_weight = 0.2  # Handling edge cases
        
        positive_score = 0.0
        negative_score = 0.0
        boundary_score = 0.0
        
        positive_count = negative_count = boundary_count = 0
        
        for result in results:
            test_case = next((tc for tc in self.test_cases if tc.name == result.test_case_name), None)
            if not test_case:
                continue
            
            if test_case.test_type == "positive":
                positive_count += 1
                if result.passed:
                    positive_score += 1
            elif test_case.test_type == "negative":
                negative_count += 1
                if result.passed:
                    negative_score += 1
            elif test_case.test_type == "boundary":
                boundary_count += 1
                if result.passed:
                    boundary_score += 1
        
        # Normalize scores
        positive_norm = positive_score / positive_count if positive_count > 0 else 0
        negative_norm = negative_score / negative_count if negative_count > 0 else 0
        boundary_norm = boundary_score / boundary_count if boundary_count > 0 else 0
        
        # Calculate weighted score
        completeness_score = (
            positive_weight * positive_norm +
            negative_weight * negative_norm +
            boundary_weight * boundary_norm
        )
        
        return completeness_score
    
    def _result_to_dict(self, result: CompletenessTestResult) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "test_case_name": result.test_case_name,
            "expected_result": result.expected_result,
            "actual_result": result.actual_result,
            "passed": result.passed,
            "execution_time_ms": result.execution_time_ms,
            "counter_example": result.counter_example,
            "error_message": result.error_message
        }


# Example usage
async def run_completeness_testing_example():
    """Example of running verification completeness testing."""
    tester = VerificationCompletenessTester()
    results = await tester.run_completeness_tests()
    
    print("=== Verification Completeness Test Results ===")
    print(json.dumps(results, indent=2))
    
    # Check for critical issues
    if results["negative_case_pass_rate"] < 0.8:
        print("⚠️  WARNING: Low negative case pass rate - verification may not properly detect violations")
    
    if results["positive_case_pass_rate"] < 0.8:
        print("⚠️  WARNING: Low positive case pass rate - verification may be too strict")
    
    if results["verification_completeness_score"] < 0.7:
        print("❌ CRITICAL: Low verification completeness score - SMT encoding needs improvement")
    else:
        print("✅ Verification completeness score acceptable")


if __name__ == "__main__":
    asyncio.run(run_completeness_testing_example())
