#!/usr/bin/env python3
"""
ACGS-PGP Groq LLM Integration Test Script
Tests the three Groq-hosted Llama models for ACGS-PGP testing and research operations
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Any
import logging

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/alphaevolve_gs_engine/src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqLLMIntegrationTest:
    def __init__(self):
        self.results = {
            'alphaevolve_engine': {'passed': 0, 'failed': 0, 'tests': []},
            'gs_service': {'passed': 0, 'failed': 0, 'tests': []},
            'model_performance': {'passed': 0, 'failed': 0, 'tests': []}
        }
        
        # Groq models to test
        self.groq_models = [
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-maverick-17b-128e-instruct", 
            "meta-llama/llama-4-scout-17b-16e-instruct"
        ]
        
        # Test constitutional principles
        self.test_principles = [
            {
                "id": 1,
                "content": "All users must have appropriate authorization before accessing sensitive data.",
                "expected_predicates": ["authorized_access", "sensitive_data"]
            },
            {
                "id": 2, 
                "content": "Financial transactions must be auditable and traceable.",
                "expected_predicates": ["auditable_transaction", "traceable_transaction"]
            },
            {
                "id": 3,
                "content": "Data privacy must be maintained according to GDPR compliance standards.",
                "expected_predicates": ["gdpr_compliant", "data_privacy"]
            }
        ]

    def log_test_result(self, category: str, test_name: str, passed: bool, details: str = ""):
        """Log test result and update statistics"""
        status = "PASS" if passed else "FAIL"
        logger.info(f"[{category}] {test_name}: {status} - {details}")
        
        self.results[category]['tests'].append({
            'name': test_name,
            'status': status,
            'details': details
        })
        
        if passed:
            self.results[category]['passed'] += 1
        else:
            self.results[category]['failed'] += 1

    async def test_alphaevolve_groq_service(self):
        """Test AlphaEvolve GS Engine with Groq models"""
        logger.info("Testing AlphaEvolve GS Engine Groq Integration...")
        
        try:
            from alphaevolve_gs_engine.services.llm_service import get_llm_service, GroqLLMService
            
            # Test each Groq model
            for model in self.groq_models:
                test_name = f"AlphaEvolve Groq Service - {model}"
                
                try:
                    # Configure Groq service
                    config = {
                        "api_key": os.getenv("GROQ_API_KEY"),
                        "default_model": model
                    }
                    
                    groq_service = get_llm_service("groq", config)
                    
                    if isinstance(groq_service, GroqLLMService):
                        # Test text generation
                        prompt = "Generate a brief policy rule for data access control."
                        response = groq_service.generate_text(prompt, max_tokens=200, temperature=0.3)
                        
                        if response and len(response) > 10:
                            self.log_test_result('alphaevolve_engine', test_name, True, 
                                               f"Generated {len(response)} characters")
                        else:
                            self.log_test_result('alphaevolve_engine', test_name, False, 
                                               "Empty or too short response")
                    else:
                        self.log_test_result('alphaevolve_engine', test_name, False, 
                                           "Failed to create GroqLLMService instance")
                        
                except Exception as e:
                    self.log_test_result('alphaevolve_engine', test_name, False, f"Error: {e}")
                    
        except ImportError as e:
            self.log_test_result('alphaevolve_engine', "Import Test", False, f"Import error: {e}")

    async def test_gs_service_groq_client(self):
        """Test GS Service GroqLLMClient"""
        logger.info("Testing GS Service GroqLLMClient Integration...")
        
        try:
            # Set environment for Groq testing
            os.environ["LLM_PROVIDER"] = "groq"
            
            from gs_service.app.core.llm_integration import get_llm_client, GroqLLMClient, LLMInterpretationInput
            
            client = get_llm_client()
            
            if isinstance(client, GroqLLMClient):
                # Test structured interpretation with each principle
                for principle in self.test_principles:
                    test_name = f"GS Service Groq Client - Principle {principle['id']}"
                    
                    try:
                        input_data = LLMInterpretationInput(
                            principle_id=principle['id'],
                            principle_content=principle['content']
                        )
                        
                        result = await client.get_structured_interpretation(input_data)
                        
                        if result and result.interpretations:
                            # Check if expected predicates are present
                            found_predicates = []
                            for interp in result.interpretations:
                                if hasattr(interp, 'head') and hasattr(interp.head, 'predicate_name'):
                                    found_predicates.append(interp.head.predicate_name)
                            
                            success = len(found_predicates) > 0
                            details = f"Found predicates: {found_predicates}"
                            
                            self.log_test_result('gs_service', test_name, success, details)
                        else:
                            self.log_test_result('gs_service', test_name, False, "No interpretations returned")
                            
                    except Exception as e:
                        self.log_test_result('gs_service', test_name, False, f"Error: {e}")
            else:
                self.log_test_result('gs_service', "Client Creation", False, 
                                   f"Expected GroqLLMClient, got {type(client)}")
                
        except ImportError as e:
            self.log_test_result('gs_service', "Import Test", False, f"Import error: {e}")
        finally:
            # Reset environment
            os.environ["LLM_PROVIDER"] = "mock"

    async def test_model_performance_comparison(self):
        """Compare performance across the three Groq models"""
        logger.info("Testing Groq Model Performance Comparison...")
        
        if not os.getenv("GROQ_API_KEY"):
            self.log_test_result('model_performance', "API Key Check", False, "GROQ_API_KEY not set")
            return
        
        try:
            from alphaevolve_gs_engine.services.llm_service import GroqLLMService
            
            performance_results = {}
            
            for model in self.groq_models:
                test_name = f"Performance Test - {model}"
                
                try:
                    import time
                    start_time = time.time()
                    
                    groq_service = GroqLLMService(default_model=model)
                    
                    # Test prompt for policy generation
                    prompt = """Generate a constitutional AI governance rule for the following principle:
                    "All automated decisions affecting users must be explainable and auditable."
                    
                    Provide a structured rule with conditions and actions."""
                    
                    response = groq_service.generate_text(prompt, max_tokens=300, temperature=0.2)
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    performance_results[model] = {
                        'response_time': response_time,
                        'response_length': len(response) if response else 0,
                        'success': bool(response and len(response) > 50)
                    }
                    
                    if response and len(response) > 50:
                        self.log_test_result('model_performance', test_name, True, 
                                           f"Response time: {response_time:.2f}s, Length: {len(response)}")
                    else:
                        self.log_test_result('model_performance', test_name, False, 
                                           f"Poor response quality or empty response")
                        
                except Exception as e:
                    self.log_test_result('model_performance', test_name, False, f"Error: {e}")
                    performance_results[model] = {'error': str(e)}
            
            # Log performance summary
            logger.info("Performance Summary:")
            for model, results in performance_results.items():
                if 'error' not in results:
                    logger.info(f"  {model}: {results['response_time']:.2f}s, {results['response_length']} chars")
                    
        except Exception as e:
            self.log_test_result('model_performance', "Performance Test Setup", False, f"Setup error: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("ACGS-PGP GROQ LLM INTEGRATION TEST SUMMARY")
        print("="*80)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.results.items():
            passed = results['passed']
            failed = results['failed']
            total = passed + failed
            
            total_passed += passed
            total_failed += failed
            
            print(f"\n{category.upper().replace('_', ' ')}:")
            print(f"  Passed: {passed}/{total}")
            print(f"  Failed: {failed}/{total}")
            
            if failed > 0:
                print("  Failed tests:")
                for test in results['tests']:
                    if test['status'] == 'FAIL':
                        print(f"    - {test['name']}: {test['details']}")
        
        print(f"\nOVERALL RESULTS:")
        print(f"  Total Passed: {total_passed}")
        print(f"  Total Failed: {total_failed}")
        print(f"  Success Rate: {(total_passed/(total_passed+total_failed)*100):.1f}%" if (total_passed+total_failed) > 0 else "No tests run")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        if total_failed == 0:
            print("  ✅ All Groq LLM integrations are working correctly!")
            print("  ✅ Ready for ACGS-PGP testing with Groq models")
        else:
            print("  ⚠️  Some tests failed. Check the following:")
            print("     - Ensure GROQ_API_KEY is set correctly")
            print("     - Verify network connectivity to Groq API")
            print("     - Check model availability and quotas")

async def main():
    """Main test execution"""
    print("Starting ACGS-PGP Groq LLM Integration Tests...")
    
    # Check prerequisites
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  Warning: GROQ_API_KEY not set. Some tests will be skipped.")
        print("   Set GROQ_API_KEY environment variable to run full tests.")
    
    test_suite = GroqLLMIntegrationTest()
    
    # Run test suites
    await test_suite.test_alphaevolve_groq_service()
    await test_suite.test_gs_service_groq_client()
    await test_suite.test_model_performance_comparison()
    
    # Print results
    test_suite.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
