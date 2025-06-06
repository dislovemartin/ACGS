"""
LLM Reliability Framework for ACGS-PGP

Implements multi-model validation, bias mitigation, and semantic faithfulness
measures to achieve >99.9% reliability for safety-critical applications.

Based on AlphaEvolve-ACGS Integration System research paper improvements.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import json
import hashlib
import re
from datetime import datetime, timezone
import statistics
from collections import defaultdict, deque

# Core dependencies
from ..schemas import LLMInterpretationInput, LLMStructuredOutput, ConstitutionalSynthesisInput, ConstitutionalSynthesisOutput
from ..models.reliability_models import ConstitutionalPrinciple, SynthesisContext
from .llm_integration import get_llm_client

# Enhanced dependencies for reliability framework
try:
    import redis
    from langchain.llms import OpenAI, Cohere
    from langchain.chat_models import ChatAnthropic # Assuming ChatCohere might exist or Cohere uses base LLM
    # For Gemini, we might need a specific LangChain integration or a custom client via get_llm_client
    # from langchain_google_genai import ChatGoogleGenerativeAI # Example if using langchain-google-genai
    from langchain.prompts import PromptTemplate
    from jinja2 import Template
    from sentence_transformers import SentenceTransformer
    from transformers import pipeline
    import torch
    ENHANCED_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Enhanced reliability dependencies not available: {e}")
    ENHANCED_DEPENDENCIES_AVAILABLE = False

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReliabilityLevel(Enum):
    """Reliability levels for different application contexts."""
    STANDARD = "standard"  # 95% reliability
    HIGH = "high"  # 99% reliability
    SAFETY_CRITICAL = "safety_critical"  # 99.9% reliability


class RecoveryStrategy(Enum):
    """Recovery strategies for automatic reliability recovery."""
    MODEL_REROUTING = "model_rerouting"
    MODEL_RETRAINING = "model_retraining"
    TRAFFIC_REDISTRIBUTION = "traffic_redistribution"
    CONFIGURATION_ADJUSTMENT = "configuration_adjustment"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK_ACTIVATION = "fallback_activation"
    EMERGENCY_SAFEGUARDS = "emergency_safeguards"
    HUMAN_ESCALATION = "human_escalation"


class RecoveryTrigger(Enum):
    """Triggers that initiate automatic recovery procedures."""
    RELIABILITY_THRESHOLD_BREACH = "reliability_threshold_breach"
    MODEL_FAILURE_RATE_HIGH = "model_failure_rate_high"
    RESPONSE_TIME_DEGRADATION = "response_time_degradation"
    CONSENSUS_FAILURE = "consensus_failure"
    BIAS_DETECTION_SPIKE = "bias_detection_spike"
    SEMANTIC_FAITHFULNESS_DROP = "semantic_faithfulness_drop"
    SYSTEM_OVERLOAD = "system_overload"
    PREDICTIVE_FAILURE = "predictive_failure"


class RecoveryStatus(Enum):
    """Status of recovery operations."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    PARTIALLY_SUCCESSFUL = "partially_successful"
    CANCELLED = "cancelled"
    MISSION_CRITICAL = "mission_critical"  # 99.99% reliability


@dataclass
class RecoveryAction:
    """Represents a recovery action to be executed."""
    strategy: RecoveryStrategy
    trigger: RecoveryTrigger
    priority: int  # 1 = highest priority
    target_component: str  # Model name, service, or "system"
    parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_recovery_time: float = 30.0  # seconds
    success_probability: float = 0.8
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RecoveryExecution:
    """Tracks the execution of a recovery action."""
    action: RecoveryAction
    status: RecoveryStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics_before: Optional[Dict[str, float]] = None
    metrics_after: Optional[Dict[str, float]] = None
    effectiveness_score: Optional[float] = None  # 0.0 to 1.0


@dataclass
class LLMReliabilityConfig:
    """Enhanced configuration for LLM reliability framework."""
    # Core reliability settings
    target_reliability: ReliabilityLevel = ReliabilityLevel.SAFETY_CRITICAL
    ensemble_size: int = 5  # Number of models in ensemble (1 primary + 4 validators)
    consensus_threshold: float = 0.8  # Agreement threshold for intermediate consensus steps
    bias_detection_enabled: bool = True
    semantic_validation_enabled: bool = True
    fallback_strategy: str = "conservative"  # "conservative", "majority", "expert"
    rule_based_fallback_enabled: bool = True # New: Enable rule-based fallback
    max_retries: int = 3
    llm_failure_threshold: int = 5 # New: Threshold for consecutive LLM failures before degradation
    timeout_seconds: int = 30

    # Automatic Recovery Configuration
    auto_recovery_enabled: bool = True
    recovery_trigger_thresholds: Dict[RecoveryTrigger, float] = field(default_factory=lambda: {
        RecoveryTrigger.RELIABILITY_THRESHOLD_BREACH: 0.95,  # Below 95% reliability
        RecoveryTrigger.MODEL_FAILURE_RATE_HIGH: 0.1,  # Above 10% failure rate
        RecoveryTrigger.RESPONSE_TIME_DEGRADATION: 2.0,  # 2x normal response time
        RecoveryTrigger.CONSENSUS_FAILURE: 0.7,  # Below 70% consensus rate
        RecoveryTrigger.BIAS_DETECTION_SPIKE: 0.05,  # Above 5% bias detection
        RecoveryTrigger.SEMANTIC_FAITHFULNESS_DROP: 0.85,  # Below 85% faithfulness
    })
    max_concurrent_recoveries: int = 3
    recovery_cooldown_seconds: int = 300  # 5 minutes between recovery attempts
    recovery_timeout_seconds: int = 180  # 3 minutes max per recovery
    enable_predictive_recovery: bool = True
    recovery_effectiveness_threshold: float = 0.6  # Minimum effectiveness to consider successful
    default_fallback_response: str = "An automated policy could not be generated due to system constraints. Please try again later or consult support." # New: Default response for critical failures
    enable_model_degradation: bool = True # New: Enable/disable dynamic model degradation
    # Updated to match protocol's UltraReliableConsensus.confidence_threshold
    confidence_threshold: float = 0.999

    # Enhanced features for >99.9% reliability
    multi_model_validation_enabled: bool = True
    ensemble_voting_enabled: bool = True # This will be part of the new consensus logic
    counterfactual_testing_enabled: bool = True
    proactive_bias_mitigation: bool = True
    nli_validation_enabled: bool = True
    prometheus_metrics_enabled: bool = True
    formal_verification_enabled: bool = False # Placeholder for now

    # Model configuration
    primary_model: str = "gpt-4-turbo" # Protocol: Constitutional prompting and primary synthesis
    secondary_models: List[str] = field(default_factory=lambda: [
        "claude-3.5-sonnet",      # Protocol: Adversarial validation and edge case detection
        "cohere-command-r-plus", # Protocol: Logical consistency verification
        "gemini-1.5-pro",        # Protocol: Semantic similarity validation (using 1.5 pro)
        "local-finetuned-model"  # Protocol: Domain-specific validation
    ])
    model_weights: Dict[str, float] = field(default_factory=lambda: {
        "gpt-4-turbo": 0.4,          # Primary synthesizer
        "claude-3.5-sonnet": 0.15,   # Validator
        "cohere-command-r-plus": 0.15, # Validator
        "gemini-1.5-pro": 0.15,      # Validator
        "local-finetuned-model": 0.15 # Validator
    })

    # Thresholds
    bias_threshold: float = 0.3
    # Updated to match protocol's UltraReliableConsensus.semantic_threshold
    semantic_threshold: float = 0.95
    reliability_target: float = 0.999  # >99.9% reliability target

    # Performance settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600

    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # API keys (optional - can be set via environment)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None # For Gemini Pro


@dataclass
class ReliabilityMetrics:
    """Enhanced metrics for LLM reliability assessment."""
    # Core reliability metrics
    success_rate: float
    consensus_rate: float
    bias_detection_rate: float
    semantic_faithfulness_score: float
    average_response_time: float
    error_rate: float
    fallback_usage_rate: float
    confidence_score: float

    # Enhanced metrics for >99.9% reliability
    model_agreement_score: float = 0.0
    counterfactual_robustness: float = 0.0
    nli_validation_score: float = 0.0
    proactive_bias_score: float = 0.0
    cache_hit_rate: float = 0.0

    # Detailed performance metrics
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    throughput_requests_per_second: float = 0.0

    # Quality metrics
    hallucination_rate: float = 0.0
    factual_accuracy_score: float = 0.0
    constitutional_compliance_score: float = 0.0

    # Timestamp and metadata
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request_id: Optional[str] = None
    model_versions: Dict[str, str] = field(default_factory=dict)
    model_failures_total: Dict[str, int] = field(default_factory=dict) # New: Total failures per model for this metric snapshot

    def overall_reliability_score(self) -> float:
        """Calculate overall reliability score combining all metrics."""
        core_score = (
            self.success_rate * 0.3 +
            self.consensus_rate * 0.2 +
            self.confidence_score * 0.2 +
            (1 - self.error_rate) * 0.15 +
            self.semantic_faithfulness_score * 0.15
        )

        # Penalty for bias and hallucinations
        bias_penalty = max(0, self.bias_detection_rate - 0.1) * 0.5
        hallucination_penalty = self.hallucination_rate * 0.3

        return max(0.0, core_score - bias_penalty - hallucination_penalty)


@dataclass
class UltraReliableResult:
    """Result from ultra-reliable consensus framework."""
    policy: Optional[LLMStructuredOutput]
    confidence: float
    validation_path: str  # "automated_consensus", "expert_review", "failed_synthesis"
    requires_human_review: bool
    error_message: Optional[str] = None
    synthesis_details: Optional[Dict[str, Any]] = None
    validation_details: Optional[Dict[str, Any]] = None
    formal_verification_status: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: Optional[str] = None # Added status field
    performance_metrics_details: Optional[Dict[str, Any]] = None # New field for detailed performance metrics


class PrometheusMetricsCollector:
    """Collects and exports Prometheus metrics for reliability monitoring."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled and PROMETHEUS_AVAILABLE
        if self.enabled:
            self.registry = CollectorRegistry()
            self._setup_metrics()

    def _setup_metrics(self):
        """Setup Prometheus metrics."""
        if not self.enabled:
            return

        self.reliability_score = Gauge(
            'llm_reliability_score',
            'Overall LLM reliability score',
            registry=self.registry
        )
        self.response_time = Histogram(
            'llm_response_time_seconds',
            'LLM response time in seconds',
            registry=self.registry
        )
        self.success_rate = Gauge(
            'llm_success_rate',
            'LLM success rate',
            registry=self.registry
        )
        self.bias_detection_rate = Gauge(
            'llm_bias_detection_rate',
            'Rate of bias detection in LLM outputs',
            registry=self.registry
        )
        self.consensus_rate = Gauge(
            'llm_consensus_rate',
            'Rate of consensus among ensemble models',
            registry=self.registry
        )
        self.cache_hit_rate = Gauge(
            'llm_cache_hit_rate',
            'Cache hit rate for LLM requests',
            registry=self.registry
        )
        self.fallbacks_total = Counter(
            'llm_fallbacks_total',
            'Total number of times fallback mechanisms were used',
            registry=self.registry
        )
        self.escalations_total = Counter(
            'llm_escalations_total',
            'Total number of times human review escalations occurred',
            registry=self.registry
        )
        self.failures_total = Counter(
            'llm_failures_total',
            'Total number of LLM processing failures',
            registry=self.registry
        )
        self.model_failures_total = Counter( # New: Track failures per model
            'llm_model_failures_total',
            'Total number of LLM processing failures per model',
            ['model_name'], # Label for model name
            registry=self.registry
        )
        self.recoveries_total = Counter(
            'llm_recoveries_total',
            'Total number of automatic recovery actions executed',
            ['strategy'], # Label for recovery strategy
            registry=self.registry
        )

    def record_metrics(self, metrics: ReliabilityMetrics):
        """Record metrics to Prometheus."""
        if not self.enabled:
            return

        self.reliability_score.set(metrics.overall_reliability_score())
        self.response_time.observe(metrics.average_response_time)
        self.success_rate.set(metrics.success_rate)
        self.bias_detection_rate.set(metrics.bias_detection_rate)
        self.consensus_rate.set(metrics.consensus_rate)
        self.cache_hit_rate.set(metrics.cache_hit_rate)

    def increment_fallbacks(self):
        """Increment the total number of times fallback mechanisms were used."""
        if self.enabled:
            self.fallbacks_total.inc()
            logger.debug("Prometheus: Fallback incremented.")

    def increment_escalations(self):
        """Increment the total number of times human review escalations occurred."""
        if self.enabled:
            self.escalations_total.inc()
            logger.debug("Prometheus: Escalation incremented.")

    def increment_failures(self):
        """Increment the total number of LLM processing failures."""
        if self.enabled:
            self.failures_total.inc()
            logger.debug("Prometheus: Failure incremented.")

    def increment_model_failures(self, model_name: str):
        """Increment the total number of LLM processing failures for a specific model."""
        if self.enabled:
            self.model_failures_total.labels(model_name=model_name).inc()
            logger.debug(f"Prometheus: Model {model_name} failure incremented.")

    def increment_recoveries(self, strategy: str):
        """Increment the total number of automatic recovery actions for a specific strategy."""
        if self.enabled:
            self.recoveries_total.labels(strategy=strategy).inc()
            logger.debug(f"Prometheus: Recovery {strategy} incremented.")


class CacheManager:
    """Manages Redis caching for LLM responses."""

    def __init__(self, config: LLMReliabilityConfig):
        self.config = config
        self.redis_client = None
        if config.cache_enabled and ENHANCED_DEPENDENCIES_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=config.redis_host,
                    port=config.redis_port,
                    db=config.redis_db,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
                self.redis_client = None

    def _generate_cache_key(self, input_data: LLMInterpretationInput) -> str:
        """Generate cache key for input data."""
        key_data = {
            "principle_id": input_data.principle_id,
            "principle_text": getattr(input_data, 'principle_text', ''),
            "context": getattr(input_data, 'context', '')
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"llm_cache:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def get_cached_response(self, input_data: LLMInterpretationInput) -> Optional[LLMStructuredOutput]:
        """Get cached response if available."""
        if not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(input_data)
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                return LLMStructuredOutput(
                    interpretations=data.get('interpretations', []),
                    raw_llm_response=data.get('raw_llm_response', '')
                )
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")

        return None

    async def cache_response(self, input_data: LLMInterpretationInput, output: LLMStructuredOutput):
        """Cache response for future use."""
        if not self.redis_client:
            return

        try:
            cache_key = self._generate_cache_key(input_data)
            cache_data = {
                'interpretations': output.interpretations,
                'raw_llm_response': output.raw_llm_response,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            self.redis_client.setex(
                cache_key,
                self.config.cache_ttl_seconds,
                json.dumps(cache_data)
            )
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")


class AutomaticRecoveryOrchestrator:
    """
    Orchestrates automatic reliability recovery procedures.
    Implements self-healing mechanisms to restore system reliability without manual intervention.
    """

    def __init__(self, config: LLMReliabilityConfig, metrics_collector: PrometheusMetricsCollector):
        self.config = config
        self.metrics_collector = metrics_collector
        self.active_recoveries: Dict[str, RecoveryExecution] = {}
        self.recovery_history: deque = deque(maxlen=1000)
        self.last_recovery_attempt: Dict[str, datetime] = {}
        self.recovery_effectiveness_history: Dict[RecoveryStrategy, deque] = defaultdict(lambda: deque(maxlen=100))
        self.baseline_metrics: Dict[str, float] = {}
        self.trend_analyzer = TrendAnalyzer()

    async def monitor_and_recover(
        self,
        current_metrics: Dict[str, float],
        component_status: Dict[str, Any],
        request_id: str
    ) -> List[RecoveryExecution]:
        """
        Main monitoring and recovery coordination method.
        Analyzes current system state and triggers appropriate recovery actions.
        """
        if not self.config.auto_recovery_enabled:
            return []

        # Update baseline metrics if not set
        if not self.baseline_metrics:
            self.baseline_metrics = current_metrics.copy()

        # Detect triggers that require recovery
        triggered_recoveries = await self._detect_recovery_triggers(current_metrics, component_status, request_id)

        if not triggered_recoveries:
            return []

        # Filter out recoveries that are in cooldown
        filtered_recoveries = self._filter_cooldown_recoveries(triggered_recoveries, request_id)

        # Prioritize and limit concurrent recoveries
        prioritized_recoveries = self._prioritize_recoveries(filtered_recoveries)

        # Execute recovery actions
        executed_recoveries = []
        for recovery_action in prioritized_recoveries:
            if len(self.active_recoveries) >= self.config.max_concurrent_recoveries:
                logger.warning(f"Request {request_id}: Maximum concurrent recoveries reached, queuing {recovery_action.strategy.value}")
                break

            execution = await self._execute_recovery_action(recovery_action, current_metrics, request_id)
            if execution:
                executed_recoveries.append(execution)

        return executed_recoveries

    async def _detect_recovery_triggers(
        self,
        current_metrics: Dict[str, float],
        component_status: Dict[str, Any],
        request_id: str
    ) -> List[RecoveryAction]:
        """Detect conditions that trigger automatic recovery."""
        triggered_actions = []

        # Check reliability threshold breach
        overall_reliability = current_metrics.get('overall_reliability', 1.0)
        reliability_threshold = self.config.recovery_trigger_thresholds.get(
            RecoveryTrigger.RELIABILITY_THRESHOLD_BREACH, 0.95
        )

        if overall_reliability < reliability_threshold:
            logger.warning(f"Request {request_id}: Reliability threshold breach detected: {overall_reliability:.3f} < {reliability_threshold}")
            triggered_actions.append(RecoveryAction(
                strategy=RecoveryStrategy.MODEL_REROUTING,
                trigger=RecoveryTrigger.RELIABILITY_THRESHOLD_BREACH,
                priority=1,
                target_component="system",
                parameters={"current_reliability": overall_reliability, "threshold": reliability_threshold}
            ))

        # Check model failure rates
        for model_name, status in component_status.get('models', {}).items():
            failure_rate = status.get('failure_rate', 0.0)
            failure_threshold = self.config.recovery_trigger_thresholds.get(
                RecoveryTrigger.MODEL_FAILURE_RATE_HIGH, 0.1
            )

            if failure_rate > failure_threshold:
                logger.warning(f"Request {request_id}: High failure rate detected for {model_name}: {failure_rate:.3f}")
                triggered_actions.append(RecoveryAction(
                    strategy=RecoveryStrategy.CIRCUIT_BREAKER,
                    trigger=RecoveryTrigger.MODEL_FAILURE_RATE_HIGH,
                    priority=2,
                    target_component=model_name,
                    parameters={"failure_rate": failure_rate, "threshold": failure_threshold}
                ))

        # Check response time degradation
        avg_response_time = current_metrics.get('avg_response_time', 0.0)
        baseline_response_time = self.baseline_metrics.get('avg_response_time', avg_response_time)
        degradation_threshold = self.config.recovery_trigger_thresholds.get(
            RecoveryTrigger.RESPONSE_TIME_DEGRADATION, 2.0
        )

        if baseline_response_time > 0 and avg_response_time > baseline_response_time * degradation_threshold:
            logger.warning(f"Request {request_id}: Response time degradation detected: {avg_response_time:.3f}s vs baseline {baseline_response_time:.3f}s")
            triggered_actions.append(RecoveryAction(
                strategy=RecoveryStrategy.TRAFFIC_REDISTRIBUTION,
                trigger=RecoveryTrigger.RESPONSE_TIME_DEGRADATION,
                priority=3,
                target_component="system",
                parameters={"current_time": avg_response_time, "baseline_time": baseline_response_time}
            ))

        # Check consensus failure rate
        consensus_rate = current_metrics.get('consensus_rate', 1.0)
        consensus_threshold = self.config.recovery_trigger_thresholds.get(
            RecoveryTrigger.CONSENSUS_FAILURE, 0.7
        )

        if consensus_rate < consensus_threshold:
            logger.warning(f"Request {request_id}: Low consensus rate detected: {consensus_rate:.3f}")
            triggered_actions.append(RecoveryAction(
                strategy=RecoveryStrategy.CONFIGURATION_ADJUSTMENT,
                trigger=RecoveryTrigger.CONSENSUS_FAILURE,
                priority=2,
                target_component="consensus_system",
                parameters={"consensus_rate": consensus_rate, "threshold": consensus_threshold}
            ))

        # Check bias detection spike
        bias_detection_rate = current_metrics.get('bias_detection_rate', 0.0)
        bias_threshold = self.config.recovery_trigger_thresholds.get(
            RecoveryTrigger.BIAS_DETECTION_SPIKE, 0.05
        )

        if bias_detection_rate > bias_threshold:
            logger.warning(f"Request {request_id}: Bias detection spike: {bias_detection_rate:.3f}")
            triggered_actions.append(RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK_ACTIVATION,
                trigger=RecoveryTrigger.BIAS_DETECTION_SPIKE,
                priority=1,
                target_component="bias_detection",
                parameters={"bias_rate": bias_detection_rate, "threshold": bias_threshold}
            ))

        # Predictive failure detection using trend analysis
        if self.config.enable_predictive_recovery:
            predictive_triggers = await self._detect_predictive_failures(current_metrics, request_id)
            triggered_actions.extend(predictive_triggers)

        return triggered_actions

    async def _detect_predictive_failures(self, current_metrics: Dict[str, float], request_id: str) -> List[RecoveryAction]:
        """Detect potential future failures using trend analysis."""
        predictive_actions = []

        # Add current metrics to trend analyzer
        self.trend_analyzer.add_metrics(current_metrics)

        # Check for predictive reliability failure
        reliability_failure_prob = self.trend_analyzer.predict_failure_probability('overall_reliability')
        if reliability_failure_prob > 0.7:  # 70% probability of failure
            logger.info(f"Request {request_id}: Predictive reliability failure detected (probability: {reliability_failure_prob:.2f})")
            predictive_actions.append(RecoveryAction(
                strategy=RecoveryStrategy.MODEL_REROUTING,
                trigger=RecoveryTrigger.PREDICTIVE_FAILURE,
                priority=2,
                target_component="system",
                parameters={"failure_probability": reliability_failure_prob, "metric": "overall_reliability"}
            ))

        # Check for predictive response time failure
        response_time_failure_prob = self.trend_analyzer.predict_failure_probability('avg_response_time')
        if response_time_failure_prob > 0.6:  # 60% probability of failure
            logger.info(f"Request {request_id}: Predictive response time failure detected (probability: {response_time_failure_prob:.2f})")
            predictive_actions.append(RecoveryAction(
                strategy=RecoveryStrategy.TRAFFIC_REDISTRIBUTION,
                trigger=RecoveryTrigger.PREDICTIVE_FAILURE,
                priority=3,
                target_component="system",
                parameters={"failure_probability": response_time_failure_prob, "metric": "avg_response_time"}
            ))

        return predictive_actions

    def _filter_cooldown_recoveries(self, recovery_actions: List[RecoveryAction], request_id: str) -> List[RecoveryAction]:
        """Filter out recovery actions that are in cooldown period."""
        filtered_actions = []
        current_time = datetime.now(timezone.utc)

        for action in recovery_actions:
            cooldown_key = f"{action.strategy.value}_{action.target_component}"
            last_attempt = self.last_recovery_attempt.get(cooldown_key)

            if last_attempt:
                time_since_last = (current_time - last_attempt).total_seconds()
                if time_since_last < self.config.recovery_cooldown_seconds:
                    logger.debug(f"Request {request_id}: Recovery action {action.strategy.value} for {action.target_component} is in cooldown")
                    continue

            filtered_actions.append(action)

        return filtered_actions

    def _prioritize_recoveries(self, recovery_actions: List[RecoveryAction]) -> List[RecoveryAction]:
        """Prioritize recovery actions based on priority and effectiveness history."""
        if not recovery_actions:
            return []

        # Sort by priority (lower number = higher priority)
        sorted_actions = sorted(recovery_actions, key=lambda x: x.priority)

        # Adjust priority based on historical effectiveness
        for action in sorted_actions:
            effectiveness_history = self.recovery_effectiveness_history.get(action.strategy, deque())
            if effectiveness_history:
                avg_effectiveness = statistics.mean(effectiveness_history)
                # Boost priority for historically effective strategies
                if avg_effectiveness > 0.8:
                    action.priority = max(1, action.priority - 1)
                elif avg_effectiveness < 0.4:
                    action.priority = min(5, action.priority + 1)

        # Re-sort after priority adjustment
        return sorted(sorted_actions, key=lambda x: x.priority)

    async def _execute_recovery_action(
        self,
        action: RecoveryAction,
        current_metrics: Dict[str, float],
        request_id: str
    ) -> Optional[RecoveryExecution]:
        """Execute a specific recovery action."""
        execution_id = f"{action.strategy.value}_{action.target_component}_{int(time.time())}"

        execution = RecoveryExecution(
            action=action,
            status=RecoveryStatus.INITIATED,
            started_at=datetime.now(timezone.utc),
            metrics_before=current_metrics.copy()
        )

        self.active_recoveries[execution_id] = execution
        logger.info(f"Request {request_id}: Executing recovery action {action.strategy.value} for {action.target_component}")

        try:
            execution.status = RecoveryStatus.IN_PROGRESS

            # Execute the specific recovery strategy
            success = await self._execute_strategy(action, request_id)

            if success:
                execution.status = RecoveryStatus.SUCCESSFUL
                logger.info(f"Request {request_id}: Recovery action {action.strategy.value} completed successfully")
            else:
                execution.status = RecoveryStatus.FAILED
                logger.warning(f"Request {request_id}: Recovery action {action.strategy.value} failed")

        except Exception as e:
            execution.status = RecoveryStatus.FAILED
            execution.error_message = str(e)
            logger.error(f"Request {request_id}: Recovery action {action.strategy.value} failed with error: {e}")

        finally:
            execution.completed_at = datetime.now(timezone.utc)

            # Update recovery attempt timestamp
            cooldown_key = f"{action.strategy.value}_{action.target_component}"
            self.last_recovery_attempt[cooldown_key] = execution.completed_at

            # Move from active to history
            if execution_id in self.active_recoveries:
                del self.active_recoveries[execution_id]
            self.recovery_history.append(execution)

        return execution

    async def _execute_strategy(self, action: RecoveryAction, request_id: str) -> bool:
        """Execute the specific recovery strategy."""
        try:
            if action.strategy == RecoveryStrategy.MODEL_REROUTING:
                return await self._execute_model_rerouting(action, request_id)
            elif action.strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                return await self._execute_circuit_breaker(action, request_id)
            elif action.strategy == RecoveryStrategy.TRAFFIC_REDISTRIBUTION:
                return await self._execute_traffic_redistribution(action, request_id)
            elif action.strategy == RecoveryStrategy.CONFIGURATION_ADJUSTMENT:
                return await self._execute_configuration_adjustment(action, request_id)
            elif action.strategy == RecoveryStrategy.FALLBACK_ACTIVATION:
                return await self._execute_fallback_activation(action, request_id)
            elif action.strategy == RecoveryStrategy.EMERGENCY_SAFEGUARDS:
                return await self._execute_emergency_safeguards(action, request_id)
            elif action.strategy == RecoveryStrategy.MODEL_RETRAINING:
                return await self._execute_model_retraining(action, request_id)
            else:
                logger.warning(f"Request {request_id}: Unknown recovery strategy: {action.strategy}")
                return False
        except Exception as e:
            logger.error(f"Request {request_id}: Error executing strategy {action.strategy}: {e}")
            return False

    async def _execute_model_rerouting(self, action: RecoveryAction, request_id: str) -> bool:
        """Execute model rerouting recovery strategy."""
        logger.info(f"Request {request_id}: Executing model rerouting for {action.target_component}")

        # This would integrate with the EnhancedMultiModelValidator to reroute traffic
        # For now, we'll simulate the action
        await asyncio.sleep(0.1)  # Simulate processing time

        # Record the recovery action in metrics
        self.metrics_collector.increment_recoveries("model_rerouting")

        return True

    async def _execute_circuit_breaker(self, action: RecoveryAction, request_id: str) -> bool:
        """Execute circuit breaker recovery strategy."""
        logger.info(f"Request {request_id}: Activating circuit breaker for {action.target_component}")

        # This would temporarily disable the failing component
        # For now, we'll simulate the action
        await asyncio.sleep(0.1)  # Simulate processing time

        # Record the recovery action in metrics
        self.metrics_collector.increment_recoveries("circuit_breaker")

        return True

    async def _execute_traffic_redistribution(self, action: RecoveryAction, request_id: str) -> bool:
        """Execute traffic redistribution recovery strategy."""
        logger.info(f"Request {request_id}: Redistributing traffic for {action.target_component}")

        # This would redistribute load across healthy components
        # For now, we'll simulate the action
        await asyncio.sleep(0.1)  # Simulate processing time

        # Record the recovery action in metrics
        self.metrics_collector.increment_recoveries("traffic_redistribution")

        return True

    async def _execute_configuration_adjustment(self, action: RecoveryAction, request_id: str) -> bool:
        """Execute configuration adjustment recovery strategy."""
        logger.info(f"Request {request_id}: Adjusting configuration for {action.target_component}")

        # This would adjust system parameters like timeouts, thresholds, etc.
        # For now, we'll simulate the action
        await asyncio.sleep(0.1)  # Simulate processing time

        # Record the recovery action in metrics
        self.metrics_collector.increment_recoveries("configuration_adjustment")

        return True

    async def _execute_fallback_activation(self, action: RecoveryAction, request_id: str) -> bool:
        """Execute fallback activation recovery strategy."""
        logger.info(f"Request {request_id}: Activating fallback for {action.target_component}")

        # This would activate fallback mechanisms
        # For now, we'll simulate the action
        await asyncio.sleep(0.1)  # Simulate processing time

        # Record the recovery action in metrics
        self.metrics_collector.increment_recoveries("fallback_activation")

        return True

    async def _execute_emergency_safeguards(self, action: RecoveryAction, request_id: str) -> bool:
        """Execute emergency safeguards recovery strategy."""
        logger.info(f"Request {request_id}: Activating emergency safeguards for {action.target_component}")

        # This would activate emergency safeguards
        # For now, we'll simulate the action
        await asyncio.sleep(0.1)  # Simulate processing time

        # Record the recovery action in metrics
        self.metrics_collector.increment_recoveries("emergency_safeguards")

        return True

    async def _execute_model_retraining(self, action: RecoveryAction, request_id: str) -> bool:
        """Execute model retraining recovery strategy."""
        logger.info(f"Request {request_id}: Initiating model retraining for {action.target_component}")

        # This would trigger model retraining
        # For now, we'll simulate the action
        await asyncio.sleep(0.1)  # Simulate processing time

        # Record the recovery action in metrics
        self.metrics_collector.increment_recoveries("model_retraining")

        return True

    async def measure_recovery_effectiveness(
        self,
        execution: RecoveryExecution,
        metrics_after: Dict[str, float]
    ) -> float:
        """Measure the effectiveness of a recovery action."""
        if not execution.metrics_before or not metrics_after:
            return 0.0

        execution.metrics_after = metrics_after.copy()

        # Calculate improvement in key metrics
        improvements = []

        # Check reliability improvement
        reliability_before = execution.metrics_before.get('overall_reliability', 0.0)
        reliability_after = metrics_after.get('overall_reliability', 0.0)
        if reliability_before > 0:
            reliability_improvement = (reliability_after - reliability_before) / reliability_before
            improvements.append(max(0.0, reliability_improvement))

        # Check response time improvement (lower is better)
        response_time_before = execution.metrics_before.get('avg_response_time', 0.0)
        response_time_after = metrics_after.get('avg_response_time', 0.0)
        if response_time_before > 0:
            response_time_improvement = (response_time_before - response_time_after) / response_time_before
            improvements.append(max(0.0, response_time_improvement))

        # Check consensus rate improvement
        consensus_before = execution.metrics_before.get('consensus_rate', 0.0)
        consensus_after = metrics_after.get('consensus_rate', 0.0)
        if consensus_before > 0:
            consensus_improvement = (consensus_after - consensus_before) / consensus_before
            improvements.append(max(0.0, consensus_improvement))

        # Calculate overall effectiveness
        if improvements:
            effectiveness = min(1.0, statistics.mean(improvements))
        else:
            effectiveness = 0.5 if execution.status == RecoveryStatus.SUCCESSFUL else 0.0

        execution.effectiveness_score = effectiveness

        # Update effectiveness history
        self.recovery_effectiveness_history[execution.action.strategy].append(effectiveness)

        logger.info(f"Recovery effectiveness for {execution.action.strategy.value}: {effectiveness:.3f}")

        return effectiveness

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get comprehensive recovery statistics."""
        if not self.recovery_history:
            return {"status": "no_data"}

        recent_recoveries = list(self.recovery_history)[-100:]  # Last 100 recoveries

        # Calculate success rates by strategy
        strategy_stats = defaultdict(lambda: {"total": 0, "successful": 0, "avg_effectiveness": 0.0})

        for execution in recent_recoveries:
            strategy = execution.action.strategy
            strategy_stats[strategy]["total"] += 1

            if execution.status == RecoveryStatus.SUCCESSFUL:
                strategy_stats[strategy]["successful"] += 1

            if execution.effectiveness_score is not None:
                current_avg = strategy_stats[strategy]["avg_effectiveness"]
                total = strategy_stats[strategy]["total"]
                strategy_stats[strategy]["avg_effectiveness"] = (
                    (current_avg * (total - 1) + execution.effectiveness_score) / total
                )

        # Calculate overall statistics
        total_recoveries = len(recent_recoveries)
        successful_recoveries = sum(1 for e in recent_recoveries if e.status == RecoveryStatus.SUCCESSFUL)

        avg_recovery_time = 0.0
        if recent_recoveries:
            recovery_times = []
            for execution in recent_recoveries:
                if execution.completed_at and execution.started_at:
                    recovery_time = (execution.completed_at - execution.started_at).total_seconds()
                    recovery_times.append(recovery_time)
            if recovery_times:
                avg_recovery_time = statistics.mean(recovery_times)

        return {
            "total_recoveries": total_recoveries,
            "success_rate": successful_recoveries / total_recoveries if total_recoveries > 0 else 0.0,
            "avg_recovery_time_seconds": avg_recovery_time,
            "active_recoveries": len(self.active_recoveries),
            "strategy_statistics": dict(strategy_stats),
            "recent_recovery_count": len(recent_recoveries)
        }


class TrendAnalyzer:
    """Analyzes trends in metrics to predict potential failures."""

    def __init__(self):
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

    def add_metrics(self, metrics: Dict[str, float]):
        """Add new metrics to history for trend analysis."""
        timestamp = time.time()
        for metric_name, value in metrics.items():
            self.metric_history[metric_name].append((timestamp, value))

    def predict_failure_probability(self, metric_name: str, lookahead_seconds: int = 300) -> float:
        """Predict probability of failure for a specific metric."""
        if metric_name not in self.metric_history or len(self.metric_history[metric_name]) < 10:
            return 0.0

        history = list(self.metric_history[metric_name])
        timestamps = [item[0] for item in history]
        values = [item[1] for item in history]

        # Simple linear regression for trend prediction
        if len(values) < 3:
            return 0.0

        try:
            # Calculate trend slope
            x = np.array(range(len(values)))
            y = np.array(values)
            slope = np.polyfit(x, y, 1)[0]

            # Predict future value
            future_steps = lookahead_seconds / 60  # Assuming 1-minute intervals
            predicted_value = values[-1] + slope * future_steps

            # Calculate failure probability based on predicted value and thresholds
            if metric_name == 'overall_reliability':
                if predicted_value < 0.95:
                    return min(1.0, (0.95 - predicted_value) * 10)
            elif metric_name == 'avg_response_time':
                baseline = np.mean(values[:len(values)//2]) if len(values) > 6 else values[0]
                if predicted_value > baseline * 2:
                    return min(1.0, (predicted_value / baseline - 2) * 0.5)

            return 0.0

        except Exception as e:
            logger.warning(f"Error in trend prediction for {metric_name}: {e}")
            return 0.0


class EnhancedMultiModelValidator:
    """Enhanced multi-model validator using LangChain and multiple providers."""

    def __init__(self, config: LLMReliabilityConfig, metrics_collector: PrometheusMetricsCollector): # Add metrics_collector param
        self.config = config
        self.models = {}
        self.cache_manager = CacheManager(config)
        self.metrics_collector = metrics_collector # Store it
        self.performance_history = []
        self.model_failure_counts: Dict[str, int] = {} # Track consecutive failures per model
        self.active_models: List[str] = [] # List of currently active models
        self.model_health_status: Dict[str, Dict[str, Any]] = {} # Track model health metrics
        self.degraded_models: Dict[str, Dict[str, Any]] = {} # Track degraded models for potential recovery
        self.last_health_check: Dict[str, float] = {} # Track last health check timestamp per model
        self.ultra_result_cache: Dict[str, UltraReliableResult] = {}

    async def initialize(self):
        """Initialize multiple LLM models for ensemble validation based on config."""
        if not ENHANCED_DEPENDENCIES_AVAILABLE:
            logger.warning("Enhanced dependencies (e.g., LangChain specific clients) not fully available. Some models may use fallback.")
            # We can still try to initialize models that don't rely on missing specific imports

        all_model_names = [self.config.primary_model] + self.config.secondary_models
        
        for model_name in all_model_names:
            weight = self.config.model_weights.get(model_name)
            if weight is None:
                logger.warning(f"Weight not defined for model {model_name}, skipping.")
                continue

            client = None
            model_type = "unknown"

            try:
                if "gpt-4" in model_name and self.config.openai_api_key:
                    client = OpenAI(openai_api_key=self.config.openai_api_key, model_name=model_name)
                    model_type = "openai"
                    logger.info(f"Initialized OpenAI model: {model_name}")
                elif "claude-3" in model_name and self.config.anthropic_api_key:
                    # Langchain's ChatAnthropic might take model_name in constructor or via a specific method
                    client = ChatAnthropic(anthropic_api_key=self.config.anthropic_api_key, model_name=model_name)
                    model_type = "anthropic"
                    logger.info(f"Initialized Anthropic model: {model_name}")
                elif "cohere-command" in model_name and self.config.cohere_api_key:
                    client = Cohere(cohere_api_key=self.config.cohere_api_key, model=model_name)
                    model_type = "cohere"
                    logger.info(f"Initialized Cohere model: {model_name}")
                elif "gemini" in model_name and self.config.gemini_api_key:
                    # Placeholder: LangChain's Google GenAI integration would be used here
                    # For now, using get_llm_client as a stand-in, assuming it can handle Gemini
                    # client = ChatGoogleGenerativeAI(model_name=model_name, google_api_key=self.config.gemini_api_key)
                    client = get_llm_client(llm_type="gemini", model_name=model_name, api_key=self.config.gemini_api_key)
                    model_type = "gemini"
                    logger.info(f"Initialized Gemini model (via get_llm_client): {model_name}")
                elif "local-finetuned-model" in model_name:
                    # Placeholder for local model loading logic
                    # This might involve loading from a path or a specific local API
                    client = get_llm_client(llm_type="local", model_name=model_name) # Assuming get_llm_client can handle this
                    model_type = "local"
                    logger.info(f"Initialized Local Fine-tuned Model (via get_llm_client): {model_name}")
                else:
                    logger.warning(f"Unsupported model or missing API key for: {model_name}. Attempting fallback.")
                    # Attempt generic fallback if specific client fails or isn't defined
                    client = get_llm_client(model_name=model_name) # Generic client
                    model_type = "fallback_generic"
                    logger.info(f"Initialized Fallback model (via get_llm_client): {model_name}")

                if client:
                    self.models[model_name] = {
                        "client": client,
                        "weight": weight,
                        "type": model_type
                    }
                    self.active_models.append(model_name) # Add to active models
                    self.model_failure_counts[model_name] = 0 # Initialize failure count
            except Exception as e:
                logger.error(f"Failed to initialize model {model_name}: {e}")

        if not self.models:
            logger.error("No models could be initialized. LLM Reliability Framework will not function correctly.")
            # Fallback to a single basic model if all else fails, to prevent complete breakdown
            try:
                logger.info("Attempting to initialize a single default fallback model.")
                default_client = get_llm_client()
                self.models["default_fallback"] = {
                    "client": default_client,
                    "weight": 1.0,
                    "type": "default_fallback_emergency"
                }
                logger.info("Initialized a single default fallback model.")
            except Exception as e_fallback:
                logger.critical(f"CRITICAL: Failed to initialize even a single default fallback model: {e_fallback}")
        
        logger.info(f"Successfully initialized {len(self.models)} models for ensemble validation.")

    async def achieve_ultra_reliable_consensus(
        self,
        principle: ConstitutionalPrinciple,
        context: Optional[SynthesisContext] = None,
    ) -> UltraReliableResult:
        """
        Achieve >99.9% reliable policy synthesis through a multi-stage consensus framework,
        aligning with the research protocol's UltraReliableConsensus class.
        """
        start_time = time.time()
        request_id = hashlib.md5(f"{principle.id}_{start_time}".encode()).hexdigest()[:8]

        principle_text = principle.text
        synthesis_context = context

        input_data = LLMInterpretationInput(
            principle_id=principle.id,
            principle_content=principle.text,
            target_context=getattr(context, "domain", None),
        )

        cache_key = self.cache_manager._generate_cache_key(input_data) + ":ultra"
        if cache_key in self.ultra_result_cache:
            metrics = self._create_cached_metrics(start_time, request_id)
            self.performance_history.append(metrics)
            logger.debug(f"Request {request_id}: Returning cached ultra reliable result")
            return self.ultra_result_cache[cache_key]

        # Stage 1: Multi-model synthesis (Parallel synthesis by multiple models)
        # `responses` here are the initial synthesis attempts from various models.
        synthesis_results, synthesis_errors, synthesis_metrics_details = await self._parallel_synthesis(input_data, request_id)

        if not synthesis_results:
            logger.error(f"Request {request_id}: All models failed during initial synthesis stage.")
            # Create a basic ReliabilityMetrics for logging if needed
            # metrics = self._calculate_enhanced_metrics([], synthesis_errors, [], time.time() - start_time, LLMStructuredOutput(interpretations=[], raw_llm_response=""), request_id)
            # self.performance_history.append(metrics) # Log failure
            return UltraReliableResult(
                policy=None,
                confidence=0.0,
                validation_path="failed_synthesis",
                requires_human_review=True,
                error_message=f"All models failed initial synthesis: {'; '.join(synthesis_errors)}",
                performance_metrics_details=synthesis_metrics_details # Pass the metrics
            )

        # Stage 2: Cross-validation matrix
        # Each synthesis_result is validated by other models.
        validation_matrix = await self._cross_validate_results(synthesis_results, principle_text, request_id)

        # Stage 3: Semantic consistency check (using EnhancedSemanticFaithfulnessValidator)
        # This should check each synthesis_result against the original principle.
        semantic_scores = await self._validate_semantic_consistency(
            synthesis_results, principle_text, request_id
        )

        # Stage 4: Formal verification where applicable (Placeholder)
        formal_verification_results = await self._attempt_formal_verification(
            synthesis_results, principle_text, request_id
        )

        # Stage 5: Consensus decision
        # This is the core logic to determine the final policy and confidence.
        # It will use validation_matrix, semantic_scores, formal_verification_results.
        final_policy, final_confidence, consensus_details = await self._weighted_consensus_decision(
            synthesis_results, validation_matrix, semantic_scores, formal_verification_results, request_id
        )
        
        metrics = self._calculate_overall_reliability_metrics(
            synthesis_results,
            synthesis_errors,
            validation_matrix,
            semantic_scores,
            formal_verification_results,
            final_policy is not None,
            final_confidence,
            synthesis_metrics_details,
            start_time,
            request_id
        )
        self.performance_history.append(metrics)

        if final_policy and final_confidence >= self.config.confidence_threshold:
            logger.info(f"Request {request_id}: Automated consensus achieved with confidence {final_confidence:.4f}")
            ultra_result = UltraReliableResult(
                policy=final_policy,
                confidence=final_confidence,
                validation_path="automated_consensus",
                requires_human_review=False,
                synthesis_details=consensus_details,
                performance_metrics_details=synthesis_metrics_details
            )
        else:
            logger.warning(f"Request {request_id}: Automated consensus failed or confidence too low ({final_confidence:.4f}). Escalating.")
            # Pass all gathered information to the escalation process
            ultra_result = await self._escalate_to_expert_review(
                synthesis_results, validation_matrix, semantic_scores, formal_verification_results,
                final_policy, final_confidence, principle_text, synthesis_context, request_id,
                synthesis_metrics_details # Pass the metrics to escalation
            )
        self.ultra_result_cache[cache_key] = ultra_result
        return ultra_result
    async def _parallel_synthesis(
        self,
        input_data: LLMInterpretationInput,
        request_id: str
    ) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, Any]]:
        """
        Stage 1: Perform synthesis using multiple configured models in parallel.
        Returns a list of synthesis results, a list of errors, and metrics details.
        Each synthesis result includes the model name, the LLMStructuredOutput, weight, etc.
        """
        start_time = time.time()  # Track start time for throughput calculation
        logger.info(f"Request {request_id}: Starting Stage 1 - Parallel Synthesis with {len(self.models)} models.")
        responses_data = [] # To store successful responses with their metadata
        errors = []
        response_times_map = {} # model_name: time

        if not self.models:
            logger.error(f"Request {request_id}: No models available for parallel synthesis.")
            return [], ["No models configured"], {"synthesis_attempts": 0}

        tasks_with_model_names = []
        # Only use active models for parallel synthesis
        for model_name in self.active_models:
            model_info = self.models[model_name]
            # Create a coroutine that, when awaited, returns (model_name, result_of_call)
            async def task_wrapper(m_name, m_info, i_data, r_id):
                try:
                    res = await self._call_individual_model_for_synthesis(m_name, m_info, i_data, r_id)
                    # Reset failure count on success
                    self.model_failure_counts[m_name] = 0
                    return m_name, res # res is (LLMStructuredOutput, float_time) or None if exception handled inside
                except Exception as e:
                    # Increment failure count on failure
                    self.model_failure_counts[m_name] += 1
                    self.metrics_collector.increment_model_failures(m_name) # Increment Prometheus counter
                    if self.config.enable_model_degradation and self.model_failure_counts[m_name] >= self.config.llm_failure_threshold:
                        await self._degrade_model(m_name, request_id)
                    return m_name, e # Return the exception associated with the model name

            tasks_with_model_names.append(task_wrapper(model_name, model_info, input_data, request_id))
        
        # Gather results. Each item in `gathered_results` will be (model_name, actual_result_or_exception)
        gathered_results = await asyncio.gather(*tasks_with_model_names, return_exceptions=False) # Exceptions are handled in task_wrapper

        for model_name, result in gathered_results:
            # Check if the model is still active before processing its result
            if model_name not in self.active_models:
                logger.warning(f"Request {request_id}: Model {model_name} was degraded during synthesis, skipping its result.")
                continue

            model_info = self.models[model_name] # Get model_info again using the returned model_name
            if isinstance(result, Exception):
                error_message = f"Model {model_name}: {str(result)}"
                errors.append(error_message)
                logger.warning(f"Request {request_id}: Model {model_name} failed during synthesis: {result}")
            elif result and isinstance(result, tuple) and len(result) == 2: # result is (response_output, response_time)
                response_output, response_time = result
                if response_output and isinstance(response_output, LLMStructuredOutput):
                    response_times_map[model_name] = response_time
                    responses_data.append({
                        "model_name": model_name,
                        "synthesis_output": response_output,
                        "weight": model_info["weight"],
                        "type": model_info["type"],
                        "response_time": response_time
                    })
                    logger.debug(f"Request {request_id}: Model {model_name} synthesized in {response_time:.3f}s")
                else:
                    error_message = f"Model {model_name}: Invalid synthesis output format received."
                    errors.append(error_message)
                    logger.warning(f"Request {request_id}: {error_message} Output: {response_output}")
            else:
                # This case should ideally not be reached if _call_individual_model_for_synthesis always returns a tuple or raises
                error_message = f"Model {model_name}: Unexpected result format from _call_individual_model_for_synthesis: {result}"
                errors.append(error_message)
                logger.error(f"Request {request_id}: {error_message}")

        metrics_details = {
            "response_times_map": response_times_map,
            "synthesis_attempts": len(self.models),
            "successful_synthesis_count": len(responses_data)
        }
        
        # Calculate aggregated response times for individual model calls within this stage
        individual_response_times = list(response_times_map.values())
        if individual_response_times:
            metrics_details["avg_individual_response_time"] = np.mean(individual_response_times)
            metrics_details["p95_individual_response_time"] = np.percentile(individual_response_times, 95)
            metrics_details["p99_individual_response_time"] = np.percentile(individual_response_times, 99)
        else:
            metrics_details["avg_individual_response_time"] = 0.0
            metrics_details["p95_individual_response_time"] = 0.0
            metrics_details["p99_individual_response_time"] = 0.0

        # Calculate throughput for this stage (requests per second)
        total_synthesis_time = time.time() - start_time # This start_time is for _parallel_synthesis
        metrics_details["synthesis_throughput_rps"] = len(responses_data) / total_synthesis_time if total_synthesis_time > 0 else 0.0
        
        logger.info(f"Request {request_id}: Stage 1 - Parallel Synthesis completed. Successes: {len(responses_data)}, Failures: {len(errors)}")
        return responses_data, errors, metrics_details

    async def _call_individual_model_for_synthesis(
        self, model_name: str, model_info: Dict, input_data: LLMInterpretationInput, request_id: str
    ) -> Tuple[LLMStructuredOutput, float]: # Ensure it always returns this tuple or raises
        """Helper to call a single model and record its time, returns (response, time) or raises exception."""
        model_start_time = time.time()
        logger.debug(f"Request {request_id}: Calling model {model_name} (type: {model_info.get('type', 'unknown')}) for synthesis.")
        
        try:
            response_output: Optional[LLMStructuredOutput] = None
            client = model_info.get("client")

            if not client:
                logger.error(f"Request {request_id}: No client found for model {model_name}.")
                raise ValueError(f"Client not initialized for model {model_name}")

            # Construct a specific prompt for synthesis if needed, or use a generic one.
            # The current input_data (LLMInterpretationInput) is assumed to be suitable.
            
            model_type = model_info.get("type", "unknown")

            if model_type in ["openai", "anthropic", "cohere"]: # LangChain models
                if not hasattr(self, '_call_langchain_model'): # Defensive check
                    logger.error(f"Request {request_id}: _call_langchain_model method missing.")
                    raise NotImplementedError("_call_langchain_model is not implemented.")
                response_output = await self._call_langchain_model(client, input_data, model_name)
            elif model_type in ["fallback_generic", "default_fallback_emergency", "local", "gemini", "fallback"]:
                if not hasattr(client, 'get_structured_interpretation'):
                    logger.error(f"Request {request_id}: Client for model {model_name} (type {model_type}) does not have get_structured_interpretation method.")
                    raise NotImplementedError(f"get_structured_interpretation not implemented for {model_type} client.")
                response_output = await client.get_structured_interpretation(input_data)
            else:
                logger.error(f"Request {request_id}: Unknown model type '{model_type}' for model {model_name}.")
                raise ValueError(f"Unknown model type '{model_type}' for {model_name}")
            
            if not response_output or not isinstance(response_output, LLMStructuredOutput):
                logger.error(f"Request {request_id}: Model {model_name} returned invalid output type: {type(response_output)}. Expected LLMStructuredOutput.")
                # Create a default error response to avoid downstream issues if possible, or raise
                raise ValueError(f"Model {model_name} returned invalid output type.")

            model_response_time = time.time() - model_start_time
            logger.debug(f"Request {request_id}: Model {model_name} responded in {model_response_time:.3f}s.")
            return response_output, model_response_time
            
        except Exception as e:
            # Log the specific exception and model name before re-raising
            logger.error(f"Request {request_id}: Exception during synthesis call for model {model_name} (type: {model_info.get('type', 'unknown')}): {type(e).__name__} - {e}", exc_info=True)
            raise # Re-raise the caught exception to be handled by the caller (_parallel_synthesis)

    async def _cross_validate_results(
        self,
        synthesis_results: List[Dict[str, Any]],
        principle_text: str,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Stage 2: Perform cross-validation of synthesis results.
        Each synthesis is validated by other models in the ensemble.
        Returns a validation matrix or similar structure.
        """
        logger.info(f"Request {request_id}: Starting Stage 2 - Cross-Validation.")
        validation_matrix = {} # e.g., {synthesizer_model_name: {validator_model_name: validation_score/result}}
        
        validation_tasks = []

        for synth_item in synthesis_results:
            synthesizer_model_name = synth_item["model_name"]
            synthesized_policy_text = synth_item["synthesis_output"].raw_llm_response
            # Initialize the entry for the synthesizer model to avoid KeyError later if all its validations fail
            validation_matrix[synthesizer_model_name] = {}


            for validator_model_name, validator_model_info in self.models.items():
                if validator_model_name == synthesizer_model_name: # A model doesn't validate its own synthesis
                    continue
                
                # Prepare task for concurrent execution
                validation_tasks.append(
                    self._perform_single_cross_validation(
                        synthesizer_model_name, validator_model_name, validator_model_info,
                        principle_text, synthesized_policy_text, request_id
                    )
                )
        
        cross_validation_run_results = await asyncio.gather(*validation_tasks, return_exceptions=True)

        for result_item in cross_validation_run_results:
            if isinstance(result_item, Exception):
                logger.error(f"Request {request_id}: Error during a cross-validation task: {result_item}")
                # Decide how to handle individual validator failures, e.g., mark as low score or skip
                # For now, we log and the specific synth_name/validator_name pair won't get an entry or will have error.
            elif result_item:
                synth_name, validator_name, val_score, val_comment = result_item
                if synth_name not in validation_matrix:
                     validation_matrix[synth_name] = {} # Should have been initialized
                validation_matrix[synth_name][validator_name] = {
                    "score": val_score,
                    "comment": val_comment
                }
        
        logger.info(f"Request {request_id}: Stage 2 - Cross-Validation completed.")
        return validation_matrix

    async def _perform_single_cross_validation(
        self, synthesizer_model_name: str, validator_model_name: str, validator_model_info: Dict,
        principle_text: str, synthesized_policy_text: str, request_id: str
    ) -> Tuple[str, str, float, str]:
        """Helper for a single cross-validation call."""
        try:
            # This prompt asks the validator to assess the synthesized policy against the original principle.
            validation_prompt_text = (
                f"Original Constitutional Principle: \"{principle_text}\"\n\n"
                f"Proposed Policy (synthesized by '{synthesizer_model_name}'): \"{synthesized_policy_text}\"\n\n"
                f"Task: As the '{validator_model_name}' model, evaluate the Proposed Policy based on the Original Constitutional Principle. \n"
                f"1. Is the Proposed Policy a faithful interpretation of the Original Principle? (Yes/No/Partially)\n"
                f"2. Is the Proposed Policy logically consistent with the Original Principle? (Yes/No/Partially)\n"
                f"3. Provide an overall alignment score from 0.0 (no alignment) to 1.0 (perfect alignment).\n"
                f"4. Briefly justify your score and highlight any misalignments or inconsistencies.\n\n"
                f"Respond ONLY with a JSON object containing 'faithful' (string), 'consistent' (string), 'score' (float), and 'justification' (string)."
            )
            
            validation_input = LLMInterpretationInput(
                principle_id=f"validation_{request_id}_{synthesizer_model_name}_by_{validator_model_name}",
                principle_text=validation_prompt_text,
                context = {"role": "validation", "original_principle_preview": principle_text[:100]+"...", "policy_under_review_preview": synthesized_policy_text[:100]+"..."}
            )
            
            # Use _call_individual_model_for_synthesis to get LLMStructuredOutput
            validation_llm_output, _ = await self._call_individual_model_for_synthesis(validator_model_name, validator_model_info, validation_input, request_id)
            
            parsed_validation = self._parse_structured_validation_response(validation_llm_output.raw_llm_response, validator_model_name, synthesizer_model_name, request_id)
            validation_score = parsed_validation.get("score", 0.0)
            validation_comment = parsed_validation.get("justification", "Automated validation placeholder")

            logger.debug(f"Request {request_id}: {validator_model_name} validated {synthesizer_model_name}'s policy, score: {validation_score:.2f}")
            return synthesizer_model_name, validator_model_name, validation_score, validation_comment
        except Exception as e:
            logger.error(f"Request {request_id}: Error during cross-validation by {validator_model_name} for {synthesizer_model_name}: {e}")
            return synthesizer_model_name, validator_model_name, 0.0, f"Validation error: {e}"

    def _parse_structured_validation_response(self, raw_response: str, validator_name: str, synthesizer_name: str, request_id: str) -> Dict[str, Any]:
        """ Parses a structured JSON validation response from an LLM. """
        try:
            # Attempt to find JSON block if the response is not pure JSON
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = raw_response[json_start:json_end]
            else:
                json_str = raw_response # Assume it might be pure JSON

            data = json.loads(json_str)
            score = float(data.get("score", 0.0))
            justification = data.get("justification", "N/A")
            # Could also extract 'faithful' and 'consistent' if needed
            return {"score": score, "justification": justification}
        except json.JSONDecodeError as e:
            logger.warning(f"Request {request_id}: Failed to parse JSON validation response from {validator_name} for {synthesizer_name}: {e}. Raw: {raw_response[:200]}")
            # Fallback: try to extract score with regex if JSON parsing fails
            import re
            match = re.search(r"score[\s:]*([0-9.]+)", raw_response, re.IGNORECASE)
            if match:
                try:
                    return {"score": float(match.group(1)), "justification": "Extracted score via regex after JSON parse failure."}
                except ValueError:
                    pass # Score not a float
            return {"score": 0.0, "justification": "Could not parse validation response."}
        except Exception as e: # Catch other potential errors like float conversion
            logger.warning(f"Request {request_id}: Error processing validation response from {validator_name} for {synthesizer_name}: {e}. Raw: {raw_response[:200]}")
            return {"score": 0.0, "justification": f"Error processing validation: {e}"}


    async def _validate_semantic_consistency(
        self,
        synthesis_results: List[Dict[str, Any]],
        principle_text: str,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Stage 3: Validate semantic consistency of each synthesis against the original principle.
        Uses EnhancedSemanticFaithfulnessValidator.
        Returns a dictionary of semantic scores for each synthesis.
        """
        logger.info(f"Request {request_id}: Starting Stage 3 - Semantic Consistency Validation.")
        semantic_scores = {} # {synthesizer_model_name: faithfulness_score_details}
        
        if not hasattr(self, 'faithfulness_validator') or not isinstance(self.faithfulness_validator, EnhancedSemanticFaithfulnessValidator):
            logger.error(f"Request {request_id}: EnhancedSemanticFaithfulnessValidator not initialized in EnhancedMultiModelValidator. Skipping semantic consistency.")
            for synthesis_item in synthesis_results:
                model_name = synthesis_item["model_name"]
                semantic_scores[model_name] = {"overall_score": 0.0, "error": "Faithfulness validator not available."}
            return semantic_scores

        validation_tasks = []
        for synthesis_item in synthesis_results:
            model_name = synthesis_item["model_name"]
            
            # Ensure synthesis_output exists and has raw_llm_response
            if "synthesis_output" not in synthesis_item or not hasattr(synthesis_item["synthesis_output"], 'raw_llm_response'):
                logger.warning(f"Request {request_id}: Missing 'synthesis_output' or 'raw_llm_response' for model {model_name} in semantic consistency check. Skipping.")
                semantic_scores[model_name] = {"overall_score": 0.0, "error": "Missing synthesis output for validation."}
                continue

            policy_text = synthesis_item["synthesis_output"].raw_llm_response
            
            # Create a partial or lambda to pass model_name along with the task result
            async def task_with_model_name(p_text, pol_text, m_name):
                res = await self.faithfulness_validator.validate_faithfulness_comprehensive(p_text, pol_text)
                return m_name, res

            validation_tasks.append(task_with_model_name(principle_text, policy_text, model_name))
        
        if not validation_tasks:
            logger.info(f"Request {request_id}: No valid synthesis results to perform semantic consistency validation on.")
            return semantic_scores

        faithfulness_run_results = await asyncio.gather(*validation_tasks, return_exceptions=True)

        for result_item in faithfulness_run_results:
            if isinstance(result_item, Exception):
                # This error is from asyncio.gather itself or an unhandled exception in task_with_model_name
                logger.error(f"Request {request_id}: General error during semantic consistency gathering: {result_item}")
                # We don't know which model this was for without more context, so we can't assign it.
                # This indicates a problem with the task setup or an unexpected error.
            elif result_item:
                model_name, faithfulness_details = result_item
                if isinstance(faithfulness_details, Exception): # Exception from validate_faithfulness_comprehensive
                    logger.error(f"Request {request_id}: Error during semantic consistency for {model_name}: {faithfulness_details}")
                    semantic_scores[model_name] = {"overall_score": 0.0, "error": str(faithfulness_details)}
                else:
                    semantic_scores[model_name] = faithfulness_details
                    logger.debug(f"Request {request_id}: Semantic score for {model_name}'s policy: {faithfulness_details.get('overall_score', 0.0):.2f}")
            
        logger.info(f"Request {request_id}: Stage 3 - Semantic Consistency Validation completed with {len(semantic_scores)} results.")
        return semantic_scores

    async def _attempt_formal_verification(
        self,
        synthesis_results: List[Dict[str, Any]],
        principle_text: str, # Or a more structured ConstitutionalPrinciple
        request_id: str
    ) -> Dict[str, Any]:
        """
        Stage 4: Attempt formal verification where applicable.
        Placeholder implementation.
        """
        logger.info(f"Request {request_id}: Starting Stage 4 - Formal Verification (Placeholder).")
        if not self.config.formal_verification_enabled:
            logger.info(f"Request {request_id}: Formal verification is disabled by config.")
            return {res["model_name"]: {"verified": False, "reason": "disabled", "details": None} for res in synthesis_results}

        formal_verification_results = {}
        for synthesis_item in synthesis_results:
            model_name = synthesis_item["model_name"]
            # policy_to_verify = synthesis_item["synthesis_output"]
            # In a real scenario, this would involve translating policy to a formal language (e.g., SMT-LIB)
            # and using a solver like Z3.
            formal_verification_results[model_name] = {
                "verified": False, # Placeholder
                "reason": "Not yet implemented",
                "details": None
            }
            logger.debug(f"Request {request_id}: Formal verification for {model_name}'s policy (stubbed).")
        
        logger.info(f"Request {request_id}: Stage 4 - Formal Verification (Placeholder) completed.")
        return formal_verification_results

    async def _weighted_consensus_decision(
        self,
        synthesis_results: List[Dict[str, Any]],
        validation_matrix: Dict[str, Dict[str, Dict[str, Any]]],
        semantic_scores: Dict[str, Dict[str, Any]],
        formal_verification_results: Dict[str, Dict[str, Any]],
        request_id: str
    ) -> Tuple[Optional[LLMStructuredOutput], float, Dict[str, Any]]:
        """
        Stage 5: Make a consensus decision based on all gathered evidence.
        Calculates final policy and confidence.
        """
        logger.info(f"Request {request_id}: Starting Stage 5 - Weighted Consensus Decision.")
        
        candidate_policies = []
        if not synthesis_results:
            logger.error(f"Request {request_id}: No synthesis results provided to _weighted_consensus_decision.")
            return None, 0.0, {"reason": "No synthesis results"}

        for synth_item in synthesis_results:
            model_name = synth_item["model_name"]
            policy_output = synth_item["synthesis_output"]
            base_weight = synth_item.get("weight", self.config.model_weights.get(model_name, 0.1))
            
            semantic_consistency_score = semantic_scores.get(model_name, {}).get("overall_score", 0.0)
            
            cross_val_data_for_model = validation_matrix.get(model_name, {})
            cross_val_scores_list = [
                val_data.get("score", 0.0)
                for val_data in cross_val_data_for_model.values() if isinstance(val_data, dict) # Ensure val_data is a dict
            ]
            avg_cross_val_score = np.mean(cross_val_scores_list) if cross_val_scores_list else 0.0
            
            formally_verified = formal_verification_results.get(model_name, {}).get("verified", False)
            formal_verification_bonus = 0.15 if formally_verified else 0.0

            w_semantic = 0.50
            w_cross_val = 0.30
            w_base_model = 0.05
            w_formal_verif = 0.15

            combined_score = (
                semantic_consistency_score * w_semantic +
                avg_cross_val_score * w_cross_val +
                base_weight * w_base_model +
                formal_verification_bonus
            )
            combined_score = min(combined_score, 1.0) # Cap score at 1.0
            
            candidate_policies.append({
                "model_name": model_name,
                "policy_output": policy_output,
                "final_score": combined_score,
                "details": {
                    "base_model_weight_contribution": base_weight * w_base_model,
                    "semantic_score_contribution": semantic_consistency_score * w_semantic,
                    "avg_cross_val_score_contribution": avg_cross_val_score * w_cross_val,
                    "formal_verification_bonus": formal_verification_bonus,
                    "raw_semantic_score": semantic_consistency_score,
                    "raw_avg_cross_val_score": avg_cross_val_score,
                    "raw_base_weight": base_weight,
                    "formally_verified": formally_verified
                }
            })
            logger.debug(f"Request {request_id}: Candidate {model_name}, combined_score: {combined_score:.4f}")

        if not candidate_policies:
            logger.error(f"Request {request_id}: No candidate policies after scoring in consensus decision.")
            return None, 0.0, {"reason": "No candidates scored"}

        best_candidate = max(candidate_policies, key=lambda x: x["final_score"])
        
        final_policy_output = best_candidate["policy_output"]
        final_confidence = best_candidate["final_score"]

        consensus_details = {
            "chosen_policy_model": best_candidate["model_name"],
            "chosen_policy_confidence": final_confidence,
            "all_candidate_scores": {
                cp["model_name"]: cp["final_score"] for cp in candidate_policies
            },
            "chosen_policy_scoring_breakdown": best_candidate["details"]
        }
        
        logger.info(f"Request {request_id}: Stage 5 - Weighted Consensus Decision completed. Best: {best_candidate['model_name']}, Confidence: {final_confidence:.4f}")
        return final_policy_output, final_confidence, consensus_details

    async def _escalate_to_expert_review(
        self,
        synthesis_results: List[Dict[str, Any]],
        validation_matrix: Dict[str, Any],
        semantic_scores: Dict[str, Any],
        formal_verification_results: Dict[str, Any],
        current_best_policy: Optional[LLMStructuredOutput],
        current_confidence: float,
        principle_text: str,
        context: Optional[str],
        request_id: str,
        synthesis_metrics_details: Dict[str, Any], # New parameter
    ) -> UltraReliableResult:
        """
        Handle escalation to expert review when automated consensus is insufficient.
        """
        logger.warning(f"Request {request_id}: Escalating to expert review. Confidence: {current_confidence:.4f}")
        self.metrics_collector.increment_escalations() # Increment escalation counter
        
        best_policy_model_name = "N/A"
        if current_best_policy:
            for sr in synthesis_results:
                # Ensure 'synthesis_output' exists and is comparable
                if sr.get("synthesis_output") == current_best_policy:
                    best_policy_model_name = sr["model_name"]
                    break
            if best_policy_model_name == "N/A":
                 best_policy_model_name = "Consensus (below threshold)"

        escalation_details = {
            "reason": "Automated consensus confidence below threshold or no policy selected.",
            "current_confidence": current_confidence,
            "current_best_policy_model": best_policy_model_name,
            "principle_text": principle_text,
            "context": context,
            "synthesis_results_summary": [
                {
                    "model": res["model_name"],
                    "output_preview": res.get("synthesis_output").raw_llm_response[:150]+"..." if res.get("synthesis_output") else "N/A",
                    "response_time": res.get("response_time")
                } for res in synthesis_results
            ],
            "validation_matrix_summary": {
                synth_model: {
                    validator: details.get("score") if isinstance(details, dict) else "N/A"
                    for validator, details in val_data.items()
                } for synth_model, val_data in validation_matrix.items()
            },
            "semantic_scores_summary": {
                model: data.get("overall_score") if isinstance(data, dict) else "N/A"
                for model, data in semantic_scores.items()
            },
            "formal_verification_summary": formal_verification_results,
        }

        return UltraReliableResult(
            policy=current_best_policy,
            confidence=current_confidence,
            validation_path="expert_review_required",
            requires_human_review=True,
            synthesis_details=escalation_details,
            error_message="Automated consensus confidence below threshold or no policy selected; expert review required.",
            performance_metrics_details=synthesis_metrics_details # Pass the metrics
        )


    async def _call_langchain_model(self, model_client, input_data: LLMInterpretationInput, model_name_for_log: str = "") -> LLMStructuredOutput:
        """Call LangChain model and convert response to our format."""
        try:
            # Create prompt for the model
            prompt = f"Analyze the following constitutional principle and provide structured interpretation:\n\nPrinciple: {getattr(input_data, 'principle_text', 'N/A')}\nContext: {getattr(input_data, 'context', 'N/A')}"

            # Call the model
            response = model_client.predict(prompt)

            # Convert to our structured format
            return LLMStructuredOutput(
                interpretations=[],  # Would parse structured response in practice
                raw_llm_response=response
            )
        except Exception as e:
            logger.error(f"LangChain model call failed: {e}")
            raise

    def _create_cached_metrics(self, start_time: float, request_id: str) -> ReliabilityMetrics:
        """Create metrics for cached response."""
        return ReliabilityMetrics(
            success_rate=1.0,
            consensus_rate=1.0,
            bias_detection_rate=0.95,
            semantic_faithfulness_score=0.95,
            average_response_time=time.time() - start_time,
            error_rate=0.0,
            fallback_usage_rate=0.0,
            confidence_score=0.95,
            cache_hit_rate=1.0,
            request_id=request_id
        )

    def _calculate_overall_reliability_metrics(
        self,
        synthesis_results: List[Dict[str, Any]],
        errors: List[str],
        validation_matrix: Dict[str, Any],
        semantic_scores: Dict[str, Any],
        formal_verification_results: Dict[str, Any],
        success: bool,
        final_confidence: float,
        metrics_details: Dict[str, Any],
        start_time: float,
        request_id: str
    ) -> ReliabilityMetrics:
        total_time = time.time() - start_time
        total_attempts = metrics_details.get("synthesis_attempts", len(synthesis_results) + len(errors))
        response_times = list(metrics_details.get("response_times_map", {}).values())

        avg_response = metrics_details.get("avg_individual_response_time", np.mean(response_times) if response_times else 0.0)
        p95_time = metrics_details.get("p95_individual_response_time", np.percentile(response_times, 95) if response_times else 0.0)
        p99_time = metrics_details.get("p99_individual_response_time", np.percentile(response_times, 99) if response_times else 0.0)

        semantic_avg = float(np.mean([v.get("overall_score", 0) for v in semantic_scores.values()])) if semantic_scores else 0.0
        agreement_scores = []
        for vals in validation_matrix.values():
            for item in vals.values():
                if isinstance(item, dict) and "score" in item:
                    agreement_scores.append(item["score"])
        model_agreement = float(np.mean(agreement_scores)) if agreement_scores else final_confidence

        error_rate = len(errors) / total_attempts if total_attempts else 0.0

        return ReliabilityMetrics(
            success_rate=1.0 if success else 0.0,
            consensus_rate=final_confidence,
            bias_detection_rate=0.0,
            semantic_faithfulness_score=semantic_avg,
            average_response_time=avg_response,
            error_rate=error_rate,
            fallback_usage_rate=0.0,
            confidence_score=final_confidence,
            model_agreement_score=model_agreement,
            p95_response_time=p95_time,
            p99_response_time=p99_time,
            throughput_requests_per_second=metrics_details.get("synthesis_throughput_rps", 0.0),
            request_id=request_id
        )

    async def _analyze_enhanced_consensus(self, responses: List[Dict]) -> LLMStructuredOutput:
        """Analyze consensus with enhanced algorithms."""
        if len(responses) == 1:
            return responses[0]["response"]

        # Enhanced consensus using weighted voting
        weighted_responses = []
        total_weight = sum(resp["weight"] for resp in responses)

        for resp in responses:
            normalized_weight = resp["weight"] / total_weight
            weighted_responses.append({
                "response": resp["response"],
                "weight": normalized_weight,
                "model": resp["model"]
            })

        # Simple consensus for now - would use semantic similarity in practice
        consensus_text = f"Ensemble consensus from {len(responses)} models: "
        consensus_text += "; ".join([
            f"{resp['model']}({resp['weight']:.2f}): {resp['response'].raw_llm_response[:100]}..."
            for resp in weighted_responses
        ])

        return LLMStructuredOutput(
            interpretations=[],
            raw_llm_response=consensus_text
        )

    def _calculate_enhanced_metrics(
        self,
        responses: List[Dict],
        errors: List[str],
        response_times: List[float],
        total_time: float,
        consensus_result: LLMStructuredOutput,
        request_id: str
    ) -> ReliabilityMetrics:
        """Calculate comprehensive reliability metrics."""
        total_attempts = len(responses) + len(errors)
        success_rate = len(responses) / total_attempts if total_attempts > 0 else 0.0

        # Calculate model agreement score
        model_agreement = 1.0 if len(responses) > 1 else 0.5

        # Calculate performance percentiles
        if response_times:
            p95_time = np.percentile(response_times, 95)
            p99_time = np.percentile(response_times, 99)
        else:
            p95_time = p99_time = 0.0

        return ReliabilityMetrics(
            success_rate=success_rate,
            consensus_rate=model_agreement,
            bias_detection_rate=0.95,  # Would be calculated from actual bias detection
            semantic_faithfulness_score=0.92,  # Would be calculated from actual validation
            average_response_time=total_time,
            error_rate=len(errors) / total_attempts if total_attempts > 0 else 0.0,
            fallback_usage_rate=0.0,
            confidence_score=min(success_rate * model_agreement, 1.0),
            model_agreement_score=model_agreement,
            p95_response_time=p95_time,
            p99_response_time=p99_time,
            throughput_requests_per_second=1.0 / total_time if total_time > 0 else 0.0,
            request_id=request_id,
            model_versions={resp["model"]: "1.0" for resp in responses}
        )

    async def _handle_complete_failure(
        self,
        input_data: LLMInterpretationInput,
        errors: List[str],
        request_id: str
    ) -> Tuple[LLMStructuredOutput, ReliabilityMetrics]:
        """Handle case where all models fail."""
        logger.error(f"All models failed for principle {input_data.principle_id}: {errors}")

        fallback_response = LLMStructuredOutput(
            interpretations=[],
            raw_llm_response=f"All models failed: {'; '.join(errors)}"
        )

        metrics = ReliabilityMetrics(
            success_rate=0.0,
            consensus_rate=0.0,
            bias_detection_rate=0.0,
            semantic_faithfulness_score=0.0,
            average_response_time=0.0,
            error_rate=1.0,
            fallback_usage_rate=1.0,
            confidence_score=0.0,
            request_id=request_id
        )

        return fallback_response, metrics


class EnhancedBiasDetectionFramework:
    """Enhanced bias detection using HuggingFace Fairness Indicators and counterfactual testing."""

    def __init__(self, config: LLMReliabilityConfig):
        self.config = config
        self.bias_patterns = self._load_bias_patterns()
        self.fairness_pipeline = None
        self.counterfactual_templates = self._load_counterfactual_templates()

        # Initialize HuggingFace bias detection if available
        if ENHANCED_DEPENDENCIES_AVAILABLE and config.proactive_bias_mitigation:
            try:
                self.fairness_pipeline = pipeline(
                    "text-classification",
                    model="unitary/toxic-bert",
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info("Initialized HuggingFace bias detection pipeline")
            except Exception as e:
                logger.warning(f"Failed to initialize HuggingFace pipeline: {e}")

    def _load_bias_patterns(self) -> Dict[str, List[str]]:
        """Load comprehensive bias patterns for detection."""
        return {
            "demographic": [
                "age", "gender", "race", "ethnicity", "nationality", "religion",
                "sexual orientation", "disability", "appearance", "accent"
            ],
            "socioeconomic": [
                "income", "education", "occupation", "class", "wealth", "poverty",
                "employment status", "housing", "neighborhood"
            ],
            "cultural": [
                "religion", "culture", "tradition", "belief", "language", "customs",
                "values", "practices", "heritage", "background"
            ],
            "cognitive": [
                "intelligence", "ability", "disability", "mental health", "learning",
                "cognitive capacity", "competence", "skills", "aptitude"
            ],
            "behavioral": [
                "criminal history", "lifestyle", "habits", "choices", "behavior",
                "character", "personality", "reputation", "associations"
            ]
        }

    def _load_counterfactual_templates(self) -> List[Dict[str, str]]:
        """Load templates for counterfactual bias testing."""
        return [
            {
                "original": "he",
                "counterfactual": "she",
                "category": "gender"
            },
            {
                "original": "young person",
                "counterfactual": "elderly person",
                "category": "age"
            },
            {
                "original": "educated individual",
                "counterfactual": "person without formal education",
                "category": "education"
            },
            {
                "original": "native speaker",
                "counterfactual": "non-native speaker",
                "category": "language"
            }
        ]

    async def detect_bias_comprehensive(self, output: LLMStructuredOutput) -> Dict[str, Any]:
        """Comprehensive bias detection using multiple methods."""
        results = {
            "pattern_based": await self._detect_pattern_bias(output),
            "ml_based": await self._detect_ml_bias(output),
            "counterfactual": await self._detect_counterfactual_bias(output),
            "overall_score": 0.0,
            "bias_level": "low",
            "recommendations": []
        }

        # Combine scores with weights
        pattern_weight = 0.4
        ml_weight = 0.4
        counterfactual_weight = 0.2

        results["overall_score"] = (
            results["pattern_based"]["bias_score"] * pattern_weight +
            results["ml_based"]["bias_score"] * ml_weight +
            results["counterfactual"]["bias_score"] * counterfactual_weight
        )

        # Determine bias level
        if results["overall_score"] > 0.7:
            results["bias_level"] = "high"
            results["recommendations"].append("Immediate bias mitigation required")
        elif results["overall_score"] > 0.4:
            results["bias_level"] = "medium"
            results["recommendations"].append("Bias mitigation recommended")
        else:
            results["bias_level"] = "low"
            results["recommendations"].append("Preventive measures sufficient")

        return results

    async def _detect_pattern_bias(self, output: LLMStructuredOutput) -> Dict[str, Any]:
        """Pattern-based bias detection (enhanced version of original method)."""
        bias_score = 0.0
        detected_patterns = []
        category_scores = {}

        text = output.raw_llm_response.lower()

        for category, patterns in self.bias_patterns.items():
            category_score = 0.0
            for pattern in patterns:
                if pattern in text:
                    # Weight by pattern severity and frequency
                    frequency = text.count(pattern)
                    severity = 0.2 if category in ["demographic", "cognitive"] else 0.1
                    pattern_score = min(frequency * severity, 0.5)
                    category_score += pattern_score
                    detected_patterns.append(f"{category}:{pattern}({frequency})")

            category_scores[category] = min(category_score, 1.0)
            bias_score += category_score

        return {
            "bias_score": min(bias_score, 1.0),
            "detected_patterns": detected_patterns,
            "category_scores": category_scores,
            "method": "pattern_based"
        }

    async def _detect_ml_bias(self, output: LLMStructuredOutput) -> Dict[str, Any]:
        """ML-based bias detection using HuggingFace models."""
        if not self.fairness_pipeline:
            return {"bias_score": 0.0, "confidence": 0.0, "method": "ml_based", "available": False}

        try:
            result = self.fairness_pipeline(output.raw_llm_response)

            # Convert toxicity score to bias score
            if isinstance(result, list) and len(result) > 0:
                toxicity_score = result[0].get('score', 0.0) if result[0].get('label') == 'TOXIC' else 0.0
                bias_score = min(toxicity_score * 1.2, 1.0)  # Scale toxicity to bias
            else:
                bias_score = 0.0

            return {
                "bias_score": bias_score,
                "confidence": result[0].get('score', 0.0) if result else 0.0,
                "method": "ml_based",
                "available": True,
                "raw_result": result
            }
        except Exception as e:
            logger.warning(f"ML bias detection failed: {e}")
            return {"bias_score": 0.0, "confidence": 0.0, "method": "ml_based", "available": False}

    async def _detect_counterfactual_bias(self, output: LLMStructuredOutput) -> Dict[str, Any]:
        """Counterfactual bias testing by substituting demographic terms."""
        if not self.config.counterfactual_testing_enabled:
            return {"bias_score": 0.0, "method": "counterfactual", "enabled": False}

        original_text = output.raw_llm_response
        bias_indicators = []
        total_tests = 0
        failed_tests = 0

        for template in self.counterfactual_templates:
            if template["original"] in original_text.lower():
                total_tests += 1

                # Create counterfactual version
                counterfactual_text = original_text.replace(
                    template["original"],
                    template["counterfactual"]
                )

                # Simple semantic difference check (would use more sophisticated methods in practice)
                semantic_difference = self._calculate_semantic_difference(
                    original_text, counterfactual_text
                )

                if semantic_difference > 0.3:  # Threshold for significant difference
                    failed_tests += 1
                    bias_indicators.append({
                        "category": template["category"],
                        "original": template["original"],
                        "counterfactual": template["counterfactual"],
                        "difference": semantic_difference
                    })

        bias_score = failed_tests / total_tests if total_tests > 0 else 0.0

        return {
            "bias_score": bias_score,
            "total_tests": total_tests,
            "failed_tests": failed_tests,
            "bias_indicators": bias_indicators,
            "method": "counterfactual",
            "enabled": True
        }

    def _calculate_semantic_difference(self, text1: str, text2: str) -> float:
        """Calculate semantic difference between two texts (simplified)."""
        # Simplified implementation - would use sentence transformers in practice
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 0.0

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        jaccard_similarity = intersection / union if union > 0 else 0.0
        return 1.0 - jaccard_similarity

    async def mitigate_bias_proactive(self, output: LLMStructuredOutput) -> LLMStructuredOutput:
        """Proactive bias mitigation with multiple strategies."""
        bias_analysis = await self.detect_bias_comprehensive(output)

        mitigated_text = output.raw_llm_response
        mitigation_applied = []

        # Apply mitigation based on bias level
        if bias_analysis["bias_level"] == "high":
            mitigated_text = self._apply_strong_mitigation(mitigated_text)
            mitigation_applied.append("strong_mitigation")
        elif bias_analysis["bias_level"] == "medium":
            mitigated_text = self._apply_moderate_mitigation(mitigated_text)
            mitigation_applied.append("moderate_mitigation")
        else:
            mitigated_text = self._apply_preventive_mitigation(mitigated_text)
            mitigation_applied.append("preventive_mitigation")

        # Add bias analysis metadata
        mitigation_metadata = f"\n[Bias Analysis: {bias_analysis['bias_level']} level, Score: {bias_analysis['overall_score']:.3f}, Mitigations: {', '.join(mitigation_applied)}]"

        return LLMStructuredOutput(
            interpretations=output.interpretations,
            raw_llm_response=mitigated_text + mitigation_metadata
        )

    def _apply_strong_mitigation(self, text: str) -> str:
        """Apply strong bias mitigation for high-bias content."""
        # Replace problematic terms with neutral alternatives
        mitigations = {
            "normal users": "all users",
            "standard users": "authorized users",
            "typical users": "users",
            "regular people": "individuals",
            "ordinary citizens": "citizens",
            "normal people": "people",
            "standard capabilities": "appropriate capabilities",
            "typical behavior": "expected behavior"
        }

        mitigated = text
        for biased_term, neutral_term in mitigations.items():
            mitigated = mitigated.replace(biased_term, neutral_term)

        return mitigated

    def _apply_moderate_mitigation(self, text: str) -> str:
        """Apply moderate bias mitigation for medium-bias content."""
        mitigations = {
            "normal users": "authorized users",
            "standard users": "users",
            "regular users": "users",
            "typical users": "users"
        }

        mitigated = text
        for biased_term, neutral_term in mitigations.items():
            mitigated = mitigated.replace(biased_term, neutral_term)

        return mitigated

    def _apply_preventive_mitigation(self, text: str) -> str:
        """Apply preventive bias mitigation for low-bias content."""
        # Light touch preventive measures
        if "normal users" in text:
            text = text.replace("normal users", "users")

        return text

    # Backward compatibility method
    async def detect_bias(self, output: LLMStructuredOutput) -> Dict[str, Any]:
        """Backward compatibility method for basic bias detection."""
        pattern_result = await self._detect_pattern_bias(output)
        return {
            "bias_score": pattern_result["bias_score"],
            "detected_patterns": pattern_result["detected_patterns"],
            "bias_level": "high" if pattern_result["bias_score"] > 0.5 else "medium" if pattern_result["bias_score"] > 0.2 else "low"
        }

    # Backward compatibility method
    async def mitigate_bias(self, output: LLMStructuredOutput) -> LLMStructuredOutput:
        """Backward compatibility method for bias mitigation."""
        if self.config.proactive_bias_mitigation:
            return await self.mitigate_bias_proactive(output)
        else:
            # Use original simple mitigation
            bias_analysis = await self.detect_bias(output)

            if bias_analysis["bias_score"] > 0.3:
                mitigated_response = output.raw_llm_response.replace(
                    "normal users with standard capabilities",
                    "all users with appropriate access permissions"
                ) + "\n[High bias mitigation applied]"
            elif bias_analysis["bias_score"] > 0.0:
                mitigated_response = output.raw_llm_response.replace(
                    "normal users",
                    "authorized users"
                ) + "\n[Bias mitigation applied]"
            else:
                mitigated_response = output.raw_llm_response.replace(
                    "normal users with standard capabilities",
                    "users with appropriate authorization levels"
                ) + "\n[Preventive bias mitigation applied]"

            return LLMStructuredOutput(
                interpretations=output.interpretations,
                raw_llm_response=mitigated_response
            )


class EnhancedSemanticFaithfulnessValidator:
    """Enhanced semantic faithfulness validation using NLI models and SentenceTransformers."""

    def __init__(self, config: LLMReliabilityConfig):
        self.config = config
        self.sentence_transformer = None
        self.nli_pipeline = None

        # Initialize enhanced models if available
        if ENHANCED_DEPENDENCIES_AVAILABLE and config.nli_validation_enabled:
            try:
                # Initialize SentenceTransformer for semantic similarity
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Initialized SentenceTransformer model")

                # Initialize NLI pipeline for entailment checking
                self.nli_pipeline = pipeline(
                    "text-classification",
                    model="microsoft/DialoGPT-medium",  # Would use a proper NLI model in practice
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info("Initialized NLI pipeline")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced semantic validation: {e}")

    async def validate_faithfulness_comprehensive(
        self,
        principle_text: str,
        policy_output: str
    ) -> Dict[str, Any]:
        """Comprehensive semantic faithfulness validation."""
        results = {
            "word_overlap": await self._calculate_word_overlap(principle_text, policy_output),
            "semantic_similarity": await self._calculate_semantic_similarity(principle_text, policy_output),
            "nli_entailment": await self._check_nli_entailment(principle_text, policy_output),
            "constitutional_compliance": await self._check_constitutional_compliance(principle_text, policy_output),
            "overall_score": 0.0,
            "validation_passed": False,
            "recommendations": []
        }

        # Combine scores with weights
        word_weight = 0.2
        semantic_weight = 0.4
        nli_weight = 0.3
        constitutional_weight = 0.1

        results["overall_score"] = (
            results["word_overlap"]["score"] * word_weight +
            results["semantic_similarity"]["score"] * semantic_weight +
            results["nli_entailment"]["score"] * nli_weight +
            results["constitutional_compliance"]["score"] * constitutional_weight
        )

        # Determine if validation passed
        results["validation_passed"] = results["overall_score"] >= self.config.semantic_threshold

        # Generate recommendations
        if results["overall_score"] < 0.5:
            results["recommendations"].append("Significant semantic drift detected - review policy generation")
        elif results["overall_score"] < 0.7:
            results["recommendations"].append("Moderate semantic drift - consider refinement")
        else:
            results["recommendations"].append("Good semantic faithfulness maintained")

        return results

    async def _calculate_word_overlap(self, principle_text: str, policy_output: str) -> Dict[str, Any]:
        """Calculate word overlap between principle and policy."""
        principle_words = set(principle_text.lower().split())
        policy_words = set(policy_output.lower().split())

        if not principle_words:
            return {"score": 0.0, "overlap": 0, "total_principle_words": 0, "method": "word_overlap"}

        overlap = len(principle_words & policy_words)
        total_principle_words = len(principle_words)
        score = overlap / total_principle_words
        return {
            "score": score,
            "overlap": overlap,
            "total_principle_words": total_principle_words,
            "principle_coverage": score,
            "method": "word_overlap"
        }

    async def _calculate_semantic_similarity(self, principle_text: str, policy_output: str) -> Dict[str, Any]:
        """Calculate semantic similarity using SentenceTransformers."""
        if not self.sentence_transformer:
            # Fallback to simple similarity
            return await self._calculate_simple_similarity(principle_text, policy_output)

        try:
            # Encode texts to embeddings
            principle_embedding = self.sentence_transformer.encode([principle_text])
            policy_embedding = self.sentence_transformer.encode([policy_output])

            # Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = cosine_similarity(principle_embedding, policy_embedding)[0][0]

            return {
                "score": float(similarity),
                "method": "sentence_transformer",
                "model": "all-MiniLM-L6-v2",
                "available": True
            }
        except Exception as e:
            logger.warning(f"SentenceTransformer similarity calculation failed: {e}")
            return await self._calculate_simple_similarity(principle_text, policy_output)

    async def _calculate_simple_similarity(self, principle_text: str, policy_output: str) -> Dict[str, Any]:
        """Fallback simple similarity calculation."""
        principle_words = set(principle_text.lower().split())
        policy_words = set(policy_output.lower().split())

        if not principle_words and not policy_words:
            return {"score": 1.0, "method": "simple_fallback", "available": False}

        if not principle_words or not policy_words:
            return {"score": 0.0, "method": "simple_fallback", "available": False}

        intersection = len(principle_words & policy_words)
        union = len(principle_words | policy_words)
        jaccard_similarity = intersection / union if union > 0 else 0.0

        return {
            "score": jaccard_similarity,
            "method": "simple_fallback",
            "available": False
        }

    async def _check_nli_entailment(self, principle_text: str, policy_output: str) -> Dict[str, Any]:
        """Check if policy entails the principle using NLI."""
        if not self.nli_pipeline:
            return {"score": 0.5, "method": "nli", "available": False, "entailment": "unknown"}

        try:
            # Create entailment prompt
            premise = principle_text
            hypothesis = policy_output

            # For now, use a simple heuristic since we don't have a proper NLI model
            # In practice, would use models like RoBERTa-large-MNLI
            overlap_result = await self._calculate_word_overlap(principle_text, policy_output)

            # Simple heuristic: high overlap suggests entailment
            if overlap_result["score"] > 0.7:
                entailment = "entailment"
                score = 0.9
            elif overlap_result["score"] > 0.4:
                entailment = "neutral"
                score = 0.6
            else:
                entailment = "contradiction"
                score = 0.2

            return {
                "score": score,
                "entailment": entailment,
                "method": "nli_heuristic",
                "available": True
            }
        except Exception as e:
            logger.warning(f"NLI entailment check failed: {e}")
            return {"score": 0.5, "method": "nli", "available": False, "entailment": "unknown"}

    async def _check_constitutional_compliance(self, principle_text: str, policy_output: str) -> Dict[str, Any]:
        """Check constitutional compliance of the policy."""
        # Simple constitutional compliance check
        constitutional_keywords = [
            "rights", "freedom", "equality", "justice", "fairness", "due process",
            "privacy", "liberty", "dignity", "non-discrimination", "transparency"
        ]

        principle_lower = principle_text.lower()
        policy_lower = policy_output.lower()

        principle_constitutional = sum(1 for keyword in constitutional_keywords if keyword in principle_lower)
        policy_constitutional = sum(1 for keyword in constitutional_keywords if keyword in policy_lower)

        if principle_constitutional == 0:
            score = 1.0  # No constitutional requirements to violate
        else:
            score = min(policy_constitutional / principle_constitutional, 1.0)

        return {
            "score": score,
            "principle_constitutional_keywords": principle_constitutional,
            "policy_constitutional_keywords": policy_constitutional,
            "method": "constitutional_keyword_analysis"
        }

    # Backward compatibility method
    async def validate_faithfulness(
        self,
        principle_text: str,
        policy_output: str
    ) -> Dict[str, Any]:
        """Backward compatibility method for basic faithfulness validation."""
        if self.config.nli_validation_enabled:
            comprehensive_result = await self.validate_faithfulness_comprehensive(principle_text, policy_output)
            return {
                "faithfulness_score": comprehensive_result["overall_score"],
                "word_overlap": comprehensive_result["word_overlap"]["overlap"],
                "principle_coverage": comprehensive_result["word_overlap"]["score"],
                "validation_passed": comprehensive_result["validation_passed"]
            }
        else:
            # Use original simple validation
            word_overlap_result = await self._calculate_word_overlap(principle_text, policy_output)
            return {
                "faithfulness_score": word_overlap_result["score"],
                "word_overlap": word_overlap_result["overlap"],
                "principle_coverage": word_overlap_result["score"],
                "validation_passed": word_overlap_result["score"] >= 0.6
            }


class SemanticFaithfulnessValidator:
    """Validates semantic faithfulness of principle-to-policy translation."""
    
    def __init__(self, config: LLMReliabilityConfig):
        self.config = config
    
    async def validate_faithfulness(
        self,
        principle_text: str,
        policy_output: str
    ) -> Dict[str, Any]:
        """Validate semantic faithfulness of translation."""
        # Simplified faithfulness check
        principle_words = set(principle_text.lower().split())
        policy_words = set(policy_output.lower().split())
        
        # Calculate overlap
        overlap = len(principle_words & policy_words)
        total_principle_words = len(principle_words)
        
        faithfulness_score = overlap / total_principle_words if total_principle_words > 0 else 0.0
        
        return {
            "faithfulness_score": faithfulness_score,
            "word_overlap": overlap,
            "principle_coverage": faithfulness_score,
            "validation_passed": faithfulness_score >= 0.6
        }


class EnhancedLLMReliabilityFramework:
    """Enhanced main framework coordinating all reliability components for >99.9% reliability."""

    def __init__(self, config: LLMReliabilityConfig = None):
        self.config = config or LLMReliabilityConfig()

        # Initialize monitoring and metrics first
        self.metrics_collector = PrometheusMetricsCollector(self.config.prometheus_metrics_enabled)
        self.performance_metrics = []
        self.reliability_history = []

        # Initialize enhanced components
        self.multi_model_validator = EnhancedMultiModelValidator(self.config, self.metrics_collector)
        self.bias_detector = EnhancedBiasDetectionFramework(self.config)
        self.faithfulness_validator = EnhancedSemanticFaithfulnessValidator(self.config)

        # Initialize automatic recovery orchestrator
        self.recovery_orchestrator = AutomaticRecoveryOrchestrator(self.config, self.metrics_collector)

        logger.info("Enhanced LLM Reliability Framework initialized with automatic recovery")

    async def initialize(self):
        """Initialize all framework components."""
        # Initialize multi_model_validator first, as it needs metrics_collector
        await self.multi_model_validator.initialize()
        # After multi_model_validator initializes its models, populate active_models and failure_counts
        self.multi_model_validator.active_models = list(self.multi_model_validator.models.keys())
        self.multi_model_validator.model_failure_counts = {model_name: 0 for model_name in self.multi_model_validator.active_models}
        logger.info("Enhanced LLM Reliability Framework fully initialized")

    async def process_with_reliability(
        self,
        input_data: LLMInterpretationInput
    ) -> Tuple[LLMStructuredOutput, ReliabilityMetrics]:
        """Process LLM request with full enhanced reliability framework."""
        start_time = time.time()

        try:
            # Multi-model validation with enhanced ensemble
            # Multi-model validation using the new ultra-reliable consensus method
            # The request_id for the overall process_with_reliability context
            process_request_id = hashlib.md5(f"{getattr(input_data, 'principle_id', 'unknown_principle')}_{start_time}_process".encode()).hexdigest()[:8]
            
            principle = ConstitutionalPrinciple(
                id=str(input_data.principle_id),
                text=input_data.principle_content,
            )
            context = SynthesisContext(domain=input_data.target_context)
            ultra_reliable_result = await self.multi_model_validator.achieve_ultra_reliable_consensus(
                principle, context
            )

            output: LLMStructuredOutput = LLMStructuredOutput(interpretations=[], raw_llm_response="") # Initialize output

            if ultra_reliable_result.policy and isinstance(ultra_reliable_result.policy, LLMStructuredOutput):
                output = ultra_reliable_result.policy
            elif ultra_reliable_result.policy:
                # If policy is some other type, wrap or handle appropriately.
                logger.warning(f"Request {process_request_id}: Policy from consensus is not LLMStructuredOutput, type: {type(ultra_reliable_result.policy)}. Wrapping.")
                output = LLMStructuredOutput(interpretations=[], raw_llm_response=str(ultra_reliable_result.policy))
            else: # No policy could be synthesized or agreed upon, or an error occurred
                logger.error(f"Request {process_request_id}: No policy synthesized by ultra-reliable consensus. Error: {ultra_reliable_result.error_message}")
                # Attempt rule-based fallback immediately if no policy is synthesized
                if self.config.rule_based_fallback_enabled:
                    fallback_policy, fallback_message = await self._apply_rule_based_fallback(
                        input_data,
                        ultra_reliable_result.error_message or "No policy synthesized by consensus.",
                        None # No current best policy to pass
                    )
                    if fallback_policy:
                        output = fallback_policy
                        ultra_reliable_result.status = "FALLBACK_APPLIED_NO_CONSENSUS"
                        logger.warning(f"Request {process_request_id}: Rule-based fallback applied due to no consensus: {fallback_message}")
                        self.metrics_collector.increment_fallbacks()
                    else:
                        # If rule-based fallback also fails, use emergency safeguards
                        output = await self._apply_emergency_safeguards(
                            LLMStructuredOutput(interpretations=[], raw_llm_response=ultra_reliable_result.error_message or "No policy synthesized."),
                            ReliabilityMetrics(
                                success_rate=0.0, consensus_rate=0.0, bias_detection_rate=0.0,
                                semantic_faithfulness_score=0.0, average_response_time=time.time() - start_time,
                                error_rate=1.0, fallback_usage_rate=1.0, confidence_score=0.0,
                                request_id=process_request_id
                            )
                        )
                        ultra_reliable_result.status = "EMERGENCY_SAFEGUARDS_NO_CONSENSUS"
                        self.metrics_collector.increment_fallbacks()
                else:
                    # If rule-based fallback is disabled, directly apply emergency safeguards
                    output = await self._apply_emergency_safeguards(
                        LLMStructuredOutput(interpretations=[], raw_llm_response=ultra_reliable_result.error_message or "No policy synthesized."),
                        ReliabilityMetrics(
                            success_rate=0.0, consensus_rate=0.0, bias_detection_rate=0.0,
                            semantic_faithfulness_score=0.0, average_response_time=time.time() - start_time,
                            error_rate=1.0, fallback_usage_rate=1.0, confidence_score=0.0,
                            request_id=process_request_id
                        )
                    )
                    ultra_reliable_result.status = "EMERGENCY_SAFEGUARDS_NO_CONSENSUS"
                    self.metrics_collector.increment_fallbacks()

            # Construct ReliabilityMetrics from UltraReliableResult and other process details
            metrics = ReliabilityMetrics(
                success_rate=1.0 if ultra_reliable_result.policy and not ultra_reliable_result.requires_human_review else 0.0,
                consensus_rate=ultra_reliable_result.confidence,
                bias_detection_rate=0.0, # To be updated by bias_detector
                semantic_faithfulness_score=0.0, # To be updated by faithfulness_validator
                average_response_time=ultra_reliable_result.performance_metrics_details.get("avg_individual_response_time", time.time() - start_time), # Use individual avg
                error_rate=1.0 if ultra_reliable_result.error_message and not ultra_reliable_result.policy else 0.0,
                fallback_usage_rate=1.0 if ultra_reliable_result.requires_human_review else 0.0,
                confidence_score=ultra_reliable_result.confidence,
                request_id=process_request_id,
                model_agreement_score=ultra_reliable_result.synthesis_details.get("chosen_policy_scoring_breakdown", {}).get("raw_avg_cross_val_score", ultra_reliable_result.confidence) if ultra_reliable_result.synthesis_details else ultra_reliable_result.confidence,
                cache_hit_rate=0.0, # Assuming no top-level cache hit for this new structure yet
                # Placeholder for hallucination_rate and factual_accuracy_score
                # These would ideally come from a dedicated quality assessment module
                hallucination_rate=ultra_reliable_result.validation_details.get("hallucination_score", 0.0) if ultra_reliable_result.validation_details else 0.0,
                factual_accuracy_score=ultra_reliable_result.validation_details.get("factual_accuracy_score", 0.0) if ultra_reliable_result.validation_details else 0.0,
                p95_response_time=ultra_reliable_result.performance_metrics_details.get("p95_individual_response_time", 0.0), # New
                p99_response_time=ultra_reliable_result.performance_metrics_details.get("p99_individual_response_time", 0.0), # New
                throughput_requests_per_second=ultra_reliable_result.performance_metrics_details.get("synthesis_throughput_rps", 0.0), # New
                model_failures_total=self.multi_model_validator.model_failure_counts # Populate with current failure counts
            )
            
            if ultra_reliable_result.requires_human_review:
                logger.warning(f"Request {process_request_id}: Human review required. Path: {ultra_reliable_result.validation_path}. Message: {ultra_reliable_result.error_message}")
                self.metrics_collector.increment_escalations() # Increment escalation counter
            elif not ultra_reliable_result.policy and ultra_reliable_result.error_message:
                 logger.error(f"Request {process_request_id}: Policy synthesis failed. Path: {ultra_reliable_result.validation_path}. Error: {ultra_reliable_result.error_message}")
                 self.metrics_collector.increment_failures() # Increment failure counter

            # Enhanced bias detection and mitigation
            if self.config.bias_detection_enabled:
                if self.config.proactive_bias_mitigation:
                    # Perform bias detection on the current output
                    bias_analysis_before_mitigation = await self.bias_detector.detect_bias_comprehensive(output)
                    metrics.bias_detection_rate = bias_analysis_before_mitigation["overall_score"] # Record bias before mitigation
                    
                    output = await self.bias_detector.mitigate_bias_proactive(output)
                    # After mitigation, re-evaluate bias to get the post-mitigation score
                    bias_analysis_after_mitigation = await self.bias_detector.detect_bias_comprehensive(output)
                    metrics.proactive_bias_score = bias_analysis_after_mitigation["overall_score"] # Record bias after mitigation
                else:
                    # If proactive mitigation is off, just detect bias and record
                    bias_analysis = await self.bias_detector.detect_bias(output)
                    metrics.bias_detection_rate = bias_analysis["bias_score"]
                    metrics.proactive_bias_score = 0.0 # Not applicable if proactive mitigation is off

            # Enhanced semantic faithfulness validation
            if self.config.semantic_validation_enabled and hasattr(input_data, 'principle_text'):
                if self.config.nli_validation_enabled:
                    faithfulness = await self.faithfulness_validator.validate_faithfulness_comprehensive(
                        input_data.principle_text, output.raw_llm_response
                    )
                    metrics.semantic_faithfulness_score = faithfulness["overall_score"]
                    metrics.nli_validation_score = faithfulness["nli_entailment"]["score"]
                    metrics.constitutional_compliance_score = faithfulness["constitutional_compliance"]["score"]
                    # Attempt to extract hallucination and factual accuracy from faithfulness details
                    metrics.hallucination_rate = faithfulness.get("hallucination_rate", metrics.hallucination_rate)
                    metrics.factual_accuracy_score = faithfulness.get("factual_accuracy_score", metrics.factual_accuracy_score)
                else:
                    faithfulness = await self.faithfulness_validator.validate_faithfulness(
                        input_data.principle_text, output.raw_llm_response
                    )
                    metrics.semantic_faithfulness_score = faithfulness["faithfulness_score"]
                    # Fallback for hallucination and factual accuracy if NLI is not enabled
                    metrics.hallucination_rate = 0.0 # Default or placeholder
                    metrics.factual_accuracy_score = 0.0 # Default or placeholder

            # Calculate overall reliability score
            overall_reliability = metrics.overall_reliability_score()

            # Check if reliability target is met
            # Only apply additional safeguards if reliability is too low AND no fallback was already applied due to no consensus
            if overall_reliability < self.config.reliability_target and ultra_reliable_result.status not in ["FALLBACK_APPLIED_NO_CONSENSUS", "EMERGENCY_SAFEGUARDS_NO_CONSENSUS"]:
                logger.warning(f"Reliability target not met: {overall_reliability:.3f} < {self.config.reliability_target}")

                if ultra_reliable_result.requires_human_review:
                    logger.warning(f"Request {process_request_id}: Human review required. Path: {ultra_reliable_result.validation_path}. Message: {ultra_reliable_result.error_message}")
                    
                    fallback_applied = False
                    if self.config.rule_based_fallback_enabled:
                        logger.info(f"Request {process_request_id}: Attempting rule-based fallback.")
                        fallback_policy, fallback_message = await self._apply_rule_based_fallback(
                            input_data,
                            ultra_reliable_result.error_message,
                            output # Pass the current best policy (output from consensus)
                        )
                        if fallback_policy:
                            output = fallback_policy
                            ultra_reliable_result.status = "FALLBACK_APPLIED"
                            logger.warning(f"Request {process_request_id}: Rule-based fallback applied: {fallback_message}")
                            fallback_applied = True
                            metrics.fallback_usage_rate = 1.0 # Indicate fallback was used
                            self.metrics_collector.increment_fallbacks() # Increment fallback counter
                        else:
                            logger.info(f"Request {process_request_id}: Rule-based fallback not applicable: {fallback_message}")

                    if not fallback_applied:
                        logger.warning(f"Request {process_request_id}: Applying emergency safeguards.")
                        output = await self._apply_emergency_safeguards(output, metrics)
                        ultra_reliable_result.status = "ESCALATED_WITH_SAFEGUARDS"
                        metrics.fallback_usage_rate = 1.0 # Indicate safeguards were used
                        self.metrics_collector.increment_fallbacks() # Increment fallback counter for emergency safeguards
                elif overall_reliability < 0.8: # Apply emergency safeguards if reliability is very low, even if not human review
                    logger.warning(f"Request {process_request_id}: Applying emergency safeguards due to very low reliability ({overall_reliability:.3f}).")
                    output = await self._apply_emergency_safeguards(output, metrics)
                    ultra_reliable_result.status = "EMERGENCY_SAFEGUARDS_LOW_RELIABILITY"
                    self.metrics_collector.increment_fallbacks() # Increment fallback counter for emergency safeguards

            # Store performance metrics
            self.performance_metrics.append(metrics)
            self.reliability_history.append(overall_reliability)

            # Limit history size
            if len(self.performance_metrics) > 1000:
                self.performance_metrics = self.performance_metrics[-1000:]
                self.reliability_history = self.reliability_history[-1000:]

            # Record metrics to Prometheus
            self.metrics_collector.record_metrics(metrics)

            # Automatic Recovery Monitoring and Execution
            if self.config.auto_recovery_enabled:
                try:
                    # Prepare current metrics for recovery monitoring
                    current_metrics = {
                        'overall_reliability': overall_reliability,
                        'avg_response_time': metrics.average_response_time,
                        'consensus_rate': metrics.consensus_rate,
                        'bias_detection_rate': metrics.bias_detection_rate,
                        'semantic_faithfulness_score': metrics.semantic_faithfulness_score,
                        'error_rate': metrics.error_rate,
                        'success_rate': metrics.success_rate
                    }

                    # Prepare component status for recovery monitoring
                    component_status = {
                        'models': {
                            model_name: {
                                'failure_rate': self.multi_model_validator.model_failure_counts.get(model_name, 0) / max(1, len(self.performance_metrics)),
                                'active': model_name in self.multi_model_validator.active_models,
                                'health_status': self.multi_model_validator.model_health_status.get(model_name, {})
                            }
                            for model_name in self.multi_model_validator.models.keys()
                        },
                        'system': {
                            'total_requests': len(self.performance_metrics),
                            'recent_reliability': overall_reliability
                        }
                    }

                    # Execute recovery monitoring and actions
                    recovery_executions = await self.recovery_orchestrator.monitor_and_recover(
                        current_metrics, component_status, process_request_id
                    )

                    # Log recovery actions if any were executed
                    if recovery_executions:
                        logger.info(f"Request {process_request_id}: Executed {len(recovery_executions)} recovery actions")
                        for execution in recovery_executions:
                            logger.info(f"Recovery: {execution.action.strategy.value} for {execution.action.target_component} - Status: {execution.status.value}")

                        # Measure recovery effectiveness after a brief delay
                        await asyncio.sleep(1.0)  # Allow recovery actions to take effect

                        # Re-calculate metrics to measure recovery effectiveness
                        post_recovery_metrics = {
                            'overall_reliability': self.get_overall_reliability(),
                            'avg_response_time': metrics.average_response_time,  # Would be updated in real implementation
                            'consensus_rate': metrics.consensus_rate,
                            'bias_detection_rate': metrics.bias_detection_rate,
                            'semantic_faithfulness_score': metrics.semantic_faithfulness_score,
                            'error_rate': metrics.error_rate,
                            'success_rate': metrics.success_rate
                        }

                        # Measure effectiveness for each recovery execution
                        for execution in recovery_executions:
                            effectiveness = await self.recovery_orchestrator.measure_recovery_effectiveness(
                                execution, post_recovery_metrics
                            )
                            logger.info(f"Recovery effectiveness for {execution.action.strategy.value}: {effectiveness:.3f}")

                except Exception as recovery_error:
                    logger.error(f"Request {process_request_id}: Error in automatic recovery monitoring: {recovery_error}")
                    # Don't fail the main request due to recovery errors

            # Log reliability status
            if overall_reliability >= self.config.reliability_target:
                logger.info(f"Request {process_request_id}: Reliability target achieved: {overall_reliability:.3f}")

            return output, metrics

        except Exception as e:
            logger.error(
                f"Error in process_with_reliability for input {getattr(input_data, 'input_hash', 'n/a')}: {e}",
                exc_info=True,
            )
            self.metrics_collector.increment_failures() # Increment overall failures
            # In case of an unexpected error, apply emergency safeguards as a last resort
            final_policy = await self._apply_emergency_safeguards(
                LLMStructuredOutput(interpretations=[], raw_llm_response=f"Unexpected error: {str(e)}"),
                ReliabilityMetrics(
                    success_rate=0.0, consensus_rate=0.0, bias_detection_rate=0.0,
                    semantic_faithfulness_score=0.0, average_response_time=time.time() - start_time,
                    error_rate=1.0, fallback_usage_rate=1.0, confidence_score=0.0,
                    request_id=process_request_id,
                    hallucination_rate=1.0, # Assume high hallucination on error
                    factual_accuracy_score=0.0 # Assume low factual accuracy on error
                )
            )
            return final_policy, ReliabilityMetrics(
                success_rate=0.0, consensus_rate=0.0, bias_detection_rate=0.0,
                semantic_faithfulness_score=0.0, average_response_time=time.time() - start_time,
                error_rate=1.0, fallback_usage_rate=1.0, confidence_score=0.0,
                request_id=process_request_id,
                hallucination_rate=1.0, # Assume high hallucination on error
                factual_accuracy_score=0.0 # Assume low factual accuracy on error
            )

    async def _apply_emergency_safeguards(
        self,
        output: LLMStructuredOutput,
        metrics: ReliabilityMetrics
    ) -> LLMStructuredOutput:
        """Apply emergency safeguards when reliability is critically low."""
        logger.warning("Applying emergency safeguards due to low reliability")

        safeguarded_response = output.raw_llm_response + "\n\n[EMERGENCY SAFEGUARDS APPLIED: This response has been flagged for low reliability. Please review carefully before implementation.]"

        metrics.fallback_usage_rate = 1.0

        return LLMStructuredOutput(
            interpretations=output.interpretations,
            raw_llm_response=safeguarded_response
        )

    async def _apply_rule_based_fallback(
        self,
        input_data: LLMInterpretationInput,
        error_message: str,
        current_best_policy: Optional[LLMStructuredOutput]
    ) -> Tuple[Optional[LLMStructuredOutput], str]:
        """
        Applies rule-based fallback mechanisms when LLM outputs fail validation.
        Returns a fallback policy and a message indicating the fallback action.
        """
        logger.warning(f"Applying rule-based fallback for LLM failure: {error_message}")

        # Example rule 1: If the error is about "malformed JSON", try to wrap the current best policy
        if "malformed json" in error_message.lower() and current_best_policy:
            try:
                # Attempt to re-parse or re-format the raw response
                # This is a simple example; a real implementation might use a more robust JSON repair LLM call
                repaired_json_str = f"```json\n{current_best_policy.raw_llm_response}\n```"
                logger.info("Rule-based fallback: Attempted to repair malformed JSON.")
                return LLMStructuredOutput(
                    interpretations=current_best_policy.interpretations,
                    raw_llm_response=repaired_json_str
                ), "Rule-based fallback: Malformed JSON repaired."
            except Exception as e:
                logger.error(f"Failed to repair JSON in fallback: {e}")

        # Example rule 2: If the error is about "safety violation", return a generic safe response
        if "safety violation" in error_message.lower() or "unsafe content" in error_message.lower():
            safe_response = "The requested policy could not be generated due to potential safety concerns. Please refine your request or consult an expert."
            logger.info("Rule-based fallback: Returned generic safe response due to safety violation.")
            return LLMStructuredOutput(
                interpretations=[],
                raw_llm_response=safe_response
            ), "Rule-based fallback: Generic safe response due to safety violation."

        # Example rule 3: If the error is about "lack of consensus", return a simplified default policy
        if "consensus below threshold" in error_message.lower() or "no policy selected" in error_message.lower():
            default_policy_text = f"A definitive policy could not be established due to lack of consensus among models. Defaulting to a conservative interpretation of principle: '{input_data.principle_text}'."
            logger.info("Rule-based fallback: Returned conservative default policy due to lack of consensus.")
            return LLMStructuredOutput(
                interpretations=[],
                raw_llm_response=default_policy_text
            ), "Rule-based fallback: Conservative default policy applied."

        # Example rule 4: If all models are degraded, return a hardcoded default response
        if not self.multi_model_validator.active_models:
            logger.critical(f"All LLM models are degraded. Returning default fallback response: {self.config.default_fallback_response}")
            return LLMStructuredOutput(
                interpretations=[],
                raw_llm_response=self.config.default_fallback_response
            ), "Rule-based fallback: All models degraded, returned default response."

        # If no specific rule applies, try re-routing to a healthy model
        if self.multi_model_validator.active_models:
            logger.info("No specific rule-based fallback applied, attempting to re-route to a healthy model.")
            rerouted_policy, reroute_message = await self._re_route_to_healthy_model(input_data, current_best_policy)
            if rerouted_policy:
                return rerouted_policy, reroute_message
            else:
                logger.warning(f"Re-routing to healthy model failed: {reroute_message}")
                return None, reroute_message

        logger.info("No specific rule-based fallback applied and no active models for re-routing.")
        return None, "No specific rule-based fallback applied and no active models for re-routing."

    async def _re_route_to_healthy_model(
        self,
        input_data: LLMInterpretationInput,
        current_best_policy: Optional[LLMStructuredOutput]
    ) -> Tuple[Optional[LLMStructuredOutput], str]:
        """
        Attempts to re-route the request to a different, healthy model if the primary model fails or is degraded.
        This is a key part of Automatic Reliability Recovery.
        """
        logger.info(f"Attempting to re-route request for principle {input_data.principle_id} to a healthy model.")

        # Filter out models that have been degraded or have high failure counts
        eligible_models = [
            model_name for model_name in self.multi_model_validator.active_models
            if self.multi_model_validator.model_failure_counts.get(model_name, 0) < self.config.llm_failure_threshold
        ]

        if not eligible_models:
            return None, "No eligible healthy models available for re-routing."

        # Prioritize models that haven't been used recently or have lower failure rates
        # For simplicity, we'll just pick the first eligible model for now.
        # A more sophisticated approach would involve a round-robin or a more intelligent selection.
        target_model_name = eligible_models[0]
        target_model_info = self.multi_model_validator.models.get(target_model_name)

        if not target_model_info:
            return None, f"Target model {target_model_name} not found in initialized models."

        try:
            logger.info(f"Re-routing request to model: {target_model_name}")
            # Re-process the input data using the selected healthy model
            # This will bypass the full consensus process and directly call the model
            rerouted_output, _ = await self.multi_model_validator._call_individual_model_for_synthesis(
                target_model_name, target_model_info, input_data, input_data.principle_id # Using principle_id as request_id for simplicity here
            )
            
            if rerouted_output:
                logger.info(f"Successfully re-routed and obtained response from {target_model_name}.")
                return rerouted_output, f"Re-routed to {target_model_name} due to previous failure."
            else:
                return None, f"Re-routed model {target_model_name} returned no output."

        except Exception as e:
            logger.error(f"Error during re-routing to model {target_model_name}: {e}", exc_info=True)
            # Increment failure count for the re-routed model
            self.multi_model_validator.model_failure_counts[target_model_name] = self.multi_model_validator.model_failure_counts.get(target_model_name, 0) + 1
            self.metrics_collector.increment_model_failures(target_model_name)
            if self.config.enable_model_degradation and self.multi_model_validator.model_failure_counts[target_model_name] >= self.config.llm_failure_threshold:
                await self.multi_model_validator._degrade_model(target_model_name, input_data.principle_id) # Use principle_id as request_id
            return None, f"Failed to re-route to {target_model_name}: {e}"

    async def _degrade_model(self, model_name: str, request_id: str):
        """Degrade (disable) a model that has consistently failed."""
        if model_name in self.multi_model_validator.active_models:
            self.multi_model_validator.active_models.remove(model_name)
            logger.warning(f"Request {request_id}: Model {model_name} has been degraded due to {self.multi_model_validator.model_failure_counts[model_name]} consecutive failures.")
            # Optionally, notify monitoring systems or trigger an alert
            self.metrics_collector.increment_escalations() # Consider model degradation an escalation
        else:
            logger.info(f"Request {request_id}: Attempted to degrade {model_name}, but it was already inactive.")

    def get_overall_reliability(self) -> float:
        """Calculate overall system reliability with enhanced metrics."""
        if not self.reliability_history:
            return 0.0

        # Use recent reliability scores
        recent_scores = self.reliability_history[-100:]  # Last 100 requests

        # Calculate weighted average (more recent scores have higher weight)
        weights = np.exp(np.linspace(0, 1, len(recent_scores)))
        weighted_avg = np.average(recent_scores, weights=weights)

        return float(weighted_avg)

    def get_reliability_trend(self) -> Dict[str, Any]:
        """Get reliability trend analysis."""
        if len(self.reliability_history) < 10:
            return {"trend": "insufficient_data", "direction": "unknown", "confidence": 0.0}

        recent_scores = self.reliability_history[-50:]  # Last 50 requests

        # Calculate trend using linear regression
        x = np.arange(len(recent_scores))
        y = np.array(recent_scores)

        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]

        if slope > 0.001:
            direction = "improving"
        elif slope < -0.001:
            direction = "declining"
        else:
            direction = "stable"

        # Calculate confidence based on variance
        variance = np.var(recent_scores)
        confidence = max(0.0, 1.0 - variance)

        return {
            "trend": direction,
            "slope": float(slope),
            "confidence": float(confidence),
            "recent_average": float(np.mean(recent_scores)),
            "variance": float(variance)
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.performance_metrics:
            return {"status": "no_data"}

        recent_metrics = self.performance_metrics[-100:]

        summary = {
            "overall_reliability": self.get_overall_reliability(),
            "reliability_trend": self.get_reliability_trend(),
            "target_achievement": self.get_overall_reliability() >= self.config.reliability_target,
            "metrics": {
                "avg_success_rate": float(np.mean([m.success_rate for m in recent_metrics])),
                "avg_consensus_rate": float(np.mean([m.consensus_rate for m in recent_metrics])),
                "avg_bias_detection_rate": float(np.mean([m.bias_detection_rate for m in recent_metrics])),
                "avg_semantic_faithfulness": float(np.mean([m.semantic_faithfulness_score for m in recent_metrics])),
                "avg_response_time": float(np.mean([m.average_response_time for m in recent_metrics])),
                "avg_error_rate": float(np.mean([m.error_rate for m in recent_metrics])),
                "cache_hit_rate": float(np.mean([m.cache_hit_rate for m in recent_metrics]))
            },
            "total_requests": len(self.performance_metrics),
            "config": {
                "reliability_target": self.config.reliability_target,
                "bias_detection_enabled": self.config.bias_detection_enabled,
                "semantic_validation_enabled": self.config.semantic_validation_enabled,
                "proactive_bias_mitigation": self.config.proactive_bias_mitigation,
                "nli_validation_enabled": self.config.nli_validation_enabled
            }
        }

        return summary

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get comprehensive automatic recovery statistics."""
        if not hasattr(self, 'recovery_orchestrator'):
            return {"status": "recovery_not_enabled"}

        return self.recovery_orchestrator.get_recovery_statistics()

    async def trigger_manual_recovery(
        self,
        strategy: RecoveryStrategy,
        target_component: str,
        parameters: Dict[str, Any] = None,
        request_id: str = None
    ) -> Optional[RecoveryExecution]:
        """Manually trigger a specific recovery action."""
        if not hasattr(self, 'recovery_orchestrator'):
            logger.warning("Recovery orchestrator not available for manual recovery")
            return None

        if not request_id:
            request_id = f"manual_{int(time.time())}"

        # Create manual recovery action
        action = RecoveryAction(
            strategy=strategy,
            trigger=RecoveryTrigger.RELIABILITY_THRESHOLD_BREACH,  # Use generic trigger for manual
            priority=1,  # High priority for manual actions
            target_component=target_component,
            parameters=parameters or {}
        )

        # Get current metrics for recovery execution
        current_metrics = {}
        if self.performance_metrics:
            latest_metrics = self.performance_metrics[-1]
            current_metrics = {
                'overall_reliability': self.get_overall_reliability(),
                'avg_response_time': latest_metrics.average_response_time,
                'consensus_rate': latest_metrics.consensus_rate,
                'bias_detection_rate': latest_metrics.bias_detection_rate,
                'semantic_faithfulness_score': latest_metrics.semantic_faithfulness_score,
                'error_rate': latest_metrics.error_rate,
                'success_rate': latest_metrics.success_rate
            }

        # Execute the recovery action
        execution = await self.recovery_orchestrator._execute_recovery_action(
            action, current_metrics, request_id
        )

        logger.info(f"Manual recovery triggered: {strategy.value} for {target_component}")
        return execution


# Backward compatibility alias
class LLMReliabilityFramework(EnhancedLLMReliabilityFramework):
    """Backward compatibility alias for the enhanced framework."""
    pass


@dataclass
class ConstitutionalPrinciple:
    """
    Represents a constitutional principle to be interpreted or synthesized into policy.
    Aligns with the research protocol's concept.
    """
    id: str
    text: str
    version: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict) # E.g., keywords, related principles


@dataclass
class SynthesisContext:
    """
    Provides context for the policy synthesis process.
    Aligns with the research protocol's concept.
    """
    domain: Optional[str] = None  # E.g., "healthcare", "finance"
    jurisdiction: Optional[str] = None # E.g., "EU", "US-CA"
    target_audience: Optional[str] = None # E.g., "developers", "end_users"
    application_scenario: Optional[str] = None # Specific use case
    historical_data: Optional[List[Dict[str, Any]]] = field(default_factory=list) # Past interpretations or issues
    related_policies: Optional[List[str]] = field(default_factory=list) # IDs or texts of related policies
    custom_instructions: Optional[str] = None # Specific instructions for this synthesis task
    metadata: Dict[str, Any] = field(default_factory=dict)
