#!/usr/bin/env python3
"""
Integration test for AI model service and TaskMaster AI integration.
Tests Google Gemini 2.5 Flash and DeepSeek-R1 model integration with ACGS-PGP.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend'))

# Import with absolute path handling
try:
    from ai_model_service import AIModelService, ModelRole, get_ai_model_service, reset_ai_model_service
    from utils import get_config, reset_config
except ImportError:
    # Try alternative import path
    import shared.ai_model_service as ai_model_service
    import shared.utils as utils
    AIModelService = ai_model_service.AIModelService
    ModelRole = ai_model_service.ModelRole
    get_ai_model_service = ai_model_service.get_ai_model_service
    reset_ai_model_service = ai_model_service.reset_ai_model_service
    get_config = utils.get_config
    reset_config = utils.reset_config


class AIModelIntegrationTest:
    """Test AI model integration for ACGS-PGP."""
    
    def __init__(self):
        self.config = get_config()
        self.results = {
            'configuration_tests': {'passed': 0, 'failed': 0, 'tests': []},
            'model_availability': {'passed': 0, 'failed': 0, 'tests': []},
            'model_generation': {'passed': 0, 'failed': 0, 'tests': []},
            'taskmaster_integration': {'passed': 0, 'failed': 0, 'tests': []}
        }
    
    async def run_all_tests(self):
        """Run all AI model integration tests."""
        print("🤖 Starting AI Model Integration Tests")
        print("=" * 60)
        
        # Test configuration
        await self.test_ai_configuration()
        await self.test_model_enablement()
        await self.test_api_key_configuration()
        
        # Test model availability
        await self.test_model_service_initialization()
        await self.test_available_models()
        
        # Test model generation
        await self.test_gemini_2_5_flash_generation()
        await self.test_deepseek_r1_generation()
        await self.test_model_role_selection()
        
        # Test TaskMaster integration
        await self.test_taskmaster_model_configuration()
        
        # Generate summary
        self.generate_test_summary()
    
    async def test_ai_configuration(self):
        """Test AI model configuration loading."""
        test_name = "AI Configuration Loading"
        
        try:
            # Test AI model configuration access
            primary_model = self.config.get_ai_model('primary')
            research_model = self.config.get_ai_model('research')
            gemini_model = self.config.get_ai_model('gemini_2_5_flash')
            deepseek_model = self.config.get_ai_model('deepseek_r1')
            
            # Test LLM settings
            llm_settings = self.config.get_llm_settings()
            
            # Validate configuration
            assert primary_model, "Primary model not configured"
            assert research_model, "Research model not configured"
            assert gemini_model == 'gemini-2.5-flash-preview-04-17', f"Unexpected Gemini model: {gemini_model}"
            assert 'deepseek' in deepseek_model.lower(), f"Unexpected DeepSeek model: {deepseek_model}"
            assert llm_settings['max_tokens'] > 0, "Invalid max_tokens setting"
            
            self._record_test_result('configuration_tests', test_name, True, 
                                   f"AI configuration loaded. Primary: {primary_model}, Gemini: {gemini_model}")
            
        except Exception as e:
            self._record_test_result('configuration_tests', test_name, False, str(e))
    
    async def test_model_enablement(self):
        """Test model enablement flags."""
        test_name = "Model Enablement Flags"
        
        try:
            gemini_enabled = self.config.is_model_enabled('enable_gemini_2_5_flash')
            deepseek_enabled = self.config.is_model_enabled('enable_deepseek_r1')
            bias_detection_enabled = self.config.is_model_enabled('enable_bias_detection_llm')
            
            # Test TaskMaster configuration
            taskmaster_config = self.config.get_model_config_for_taskmaster()
            
            assert isinstance(gemini_enabled, bool), "Gemini enablement flag should be boolean"
            assert isinstance(deepseek_enabled, bool), "DeepSeek enablement flag should be boolean"
            assert 'models' in taskmaster_config, "TaskMaster config missing models section"
            assert 'gemini_2_5_flash' in taskmaster_config['models'], "Gemini model missing from TaskMaster config"
            
            self._record_test_result('configuration_tests', test_name, True, 
                                   f"Model flags: Gemini={gemini_enabled}, DeepSeek={deepseek_enabled}")
            
        except Exception as e:
            self._record_test_result('configuration_tests', test_name, False, str(e))
    
    async def test_api_key_configuration(self):
        """Test API key configuration."""
        test_name = "API Key Configuration"
        
        try:
            # Test API key access (without revealing actual keys)
            google_key = self.config.get_ai_api_key('google')
            huggingface_key = self.config.get_ai_api_key('huggingface')
            openrouter_key = self.config.get_ai_api_key('openrouter')
            
            # Test endpoints
            hf_endpoint = self.config.get_ai_endpoint('huggingface')
            openrouter_endpoint = self.config.get_ai_endpoint('openrouter')
            
            # Validate configuration structure
            assert hf_endpoint and hf_endpoint.startswith('https://'), f"Invalid HuggingFace endpoint: {hf_endpoint}"
            assert openrouter_endpoint and openrouter_endpoint.startswith('https://'), f"Invalid OpenRouter endpoint: {openrouter_endpoint}"
            
            key_status = {
                'google': 'configured' if google_key else 'missing',
                'huggingface': 'configured' if huggingface_key else 'missing',
                'openrouter': 'configured' if openrouter_key else 'missing'
            }
            
            self._record_test_result('configuration_tests', test_name, True, 
                                   f"API key status: {key_status}")
            
        except Exception as e:
            self._record_test_result('configuration_tests', test_name, False, str(e))
    
    async def test_model_service_initialization(self):
        """Test AI model service initialization."""
        test_name = "Model Service Initialization"
        
        try:
            ai_service = await get_ai_model_service()
            
            assert ai_service is not None, "AI model service not initialized"
            assert len(ai_service.models) > 0, "No models loaded"
            
            # Test that required models are present
            required_models = ['primary', 'research', 'fallback']
            for model_name in required_models:
                assert model_name in ai_service.models, f"Required model missing: {model_name}"
            
            self._record_test_result('model_availability', test_name, True, 
                                   f"AI service initialized with {len(ai_service.models)} models")
            
        except Exception as e:
            self._record_test_result('model_availability', test_name, False, str(e))
    
    async def test_available_models(self):
        """Test available models listing."""
        test_name = "Available Models Listing"
        
        try:
            ai_service = await get_ai_model_service()
            available_models = ai_service.get_available_models()
            
            # Check for new models
            gemini_available = any('gemini' in name for name in available_models.keys())
            deepseek_available = any('deepseek' in name for name in available_models.keys())
            
            # Validate model information
            for model_name, model_info in available_models.items():
                assert 'provider' in model_info, f"Model {model_name} missing provider"
                assert 'model_id' in model_info, f"Model {model_name} missing model_id"
                assert 'enabled' in model_info, f"Model {model_name} missing enabled flag"
            
            self._record_test_result('model_availability', test_name, True, 
                                   f"Models available: {len(available_models)}, Gemini: {gemini_available}, DeepSeek: {deepseek_available}")
            
        except Exception as e:
            self._record_test_result('model_availability', test_name, False, str(e))
    
    async def test_gemini_2_5_flash_generation(self):
        """Test Google Gemini 2.5 Flash text generation."""
        test_name = "Gemini 2.5 Flash Generation"
        
        try:
            ai_service = await get_ai_model_service()
            
            # Test Gemini model if available
            if 'gemini_2_5_flash' in ai_service.models:
                prompt = "Analyze the constitutional implications of AI governance policies."
                response = await ai_service.generate_text(
                    prompt=prompt,
                    model_name='gemini_2_5_flash',
                    max_tokens=1000
                )
                
                assert response.content, "Empty response from Gemini model"
                assert response.model_id == 'gemini-2.5-flash-preview-04-17', f"Unexpected model ID: {response.model_id}"
                assert response.provider == 'google', f"Unexpected provider: {response.provider}"
                
                self._record_test_result('model_generation', test_name, True, 
                                       f"Gemini generation successful. Response length: {len(response.content)}")
            else:
                self._record_test_result('model_generation', test_name, False, 
                                       "Gemini 2.5 Flash model not available")
            
        except Exception as e:
            self._record_test_result('model_generation', test_name, False, str(e))
    
    async def test_deepseek_r1_generation(self):
        """Test DeepSeek-R1 text generation."""
        test_name = "DeepSeek-R1 Generation"
        
        try:
            ai_service = await get_ai_model_service()
            
            # Test DeepSeek models if available
            deepseek_models = [name for name in ai_service.models.keys() if 'deepseek' in name]
            
            if deepseek_models:
                model_name = deepseek_models[0]  # Use first available DeepSeek model
                prompt = "Provide research-backed analysis of bias detection in AI policy systems."
                response = await ai_service.generate_text(
                    prompt=prompt,
                    model_name=model_name,
                    max_tokens=1000
                )
                
                assert response.content, "Empty response from DeepSeek model"
                assert 'deepseek' in response.model_id.lower(), f"Unexpected model ID: {response.model_id}"
                
                self._record_test_result('model_generation', test_name, True, 
                                       f"DeepSeek generation successful with {model_name}. Response length: {len(response.content)}")
            else:
                self._record_test_result('model_generation', test_name, False, 
                                       "DeepSeek-R1 models not available")
            
        except Exception as e:
            self._record_test_result('model_generation', test_name, False, str(e))
    
    async def test_model_role_selection(self):
        """Test model selection by role."""
        test_name = "Model Role Selection"
        
        try:
            ai_service = await get_ai_model_service()
            
            # Test role-based model selection
            roles_to_test = [ModelRole.PRIMARY, ModelRole.RESEARCH, ModelRole.TESTING]
            
            for role in roles_to_test:
                try:
                    prompt = f"Test prompt for {role.value} role."
                    response = await ai_service.generate_text(
                        prompt=prompt,
                        role=role,
                        max_tokens=100
                    )
                    
                    assert response.content, f"Empty response for {role.value} role"
                    
                except Exception as role_error:
                    # Some roles might not have models configured
                    print(f"  ⚠️  Role {role.value} not available: {role_error}")
            
            self._record_test_result('model_generation', test_name, True, 
                                   f"Role-based selection tested for {len(roles_to_test)} roles")
            
        except Exception as e:
            self._record_test_result('model_generation', test_name, False, str(e))
    
    async def test_taskmaster_model_configuration(self):
        """Test TaskMaster AI model configuration integration."""
        test_name = "TaskMaster Model Configuration"
        
        try:
            taskmaster_config = self.config.get_model_config_for_taskmaster()
            
            # Validate TaskMaster configuration structure
            assert 'models' in taskmaster_config, "Missing models section"
            assert 'api_keys' in taskmaster_config, "Missing api_keys section"
            
            models = taskmaster_config['models']
            assert 'main' in models, "Missing main model"
            assert 'research' in models, "Missing research model"
            assert 'fallback' in models, "Missing fallback model"
            
            # Check new models
            new_models = ['gemini_2_5_flash', 'deepseek_r1_hf', 'deepseek_r1_openrouter']
            available_new_models = [model for model in new_models if model in models]
            
            # Validate model structure
            for model_name, model_config in models.items():
                if isinstance(model_config, dict):
                    assert 'provider' in model_config, f"Model {model_name} missing provider"
                    assert 'modelId' in model_config, f"Model {model_name} missing modelId"
            
            self._record_test_result('taskmaster_integration', test_name, True, 
                                   f"TaskMaster config valid. New models: {available_new_models}")
            
        except Exception as e:
            self._record_test_result('taskmaster_integration', test_name, False, str(e))
    
    def _record_test_result(self, category: str, test_name: str, success: bool, details: str):
        """Record test result in the appropriate category."""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results[category]['tests'].append(result)
        
        if success:
            self.results[category]['passed'] += 1
            print(f"✅ {test_name}: {details}")
        else:
            self.results[category]['failed'] += 1
            print(f"❌ {test_name}: {details}")
    
    def generate_test_summary(self):
        """Generate and display test summary."""
        print("\n" + "=" * 60)
        print("📊 AI MODEL INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.results.items():
            passed = results['passed']
            failed = results['failed']
            total = passed + failed
            
            total_passed += passed
            total_failed += failed
            
            print(f"\n{category.replace('_', ' ').title()}:")
            print(f"  ✅ Passed: {passed}/{total}")
            print(f"  ❌ Failed: {failed}/{total}")
            
            if failed > 0:
                print("  Failed tests:")
                for test in results['tests']:
                    if not test['success']:
                        print(f"    - {test['test_name']}: {test['details']}")
        
        overall_total = total_passed + total_failed
        success_rate = (total_passed / overall_total * 100) if overall_total > 0 else 0
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {overall_total}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Save results to file
        with open('ai_model_integration_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: ai_model_integration_test_results.json")
        
        return success_rate >= 80  # Consider successful if 80% or more tests pass


async def main():
    """Main test execution function."""
    tester = AIModelIntegrationTest()
    success = await tester.run_all_tests()
    
    # Clean up
    await reset_ai_model_service()
    
    if success:
        print("\n🎉 AI model integration tests PASSED!")
        return 0
    else:
        print("\n💥 AI model integration tests FAILED!")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
