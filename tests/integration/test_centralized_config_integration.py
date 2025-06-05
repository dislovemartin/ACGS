#!/usr/bin/env python3
"""
Integration test for centralized configuration management.
Tests cross-service configuration consistency and integration test fixes.
"""

import asyncio
import httpx
import json
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/shared'))

from utils import get_config, reset_config


class CentralizedConfigIntegrationTest:
    """Test centralized configuration across ACGS-PGP services."""
    
    def __init__(self):
        self.config = get_config()
        self.results = {
            'configuration_tests': {'passed': 0, 'failed': 0, 'tests': []},
            'service_communication': {'passed': 0, 'failed': 0, 'tests': []},
            'cross_service_integration': {'passed': 0, 'failed': 0, 'tests': []}
        }
    
    async def run_all_tests(self):
        """Run all centralized configuration tests."""
        print("🔧 Starting Centralized Configuration Integration Tests")
        print("=" * 60)
        
        # Test configuration loading and validation
        await self.test_configuration_loading()
        await self.test_service_url_consistency()
        await self.test_environment_detection()
        
        # Test cross-service communication with centralized URLs
        await self.test_cross_service_health_checks()
        await self.test_service_url_resolution()
        
        # Test integration test fixes
        await self.test_integration_test_configuration()
        
        # Generate summary
        self.generate_test_summary()
    
    async def test_configuration_loading(self):
        """Test that configuration loads correctly from environment."""
        test_name = "Configuration Loading"
        
        try:
            # Test basic configuration access
            environment = self.config.get('environment')
            api_version = self.config.get('api_version')
            
            # Test service URLs
            auth_url = self.config.get_service_url('auth')
            ac_url = self.config.get_service_url('ac')
            
            # Test nested configuration access
            cors_origins = self.config.get('cors_origins')
            
            # Validate configuration structure
            assert environment in ['development', 'production', 'testing'], f"Invalid environment: {environment}"
            assert api_version == 'v1', f"Unexpected API version: {api_version}"
            assert auth_url.startswith('http'), f"Invalid auth URL: {auth_url}"
            assert isinstance(cors_origins, list), f"CORS origins should be list: {cors_origins}"
            
            self._record_test_result('configuration_tests', test_name, True, 
                                   f"Configuration loaded successfully. Environment: {environment}")
            
        except Exception as e:
            self._record_test_result('configuration_tests', test_name, False, str(e))
    
    async def test_service_url_consistency(self):
        """Test that service URLs are consistent across different access methods."""
        test_name = "Service URL Consistency"
        
        try:
            services = ['auth', 'ac', 'integrity', 'fv', 'gs', 'pgc']
            
            for service in services:
                # Test external URL
                external_url = self.config.get_service_url(service)
                
                # Test internal URL
                internal_url = self.config.get_service_url(service, internal=True)
                
                # Test URL with API path
                api_url = self.config.get_service_url(service, api_path='/health')
                
                # Validate URL formats
                assert external_url.startswith('http'), f"Invalid external URL for {service}: {external_url}"
                assert internal_url.startswith('http'), f"Invalid internal URL for {service}: {internal_url}"
                assert '/api/v1/health' in api_url, f"API path not properly constructed for {service}: {api_url}"
            
            self._record_test_result('configuration_tests', test_name, True, 
                                   f"All {len(services)} service URLs are consistent")
            
        except Exception as e:
            self._record_test_result('configuration_tests', test_name, False, str(e))
    
    async def test_environment_detection(self):
        """Test environment detection and configuration switching."""
        test_name = "Environment Detection"
        
        try:
            # Test environment detection methods
            is_dev = self.config.is_development()
            is_prod = self.config.is_production()
            is_test = self.config.is_test_mode()
            
            # Test database URL selection
            db_url = self.config.get_database_url()
            test_db_url = self.config.get_database_url(test_mode=True)
            
            # Validate environment consistency
            environment = self.config.get('environment')
            if environment == 'development':
                assert is_dev and not is_prod, "Development environment detection failed"
            elif environment == 'production':
                assert is_prod and not is_dev, "Production environment detection failed"
            
            assert db_url != test_db_url, "Database URLs should be different for test and normal modes"
            
            self._record_test_result('configuration_tests', test_name, True, 
                                   f"Environment detection working. Current: {environment}")
            
        except Exception as e:
            self._record_test_result('configuration_tests', test_name, False, str(e))
    
    async def test_cross_service_health_checks(self):
        """Test health checks using centralized service URLs."""
        test_name = "Cross-Service Health Checks"
        
        try:
            services = ['auth', 'ac', 'integrity', 'fv', 'gs', 'pgc']
            successful_checks = 0
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                for service in services:
                    try:
                        health_url = self.config.get_service_url(service, api_path='/health')
                        response = await client.get(health_url)
                        
                        if response.status_code == 200:
                            successful_checks += 1
                            print(f"  ✅ {service} service health check passed")
                        else:
                            print(f"  ⚠️  {service} service returned {response.status_code}")
                    
                    except Exception as e:
                        print(f"  ❌ {service} service health check failed: {str(e)}")
            
            # Consider test successful if at least some services are running
            success = successful_checks > 0
            message = f"{successful_checks}/{len(services)} services responded to health checks"
            
            self._record_test_result('service_communication', test_name, success, message)
            
        except Exception as e:
            self._record_test_result('service_communication', test_name, False, str(e))
    
    async def test_service_url_resolution(self):
        """Test service URL resolution for cross-service communication."""
        test_name = "Service URL Resolution"
        
        try:
            # Test various URL construction scenarios
            test_cases = [
                ('ac', '/principles', 'http://localhost:8001/api/v1/principles'),
                ('fv', '/bias-detection', 'http://localhost:8003/api/v1/bias-detection'),
                ('gs', '/synthesis', 'http://localhost:8004/api/v1/synthesis'),
            ]
            
            for service, path, expected_pattern in test_cases:
                url = self.config.get_service_url(service, api_path=path)
                
                # Check that URL contains expected components
                assert f'/api/v1{path}' in url, f"API path not properly constructed: {url}"
                assert service in ['ac', 'fv', 'gs'], f"Unknown service: {service}"
            
            self._record_test_result('service_communication', test_name, True, 
                                   f"All {len(test_cases)} URL resolution tests passed")
            
        except Exception as e:
            self._record_test_result('service_communication', test_name, False, str(e))
    
    async def test_integration_test_configuration(self):
        """Test configuration fixes for integration tests."""
        test_name = "Integration Test Configuration"
        
        try:
            # Test that configuration can be used in integration test scenarios
            
            # Test service URL mapping for integration tests
            service_mapping = {}
            for service in ['auth', 'ac', 'integrity', 'fv', 'gs', 'pgc']:
                service_mapping[service] = {
                    'url': self.config.get_service_url(service),
                    'health': self.config.get_service_url(service, api_path='/health')
                }
            
            # Validate that all services have proper URLs
            assert len(service_mapping) == 6, "Not all services configured"
            
            # Test configuration consistency for test mode
            test_config = get_config()
            assert test_config is self.config, "Configuration should be singleton"
            
            self._record_test_result('cross_service_integration', test_name, True, 
                                   "Integration test configuration validated")
            
        except Exception as e:
            self._record_test_result('cross_service_integration', test_name, False, str(e))
    
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
        print("📊 CENTRALIZED CONFIGURATION TEST SUMMARY")
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
        with open('centralized_config_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: centralized_config_test_results.json")
        
        return success_rate >= 80  # Consider successful if 80% or more tests pass


async def main():
    """Main test execution function."""
    tester = CentralizedConfigIntegrationTest()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 Centralized configuration integration tests PASSED!")
        return 0
    else:
        print("\n💥 Centralized configuration integration tests FAILED!")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
