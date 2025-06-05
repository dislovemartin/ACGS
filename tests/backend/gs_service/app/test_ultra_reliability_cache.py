import asyncio
import pytest
from unittest.mock import AsyncMock

import sys
import types
tenacity_mod = types.ModuleType("tenacity")
tenacity_mod.retry = lambda *a, **k: (lambda f: f)
tenacity_mod.stop_after_attempt = lambda *a, **k: None
tenacity_mod.wait_exponential = lambda *a, **k: None
class RetryError(Exception):
    pass
tenacity_mod.RetryError = RetryError
sys.modules.setdefault("tenacity", tenacity_mod)
sys.modules.setdefault("openai", types.ModuleType("openai"))
shared_mod = types.ModuleType("shared")
auth_mod = types.ModuleType("auth")
auth_mod.get_service_token = lambda: ""
auth_mod.get_auth_headers = lambda token=None: {}
shared_mod.auth = auth_mod
sys.modules.setdefault("shared", shared_mod)
sys.modules.setdefault("shared.auth", auth_mod)


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

from src.backend.gs_service.app.core.llm_reliability_framework import (
    EnhancedMultiModelValidator,
    LLMReliabilityConfig,
    PrometheusMetricsCollector,
    UltraReliableResult,
    LLMStructuredOutput,
    LLMInterpretationInput,
)

@pytest.mark.asyncio
async def test_ultra_reliable_result_caching():
    config = LLMReliabilityConfig(cache_enabled=False)
    collector = PrometheusMetricsCollector(enabled=False)
    validator = EnhancedMultiModelValidator(config, collector)

    # Patch internal stages to return deterministic results
    validator._parallel_synthesis = AsyncMock(return_value=([
        {
            "model_name": "m1",
            "synthesis_output": LLMStructuredOutput(interpretations=[], raw_llm_response="policy"),
            "weight": 1.0,
            "type": "test",
            "response_time": 0.1,
        }
    ], [], {"avg_individual_response_time": 0.1, "p95_individual_response_time": 0.1, "p99_individual_response_time": 0.1, "synthesis_throughput_rps": 10.0, "response_times_map": {"m1": 0.1}, "synthesis_attempts": 1}))
    validator._cross_validate_results = AsyncMock(return_value={"m1": {"m1": {"score": 1.0}}})
    validator._validate_semantic_consistency = AsyncMock(return_value={"m1": {"overall_score": 0.9}})
    validator._attempt_formal_verification = AsyncMock(return_value={"m1": {"verified": True}})
    validator._weighted_consensus_decision = AsyncMock(return_value=(LLMStructuredOutput(interpretations=[], raw_llm_response="policy"), 0.95, {}))

    input_data = LLMInterpretationInput(principle_id=1, principle_content="p", target_context="c")
    result1 = await validator.achieve_ultra_reliable_consensus(input_data)
    assert isinstance(result1, UltraReliableResult)
    assert validator._parallel_synthesis.call_count == 1
    assert len(validator.performance_history) == 1

    # Second call should hit cache
    result2 = await validator.achieve_ultra_reliable_consensus(input_data)
    assert isinstance(result2, UltraReliableResult)
    # Methods should not be called again
    assert validator._parallel_synthesis.call_count == 1
    assert len(validator.performance_history) == 2
    assert result1 is result2

