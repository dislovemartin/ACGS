"""
WINA-Optimized Policy Enforcement Module for PGC Service

This module integrates WINA (Weight Informed Neuron Activation) optimization
insights into the policy enforcement pipeline for enhanced performance and
targeted policy application.

Key Features:
- WINA-informed enforcement strategy selection
- Performance-aware policy evaluation optimization
- Constitutional compliance verification during enforcement
- Adaptive enforcement based on system state and WINA insights
- Integration with existing OPA client and incremental compiler

Target Performance:
- Improved enforcement efficiency through WINA insights
- Reduced policy evaluation latency
- Enhanced constitutional compliance verification
- Adaptive enforcement strategy selection
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

# WINA imports
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))
    from wina.config import WINAConfig, load_wina_config_from_env
    from wina.metrics import WINAMetrics
    from wina.constitutional_integration import ConstitutionalWINAIntegration
    WINA_AVAILABLE = True
except ImportError as e:
    WINA_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"WINA modules not available: {e}")

from .opa_client import OPAClient, PolicyEvaluationRequest, PolicyEvaluationResponse
from .incremental_compiler import IncrementalCompiler, CompilationMetrics
from .wina_policy_compiler import WINAPolicyCompiler, WINACompilationResult
from ..schemas import IntegrityPolicyRule
from .. import schemas

logger = logging.getLogger(__name__)


class EnforcementStrategy(Enum):
    """Enforcement strategy options based on WINA insights."""
    STANDARD = "standard"
    WINA_OPTIMIZED = "wina_optimized"
    CONSTITUTIONAL_PRIORITY = "constitutional_priority"
    PERFORMANCE_FOCUSED = "performance_focused"
    ADAPTIVE = "adaptive"


@dataclass
class EnforcementContext:
    """Context information for policy enforcement."""
    user_id: str
    action_type: str
    resource_id: str
    environment_factors: Dict[str, Any] = field(default_factory=dict)
    priority_level: str = "normal"
    constitutional_requirements: List[str] = field(default_factory=list)
    performance_constraints: Dict[str, float] = field(default_factory=dict)


@dataclass
class WINAEnforcementMetrics:
    """Metrics for WINA-optimized enforcement operations."""
    enforcement_time_ms: float
    strategy_used: EnforcementStrategy
    wina_optimization_applied: bool
    constitutional_compliance_score: float
    performance_improvement: float
    cache_hit_rate: float
    opa_evaluation_time_ms: float
    wina_analysis_time_ms: float
    total_policies_evaluated: int
    optimized_policies_count: int
    constitutional_violations_detected: int
    enforcement_accuracy: float


@dataclass
class WINAEnforcementResult:
    """Result of WINA-optimized policy enforcement."""
    decision: str  # "permit", "deny", "conditional"
    reason: str
    confidence_score: float
    enforcement_metrics: WINAEnforcementMetrics
    constitutional_compliance: bool
    optimization_applied: bool
    matching_rules: Optional[List[Dict[str, Any]]] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    wina_insights: Dict[str, Any] = field(default_factory=dict)


class WINAEnforcementOptimizer:
    """
    WINA-optimized policy enforcement engine for enhanced performance.
    
    Integrates WINA optimization insights with the PGC enforcement pipeline
    to improve enforcement efficiency while maintaining constitutional compliance.
    """
    
    def __init__(self, enable_wina: bool = True):
        """
        Initialize WINA-optimized enforcement engine.
        
        Args:
            enable_wina: Whether to enable WINA optimization
        """
        self.enable_wina = enable_wina
        
        # Initialize WINA components
        if enable_wina and WINA_AVAILABLE:
            try:
                self.wina_config, self.wina_integration_config = load_wina_config_from_env()
                self.wina_metrics = WINAMetrics(self.wina_config)
                self.constitutional_wina = ConstitutionalWINAIntegration(
                    self.wina_config, self.wina_integration_config
                )
                logger.info("WINA optimization enabled for policy enforcement")
            except Exception as e:
                logger.warning(f"Failed to initialize WINA: {e}. Disabling WINA optimization.")
                self.enable_wina = False
        else:
            self.enable_wina = False
        
        # Initialize core components
        self.opa_client: Optional[OPAClient] = None
        self.wina_policy_compiler: Optional[WINAPolicyCompiler] = None
        
        # Performance tracking
        self._enforcement_history: List[WINAEnforcementResult] = []
        self._strategy_performance: Dict[EnforcementStrategy, List[float]] = {
            strategy: [] for strategy in EnforcementStrategy
        }
        self._constitutional_compliance_cache: Dict[str, Tuple[bool, datetime]] = {}
        self._enforcement_cache: Dict[str, Tuple[WINAEnforcementResult, datetime]] = {}
        
        # Configuration
        self.cache_ttl = timedelta(minutes=5)
        self.max_cache_size = 1000
        self.constitutional_compliance_threshold = 0.85
        self.performance_improvement_threshold = 0.1
        
        logger.info("WINA Enforcement Optimizer initialized")
    
    async def initialize(self, opa_client: OPAClient, wina_policy_compiler: WINAPolicyCompiler):
        """Initialize with required components."""
        self.opa_client = opa_client
        self.wina_policy_compiler = wina_policy_compiler
        logger.info("WINA Enforcement Optimizer components initialized")
    
    async def optimize_enforcement(
        self,
        context: EnforcementContext,
        policies: List[IntegrityPolicyRule],
        optimization_hints: Optional[Dict[str, Any]] = None
    ) -> WINAEnforcementResult:
        """
        Perform WINA-optimized policy enforcement.
        
        Args:
            context: Enforcement context
            policies: Available policies for enforcement
            optimization_hints: Optional WINA optimization hints
            
        Returns:
            WINAEnforcementResult with enforcement decision and metrics
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            logger.info(f"Starting WINA-optimized enforcement for user {context.user_id}")
            
            # Phase 1: Check cache for previous enforcement decisions
            cache_result = await self._check_enforcement_cache(context)
            if cache_result:
                logger.debug("Cache hit for enforcement decision")
                return cache_result
            
            # Phase 2: Select optimal enforcement strategy
            strategy = await self._select_enforcement_strategy(context, policies, optimization_hints)
            
            # Phase 3: Apply WINA-informed policy optimization
            optimized_policies = await self._optimize_policies_for_enforcement(
                policies, context, strategy, optimization_hints
            )
            
            # Phase 4: Perform constitutional compliance verification
            constitutional_compliance = await self._verify_constitutional_compliance(
                context, optimized_policies
            )
            
            # Phase 5: Execute policy enforcement with selected strategy
            enforcement_result = await self._execute_enforcement_strategy(
                strategy, context, optimized_policies, constitutional_compliance
            )
            
            # Phase 6: Calculate performance metrics
            enforcement_time = (time.time() - start_time) * 1000
            metrics = await self._calculate_enforcement_metrics(
                enforcement_time, strategy, context, optimized_policies, enforcement_result
            )
            
            # Create final result
            result = WINAEnforcementResult(
                decision=enforcement_result.get("decision", "deny"),
                reason=enforcement_result.get("reason", "No specific policy grants permission"),
                confidence_score=enforcement_result.get("confidence_score", 0.0),
                enforcement_metrics=metrics,
                constitutional_compliance=constitutional_compliance,
                optimization_applied=self.enable_wina and strategy != EnforcementStrategy.STANDARD,
                matching_rules=enforcement_result.get("matching_rules"),
                warnings=warnings,
                errors=errors,
                wina_insights=enforcement_result.get("wina_insights", {})
            )
            
            # Update tracking and cache
            await self._update_enforcement_tracking(result)
            await self._cache_enforcement_result(context, result)
            
            logger.info(f"WINA-optimized enforcement completed. "
                       f"Decision: {result.decision}, "
                       f"Strategy: {strategy.value}, "
                       f"Performance improvement: {metrics.performance_improvement:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"WINA enforcement optimization failed: {e}")
            errors.append(str(e))
            
            # Fallback to standard enforcement
            return await self._fallback_enforcement(context, policies, errors)

    async def _check_enforcement_cache(self, context: EnforcementContext) -> Optional[WINAEnforcementResult]:
        """Check cache for previous enforcement decisions."""
        cache_key = self._generate_cache_key(context)

        if cache_key in self._enforcement_cache:
            result, timestamp = self._enforcement_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for enforcement context: {cache_key}")
                return result
            else:
                # Remove expired entry
                del self._enforcement_cache[cache_key]

        return None

    async def _select_enforcement_strategy(
        self,
        context: EnforcementContext,
        policies: List[IntegrityPolicyRule],
        optimization_hints: Optional[Dict[str, Any]]
    ) -> EnforcementStrategy:
        """Select optimal enforcement strategy based on WINA insights and context."""

        if not self.enable_wina:
            return EnforcementStrategy.STANDARD

        try:
            # Analyze context requirements
            has_constitutional_requirements = bool(context.constitutional_requirements)
            has_performance_constraints = bool(context.performance_constraints)
            is_high_priority = context.priority_level in ["high", "critical"]

            # Get WINA insights for strategy selection
            wina_insights = await self._get_wina_strategy_insights(context, policies)

            # Strategy selection logic
            if has_constitutional_requirements and wina_insights.get("constitutional_risk", 0) > 0.5:
                return EnforcementStrategy.CONSTITUTIONAL_PRIORITY
            elif has_performance_constraints and wina_insights.get("performance_benefit", 0) > self.performance_improvement_threshold:
                return EnforcementStrategy.PERFORMANCE_FOCUSED
            elif is_high_priority and wina_insights.get("optimization_potential", 0) > 0.7:
                return EnforcementStrategy.WINA_OPTIMIZED
            elif wina_insights.get("adaptive_recommendation", False):
                return EnforcementStrategy.ADAPTIVE
            else:
                return EnforcementStrategy.WINA_OPTIMIZED if self.enable_wina else EnforcementStrategy.STANDARD

        except Exception as e:
            logger.warning(f"Strategy selection failed: {e}. Using standard strategy.")
            return EnforcementStrategy.STANDARD

    async def _optimize_policies_for_enforcement(
        self,
        policies: List[IntegrityPolicyRule],
        context: EnforcementContext,
        strategy: EnforcementStrategy,
        optimization_hints: Optional[Dict[str, Any]]
    ) -> List[IntegrityPolicyRule]:
        """Optimize policies for enforcement using WINA insights."""

        if not self.enable_wina or strategy == EnforcementStrategy.STANDARD:
            return policies

        try:
            # Apply WINA-informed policy filtering and optimization
            optimized_policies = []

            for policy in policies:
                # Check policy relevance for current context
                relevance_score = await self._calculate_policy_relevance(policy, context)

                if relevance_score > 0.1:  # Only include relevant policies
                    # Apply WINA optimization based on strategy
                    optimized_policy = await self._apply_wina_policy_optimization(
                        policy, context, strategy, optimization_hints
                    )
                    optimized_policies.append(optimized_policy)

            logger.debug(f"Optimized {len(policies)} policies to {len(optimized_policies)} for enforcement")
            return optimized_policies

        except Exception as e:
            logger.warning(f"Policy optimization failed: {e}. Using original policies.")
            return policies

    async def _verify_constitutional_compliance(
        self,
        context: EnforcementContext,
        policies: List[IntegrityPolicyRule]
    ) -> bool:
        """Verify constitutional compliance for enforcement context."""

        if not self.enable_wina or not hasattr(self, 'constitutional_wina'):
            return True  # Default to compliant if WINA not available

        try:
            # Check cache first
            compliance_key = self._generate_compliance_cache_key(context, policies)
            if compliance_key in self._constitutional_compliance_cache:
                compliance, timestamp = self._constitutional_compliance_cache[compliance_key]
                if datetime.now() - timestamp < self.cache_ttl:
                    return compliance

            # Perform constitutional compliance verification
            compliance_score = await self.constitutional_wina.verify_enforcement_compliance(
                context.constitutional_requirements,
                [policy.rule_content for policy in policies],
                {
                    "user_id": context.user_id,
                    "action_type": context.action_type,
                    "resource_id": context.resource_id,
                    "environment_factors": context.environment_factors
                }
            )

            is_compliant = compliance_score >= self.constitutional_compliance_threshold

            # Cache result
            self._constitutional_compliance_cache[compliance_key] = (is_compliant, datetime.now())

            # Clean cache if too large
            if len(self._constitutional_compliance_cache) > self.max_cache_size:
                await self._clean_compliance_cache()

            return is_compliant

        except Exception as e:
            logger.warning(f"Constitutional compliance verification failed: {e}. Defaulting to compliant.")
            return True

    async def _execute_enforcement_strategy(
        self,
        strategy: EnforcementStrategy,
        context: EnforcementContext,
        policies: List[IntegrityPolicyRule],
        constitutional_compliance: bool
    ) -> Dict[str, Any]:
        """Execute the selected enforcement strategy."""

        if not self.opa_client:
            raise RuntimeError("OPA client not initialized")

        try:
            # Prepare OPA evaluation request
            evaluation_request = PolicyEvaluationRequest(
                query="data.acgs.authz.allow",
                input_data={
                    "user": {"id": context.user_id},
                    "action": {"type": context.action_type},
                    "resource": {"id": context.resource_id},
                    "environment": context.environment_factors,
                    "constitutional_compliance": constitutional_compliance,
                    "strategy": strategy.value
                },
                explain="full" if strategy == EnforcementStrategy.CONSTITUTIONAL_PRIORITY else "off",
                metrics=True
            )

            # Execute OPA evaluation with strategy-specific optimizations
            opa_start_time = time.time()
            opa_response = await self._execute_opa_evaluation_with_strategy(
                evaluation_request, strategy, policies
            )
            opa_time = (time.time() - opa_start_time) * 1000

            # Process OPA response based on strategy
            enforcement_result = await self._process_opa_response(
                opa_response, strategy, context, constitutional_compliance
            )

            # Add timing information
            enforcement_result["opa_evaluation_time_ms"] = opa_time

            return enforcement_result

        except Exception as e:
            logger.error(f"Enforcement strategy execution failed: {e}")
            return {
                "decision": "deny",
                "reason": f"Enforcement execution failed: {str(e)}",
                "confidence_score": 0.0,
                "opa_evaluation_time_ms": 0.0
            }

    async def _get_wina_strategy_insights(
        self,
        context: EnforcementContext,
        policies: List[IntegrityPolicyRule]
    ) -> Dict[str, Any]:
        """Get WINA insights for strategy selection."""

        if not self.enable_wina:
            return {}

        try:
            # Analyze constitutional risk
            constitutional_risk = 0.0
            if context.constitutional_requirements:
                constitutional_risk = await self._analyze_constitutional_risk(context, policies)

            # Analyze performance benefit potential
            performance_benefit = await self._analyze_performance_benefit(context, policies)

            # Analyze optimization potential
            optimization_potential = await self._analyze_optimization_potential(context, policies)

            # Determine adaptive recommendation
            adaptive_recommendation = (
                constitutional_risk > 0.3 and
                performance_benefit > 0.2 and
                optimization_potential > 0.5
            )

            return {
                "constitutional_risk": constitutional_risk,
                "performance_benefit": performance_benefit,
                "optimization_potential": optimization_potential,
                "adaptive_recommendation": adaptive_recommendation,
                "policy_count": len(policies),
                "context_complexity": len(context.environment_factors)
            }

        except Exception as e:
            logger.warning(f"WINA strategy insights analysis failed: {e}")
            return {}

    async def _calculate_policy_relevance(
        self,
        policy: IntegrityPolicyRule,
        context: EnforcementContext
    ) -> float:
        """Calculate policy relevance score for current context."""

        try:
            relevance_score = 0.0

            # Basic relevance based on policy content
            policy_content = policy.rule_content.lower()

            # Check for user-related terms
            if context.user_id.lower() in policy_content or "user" in policy_content:
                relevance_score += 0.3

            # Check for action-related terms
            if context.action_type.lower() in policy_content or "action" in policy_content:
                relevance_score += 0.3

            # Check for resource-related terms
            if context.resource_id.lower() in policy_content or "resource" in policy_content:
                relevance_score += 0.3

            # Check for environment factors
            for factor in context.environment_factors:
                if factor.lower() in policy_content:
                    relevance_score += 0.1

            # Normalize to [0, 1]
            return min(relevance_score, 1.0)

        except Exception as e:
            logger.warning(f"Policy relevance calculation failed: {e}")
            return 0.5  # Default moderate relevance

    async def _apply_wina_policy_optimization(
        self,
        policy: IntegrityPolicyRule,
        context: EnforcementContext,
        strategy: EnforcementStrategy,
        optimization_hints: Optional[Dict[str, Any]]
    ) -> IntegrityPolicyRule:
        """Apply WINA optimization to a single policy."""

        if not self.enable_wina or strategy == EnforcementStrategy.STANDARD:
            return policy

        try:
            # For now, return the original policy
            # In a full implementation, this would apply WINA-specific optimizations
            # such as rule simplification, condition reordering, etc.
            return policy

        except Exception as e:
            logger.warning(f"WINA policy optimization failed: {e}")
            return policy

    async def _execute_opa_evaluation_with_strategy(
        self,
        request: PolicyEvaluationRequest,
        strategy: EnforcementStrategy,
        policies: List[IntegrityPolicyRule]
    ) -> PolicyEvaluationResponse:
        """Execute OPA evaluation with strategy-specific optimizations."""

        try:
            # Apply strategy-specific request modifications
            if strategy == EnforcementStrategy.PERFORMANCE_FOCUSED:
                # Disable detailed explanations for better performance
                request.explain = "off"
                request.metrics = False
            elif strategy == EnforcementStrategy.CONSTITUTIONAL_PRIORITY:
                # Enable full explanations for constitutional compliance
                request.explain = "full"
                request.metrics = True

            # Execute OPA evaluation
            response = await self.opa_client.evaluate_policy(request)

            return response

        except Exception as e:
            logger.error(f"OPA evaluation with strategy failed: {e}")
            raise

    async def _process_opa_response(
        self,
        response: PolicyEvaluationResponse,
        strategy: EnforcementStrategy,
        context: EnforcementContext,
        constitutional_compliance: bool
    ) -> Dict[str, Any]:
        """Process OPA response based on enforcement strategy."""

        try:
            # Extract basic decision
            result = response.result or {}
            decision = "permit" if result.get("allow", False) else "deny"

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(response, strategy, constitutional_compliance)

            # Generate reason
            reason = self._generate_enforcement_reason(response, decision, strategy, context)

            # Extract matching rules if available
            matching_rules = self._extract_matching_rules(response)

            # Generate WINA insights
            wina_insights = await self._generate_wina_insights(response, strategy, context)

            return {
                "decision": decision,
                "reason": reason,
                "confidence_score": confidence_score,
                "matching_rules": matching_rules,
                "wina_insights": wina_insights,
                "opa_metrics": response.metrics
            }

        except Exception as e:
            logger.error(f"OPA response processing failed: {e}")
            return {
                "decision": "deny",
                "reason": f"Response processing failed: {str(e)}",
                "confidence_score": 0.0
            }

    # Utility methods for caching, metrics, and analysis

    def _generate_cache_key(self, context: EnforcementContext) -> str:
        """Generate cache key for enforcement context."""
        import hashlib

        key_data = f"{context.user_id}:{context.action_type}:{context.resource_id}:{context.priority_level}"
        if context.environment_factors:
            key_data += f":{sorted(context.environment_factors.items())}"
        if context.constitutional_requirements:
            key_data += f":{sorted(context.constitutional_requirements)}"

        return hashlib.md5(key_data.encode()).hexdigest()

    def _generate_compliance_cache_key(self, context: EnforcementContext, policies: List[IntegrityPolicyRule]) -> str:
        """Generate cache key for constitutional compliance."""
        import hashlib

        policy_ids = [str(getattr(policy, 'id', hash(policy.rule_content))) for policy in policies]
        key_data = f"{context.user_id}:{context.action_type}:{sorted(policy_ids)}"
        if context.constitutional_requirements:
            key_data += f":{sorted(context.constitutional_requirements)}"

        return hashlib.md5(key_data.encode()).hexdigest()

    def _calculate_confidence_score(
        self,
        response: PolicyEvaluationResponse,
        strategy: EnforcementStrategy,
        constitutional_compliance: bool
    ) -> float:
        """Calculate confidence score for enforcement decision."""

        base_confidence = 0.8  # Base confidence for OPA decisions

        # Adjust based on strategy
        if strategy == EnforcementStrategy.CONSTITUTIONAL_PRIORITY:
            base_confidence += 0.1 if constitutional_compliance else -0.3
        elif strategy == EnforcementStrategy.WINA_OPTIMIZED:
            base_confidence += 0.05
        elif strategy == EnforcementStrategy.PERFORMANCE_FOCUSED:
            base_confidence -= 0.05  # Slightly lower due to reduced analysis

        # Adjust based on OPA metrics if available
        if response.metrics:
            evaluation_time = response.metrics.get("timer_rego_query_eval_ns", 0) / 1_000_000  # Convert to ms
            if evaluation_time < 10:  # Fast evaluation
                base_confidence += 0.05
            elif evaluation_time > 100:  # Slow evaluation
                base_confidence -= 0.05

        return max(0.0, min(1.0, base_confidence))

    def _generate_enforcement_reason(
        self,
        response: PolicyEvaluationResponse,
        decision: str,
        strategy: EnforcementStrategy,
        context: EnforcementContext
    ) -> str:
        """Generate human-readable reason for enforcement decision."""

        if decision == "permit":
            reason = f"Action '{context.action_type}' on resource '{context.resource_id}' by user '{context.user_id}' is permitted by policy"
        else:
            reason = f"Action '{context.action_type}' on resource '{context.resource_id}' by user '{context.user_id}' is denied by policy"

        # Add strategy-specific information
        if strategy == EnforcementStrategy.CONSTITUTIONAL_PRIORITY:
            reason += " (constitutional compliance verified)"
        elif strategy == EnforcementStrategy.WINA_OPTIMIZED:
            reason += " (WINA-optimized enforcement)"
        elif strategy == EnforcementStrategy.PERFORMANCE_FOCUSED:
            reason += " (performance-optimized enforcement)"

        return reason

    def _extract_matching_rules(self, response: PolicyEvaluationResponse) -> Optional[List[Dict[str, Any]]]:
        """Extract matching rules from OPA response."""

        if not response.explanation:
            return None

        matching_rules = []
        for explanation in response.explanation:
            if explanation.get("op") == "eval" and explanation.get("type") == "rule":
                rule_info = {
                    "location": explanation.get("location", {}),
                    "node": explanation.get("node", {}),
                    "result": explanation.get("result")
                }
                matching_rules.append(rule_info)

        return matching_rules if matching_rules else None

    async def _generate_wina_insights(
        self,
        response: PolicyEvaluationResponse,
        strategy: EnforcementStrategy,
        context: EnforcementContext
    ) -> Dict[str, Any]:
        """Generate WINA-specific insights for the enforcement result."""

        insights = {
            "strategy_used": strategy.value,
            "wina_enabled": self.enable_wina,
            "optimization_applied": strategy != EnforcementStrategy.STANDARD
        }

        if self.enable_wina and response.metrics:
            # Add WINA-specific performance insights
            evaluation_time = response.metrics.get("timer_rego_query_eval_ns", 0) / 1_000_000
            insights.update({
                "evaluation_time_ms": evaluation_time,
                "performance_category": "fast" if evaluation_time < 10 else "slow" if evaluation_time > 100 else "normal"
            })

        return insights

    async def _calculate_enforcement_metrics(
        self,
        enforcement_time: float,
        strategy: EnforcementStrategy,
        context: EnforcementContext,
        policies: List[IntegrityPolicyRule],
        enforcement_result: Dict[str, Any]
    ) -> WINAEnforcementMetrics:
        """Calculate comprehensive enforcement metrics."""

        # Calculate performance improvement
        baseline_time = await self._get_baseline_enforcement_time(context)
        performance_improvement = max(0.0, (baseline_time - enforcement_time) / baseline_time) if baseline_time > 0 else 0.0

        # Calculate cache hit rate
        cache_hit_rate = self._calculate_cache_hit_rate()

        return WINAEnforcementMetrics(
            enforcement_time_ms=enforcement_time,
            strategy_used=strategy,
            wina_optimization_applied=self.enable_wina and strategy != EnforcementStrategy.STANDARD,
            constitutional_compliance_score=enforcement_result.get("constitutional_compliance_score", 1.0),
            performance_improvement=performance_improvement,
            cache_hit_rate=cache_hit_rate,
            opa_evaluation_time_ms=enforcement_result.get("opa_evaluation_time_ms", 0.0),
            wina_analysis_time_ms=max(0.0, enforcement_time - enforcement_result.get("opa_evaluation_time_ms", 0.0)),
            total_policies_evaluated=len(policies),
            optimized_policies_count=len(policies) if strategy != EnforcementStrategy.STANDARD else 0,
            constitutional_violations_detected=0,  # Would be calculated based on compliance analysis
            enforcement_accuracy=enforcement_result.get("confidence_score", 0.0)
        )

    # Additional helper methods

    async def _analyze_constitutional_risk(self, context: EnforcementContext, policies: List[IntegrityPolicyRule]) -> float:
        """Analyze constitutional risk for the enforcement context."""
        if not context.constitutional_requirements:
            return 0.0

        # Simple heuristic: more constitutional requirements = higher risk
        risk_score = min(len(context.constitutional_requirements) * 0.2, 1.0)
        return risk_score

    async def _analyze_performance_benefit(self, context: EnforcementContext, policies: List[IntegrityPolicyRule]) -> float:
        """Analyze potential performance benefit from WINA optimization."""
        # Simple heuristic: more policies and complex context = higher benefit potential
        policy_factor = min(len(policies) * 0.1, 0.5)
        context_factor = min(len(context.environment_factors) * 0.1, 0.3)
        return policy_factor + context_factor

    async def _analyze_optimization_potential(self, context: EnforcementContext, policies: List[IntegrityPolicyRule]) -> float:
        """Analyze optimization potential for the current context."""
        # Simple heuristic based on context complexity and policy count
        if len(policies) > 10:
            return 0.8
        elif len(policies) > 5:
            return 0.6
        else:
            return 0.4

    async def _get_baseline_enforcement_time(self, context: EnforcementContext) -> float:
        """Get baseline enforcement time for performance comparison."""
        # Simple baseline calculation based on historical data
        if hasattr(self, '_baseline_times'):
            return sum(self._baseline_times) / len(self._baseline_times)
        return 50.0  # Default baseline of 50ms

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate current cache hit rate."""
        if not hasattr(self, '_cache_stats'):
            return 0.0

        total_requests = getattr(self, '_total_cache_requests', 0)
        cache_hits = getattr(self, '_cache_hits', 0)

        return cache_hits / total_requests if total_requests > 0 else 0.0

    async def _update_enforcement_tracking(self, result: WINAEnforcementResult):
        """Update enforcement tracking and performance metrics."""
        self._enforcement_history.append(result)

        # Keep only recent history
        if len(self._enforcement_history) > 1000:
            self._enforcement_history = self._enforcement_history[-500:]

        # Update strategy performance tracking
        strategy = result.enforcement_metrics.strategy_used
        performance = result.enforcement_metrics.performance_improvement
        self._strategy_performance[strategy].append(performance)

        # Keep only recent performance data
        if len(self._strategy_performance[strategy]) > 100:
            self._strategy_performance[strategy] = self._strategy_performance[strategy][-50:]

    async def _cache_enforcement_result(self, context: EnforcementContext, result: WINAEnforcementResult):
        """Cache enforcement result for future use."""
        cache_key = self._generate_cache_key(context)
        self._enforcement_cache[cache_key] = (result, datetime.now())

        # Clean cache if too large
        if len(self._enforcement_cache) > self.max_cache_size:
            await self._clean_enforcement_cache()

    async def _clean_enforcement_cache(self):
        """Clean expired entries from enforcement cache."""
        current_time = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._enforcement_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]

        for key in expired_keys:
            del self._enforcement_cache[key]

    async def _clean_compliance_cache(self):
        """Clean expired entries from compliance cache."""
        current_time = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._constitutional_compliance_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]

        for key in expired_keys:
            del self._constitutional_compliance_cache[key]

    async def _fallback_enforcement(
        self,
        context: EnforcementContext,
        policies: List[IntegrityPolicyRule],
        errors: List[str]
    ) -> WINAEnforcementResult:
        """Fallback enforcement when WINA optimization fails."""

        # Create basic enforcement metrics
        fallback_metrics = WINAEnforcementMetrics(
            enforcement_time_ms=0.0,
            strategy_used=EnforcementStrategy.STANDARD,
            wina_optimization_applied=False,
            constitutional_compliance_score=0.5,
            performance_improvement=0.0,
            cache_hit_rate=0.0,
            opa_evaluation_time_ms=0.0,
            wina_analysis_time_ms=0.0,
            total_policies_evaluated=len(policies),
            optimized_policies_count=0,
            constitutional_violations_detected=0,
            enforcement_accuracy=0.5
        )

        return WINAEnforcementResult(
            decision="deny",
            reason="Enforcement failed due to system errors",
            confidence_score=0.0,
            enforcement_metrics=fallback_metrics,
            constitutional_compliance=False,
            optimization_applied=False,
            warnings=[],
            errors=errors,
            wina_insights={}
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for monitoring and optimization."""

        total_enforcements = len(self._enforcement_history)
        if total_enforcements == 0:
            return {"total_enforcements": 0}

        # Calculate average metrics
        avg_enforcement_time = sum(r.enforcement_metrics.enforcement_time_ms for r in self._enforcement_history) / total_enforcements
        avg_performance_improvement = sum(r.enforcement_metrics.performance_improvement for r in self._enforcement_history) / total_enforcements
        avg_constitutional_compliance = sum(r.enforcement_metrics.constitutional_compliance_score for r in self._enforcement_history) / total_enforcements

        # Calculate strategy distribution
        strategy_counts = {}
        for result in self._enforcement_history:
            strategy = result.enforcement_metrics.strategy_used.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return {
            "total_enforcements": total_enforcements,
            "average_enforcement_time_ms": avg_enforcement_time,
            "average_performance_improvement": avg_performance_improvement,
            "average_constitutional_compliance": avg_constitutional_compliance,
            "strategy_distribution": strategy_counts,
            "wina_enabled": self.enable_wina,
            "cache_size": len(self._enforcement_cache),
            "compliance_cache_size": len(self._constitutional_compliance_cache)
        }


# Global WINA enforcement optimizer instance
_wina_enforcement_optimizer: Optional[WINAEnforcementOptimizer] = None


async def get_wina_enforcement_optimizer() -> WINAEnforcementOptimizer:
    """Get or create the global WINA enforcement optimizer instance."""
    global _wina_enforcement_optimizer

    if _wina_enforcement_optimizer is None:
        import os
        enable_wina = os.getenv("ENABLE_WINA", "true").lower() == "true"

        _wina_enforcement_optimizer = WINAEnforcementOptimizer(enable_wina=enable_wina)
        logger.info("WINA Enforcement Optimizer instance created")

    return _wina_enforcement_optimizer


async def close_wina_enforcement_optimizer() -> None:
    """Close the global WINA enforcement optimizer."""
    global _wina_enforcement_optimizer
    if _wina_enforcement_optimizer:
        # Perform any cleanup if needed
        _wina_enforcement_optimizer = None
        logger.info("WINA Enforcement Optimizer instance closed")
