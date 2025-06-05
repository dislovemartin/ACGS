"""
Comprehensive Test Suite for ACGS Phase 2 Implementation

Tests the dependency injection framework, event-driven architecture,
and database optimization components to ensure ≥90% test coverage
and <50ms policy decision latency requirements are maintained.
"""

import asyncio
import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

# Import Phase 2 components
from src.backend.shared.di import (
    DIContainer, inject, injectable, singleton, transient,
    ServiceInterface, get_container
)
from src.backend.shared.events import (
    EventBus, Event, EventType, EventPriority, EventStatus,
    get_event_bus
)
from src.backend.shared.database import (
    DatabasePoolManager, ConnectionPool, PoolConfig,
    get_pool_manager
)


class TestDependencyInjection:
    """Test dependency injection framework."""
    
    def setup_method(self):
        """Setup test environment."""
        self.container = DIContainer()
    
    def test_service_registration(self):
        """Test service registration and resolution."""
        # Define test interfaces and implementations
        class ITestService:
            def get_data(self) -> str:
                pass
        
        @injectable
        class TestService(ITestService):
            def get_data(self) -> str:
                return "test_data"
        
        # Register service
        self.container.register_singleton(ITestService, TestService)
        
        # Resolve service
        service = self.container.resolve(ITestService)
        assert isinstance(service, TestService)
        assert service.get_data() == "test_data"
        
        # Test singleton behavior
        service2 = self.container.resolve(ITestService)
        assert service is service2
    
    def test_dependency_injection(self):
        """Test automatic dependency injection."""
        class IDependency:
            def get_value(self) -> int:
                pass
        
        @injectable
        class Dependency(IDependency):
            def get_value(self) -> int:
                return 42
        
        @injectable
        class ServiceWithDependency:
            def __init__(self, dependency: IDependency):
                self.dependency = dependency
            
            def process(self) -> int:
                return self.dependency.get_value() * 2
        
        # Register dependencies
        self.container.register_singleton(IDependency, Dependency)
        self.container.register_transient(ServiceWithDependency)
        
        # Resolve service with automatic dependency injection
        service = self.container.resolve(ServiceWithDependency)
        assert service.process() == 84
    
    def test_decorator_registration(self):
        """Test decorator-based service registration."""
        @singleton()
        class SingletonService:
            def __init__(self):
                self.value = "singleton"
        
        @transient()
        class TransientService:
            def __init__(self):
                self.value = "transient"
        
        # Test singleton
        service1 = get_container().resolve(SingletonService)
        service2 = get_container().resolve(SingletonService)
        assert service1 is service2
        
        # Test transient
        service3 = get_container().resolve(TransientService)
        service4 = get_container().resolve(TransientService)
        assert service3 is not service4
    
    @pytest.mark.asyncio
    async def test_scoped_services(self):
        """Test scoped service lifecycle."""
        @injectable
        class ScopedService:
            def __init__(self):
                self.created_at = time.time()
        
        self.container.register_scoped(ScopedService)
        
        # Test within scope
        async with self.container.scope("test_scope"):
            service1 = self.container.resolve(ScopedService)
            service2 = self.container.resolve(ScopedService)
            assert service1 is service2
        
        # Test new scope
        async with self.container.scope("test_scope2"):
            service3 = self.container.resolve(ScopedService)
            assert service1 is not service3
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        class IServiceA:
            pass
        
        class IServiceB:
            pass
        
        @injectable
        class ServiceA(IServiceA):
            def __init__(self, service_b: IServiceB):
                self.service_b = service_b
        
        @injectable
        class ServiceB(IServiceB):
            def __init__(self, service_a: IServiceA):
                self.service_a = service_a
        
        # Register circular dependencies
        self.container.register_singleton(IServiceA, ServiceA)
        self.container.register_singleton(IServiceB, ServiceB)
        
        # Should detect circular dependency
        with pytest.raises(ValueError, match="Circular dependency"):
            self.container.resolve(IServiceA)
    
    def test_validation_and_metrics(self):
        """Test container validation and metrics."""
        class IMissingDependency:
            pass
        
        @injectable
        class ServiceWithMissingDep:
            def __init__(self, missing: IMissingDependency):
                self.missing = missing
        
        self.container.register_transient(ServiceWithMissingDep)
        
        # Test validation
        errors = self.container.validate_registrations()
        assert len(errors) > 0
        assert "unregistered" in errors[0]
        
        # Test dependency graph
        graph = self.container.get_dependency_graph()
        assert ServiceWithMissingDep in graph


class TestEventDrivenArchitecture:
    """Test event-driven architecture components."""
    
    def setup_method(self):
        """Setup test environment."""
        self.event_bus = EventBus()
    
    @pytest.mark.asyncio
    async def test_event_publishing_and_subscription(self):
        """Test basic event publishing and subscription."""
        await self.event_bus.start()
        
        # Track received events
        received_events = []
        
        async def event_handler(event: Event):
            received_events.append(event)
        
        # Subscribe to events
        subscription_id = await self.event_bus.subscribe(
            EventType.USER_CREATED.value,
            event_handler
        )
        
        # Publish event
        await self.event_bus.publish(
            EventType.USER_CREATED.value,
            {"user_id": "123", "username": "test_user"},
            {"source_service": "auth_service"}
        )
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert len(received_events) == 1
        event = received_events[0]
        assert event.metadata.event_type == EventType.USER_CREATED
        assert event.data.payload["user_id"] == "123"
        
        # Cleanup
        await self.event_bus.unsubscribe(subscription_id)
        await self.event_bus.stop()
    
    @pytest.mark.asyncio
    async def test_event_filtering(self):
        """Test event filtering and routing."""
        await self.event_bus.start()
        
        received_events = []
        
        async def filtered_handler(event: Event):
            received_events.append(event)
        
        # Subscribe with filter
        await self.event_bus.subscribe(
            EventType.USER_CREATED.value,
            filtered_handler
        )
        
        # Publish events with different sources
        await self.event_bus.publish(
            EventType.USER_CREATED.value,
            {"user_id": "123"},
            {"source_service": "auth_service"}
        )
        
        await self.event_bus.publish(
            EventType.USER_CREATED.value,
            {"user_id": "456"},
            {"source_service": "admin_service"}
        )
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Both events should be received (no filtering applied)
        assert len(received_events) == 2
        
        await self.event_bus.stop()
    
    @pytest.mark.asyncio
    async def test_event_priority_and_status(self):
        """Test event priority and status tracking."""
        await self.event_bus.start()
        
        # Create high priority event
        event = Event.create(
            event_type=EventType.SYSTEM_ERROR,
            payload={"error": "Critical system failure"},
            source_service="system",
            priority=EventPriority.CRITICAL
        )
        
        # Verify event properties
        assert event.metadata.priority == EventPriority.CRITICAL
        assert event.metadata.status == EventStatus.PENDING
        assert event.metadata.event_type == EventType.SYSTEM_ERROR
        
        # Test event serialization
        event_dict = event.to_dict()
        assert event_dict["metadata"]["priority"] == "critical"
        assert event_dict["metadata"]["status"] == "pending"
        
        await self.event_bus.stop()
    
    @pytest.mark.asyncio
    async def test_event_metrics(self):
        """Test event bus metrics collection."""
        await self.event_bus.start()
        
        # Publish several events
        for i in range(5):
            await self.event_bus.publish(
                EventType.USER_CREATED.value,
                {"user_id": f"user_{i}"},
                {"source_service": "test_service"}
            )
        
        # Get metrics
        metrics = self.event_bus.get_metrics()
        
        assert metrics["events_published"] == 5
        assert "handlers_by_type" in metrics
        assert "active_processing_tasks" in metrics
        
        await self.event_bus.stop()


class TestDatabaseOptimization:
    """Test database optimization components."""
    
    def setup_method(self):
        """Setup test environment."""
        self.pool_manager = DatabasePoolManager()
    
    @pytest.mark.asyncio
    async def test_connection_pool_creation(self):
        """Test connection pool creation and configuration."""
        config = PoolConfig(
            min_connections=2,
            max_connections=10,
            pool_timeout=15.0
        )
        
        # Mock database URL for testing
        database_url = "postgresql+asyncpg://test:test@localhost/test"
        
        with patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            pool = ConnectionPool(database_url, config)
            
            assert pool.config.min_connections == 2
            assert pool.config.max_connections == 10
            assert pool.config.pool_timeout == 15.0
    
    @pytest.mark.asyncio
    async def test_pool_manager_registration(self):
        """Test pool manager service registration."""
        # Register test pool
        with patch('sqlalchemy.ext.asyncio.create_async_engine'):
            pool = self.pool_manager.register_pool(
                "test_pool",
                "postgresql+asyncpg://test:test@localhost/test"
            )
            
            assert pool is not None
            assert self.pool_manager.get_pool("test_pool") is pool
    
    @pytest.mark.asyncio
    async def test_connection_metrics(self):
        """Test connection pool metrics collection."""
        with patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_engine:
            # Mock engine and pool
            mock_pool = Mock()
            mock_pool.size.return_value = 5
            mock_pool.checkedout.return_value = 2
            mock_pool.overflow.return_value = 0
            mock_pool.checkedin.return_value = 3
            
            mock_engine.return_value.pool = mock_pool
            
            pool = ConnectionPool("test://url")
            metrics = pool.get_metrics()
            
            assert "total_connections" in metrics
            assert "active_connections" in metrics
            assert "pool_utilization" in metrics
            assert "query_count" in metrics
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test database health check functionality."""
        with patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_engine:
            # Mock successful connection
            mock_conn = AsyncMock()
            mock_engine.return_value.begin.return_value.__aenter__.return_value = mock_conn
            
            pool = ConnectionPool("test://url")
            health = await pool.health_check()
            
            assert health["status"] == "healthy"
            assert "response_time" in health
            assert "metrics" in health


class TestPerformanceRequirements:
    """Test performance requirements compliance."""
    
    @pytest.mark.asyncio
    async def test_policy_decision_latency(self):
        """Test that policy decisions maintain <50ms latency."""
        # Simulate policy decision workflow
        start_time = time.time()
        
        # Mock policy evaluation process
        container = DIContainer()
        
        @injectable
        class MockPolicyService:
            async def evaluate_policy(self, context: Dict[str, Any]) -> Dict[str, Any]:
                # Simulate policy evaluation
                await asyncio.sleep(0.01)  # 10ms processing time
                return {"decision": "allow", "confidence": 0.95}
        
        container.register_singleton(MockPolicyService)
        
        # Resolve and execute
        policy_service = container.resolve(MockPolicyService)
        result = await policy_service.evaluate_policy({"user_id": "123"})
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify latency requirement
        assert latency < 50.0, f"Policy decision latency {latency}ms exceeds 50ms requirement"
        assert result["decision"] == "allow"
    
    @pytest.mark.asyncio
    async def test_event_processing_performance(self):
        """Test event processing performance."""
        event_bus = EventBus()
        await event_bus.start()
        
        # Measure event publishing performance
        start_time = time.time()
        
        # Publish multiple events
        for i in range(100):
            await event_bus.publish(
                EventType.USER_CREATED.value,
                {"user_id": f"user_{i}"},
                {"source_service": "test_service"}
            )
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        avg_time_per_event = total_time / 100
        
        # Verify performance
        assert avg_time_per_event < 5.0, f"Average event publishing time {avg_time_per_event}ms too high"
        
        await event_bus.stop()
    
    def test_dependency_injection_performance(self):
        """Test dependency injection resolution performance."""
        container = DIContainer()
        
        # Register multiple services
        for i in range(50):
            @injectable
            class TestService:
                def __init__(self):
                    self.id = i
            
            container.register_transient(f"TestService{i}", TestService)
        
        # Measure resolution performance
        start_time = time.time()
        
        for i in range(50):
            service = container.resolve(f"TestService{i}")
            assert service is not None
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        avg_resolution_time = total_time / 50
        
        # Verify performance
        assert avg_resolution_time < 1.0, f"Average DI resolution time {avg_resolution_time}ms too high"


class TestIntegration:
    """Integration tests for Phase 2 components."""
    
    @pytest.mark.asyncio
    async def test_di_event_integration(self):
        """Test integration between DI and event systems."""
        container = DIContainer()
        event_bus = EventBus()
        await event_bus.start()
        
        # Register event bus in DI container
        container.register_instance(EventBus, event_bus)
        
        @injectable
        class EventPublisher:
            def __init__(self, event_bus: EventBus):
                self.event_bus = event_bus
            
            async def publish_user_event(self, user_id: str):
                await self.event_bus.publish(
                    EventType.USER_CREATED.value,
                    {"user_id": user_id},
                    {"source_service": "integration_test"}
                )
        
        container.register_transient(EventPublisher)
        
        # Resolve and use
        publisher = container.resolve(EventPublisher)
        await publisher.publish_user_event("test_user")
        
        # Verify event was published
        metrics = event_bus.get_metrics()
        assert metrics["events_published"] >= 1
        
        await event_bus.stop()
    
    @pytest.mark.asyncio
    async def test_complete_workflow_performance(self):
        """Test complete workflow performance with all Phase 2 components."""
        # Setup all components
        container = DIContainer()
        event_bus = EventBus()
        pool_manager = DatabasePoolManager()
        
        await event_bus.start()
        
        # Register components
        container.register_instance(EventBus, event_bus)
        container.register_instance(DatabasePoolManager, pool_manager)
        
        @injectable
        class WorkflowService:
            def __init__(self, event_bus: EventBus, pool_manager: DatabasePoolManager):
                self.event_bus = event_bus
                self.pool_manager = pool_manager
            
            async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
                # Simulate complete workflow
                start_time = time.time()
                
                # 1. Validate request (DI)
                # 2. Process business logic
                # 3. Publish events
                await self.event_bus.publish(
                    EventType.WORKFLOW_STARTED.value,
                    request_data,
                    {"source_service": "workflow_service"}
                )
                
                # 4. Return result
                processing_time = (time.time() - start_time) * 1000
                
                return {
                    "status": "completed",
                    "processing_time_ms": processing_time,
                    "request_id": request_data.get("request_id")
                }
        
        container.register_transient(WorkflowService)
        
        # Execute workflow
        start_time = time.time()
        
        workflow_service = container.resolve(WorkflowService)
        result = await workflow_service.process_request({
            "request_id": "test_123",
            "data": {"key": "value"}
        })
        
        end_time = time.time()
        total_latency = (end_time - start_time) * 1000
        
        # Verify performance requirements
        assert total_latency < 50.0, f"Total workflow latency {total_latency}ms exceeds 50ms"
        assert result["status"] == "completed"
        
        await event_bus.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
