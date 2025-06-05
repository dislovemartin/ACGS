#!/usr/bin/env python3
"""
Ollama Constitutional Prompting Test for ACGS-PGP

This script tests constitutional prompting workflows with Ollama integration.
"""

import asyncio
import sys
import os
import time
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from gs_service.app.core.ollama_client import OllamaLLMClient
from gs_service.app.schemas import LLMInterpretationInput


async def test_constitutional_prompting():
    """Test constitutional prompting with Ollama."""
    print("🧪 Testing Constitutional Prompting with Ollama")
    
    try:
        client = OllamaLLMClient()
        
        # Test 1: Basic constitutional prompt
        print("1. Testing basic constitutional interpretation...")
        
        query = LLMInterpretationInput(
            principle_id=1,
            principle_content="AI systems must ensure fairness and non-discrimination in all decisions",
            target_context="healthcare",
            datalog_predicate_schema={
                "user_has_role": "user_has_role(User, Role)",
                "action_allowed": "action_allowed(User, Action, Resource)",
                "sensitive_data": "sensitive_data(Data)"
            }
        )
        
        start_time = time.time()
        result = await client.get_structured_interpretation(query)
        response_time = time.time() - start_time
        
        print(f"   Response time: {response_time:.2f}s")
        print(f"   Interpretations generated: {len(result.interpretations)}")
        print(f"   Raw response length: {len(result.raw_llm_response)}")
        
        if result.interpretations:
            interpretation = result.interpretations[0]
            print(f"   Sample rule head: {interpretation.head.predicate_name}")
            print(f"   Sample rule body: {len(interpretation.body)} conditions")
            print(f"   Confidence: {interpretation.confidence}")
        
        # Test 2: Complex constitutional scenario
        print("\n2. Testing complex constitutional scenario...")
        
        complex_query = LLMInterpretationInput(
            principle_id=2,
            principle_content="Data privacy must be protected with user consent and minimal data collection",
            target_context="financial_services",
            datalog_predicate_schema={
                "user_consent": "user_consent(User, DataType, Purpose)",
                "data_collection": "data_collection(System, User, DataType)",
                "privacy_violation": "privacy_violation(Action, User, DataType)"
            }
        )
        
        start_time = time.time()
        complex_result = await client.get_structured_interpretation(complex_query)
        complex_response_time = time.time() - start_time
        
        print(f"   Response time: {complex_response_time:.2f}s")
        print(f"   Interpretations generated: {len(complex_result.interpretations)}")
        
        # Test 3: Performance comparison
        print("\n3. Testing performance with multiple requests...")
        
        response_times = []
        for i in range(3):
            test_query = LLMInterpretationInput(
                principle_id=i+3,
                principle_content=f"Test principle {i+1}: Ensure system reliability and security",
                target_context="general",
                datalog_predicate_schema={}
            )
            
            start_time = time.time()
            await client.generate_text(
                prompt=f"Explain constitutional principle {i+1} briefly",
                temperature=0.2,
                max_tokens=100
            )
            response_time = time.time() - start_time
            response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times)
        print(f"   Average response time: {avg_response_time:.2f}s")
        print(f"   Response time range: {min(response_times):.2f}s - {max(response_times):.2f}s")
        
        await client.close()
        
        # Performance evaluation
        performance_score = 100
        if avg_response_time > 10:
            performance_score -= 30
        elif avg_response_time > 5:
            performance_score -= 15
        
        if len(result.interpretations) == 0:
            performance_score -= 40
        
        print(f"\n   Performance Score: {performance_score}/100")
        
        success = (
            len(result.interpretations) > 0 and
            len(complex_result.interpretations) > 0 and
            avg_response_time < 15  # 15 second threshold
        )
        
        print(f"✅ Constitutional prompting test: {'PASSED' if success else 'FAILED'}")
        return success
        
    except Exception as e:
        print(f"❌ Constitutional prompting test failed: {e}")
        return False


async def test_policy_synthesis():
    """Test policy synthesis capabilities."""
    print("\n🧪 Testing Policy Synthesis with Ollama")
    
    try:
        client = OllamaLLMClient()
        
        # Test policy synthesis prompt
        policy_prompt = """
        Generate a data privacy policy rule based on the following constitutional principle:
        
        Principle: "Personal data must be processed lawfully, fairly, and transparently"
        
        Context: Healthcare data processing system
        
        Please provide a structured policy rule that implements this principle.
        """
        
        start_time = time.time()
        policy_response = await client.generate_text(
            prompt=policy_prompt,
            temperature=0.1,  # Low temperature for consistency
            max_tokens=300
        )
        response_time = time.time() - start_time
        
        print(f"   Response time: {response_time:.2f}s")
        print(f"   Policy length: {len(policy_response)} characters")
        print(f"   Policy preview: {policy_response[:200]}...")
        
        # Evaluate policy quality
        quality_indicators = [
            "lawfully" in policy_response.lower(),
            "fairly" in policy_response.lower(),
            "transparently" in policy_response.lower(),
            "healthcare" in policy_response.lower(),
            "data" in policy_response.lower()
        ]
        
        quality_score = sum(quality_indicators) / len(quality_indicators) * 100
        print(f"   Quality score: {quality_score:.1f}%")
        
        await client.close()
        
        success = quality_score >= 60 and response_time < 20
        print(f"✅ Policy synthesis test: {'PASSED' if success else 'FAILED'}")
        return success
        
    except Exception as e:
        print(f"❌ Policy synthesis test failed: {e}")
        return False


async def test_performance_comparison():
    """Test performance comparison with different parameters."""
    print("\n🧪 Testing Performance with Different Parameters")
    
    try:
        client = OllamaLLMClient()
        
        test_configs = [
            {"temperature": 0.1, "max_tokens": 100, "name": "Conservative"},
            {"temperature": 0.5, "max_tokens": 200, "name": "Balanced"},
            {"temperature": 0.8, "max_tokens": 300, "name": "Creative"}
        ]
        
        results = []
        
        for config in test_configs:
            print(f"   Testing {config['name']} configuration...")
            
            start_time = time.time()
            response = await client.generate_text(
                prompt="Explain the importance of constitutional AI governance",
                temperature=config["temperature"],
                max_tokens=config["max_tokens"]
            )
            response_time = time.time() - start_time
            
            results.append({
                "config": config["name"],
                "response_time": response_time,
                "response_length": len(response),
                "tokens_per_second": len(response.split()) / response_time if response_time > 0 else 0
            })
            
            print(f"     Response time: {response_time:.2f}s")
            print(f"     Response length: {len(response)} chars")
            print(f"     Tokens/second: {len(response.split()) / response_time if response_time > 0 else 0:.1f}")
        
        await client.close()
        
        # Find best performing configuration
        best_config = min(results, key=lambda x: x["response_time"])
        print(f"\n   Best performing config: {best_config['config']}")
        print(f"   Best response time: {best_config['response_time']:.2f}s")
        
        success = all(r["response_time"] < 30 for r in results)
        print(f"✅ Performance comparison test: {'PASSED' if success else 'FAILED'}")
        return success
        
    except Exception as e:
        print(f"❌ Performance comparison test failed: {e}")
        return False


async def main():
    """Main test execution."""
    print("🚀 ACGS-PGP Ollama Constitutional Prompting Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(await test_constitutional_prompting())
    results.append(await test_policy_synthesis())
    results.append(await test_performance_comparison())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Constitutional Prompting Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All constitutional prompting tests passed!")
        print("✅ Ollama is ready for constitutional AI governance workflows")
        exit_code = 0
    elif passed >= total * 0.7:
        print("⚠️  Most tests passed with some performance issues")
        print("✅ Ollama integration is functional but may need optimization")
        exit_code = 0
    else:
        print("❌ Multiple tests failed")
        print("⚠️  Ollama integration needs attention")
        exit_code = 1
    
    # Recommendations
    print("\n💡 Recommendations:")
    if passed == total:
        print("1. Ollama constitutional prompting is working excellently")
        print("2. Consider integrating with production ACGS-PGP workflows")
        print("3. Monitor performance under production load")
        print("4. Implement constitutional fidelity monitoring")
    elif passed >= total * 0.7:
        print("1. Basic functionality is working")
        print("2. Consider optimizing model parameters for better performance")
        print("3. Monitor response times in production")
        print("4. Test with larger constitutional principle sets")
    else:
        print("1. Check Ollama server configuration and model availability")
        print("2. Verify network connectivity to Ollama server")
        print("3. Consider using a different model or adjusting parameters")
        print("4. Review error logs for specific issues")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
