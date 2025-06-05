#!/usr/bin/env python3
"""
Debug Ollama Integration Issues
"""

import asyncio
import aiohttp
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))


async def test_direct_ollama():
    """Test direct Ollama API call."""
    print("🔍 Testing Direct Ollama API Call")
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q8_K_XL",
                "prompt": "What is AI governance?",
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 100
                }
            }
            
            print(f"Sending request to: http://127.0.0.1:11434/api/generate")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            async with session.post(
                "http://127.0.0.1:11434/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"Response status: {response.status}")
                print(f"Response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"Response data keys: {list(data.keys())}")
                    print(f"Response: {data.get('response', 'No response field')[:200]}...")
                    return True
                else:
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"Direct API test failed: {e}")
        return False


async def test_ollama_client():
    """Test our Ollama client implementation."""
    print("\n🔍 Testing Ollama Client Implementation")
    
    try:
        from gs_service.app.core.ollama_client import OllamaLLMClient
        
        client = OllamaLLMClient()
        
        # Test health check first
        print("1. Testing health check...")
        is_healthy = await client.health_check()
        print(f"   Health check result: {is_healthy}")
        
        if not is_healthy:
            print("   Health check failed, skipping generation test")
            await client.close()
            return False
        
        # Test simple generation
        print("2. Testing simple generation...")
        try:
            response = await client.generate_text(
                prompt="Hello, how are you?",
                temperature=0.3,
                max_tokens=50
            )
            print(f"   Generation successful: {len(response)} characters")
            print(f"   Response preview: {response[:100]}...")
            await client.close()
            return True
            
        except Exception as gen_error:
            print(f"   Generation failed: {gen_error}")
            await client.close()
            return False
            
    except Exception as e:
        print(f"Client test failed: {e}")
        return False


async def test_model_availability():
    """Test model availability."""
    print("\n🔍 Testing Model Availability")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:11434/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    print(f"Available models: {len(models)}")
                    
                    target_model = "hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q8_K_XL"
                    model_names = [model["name"] for model in models]
                    
                    print(f"Model names:")
                    for name in model_names:
                        print(f"  - {name}")
                    
                    if target_model in model_names:
                        print(f"✅ Target model '{target_model}' is available")
                        return True
                    else:
                        print(f"❌ Target model '{target_model}' not found")
                        return False
                else:
                    print(f"Failed to get models: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"Model availability test failed: {e}")
        return False


async def main():
    """Main debug execution."""
    print("🚀 Ollama Integration Debug")
    print("=" * 40)
    
    results = []
    
    # Run debug tests
    results.append(await test_model_availability())
    results.append(await test_direct_ollama())
    results.append(await test_ollama_client())
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Debug Summary")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All debug tests passed - Ollama integration should work")
    else:
        print("❌ Some debug tests failed - check the issues above")
        
        if not results[0]:
            print("💡 Model not available - run: ollama pull hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q8_K_XL")
        if not results[1]:
            print("💡 Direct API failed - check Ollama server status")
        if not results[2]:
            print("💡 Client implementation issue - check error handling")


if __name__ == "__main__":
    asyncio.run(main())
