#!/usr/bin/env python3
"""
Test script for Enhanced LLM Reliability Framework

This script demonstrates the enhanced LLM reliability framework capabilities
and validates that it achieves the >99.9% reliability target.
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_reliability_framework():
    """Test the enhanced LLM reliability framework."""
    try:
        # Import the enhanced framework
        from backend.gs_service.app.core.llm_reliability_framework import (
            EnhancedLLMReliabilityFramework,
            LLMReliabilityConfig,
            ReliabilityLevel
        )
        from backend.gs_service.app.schemas import LLMInterpretationInput
        
        print("🚀 Testing Enhanced LLM Reliability Framework")
        print("=" * 60)
        
        # Create enhanced configuration for >99.9% reliability
        config = LLMReliabilityConfig(
            target_reliability=ReliabilityLevel.SAFETY_CRITICAL,
            reliability_target=0.999,  # >99.9% target
            bias_detection_enabled=True,
            semantic_validation_enabled=True,
            multi_model_validation_enabled=True,
            ensemble_voting_enabled=True,
            counterfactual_testing_enabled=True,
            proactive_bias_mitigation=True,
            nli_validation_enabled=True,
            prometheus_metrics_enabled=True,
            cache_enabled=True
        )
        
        print(f"✅ Configuration created with {config.reliability_target:.1%} reliability target")
        
        # Initialize the enhanced framework
        framework = EnhancedLLMReliabilityFramework(config)
        await framework.initialize()
        
        print("✅ Enhanced LLM Reliability Framework initialized")
        
        # Test cases for reliability validation
        test_cases = [
            {
                "name": "Basic Constitutional Principle",
                "principle_id": "test_001",
                "principle_text": "All users shall have equal access to system resources regardless of their background",
                "context": "access_control"
            },
            {
                "name": "Privacy Protection Principle",
                "principle_id": "test_002", 
                "principle_text": "User privacy must be protected through appropriate data handling measures",
                "context": "data_protection"
            },
            {
                "name": "Fairness and Non-discrimination",
                "principle_id": "test_003",
                "principle_text": "The system shall not discriminate based on demographic characteristics",
                "context": "fairness"
            },
            {
                "name": "Transparency and Accountability",
                "principle_id": "test_004",
                "principle_text": "All system decisions must be transparent and auditable",
                "context": "transparency"
            },
            {
                "name": "Security and Safety",
                "principle_id": "test_005",
                "principle_text": "System security measures must protect against unauthorized access",
                "context": "security"
            }
        ]
        
        print(f"\n🧪 Running {len(test_cases)} test cases...")
        print("-" * 60)
        
        reliability_scores = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case['name']}")
            
            # Create input data
            input_data = LLMInterpretationInput(
                principle_id=test_case["principle_id"],
                principle_text=test_case["principle_text"],
                context=test_case["context"]
            )
            
            # Process with enhanced reliability framework
            output, metrics = await framework.process_with_reliability(input_data)
            
            # Calculate reliability score
            reliability_score = metrics.overall_reliability_score()
            reliability_scores.append(reliability_score)
            
            print(f"  📊 Reliability Score: {reliability_score:.4f} ({reliability_score:.2%})")
            print(f"  📈 Success Rate: {metrics.success_rate:.3f}")
            print(f"  🤝 Consensus Rate: {metrics.consensus_rate:.3f}")
            print(f"  🛡️  Bias Detection Rate: {metrics.bias_detection_rate:.3f}")
            print(f"  🎯 Semantic Faithfulness: {metrics.semantic_faithfulness_score:.3f}")
            print(f"  ⚡ Response Time: {metrics.average_response_time:.3f}s")
            
            # Check if individual test meets reliability target
            target_met = "✅" if reliability_score >= config.reliability_target else "❌"
            print(f"  🎯 Target Achievement: {target_met} ({reliability_score:.2%} vs {config.reliability_target:.1%})")
        
        # Calculate overall framework performance
        print("\n" + "=" * 60)
        print("📊 OVERALL FRAMEWORK PERFORMANCE")
        print("=" * 60)
        
        overall_reliability = framework.get_overall_reliability()
        performance_summary = framework.get_performance_summary()
        reliability_trend = framework.get_reliability_trend()
        
        print(f"🎯 Overall Reliability: {overall_reliability:.4f} ({overall_reliability:.2%})")
        print(f"📈 Target Achievement: {'✅ PASSED' if overall_reliability >= config.reliability_target else '❌ FAILED'}")
        print(f"📊 Average Success Rate: {performance_summary['metrics']['avg_success_rate']:.3f}")
        print(f"🤝 Average Consensus Rate: {performance_summary['metrics']['avg_consensus_rate']:.3f}")
        print(f"🛡️  Average Bias Detection: {performance_summary['metrics']['avg_bias_detection_rate']:.3f}")
        print(f"🎯 Average Semantic Faithfulness: {performance_summary['metrics']['avg_semantic_faithfulness']:.3f}")
        print(f"⚡ Average Response Time: {performance_summary['metrics']['avg_response_time']:.3f}s")
        print(f"💾 Cache Hit Rate: {performance_summary['metrics']['cache_hit_rate']:.3f}")
        print(f"📈 Reliability Trend: {reliability_trend['trend']} ({reliability_trend['direction']})")
        
        # Detailed feature analysis
        print(f"\n🔧 ENHANCED FEATURES STATUS")
        print("-" * 60)
        print(f"🔄 Multi-Model Validation: {'✅ Enabled' if config.multi_model_validation_enabled else '❌ Disabled'}")
        print(f"🛡️  Proactive Bias Mitigation: {'✅ Enabled' if config.proactive_bias_mitigation else '❌ Disabled'}")
        print(f"🧠 NLI Validation: {'✅ Enabled' if config.nli_validation_enabled else '❌ Disabled'}")
        print(f"🔄 Counterfactual Testing: {'✅ Enabled' if config.counterfactual_testing_enabled else '❌ Disabled'}")
        print(f"📊 Prometheus Metrics: {'✅ Enabled' if config.prometheus_metrics_enabled else '❌ Disabled'}")
        print(f"💾 Redis Caching: {'✅ Enabled' if config.cache_enabled else '❌ Disabled'}")
        
        # Final assessment
        print(f"\n🏆 FINAL ASSESSMENT")
        print("=" * 60)
        
        if overall_reliability >= config.reliability_target:
            print(f"🎉 SUCCESS: Enhanced LLM Reliability Framework achieves {overall_reliability:.2%} reliability")
            print(f"✅ Target of {config.reliability_target:.1%} reliability has been MET")
            print("🚀 Framework is ready for safety-critical applications")
        else:
            print(f"⚠️  WARNING: Enhanced LLM Reliability Framework achieves {overall_reliability:.2%} reliability")
            print(f"❌ Target of {config.reliability_target:.1%} reliability has NOT been met")
            print("🔧 Additional tuning may be required")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 60)
        if overall_reliability >= 0.995:
            print("✅ Excellent reliability achieved - framework ready for production")
        elif overall_reliability >= 0.99:
            print("✅ Good reliability achieved - minor optimizations recommended")
        elif overall_reliability >= 0.95:
            print("⚠️  Moderate reliability - consider enabling more advanced features")
        else:
            print("❌ Low reliability - significant improvements needed")
        
        return overall_reliability >= config.reliability_target
        
    except Exception as e:
        logger.error(f"Error testing enhanced reliability framework: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🔬 Enhanced LLM Reliability Framework Test Suite")
    print("=" * 60)
    
    success = await test_enhanced_reliability_framework()
    
    if success:
        print("\n🎉 All tests PASSED - Enhanced LLM Reliability Framework is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Tests FAILED - Please check the implementation")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
