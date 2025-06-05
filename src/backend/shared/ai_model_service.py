#!/usr/bin/env python3
"""
AI Model Service for ACGS-PGP
Provides centralized AI model management and integration for the ACGS-PGP framework.
Supports Google Gemini 2.5 Flash, DeepSeek-R1, and other AI models for various operations.
"""

import asyncio
import httpx
import json
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
try:
    from .utils import get_config
except ImportError:
    from utils import get_config

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported AI model providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"
    MISTRAL = "mistral"
    XAI = "xai"


class ModelRole(Enum):
    """AI model roles in ACGS-PGP operations."""
    PRIMARY = "primary"              # Main policy synthesis and governance
    RESEARCH = "research"            # Research-backed operations
    FALLBACK = "fallback"           # Backup model
    BIAS_DETECTION = "bias_detection"  # Bias detection and fairness analysis
    TESTING = "testing"             # Testing and validation
    CONSTITUTIONAL = "constitutional"  # Constitutional analysis


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    provider: ModelProvider
    model_id: str
    max_tokens: int
    temperature: float
    enabled: bool = True
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    role: Optional[ModelRole] = None


@dataclass
class ModelResponse:
    """Response from an AI model."""
    content: str
    model_id: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AIModelService:
    """
    Centralized AI model service for ACGS-PGP operations.
    Manages multiple AI models and provides unified interface for different tasks.
    """
    
    def __init__(self):
        """Initialize AI model service with centralized configuration."""
        self.config = get_config()
        self.models = self._load_model_configurations()
        self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"AIModelService initialized with {len(self.models)} models")
    
    def _load_model_configurations(self) -> Dict[str, ModelConfig]:
        """Load model configurations from centralized config."""
        models = {}
        
        # Primary models
        models['primary'] = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_id=self.config.get_ai_model('primary'),
            max_tokens=self.config.get('llm_settings.max_tokens', 64000),
            temperature=self.config.get('llm_settings.temperature', 0.2),
            api_key=self.config.get_ai_api_key('anthropic'),
            role=ModelRole.PRIMARY
        )
        
        models['research'] = ModelConfig(
            provider=ModelProvider.PERPLEXITY,
            model_id=self.config.get_ai_model('research'),
            max_tokens=8700,
            temperature=self.config.get('llm_settings.research_temperature', 0.1),
            api_key=self.config.get_ai_api_key('perplexity'),
            role=ModelRole.RESEARCH
        )
        
        models['fallback'] = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_id=self.config.get_ai_model('fallback'),
            max_tokens=self.config.get('llm_settings.max_tokens', 64000),
            temperature=self.config.get('llm_settings.temperature', 0.2),
            api_key=self.config.get_ai_api_key('anthropic'),
            role=ModelRole.FALLBACK
        )
        
        # Google Gemini 2.5 Flash for testing
        if self.config.is_model_enabled('enable_gemini_2_5_flash'):
            models['gemini_2_5_flash'] = ModelConfig(
                provider=ModelProvider.GOOGLE,
                model_id=self.config.get_ai_model('gemini_2_5_flash'),
                max_tokens=32000,
                temperature=0.1,
                api_key=self.config.get_ai_api_key('google'),
                role=ModelRole.TESTING,
                enabled=True
            )
        
        # DeepSeek-R1 models for research operations
        if self.config.is_model_enabled('enable_deepseek_r1'):
            # HuggingFace version
            models['deepseek_r1_hf'] = ModelConfig(
                provider=ModelProvider.HUGGINGFACE,
                model_id=self.config.get_ai_model('deepseek_r1'),
                max_tokens=8192,
                temperature=0.2,
                api_key=self.config.get_ai_api_key('huggingface'),
                endpoint=self.config.get_ai_endpoint('huggingface'),
                role=ModelRole.RESEARCH,
                enabled=True
            )
            
            # OpenRouter version (more reliable)
            models['deepseek_r1_openrouter'] = ModelConfig(
                provider=ModelProvider.OPENROUTER,
                model_id=self.config.get_ai_model('deepseek_r1_openrouter'),
                max_tokens=8192,
                temperature=0.2,
                api_key=self.config.get_ai_api_key('openrouter'),
                endpoint=self.config.get_ai_endpoint('openrouter'),
                role=ModelRole.RESEARCH,
                enabled=True
            )
        
        return models
    
    async def generate_text(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        role: Optional[ModelRole] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate text using specified model or role.
        
        Args:
            prompt: Input prompt for text generation
            model_name: Specific model name to use
            role: Model role to use (if model_name not specified)
            max_tokens: Override max tokens
            temperature: Override temperature
            **kwargs: Additional model-specific parameters
            
        Returns:
            ModelResponse with generated text and metadata
        """
        # Determine which model to use
        if model_name:
            if model_name not in self.models:
                raise ValueError(f"Unknown model: {model_name}")
            model_config = self.models[model_name]
        elif role:
            model_config = self._get_model_by_role(role)
        else:
            model_config = self.models['primary']
        
        # Override parameters if provided
        if max_tokens:
            model_config.max_tokens = max_tokens
        if temperature is not None:
            model_config.temperature = temperature
        
        # Generate text based on provider
        try:
            if model_config.provider == ModelProvider.GOOGLE:
                return await self._generate_google(prompt, model_config, **kwargs)
            elif model_config.provider == ModelProvider.HUGGINGFACE:
                return await self._generate_huggingface(prompt, model_config, **kwargs)
            elif model_config.provider == ModelProvider.OPENROUTER:
                return await self._generate_openrouter(prompt, model_config, **kwargs)
            else:
                # For other providers, use mock response for now
                return await self._generate_mock(prompt, model_config, **kwargs)
                
        except Exception as e:
            logger.error(f"Error generating text with {model_config.model_id}: {e}")
            # Fallback to mock response
            return await self._generate_mock(prompt, model_config, error=str(e))
    
    def _get_model_by_role(self, role: ModelRole) -> ModelConfig:
        """Get model configuration by role."""
        for model_config in self.models.values():
            if model_config.role == role and model_config.enabled:
                return model_config
        
        # Fallback to primary model
        return self.models['primary']
    
    async def _generate_google(self, prompt: str, config: ModelConfig, **kwargs) -> ModelResponse:
        """Generate text using Google Gemini API."""
        if not config.api_key:
            raise ValueError("Google API key not configured")
        
        # Mock implementation for now - would integrate with actual Google API
        logger.info(f"Generating text with Google Gemini 2.5 Flash: {config.model_id}")
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        return ModelResponse(
            content=f"[Google Gemini 2.5 Flash Response] Generated response for: {prompt[:100]}...",
            model_id=config.model_id,
            provider=config.provider.value,
            tokens_used=len(prompt.split()) * 2,
            finish_reason="completed",
            metadata={"provider": "google", "model_type": "gemini_2_5_flash"}
        )
    
    async def _generate_huggingface(self, prompt: str, config: ModelConfig, **kwargs) -> ModelResponse:
        """Generate text using HuggingFace Inference API."""
        if not config.api_key:
            raise ValueError("HuggingFace API key not configured")
        
        logger.info(f"Generating text with HuggingFace DeepSeek-R1: {config.model_id}")
        
        # Mock implementation for now - would integrate with actual HuggingFace API
        await asyncio.sleep(0.2)
        
        return ModelResponse(
            content=f"[DeepSeek-R1 HuggingFace Response] Research-backed analysis: {prompt[:100]}...",
            model_id=config.model_id,
            provider=config.provider.value,
            tokens_used=len(prompt.split()) * 2,
            finish_reason="completed",
            metadata={"provider": "huggingface", "model_type": "deepseek_r1"}
        )
    
    async def _generate_openrouter(self, prompt: str, config: ModelConfig, **kwargs) -> ModelResponse:
        """Generate text using OpenRouter API."""
        if not config.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        logger.info(f"Generating text with OpenRouter DeepSeek: {config.model_id}")
        
        # Mock implementation for now - would integrate with actual OpenRouter API
        await asyncio.sleep(0.15)
        
        return ModelResponse(
            content=f"[DeepSeek-R1 OpenRouter Response] Advanced reasoning: {prompt[:100]}...",
            model_id=config.model_id,
            provider=config.provider.value,
            tokens_used=len(prompt.split()) * 2,
            finish_reason="completed",
            metadata={"provider": "openrouter", "model_type": "deepseek_r1"}
        )
    
    async def _generate_mock(self, prompt: str, config: ModelConfig, error: Optional[str] = None, **kwargs) -> ModelResponse:
        """Generate mock response for testing."""
        await asyncio.sleep(0.05)
        
        content = f"[Mock {config.provider.value} Response]"
        if error:
            content += f" Error occurred: {error}. "
        content += f" Generated response for: {prompt[:100]}..."
        
        return ModelResponse(
            content=content,
            model_id=config.model_id,
            provider=config.provider.value,
            tokens_used=len(prompt.split()) * 2,
            finish_reason="completed" if not error else "error",
            metadata={"provider": config.provider.value, "mock": True, "error": error}
        )
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available models."""
        return {
            name: {
                'provider': config.provider.value,
                'model_id': config.model_id,
                'role': config.role.value if config.role else None,
                'enabled': config.enabled,
                'max_tokens': config.max_tokens,
                'temperature': config.temperature,
                'has_api_key': config.api_key is not None
            }
            for name, config in self.models.items()
        }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Global AI model service instance
_ai_model_service: Optional[AIModelService] = None


async def get_ai_model_service() -> AIModelService:
    """Get global AI model service instance."""
    global _ai_model_service
    
    if _ai_model_service is None:
        _ai_model_service = AIModelService()
    
    return _ai_model_service


async def reset_ai_model_service():
    """Reset global AI model service (useful for testing)."""
    global _ai_model_service
    
    if _ai_model_service:
        await _ai_model_service.close()
    
    _ai_model_service = None
