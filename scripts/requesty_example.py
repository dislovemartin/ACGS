#!/usr/bin/env python3
"""
Requesty API Integration Example

This script demonstrates how to integrate with the Requesty API router
using the Anthropic Claude Sonnet model through the OpenAI-compatible interface.

Required packages:
- pip install openai python-dotenv

Usage:
    python requesty_example.py

Setup:
1. Ensure the .env file contains your ROUTER_API_KEY
2. Install required dependencies: pip install openai python-dotenv
3. Run the script to test the integration

Next steps for testing:
- Modify the test_message variable to test different prompts
- Add additional error handling for specific use cases
- Integrate this pattern into your main application
"""

import os
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

class RequestyAPIClient:
    """
    A client for interacting with the Requesty API router using Anthropic Claude Sonnet.
    
    This class provides a simple interface for making API calls through the Requesty
    router service, which provides access to various AI models including Claude.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Requesty API client.
        
        Args:
            api_key: Optional API key. If not provided, will try to load from ROUTER_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('ROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("API key is required. Set ROUTER_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize OpenAI client with Requesty router configuration
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://router.requesty.ai/v1"
        )
        
        # Model configuration
        self.model = "anthropic/claude-sonnet-4-20250514"
        
    def chat_completion(
        self, 
        message: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to Claude via Requesty router.
        
        Args:
            message: The user message to send
            system_prompt: Optional system prompt to set context
            max_tokens: Maximum number of tokens in the response
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Dictionary containing the response data
            
        Raises:
            Exception: If the API call fails
        """
        try:
            # Prepare messages
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": message
            })
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract and return response data
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

def main():
    """
    Main function to demonstrate the Requesty API integration.
    """
    print("🚀 Requesty API Integration Test")
    print("=" * 50)
    
    try:
        # Initialize the client
        print("📡 Initializing Requesty API client...")
        client = RequestyAPIClient()
        print(f"✅ Client initialized with model: {client.model}")
        
        # Test message
        test_message = """
        Explain the concept of quantum computing in simple terms, 
        including its potential advantages over classical computing.
        """
        
        system_prompt = """
        You are a helpful AI assistant that explains complex topics clearly and concisely.
        Focus on making technical concepts accessible to a general audience.
        """
        
        print("\n💬 Sending test message...")
        print(f"Message: {test_message.strip()}")
        
        # Make the API call
        result = client.chat_completion(
            message=test_message,
            system_prompt=system_prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        # Display results
        if result["success"]:
            print("\n✅ API call successful!")
            print(f"Model: {result['model']}")
            print(f"Tokens used: {result['usage']['total_tokens']} "
                  f"(prompt: {result['usage']['prompt_tokens']}, "
                  f"completion: {result['usage']['completion_tokens']})")
            print("\n📝 Response:")
            print("-" * 40)
            print(result["content"])
            print("-" * 40)
        else:
            print(f"\n❌ API call failed!")
            print(f"Error Type: {result['error_type']}")
            print(f"Error Message: {result['error']}")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n🔧 Setup checklist:")
        print("1. Ensure .env file exists with ROUTER_API_KEY")
        print("2. Install dependencies: pip install openai python-dotenv")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    print("\n🎉 Integration test completed!")
    return 0

if __name__ == "__main__":
    """
    Run the integration test when script is executed directly.
    
    Before running:
    1. Install dependencies:
       pip install openai python-dotenv
       
    2. Ensure .env file contains:
       ROUTER_API_KEY=your_api_key_here
       
    3. Run the script:
       python requesty_example.py
    """
    sys.exit(main())