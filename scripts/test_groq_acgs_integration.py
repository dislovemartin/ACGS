#!/usr/bin/env python3
"""
ACGS-PGP Groq Integration Test Script
Comprehensive testing of the three Groq-hosted Llama models for ACGS-PGP operations

This script tests:
1. llama-3.3-70b-versatile - Large versatile model for comprehensive testing
2. meta-llama/llama-4-maverick-17b-128e-instruct - Mid-size model with extended context  
3. meta-llama/llama-4-scout-17b-16e-instruct - Efficient model for rapid testing

Usage:
    python scripts/test_groq_acgs_integration.py
    
Environment Variables Required:
    GROQ_API_KEY - Your Groq API key
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, List, Any, Optional

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'src/backend'))
sys.path.insert(0, os.path.join(project_root, 'src/alphaevolve_gs_engine/src'))

class ACGSGroqTester:
    def __init__(self):
        self.groq_models = {
            "versatile": {
                "name": "llama-3.3-70b-versatile",
                "description": "Large versatile model for comprehensive testing and complex reasoning",
                "use_case": "Complex constitutional analysis and policy synthesis"
            },
            "maverick": {
                "name": "meta-llama/llama-4-maverick-17b-128e-instruct", 
                "description": "Mid-size model with extended context for research operations",
                "use_case": "Research-backed governance analysis with extended context"
            },
            "scout": {
                "name": "meta-llama/llama-4-scout-17b-16e-instruct",
                "description": "Efficient model for rapid testing and quick task generation", 
                "use_case": "Rapid policy validation and quick constitutional checks"
            }
        }
        
        self.test_scenarios = [
            {
                "name": "Constitutional Principle Interpretation",
                "principle": "All automated decisions affecting users must be explainable and auditable.",
                "expected_elements": ["explainable", "auditable", "automated_decision"]
            },
            {
                "name": "Data Privacy Governance",
                "principle": "Personal data must be processed lawfully, fairly, and transparently according to GDPR.",
                "expected_elements": ["lawful_processing", "fair_processing", "transparent_processing", "gdpr"]
            },
            {
                "name": "Access Control Policy",
                "principle": "Users must have appropriate authorization before accessing sensitive resources.",
                "expected_elements": ["authorization", "access_control", "sensitive_resources"]
            }
        ]
        
        self.results = {}

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check API key
        if not os.getenv("GROQ_API_KEY"):
            print("❌ GROQ_API_KEY environment variable not set")
            print("   Please set your Groq API key: export GROQ_API_KEY='your_key_here'")
            return False
        
        print("✅ GROQ_API_KEY is set")
        
        # Check imports
        try:
            from alphaevolve_gs_engine.services.llm_service import GroqLLMService
            print("✅ AlphaEvolve GS Engine imports available")
        except ImportError as e:
            print(f"❌ AlphaEvolve GS Engine import failed: {e}")
            return False
            
        return True

    async def test_alphaevolve_integration(self):
        """Test AlphaEvolve GS Engine with Groq models"""
        print("\n🧪 Testing AlphaEvolve GS Engine Integration...")
        
        try:
            from alphaevolve_gs_engine.services.llm_service import GroqLLMService
            
            for model_key, model_info in self.groq_models.items():
                print(f"\n📋 Testing {model_info['name']}...")
                print(f"   Use case: {model_info['use_case']}")
                
                try:
                    # Initialize service
                    service = GroqLLMService(default_model=model_info['name'])
                    
                    # Test text generation
                    start_time = time.time()
                    prompt = f"""
As an AI governance expert, analyze this constitutional principle and generate a policy rule:

Principle: "{self.test_scenarios[0]['principle']}"

Generate a structured policy rule that implements this principle in a governance system.
Include specific conditions and actions.
"""
                    
                    response = service.generate_text(prompt, max_tokens=400, temperature=0.3)
                    end_time = time.time()
                    
                    # Evaluate response
                    response_time = end_time - start_time
                    response_quality = self.evaluate_response_quality(response, self.test_scenarios[0]['expected_elements'])
                    
                    self.results[f"alphaevolve_{model_key}"] = {
                        "model": model_info['name'],
                        "response_time": response_time,
                        "response_length": len(response) if response else 0,
                        "quality_score": response_quality,
                        "success": bool(response and len(response) > 100),
                        "response_preview": response[:200] + "..." if response and len(response) > 200 else response
                    }
                    
                    print(f"   ⏱️  Response time: {response_time:.2f}s")
                    print(f"   📏 Response length: {len(response) if response else 0} characters")
                    print(f"   🎯 Quality score: {response_quality:.2f}/1.0")
                    print(f"   ✅ Success: {'Yes' if response and len(response) > 100 else 'No'}")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    self.results[f"alphaevolve_{model_key}"] = {"error": str(e)}
                    
        except ImportError as e:
            print(f"❌ Failed to import AlphaEvolve components: {e}")

    async def test_gs_service_integration(self):
        """Test GS Service integration with Groq models"""
        print("\n🧪 Testing GS Service Integration...")
        
        try:
            # Set environment for Groq testing
            original_provider = os.getenv("LLM_PROVIDER", "mock")
            os.environ["LLM_PROVIDER"] = "groq"
            
            from gs_service.app.core.llm_integration import GroqLLMClient, LLMInterpretationInput
            
            for model_key, model_info in self.groq_models.items():
                print(f"\n📋 Testing GS Service with {model_info['name']}...")
                
                try:
                    # Set specific model
                    os.environ["GROQ_MODEL_NAME"] = model_info['name']
                    
                    client = GroqLLMClient()
                    
                    # Test structured interpretation
                    test_scenario = self.test_scenarios[1]  # Data Privacy Governance
                    input_data = LLMInterpretationInput(
                        principle_id=2,
                        principle_content=test_scenario['principle']
                    )
                    
                    start_time = time.time()
                    result = await client.get_structured_interpretation(input_data)
                    end_time = time.time()
                    
                    # Evaluate structured output
                    response_time = end_time - start_time
                    structure_quality = self.evaluate_structured_output(result)
                    
                    self.results[f"gs_service_{model_key}"] = {
                        "model": model_info['name'],
                        "response_time": response_time,
                        "interpretations_count": len(result.interpretations) if result and result.interpretations else 0,
                        "structure_quality": structure_quality,
                        "success": bool(result and result.interpretations),
                        "raw_response_preview": result.raw_llm_response[:200] + "..." if result and result.raw_llm_response and len(result.raw_llm_response) > 200 else (result.raw_llm_response if result else "No response")
                    }
                    
                    print(f"   ⏱️  Response time: {response_time:.2f}s")
                    print(f"   📊 Interpretations: {len(result.interpretations) if result and result.interpretations else 0}")
                    print(f"   🎯 Structure quality: {structure_quality:.2f}/1.0")
                    print(f"   ✅ Success: {'Yes' if result and result.interpretations else 'No'}")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    self.results[f"gs_service_{model_key}"] = {"error": str(e)}
            
            # Restore original provider
            os.environ["LLM_PROVIDER"] = original_provider
            
        except ImportError as e:
            print(f"❌ Failed to import GS Service components: {e}")

    def evaluate_response_quality(self, response: str, expected_elements: List[str]) -> float:
        """Evaluate response quality based on expected elements"""
        if not response:
            return 0.0
        
        response_lower = response.lower()
        found_elements = 0
        
        for element in expected_elements:
            if element.lower() in response_lower:
                found_elements += 1
        
        # Base score from element coverage
        element_score = found_elements / len(expected_elements) if expected_elements else 0
        
        # Length bonus (reasonable length indicates substantive response)
        length_score = min(len(response) / 500, 1.0)  # Normalize to 500 chars
        
        # Combined score
        return (element_score * 0.7) + (length_score * 0.3)

    def evaluate_structured_output(self, result) -> float:
        """Evaluate structured output quality"""
        if not result:
            return 0.0
        
        score = 0.0
        
        # Check if interpretations exist
        if hasattr(result, 'interpretations') and result.interpretations:
            score += 0.4
            
            # Check interpretation structure
            for interp in result.interpretations:
                if hasattr(interp, 'head') and hasattr(interp, 'body'):
                    score += 0.2
                if hasattr(interp, 'explanation') and interp.explanation:
                    score += 0.2
                if hasattr(interp, 'confidence') and isinstance(interp.confidence, (int, float)):
                    score += 0.2
                break  # Just check first interpretation for structure
        
        return min(score, 1.0)

    def print_comprehensive_report(self):
        """Print comprehensive test report"""
        print("\n" + "="*80)
        print("🎯 ACGS-PGP GROQ INTEGRATION COMPREHENSIVE REPORT")
        print("="*80)
        
        # Model Performance Summary
        print("\n📊 MODEL PERFORMANCE SUMMARY")
        print("-" * 50)
        
        for model_key, model_info in self.groq_models.items():
            print(f"\n🤖 {model_info['name']}")
            print(f"   Description: {model_info['description']}")
            print(f"   Use Case: {model_info['use_case']}")
            
            # AlphaEvolve results
            alphaevolve_key = f"alphaevolve_{model_key}"
            if alphaevolve_key in self.results:
                result = self.results[alphaevolve_key]
                if "error" not in result:
                    print(f"   AlphaEvolve: ✅ {result['response_time']:.2f}s, Quality: {result['quality_score']:.2f}")
                else:
                    print(f"   AlphaEvolve: ❌ {result['error']}")
            
            # GS Service results  
            gs_key = f"gs_service_{model_key}"
            if gs_key in self.results:
                result = self.results[gs_key]
                if "error" not in result:
                    print(f"   GS Service: ✅ {result['response_time']:.2f}s, Structure: {result['structure_quality']:.2f}")
                else:
                    print(f"   GS Service: ❌ {result['error']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 50)
        
        successful_tests = sum(1 for result in self.results.values() if "error" not in result and result.get("success", False))
        total_tests = len(self.results)
        
        if successful_tests == total_tests:
            print("✅ All Groq models are successfully integrated with ACGS-PGP!")
            print("✅ Ready for production testing with diverse model options")
            print("✅ Recommended usage:")
            print("   - Use llama-3.3-70b-versatile for complex constitutional analysis")
            print("   - Use llama-4-maverick for research operations with extended context")
            print("   - Use llama-4-scout for rapid policy validation and testing")
        else:
            print(f"⚠️  {total_tests - successful_tests}/{total_tests} tests failed")
            print("🔧 Troubleshooting steps:")
            print("   1. Verify GROQ_API_KEY is valid and has sufficient quota")
            print("   2. Check network connectivity to api.groq.com")
            print("   3. Ensure all dependencies are installed")
            print("   4. Review error messages above for specific issues")

async def main():
    """Main execution function"""
    print("🚀 Starting ACGS-PGP Groq Integration Tests")
    print("="*60)
    
    tester = ACGSGroqTester()
    
    # Check prerequisites
    if not tester.check_prerequisites():
        print("\n❌ Prerequisites not met. Exiting.")
        return
    
    # Run tests
    await tester.test_alphaevolve_integration()
    await tester.test_gs_service_integration()
    
    # Generate report
    tester.print_comprehensive_report()
    
    print(f"\n🎉 Testing completed!")

if __name__ == "__main__":
    asyncio.run(main())
