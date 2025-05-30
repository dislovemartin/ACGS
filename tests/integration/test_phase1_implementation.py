#!/usr/bin/env python3
"""
Test script for ACGS-PGP Phase 1 Implementation

This script tests the three main Phase 1 components:
1. Enhanced Principle Management
2. Constitutional Prompting
3. Basic Contextual Analysis
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_enhanced_principle_management():
    """Test the enhanced principle management features."""
    print("\n" + "="*60)
    print("TESTING ENHANCED PRINCIPLE MANAGEMENT")
    print("="*60)
    
    try:
        # Import the enhanced schemas and models
        from backend.ac_service.app import schemas
        from backend.shared.models import Principle
        
        # Test enhanced principle schema
        print("✓ Testing enhanced principle schema...")
        
        enhanced_principle_data = {
            "name": "Test Safety Principle",
            "description": "A test principle for safety validation",
            "content": "AI systems must prioritize user safety in all operations",
            "priority_weight": 0.9,
            "scope": ["healthcare", "autonomous_systems", "critical_infrastructure"],
            "normative_statement": "SHALL ensure user safety is never compromised",
            "constraints": {
                "mandatory_checks": ["safety_validation", "risk_assessment"],
                "prohibited_actions": ["unsafe_operations"]
            },
            "rationale": "User safety is paramount in AI system operations",
            "keywords": ["safety", "user_protection", "risk_mitigation"],
            "category": "Safety",
            "validation_criteria_nl": "System must pass safety validation tests",
            "constitutional_metadata": {
                "constitutional_level": "fundamental",
                "enforcement_priority": "critical"
            }
        }
        
        # Create principle using enhanced schema
        principle_create = schemas.PrincipleCreate(**enhanced_principle_data)
        print(f"✓ Enhanced principle schema validation passed")
        print(f"  - Priority weight: {principle_create.priority_weight}")
        print(f"  - Scope: {principle_create.scope}")
        print(f"  - Category: {principle_create.category}")
        print(f"  - Keywords: {principle_create.keywords}")
        
        # Test principle update schema
        principle_update = schemas.PrincipleUpdate(
            priority_weight=0.95,
            scope=["healthcare", "autonomous_systems"],
            category="Critical_Safety"
        )
        print(f"✓ Enhanced principle update schema validation passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Enhanced principle management test failed: {e}")
        return False

async def test_constitutional_prompting():
    """Test the constitutional prompting functionality."""
    print("\n" + "="*60)
    print("TESTING CONSTITUTIONAL PROMPTING")
    print("="*60)
    
    try:
        # Import constitutional prompting components
        from backend.gs_service.app.core.constitutional_prompting import constitutional_prompt_builder
        from backend.gs_service.app.schemas import ConstitutionalSynthesisInput
        
        print("✓ Testing constitutional prompt builder...")
        
        # Test constitutional context building
        print("  - Building constitutional context...")
        constitutional_context = await constitutional_prompt_builder.build_constitutional_context(
            context="healthcare_ai_systems",
            category="Safety"
        )
        
        print(f"✓ Constitutional context built successfully")
        print(f"  - Context: {constitutional_context['context']}")
        print(f"  - Principle count: {constitutional_context['principle_count']}")
        print(f"  - Has constitutional hierarchy: {'constitutional_hierarchy' in constitutional_context}")
        
        # Test constitutional prompt building
        print("  - Building constitutional prompt...")
        synthesis_request = "Generate governance rules for AI-powered medical diagnosis systems"
        
        constitutional_prompt = constitutional_prompt_builder.build_constitutional_prompt(
            constitutional_context=constitutional_context,
            synthesis_request=synthesis_request,
            target_format="datalog"
        )
        
        print(f"✓ Constitutional prompt built successfully")
        print(f"  - Prompt length: {len(constitutional_prompt)} characters")
        print(f"  - Contains constitutional preamble: {'CONSTITUTIONAL FRAMEWORK' in constitutional_prompt}")
        print(f"  - Contains synthesis request: {synthesis_request[:50] in constitutional_prompt}")
        
        # Test constitutional synthesis input schema
        synthesis_input = ConstitutionalSynthesisInput(
            context="healthcare_ai_systems",
            category="Safety",
            synthesis_request=synthesis_request,
            target_format="datalog"
        )
        
        print(f"✓ Constitutional synthesis input schema validation passed")
        print(f"  - Context: {synthesis_input.context}")
        print(f"  - Target format: {synthesis_input.target_format}")
        
        return True
        
    except Exception as e:
        print(f"✗ Constitutional prompting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_contextual_analysis():
    """Test the basic contextual analysis functionality."""
    print("\n" + "="*60)
    print("TESTING BASIC CONTEXTUAL ANALYSIS")
    print("="*60)
    
    try:
        # Import contextual analysis components
        from backend.gs_service.app.core.contextual_analyzer import contextual_analyzer, EnvironmentalFactor
        
        print("✓ Testing contextual analyzer...")
        
        # Test environmental factor creation
        print("  - Adding environmental factors...")
        
        factors = [
            EnvironmentalFactor(
                factor_id="gdpr_compliance_2024",
                factor_type="regulatory",
                value="GDPR compliance requirements updated for AI systems",
                source="eu_regulation",
                confidence=0.95
            ),
            EnvironmentalFactor(
                factor_id="healthcare_security_standard",
                factor_type="technical",
                value="New healthcare data security standards implemented",
                source="healthcare_authority",
                confidence=0.9
            ),
            EnvironmentalFactor(
                factor_id="user_privacy_concerns",
                factor_type="social",
                value="Increased user concerns about AI privacy",
                source="user_feedback",
                confidence=0.8
            )
        ]
        
        for factor in factors:
            contextual_analyzer.add_environmental_factor(factor)
        
        print(f"✓ Added {len(factors)} environmental factors")
        
        # Test contextual analysis
        print("  - Performing contextual analysis...")
        
        analysis_result = contextual_analyzer.analyze_context(
            context="healthcare_ai_systems",
            additional_data={"system_type": "medical_diagnosis", "deployment": "hospital"}
        )
        
        print(f"✓ Contextual analysis completed successfully")
        print(f"  - Context: {analysis_result['context']}")
        print(f"  - Relevant factors: {len(analysis_result['relevant_factors'])}")
        print(f"  - Similar contexts: {len(analysis_result['similar_contexts'])}")
        print(f"  - Recommendations: {len(analysis_result['recommendations'])}")
        
        # Test adaptation triggers
        print("  - Getting adaptation triggers...")
        
        triggers = contextual_analyzer.get_context_adaptation_triggers("healthcare_ai_systems")
        
        print(f"✓ Adaptation triggers retrieved successfully")
        print(f"  - Immediate triggers: {len(triggers['immediate_triggers'])}")
        print(f"  - Scheduled triggers: {len(triggers['scheduled_triggers'])}")
        print(f"  - Conditional triggers: {len(triggers['conditional_triggers'])}")
        
        # Test factor retrieval by type
        regulatory_factors = contextual_analyzer.get_environmental_factors_by_type("regulatory")
        print(f"✓ Retrieved {len(regulatory_factors)} regulatory factors")
        
        return True
        
    except Exception as e:
        print(f"✗ Contextual analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration():
    """Test integration between the Phase 1 components."""
    print("\n" + "="*60)
    print("TESTING PHASE 1 INTEGRATION")
    print("="*60)
    
    try:
        # Import integration components
        from backend.gs_service.app.core.llm_integration import query_llm_for_constitutional_synthesis
        from backend.gs_service.app.schemas import ConstitutionalSynthesisInput
        
        print("✓ Testing integrated constitutional synthesis...")
        
        # Create a comprehensive synthesis request
        synthesis_input = ConstitutionalSynthesisInput(
            context="financial_ai_systems",
            category="Privacy",
            synthesis_request="Generate governance rules for AI-powered financial advisory systems that handle sensitive customer data",
            target_format="datalog"
        )
        
        # Perform constitutional synthesis (will use mock LLM)
        print("  - Performing constitutional synthesis...")
        synthesis_result = await query_llm_for_constitutional_synthesis(synthesis_input)
        
        print(f"✓ Constitutional synthesis completed successfully")
        print(f"  - Context: {synthesis_result.context}")
        print(f"  - Generated rules: {len(synthesis_result.generated_rules)}")
        print(f"  - Constitutional context principles: {synthesis_result.constitutional_context.get('principle_count', 0)}")
        print(f"  - Synthesis method: {synthesis_result.synthesis_metadata.get('synthesis_method', 'unknown')}")
        
        # Validate generated rules have constitutional compliance info
        if synthesis_result.generated_rules:
            first_rule = synthesis_result.generated_rules[0]
            print(f"  - First rule format: {first_rule.rule_format}")
            print(f"  - Constitutional compliance entries: {len(first_rule.constitutional_compliance)}")
            print(f"  - Rule confidence: {first_rule.confidence}")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all Phase 1 tests."""
    print("ACGS-PGP Phase 1 Implementation Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    
    test_results = []
    
    # Run individual component tests
    test_results.append(("Enhanced Principle Management", await test_enhanced_principle_management()))
    test_results.append(("Constitutional Prompting", await test_constitutional_prompting()))
    test_results.append(("Basic Contextual Analysis", await test_contextual_analysis()))
    test_results.append(("Phase 1 Integration", await test_integration()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 1 components are working correctly!")
        return 0
    else:
        print("⚠️  Some Phase 1 components need attention.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
