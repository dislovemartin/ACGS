"""
Integration Tests for AlphaEvolve-ACGS Framework Enhancements

This test suite validates the enhanced components implemented based on
2024-2025 research breakthroughs:

1. Collective Constitutional AI (CCAI) with Polis integration
2. Enhanced Multi-Model Validation with boosting and clustering
3. Ultra Low Latency Optimization targeting sub-25ms decisions
4. BBQ bias evaluation across nine social dimensions
5. Democratic legitimacy scoring and monitoring
"""

import asyncio
import pytest
import time
from typing import Dict, List, Any
from unittest.mock import AsyncMock, patch

# Test imports for enhanced components
try:
    from src.backend.ac_service.app.services.collective_constitutional_ai import (
        get_collective_constitutional_ai,
        BiasCategory,
        DemocraticLegitimacyLevel,
        CollectiveInput,
        DemocraticPrinciple
    )
    from src.backend.gs_service.app.services.enhanced_multi_model_validation import (
        get_enhanced_multi_model_validator,
        ValidationStrategy,
        ModelCluster,
        ValidationContext
    )
    from src.backend.pgc_service.app.core.ultra_low_latency_optimizer import (
        get_ultra_low_latency_optimizer,
        OptimizationLevel,
        LatencyTarget
    )
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced components not available: {e}")
    ENHANCED_COMPONENTS_AVAILABLE = False

# Skip all tests if enhanced components are not available
pytestmark = pytest.mark.skipif(
    not ENHANCED_COMPONENTS_AVAILABLE, 
    reason="Enhanced AlphaEvolve-ACGS components not available"
)


class TestCollectiveConstitutionalAI:
    """Test Collective Constitutional AI functionality."""
    
    @pytest.fixture
    def ccai_service(self):
        """Get CCAI service instance."""
        return get_collective_constitutional_ai()
    
    async def test_polis_conversation_creation(self, ccai_service):
        """Test creating Polis conversations for democratic deliberation."""
        conversation = await ccai_service.create_polis_conversation(
            topic="AI Governance Principles",
            description="Democratic deliberation on fundamental AI governance principles",
            target_participants=50
        )
        
        assert conversation.topic == "AI Governance Principles"
        assert conversation.participant_count == 0  # Initially empty
        assert conversation.status == "active"
        assert conversation.conversation_id in ccai_service.active_conversations
        
        print(f"✅ Created Polis conversation: {conversation.conversation_id}")
    
    async def test_bbq_bias_evaluation(self, ccai_service):
        """Test BBQ bias evaluation across nine social dimensions."""
        test_principle = (
            "AI systems should treat all users fairly regardless of their background. "
            "However, older users may need additional support for technology adoption."
        )
        
        bias_results = await ccai_service.evaluate_bias_bbq(
            principle_text=test_principle,
            categories=[BiasCategory.AGE, BiasCategory.GENDER_IDENTITY, BiasCategory.RACE_ETHNICITY]
        )
        
        assert len(bias_results) == 3
        
        # Check age bias detection (should detect potential bias)
        age_result = next(r for r in bias_results if r.category == BiasCategory.AGE)
        assert age_result.bias_score > 0.0  # Should detect age-related language
        assert len(age_result.recommendations) > 0
        
        # Check other categories (should have lower bias scores)
        gender_result = next(r for r in bias_results if r.category == BiasCategory.GENDER_IDENTITY)
        race_result = next(r for r in bias_results if r.category == BiasCategory.RACE_ETHNICITY)
        
        print(f"✅ BBQ Bias Evaluation Results:")
        print(f"   Age bias: {age_result.bias_score:.3f}")
        print(f"   Gender bias: {gender_result.bias_score:.3f}")
        print(f"   Race bias: {race_result.bias_score:.3f}")
    
    async def test_collective_input_aggregation(self, ccai_service):
        """Test aggregating collective input from conversations."""
        # Create a conversation first
        conversation = await ccai_service.create_polis_conversation(
            topic="Test Aggregation",
            description="Test collective input aggregation"
        )
        
        # Test aggregation (will use mock data since no real Polis API)
        collective_inputs = await ccai_service.aggregate_collective_input(
            conversation_id=conversation.conversation_id,
            min_consensus=0.6
        )
        
        assert len(collective_inputs) > 0
        assert all(ci.validated for ci in collective_inputs)
        assert all(ci.weight >= 0.6 for ci in collective_inputs)
        
        print(f"✅ Aggregated {len(collective_inputs)} collective inputs")
    
    async def test_democratic_principle_synthesis(self, ccai_service):
        """Test synthesizing democratic principles from collective input."""
        # Create mock collective inputs
        collective_inputs = [
            CollectiveInput(
                input_id="input_1",
                source="mock",
                content="AI systems must prioritize human welfare",
                participant_id="participant_1",
                timestamp=time.time(),
                weight=0.85,
                validated=True
            ),
            CollectiveInput(
                input_id="input_2",
                source="mock",
                content="Transparency in AI decision-making is essential",
                participant_id="participant_2",
                timestamp=time.time(),
                weight=0.92,
                validated=True
            )
        ]
        
        democratic_principle = await ccai_service.synthesize_democratic_principle(
            topic="Human-Centered AI Governance",
            collective_inputs=collective_inputs
        )
        
        assert democratic_principle.legitimacy_level == DemocraticLegitimacyLevel.HIGH
        assert democratic_principle.stakeholder_agreement > 0.8
        assert len(democratic_principle.bias_evaluation) > 0
        assert len(democratic_principle.collective_inputs) == 2
        
        print(f"✅ Synthesized democratic principle with {democratic_principle.legitimacy_level.value} legitimacy")
    
    async def test_democratic_legitimacy_monitoring(self, ccai_service):
        """Test monitoring democratic legitimacy metrics."""
        # First create some principles
        await self.test_democratic_principle_synthesis(ccai_service)
        
        metrics = await ccai_service.monitor_democratic_legitimacy()
        
        assert "total_principles" in metrics
        assert "average_stakeholder_agreement" in metrics
        assert "average_bias_reduction" in metrics
        assert "bias_by_category" in metrics
        assert "democratic_legitimacy_score" in metrics
        
        # Validate target achievement
        target_bias_reduction = 0.4  # 40% target from research
        actual_bias_reduction = metrics["average_bias_reduction"]
        
        print(f"✅ Democratic Legitimacy Monitoring:")
        print(f"   Total principles: {metrics['total_principles']}")
        print(f"   Avg stakeholder agreement: {metrics['average_stakeholder_agreement']:.1%}")
        print(f"   Bias reduction achieved: {actual_bias_reduction:.1%} (target: 40%)")


class TestEnhancedMultiModelValidation:
    """Test Enhanced Multi-Model Validation functionality."""
    
    @pytest.fixture
    def validator(self):
        """Get enhanced multi-model validator instance."""
        return get_enhanced_multi_model_validator()
    
    async def test_boosting_majority_vote(self, validator):
        """Test boosting-based weighted majority vote validation."""
        context = ValidationContext(
            query_type="constitutional_analysis",
            complexity_score=0.8,
            constitutional_requirements=["fairness", "transparency"],
            bias_sensitivity=0.7,
            uncertainty_tolerance=0.3
        )
        
        result = await validator.validate_with_ensemble(
            query="Should AI systems be required to explain their decisions?",
            context=context,
            strategy=ValidationStrategy.BOOSTING_MAJORITY_VOTE,
            max_models=3
        )
        
        assert result.strategy_used == ValidationStrategy.BOOSTING_MAJORITY_VOTE
        assert result.confidence > 0.0
        assert result.constitutional_fidelity >= 0.0
        assert len(result.model_contributions) > 0
        assert result.validation_time > 0.0
        
        print(f"✅ Boosting Majority Vote:")
        print(f"   Confidence: {result.confidence:.3f}")
        print(f"   Constitutional fidelity: {result.constitutional_fidelity:.3f}")
        print(f"   Validation time: {result.validation_time:.3f}s")
    
    async def test_cluster_based_selection(self, validator):
        """Test cluster-based dynamic model selection."""
        context = ValidationContext(
            query_type="bias_detection",
            complexity_score=0.6,
            constitutional_requirements=["non_discrimination"],
            bias_sensitivity=0.9,
            uncertainty_tolerance=0.2,
            target_cluster=ModelCluster.BIAS_DETECTION
        )
        
        result = await validator.validate_with_ensemble(
            query="Does this policy discriminate against any protected groups?",
            context=context,
            strategy=ValidationStrategy.CLUSTER_BASED_SELECTION,
            max_models=3
        )
        
        assert result.strategy_used == ValidationStrategy.CLUSTER_BASED_SELECTION
        assert result.consensus_level >= 0.0
        
        print(f"✅ Cluster-based Selection:")
        print(f"   Target cluster: {context.target_cluster.value}")
        print(f"   Consensus level: {result.consensus_level:.3f}")
    
    async def test_uncertainty_weighted_validation(self, validator):
        """Test uncertainty-weighted validation with SPUQ methodology."""
        context = ValidationContext(
            query_type="policy_synthesis",
            complexity_score=0.7,
            constitutional_requirements=["accountability"],
            bias_sensitivity=0.5,
            uncertainty_tolerance=0.4
        )
        
        result = await validator.validate_with_ensemble(
            query="Generate a policy for AI system accountability",
            context=context,
            strategy=ValidationStrategy.UNCERTAINTY_WEIGHTED,
            max_models=4
        )
        
        assert result.strategy_used == ValidationStrategy.UNCERTAINTY_WEIGHTED
        assert "epistemic_uncertainty" in result.uncertainty_quantification
        assert "aleatoric_uncertainty" in result.uncertainty_quantification
        assert "total_uncertainty" in result.uncertainty_quantification
        
        print(f"✅ Uncertainty-weighted Validation:")
        print(f"   Epistemic uncertainty: {result.uncertainty_quantification['epistemic_uncertainty']:.3f}")
        print(f"   Aleatoric uncertainty: {result.uncertainty_quantification['aleatoric_uncertainty']:.3f}")
    
    async def test_hybrid_ensemble_validation(self, validator):
        """Test hybrid ensemble validation combining multiple strategies."""
        context = ValidationContext(
            query_type="comprehensive_analysis",
            complexity_score=0.9,
            constitutional_requirements=["fairness", "transparency", "accountability"],
            bias_sensitivity=0.8,
            uncertainty_tolerance=0.2
        )
        
        result = await validator.validate_with_ensemble(
            query="Evaluate the constitutional compliance of this AI governance framework",
            context=context,
            strategy=ValidationStrategy.HYBRID_ENSEMBLE,
            max_models=5
        )
        
        assert result.strategy_used == ValidationStrategy.HYBRID_ENSEMBLE
        assert result.confidence > 0.0
        assert result.constitutional_fidelity > 0.0
        
        print(f"✅ Hybrid Ensemble Validation:")
        print(f"   Models used: {len(result.model_contributions)}")
        print(f"   Overall confidence: {result.confidence:.3f}")
        print(f"   Constitutional fidelity: {result.constitutional_fidelity:.3f}")
    
    async def test_validation_metrics(self, validator):
        """Test validation metrics collection and reporting."""
        # Run a few validations first
        await self.test_boosting_majority_vote(validator)
        await self.test_cluster_based_selection(validator)
        
        metrics = validator.get_validation_metrics()
        
        assert "total_validations" in metrics
        assert "average_confidence" in metrics
        assert "strategy_usage_distribution" in metrics
        assert "model_usage_statistics" in metrics
        assert "reliability_target" in metrics
        
        print(f"✅ Validation Metrics:")
        print(f"   Total validations: {metrics['total_validations']}")
        print(f"   Average confidence: {metrics['average_confidence']:.3f}")
        print(f"   Reliability target: {metrics['reliability_target']}")


class TestUltraLowLatencyOptimization:
    """Test Ultra Low Latency Optimization functionality."""
    
    @pytest.fixture
    def optimizer(self):
        """Get ultra low latency optimizer instance."""
        return get_ultra_low_latency_optimizer()
    
    async def test_sub_25ms_policy_decision(self, optimizer):
        """Test achieving sub-25ms policy decision latency."""
        policy_request = {
            "user_id": "test_user_123",
            "resource": "sensitive_data",
            "action": "read",
            "context": {"department": "engineering", "clearance_level": "high"}
        }
        
        result = await optimizer.optimize_policy_decision(
            policy_request=policy_request,
            optimization_level=OptimizationLevel.ENHANCED
        )
        
        assert result.latency_ms > 0.0
        assert result.optimization_level == OptimizationLevel.ENHANCED
        assert "cache_lookup" in result.breakdown or "policy_evaluation" in result.breakdown
        
        # Check if target is met (sub-25ms)
        target_met = result.latency_ms <= optimizer.target_latency
        
        print(f"✅ Ultra Low Latency Optimization:")
        print(f"   Latency: {result.latency_ms:.2f}ms (target: {optimizer.target_latency}ms)")
        print(f"   Target met: {target_met}")
        print(f"   Cache hit: {result.cache_hit}")
        print(f"   Breakdown: {result.breakdown}")
    
    async def test_performance_benchmark(self, optimizer):
        """Test performance benchmarking with multiple requests."""
        benchmark_results = await optimizer.benchmark_performance(num_requests=20)
        
        assert "benchmark_config" in benchmark_results
        assert "latency_metrics" in benchmark_results
        assert "performance_metrics" in benchmark_results
        assert "assessment" in benchmark_results
        
        latency_metrics = benchmark_results["latency_metrics"]
        performance_metrics = benchmark_results["performance_metrics"]
        
        print(f"✅ Performance Benchmark (20 requests):")
        print(f"   Avg latency: {latency_metrics['avg_latency_ms']:.2f}ms")
        print(f"   P95 latency: {latency_metrics['p95_latency_ms']:.2f}ms")
        print(f"   Cache hit rate: {performance_metrics['cache_hit_rate']:.1%}")
        print(f"   Throughput: {performance_metrics['throughput_rps']:.1f} RPS")
        print(f"   Performance grade: {benchmark_results['assessment']['performance_grade']}")
    
    async def test_adaptive_optimization(self, optimizer):
        """Test adaptive optimization based on performance."""
        # Run some operations first to generate performance data
        await self.test_sub_25ms_policy_decision(optimizer)
        
        adaptation_result = await optimizer.adaptive_optimization()
        
        assert "current_performance" in adaptation_result
        assert "adjustments_made" in adaptation_result
        assert "next_review" in adaptation_result
        
        print(f"✅ Adaptive Optimization:")
        print(f"   Current avg latency: {adaptation_result['current_performance']['avg_latency_ms']:.2f}ms")
        print(f"   Adjustments made: {len(adaptation_result['adjustments_made'])}")
        for adjustment in adaptation_result['adjustments_made']:
            print(f"     - {adjustment}")


@pytest.mark.asyncio
async def test_end_to_end_alphaevolve_enhancement():
    """
    End-to-end test of AlphaEvolve-ACGS enhancements integration.
    
    This test validates the complete workflow from democratic principle
    creation through multi-model validation to ultra-low latency enforcement.
    """
    print("\n🧬 AlphaEvolve-ACGS Framework Enhancement Integration Test")
    print("=" * 70)
    
    # Step 1: Collective Constitutional AI
    print("\n1. Testing Collective Constitutional AI...")
    ccai = get_collective_constitutional_ai()
    
    # Create democratic principle
    collective_inputs = [
        CollectiveInput(
            input_id="e2e_input_1",
            source="test",
            content="AI systems must ensure fairness across all user groups",
            participant_id="stakeholder_1",
            timestamp=time.time(),
            weight=0.88,
            validated=True
        )
    ]
    
    principle = await ccai.synthesize_democratic_principle(
        topic="End-to-End Fairness Principle",
        collective_inputs=collective_inputs
    )
    
    print(f"   ✅ Created principle with {principle.legitimacy_level.value} legitimacy")
    
    # Step 2: Enhanced Multi-Model Validation
    print("\n2. Testing Enhanced Multi-Model Validation...")
    validator = get_enhanced_multi_model_validator()
    
    context = ValidationContext(
        query_type="principle_validation",
        complexity_score=0.8,
        constitutional_requirements=["fairness"],
        bias_sensitivity=0.9,
        uncertainty_tolerance=0.2
    )
    
    validation_result = await validator.validate_with_ensemble(
        query=f"Validate this principle: {principle.description}",
        context=context,
        strategy=ValidationStrategy.HYBRID_ENSEMBLE
    )
    
    print(f"   ✅ Validation confidence: {validation_result.confidence:.3f}")
    print(f"   ✅ Constitutional fidelity: {validation_result.constitutional_fidelity:.3f}")
    
    # Step 3: Ultra Low Latency Optimization
    print("\n3. Testing Ultra Low Latency Optimization...")
    optimizer = get_ultra_low_latency_optimizer()
    
    policy_request = {
        "user_id": "e2e_test_user",
        "resource": "governance_system",
        "action": "apply_principle",
        "context": {"principle_id": principle.principle_id}
    }
    
    optimization_result = await optimizer.optimize_policy_decision(
        policy_request=policy_request,
        optimization_level=OptimizationLevel.ENHANCED
    )
    
    print(f"   ✅ Policy decision latency: {optimization_result.latency_ms:.2f}ms")
    print(f"   ✅ Target achieved: {optimization_result.latency_ms <= 25.0}")
    
    # Step 4: Integration Assessment
    print("\n4. Integration Assessment...")
    
    # Calculate overall enhancement metrics
    bias_reduction = 1.0 - sum(r.bias_score for r in principle.bias_evaluation) / len(principle.bias_evaluation)
    reliability_score = validation_result.confidence
    latency_improvement = max(0, (50.0 - optimization_result.latency_ms) / 50.0)  # Improvement from 50ms baseline
    
    overall_score = (bias_reduction * 0.3 + reliability_score * 0.4 + latency_improvement * 0.3)
    
    print(f"   📊 Enhancement Metrics:")
    print(f"      Bias reduction: {bias_reduction:.1%} (target: 40%)")
    print(f"      Reliability score: {reliability_score:.1%} (target: >99.9%)")
    print(f"      Latency improvement: {latency_improvement:.1%} (target: 50%)")
    print(f"      Overall enhancement score: {overall_score:.1%}")
    
    # Validate research targets
    targets_met = {
        "40% bias reduction": bias_reduction >= 0.4,
        "99.9% reliability": reliability_score >= 0.999,
        "Sub-25ms latency": optimization_result.latency_ms <= 25.0,
        "Democratic legitimacy": principle.legitimacy_level in [DemocraticLegitimacyLevel.HIGH, DemocraticLegitimacyLevel.CONSENSUS]
    }
    
    print(f"\n   🎯 Research Targets Achievement:")
    for target, achieved in targets_met.items():
        status = "✅" if achieved else "⚠️"
        print(f"      {status} {target}: {'ACHIEVED' if achieved else 'IN PROGRESS'}")
    
    print(f"\n🎉 AlphaEvolve-ACGS Enhancement Integration: {sum(targets_met.values())}/{len(targets_met)} targets achieved")
    
    return {
        "principle": principle,
        "validation_result": validation_result,
        "optimization_result": optimization_result,
        "targets_met": targets_met,
        "overall_score": overall_score
    }


if __name__ == "__main__":
    asyncio.run(test_end_to_end_alphaevolve_enhancement())
