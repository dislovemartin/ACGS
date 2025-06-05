#!/usr/bin/env python3
"""
NVIDIA Qwen Integration Test Script
Tests the integration of NVIDIA API with Qwen 3 235B reasoning model

This script demonstrates how to use the NVIDIA API with Qwen models
for constitutional governance tasks in the ACGS-PGP framework.
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Any

# Add the backend path to sys.path for imports
sys.path.append('/home/dislove/ACGS-master/src/backend')

try:
    from gs_service.app.core.nvidia_qwen_client import (
        NVIDIAQwenClient, 
        QwenModelConfig,
        get_nvidia_qwen_client
    )
    NVIDIA_CLIENT_AVAILABLE = True
except ImportError as e:
    NVIDIA_CLIENT_AVAILABLE = False
    print(f"NVIDIA client not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_basic_reasoning():
    """Test basic reasoning capabilities with Qwen model."""
    print("\n🧠 Testing Basic Reasoning Capabilities")
    print("=" * 50)
    
    # Get NVIDIA API key from environment or use the provided one
    api_key = os.getenv("NVIDIA_API_KEY", "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")
    
    if not api_key:
        print("❌ NVIDIA_API_KEY not found in environment")
        return False
    
    try:
        # Initialize client
        client = NVIDIAQwenClient(api_key=api_key)
        
        # Test basic reasoning
        prompt = """
        Analyze the following constitutional governance scenario:
        
        A new AI system is being deployed that makes automated decisions about resource allocation.
        The system must balance efficiency with fairness, and ensure transparency while protecting privacy.
        
        What constitutional principles should guide this system, and how should conflicts be resolved?
        """
        
        print("📝 Sending reasoning request...")
        response = await client.generate_constitutional_analysis(
            prompt=prompt,
            enable_reasoning=True
        )
        
        if response.success:
            print("✅ Reasoning request successful!")
            print(f"⏱️  Response time: {response.response_time_ms:.1f}ms")
            print(f"🤖 Model used: {response.model_used}")
            
            if response.reasoning_content:
                print("\n🧠 Reasoning Process:")
                print("-" * 30)
                print(response.reasoning_content[:500] + "..." if len(response.reasoning_content) > 500 else response.reasoning_content)
            
            print("\n💡 Final Response:")
            print("-" * 30)
            print(response.content[:500] + "..." if len(response.content) > 500 else response.content)
            
            if response.token_usage:
                print(f"\n📊 Token Usage: {response.token_usage}")
            
            return True
        else:
            print(f"❌ Reasoning request failed: {response.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Error in basic reasoning test: {e}")
        return False

async def test_constitutional_compliance():
    """Test constitutional compliance analysis."""
    print("\n🏛️ Testing Constitutional Compliance Analysis")
    print("=" * 50)
    
    api_key = os.getenv("NVIDIA_API_KEY", "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")
    
    try:
        client = NVIDIAQwenClient(api_key=api_key)
        
        # Test policy compliance analysis
        policy_text = """
        All user data must be encrypted at rest and in transit.
        Access to personal information requires explicit user consent.
        Automated decisions affecting users must be explainable and auditable.
        """
        
        constitutional_principles = [
            "Privacy and data protection",
            "Transparency and accountability", 
            "Fairness and non-discrimination",
            "User autonomy and consent"
        ]
        
        print("📝 Analyzing constitutional compliance...")
        response = await client.analyze_constitutional_compliance(
            policy_text=policy_text,
            constitutional_principles=constitutional_principles
        )
        
        if response.success:
            print("✅ Compliance analysis successful!")
            print(f"⏱️  Response time: {response.response_time_ms:.1f}ms")
            
            print("\n📋 Compliance Analysis:")
            print("-" * 30)
            print(response.content[:800] + "..." if len(response.content) > 800 else response.content)
            
            return True
        else:
            print(f"❌ Compliance analysis failed: {response.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Error in compliance analysis test: {e}")
        return False

async def test_policy_synthesis():
    """Test policy synthesis capabilities."""
    print("\n📜 Testing Policy Synthesis")
    print("=" * 50)
    
    api_key = os.getenv("NVIDIA_API_KEY", "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")
    
    try:
        client = NVIDIAQwenClient(api_key=api_key)
        
        constitutional_context = """
        Core Constitutional Principles:
        1. Algorithmic fairness and non-discrimination
        2. Transparency and explainability
        3. Privacy and data protection
        4. Human oversight and accountability
        """
        
        synthesis_requirements = """
        Generate policies for an AI-powered hiring system that:
        - Evaluates candidates fairly across all demographics
        - Provides clear explanations for decisions
        - Protects candidate privacy
        - Allows for human review and appeal
        """
        
        print("📝 Synthesizing constitutional policies...")
        response = await client.generate_policy_synthesis(
            constitutional_context=constitutional_context,
            synthesis_requirements=synthesis_requirements
        )
        
        if response.success:
            print("✅ Policy synthesis successful!")
            print(f"⏱️  Response time: {response.response_time_ms:.1f}ms")
            
            if response.reasoning_content:
                print("\n🧠 Synthesis Reasoning:")
                print("-" * 30)
                print(response.reasoning_content[:400] + "..." if len(response.reasoning_content) > 400 else response.reasoning_content)
            
            print("\n📜 Synthesized Policies:")
            print("-" * 30)
            print(response.content[:600] + "..." if len(response.content) > 600 else response.content)
            
            return True
        else:
            print(f"❌ Policy synthesis failed: {response.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Error in policy synthesis test: {e}")
        return False

async def test_model_capabilities():
    """Test model capabilities reporting."""
    print("\n🔧 Testing Model Capabilities")
    print("=" * 50)
    
    api_key = os.getenv("NVIDIA_API_KEY", "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")
    
    try:
        client = NVIDIAQwenClient(api_key=api_key)
        capabilities = client.get_model_capabilities()
        
        print("✅ Model capabilities retrieved!")
        print("\n📊 Capabilities:")
        for key, value in capabilities.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting model capabilities: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive NVIDIA Qwen integration tests."""
    print("🚀 NVIDIA Qwen Integration Test Suite")
    print("=" * 60)
    
    if not NVIDIA_CLIENT_AVAILABLE:
        print("❌ NVIDIA client not available. Please check dependencies.")
        return
    
    # Test results tracking
    test_results = []
    
    # Run individual tests
    tests = [
        ("Model Capabilities", test_model_capabilities),
        ("Basic Reasoning", test_basic_reasoning),
        ("Constitutional Compliance", test_constitutional_compliance),
        ("Policy Synthesis", test_policy_synthesis)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name} test...")
            result = await test_func()
            test_results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! NVIDIA Qwen integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    print("\n💡 Integration Notes:")
    print("   - Qwen 3 235B model supports advanced reasoning capabilities")
    print("   - Reasoning content provides step-by-step analysis")
    print("   - Model is well-suited for constitutional governance tasks")
    print("   - Integration supports policy synthesis, compliance analysis, and conflict resolution")

def main():
    """Main test execution."""
    try:
        asyncio.run(run_comprehensive_test())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution error: {e}")

if __name__ == "__main__":
    main()
