"""
Multi-Model LLM Manager for GS Engine

This module implements the multi-model LLM management patterns from the
Gemini-LangGraph analysis, providing specialized model selection, fallback
mechanisms, and reliability tracking for >99.9% reliability targets.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Type
from datetime import datetime, timezone
import time

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import AIMessage, HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatGoogleGenerativeAI = None
    AIMessage = None
    HumanMessage = None

from src.backend.shared.langgraph_config import (
    get_langgraph_config,
    ModelRole,
    PolicySynthesisConfig
)

logger = logging.getLogger(__name__)


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
                    if self.config.gemini_api_key:
                        client = ChatGoogleGenerativeAI(
                            model=model_name,
                            api_key=self.config.gemini_api_key,
                            max_retries=1,  # We handle retries at the manager level
                            timeout=self.config.timeout_seconds
                        )
                        self.model_clients[model_name] = client
                        self.performance_trackers[model_name] = ModelPerformanceTracker(model_name)
                        logger.info(f"Initialized Gemini model: {model_name}")
                
                # Add support for other model providers here
                # elif model_name.startswith("gpt"):
                #     # OpenAI models
                # elif model_name.startswith("llama"):
                #     # Groq/Llama models
                
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
        
        # Update temperature
        client.temperature = temperature
        
        if structured_output_class:
            structured_client = client.with_structured_output(structured_output_class)
            response = await structured_client.ainvoke(prompt)
            return response
        else:
            response = await client.ainvoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
    
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
