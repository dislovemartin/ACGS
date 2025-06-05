"""
NVIDIA API Qwen Client for ACGS-PGP
Enhanced integration for Qwen 3 235B model with reasoning capabilities

This module provides specialized support for NVIDIA's API integration with Qwen models,
particularly the Qwen 3 235B model that supports reasoning capabilities through the
chat_template_kwargs parameter.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime, timezone
import json

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

logger = logging.getLogger(__name__)

@dataclass
class QwenReasoningResponse:
    """Response from Qwen model with reasoning capabilities."""
    content: str
    reasoning_content: Optional[str] = None
    model_used: str = ""
    response_time_ms: float = 0.0
    token_usage: Optional[Dict[str, int]] = None
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class QwenModelConfig:
    """Configuration for Qwen model interactions."""
    model_name: str = "qwen/qwen3-235b-a22b"
    temperature: float = 0.2
    top_p: float = 0.7
    max_tokens: int = 8192
    enable_reasoning: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3

class NVIDIAQwenClient:
    """
    Specialized client for NVIDIA API Qwen models with reasoning capabilities.
    
    Provides enhanced integration for constitutional governance tasks requiring
    deep reasoning and analysis capabilities.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://integrate.api.nvidia.com/v1"):
        """
        Initialize NVIDIA Qwen client.
        
        Args:
            api_key: NVIDIA API key
            base_url: NVIDIA API base URL
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library required for NVIDIA API integration")
        
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.default_config = QwenModelConfig()
        
        logger.info(f"Initialized NVIDIA Qwen client with base URL: {base_url}")
    
    async def generate_constitutional_analysis(
        self,
        prompt: str,
        config: Optional[QwenModelConfig] = None,
        enable_reasoning: bool = True
    ) -> QwenReasoningResponse:
        """
        Generate constitutional analysis with reasoning capabilities.
        
        Args:
            prompt: Input prompt for constitutional analysis
            config: Optional model configuration
            enable_reasoning: Whether to enable reasoning mode
            
        Returns:
            QwenReasoningResponse with analysis and reasoning
        """
        if config is None:
            config = self.default_config
        
        start_time = time.time()
        
        try:
            # Prepare request parameters
            messages = [{"role": "user", "content": prompt}]
            
            # Configure extra body for reasoning if enabled
            extra_body = {}
            if enable_reasoning and "qwen3-235b" in config.model_name.lower():
                extra_body = {"chat_template_kwargs": {"thinking": True}}
            
            # Execute API call in thread pool (OpenAI client is synchronous)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=config.model_name,
                    messages=messages,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    max_tokens=config.max_tokens,
                    extra_body=extra_body,
                    stream=False
                )
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Extract content and reasoning
            content = response.choices[0].message.content
            reasoning_content = None
            
            # Check for reasoning content in response
            if hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning_content = response.choices[0].message.reasoning_content
            elif hasattr(response.choices[0], 'delta') and hasattr(response.choices[0].delta, 'reasoning_content'):
                reasoning_content = response.choices[0].delta.reasoning_content
            
            # Extract token usage if available
            token_usage = None
            if hasattr(response, 'usage'):
                token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return QwenReasoningResponse(
                content=content,
                reasoning_content=reasoning_content,
                model_used=config.model_name,
                response_time_ms=response_time,
                token_usage=token_usage,
                success=True
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Error in NVIDIA Qwen API call: {e}")
            
            return QwenReasoningResponse(
                content="",
                model_used=config.model_name,
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
    
    async def generate_policy_synthesis(
        self,
        constitutional_context: str,
        synthesis_requirements: str,
        config: Optional[QwenModelConfig] = None
    ) -> QwenReasoningResponse:
        """
        Generate policy synthesis with constitutional reasoning.
        
        Args:
            constitutional_context: Constitutional principles and context
            synthesis_requirements: Specific synthesis requirements
            config: Optional model configuration
            
        Returns:
            QwenReasoningResponse with policy synthesis and reasoning
        """
        prompt = f"""
CONSTITUTIONAL GOVERNANCE POLICY SYNTHESIS

Constitutional Context:
{constitutional_context}

Synthesis Requirements:
{synthesis_requirements}

Please provide a comprehensive policy synthesis that:
1. Analyzes the constitutional principles and their implications
2. Develops specific policy recommendations aligned with constitutional requirements
3. Considers potential conflicts and resolution strategies
4. Provides implementation guidance with constitutional safeguards

Use your reasoning capabilities to work through the constitutional analysis step by step,
considering multiple perspectives and potential edge cases.
"""
        
        return await self.generate_constitutional_analysis(
            prompt=prompt,
            config=config,
            enable_reasoning=True
        )
    
    async def analyze_constitutional_compliance(
        self,
        policy_text: str,
        constitutional_principles: List[str],
        config: Optional[QwenModelConfig] = None
    ) -> QwenReasoningResponse:
        """
        Analyze policy compliance with constitutional principles.
        
        Args:
            policy_text: Policy text to analyze
            constitutional_principles: List of constitutional principles
            config: Optional model configuration
            
        Returns:
            QwenReasoningResponse with compliance analysis and reasoning
        """
        principles_text = "\n".join([f"- {principle}" for principle in constitutional_principles])
        
        prompt = f"""
CONSTITUTIONAL COMPLIANCE ANALYSIS

Policy to Analyze:
{policy_text}

Constitutional Principles:
{principles_text}

Please provide a detailed constitutional compliance analysis that:
1. Evaluates alignment with each constitutional principle
2. Identifies potential conflicts or violations
3. Assesses overall constitutional fidelity score (0.0-1.0)
4. Recommends specific improvements if needed
5. Considers long-term constitutional implications

Use your reasoning capabilities to thoroughly examine each principle and provide
a comprehensive assessment with clear justification for your conclusions.

Please format your response as JSON with the following structure:
{{
    "overall_fidelity_score": 0.85,
    "principle_analysis": [
        {{
            "principle": "principle text",
            "compliance_score": 0.9,
            "analysis": "detailed analysis",
            "recommendations": ["recommendation 1", "recommendation 2"]
        }}
    ],
    "identified_conflicts": ["conflict 1", "conflict 2"],
    "improvement_recommendations": ["improvement 1", "improvement 2"],
    "constitutional_implications": "long-term implications analysis"
}}
"""
        
        return await self.generate_constitutional_analysis(
            prompt=prompt,
            config=config,
            enable_reasoning=True
        )
    
    async def generate_conflict_resolution(
        self,
        conflicting_policies: List[str],
        constitutional_framework: str,
        config: Optional[QwenModelConfig] = None
    ) -> QwenReasoningResponse:
        """
        Generate conflict resolution strategies for conflicting policies.
        
        Args:
            conflicting_policies: List of conflicting policy texts
            constitutional_framework: Constitutional framework for resolution
            config: Optional model configuration
            
        Returns:
            QwenReasoningResponse with conflict resolution and reasoning
        """
        policies_text = "\n\n".join([f"Policy {i+1}:\n{policy}" for i, policy in enumerate(conflicting_policies)])
        
        prompt = f"""
CONSTITUTIONAL CONFLICT RESOLUTION

Conflicting Policies:
{policies_text}

Constitutional Framework:
{constitutional_framework}

Please provide a comprehensive conflict resolution strategy that:
1. Identifies the specific nature and scope of conflicts
2. Analyzes constitutional precedence and hierarchy
3. Develops resolution strategies that maintain constitutional integrity
4. Proposes harmonized policy language that resolves conflicts
5. Ensures long-term constitutional consistency

Use your reasoning capabilities to work through the conflict analysis systematically,
considering multiple resolution approaches and their constitutional implications.

Please provide both the reasoning process and the final resolution recommendations.
"""
        
        return await self.generate_constitutional_analysis(
            prompt=prompt,
            config=config,
            enable_reasoning=True
        )
    
    def get_model_capabilities(self) -> Dict[str, Any]:
        """
        Get information about model capabilities.
        
        Returns:
            Dictionary with model capability information
        """
        return {
            "model_name": self.default_config.model_name,
            "reasoning_support": True,
            "max_tokens": self.default_config.max_tokens,
            "constitutional_analysis": True,
            "policy_synthesis": True,
            "conflict_resolution": True,
            "compliance_analysis": True,
            "api_provider": "NVIDIA",
            "base_url": self.base_url
        }

# Global NVIDIA Qwen client instance
_nvidia_qwen_client: Optional[NVIDIAQwenClient] = None

def get_nvidia_qwen_client(api_key: Optional[str] = None) -> Optional[NVIDIAQwenClient]:
    """
    Get the global NVIDIA Qwen client instance.
    
    Args:
        api_key: Optional API key override
        
    Returns:
        NVIDIAQwenClient instance or None if not available
    """
    global _nvidia_qwen_client
    
    if api_key is None:
        import os
        api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        logger.warning("NVIDIA_API_KEY not available. NVIDIA Qwen client disabled.")
        return None
    
    if _nvidia_qwen_client is None:
        try:
            _nvidia_qwen_client = NVIDIAQwenClient(api_key=api_key)
            logger.info("Initialized global NVIDIA Qwen client")
        except Exception as e:
            logger.error(f"Failed to initialize NVIDIA Qwen client: {e}")
            return None
    
    return _nvidia_qwen_client
