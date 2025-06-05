"""
Ollama LLM Client for ACGS-PGP Local Model Integration

This module provides integration with Ollama local model deployment,
supporting the DeepSeek-R1-0528-Qwen3-8B model and other local models
for constitutional prompting and policy synthesis workflows.

Implements async/await patterns and follows ACGS-PGP reliability standards
with circuit breaker patterns and fallback mechanisms.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Type
from datetime import datetime, timezone
import aiohttp
import json
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential

from ..schemas import LLMInterpretationInput, LLMStructuredOutput, LLMSuggestedRule, LLMSuggestedAtom

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama client."""
    base_url: str = "http://127.0.0.1:11434"
    api_key: Optional[str] = None
    default_model: str = "hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q8_K_XL"
    timeout_seconds: int = 60
    max_retries: int = 3
    temperature: float = 0.3
    max_tokens: int = 4096


class OllamaLLMClient:
    """
    Ollama LLM client for local model deployment.
    
    Provides integration with Ollama server for constitutional prompting
    and policy synthesis using local models like DeepSeek-R1.
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize Ollama client.
        
        Args:
            config: Ollama configuration. If None, loads from environment.
        """
        self.config = config or self._load_config_from_env()
        self.session: Optional[aiohttp.ClientSession] = None
        self._available_models: Optional[List[str]] = None
        
        logger.info(f"Initialized OllamaLLMClient with base URL: {self.config.base_url}")
    
    @classmethod
    def _load_config_from_env(cls) -> OllamaConfig:
        """Load Ollama configuration from environment variables."""
        return OllamaConfig(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            api_key=os.getenv("OLLAMA_API_KEY"),
            default_model=os.getenv("OLLAMA_DEFAULT_MODEL", "hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q8_K_XL"),
            timeout_seconds=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")),
            max_retries=int(os.getenv("OLLAMA_MAX_RETRIES", "3")),
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "4096"))
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is available."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            headers = {}
            
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """
        Check if Ollama server is available and responsive.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            await self._ensure_session()
            
            async with self.session.get(f"{self.config.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    self._available_models = [model["name"] for model in data.get("models", [])]
                    logger.info(f"Ollama server healthy. Available models: {len(self._available_models)}")
                    return True
                else:
                    logger.warning(f"Ollama server returned status {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """
        Get list of available models from Ollama server.
        
        Returns:
            List of available model names
        """
        if self._available_models is None:
            await self.health_check()
        
        return self._available_models or []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama model.
        
        Args:
            prompt: Input prompt for text generation
            model: Model name to use (defaults to configured default)
            temperature: Sampling temperature (defaults to configured value)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If generation fails after retries
        """
        await self._ensure_session()
        
        model_name = model or self.config.default_model
        temp = temperature if temperature is not None else self.config.temperature
        max_tok = max_tokens or self.config.max_tokens
        
        # Check if model is available
        available_models = await self.get_available_models()
        if model_name not in available_models:
            raise ValueError(f"Model {model_name} not available. Available models: {available_models}")
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": max_tok,
                **kwargs
            }
        }
        
        logger.debug(f"Sending request to Ollama: model={model_name}, prompt_length={len(prompt)}")
        
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/generate",
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
                
                data = await response.json()
                generated_text = data.get("response", "")
                
                logger.info(f"Ollama generated {len(generated_text)} characters")
                return generated_text
                
        except asyncio.TimeoutError:
            logger.error(f"Ollama generation timed out for model {model_name}")
            raise Exception(f"Ollama generation timed out after {self.config.timeout_seconds}s")
        except aiohttp.ClientError as e:
            logger.error(f"Ollama client error for model {model_name}: {e}")
            raise Exception(f"Ollama client error: {e}")
        except Exception as e:
            logger.error(f"Ollama generation failed for model {model_name}: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_structured_interpretation(
        self,
        query: LLMInterpretationInput,
        wina_gating_mask: Optional[Dict[str, bool]] = None
    ) -> LLMStructuredOutput:
        """
        Get structured interpretation using Ollama model.
        
        Args:
            query: LLM interpretation input
            wina_gating_mask: Optional WINA gating mask for optimization
            
        Returns:
            Structured LLM output with interpretations
        """
        try:
            prompt = self._construct_constitutional_prompt(query, wina_gating_mask)
            
            response_text = await self.generate_text(
                prompt=prompt,
                temperature=0.1,  # Low temperature for structured output
                max_tokens=2048
            )
            
            # Parse the response into structured format
            interpretations = self._parse_constitutional_response(response_text, query)
            
            return LLMStructuredOutput(
                interpretations=interpretations,
                raw_llm_response=response_text
            )
            
        except Exception as e:
            logger.error(f"Ollama structured interpretation failed for principle {query.principle_id}: {e}")

            # Create a fallback interpretation
            fallback_rule = LLMSuggestedRule(
                head=LLMSuggestedAtom(
                    predicate_name=f"ollama_fallback_rule_{query.principle_id}",
                    arguments=["Context"]
                ),
                body=[],
                explanation=f"Fallback rule due to error: {str(e)}",
                confidence=0.1
            )

            return LLMStructuredOutput(
                interpretations=[fallback_rule],
                raw_llm_response=f"Error in Ollama interpretation: {str(e)}"
            )
    
    def _construct_constitutional_prompt(
        self,
        query: LLMInterpretationInput,
        wina_gating_mask: Optional[Dict[str, bool]] = None
    ) -> str:
        """Construct constitutional prompting prompt for Ollama."""
        prompt = f"""You are an AI assistant specialized in constitutional governance and policy synthesis.

Constitutional Principle ID: {query.principle_id}
Principle Text: {query.principle_content}

Target Context: {query.target_context or "general"}
Datalog Schema: {json.dumps(query.datalog_predicate_schema or {}, indent=2)}

Task: Provide a structured interpretation of how this constitutional principle applies to the given environmental context. Focus on:

1. Direct applicability and relevance
2. Potential conflicts or tensions
3. Implementation guidance
4. Risk assessment
5. Compliance requirements

Please provide your response in a clear, structured format that can be used for policy synthesis.

Response:"""
        
        return prompt
    
    def _parse_constitutional_response(
        self,
        response_text: str,
        query: LLMInterpretationInput
    ) -> List[LLMSuggestedRule]:
        """Parse Ollama response into structured interpretations."""
        # Simple parsing - in production, this could be more sophisticated
        # Create a basic rule structure from the response
        head = LLMSuggestedAtom(
            predicate_name=f"ollama_constitutional_rule_{query.principle_id}",
            arguments=["Context", "Action"]
        )

        body = [
            LLMSuggestedAtom(
                predicate_name="constitutional_principle_satisfied",
                arguments=["Context", f"principle_{query.principle_id}"]
            )
        ]

        rule = LLMSuggestedRule(
            head=head,
            body=body,
            explanation=response_text.strip()[:500],  # Truncate for explanation
            confidence=0.8  # Default confidence for local model
        )

        return [rule]


# Global Ollama client instance
_ollama_client: Optional[OllamaLLMClient] = None


async def get_ollama_client() -> OllamaLLMClient:
    """
    Get the global Ollama client instance.
    
    Returns:
        OllamaLLMClient instance
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaLLMClient()
        
        # Verify server availability
        if not await _ollama_client.health_check():
            logger.warning("Ollama server not available. Client created but may not function.")
    
    return _ollama_client


async def close_ollama_client():
    """Close the global Ollama client."""
    global _ollama_client
    if _ollama_client:
        await _ollama_client.close()
        _ollama_client = None
