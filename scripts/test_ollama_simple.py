#!/usr/bin/env python3
"""
Simple Ollama Integration Test for ACGS-PGP

This script performs basic validation of Ollama integration.
"""

import asyncio
import sys
import os
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from gs_service.app.core.ollama_client import OllamaLLMClient


async def test_basic_ollama():
    """Test basic Ollama functionality."""
    print("🧪 Testing Ollama Basic Functionality")
    
    try:
        # Test 1: Health Check
        print("1. Testing health check...")
        client = OllamaLLMClient()
        
        is_healthy = await client.health_check()
        print(f"   Health check: {'✅ PASSED' if is_healthy else '❌ FAILED'}")
        
        if not is_healthy:
            print("   Ollama server is not available. Please ensure it's running.")
            return False
        
        # Test 2: Get available models
        print("2. Getting available models...")
        models = await client.get_available_models()
        print(f"   Available models: {len(models)}")
        for model in models:
            print(f"     - {model}")
        
        # Test 3: Basic text generation
        print("3. Testing text generation...")
        response = await client.generate_text(
            prompt="What is AI governance? Please provide a brief answer.",
            temperature=0.3,
            max_tokens=100
        )
        
        print(f"   Generated response ({len(response)} chars):")
        print(f"   {response[:200]}...")
        
        await client.close()
        
        print("✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_multi_model_manager():
    """Test MultiModelManager integration."""
    print("\n🧪 Testing MultiModelManager Integration")
    
    try:
        from gs_service.app.workflows.multi_model_manager import MultiModelManager
        from shared.langgraph_config import ModelRole
        
        print("1. Initializing MultiModelManager...")
        manager = MultiModelManager()
        
        print("2. Getting performance metrics...")
        metrics = manager.get_performance_metrics()
        print(f"   Total models configured: {len(metrics) - 1 if 'overall' in metrics else len(metrics)}")
        
        # Check if Ollama models are configured
        ollama_models = [
            model for model in metrics.keys() 
            if model.startswith("hf.co/") or "deepseek" in model.lower()
        ]
        print(f"   Ollama models configured: {len(ollama_models)}")
        
        print("✅ MultiModelManager integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ MultiModelManager test failed: {e}")
        return False


async def test_taskmaster_config():
    """Test TaskMaster configuration."""
    print("\n🧪 Testing TaskMaster Configuration")
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', '.taskmaster', 'config.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check Ollama configuration
            global_config = config.get("global", {})
            ollama_enabled = global_config.get("enableOllamaModels", False)
            ollama_base_url = global_config.get("ollamaBaseURL", "")
            ollama_model = global_config.get("ollamaDefaultModel", "")
            
            print(f"   Ollama enabled: {ollama_enabled}")
            print(f"   Ollama base URL: {ollama_base_url}")
            print(f"   Default model: {ollama_model}")
            
            # Check fallback model
            fallback_model = config.get("models", {}).get("fallback", {}).get("modelId", "")
            ollama_fallback = "deepseek" in fallback_model.lower() or "hf.co/" in fallback_model
            
            print(f"   Ollama fallback configured: {ollama_fallback}")
            print(f"   Fallback model: {fallback_model}")
            
            success = ollama_enabled and ollama_fallback
            print(f"✅ TaskMaster configuration: {'PASSED' if success else 'NEEDS ATTENTION'}")
            return success
        else:
            print("❌ TaskMaster config file not found")
            return False
            
    except Exception as e:
        print(f"❌ TaskMaster config test failed: {e}")
        return False


async def main():
    """Main test execution."""
    print("🚀 ACGS-PGP Ollama Integration Test")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(await test_basic_ollama())
    results.append(await test_multi_model_manager())
    results.append(await test_taskmaster_config())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Ollama integration is working correctly.")
        exit_code = 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        exit_code = 1
    
    # Recommendations
    print("\n💡 Next Steps:")
    if passed == total:
        print("1. Ollama integration is ready for use in ACGS-PGP")
        print("2. You can now use DeepSeek-R1 as a fallback model")
        print("3. Consider testing constitutional prompting workflows")
        print("4. Monitor performance in production environment")
    else:
        print("1. Ensure Ollama server is running: ollama serve")
        print("2. Verify DeepSeek model is available: ollama list")
        print("3. Check TaskMaster configuration for Ollama settings")
        print("4. Review environment variables for OLLAMA_BASE_URL")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
