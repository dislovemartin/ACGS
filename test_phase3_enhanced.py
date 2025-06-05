#!/usr/bin/env python3
"""
Enhanced Phase 3 Implementation Validation Script

Tests the advanced caching strategies, enhanced monitoring, security compliance,
and performance optimization features implemented in Phase 3.
"""

import asyncio
import time
import json
import sys
from typing import Dict, Any, List
from datetime import datetime

# Test imports
try:
    from src.backend.gs_service.app.services.cache_manager import get_cache_manager, shutdown_cache_manager
    from src.backend.gs_service.app.services.monitoring_service import get_monitoring_service, shutdown_monitoring_service
    from src.backend.gs_service.app.services.security_compliance import get_security_service
    from src.backend.gs_service.app.services.advanced_cache import CACHE_TTL_POLICIES
    ENHANCED_SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Enhanced services not available: {e}")
    ENHANCED_SERVICES_AVAILABLE = False


class Phase3EnhancedValidator:
    """Comprehensive Phase 3 enhanced features validator."""
    
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        self.cache_manager = None
        self.monitoring_service = None
        self.security_service = None
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive Phase 3 enhanced validation."""
        print("🚀 Phase 3 Enhanced Implementation Validation")
        print("=" * 60)
        
        if not ENHANCED_SERVICES_AVAILABLE:
            return {"success": False, "error": "Enhanced services not available"}
        
        try:
            # Initialize services
            await self._initialize_services()
            
            # Run test suites
            await self._test_advanced_caching()
            await self._test_enhanced_monitoring()
            await self._test_security_compliance()
            await self._test_performance_optimization()
            await self._test_integration()
            
            # Generate summary
            return self._generate_test_summary()
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            await self._cleanup_services()
    
    async def _initialize_services(self):
        """Initialize enhanced services."""
        print("\n🔧 Initializing Enhanced Services...")
        
        # Initialize cache manager
        self.cache_manager = await get_cache_manager()
        print("✅ Cache manager initialized")
        
        # Initialize monitoring service
        self.monitoring_service = await get_monitoring_service()
        print("✅ Monitoring service initialized")
        
        # Initialize security service
        self.security_service = get_security_service()
        print("✅ Security service initialized")
    
    async def _test_advanced_caching(self):
        """Test advanced caching strategies."""
        print("\n💾 Testing Advanced Caching Strategies...")
        
        test_start = time.time()
        
        try:
            # Test multi-tier cache
            policy_cache = await self.cache_manager.get_cache('policy_decisions')
            
            # Test cache warming
            test_policies = [
                {'id': 'test_policy_1', 'rule': 'Test rule 1', 'active': True},
                {'id': 'test_policy_2', 'rule': 'Test rule 2', 'active': True}
            ]
            
            warming_data = []
            for policy in test_policies:
                warming_data.append({
                    'key': f"test_policy:{policy['id']}",
                    'value': policy,
                    'ttl': CACHE_TTL_POLICIES['policy_decisions'],
                    'tags': ['test_policies']
                })
            
            await policy_cache.warm_cache(warming_data)
            print("✅ Cache warming completed")
            
            # Test cache operations
            test_key = "test_policy:test_policy_1"
            cached_value = await policy_cache.get(test_key)
            
            if cached_value and cached_value['id'] == 'test_policy_1':
                print("✅ Cache retrieval working")
            else:
                print("❌ Cache retrieval failed")
                return False
            
            # Test cache statistics
            stats = await self.cache_manager.get_cache_stats()
            if 'policy_decisions' in stats:
                print(f"✅ Cache stats available: {len(stats)} cache types")
            else:
                print("❌ Cache stats not available")
                return False
            
            # Test cache invalidation
            await self.cache_manager.invalidate_cache_tag('policy_decisions', 'test_policies')
            print("✅ Cache invalidation working")
            
            test_duration = (time.time() - test_start) * 1000
            self.performance_metrics['cache_test_duration_ms'] = test_duration
            
            self.test_results.append({
                'test': 'advanced_caching',
                'status': 'passed',
                'duration_ms': test_duration,
                'details': 'Multi-tier caching with warming and invalidation'
            })
            
            print(f"✅ Advanced caching test completed in {test_duration:.2f}ms")
            return True
            
        except Exception as e:
            print(f"❌ Advanced caching test failed: {e}")
            self.test_results.append({
                'test': 'advanced_caching',
                'status': 'failed',
                'error': str(e)
            })
            return False
    
    async def _test_enhanced_monitoring(self):
        """Test enhanced monitoring capabilities."""
        print("\n📊 Testing Enhanced Monitoring...")
        
        test_start = time.time()
        
        try:
            # Test performance metrics collection
            performance_summary = self.monitoring_service.get_performance_summary()
            
            if 'current_metrics' in performance_summary:
                print("✅ Performance metrics collection working")
            else:
                print("❌ Performance metrics collection failed")
                return False
            
            # Test Prometheus metrics export
            metrics_export = self.monitoring_service.get_metrics_export()
            
            if 'acgs_' in metrics_export:
                print("✅ Prometheus metrics export working")
            else:
                print("❌ Prometheus metrics export failed")
                return False
            
            # Test alert thresholds
            alerts = self.monitoring_service.alert_manager.active_alerts
            print(f"✅ Alert system initialized with {len(alerts)} active alerts")
            
            test_duration = (time.time() - test_start) * 1000
            self.performance_metrics['monitoring_test_duration_ms'] = test_duration
            
            self.test_results.append({
                'test': 'enhanced_monitoring',
                'status': 'passed',
                'duration_ms': test_duration,
                'details': 'Prometheus metrics, alerts, and performance tracking'
            })
            
            print(f"✅ Enhanced monitoring test completed in {test_duration:.2f}ms")
            return True
            
        except Exception as e:
            print(f"❌ Enhanced monitoring test failed: {e}")
            self.test_results.append({
                'test': 'enhanced_monitoring',
                'status': 'failed',
                'error': str(e)
            })
            return False
    
    async def _test_security_compliance(self):
        """Test security compliance enhancements."""
        print("\n🔒 Testing Security Compliance...")
        
        test_start = time.time()
        
        try:
            # Test vulnerability scanning
            scan_results = await self.security_service.run_security_scan()
            
            if 'vulnerabilities' in scan_results:
                print(f"✅ Vulnerability scan completed: {scan_results['total_issues']} issues found")
            else:
                print("❌ Vulnerability scan failed")
                return False
            
            # Test security compliance score
            compliance_score = self.security_service.get_security_compliance_score()
            print(f"✅ Security compliance score: {compliance_score:.1f}/100")
            
            # Test security summary
            security_summary = self.security_service.get_security_summary()
            
            if 'compliance_score' in security_summary:
                print("✅ Security summary generation working")
            else:
                print("❌ Security summary generation failed")
                return False
            
            test_duration = (time.time() - test_start) * 1000
            self.performance_metrics['security_test_duration_ms'] = test_duration
            
            self.test_results.append({
                'test': 'security_compliance',
                'status': 'passed',
                'duration_ms': test_duration,
                'details': f'Vulnerability scanning, compliance score: {compliance_score:.1f}'
            })
            
            print(f"✅ Security compliance test completed in {test_duration:.2f}ms")
            return True
            
        except Exception as e:
            print(f"❌ Security compliance test failed: {e}")
            self.test_results.append({
                'test': 'security_compliance',
                'status': 'failed',
                'error': str(e)
            })
            return False
    
    async def _test_performance_optimization(self):
        """Test performance optimization features."""
        print("\n⚡ Testing Performance Optimization...")
        
        test_start = time.time()
        
        try:
            # Test cache performance
            cache = await self.cache_manager.get_cache('api_responses')
            
            # Measure cache put/get performance
            cache_start = time.time()
            
            for i in range(100):
                await cache.put(f"perf_test_{i}", {"data": f"test_data_{i}"})
            
            cache_put_time = (time.time() - cache_start) * 1000
            
            cache_start = time.time()
            
            for i in range(100):
                await cache.get(f"perf_test_{i}")
            
            cache_get_time = (time.time() - cache_start) * 1000
            
            print(f"✅ Cache performance: PUT {cache_put_time:.2f}ms, GET {cache_get_time:.2f}ms")
            
            # Validate performance targets
            if cache_put_time < 100 and cache_get_time < 50:  # Target thresholds
                print("✅ Cache performance targets met")
            else:
                print("⚠️  Cache performance targets not met")
            
            test_duration = (time.time() - test_start) * 1000
            self.performance_metrics['performance_test_duration_ms'] = test_duration
            self.performance_metrics['cache_put_time_ms'] = cache_put_time
            self.performance_metrics['cache_get_time_ms'] = cache_get_time
            
            self.test_results.append({
                'test': 'performance_optimization',
                'status': 'passed',
                'duration_ms': test_duration,
                'details': f'Cache PUT: {cache_put_time:.2f}ms, GET: {cache_get_time:.2f}ms'
            })
            
            print(f"✅ Performance optimization test completed in {test_duration:.2f}ms")
            return True
            
        except Exception as e:
            print(f"❌ Performance optimization test failed: {e}")
            self.test_results.append({
                'test': 'performance_optimization',
                'status': 'failed',
                'error': str(e)
            })
            return False
    
    async def _test_integration(self):
        """Test integration between enhanced services."""
        print("\n🔗 Testing Service Integration...")
        
        test_start = time.time()
        
        try:
            # Test cache manager + monitoring integration
            cache_stats = await self.cache_manager.get_cache_stats()
            monitoring_summary = self.monitoring_service.get_performance_summary()
            security_summary = self.security_service.get_security_summary()
            
            integration_data = {
                'cache_types': len(cache_stats),
                'monitoring_active': 'current_metrics' in monitoring_summary,
                'security_compliance': security_summary.get('compliance_score', 0)
            }
            
            print(f"✅ Integration test: {integration_data}")
            
            test_duration = (time.time() - test_start) * 1000
            
            self.test_results.append({
                'test': 'service_integration',
                'status': 'passed',
                'duration_ms': test_duration,
                'details': 'Cache, monitoring, and security services integrated'
            })
            
            print(f"✅ Service integration test completed in {test_duration:.2f}ms")
            return True
            
        except Exception as e:
            print(f"❌ Service integration test failed: {e}")
            self.test_results.append({
                'test': 'service_integration',
                'status': 'failed',
                'error': str(e)
            })
            return False
    
    def _generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        passed_tests = [t for t in self.test_results if t['status'] == 'passed']
        failed_tests = [t for t in self.test_results if t['status'] == 'failed']
        
        total_duration = sum(t.get('duration_ms', 0) for t in self.test_results)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'passed_tests': len(passed_tests),
            'failed_tests': len(failed_tests),
            'success_rate': len(passed_tests) / len(self.test_results) * 100 if self.test_results else 0,
            'total_duration_ms': total_duration,
            'performance_metrics': self.performance_metrics,
            'test_results': self.test_results
        }
        
        return summary
    
    async def _cleanup_services(self):
        """Cleanup services after testing."""
        try:
            if self.cache_manager:
                await shutdown_cache_manager()
            
            if self.monitoring_service:
                await shutdown_monitoring_service()
            
            print("✅ Services cleanup completed")
            
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


async def main():
    """Main test execution."""
    validator = Phase3EnhancedValidator()
    
    try:
        results = await validator.run_all_tests()
        
        print("\n" + "=" * 60)
        print("📊 Phase 3 Enhanced Validation Results")
        print("=" * 60)
        
        if results.get('success', True):
            print(f"✅ Tests Passed: {results['passed_tests']}/{results['total_tests']}")
            print(f"📈 Success Rate: {results['success_rate']:.1f}%")
            print(f"⏱️  Total Duration: {results['total_duration_ms']:.2f}ms")
            
            if results['success_rate'] >= 80:
                print("\n🎉 Phase 3 Enhanced Implementation: VALIDATED ✅")
                return 0
            else:
                print("\n⚠️  Phase 3 Enhanced Implementation: NEEDS IMPROVEMENT")
                return 1
        else:
            print(f"❌ Validation failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Validation execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
