#!/usr/bin/env python3
"""
Phase 3 Algorithmic Fairness Test Script for ACGS-PGP
Tests the bias detection and fairness validation implementation
"""

import asyncio
import json
import sys
import time
from typing import Dict, List, Any
import httpx

# Test configuration
BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "admin_token"  # Replace with actual admin token
TEST_TIMEOUT = 30

class Phase3FairnessTestRunner:
    """Test runner for Phase 3 algorithmic fairness features."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        self.headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test_result(self, test_name: str, passed: bool, message: str):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": time.time()
        })
    
    async def test_bias_metrics_endpoint(self):
        """Test available bias metrics endpoint."""
        test_name = "Available Bias Metrics Endpoint"
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/fv/bias-metrics",
                headers=self.headers
            )
            
            if response.status_code == 200:
                metrics = response.json()
                if len(metrics) >= 4:  # Should have at least 4 predefined metrics
                    required_fields = ["metric_id", "metric_type", "metric_name", "description"]
                    if all(field in metrics[0] for field in required_fields):
                        self.log_test_result(test_name, True, f"Retrieved {len(metrics)} bias metrics")
                    else:
                        self.log_test_result(test_name, False, "Missing required fields in bias metrics")
                else:
                    self.log_test_result(test_name, False, f"Expected at least 4 metrics, got {len(metrics)}")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_fairness_properties_endpoint(self):
        """Test available fairness properties endpoint."""
        test_name = "Available Fairness Properties Endpoint"
        
        try:
            response = await self.client.get(
                f"{BASE_URL}/fv/fairness-properties",
                headers=self.headers
            )
            
            if response.status_code == 200:
                properties = response.json()
                if len(properties) >= 4:  # Should have at least 4 predefined properties
                    required_fields = ["property_id", "property_type", "property_name", "description"]
                    if all(field in properties[0] for field in required_fields):
                        self.log_test_result(test_name, True, f"Retrieved {len(properties)} fairness properties")
                    else:
                        self.log_test_result(test_name, False, "Missing required fields in fairness properties")
                else:
                    self.log_test_result(test_name, False, f"Expected at least 4 properties, got {len(properties)}")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_bias_detection_analysis(self):
        """Test bias detection analysis functionality."""
        test_name = "Bias Detection Analysis"
        
        try:
            # Test data for bias detection
            test_data = {
                "policy_rule_ids": [1, 2],
                "bias_metrics": [
                    {
                        "metric_id": "demographic_parity",
                        "metric_type": "statistical",
                        "metric_name": "Demographic Parity",
                        "description": "Test demographic parity",
                        "threshold": 0.1
                    },
                    {
                        "metric_id": "counterfactual_fairness",
                        "metric_type": "counterfactual",
                        "metric_name": "Counterfactual Fairness",
                        "description": "Test counterfactual fairness",
                        "threshold": 0.2
                    }
                ],
                "fairness_properties": [
                    {
                        "property_id": "demographic_parity",
                        "property_type": "demographic_parity",
                        "property_name": "Demographic Parity",
                        "description": "Equal positive outcome rates",
                        "protected_attributes": ["race", "gender"],
                        "threshold": 0.1,
                        "criticality_level": "high"
                    }
                ],
                "protected_attributes": ["race", "gender", "age"],
                "analysis_type": "comprehensive"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/fv/bias-detection",
                headers=self.headers,
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ["policy_rule_ids", "results", "overall_bias_score", "risk_level", "summary"]
                if all(field in result for field in required_fields):
                    self.log_test_result(test_name, True, f"Bias analysis completed with risk level: {result['risk_level']}")
                else:
                    self.log_test_result(test_name, False, "Missing required fields in bias detection response")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_fairness_validation_analysis(self):
        """Test fairness validation analysis functionality."""
        test_name = "Fairness Validation Analysis"
        
        try:
            # Test data for fairness validation
            test_data = {
                "policy_rule_ids": [1, 2],
                "fairness_properties": [
                    {
                        "property_id": "demographic_parity",
                        "property_type": "demographic_parity",
                        "property_name": "Demographic Parity",
                        "description": "Equal positive outcome rates",
                        "protected_attributes": ["race", "gender"],
                        "threshold": 0.1,
                        "criticality_level": "high"
                    },
                    {
                        "property_id": "equalized_odds",
                        "property_type": "equalized_odds",
                        "property_name": "Equalized Odds",
                        "description": "Equal true/false positive rates",
                        "protected_attributes": ["race", "gender"],
                        "threshold": 0.1,
                        "criticality_level": "high"
                    }
                ]
            }
            
            response = await self.client.post(
                f"{BASE_URL}/fv/fairness-validation",
                headers=self.headers,
                json=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ["policy_rule_ids", "results", "overall_fairness_score", "compliance_status", "summary"]
                if all(field in result for field in required_fields):
                    self.log_test_result(test_name, True, f"Fairness validation completed with status: {result['compliance_status']}")
                else:
                    self.log_test_result(test_name, False, "Missing required fields in fairness validation response")
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_comprehensive_fairness_workflow(self):
        """Test comprehensive fairness analysis workflow."""
        test_name = "Comprehensive Fairness Workflow"
        
        try:
            # Step 1: Get available metrics
            metrics_response = await self.client.get(
                f"{BASE_URL}/fv/bias-metrics",
                headers=self.headers
            )
            
            if metrics_response.status_code != 200:
                self.log_test_result(test_name, False, "Failed to get bias metrics")
                return
            
            # Step 2: Get available properties
            properties_response = await self.client.get(
                f"{BASE_URL}/fv/fairness-properties",
                headers=self.headers
            )
            
            if properties_response.status_code != 200:
                self.log_test_result(test_name, False, "Failed to get fairness properties")
                return
            
            # Step 3: Run bias detection with retrieved metrics
            metrics = metrics_response.json()[:2]  # Use first 2 metrics
            properties = properties_response.json()[:2]  # Use first 2 properties
            
            workflow_data = {
                "policy_rule_ids": [1],
                "bias_metrics": metrics,
                "fairness_properties": properties,
                "protected_attributes": ["race", "gender"],
                "analysis_type": "comprehensive"
            }
            
            bias_response = await self.client.post(
                f"{BASE_URL}/fv/bias-detection",
                headers=self.headers,
                json=workflow_data
            )
            
            if bias_response.status_code != 200:
                self.log_test_result(test_name, False, "Failed bias detection in workflow")
                return
            
            # Step 4: Run fairness validation
            fairness_data = {
                "policy_rule_ids": [1],
                "fairness_properties": properties
            }
            
            fairness_response = await self.client.post(
                f"{BASE_URL}/fv/fairness-validation",
                headers=self.headers,
                json=fairness_data
            )
            
            if fairness_response.status_code == 200:
                bias_result = bias_response.json()
                fairness_result = fairness_response.json()
                
                self.log_test_result(
                    test_name, 
                    True, 
                    f"Workflow completed: Bias risk {bias_result['risk_level']}, "
                    f"Fairness status {fairness_result['compliance_status']}"
                )
            else:
                self.log_test_result(test_name, False, "Failed fairness validation in workflow")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all Phase 3 algorithmic fairness tests."""
        print("🚀 Starting Phase 3 Algorithmic Fairness Tests")
        print("=" * 50)
        
        # Test sequence
        tests = [
            self.test_bias_metrics_endpoint,
            self.test_fairness_properties_endpoint,
            self.test_bias_detection_analysis,
            self.test_fairness_validation_analysis,
            self.test_comprehensive_fairness_workflow
        ]
        
        for test in tests:
            await test()
            await asyncio.sleep(0.5)  # Brief pause between tests
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        passed_tests = [r for r in self.test_results if r["passed"]]
        failed_tests = [r for r in self.test_results if not r["passed"]]
        
        print(f"✅ Passed: {len(passed_tests)}/{len(self.test_results)}")
        print(f"❌ Failed: {len(failed_tests)}/{len(self.test_results)}")
        
        if failed_tests:
            print("\nFailed Tests:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['message']}")
        
        # Save results
        with open("phase3_fairness_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        return len(failed_tests) == 0


async def main():
    """Main test execution."""
    print("Phase 3 Algorithmic Fairness Test Suite")
    print("Testing bias detection and fairness validation features")
    print()
    
    async with Phase3FairnessTestRunner() as test_runner:
        success = await test_runner.run_all_tests()
        
        if success:
            print("\n🎉 All Phase 3 algorithmic fairness tests passed!")
            sys.exit(0)
        else:
            print("\n💥 Some Phase 3 algorithmic fairness tests failed!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
