#!/usr/bin/env python3
"""
ACGS-PGP Performance Optimization Suite
Analyzes and optimizes database queries, LLM inference, and API response times
"""

import asyncio
import aiohttp
import time
import statistics
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

class PerformanceOptimizer:
    def __init__(self):
        self.session = None
        self.performance_metrics = {}
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
    
    async def measure_endpoint_performance(self, service: str, endpoint: str, 
                                         method: str = "GET", data: Optional[Dict] = None,
                                         iterations: int = 10) -> Dict[str, float]:
        """Measure performance metrics for a specific endpoint"""
        response_times = []
        success_count = 0
        
        url = f"{self.base_urls[service]}{endpoint}"
        
        for i in range(iterations):
            start_time = time.time()
            try:
                if method.upper() == "GET":
                    async with self.session.get(url) as response:
                        await response.read()
                        if response.status < 400:
                            success_count += 1
                elif method.upper() == "POST":
                    async with self.session.post(url, json=data) as response:
                        await response.read()
                        if response.status < 400:
                            success_count += 1
                
                end_time = time.time()
                response_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
                
            except Exception as e:
                print(f"⚠️ Request {i+1} failed: {str(e)}")
                continue
        
        if response_times:
            return {
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "success_rate": (success_count / iterations) * 100,
                "total_requests": iterations
            }
        else:
            return {
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "median_response_time": 0,
                "success_rate": 0,
                "total_requests": iterations
            }
    
    async def test_database_query_performance(self) -> Dict[str, Dict[str, float]]:
        """Test database query performance across services"""
        print("\n🗄️ Testing Database Query Performance...")
        
        db_tests = {
            "ac_principles_list": {
                "service": "ac",
                "endpoint": "/principles",
                "method": "GET"
            },
            "ac_principles_search": {
                "service": "ac", 
                "endpoint": "/principles/search",
                "method": "POST",
                "data": {"query": "safety", "category": "Safety"}
            },
            "integrity_audit_logs": {
                "service": "integrity",
                "endpoint": "/audit/logs",
                "method": "GET"
            },
            "integrity_policy_rules": {
                "service": "integrity",
                "endpoint": "/policies/rules",
                "method": "GET"
            }
        }
        
        results = {}
        for test_name, test_config in db_tests.items():
            print(f"  Testing {test_name}...")
            metrics = await self.measure_endpoint_performance(
                service=test_config["service"],
                endpoint=test_config["endpoint"],
                method=test_config["method"],
                data=test_config.get("data"),
                iterations=20
            )
            results[test_name] = metrics
            
            # Performance assessment
            avg_time = metrics["avg_response_time"]
            if avg_time < 100:
                status = "✅ Excellent"
            elif avg_time < 500:
                status = "✅ Good"
            elif avg_time < 1000:
                status = "⚠️ Acceptable"
            else:
                status = "❌ Needs optimization"
            
            print(f"    {status} - Avg: {avg_time:.1f}ms, Success: {metrics['success_rate']:.1f}%")
        
        return results
    
    async def test_llm_inference_performance(self) -> Dict[str, Dict[str, float]]:
        """Test LLM inference performance"""
        print("\n🤖 Testing LLM Inference Performance...")
        
        llm_tests = {
            "constitutional_synthesis": {
                "service": "gs",
                "endpoint": "/constitutional/synthesize",
                "method": "POST",
                "data": {
                    "context": "performance_test",
                    "category": "efficiency",
                    "synthesis_request": "Generate a simple access control policy",
                    "target_format": "rego"
                }
            },
            "contextual_analysis": {
                "service": "gs",
                "endpoint": "/constitutional/analyze-context",
                "method": "POST",
                "data": {
                    "context": "performance_test",
                    "environmental_factors": {
                        "regulatory_environment": "GDPR",
                        "risk_level": "medium"
                    }
                }
            }
        }
        
        results = {}
        for test_name, test_config in llm_tests.items():
            print(f"  Testing {test_name}...")
            metrics = await self.measure_endpoint_performance(
                service=test_config["service"],
                endpoint=test_config["endpoint"],
                method=test_config["method"],
                data=test_config["data"],
                iterations=5  # Fewer iterations for LLM tests due to cost/time
            )
            results[test_name] = metrics
            
            # LLM performance assessment (different thresholds)
            avg_time = metrics["avg_response_time"]
            if avg_time < 2000:
                status = "✅ Excellent"
            elif avg_time < 5000:
                status = "✅ Good"
            elif avg_time < 10000:
                status = "⚠️ Acceptable"
            else:
                status = "❌ Needs optimization"
            
            print(f"    {status} - Avg: {avg_time:.1f}ms, Success: {metrics['success_rate']:.1f}%")
        
        return results
    
    async def test_z3_solver_performance(self) -> Dict[str, Dict[str, float]]:
        """Test Z3 SMT solver performance"""
        print("\n🔍 Testing Z3 Solver Performance...")
        
        z3_tests = {
            "simple_verification": {
                "service": "fv",
                "endpoint": "/verify/smt-solver",
                "method": "POST",
                "data": {
                    "datalog_rules": [
                        "allow(user, read) :- authenticated(user)."
                    ],
                    "proof_obligations": [
                        "∀user. authenticated(user) → allow(user, read)"
                    ]
                }
            },
            "complex_verification": {
                "service": "fv",
                "endpoint": "/verify/smt-solver",
                "method": "POST",
                "data": {
                    "datalog_rules": [
                        "allow(user, action) :- role(user, admin), action = read.",
                        "allow(user, action) :- role(user, user), action = read, owner(user, resource).",
                        "deny(user, action) :- blacklisted(user)."
                    ],
                    "proof_obligations": [
                        "∀user,action. allow(user,action) ∧ ¬deny(user,action) → authorized(user,action)",
                        "∀user. blacklisted(user) → ∀action. ¬allow(user,action)"
                    ]
                }
            }
        }
        
        results = {}
        for test_name, test_config in z3_tests.items():
            print(f"  Testing {test_name}...")
            metrics = await self.measure_endpoint_performance(
                service=test_config["service"],
                endpoint=test_config["endpoint"],
                method=test_config["method"],
                data=test_config["data"],
                iterations=10
            )
            results[test_name] = metrics
            
            # Z3 performance assessment
            avg_time = metrics["avg_response_time"]
            if avg_time < 500:
                status = "✅ Excellent"
            elif avg_time < 2000:
                status = "✅ Good"
            elif avg_time < 5000:
                status = "⚠️ Acceptable"
            else:
                status = "❌ Needs optimization"
            
            print(f"    {status} - Avg: {avg_time:.1f}ms, Success: {metrics['success_rate']:.1f}%")
        
        return results
    
    async def test_cryptographic_performance(self) -> Dict[str, Dict[str, float]]:
        """Test cryptographic operations performance"""
        print("\n🔐 Testing Cryptographic Performance...")
        
        crypto_tests = {
            "signature_creation": {
                "service": "integrity",
                "endpoint": "/crypto/sign",
                "method": "POST",
                "data": {
                    "data": "Test data for performance measurement",
                    "key_purpose": "policy_signing"
                }
            },
            "hash_generation": {
                "service": "integrity",
                "endpoint": "/crypto/hash",
                "method": "POST",
                "data": {
                    "data": "Test data for hash performance measurement"
                }
            }
        }
        
        results = {}
        for test_name, test_config in crypto_tests.items():
            print(f"  Testing {test_name}...")
            metrics = await self.measure_endpoint_performance(
                service=test_config["service"],
                endpoint=test_config["endpoint"],
                method=test_config["method"],
                data=test_config["data"],
                iterations=15
            )
            results[test_name] = metrics
            
            # Crypto performance assessment
            avg_time = metrics["avg_response_time"]
            if avg_time < 50:
                status = "✅ Excellent"
            elif avg_time < 200:
                status = "✅ Good"
            elif avg_time < 500:
                status = "⚠️ Acceptable"
            else:
                status = "❌ Needs optimization"
            
            print(f"    {status} - Avg: {avg_time:.1f}ms, Success: {metrics['success_rate']:.1f}%")
        
        return results
    
    def generate_optimization_recommendations(self, all_results: Dict) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Database optimization recommendations
        db_results = all_results.get("database", {})
        slow_db_queries = [name for name, metrics in db_results.items() 
                          if metrics["avg_response_time"] > 500]
        if slow_db_queries:
            recommendations.append(f"🗄️ Optimize database queries: {', '.join(slow_db_queries)}")
            recommendations.append("   - Add database indexes on frequently queried fields")
            recommendations.append("   - Implement query result caching")
            recommendations.append("   - Consider database connection pooling optimization")
        
        # LLM optimization recommendations
        llm_results = all_results.get("llm", {})
        slow_llm_calls = [name for name, metrics in llm_results.items() 
                         if metrics["avg_response_time"] > 5000]
        if slow_llm_calls:
            recommendations.append(f"🤖 Optimize LLM inference: {', '.join(slow_llm_calls)}")
            recommendations.append("   - Implement response caching for similar requests")
            recommendations.append("   - Use smaller, faster models for simple tasks")
            recommendations.append("   - Implement request batching")
        
        # Z3 optimization recommendations
        z3_results = all_results.get("z3", {})
        slow_z3_verifications = [name for name, metrics in z3_results.items() 
                               if metrics["avg_response_time"] > 2000]
        if slow_z3_verifications:
            recommendations.append(f"🔍 Optimize Z3 solver: {', '.join(slow_z3_verifications)}")
            recommendations.append("   - Implement verification result caching")
            recommendations.append("   - Use incremental solving for related queries")
            recommendations.append("   - Optimize constraint formulation")
        
        # Crypto optimization recommendations
        crypto_results = all_results.get("crypto", {})
        slow_crypto_ops = [name for name, metrics in crypto_results.items() 
                          if metrics["avg_response_time"] > 200]
        if slow_crypto_ops:
            recommendations.append(f"🔐 Optimize cryptographic operations: {', '.join(slow_crypto_ops)}")
            recommendations.append("   - Use hardware security modules (HSM)")
            recommendations.append("   - Implement key caching")
            recommendations.append("   - Consider parallel signature verification")
        
        return recommendations
    
    async def run_performance_analysis(self) -> Dict:
        """Run comprehensive performance analysis"""
        print("🚀 ACGS-PGP Performance Optimization Suite")
        print("=" * 60)
        print(f"Analysis started at: {datetime.now().isoformat()}")
        
        all_results = {}
        
        # Run performance tests
        all_results["database"] = await self.test_database_query_performance()
        all_results["llm"] = await self.test_llm_inference_performance()
        all_results["z3"] = await self.test_z3_solver_performance()
        all_results["crypto"] = await self.test_cryptographic_performance()
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(all_results)
        
        # Print summary
        print("\n" + "=" * 60)
        print("PERFORMANCE ANALYSIS SUMMARY")
        print("=" * 60)
        
        if recommendations:
            print("📋 Optimization Recommendations:")
            for rec in recommendations:
                print(f"  {rec}")
        else:
            print("✅ All performance metrics are within acceptable ranges!")
        
        return {
            "results": all_results,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Main performance analysis function"""
    async with PerformanceOptimizer() as optimizer:
        analysis_results = await optimizer.run_performance_analysis()
        
        # Save results to file
        with open("performance_analysis_results.json", "w") as f:
            json.dump(analysis_results, f, indent=2)
        
        print(f"\n📊 Results saved to: performance_analysis_results.json")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
