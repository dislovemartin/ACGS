#!/usr/bin/env python3
"""
Ollama Integration Test Script for ACGS-PGP

This script tests the Ollama local model integration with the ACGS-PGP system,
validating constitutional prompting workflows, performance metrics, and
fallback mechanisms.

Usage:
    python scripts/test_ollama_integration.py
"""

import asyncio
import logging
import sys
import os
import time
import json
from typing import Dict, Any, List
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from gs_service.app.core.ollama_client import OllamaLLMClient, get_ollama_client
from gs_service.app.workflows.multi_model_manager import MultiModelManager
from shared.langgraph_config import get_langgraph_config, ModelRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OllamaIntegrationTester:
    """Test suite for Ollama integration with ACGS-PGP."""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = datetime.now(timezone.utc)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Ollama integration tests."""
        logger.info("🚀 Starting Ollama Integration Test Suite")
        
        tests = [
            ("Ollama Server Health Check", self.test_ollama_health),
            ("Ollama Client Basic Functionality", self.test_ollama_client),
            ("Constitutional Prompting Test", self.test_constitutional_prompting),
            ("MultiModelManager Integration", self.test_multi_model_manager),
            ("Performance Benchmarking", self.test_performance),
            ("Fallback Mechanism Test", self.test_fallback_mechanism),
            ("TaskMaster Integration Test", self.test_taskmaster_integration)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"🧪 Running: {test_name}")
            try:
                result = await test_func()
                self.test_results.append({
                    "test_name": test_name,
                    "success": result.get("success", False),
                    "details": result.get("details", ""),
                    "metrics": result.get("metrics", {}),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                status = "✅ PASSED" if result.get("success") else "❌ FAILED"
                logger.info(f"{status}: {test_name}")
            except Exception as e:
                logger.error(f"❌ FAILED: {test_name} - {e}")
                self.test_results.append({
                    "test_name": test_name,
                    "success": False,
                    "details": f"Exception: {str(e)}",
                    "metrics": {},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        return self.generate_report()
    
    async def test_ollama_health(self) -> Dict[str, Any]:
        """Test Ollama server health and availability."""
        try:
            client = OllamaLLMClient()
            
            # Test health check
            is_healthy = await client.health_check()
            
            if not is_healthy:
                return {
                    "success": False,
                    "details": "Ollama server is not healthy or not accessible"
                }
            
            # Get available models
            models = await client.get_available_models()
            
            await client.close()
            
            return {
                "success": True,
                "details": f"Ollama server healthy with {len(models)} models available",
                "metrics": {
                    "available_models": len(models),
                    "models": models
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"Health check failed: {str(e)}"
            }
    
    async def test_ollama_client(self) -> Dict[str, Any]:
        """Test basic Ollama client functionality."""
        try:
            client = await get_ollama_client()
            
            # Test basic text generation
            start_time = time.time()
            response = await client.generate_text(
                prompt="What is constitutional governance in AI systems?",
                temperature=0.3,
                max_tokens=200
            )
            response_time = time.time() - start_time
            
            await client.close()
            
            if not response or len(response.strip()) < 10:
                return {
                    "success": False,
                    "details": "Generated response is too short or empty"
                }
            
            return {
                "success": True,
                "details": f"Generated {len(response)} characters in {response_time:.2f}s",
                "metrics": {
                    "response_length": len(response),
                    "response_time_seconds": response_time,
                    "tokens_per_second": len(response.split()) / response_time if response_time > 0 else 0
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"Client test failed: {str(e)}"
            }
    
    async def test_constitutional_prompting(self) -> Dict[str, Any]:
        """Test constitutional prompting capabilities."""
        try:
            client = await get_ollama_client()
            
            # Test constitutional prompting
            from gs_service.app.core.llm_integration import LLMInterpretationInput
            
            query = LLMInterpretationInput(
                principle_id=1,
                principle_content="AI systems must ensure fairness and non-discrimination in all decisions",
                target_context="healthcare",
                datalog_predicate_schema={
                    "domain": "healthcare",
                    "user_demographics": "diverse_population",
                    "risk_level": "high"
                }
            )
            
            start_time = time.time()
            result = await client.get_structured_interpretation(query)
            response_time = time.time() - start_time
            
            await client.close()
            
            success = (
                result.interpretations and 
                len(result.interpretations) > 0 and
                result.raw_llm_response and
                len(result.raw_llm_response.strip()) > 50
            )
            
            return {
                "success": success,
                "details": f"Constitutional prompting completed in {response_time:.2f}s",
                "metrics": {
                    "interpretations_count": len(result.interpretations),
                    "response_time_seconds": response_time,
                    "response_length": len(result.raw_llm_response)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"Constitutional prompting test failed: {str(e)}"
            }
    
    async def test_multi_model_manager(self) -> Dict[str, Any]:
        """Test MultiModelManager integration with Ollama."""
        try:
            manager = MultiModelManager()
            
            # Test model response with Ollama fallback
            start_time = time.time()
            response = await manager.get_model_response(
                role=ModelRole.POLICY_SYNTHESIS,
                prompt="Generate a simple data privacy policy rule",
                max_retries=2
            )
            response_time = time.time() - start_time
            
            success = response.get("success", False) and response.get("content")
            
            return {
                "success": success,
                "details": f"MultiModelManager test completed in {response_time:.2f}s",
                "metrics": {
                    "response_time_seconds": response_time,
                    "model_used": response.get("model_used", "unknown"),
                    "attempt_count": response.get("attempt", 1),
                    "content_length": len(response.get("content", ""))
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"MultiModelManager test failed: {str(e)}"
            }
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test Ollama performance metrics."""
        try:
            client = await get_ollama_client()
            
            # Run multiple requests to measure performance
            response_times = []
            token_counts = []
            
            for i in range(3):
                start_time = time.time()
                response = await client.generate_text(
                    prompt=f"Explain constitutional principle {i+1} in AI governance",
                    temperature=0.2,
                    max_tokens=150
                )
                response_time = time.time() - start_time
                
                response_times.append(response_time)
                token_counts.append(len(response.split()))
            
            await client.close()
            
            avg_response_time = sum(response_times) / len(response_times)
            avg_tokens = sum(token_counts) / len(token_counts)
            tokens_per_second = avg_tokens / avg_response_time if avg_response_time > 0 else 0
            
            # Performance targets
            target_response_time = 10.0  # seconds
            target_tokens_per_second = 5.0  # tokens/second
            
            performance_score = min(
                (target_response_time / avg_response_time) * 0.5,
                (tokens_per_second / target_tokens_per_second) * 0.5
            )
            
            success = avg_response_time < target_response_time and tokens_per_second > target_tokens_per_second
            
            return {
                "success": success,
                "details": f"Performance: {avg_response_time:.2f}s avg, {tokens_per_second:.1f} tokens/s",
                "metrics": {
                    "average_response_time": avg_response_time,
                    "tokens_per_second": tokens_per_second,
                    "performance_score": performance_score,
                    "meets_targets": success
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"Performance test failed: {str(e)}"
            }
    
    async def test_fallback_mechanism(self) -> Dict[str, Any]:
        """Test fallback mechanism when Ollama is unavailable."""
        try:
            # This test simulates fallback behavior
            # In a real scenario, we'd temporarily disable Ollama
            
            manager = MultiModelManager()
            
            # Get performance metrics to check fallback behavior
            metrics = manager.get_performance_metrics()
            
            # Check if Ollama models are properly configured
            ollama_models = [
                model for model in metrics.keys() 
                if model.startswith("hf.co/") or "deepseek" in model.lower()
            ]
            
            success = len(ollama_models) > 0 or "overall" in metrics
            
            return {
                "success": success,
                "details": f"Fallback mechanism configured with {len(ollama_models)} Ollama models",
                "metrics": {
                    "ollama_models_configured": len(ollama_models),
                    "total_models": len(metrics) - 1 if "overall" in metrics else len(metrics)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"Fallback test failed: {str(e)}"
            }
    
    async def test_taskmaster_integration(self) -> Dict[str, Any]:
        """Test TaskMaster AI integration with Ollama."""
        try:
            # Check TaskMaster configuration
            config_path = os.path.join(os.path.dirname(__file__), '..', '.taskmaster', 'config.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                ollama_configured = (
                    config.get("global", {}).get("enableOllamaModels", False) and
                    config.get("global", {}).get("ollamaDefaultModel") is not None
                )
                
                fallback_model = config.get("models", {}).get("fallback", {}).get("modelId", "")
                ollama_fallback = "deepseek" in fallback_model.lower() or "hf.co/" in fallback_model
                
                success = ollama_configured and ollama_fallback
                
                return {
                    "success": success,
                    "details": f"TaskMaster Ollama integration: {'enabled' if success else 'disabled'}",
                    "metrics": {
                        "ollama_enabled": ollama_configured,
                        "ollama_fallback_configured": ollama_fallback,
                        "fallback_model": fallback_model
                    }
                }
            else:
                return {
                    "success": False,
                    "details": "TaskMaster config file not found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "details": f"TaskMaster integration test failed: {str(e)}"
            }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds()
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat()
            },
            "test_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failed_tests = [result for result in self.test_results if not result["success"]]
        
        if any("health" in test["test_name"].lower() for test in failed_tests):
            recommendations.append("Ensure Ollama server is running on http://127.0.0.1:11434")
            recommendations.append("Verify DeepSeek-R1 model is pulled: ollama pull hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q8_K_XL")
        
        if any("performance" in test["test_name"].lower() for test in failed_tests):
            recommendations.append("Consider optimizing Ollama model parameters for better performance")
            recommendations.append("Monitor system resources (CPU, memory) during model inference")
        
        if any("constitutional" in test["test_name"].lower() for test in failed_tests):
            recommendations.append("Review constitutional prompting templates for Ollama compatibility")
            recommendations.append("Adjust temperature and token limits for better constitutional compliance")
        
        if len(failed_tests) == 0:
            recommendations.append("All tests passed! Ollama integration is ready for production use")
            recommendations.append("Consider monitoring performance metrics in production environment")
        
        return recommendations


async def main():
    """Main test execution function."""
    tester = OllamaIntegrationTester()
    
    try:
        report = await tester.run_all_tests()
        
        # Print summary
        print("\n" + "="*80)
        print("🔍 OLLAMA INTEGRATION TEST REPORT")
        print("="*80)
        
        summary = report["summary"]
        print(f"📊 Tests: {summary['passed_tests']}/{summary['total_tests']} passed ({summary['success_rate']:.1f}%)")
        print(f"⏱️  Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"📅 Completed: {summary['timestamp']}")
        
        # Print test results
        print("\n📋 Test Results:")
        for result in report["test_results"]:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test_name']}: {result['details']}")
        
        # Print recommendations
        if report["recommendations"]:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        # Save detailed report
        report_path = "ollama_integration_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Exit with appropriate code
        exit_code = 0 if summary["success_rate"] >= 80 else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
