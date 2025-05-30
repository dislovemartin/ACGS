#!/usr/bin/env python3
"""
ACGS-PGP Comprehensive Feature Test Suite
Tests all Phase 1-3 components with integration scenarios
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ComprehensiveFeatureTester:
    def __init__(self):
        self.session = None
        self.test_results = {}
        self.base_urls = {
            "ac": "http://localhost:8001/api/v1",
            "gs": "http://localhost:8004/api/v1",
            "fv": "http://localhost:8003/api/v1",
            "integrity": "http://localhost:8002/api/v1",
            "pgc": "http://localhost:8005/api/v1"
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_phase1_enhanced_principles(self) -> bool:
        """Test Phase 1: Enhanced Principle Management"""
        print("\n📋 Testing Phase 1: Enhanced Principle Management...")
        
        try:
            # Test creating enhanced principle
            principle_data = {
                "name": "Test Enhanced Safety Principle",
                "description": "A comprehensive safety principle for testing",
                "content": "AI systems SHALL prioritize user safety above all other considerations",
                "priority_weight": 0.95,
                "scope": ["healthcare", "autonomous_systems", "critical_infrastructure"],
                "normative_statement": "SHALL ensure user safety is never compromised",
                "constraints": {
                    "mandatory_checks": ["safety_validation", "risk_assessment"],
                    "prohibited_actions": ["unsafe_operations", "data_exposure"]
                },
                "rationale": "User safety is fundamental to AI system trustworthiness",
                "keywords": ["safety", "user_protection", "risk_management"],
                "category": "Safety"
            }
            
            url = f"{self.base_urls['ac']}/principles"
            async with self.session.post(url, json=principle_data) as response:
                if response.status == 201:
                    created_principle = await response.json()
                    principle_id = created_principle.get("id")
                    print(f"✅ Created enhanced principle with ID: {principle_id}")
                    
                    # Test retrieving enhanced principle
                    async with self.session.get(f"{url}/{principle_id}") as get_response:
                        if get_response.status == 200:
                            retrieved_principle = await get_response.json()
                            
                            # Validate enhanced fields
                            required_fields = ["priority_weight", "scope", "normative_statement", "constraints", "rationale", "keywords", "category"]
                            missing_fields = [field for field in required_fields if field not in retrieved_principle]
                            
                            if not missing_fields:
                                print("✅ Enhanced principle fields validated")
                                return True
                            else:
                                print(f"❌ Missing enhanced fields: {missing_fields}")
                                return False
                        else:
                            print(f"❌ Failed to retrieve principle: HTTP {get_response.status}")
                            return False
                else:
                    print(f"❌ Failed to create principle: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Phase 1 test failed: {str(e)}")
            return False
    
    async def test_phase1_constitutional_prompting(self) -> bool:
        """Test Phase 1: Constitutional Prompting"""
        print("\n🏛️ Testing Phase 1: Constitutional Prompting...")
        
        try:
            # Test constitutional synthesis
            synthesis_request = {
                "context": "healthcare_data_processing",
                "category": "privacy",
                "synthesis_request": "Generate a policy for patient data access controls",
                "target_format": "rego"
            }
            
            url = f"{self.base_urls['gs']}/constitutional/synthesize"
            async with self.session.post(url, json=synthesis_request) as response:
                if response.status == 200:
                    synthesis_result = await response.json()
                    
                    # Validate constitutional synthesis response
                    required_fields = ["constitutional_context", "synthesized_policy", "constitutional_compliance"]
                    if all(field in synthesis_result for field in required_fields):
                        print("✅ Constitutional synthesis successful")
                        
                        # Test contextual analysis
                        context_request = {
                            "context": "healthcare_data_processing",
                            "environmental_factors": {
                                "regulatory_environment": "HIPAA",
                                "risk_level": "high",
                                "user_demographics": "healthcare_providers"
                            }
                        }
                        
                        context_url = f"{self.base_urls['gs']}/constitutional/analyze-context"
                        async with self.session.post(context_url, json=context_request) as context_response:
                            if context_response.status == 200:
                                context_result = await context_response.json()
                                print("✅ Contextual analysis successful")
                                return True
                            else:
                                print(f"❌ Contextual analysis failed: HTTP {context_response.status}")
                                return False
                    else:
                        print(f"❌ Missing synthesis fields: {[f for f in required_fields if f not in synthesis_result]}")
                        return False
                else:
                    print(f"❌ Constitutional synthesis failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Constitutional prompting test failed: {str(e)}")
            return False
    
    async def test_phase2_alphaevolve_integration(self) -> bool:
        """Test Phase 2: AlphaEvolve Integration"""
        print("\n🧬 Testing Phase 2: AlphaEvolve Integration...")
        
        try:
            # Test evolutionary constitutional prompting
            ec_request = {
                "context": "autonomous_vehicle_safety",
                "category": "safety",
                "synthesis_request": "Generate adaptive safety policies for autonomous vehicles",
                "evolutionary_parameters": {
                    "population_size": 10,
                    "generations": 5,
                    "mutation_rate": 0.1
                }
            }
            
            url = f"{self.base_urls['gs']}/alphaevolve/ec-constitutional-prompting"
            async with self.session.post(url, json=ec_request) as response:
                if response.status == 200:
                    ec_result = await response.json()
                    print("✅ Evolutionary constitutional prompting successful")
                    
                    # Test governance evaluation
                    eval_request = {
                        "policies": [ec_result.get("best_policy", "")],
                        "evaluation_criteria": ["safety", "efficiency", "compliance"]
                    }
                    
                    eval_url = f"{self.base_urls['gs']}/alphaevolve/governance-evaluation"
                    async with self.session.post(eval_url, json=eval_request) as eval_response:
                        if eval_response.status == 200:
                            eval_result = await eval_response.json()
                            print("✅ Governance evaluation successful")
                            return True
                        else:
                            print(f"❌ Governance evaluation failed: HTTP {eval_response.status}")
                            return False
                else:
                    print(f"❌ EC constitutional prompting failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ AlphaEvolve integration test failed: {str(e)}")
            return False
    
    async def test_phase3_formal_verification(self) -> bool:
        """Test Phase 3: Formal Verification with Z3"""
        print("\n🔍 Testing Phase 3: Formal Verification...")
        
        try:
            # Test Z3 SMT solver integration
            verification_request = {
                "datalog_rules": [
                    "allow(user, action) :- role(user, admin), action = read.",
                    "allow(user, action) :- role(user, user), action = read, owner(user, resource)."
                ],
                "proof_obligations": [
                    "∀user,action. allow(user,action) → authorized(user,action)",
                    "∀user. role(user,admin) → ∃action. allow(user,action)"
                ]
            }
            
            url = f"{self.base_urls['fv']}/verify/smt-solver"
            async with self.session.post(url, json=verification_request) as response:
                if response.status == 200:
                    verification_result = await response.json()
                    print("✅ Z3 formal verification successful")
                    
                    # Test tiered validation
                    tiered_request = {
                        "rule": {
                            "rule_content": "allow(user, read) :- authenticated(user).",
                            "rule_type": "access_control"
                        },
                        "validation_level": "rigorous"
                    }
                    
                    tiered_url = f"{self.base_urls['fv']}/verify/tiered-validation"
                    async with self.session.post(tiered_url, json=tiered_request) as tiered_response:
                        if tiered_response.status == 200:
                            tiered_result = await tiered_response.json()
                            print("✅ Tiered validation successful")
                            return True
                        else:
                            print(f"❌ Tiered validation failed: HTTP {tiered_response.status}")
                            return False
                else:
                    print(f"❌ Formal verification failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Formal verification test failed: {str(e)}")
            return False
    
    async def test_phase3_cryptographic_integrity(self) -> bool:
        """Test Phase 3: Cryptographic Integrity (PGP Assurance)"""
        print("\n🔐 Testing Phase 3: Cryptographic Integrity...")
        
        try:
            # Test digital signature creation
            sign_request = {
                "data": "Test policy content for signature verification",
                "key_purpose": "policy_signing"
            }
            
            url = f"{self.base_urls['integrity']}/crypto/sign"
            async with self.session.post(url, json=sign_request) as response:
                if response.status == 200:
                    sign_result = await response.json()
                    signature = sign_result.get("signature")
                    key_id = sign_result.get("key_id")
                    print("✅ Digital signature creation successful")
                    
                    # Test signature verification
                    verify_request = {
                        "data": "Test policy content for signature verification",
                        "signature": signature,
                        "key_id": key_id
                    }
                    
                    verify_url = f"{self.base_urls['integrity']}/crypto/verify"
                    async with self.session.post(verify_url, json=verify_request) as verify_response:
                        if verify_response.status == 200:
                            verify_result = await verify_response.json()
                            if verify_result.get("is_valid"):
                                print("✅ Signature verification successful")
                                return True
                            else:
                                print("❌ Signature verification failed")
                                return False
                        else:
                            print(f"❌ Signature verification request failed: HTTP {verify_response.status}")
                            return False
                else:
                    print(f"❌ Digital signature creation failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Cryptographic integrity test failed: {str(e)}")
            return False
    
    async def run_comprehensive_tests(self) -> Dict[str, bool]:
        """Run all comprehensive feature tests"""
        print("🚀 ACGS-PGP Comprehensive Feature Test Suite")
        print("=" * 60)
        print(f"Test started at: {datetime.now().isoformat()}")
        
        # Run all test phases
        tests = [
            ("Phase 1: Enhanced Principles", self.test_phase1_enhanced_principles),
            ("Phase 1: Constitutional Prompting", self.test_phase1_constitutional_prompting),
            ("Phase 2: AlphaEvolve Integration", self.test_phase2_alphaevolve_integration),
            ("Phase 3: Formal Verification", self.test_phase3_formal_verification),
            ("Phase 3: Cryptographic Integrity", self.test_phase3_cryptographic_integrity)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {str(e)}")
                results[test_name] = False
        
        return results

async def main():
    """Main test execution function"""
    async with ComprehensiveFeatureTester() as tester:
        results = await tester.run_comprehensive_tests()
        
        # Print summary
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All comprehensive feature tests passed!")
            return 0
        else:
            print("⚠️ Some feature tests failed - check service implementations")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
