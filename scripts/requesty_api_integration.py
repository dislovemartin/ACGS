#!/usr/bin/env python3
"""
RequestyAPI Integration for Darwin Gödel Machine

This module provides a simplified interface for the DGM to interact with the Requesty API.
"""

import os
from typing import Optional
from requesty_example import RequestyAPIClient

class RequestyAPI:
    """
    Simplified RequestyAPI wrapper for DGM integration.
    
    This class provides the interface expected by the DGM system.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Requesty API wrapper."""
        self.client = RequestyAPIClient(api_key)
    
    def send_message(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        Send a message to the API and return the response content.
        
        Args:
            message: The message to send
            system_prompt: Optional system prompt
            
        Returns:
            The response content as a string
            
        Raises:
            Exception: If the API call fails
        """
        # Use a system prompt optimized for software engineering tasks
        if system_prompt is None:
            system_prompt = """You are an expert software engineer and debugging specialist. 
            You analyze code problems systematically and provide precise, working solutions. 
            Focus on:
            - Identifying the root cause of issues
            - Providing working code fixes
            - Following best practices
            - Writing clear, maintainable code
            
            When editing files, be specific about the exact changes needed."""
        
        result = self.client.chat_completion(
            message=message,
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.3  # Lower temperature for more deterministic code generation
        )
        
        if result["success"]:
            return result["content"]
        else:
            raise Exception(f"API call failed: {result.get('error', 'Unknown error')}")