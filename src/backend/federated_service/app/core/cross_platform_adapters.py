"""
Cross-Platform Adapters for Federated Evaluation Framework

Provides standardized evaluation interface across different LLM platforms
with platform-specific optimizations and Byzantine fault tolerance.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import json
import hashlib

import httpx
import numpy as np
from pydantic import BaseModel, Field

from .federated_evaluator import PlatformType, FederatedNode
from .secure_aggregation import SecureAggregator, AggregationMethod
from shared.metrics import get_metrics

logger = logging.getLogger(__name__)

# Initialize metrics with error handling for test environments
try:
    metrics = get_metrics("federated_service")
except Exception as e:
    logger.warning(f"Failed to initialize metrics: {e}")
    # Create a mock metrics object for testing
    class MockMetrics:
        def counter(self, name, labels=None):
            return type('MockCounter', (), {'inc': lambda: None})()
        def histogram(self, name, labels=None):
            return type('MockHistogram', (), {'observe': lambda x: None})()
    metrics = MockMetrics()


class AdapterStatus(Enum):
    """Status of platform adapter."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class EvaluationMode(Enum):
    """Evaluation mode for different use cases."""
    CONSTITUTIONAL = "constitutional"
    SAFETY_CRITICAL = "safety_critical"
    FAIRNESS_AWARE = "fairness_aware"
    ADAPTIVE = "adaptive"


@dataclass
class PlatformCapabilities:
    """Platform-specific capabilities and limitations."""
    max_tokens: int = 4096
    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_json_mode: bool = False
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 10000
    latency_p95_ms: float = 1000.0
    reliability_score: float = 0.95
    cost_per_1k_tokens: float = 0.002
    
    # Platform-specific features
    supports_constitutional_ai: bool = False
    supports_bias_detection: bool = False
    supports_safety_filtering: bool = False


@dataclass
class EvaluationRequest:
    """Standardized evaluation request across platforms."""
    request_id: str
    policy_content: str
    evaluation_criteria: Dict[str, Any]
    mode: EvaluationMode = EvaluationMode.CONSTITUTIONAL
    context: Dict[str, Any] = field(default_factory=dict)
    privacy_requirements: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 60.0
    
    # MAB integration
    mab_context: Dict[str, Any] = field(default_factory=dict)
    prompt_template_id: Optional[str] = None


@dataclass
class EvaluationResponse:
    """Standardized evaluation response across platforms."""
    request_id: str
    platform_type: PlatformType
    success: bool
    
    # Core evaluation results
    policy_compliance_score: float = 0.0
    constitutional_alignment: float = 0.0
    safety_score: float = 0.0
    fairness_score: float = 0.0
    
    # Performance metrics
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    
    # Platform-specific results
    platform_specific_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Error handling
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    adapter_version: str = "1.0.0"


class BasePlatformAdapter(ABC):
    """Abstract base class for platform adapters."""
    
    def __init__(self, platform_type: PlatformType, capabilities: PlatformCapabilities):
        self.platform_type = platform_type
        self.capabilities = capabilities
        self.status = AdapterStatus.INACTIVE
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time_ms": 0.0,
            "total_tokens_used": 0,
            "total_cost": 0.0
        }
        self._client: Optional[httpx.AsyncClient] = None
        
    async def initialize(self) -> None:
        """Initialize the platform adapter."""
        try:
            self._client = httpx.AsyncClient(timeout=60.0)
            await self._platform_specific_init()
            self.status = AdapterStatus.ACTIVE
            logger.info(f"Initialized {self.platform_type.value} adapter")
            
        except Exception as e:
            self.status = AdapterStatus.ERROR
            logger.error(f"Failed to initialize {self.platform_type.value} adapter: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the platform adapter."""
        try:
            if self._client:
                await self._client.aclose()
            await self._platform_specific_shutdown()
            self.status = AdapterStatus.INACTIVE
            logger.info(f"Shutdown {self.platform_type.value} adapter")
            
        except Exception as e:
            logger.error(f"Error during {self.platform_type.value} adapter shutdown: {e}")
    
    @abstractmethod
    async def _platform_specific_init(self) -> None:
        """Platform-specific initialization logic."""
        pass
    
    @abstractmethod
    async def _platform_specific_shutdown(self) -> None:
        """Platform-specific shutdown logic."""
        pass
    
    @abstractmethod
    async def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate policy using platform-specific implementation."""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the platform."""
        try:
            start_time = time.time()
            
            # Simple test request
            test_request = EvaluationRequest(
                request_id="health_check",
                policy_content="package test\nallow { true }",
                evaluation_criteria={"category": "health_check"},
                timeout_seconds=10.0
            )
            
            response = await self.evaluate(test_request)
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy" if response.success else "unhealthy",
                "platform_type": self.platform_type.value,
                "response_time_ms": response_time,
                "capabilities": self.capabilities.__dict__,
                "metrics": self.metrics
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "platform_type": self.platform_type.value,
                "error": str(e),
                "capabilities": self.capabilities.__dict__,
                "metrics": self.metrics
            }
    
    def _update_metrics(self, response: EvaluationResponse) -> None:
        """Update adapter metrics."""
        self.metrics["total_requests"] += 1
        
        if response.success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        # Update average response time
        current_avg = self.metrics["avg_response_time_ms"]
        total_requests = self.metrics["total_requests"]
        new_avg = ((current_avg * (total_requests - 1)) + response.execution_time_ms) / total_requests
        self.metrics["avg_response_time_ms"] = new_avg
        
        self.metrics["total_tokens_used"] += response.tokens_used
        self.metrics["total_cost"] += response.cost_estimate
        
        # Update Prometheus metrics
        metrics.counter("federated_adapter_requests_total", 
                       labels={"platform": self.platform_type.value, "status": "success" if response.success else "error"}).inc()
        metrics.histogram("federated_adapter_response_time_ms", 
                         labels={"platform": self.platform_type.value}).observe(response.execution_time_ms)


class OpenAIPlatformAdapter(BasePlatformAdapter):
    """OpenAI platform adapter with GPT-4 optimization."""
    
    def __init__(self, api_key: str):
        capabilities = PlatformCapabilities(
            max_tokens=8192,
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            rate_limit_rpm=500,
            rate_limit_tpm=40000,
            latency_p95_ms=800.0,
            reliability_score=0.98,
            cost_per_1k_tokens=0.03,
            supports_constitutional_ai=True,
            supports_bias_detection=True,
            supports_safety_filtering=True
        )
        super().__init__(PlatformType.CLOUD_OPENAI, capabilities)
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
    
    async def _platform_specific_init(self) -> None:
        """Initialize OpenAI-specific components."""
        # Test API key validity
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self._client.get(f"{self.base_url}/models", headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Invalid OpenAI API key: {response.status_code}")
    
    async def _platform_specific_shutdown(self) -> None:
        """OpenAI-specific shutdown logic."""
        pass
    
    async def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate policy using OpenAI GPT-4."""
        start_time = time.time()
        
        try:
            # Build OpenAI-optimized prompt
            prompt = self._build_constitutional_prompt(request)
            
            # Prepare OpenAI API request
            payload = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a constitutional AI policy evaluator."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": min(request.context.get("max_tokens", 2048), self.capabilities.max_tokens),
                "temperature": 0.1,  # Low temperature for consistent evaluation
                "response_format": {"type": "json_object"} if self.capabilities.supports_json_mode else None
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make API request
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=request.timeout_seconds
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_openai_response(request, result, execution_time)
            else:
                return EvaluationResponse(
                    request_id=request.request_id,
                    platform_type=self.platform_type,
                    success=False,
                    execution_time_ms=execution_time,
                    error_message=f"OpenAI API error: {response.status_code}",
                    error_code=str(response.status_code)
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e),
                error_code="ADAPTER_ERROR"
            )
        finally:
            # Update metrics regardless of success/failure
            if 'response' in locals():
                self._update_metrics(response)
    
    def _build_constitutional_prompt(self, request: EvaluationRequest) -> str:
        """Build OpenAI-optimized constitutional evaluation prompt."""
        return f"""
Evaluate the following policy for constitutional compliance and safety:

Policy Content:
{request.policy_content}

Evaluation Criteria:
{json.dumps(request.evaluation_criteria, indent=2)}

Please provide a JSON response with the following structure:
{{
    "policy_compliance_score": <float 0-1>,
    "constitutional_alignment": <float 0-1>,
    "safety_score": <float 0-1>,
    "fairness_score": <float 0-1>,
    "analysis": "<detailed analysis>",
    "recommendations": ["<recommendation1>", "<recommendation2>"]
}}
"""
    
    def _parse_openai_response(self, request: EvaluationRequest, result: Dict[str, Any], execution_time: float) -> EvaluationResponse:
        """Parse OpenAI API response into standardized format."""
        try:
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            
            # Try to parse JSON response
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError:
                # Fallback to default scores if JSON parsing fails
                parsed_content = {
                    "policy_compliance_score": 0.5,
                    "constitutional_alignment": 0.5,
                    "safety_score": 0.5,
                    "fairness_score": 0.5,
                    "analysis": content,
                    "recommendations": []
                }
            
            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=True,
                policy_compliance_score=parsed_content.get("policy_compliance_score", 0.5),
                constitutional_alignment=parsed_content.get("constitutional_alignment", 0.5),
                safety_score=parsed_content.get("safety_score", 0.5),
                fairness_score=parsed_content.get("fairness_score", 0.5),
                execution_time_ms=execution_time,
                tokens_used=usage.get("total_tokens", 0),
                cost_estimate=usage.get("total_tokens", 0) * self.capabilities.cost_per_1k_tokens / 1000,
                platform_specific_metrics={
                    "model": "gpt-4",
                    "analysis": parsed_content.get("analysis", ""),
                    "recommendations": parsed_content.get("recommendations", []),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0)
                }
            )
            
        except Exception as e:
            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=False,
                execution_time_ms=execution_time,
                error_message=f"Failed to parse OpenAI response: {e}",
                error_code="PARSE_ERROR"
            )


class AnthropicPlatformAdapter(BasePlatformAdapter):
    """Anthropic Claude platform adapter with Constitutional AI optimization."""

    def __init__(self, api_key: str):
        capabilities = PlatformCapabilities(
            max_tokens=8192,
            supports_streaming=True,
            supports_function_calling=False,
            supports_json_mode=False,
            rate_limit_rpm=300,
            rate_limit_tpm=30000,
            latency_p95_ms=1200.0,
            reliability_score=0.96,
            cost_per_1k_tokens=0.025,
            supports_constitutional_ai=True,  # Native Constitutional AI
            supports_bias_detection=True,
            supports_safety_filtering=True
        )
        super().__init__(PlatformType.CLOUD_ANTHROPIC, capabilities)
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"

    async def _platform_specific_init(self) -> None:
        """Initialize Anthropic-specific components."""
        # Test API key validity with a simple request
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        # Note: Anthropic doesn't have a models endpoint, so we'll validate during first request
        logger.info("Anthropic adapter initialized (API key validation deferred)")

    async def _platform_specific_shutdown(self) -> None:
        """Anthropic-specific shutdown logic."""
        pass

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate policy using Anthropic Claude with Constitutional AI."""
        start_time = time.time()

        try:
            # Build Anthropic-optimized constitutional prompt
            prompt = self._build_constitutional_prompt(request)

            # Prepare Anthropic API request
            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": min(request.context.get("max_tokens", 2048), self.capabilities.max_tokens),
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "system": "You are Claude, an AI assistant created by Anthropic to be helpful, harmless, and honest. You specialize in constitutional AI policy evaluation."
            }

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            # Make API request
            response = await self._client.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=headers,
                timeout=request.timeout_seconds
            )

            execution_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                return self._parse_anthropic_response(request, result, execution_time)
            else:
                return EvaluationResponse(
                    request_id=request.request_id,
                    platform_type=self.platform_type,
                    success=False,
                    execution_time_ms=execution_time,
                    error_message=f"Anthropic API error: {response.status_code}",
                    error_code=str(response.status_code)
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e),
                error_code="ADAPTER_ERROR"
            )

    def _build_constitutional_prompt(self, request: EvaluationRequest) -> str:
        """Build Anthropic-optimized constitutional evaluation prompt with Constitutional AI principles."""
        return f"""
I need you to evaluate the following policy for constitutional compliance, safety, and fairness using Constitutional AI principles.

Policy Content:
{request.policy_content}

Evaluation Criteria:
{json.dumps(request.evaluation_criteria, indent=2)}

Please analyze this policy according to Constitutional AI principles:
1. Helpfulness: Does the policy enable beneficial outcomes?
2. Harmlessness: Does the policy prevent harmful outcomes?
3. Honesty: Is the policy transparent and truthful?
4. Constitutional Compliance: Does it align with democratic values and human rights?
5. Fairness: Does it treat all stakeholders equitably?

Provide your evaluation in this format:
Policy Compliance Score (0-1): [score]
Constitutional Alignment (0-1): [score]
Safety Score (0-1): [score]
Fairness Score (0-1): [score]

Detailed Analysis:
[Your detailed constitutional analysis here]

Recommendations:
- [Recommendation 1]
- [Recommendation 2]
- [Additional recommendations as needed]
"""

    def _parse_anthropic_response(self, request: EvaluationRequest, result: Dict[str, Any], execution_time: float) -> EvaluationResponse:
        """Parse Anthropic API response into standardized format."""
        try:
            content = result["content"][0]["text"]
            usage = result.get("usage", {})

            # Parse structured response from Claude
            scores = self._extract_scores_from_text(content)
            analysis_sections = self._extract_analysis_sections(content)

            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=True,
                policy_compliance_score=scores.get("policy_compliance_score", 0.5),
                constitutional_alignment=scores.get("constitutional_alignment", 0.5),
                safety_score=scores.get("safety_score", 0.5),
                fairness_score=scores.get("fairness_score", 0.5),
                execution_time_ms=execution_time,
                tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                cost_estimate=(usage.get("input_tokens", 0) + usage.get("output_tokens", 0)) * self.capabilities.cost_per_1k_tokens / 1000,
                platform_specific_metrics={
                    "model": "claude-3-sonnet-20240229",
                    "analysis": analysis_sections.get("analysis", content),
                    "recommendations": analysis_sections.get("recommendations", []),
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "constitutional_ai_principles": ["helpfulness", "harmlessness", "honesty"]
                }
            )

        except Exception as e:
            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=False,
                execution_time_ms=execution_time,
                error_message=f"Failed to parse Anthropic response: {e}",
                error_code="PARSE_ERROR"
            )

    def _extract_scores_from_text(self, text: str) -> Dict[str, float]:
        """Extract numerical scores from Claude's text response."""
        import re

        scores = {}
        patterns = {
            "policy_compliance_score": r"Policy Compliance Score.*?(\d+\.?\d*)",
            "constitutional_alignment": r"Constitutional Alignment.*?(\d+\.?\d*)",
            "safety_score": r"Safety Score.*?(\d+\.?\d*)",
            "fairness_score": r"Fairness Score.*?(\d+\.?\d*)"
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    scores[key] = float(match.group(1))
                except ValueError:
                    scores[key] = 0.5  # Default fallback
            else:
                scores[key] = 0.5  # Default fallback

        return scores

    def _extract_analysis_sections(self, text: str) -> Dict[str, Any]:
        """Extract analysis and recommendations from Claude's response."""
        sections = {"analysis": "", "recommendations": []}

        # Extract detailed analysis
        analysis_match = re.search(r"Detailed Analysis:\s*(.*?)(?=Recommendations:|$)", text, re.DOTALL | re.IGNORECASE)
        if analysis_match:
            sections["analysis"] = analysis_match.group(1).strip()

        # Extract recommendations
        recommendations_match = re.search(r"Recommendations:\s*(.*?)$", text, re.DOTALL | re.IGNORECASE)
        if recommendations_match:
            recommendations_text = recommendations_match.group(1).strip()
            # Split by bullet points or dashes
            recommendations = re.findall(r"[-•]\s*(.*?)(?=\n[-•]|\n\n|$)", recommendations_text, re.DOTALL)
            sections["recommendations"] = [rec.strip() for rec in recommendations if rec.strip()]

        return sections


class CoherePlatformAdapter(BasePlatformAdapter):
    """Cohere platform adapter optimized for command models."""

    def __init__(self, api_key: str):
        capabilities = PlatformCapabilities(
            max_tokens=4096,
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=False,
            rate_limit_rpm=100,
            rate_limit_tpm=20000,
            latency_p95_ms=1500.0,
            reliability_score=0.94,
            cost_per_1k_tokens=0.015,
            supports_constitutional_ai=False,
            supports_bias_detection=True,
            supports_safety_filtering=True
        )
        super().__init__(PlatformType.CLOUD_COHERE, capabilities)
        self.api_key = api_key
        self.base_url = "https://api.cohere.ai/v1"

    async def _platform_specific_init(self) -> None:
        """Initialize Cohere-specific components."""
        # Test API key validity
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self._client.get(f"{self.base_url}/models", headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Invalid Cohere API key: {response.status_code}")

    async def _platform_specific_shutdown(self) -> None:
        """Cohere-specific shutdown logic."""
        pass

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate policy using Cohere Command model."""
        start_time = time.time()

        try:
            # Build Cohere-optimized prompt
            prompt = self._build_constitutional_prompt(request)

            # Prepare Cohere API request
            payload = {
                "model": "command",
                "prompt": prompt,
                "max_tokens": min(request.context.get("max_tokens", 2048), self.capabilities.max_tokens),
                "temperature": 0.1,
                "k": 0,  # Disable top-k sampling for consistency
                "p": 1.0,  # Disable nucleus sampling for consistency
                "stop_sequences": ["---END---"]
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Make API request
            response = await self._client.post(
                f"{self.base_url}/generate",
                json=payload,
                headers=headers,
                timeout=request.timeout_seconds
            )

            execution_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                return self._parse_cohere_response(request, result, execution_time)
            else:
                return EvaluationResponse(
                    request_id=request.request_id,
                    platform_type=self.platform_type,
                    success=False,
                    execution_time_ms=execution_time,
                    error_message=f"Cohere API error: {response.status_code}",
                    error_code=str(response.status_code)
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e),
                error_code="ADAPTER_ERROR"
            )

    def _build_constitutional_prompt(self, request: EvaluationRequest) -> str:
        """Build Cohere-optimized constitutional evaluation prompt."""
        return f"""
Evaluate the following policy for constitutional compliance, safety, and fairness.

Policy Content:
{request.policy_content}

Evaluation Criteria:
{json.dumps(request.evaluation_criteria, indent=2)}

Please provide a structured evaluation with scores from 0 to 1:

Policy Compliance Score: [0-1 score]
Constitutional Alignment: [0-1 score]
Safety Score: [0-1 score]
Fairness Score: [0-1 score]

Analysis:
[Provide detailed analysis of the policy's strengths and weaknesses]

Recommendations:
1. [First recommendation]
2. [Second recommendation]
3. [Additional recommendations as needed]

---END---
"""

    def _parse_cohere_response(self, request: EvaluationRequest, result: Dict[str, Any], execution_time: float) -> EvaluationResponse:
        """Parse Cohere API response into standardized format."""
        try:
            content = result["generations"][0]["text"]
            meta = result.get("meta", {})

            # Parse structured response from Cohere
            scores = self._extract_scores_from_text(content)
            analysis_sections = self._extract_analysis_sections(content)

            # Estimate token usage (Cohere doesn't always provide this)
            estimated_tokens = len(content.split()) * 1.3  # Rough estimation

            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=True,
                policy_compliance_score=scores.get("policy_compliance_score", 0.5),
                constitutional_alignment=scores.get("constitutional_alignment", 0.5),
                safety_score=scores.get("safety_score", 0.5),
                fairness_score=scores.get("fairness_score", 0.5),
                execution_time_ms=execution_time,
                tokens_used=int(estimated_tokens),
                cost_estimate=estimated_tokens * self.capabilities.cost_per_1k_tokens / 1000,
                platform_specific_metrics={
                    "model": "command",
                    "analysis": analysis_sections.get("analysis", content),
                    "recommendations": analysis_sections.get("recommendations", []),
                    "likelihood": result["generations"][0].get("likelihood", 0.0),
                    "finish_reason": result["generations"][0].get("finish_reason", "unknown")
                }
            )

        except Exception as e:
            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=False,
                execution_time_ms=execution_time,
                error_message=f"Failed to parse Cohere response: {e}",
                error_code="PARSE_ERROR"
            )

    def _extract_scores_from_text(self, text: str) -> Dict[str, float]:
        """Extract numerical scores from Cohere's text response."""
        import re

        scores = {}
        patterns = {
            "policy_compliance_score": r"Policy Compliance Score:\s*(\d+\.?\d*)",
            "constitutional_alignment": r"Constitutional Alignment:\s*(\d+\.?\d*)",
            "safety_score": r"Safety Score:\s*(\d+\.?\d*)",
            "fairness_score": r"Fairness Score:\s*(\d+\.?\d*)"
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    scores[key] = float(match.group(1))
                except ValueError:
                    scores[key] = 0.5  # Default fallback
            else:
                scores[key] = 0.5  # Default fallback

        return scores

    def _extract_analysis_sections(self, text: str) -> Dict[str, Any]:
        """Extract analysis and recommendations from Cohere's response."""
        sections = {"analysis": "", "recommendations": []}

        # Extract analysis
        analysis_match = re.search(r"Analysis:\s*(.*?)(?=Recommendations:|---END---|$)", text, re.DOTALL | re.IGNORECASE)
        if analysis_match:
            sections["analysis"] = analysis_match.group(1).strip()

        # Extract recommendations
        recommendations_match = re.search(r"Recommendations:\s*(.*?)(?=---END---|$)", text, re.DOTALL | re.IGNORECASE)
        if recommendations_match:
            recommendations_text = recommendations_match.group(1).strip()
            # Split by numbered items
            recommendations = re.findall(r"\d+\.\s*(.*?)(?=\n\d+\.|\n\n|$)", recommendations_text, re.DOTALL)
            sections["recommendations"] = [rec.strip() for rec in recommendations if rec.strip()]

        return sections


class GroqPlatformAdapter(BasePlatformAdapter):
    """Groq platform adapter optimized for fast inference."""

    def __init__(self, api_key: str):
        capabilities = PlatformCapabilities(
            max_tokens=8192,
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            rate_limit_rpm=30,
            rate_limit_tpm=6000,
            latency_p95_ms=300.0,  # Very fast inference
            reliability_score=0.92,
            cost_per_1k_tokens=0.0002,  # Very cost-effective
            supports_constitutional_ai=False,
            supports_bias_detection=False,
            supports_safety_filtering=True
        )
        super().__init__(PlatformType.CLOUD_GROQ, capabilities)
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"  # OpenAI-compatible API

    async def _platform_specific_init(self) -> None:
        """Initialize Groq-specific components."""
        # Test API key validity
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self._client.get(f"{self.base_url}/models", headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Invalid Groq API key: {response.status_code}")

    async def _platform_specific_shutdown(self) -> None:
        """Groq-specific shutdown logic."""
        pass

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate policy using Groq's fast inference."""
        start_time = time.time()

        try:
            # Build Groq-optimized prompt (similar to OpenAI format)
            prompt = self._build_constitutional_prompt(request)

            # Prepare Groq API request (OpenAI-compatible)
            payload = {
                "model": "llama3-8b-8192",  # Fast Llama model
                "messages": [
                    {"role": "system", "content": "You are a fast and efficient constitutional AI policy evaluator."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": min(request.context.get("max_tokens", 2048), self.capabilities.max_tokens),
                "temperature": 0.1,
                "response_format": {"type": "json_object"} if self.capabilities.supports_json_mode else None
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Make API request
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=request.timeout_seconds
            )

            execution_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                return self._parse_groq_response(request, result, execution_time)
            else:
                return EvaluationResponse(
                    request_id=request.request_id,
                    platform_type=self.platform_type,
                    success=False,
                    execution_time_ms=execution_time,
                    error_message=f"Groq API error: {response.status_code}",
                    error_code=str(response.status_code)
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=False,
                execution_time_ms=execution_time,
                error_message=str(e),
                error_code="ADAPTER_ERROR"
            )

    def _build_constitutional_prompt(self, request: EvaluationRequest) -> str:
        """Build Groq-optimized constitutional evaluation prompt."""
        return f"""
Evaluate the following policy for constitutional compliance and safety. Provide a fast, accurate assessment.

Policy Content:
{request.policy_content}

Evaluation Criteria:
{json.dumps(request.evaluation_criteria, indent=2)}

Please provide a JSON response with the following structure:
{{
    "policy_compliance_score": <float 0-1>,
    "constitutional_alignment": <float 0-1>,
    "safety_score": <float 0-1>,
    "fairness_score": <float 0-1>,
    "analysis": "<concise analysis>",
    "recommendations": ["<recommendation1>", "<recommendation2>"]
}}
"""

    def _parse_groq_response(self, request: EvaluationRequest, result: Dict[str, Any], execution_time: float) -> EvaluationResponse:
        """Parse Groq API response into standardized format."""
        try:
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            # Try to parse JSON response
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError:
                # Fallback to default scores if JSON parsing fails
                parsed_content = {
                    "policy_compliance_score": 0.5,
                    "constitutional_alignment": 0.5,
                    "safety_score": 0.5,
                    "fairness_score": 0.5,
                    "analysis": content,
                    "recommendations": []
                }

            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=True,
                policy_compliance_score=parsed_content.get("policy_compliance_score", 0.5),
                constitutional_alignment=parsed_content.get("constitutional_alignment", 0.5),
                safety_score=parsed_content.get("safety_score", 0.5),
                fairness_score=parsed_content.get("fairness_score", 0.5),
                execution_time_ms=execution_time,
                tokens_used=usage.get("total_tokens", 0),
                cost_estimate=usage.get("total_tokens", 0) * self.capabilities.cost_per_1k_tokens / 1000,
                platform_specific_metrics={
                    "model": "llama3-8b-8192",
                    "analysis": parsed_content.get("analysis", ""),
                    "recommendations": parsed_content.get("recommendations", []),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "inference_speed": "ultra_fast"
                }
            )

        except Exception as e:
            return EvaluationResponse(
                request_id=request.request_id,
                platform_type=self.platform_type,
                success=False,
                execution_time_ms=execution_time,
                error_message=f"Failed to parse Groq response: {e}",
                error_code="PARSE_ERROR"
            )
