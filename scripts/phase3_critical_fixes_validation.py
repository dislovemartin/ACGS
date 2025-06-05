#!/usr/bin/env python3
"""
Phase 3 Critical Fixes Validation Script
Validates memory optimization and Redis cache performance fixes.
"""

import asyncio
import aiohttp
import json
import logging
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3CriticalFixesValidator:
    """
    Validates the critical fixes for Phase 3 production readiness:
    1. Memory usage optimization (<85% target)
    2. Redis cache performance (>80% hit rate target)
    3. Constitutional validation endpoint implementation
    4. Cache warming strategies
    """
    
    def __init__(self):
        self.service_endpoints = {
            "ac_service": "http://localhost:8001",
            "auth_service": "http://localhost:8000",
            "gs_service": "http://localhost:8015",
        }
        self.available_services = {}
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "fixes_validated": {},
            "performance_metrics": {},
            "production_readiness": {},
            "recommendations": []
        }
    
    async def validate_all_fixes(self):
        """Validate all critical fixes."""
        logger.info("🔧 Starting Phase 3 Critical Fixes Validation")
        logger.info("=" * 60)
        
        # Check service availability
        await self.check_service_availability()
        
        # Validate Fix #4: Memory Usage Optimization
        await self.validate_memory_optimization()
        
        # Validate Fix #5: Redis Cache Performance
        await self.validate_redis_cache_performance()
        
        # Validate Constitutional Validation Endpoint
        await self.validate_constitutional_endpoint()
        
        # Validate Cache Warming Implementation
        await self.validate_cache_warming()
        
        # Generate comprehensive validation report
        self.generate_validation_report()
        
        return self.validation_results
    
    async def check_service_availability(self):
        """Check which services are available for validation."""
        logger.info("Checking service availability...")
        
        async with aiohttp.ClientSession() as session:
            for service_name, url in self.service_endpoints.items():
                try:
                    async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            self.available_services[service_name] = url
                            logger.info(f"✅ {service_name} available at {url}")
                        else:
                            logger.warning(f"❌ {service_name} returned status {response.status}")
                except Exception as e:
                    logger.warning(f"❌ {service_name} not available: {e}")
        
        logger.info(f"Available services: {len(self.available_services)}/{len(self.service_endpoints)}")
    
    async def validate_memory_optimization(self):
        """Validate memory usage optimization implementation."""
        logger.info("\n🧠 Validating Memory Usage Optimization (Fix #4)")
        logger.info("-" * 50)
        
        try:
            # Import memory optimizer
            from src.backend.shared.memory_optimizer import MemoryOptimizer, MemoryThresholds
            
            # Initialize memory optimizer
            optimizer = MemoryOptimizer("validation_test")
            await optimizer.initialize()
            
            # Get memory stats
            memory_stats = optimizer.get_memory_stats()
            
            # Validate memory usage is below critical threshold
            current_memory = memory_stats["current_metrics"]["memory_percent"]
            memory_compliant = current_memory < 85.0
            
            self.validation_results["fixes_validated"]["memory_optimization"] = {
                "implemented": True,
                "current_memory_percent": current_memory,
                "target_met": memory_compliant,
                "thresholds": memory_stats["thresholds"],
                "optimization_features": {
                    "monitoring_active": memory_stats["optimization_status"]["monitoring_active"],
                    "leak_detection": memory_stats["optimization_status"]["leak_detection_enabled"],
                    "gc_optimization": True,
                    "request_tracking": memory_stats["optimization_status"]["active_requests"] >= 0
                }
            }
            
            logger.info(f"Memory Usage: {current_memory:.1f}% (target: <85%)")
            logger.info(f"Memory Compliance: {'✅ PASSED' if memory_compliant else '❌ FAILED'}")
            logger.info(f"Monitoring Active: {'✅ YES' if memory_stats['optimization_status']['monitoring_active'] else '❌ NO'}")
            logger.info(f"Leak Detection: {'✅ ENABLED' if memory_stats['optimization_status']['leak_detection_enabled'] else '❌ DISABLED'}")
            
            # Stop monitoring for validation
            await optimizer.stop_monitoring()
            
        except Exception as e:
            logger.error(f"Memory optimization validation failed: {e}")
            self.validation_results["fixes_validated"]["memory_optimization"] = {
                "implemented": False,
                "error": str(e),
                "target_met": False
            }
    
    async def validate_redis_cache_performance(self):
        """Validate Redis cache performance implementation."""
        logger.info("\n🚀 Validating Redis Cache Performance (Fix #5)")
        logger.info("-" * 50)
        
        try:
            # Test cache performance with constitutional validation
            if "ac_service" in self.available_services:
                cache_performance = await self._test_cache_hit_rate()
                
                self.validation_results["fixes_validated"]["redis_cache_performance"] = {
                    "implemented": True,
                    "cache_hit_rate": cache_performance["hit_rate"],
                    "target_met": cache_performance["hit_rate"] > 80,
                    "average_latency_ms": cache_performance["average_latency"],
                    "latency_target_met": cache_performance["average_latency"] < 25,
                    "total_requests": cache_performance["total_requests"],
                    "cache_hits": cache_performance["cache_hits"]
                }
                
                logger.info(f"Cache Hit Rate: {cache_performance['hit_rate']:.1f}% (target: >80%)")
                logger.info(f"Average Latency: {cache_performance['average_latency']:.2f}ms (target: <25ms)")
                logger.info(f"Cache Performance: {'✅ PASSED' if cache_performance['hit_rate'] > 80 else '❌ FAILED'}")
                
            else:
                logger.warning("AC service not available - cannot test cache performance")
                self.validation_results["fixes_validated"]["redis_cache_performance"] = {
                    "implemented": False,
                    "error": "AC service not available",
                    "target_met": False
                }
                
        except Exception as e:
            logger.error(f"Redis cache performance validation failed: {e}")
            self.validation_results["fixes_validated"]["redis_cache_performance"] = {
                "implemented": False,
                "error": str(e),
                "target_met": False
            }
    
    async def _test_cache_hit_rate(self) -> Dict[str, Any]:
        """Test cache hit rate with constitutional validation endpoint."""
        base_url = self.available_services["ac_service"]
        endpoint = f"{base_url}/api/v1/principles/validate-constitutional"
        
        # Test validation request
        test_request = {
            "proposal": {
                "id": "test_proposal",
                "title": "Test Constitutional Validation",
                "context": "governance",
                "respects_human_dignity": True,
                "ensures_fairness": True,
                "protects_privacy": True
            },
            "principles": [
                {"name": "Human Dignity", "category": "fundamental"},
                {"name": "Fairness", "category": "fundamental"}
            ]
        }
        
        total_requests = 0
        cache_hits = 0
        latencies = []
        
        async with aiohttp.ClientSession() as session:
            # Make multiple requests to test caching
            for i in range(20):
                start_time = time.time()
                
                try:
                    async with session.post(
                        endpoint,
                        json=test_request,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            total_requests += 1
                            latency = (time.time() - start_time) * 1000
                            latencies.append(latency)
                            
                            # Check if response indicates cache hit
                            response_data = await response.json()
                            if response_data.get("cached", False):
                                cache_hits += 1
                                
                except Exception as e:
                    logger.debug(f"Cache test request failed: {e}")
                
                # Small delay between requests
                await asyncio.sleep(0.1)
        
        hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return {
            "hit_rate": hit_rate,
            "average_latency": avg_latency,
            "total_requests": total_requests,
            "cache_hits": cache_hits
        }
    
    async def validate_constitutional_endpoint(self):
        """Validate constitutional validation endpoint implementation."""
        logger.info("\n⚖️ Validating Constitutional Validation Endpoint")
        logger.info("-" * 50)
        
        try:
            if "ac_service" in self.available_services:
                base_url = self.available_services["ac_service"]
                endpoint = f"{base_url}/api/v1/principles/validate-constitutional"
                
                test_request = {
                    "proposal": {
                        "id": "endpoint_test",
                        "title": "Endpoint Validation Test",
                        "context": "governance",
                        "respects_human_dignity": True,
                        "ensures_fairness": True,
                        "protects_privacy": True
                    },
                    "principles": []
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        endpoint,
                        json=test_request,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        endpoint_available = response.status == 200
                        
                        if endpoint_available:
                            response_data = await response.json()
                            has_validation_result = "validation_result" in response_data
                            has_caching_info = "cached" in response_data
                            has_latency_info = "latency_ms" in response_data
                        else:
                            has_validation_result = False
                            has_caching_info = False
                            has_latency_info = False
                
                self.validation_results["fixes_validated"]["constitutional_endpoint"] = {
                    "implemented": endpoint_available,
                    "endpoint_available": endpoint_available,
                    "response_structure_valid": has_validation_result and has_caching_info,
                    "caching_implemented": has_caching_info,
                    "latency_tracking": has_latency_info,
                    "target_met": endpoint_available and has_validation_result
                }
                
                logger.info(f"Endpoint Available: {'✅ YES' if endpoint_available else '❌ NO'}")
                logger.info(f"Response Structure: {'✅ VALID' if has_validation_result else '❌ INVALID'}")
                logger.info(f"Caching Implemented: {'✅ YES' if has_caching_info else '❌ NO'}")
                
            else:
                logger.warning("AC service not available - cannot validate endpoint")
                self.validation_results["fixes_validated"]["constitutional_endpoint"] = {
                    "implemented": False,
                    "error": "AC service not available",
                    "target_met": False
                }
                
        except Exception as e:
            logger.error(f"Constitutional endpoint validation failed: {e}")
            self.validation_results["fixes_validated"]["constitutional_endpoint"] = {
                "implemented": False,
                "error": str(e),
                "target_met": False
            }
    
    async def validate_cache_warming(self):
        """Validate cache warming implementation."""
        logger.info("\n🔥 Validating Cache Warming Implementation")
        logger.info("-" * 50)
        
        try:
            # Import cache warming service
            from src.backend.shared.cache_warming_service import CacheWarmingService, CacheWarmingConfig
            from src.backend.shared.redis_client import ACGSRedisClient
            
            # Initialize Redis client
            redis_client = ACGSRedisClient("validation_test")
            await redis_client.initialize()
            
            # Initialize cache warming service
            warming_service = CacheWarmingService(redis_client)
            await warming_service.initialize()
            
            # Test immediate warming
            warming_metrics = await warming_service.warm_cache_immediate()
            
            # Get warming stats
            warming_stats = warming_service.get_warming_stats()
            
            warming_successful = warming_metrics.successful_warmings > 0
            
            self.validation_results["fixes_validated"]["cache_warming"] = {
                "implemented": True,
                "warming_successful": warming_successful,
                "items_warmed": warming_metrics.total_items_warmed,
                "success_rate": (warming_metrics.successful_warmings / warming_metrics.total_items_warmed * 100) if warming_metrics.total_items_warmed > 0 else 0,
                "warming_duration": warming_metrics.warming_duration_seconds,
                "target_met": warming_successful
            }
            
            logger.info(f"Cache Warming: {'✅ SUCCESSFUL' if warming_successful else '❌ FAILED'}")
            logger.info(f"Items Warmed: {warming_metrics.total_items_warmed}")
            logger.info(f"Success Rate: {(warming_metrics.successful_warmings / warming_metrics.total_items_warmed * 100) if warming_metrics.total_items_warmed > 0 else 0:.1f}%")
            
            # Stop warming service
            await warming_service.stop_scheduled_warming()
            
        except Exception as e:
            logger.error(f"Cache warming validation failed: {e}")
            self.validation_results["fixes_validated"]["cache_warming"] = {
                "implemented": False,
                "error": str(e),
                "target_met": False
            }
    
    def generate_validation_report(self):
        """Generate comprehensive validation report."""
        logger.info("\n📊 Phase 3 Critical Fixes Validation Report")
        logger.info("=" * 60)
        
        fixes = self.validation_results["fixes_validated"]
        
        # Calculate overall success
        total_fixes = len(fixes)
        successful_fixes = sum(1 for fix in fixes.values() if fix.get("target_met", False))
        success_rate = (successful_fixes / total_fixes * 100) if total_fixes > 0 else 0
        
        logger.info(f"Overall Success Rate: {success_rate:.1f}% ({successful_fixes}/{total_fixes} fixes)")
        
        # Individual fix status
        for fix_name, fix_data in fixes.items():
            status = "✅ PASSED" if fix_data.get("target_met", False) else "❌ FAILED"
            logger.info(f"  {fix_name.replace('_', ' ').title()}: {status}")
        
        # Production readiness assessment
        production_ready = success_rate >= 80  # At least 80% of fixes must pass
        
        self.validation_results["production_readiness"] = {
            "overall_success_rate": success_rate,
            "successful_fixes": successful_fixes,
            "total_fixes": total_fixes,
            "production_ready": production_ready,
            "critical_issues": [
                fix_name for fix_name, fix_data in fixes.items()
                if not fix_data.get("target_met", False)
            ]
        }
        
        logger.info(f"\nProduction Readiness: {'✅ READY' if production_ready else '❌ NOT READY'}")
        
        if not production_ready:
            logger.warning("Critical issues must be resolved before production deployment:")
            for issue in self.validation_results["production_readiness"]["critical_issues"]:
                logger.warning(f"  - {issue.replace('_', ' ').title()}")
        
        # Save results
        with open("phase3_critical_fixes_validation_results.json", "w") as f:
            json.dump(self.validation_results, f, indent=2)
        
        logger.info(f"\n📄 Detailed results saved to: phase3_critical_fixes_validation_results.json")

async def main():
    """Run Phase 3 critical fixes validation."""
    validator = Phase3CriticalFixesValidator()
    results = await validator.validate_all_fixes()
    
    # Return appropriate exit code
    production_ready = results["production_readiness"]["production_ready"]
    return 0 if production_ready else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
