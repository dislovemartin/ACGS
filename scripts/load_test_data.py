#!/usr/bin/env python3
"""
Test Data Loading for ACGS-PGP Comprehensive Workflow Validation
Loads comprehensive test datasets for all Phase 1-3 components
"""

import asyncio
import json
import requests
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class TestDataLoader:
    def __init__(self):
        self.base_url = "http://localhost:8001"  # AC Service
        self.gs_url = "http://localhost:8004"    # GS Service
        self.integrity_url = "http://localhost:8002"  # Integrity Service
        self.tokens = self.load_auth_tokens()
        
    def load_auth_tokens(self) -> Dict[str, str]:
        """Load authentication tokens from file"""
        try:
            with open("auth_tokens.json", "r") as f:
                data = json.load(f)
                return data.get("tokens", {})
        except FileNotFoundError:
            print("⚠️  auth_tokens.json not found. Run setup_production_auth.py first")
            return {"admin": "admin_token"}  # Fallback
    
    def get_auth_headers(self, role: str = "admin") -> Dict[str, str]:
        """Get authorization headers for API calls"""
        token = self.tokens.get(role, "admin_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async def load_ac_principles(self):
        """Load AC principles test data"""
        print("📋 Loading AC Principles Test Data...")
        
        principles = [
            {
                "name": "AI Safety Principle",
                "description": "Ensure AI systems operate safely and do not cause harm to humans or society",
                "priority_weight": 0.95,
                "scope": ["healthcare", "autonomous_systems", "critical_infrastructure"],
                "normative_statement": "AI systems must implement fail-safe mechanisms and undergo rigorous safety testing",
                "constraints": ["no_harm", "human_oversight", "explainable_decisions"],
                "rationale": "Safety is paramount in AI systems that can impact human lives and critical infrastructure",
                "category": "Safety",
                "keywords": ["safety", "harm_prevention", "fail_safe", "testing"],
                "validation_criteria_nl": "System must demonstrate safe operation under normal and edge case conditions"
            },
            {
                "name": "Privacy Protection Principle", 
                "description": "Protect individual privacy and personal data in AI systems",
                "priority_weight": 0.90,
                "scope": ["healthcare", "financial_services", "personal_data"],
                "normative_statement": "AI systems must implement privacy-by-design and minimize data collection",
                "constraints": ["data_minimization", "consent_required", "anonymization"],
                "rationale": "Privacy is a fundamental right that must be preserved in AI systems",
                "category": "Privacy",
                "keywords": ["privacy", "data_protection", "consent", "anonymization"],
                "validation_criteria_nl": "System must demonstrate compliance with privacy regulations and data protection standards"
            },
            {
                "name": "Fairness and Non-Discrimination",
                "description": "Ensure AI systems treat all individuals fairly without bias or discrimination",
                "priority_weight": 0.85,
                "scope": ["hiring", "lending", "criminal_justice", "healthcare"],
                "normative_statement": "AI systems must be tested for bias and implement fairness measures",
                "constraints": ["bias_testing", "demographic_parity", "equal_opportunity"],
                "rationale": "AI systems must not perpetuate or amplify societal biases and discrimination",
                "category": "Fairness",
                "keywords": ["fairness", "bias", "discrimination", "equality"],
                "validation_criteria_nl": "System must pass bias testing and demonstrate fair outcomes across demographic groups"
            },
            {
                "name": "Transparency and Explainability",
                "description": "AI systems must be transparent and provide explainable decisions",
                "priority_weight": 0.80,
                "scope": ["high_stakes_decisions", "public_sector", "healthcare", "finance"],
                "normative_statement": "AI systems must provide clear explanations for their decisions and operations",
                "constraints": ["explainable_ai", "decision_transparency", "audit_trails"],
                "rationale": "Users and stakeholders have the right to understand how AI systems make decisions",
                "category": "Transparency",
                "keywords": ["transparency", "explainability", "interpretability", "audit"],
                "validation_criteria_nl": "System must provide clear, understandable explanations for its decisions"
            },
            {
                "name": "Human Oversight and Control",
                "description": "Maintain meaningful human oversight and control over AI systems",
                "priority_weight": 0.88,
                "scope": ["autonomous_systems", "critical_decisions", "healthcare", "defense"],
                "normative_statement": "AI systems must include mechanisms for human oversight and intervention",
                "constraints": ["human_in_the_loop", "override_capability", "escalation_procedures"],
                "rationale": "Humans must retain ultimate control and responsibility for AI system decisions",
                "category": "Human_Control",
                "keywords": ["human_oversight", "control", "intervention", "responsibility"],
                "validation_criteria_nl": "System must demonstrate effective human oversight and intervention capabilities"
            }
        ]
        
        created_principles = []
        for principle in principles:
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/principles/",
                    json=principle,
                    headers=self.get_auth_headers(),
                    timeout=10
                )
                
                if response.status_code == 201:
                    created = response.json()
                    created_principles.append(created)
                    print(f"  ✅ Created principle: {principle['name']}")
                elif response.status_code == 400 and "already exists" in response.text:
                    print(f"  ℹ️  Principle already exists: {principle['name']}")
                else:
                    print(f"  ❌ Failed to create principle {principle['name']}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Error creating principle {principle['name']}: {str(e)}")
        
        return created_principles
    
    async def load_constitutional_council_data(self):
        """Load Constitutional Council test data"""
        print("\n🏛️ Loading Constitutional Council Test Data...")
        
        # Meta-rules
        meta_rules = [
            {
                "rule_name": "Principle Priority Resolution",
                "rule_description": "When principles conflict, higher priority principles take precedence",
                "rule_type": "conflict_resolution",
                "rule_content": "IF conflict(principle_a, principle_b) AND priority(principle_a) > priority(principle_b) THEN apply(principle_a)",
                "applicable_contexts": ["all"],
                "precedence_level": 1
            },
            {
                "rule_name": "Safety Override Rule",
                "rule_description": "Safety principles always override other considerations in critical systems",
                "rule_type": "safety_override", 
                "rule_content": "IF context = critical_system AND principle_type = safety THEN override_all_other_principles",
                "applicable_contexts": ["healthcare", "autonomous_systems", "critical_infrastructure"],
                "precedence_level": 0
            }
        ]
        
        for meta_rule in meta_rules:
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/constitutional-council/meta-rules",
                    json=meta_rule,
                    headers=self.get_auth_headers("council_member"),
                    timeout=10
                )
                
                if response.status_code == 201:
                    print(f"  ✅ Created meta-rule: {meta_rule['rule_name']}")
                else:
                    print(f"  ❌ Failed to create meta-rule: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Error creating meta-rule: {str(e)}")
    
    async def load_environmental_factors(self):
        """Load environmental factors for contextual analysis"""
        print("\n🌍 Loading Environmental Factors...")
        
        factors = [
            {
                "factor_name": "GDPR Compliance 2024",
                "factor_type": "regulatory",
                "description": "Updated GDPR requirements for AI systems",
                "applicable_contexts": ["healthcare", "finance", "personal_data"],
                "impact_level": "high",
                "last_updated": datetime.now().isoformat()
            },
            {
                "factor_name": "Healthcare Security Standards",
                "factor_type": "technical",
                "description": "HIPAA and healthcare-specific security requirements",
                "applicable_contexts": ["healthcare"],
                "impact_level": "critical",
                "last_updated": datetime.now().isoformat()
            },
            {
                "factor_name": "Public Trust Concerns",
                "factor_type": "social",
                "description": "Growing public concern about AI bias and fairness",
                "applicable_contexts": ["public_sector", "hiring", "criminal_justice"],
                "impact_level": "medium",
                "last_updated": datetime.now().isoformat()
            }
        ]
        
        # Save to file for contextual analyzer
        with open("test_environmental_factors.json", "w") as f:
            json.dump(factors, f, indent=2)
        
        print("  ✅ Environmental factors saved to test_environmental_factors.json")
    
    async def create_test_scenarios(self):
        """Create comprehensive test scenarios"""
        print("\n🧪 Creating Test Scenarios...")
        
        scenarios = [
            {
                "scenario_name": "Healthcare AI Diagnosis System",
                "context": "healthcare_ai_systems",
                "description": "AI system for medical diagnosis and treatment recommendations",
                "applicable_principles": ["AI Safety Principle", "Privacy Protection Principle", "Transparency and Explainability"],
                "test_cases": [
                    "Patient data privacy protection",
                    "Diagnostic accuracy and safety",
                    "Explainable treatment recommendations",
                    "Bias testing across demographic groups"
                ]
            },
            {
                "scenario_name": "Autonomous Vehicle Control",
                "context": "autonomous_systems",
                "description": "Self-driving vehicle decision-making system",
                "applicable_principles": ["AI Safety Principle", "Human Oversight and Control"],
                "test_cases": [
                    "Emergency braking decisions",
                    "Human override capabilities",
                    "Ethical dilemma resolution",
                    "Safety in edge cases"
                ]
            },
            {
                "scenario_name": "Financial Lending Algorithm",
                "context": "financial_ai_systems",
                "description": "AI system for loan approval and risk assessment",
                "applicable_principles": ["Fairness and Non-Discrimination", "Transparency and Explainability"],
                "test_cases": [
                    "Bias testing across demographic groups",
                    "Explainable loan decisions",
                    "Fair lending compliance",
                    "Risk assessment transparency"
                ]
            }
        ]
        
        with open("test_scenarios.json", "w") as f:
            json.dump(scenarios, f, indent=2)
        
        print("  ✅ Test scenarios saved to test_scenarios.json")
    
    def create_comprehensive_test_script(self):
        """Create comprehensive testing script"""
        print("\n📝 Creating Comprehensive Test Script...")
        
        test_script = '''#!/bin/bash
# ACGS-PGP Comprehensive Workflow Validation
# Tests end-to-end workflows with loaded test data

source auth_tokens.env

echo "🚀 ACGS-PGP Comprehensive Workflow Testing"
echo "=========================================="

echo "1. Testing Enhanced Principle Management..."
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8001/api/v1/principles/ | jq '.total'

echo -e "\n2. Testing Constitutional Synthesis..."
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  http://localhost:8004/api/v1/constitutional/analyze-context \
  -d '{"context": "healthcare_ai_systems", "category": "Safety"}' | jq .

echo -e "\n3. Testing Constitutional Council..."
curl -H "Authorization: Bearer $COUNCIL_TOKEN" http://localhost:8001/api/v1/constitutional-council/meta-rules | jq .

echo -e "\n4. Testing AlphaEvolve Integration..."
curl -H "Authorization: Bearer $POLICY_MANAGER_TOKEN" http://localhost:8004/api/v1/alphaevolve/constitutional-prompting | jq .

echo -e "\n5. Testing Formal Verification..."
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8003/api/v1/verify/ | jq .

echo -e "\n6. Testing Cryptographic Integrity..."
curl -H "Authorization: Bearer $AUDITOR_TOKEN" http://localhost:8002/api/v1/integrity/ | jq .

echo -e "\n✅ Comprehensive Workflow Testing Complete"
'''
        
        with open("test_comprehensive_workflow.sh", "w") as f:
            f.write(test_script)
        
        os.chmod("test_comprehensive_workflow.sh", 0o755)
        print("  ✅ Comprehensive test script created: test_comprehensive_workflow.sh")
    
    async def load_all_test_data(self):
        """Main function to load all test data"""
        print("🚀 Loading Comprehensive Test Data for ACGS-PGP")
        print("=" * 60)
        
        await self.load_ac_principles()
        await self.load_constitutional_council_data()
        await self.load_environmental_factors()
        await self.create_test_scenarios()
        self.create_comprehensive_test_script()
        
        print("\n" + "=" * 60)
        print("✅ Test Data Loading Complete!")
        print("\nLoaded data:")
        print("- 5 AC Principles with enhanced fields")
        print("- 2 Constitutional Council meta-rules")
        print("- 3 Environmental factors")
        print("- 3 Test scenarios")
        print("\nNext steps:")
        print("1. Run comprehensive tests: ./test_comprehensive_workflow.sh")
        print("2. Validate workflows with loaded data")

async def main():
    loader = TestDataLoader()
    await loader.load_all_test_data()

if __name__ == "__main__":
    asyncio.run(main())
