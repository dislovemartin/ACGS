#!/usr/bin/env python3
"""
Integration test for enhanced dependency mocking system.
Tests comprehensive mocking of external dependencies and services.
"""

import asyncio
import pytest
import sys
import os
from typing import Dict, Any
from unittest.mock import patch, AsyncMock

# Add test utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/shared'))

from mock_services import (
    MockServiceManager, EnhancedHTTPXMock, MockLLMService, MockZ3Solver,
    mock_all_services, mock_service_communication, mock_database_session,
    create_mock_response, assert_service_called, get_service_call_count
)


class TestEnhancedDependencyMocking:
    """Test enhanced dependency mocking capabilities."""
    
    @pytest.mark.asyncio
    async def test_httpx_mock_service_communication(self):
        """Test HTTPX mock for cross-service communication."""
        
        service_responses = {
            'auth': {
                'health': {'status': 'ok', 'service': 'auth'},
                'verify': {'valid': True, 'user_id': 'test_user'},
            },
            'ac': {
                'health': {'status': 'ok', 'service': 'ac'},
                'principles': [
                    {'id': 1, 'title': 'Test Principle', 'content': 'Test content'}
                ],
            }
        }
        
        httpx_mock = EnhancedHTTPXMock(service_responses)
        
        # Test auth service health check
        auth_response = await httpx_mock.get('http://localhost:8000/health')
        assert auth_response.status_code == 200
        assert auth_response.json()['status'] == 'ok'
        assert auth_response.json()['service'] == 'auth'
        
        # Test AC service principles endpoint
        ac_response = await httpx_mock.get('http://localhost:8001/api/v1/principles')
        assert ac_response.status_code == 200
        principles = ac_response.json()
        assert len(principles) == 1
        assert principles[0]['title'] == 'Test Principle'
        
        # Test call tracking
        assert httpx_mock.call_count == 2
        assert httpx_mock.last_request['method'] == 'GET'
        assert 'principles' in httpx_mock.last_request['url']
    
    @pytest.mark.asyncio
    async def test_llm_service_mocking(self):
        """Test LLM service mocking with realistic responses."""
        
        llm_mock = MockLLMService()
        
        # Test text generation
        result = await llm_mock.generate_text("Generate a principle about fairness")
        
        assert 'generated_text' in result
        assert 'principle' in result['generated_text'].lower()
        assert result['confidence'] > 0.8
        assert result['tokens_used'] > 0
        assert result['model'] == 'mock-llm-v1'
        
        # Test embedding generation
        embedding = await llm_mock.generate_embedding("Test text for embedding")
        
        assert len(embedding) == 768  # Standard embedding size
        assert all(isinstance(val, float) for val in embedding)
        assert all(-0.5 <= val <= 0.5 for val in embedding)
        
        # Test statistics
        stats = llm_mock.get_generation_stats()
        assert stats['total_generations'] == 1
        assert stats['total_embeddings'] == 1
        assert stats['total_calls'] == 2
    
    @pytest.mark.asyncio
    async def test_z3_solver_mocking(self):
        """Test Z3 solver mocking for formal verification."""
        
        z3_mock = MockZ3Solver()
        
        # Test constraint addition
        z3_mock.add("x > 0")
        z3_mock.add("y < 10")
        
        # Test constraint checking
        result1 = z3_mock.check()
        assert result1 in ['sat', 'unsat', 'unknown']
        
        result2 = z3_mock.check()
        assert result2 in ['sat', 'unsat', 'unknown']
        
        # Results should cycle through different values
        result3 = z3_mock.check()
        assert result3 in ['sat', 'unsat', 'unknown']
        
        # Test model generation
        if result1 == 'sat':
            model = z3_mock.model()
            assert model is not None
        
        # Test statistics
        stats = z3_mock.get_stats()
        assert stats['constraints_added'] == 2
        assert stats['checks_performed'] == 3
        assert len(stats['current_constraints']) == 2
    
    @pytest.mark.asyncio
    async def test_database_session_mocking(self):
        """Test database session mocking with realistic behavior."""
        
        async with mock_database_session() as session:
            # Create a mock model instance
            class MockPrinciple:
                def __init__(self, title, content):
                    self.id = None
                    self.title = title
                    self.content = content
            
            # Test adding instance
            principle = MockPrinciple("Test Principle", "Test content")
            session.add(principle)
            
            # Check that ID was assigned
            assert principle.id == 1
            
            # Test commit
            await session.commit()
            
            # Test query operations
            result = await session.execute("SELECT * FROM principles")
            assert result is not None
            
            scalar_result = await session.scalar("SELECT COUNT(*) FROM principles")
            assert scalar_result is None  # Mock returns None
            
            # Test call history
            history = session.get_call_history()
            assert len(history) >= 3  # add, commit, execute calls
            
            method_calls = [call['method'] for call in history]
            assert 'add' in method_calls
            assert 'commit' in method_calls
            assert 'execute' in method_calls
    
    @pytest.mark.asyncio
    async def test_comprehensive_service_mocking(self):
        """Test comprehensive mocking of all services together."""
        
        async with mock_all_services() as mocks:
            httpx_mock = mocks['httpx']
            llm_mock = mocks['llm']
            z3_mock = mocks['z3']
            manager = mocks['manager']
            
            # Test cross-service communication
            auth_response = await httpx_mock.get('http://auth_service:8000/health')
            assert auth_response.status_code == 200
            
            ac_response = await httpx_mock.get('http://ac_service:8001/api/v1/principles')
            assert ac_response.status_code == 200
            
            # Test LLM integration
            llm_result = await llm_mock.generate_text("Synthesize policy from principles")
            assert 'policy' in llm_result['generated_text'].lower()
            
            # Test formal verification
            z3_mock.add("policy_valid = True")
            verification_result = z3_mock.check()
            assert verification_result in ['sat', 'unsat', 'unknown']
            
            # Test service manager
            assert manager.get_service_mock('httpx') == httpx_mock
            assert manager.get_service_mock('llm') == llm_mock
            assert manager.get_service_mock('z3') == z3_mock
    
    @pytest.mark.asyncio
    async def test_service_communication_context_manager(self):
        """Test service communication context manager."""
        
        async with mock_service_communication() as mocks:
            httpx_mock = mocks['httpx']
            
            # Test all service health checks
            services = ['auth', 'ac', 'fv', 'gs', 'integrity', 'pgc']
            
            for service in services:
                if service == 'auth':
                    url = 'http://auth_service:8000/health'
                else:
                    port = 8001 + ['ac', 'integrity', 'fv', 'gs', 'pgc'].index(service)
                    url = f'http://localhost:{port}/health'
                
                response = await httpx_mock.get(url)
                assert response.status_code == 200
                assert response.json()['status'] == 'ok'
                assert response.json()['service'] in [service, service.replace('_service', '')]
    
    def test_mock_response_creation(self):
        """Test mock response creation utility."""
        
        # Test successful response
        response = create_mock_response(200, {'message': 'success'})
        assert response.status_code == 200
        assert response.json() == {'message': 'success'}
        
        # Test error response
        error_response = create_mock_response(
            404, 
            {'error': 'Not found'}, 
            {'Content-Type': 'application/json'}
        )
        assert error_response.status_code == 404
        assert error_response.json() == {'error': 'Not found'}
        assert error_response.headers['Content-Type'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_service_call_tracking(self):
        """Test service call tracking and verification."""
        
        manager = MockServiceManager()
        
        # Register a mock service
        mock_service = AsyncMock()
        manager.register_service_mock('test_service', mock_service)
        
        # Record some calls
        manager.record_call('test_service', 'get_data', (), {})
        manager.record_call('test_service', 'post_data', ({'data': 'test'},), {})
        manager.record_call('test_service', 'get_data', (), {})
        
        # Test call history
        history = manager.get_call_history('test_service')
        assert len(history) == 3
        
        # Test call counting
        get_calls = [call for call in history if call['method'] == 'get_data']
        post_calls = [call for call in history if call['method'] == 'post_data']
        
        assert len(get_calls) == 2
        assert len(post_calls) == 1
        
        # Test service retrieval
        retrieved_service = manager.get_service_mock('test_service')
        assert retrieved_service == mock_service
    
    @pytest.mark.asyncio
    async def test_mock_integration_with_real_code_patterns(self):
        """Test mocking integration with realistic code patterns."""
        
        # Simulate a service client pattern
        class MockServiceClient:
            def __init__(self, httpx_client):
                self.client = httpx_client
            
            async def get_principles(self):
                response = await self.client.get('http://ac_service:8001/api/v1/principles')
                return response.json()
            
            async def detect_bias(self, data):
                response = await self.client.post(
                    'http://fv_service:8003/api/v1/bias-detection',
                    json=data
                )
                return response.json()
        
        # Test with mocked services
        async with mock_service_communication() as mocks:
            httpx_mock = mocks['httpx']
            client = MockServiceClient(httpx_mock)
            
            # Test principles retrieval
            principles = await client.get_principles()
            assert isinstance(principles, list)
            assert len(principles) == 1
            assert principles[0]['id'] == 1
            
            # Test bias detection
            bias_result = await client.detect_bias({'test': 'data'})
            assert 'overall_bias_score' in bias_result
            assert bias_result['risk_level'] == 'low'


@pytest.mark.asyncio
async def test_dependency_mocking_performance():
    """Test performance of dependency mocking system."""
    import time
    
    start_time = time.time()
    
    # Test multiple concurrent mock operations
    async with mock_all_services() as mocks:
        httpx_mock = mocks['httpx']
        llm_mock = mocks['llm']
        
        # Simulate concurrent service calls
        tasks = []
        
        for i in range(10):
            tasks.append(httpx_mock.get(f'http://service_{i}:800{i}/health'))
            tasks.append(llm_mock.generate_text(f"Test prompt {i}"))
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed
        assert len(results) == 20
        
        # Check that HTTP responses are valid
        http_responses = results[::2]  # Every other result
        for response in http_responses:
            assert response.status_code == 200
        
        # Check that LLM responses are valid
        llm_responses = results[1::2]  # Every other result
        for response in llm_responses:
            assert 'generated_text' in response
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Performance should be reasonable (under 1 second for 20 operations)
    assert execution_time < 1.0, f"Mocking operations took too long: {execution_time:.2f}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
