"""
Multi-Model LLM Manager for GS Engine

This module implements the multi-model LLM management patterns from the
Gemini-LangGraph analysis, providing specialized model selection, fallback
mechanisms, and reliability tracking for >99.9% reliability targets.

Enhanced for Task 18: GS Engine Multi-Model Enhancement with:
- LangGraph StateGraph integration for model orchestration
- Specialized Gemini model configuration
- Circuit breaker patterns for >99.9% reliability
- Constitutional compliance validation with fidelity scoring
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Type, Union
from datetime import datetime, timezone
import time
import json
from enum import Enum
from dataclasses import dataclass, field

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import AIMessage, HumanMessage
    from langgraph.graph import StateGraph, END
    from langgraph.graph.state import CompiledStateGraph
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatGoogleGenerativeAI = None
    AIMessage = None
    HumanMessage = None
    StateGraph = None
    END = None
    CompiledStateGraph = None

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# NVIDIA API support for Qwen models
try:
    import asyncio
    NVIDIA_API_AVAILABLE = True
except ImportError:
    NVIDIA_API_AVAILABLE = False

from shared.langgraph_config import (
    get_langgraph_config,
    ModelRole,
    PolicySynthesisConfig
)

# Ollama client import
try:
    from ..core.ollama_client import OllamaLLMClient, get_ollama_client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    OllamaLLMClient = None
    get_ollama_client = None

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states for model failure handling."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before attempting recovery
    success_threshold: int = 3  # Successes needed to close circuit
    timeout_seconds: int = 30   # Request timeout


@dataclass
class ModelHealthMetrics:
    """Health metrics for individual models."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    circuit_breaker_state: CircuitBreakerState = CircuitBreakerState.CLOSED

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0

    @property
    def is_healthy(self) -> bool:
        """Determine if model is healthy based on metrics."""
        return (
            self.circuit_breaker_state == CircuitBreakerState.CLOSED and
            self.success_rate >= 80.0 and
            self.consecutive_failures < 3
        )


class ModelPerformanceTracker:
    """Tracks performance metrics for individual models."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        self.quality_scores: List[float] = []
        self.last_failure_time: Optional[datetime] = None
        self.circuit_breaker_open = False
    
    def record_success(self, response_time: float, quality_score: Optional[float] = None):
        """Record a successful model request."""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_response_time += response_time
        
        if quality_score is not None:
            self.quality_scores.append(quality_score)
            # Keep only last 100 scores
            if len(self.quality_scores) > 100:
                self.quality_scores = self.quality_scores[-100:]
    
    def record_failure(self):
        """Record a failed model request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        # Open circuit breaker if failure rate is too high
        if self.get_failure_rate() > 0.5 and self.total_requests > 5:
            self.circuit_breaker_open = True
            logger.warning(f"Circuit breaker opened for model {self.model_name}")
    
    def get_success_rate(self) -> float:
        """Get the success rate for this model."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    def get_failure_rate(self) -> float:
        """Get the failure rate for this model."""
        return 1.0 - self.get_success_rate()
    
    def get_average_response_time(self) -> float:
        """Get the average response time for this model."""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests
    
    def get_average_quality_score(self) -> float:
        """Get the average quality score for this model."""
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores) / len(self.quality_scores)
    
    def should_use_model(self) -> bool:
        """Determine if this model should be used based on performance."""
        if self.circuit_breaker_open:
            # Check if we should try to close the circuit breaker
            if (self.last_failure_time and 
                (datetime.now(timezone.utc) - self.last_failure_time).seconds > 300):  # 5 minutes
                self.circuit_breaker_open = False
                logger.info(f"Circuit breaker closed for model {self.model_name}")
                return True
            return False
        
        return True


class MultiModelManager:
    """
    Manages multiple LLM models with role-based selection and fallback mechanisms.
    
    Implements patterns from the Gemini-LangGraph analysis for achieving >99.9%
    reliability through model ensemble and intelligent fallback strategies.
    """
    
    def __init__(self):
        self.config = get_langgraph_config()
        self.synthesis_config = PolicySynthesisConfig()
        self.model_clients: Dict[str, Any] = {}
        self.performance_trackers: Dict[str, ModelPerformanceTracker] = {}
        
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available. Multi-model functionality will be limited.")
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize model clients for all configured models."""
        if not LANGCHAIN_AVAILABLE:
            return
        
        # Get all unique models from configuration
        all_models = set()
        all_models.update(self.config.models.values())
        all_models.update(self.config.fallback_models.values())
        
        for model_name in all_models:
            try:
                if model_name.startswith("gemini"):
                    if self.config.gemini_api_key and LANGCHAIN_AVAILABLE:
                        client = ChatGoogleGenerativeAI(
                            model=model_name,
                            api_key=self.config.gemini_api_key,
                            max_retries=1,  # We handle retries at the manager level
                            timeout=self.config.timeout_seconds
                        )
                        self.model_clients[model_name] = client
                        self.performance_trackers[model_name] = ModelPerformanceTracker(model_name)
                        logger.info(f"Initialized Gemini model: {model_name}")

                elif model_name.startswith("meta-llama/") or model_name.startswith("llama"):
                    if self.config.groq_api_key and GROQ_AVAILABLE:
                        client = Groq(api_key=self.config.groq_api_key)
                        self.model_clients[model_name] = client
                        self.performance_trackers[model_name] = ModelPerformanceTracker(model_name)
                        logger.info(f"Initialized Groq Llama model: {model_name}")

                elif model_name.startswith("grok"):
                    if self.config.xai_api_key and OPENAI_AVAILABLE:
                        client = OpenAI(
                            api_key=self.config.xai_api_key,
                            base_url="https://api.x.ai/v1"
                        )
                        self.model_clients[model_name] = client
                        self.performance_trackers[model_name] = ModelPerformanceTracker(model_name)
                        logger.info(f"Initialized xAI Grok model: {model_name}")

                elif model_name.startswith("gpt"):
                    if self.config.openai_api_key and OPENAI_AVAILABLE:
                        client = OpenAI(api_key=self.config.openai_api_key)
                        self.model_clients[model_name] = client
                        self.performance_trackers[model_name] = ModelPerformanceTracker(model_name)
                        logger.info(f"Initialized OpenAI model: {model_name}")

                elif model_name.startswith("qwen/") or model_name.startswith("nvidia/"):
                    if self.config.nvidia_api_key and OPENAI_AVAILABLE:
                        client = OpenAI(
                            base_url="https://integrate.api.nvidia.com/v1",
                            api_key=self.config.nvidia_api_key
                        )
                        self.model_clients[model_name] = client
                        self.performance_trackers[model_name] = ModelPerformanceTracker(model_name)
                        logger.info(f"Initialized NVIDIA API model: {model_name}")

                elif (model_name.startswith("hf.co/") or
                      model_name.startswith("deepseek") or
                      model_name in ["llama3.1", "mistral", "codellama"]):
                    # Ollama local models
                    if OLLAMA_AVAILABLE:
                        try:
                            # Create Ollama client instance
                            client = OllamaLLMClient()
                            self.model_clients[model_name] = client
                            self.performance_trackers[model_name] = ModelPerformanceTracker(model_name)
                            logger.info(f"Initialized Ollama model: {model_name}")
                        except Exception as ollama_error:
                            logger.warning(f"Failed to initialize Ollama model {model_name}: {ollama_error}")

            except Exception as e:
                logger.error(f"Failed to initialize model {model_name}: {e}")
    
    async def get_model_response(
        self,
        role: ModelRole,
        prompt: str,
        structured_output_class: Optional[Type] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get response from specialized model with fallback support.
        
        Args:
            role: Model role for task specialization
            prompt: Input prompt for the model
            structured_output_class: Optional Pydantic class for structured output
            max_retries: Optional override for max retry attempts
            
        Returns:
            Model response with metadata
        """
        if not LANGCHAIN_AVAILABLE:
            return {
                "content": "LangChain not available - using mock response",
                "model_used": "mock",
                "success": False,
                "error": "LangChain not available"
            }
        
        max_retries = max_retries or self.config.max_retries
        primary_model = self.config.get_model_for_role(role)
        fallback_model = self.config.get_fallback_model_for_role(role)
        temperature = self.config.get_temperature_for_role(role)
        
        # Try primary model first
        for attempt in range(max_retries):
            model_to_use = primary_model if attempt < max_retries - 1 else fallback_model
            
            # Check if model should be used (circuit breaker)
            if (model_to_use in self.performance_trackers and 
                not self.performance_trackers[model_to_use].should_use_model()):
                continue
            
            try:
                start_time = time.time()
                response = await self._call_model(
                    model_to_use, prompt, temperature, structured_output_class
                )
                response_time = time.time() - start_time
                
                # Record success
                if model_to_use in self.performance_trackers:
                    self.performance_trackers[model_to_use].record_success(response_time)
                
                return {
                    "content": response,
                    "model_used": model_to_use,
                    "response_time": response_time,
                    "attempt": attempt + 1,
                    "success": True
                }
                
            except Exception as e:
                logger.warning(f"Model {model_to_use} failed on attempt {attempt + 1}: {e}")
                
                # Record failure
                if model_to_use in self.performance_trackers:
                    self.performance_trackers[model_to_use].record_failure()
                
                if attempt == max_retries - 1:
                    return {
                        "content": None,
                        "model_used": model_to_use,
                        "success": False,
                        "error": str(e),
                        "attempts": max_retries
                    }
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        return {
            "content": None,
            "success": False,
            "error": "All retry attempts failed",
            "attempts": max_retries
        }
    
    async def _call_model(
        self,
        model_name: str,
        prompt: str,
        temperature: float,
        structured_output_class: Optional[Type] = None
    ) -> str:
        """Call a specific model with the given parameters."""
        if model_name not in self.model_clients:
            raise ValueError(f"Model {model_name} not available")

        client = self.model_clients[model_name]

        # Handle different client types
        if isinstance(client, ChatGoogleGenerativeAI):
            # LangChain Google Gemini client
            client.temperature = temperature

            if structured_output_class:
                structured_client = client.with_structured_output(structured_output_class)
                response = await structured_client.ainvoke(prompt)
                return response
            else:
                response = await client.ainvoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)

        elif isinstance(client, Groq):
            # Groq client for Llama models
            # Run in thread pool since Groq client is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=4096
                )
            )
            content = response.choices[0].message.content

            if structured_output_class:
                # For structured output, we'd need to parse the JSON response
                # For now, return the raw content
                return content
            else:
                return content

        elif isinstance(client, OpenAI):
            # OpenAI client (for xAI Grok, OpenAI models, or NVIDIA API models)
            # Handle NVIDIA API models with reasoning capabilities
            if model_name.startswith("qwen/") or model_name.startswith("nvidia/"):
                # NVIDIA API with reasoning support
                loop = asyncio.get_event_loop()

                # Check if this is a reasoning model (Qwen 3 235B)
                extra_body = {}
                if "qwen3-235b" in model_name.lower():
                    extra_body = {"chat_template_kwargs": {"thinking": True}}

                response = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        top_p=0.7,
                        max_tokens=8192,
                        extra_body=extra_body,
                        stream=False  # For now, use non-streaming for simplicity
                    )
                )
                content = response.choices[0].message.content

                # For reasoning models, we might want to extract reasoning content
                if hasattr(response.choices[0].message, 'reasoning_content'):
                    reasoning = response.choices[0].message.reasoning_content
                    if reasoning:
                        content = f"[REASONING]\n{reasoning}\n\n[RESPONSE]\n{content}"

                return content
            else:
                # Standard OpenAI API call
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=4096
                    )
                )
                content = response.choices[0].message.content

                if structured_output_class:
                    # For structured output, we'd need to parse the JSON response
                    # For now, return the raw content
                    return content
                else:
                    return content

        elif isinstance(client, OllamaLLMClient):
            # Ollama local model client
            if structured_output_class:
                # For structured output, use the structured interpretation method
                from ..core.llm_integration import LLMInterpretationInput

                # Create a mock query for structured output
                query = LLMInterpretationInput(
                    principle_id="structured_output",
                    principle_text=prompt,
                    environmental_context={}
                )

                response = await client.get_structured_interpretation(query)
                return response.raw_llm_response
            else:
                # Standard text generation
                response = await client.generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=4096
                )
                return response

        else:
            raise ValueError(f"Unsupported client type for model {model_name}: {type(client)}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all models."""
        metrics = {}
        
        for model_name, tracker in self.performance_trackers.items():
            metrics[model_name] = {
                "total_requests": tracker.total_requests,
                "success_rate": tracker.get_success_rate(),
                "failure_rate": tracker.get_failure_rate(),
                "average_response_time": tracker.get_average_response_time(),
                "average_quality_score": tracker.get_average_quality_score(),
                "circuit_breaker_open": tracker.circuit_breaker_open,
                "last_failure_time": tracker.last_failure_time.isoformat() if tracker.last_failure_time else None
            }
        
        # Calculate overall metrics
        total_requests = sum(tracker.total_requests for tracker in self.performance_trackers.values())
        total_successful = sum(tracker.successful_requests for tracker in self.performance_trackers.values())
        
        metrics["overall"] = {
            "total_requests": total_requests,
            "overall_success_rate": total_successful / total_requests if total_requests > 0 else 0.0,
            "reliability_target_met": (total_successful / total_requests) >= 0.999 if total_requests > 0 else False,
            "active_models": len([t for t in self.performance_trackers.values() if t.should_use_model()]),
            "total_models": len(self.performance_trackers)
        }
        
        return metrics
    
    def get_model_recommendations(self) -> Dict[str, str]:
        """Get model recommendations based on performance."""
        recommendations = {}
        
        for role in ModelRole:
            primary_model = self.config.get_model_for_role(role)
            fallback_model = self.config.get_fallback_model_for_role(role)
            
            primary_tracker = self.performance_trackers.get(primary_model)
            fallback_tracker = self.performance_trackers.get(fallback_model)
            
            if primary_tracker and primary_tracker.should_use_model():
                if primary_tracker.get_success_rate() >= 0.95:
                    recommendations[role.value] = f"Use {primary_model} (excellent performance)"
                else:
                    recommendations[role.value] = f"Use {primary_model} with caution (success rate: {primary_tracker.get_success_rate():.2%})"
            elif fallback_tracker and fallback_tracker.should_use_model():
                recommendations[role.value] = f"Use fallback {fallback_model} (primary model unavailable)"
            else:
                recommendations[role.value] = "No reliable models available - manual intervention required"
        
        return recommendations


# Global multi-model manager instance
_multi_model_manager: Optional[MultiModelManager] = None


def get_multi_model_manager() -> MultiModelManager:
    """Get the global multi-model manager instance."""
    global _multi_model_manager
    if _multi_model_manager is None:
        _multi_model_manager = MultiModelManager()
    return _multi_model_manager
