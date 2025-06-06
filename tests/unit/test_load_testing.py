import pytest
import asyncio
from datetime import datetime, timezone

from scripts.load_testing import (
    LoadTester,
    LoadTestConfig,
    TestResult,
    DatabasePerformanceMetrics,
)

@pytest.mark.asyncio
async def test_database_metrics_in_report(monkeypatch):
    async def mock_service_health(self, service, port):
        return TestResult(
            service=service,
            endpoint="/health",
            response_time_ms=1.0,
            status_code=200,
            success=True,
            timestamp=datetime.now(timezone.utc),
        )

    async def mock_cross_service(self):
        return []

    async def mock_alpha(self):
        return []

    async def mock_db_perf(self):
        return DatabasePerformanceMetrics(
            connection_time_ms=1.0,
            avg_query_time_ms=2.0,
            throughput_qps=100.0,
        )

    monkeypatch.setattr(LoadTester, "test_service_health", mock_service_health)
    monkeypatch.setattr(LoadTester, "test_cross_service_communication", mock_cross_service)
    monkeypatch.setattr(LoadTester, "test_alphaevolve_integration", mock_alpha)
    monkeypatch.setattr(LoadTester, "test_database_performance", mock_db_perf)

    config = LoadTestConfig(concurrent_users=1)
    async with LoadTester(config) as tester:
        report = await tester.run_load_test()

    assert report.database_performance.throughput_qps == 100.0
    assert report.database_performance.connection_time_ms == 1.0
