#!/usr/bin/env python3
"""
Enhanced service mocking utilities for ACGS-PGP integration tests.
Provides comprehensive mocking for external dependencies and services.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager
import httpx
from datetime import datetime, timedelta


class MockServiceManager:
    """
    Centralized manager for service mocks with enhanced dependency injection.
    """
    
    def __init__(self):
        self.active_mocks = {}
        self.mock_responses = {}
        self.call_history = {}
    
    def register_service_mock(self, service_name: str, mock_instance: Any):
        """Register a mock service instance."""
        self.active_mocks[service_name] = mock_instance
        self.call_history[service_name] = []
    
    def get_service_mock(self, service_name: str) -> Any:
        """Get a registered mock service."""
        return self.active_mocks.get(service_name)
    
    def record_call(self, service_name: str, method: str, args: tuple, kwargs: dict):
        """Record a service call for verification."""
        call_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'method': method,
            'args': args,
            'kwargs': kwargs,
        }
        
        if service_name not in self.call_history:
            self.call_history[service_name] = []
        
        self.call_history[service_name].append(call_record)
    
    def get_call_history(self, service_name: str) -> List[Dict]:
        """Get call history for a service."""
        return self.call_history.get(service_name, [])
    
    def reset_all_mocks(self):
        """Reset all registered mocks."""
        for mock in self.active_mocks.values():
            if hasattr(mock, 'reset_mock'):
                mock.reset_mock()
        
        self.call_history.clear()


# Global mock manager instance
mock_manager = MockServiceManager()


class EnhancedHTTPXMock:
    """Enhanced HTTPX client mock with realistic response simulation."""
    
    def __init__(self, service_responses: Optional[Dict] = None):
        self.service_responses = service_responses or {}
        self.call_count = 0
        self.last_request = None
    
    async def get(self, url: str, **kwargs) -> MagicMock:
        """Mock GET request."""
        return self._create_response('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> MagicMock:
        """Mock POST request."""
        return self._create_response('POST', url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> MagicMock:
        """Mock PUT request."""
        return self._create_response('PUT', url, **kwargs)
    
    async def patch(self, url: str, **kwargs) -> MagicMock:
        """Mock PATCH request."""
        return self._create_response('PATCH', url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> MagicMock:
        """Mock DELETE request."""
        return self._create_response('DELETE', url, **kwargs)
    
    async def close(self):
        """Mock client close."""
        pass
    
    def _create_response(self, method: str, url: str, **kwargs) -> MagicMock:
        """Create a mock response based on URL and method."""
        self.call_count += 1
        self.last_request = {
            'method': method,
            'url': url,
            'kwargs': kwargs,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Determine service from URL
        service_name = self._extract_service_name(url)
        endpoint = self._extract_endpoint(url)
        
        # Get predefined response or create default
        response_data = self._get_response_data(service_name, endpoint, method)
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = response_data.get('status_code', 200)
        mock_response.json.return_value = response_data.get('json', {})
        mock_response.text = json.dumps(response_data.get('json', {}))
        mock_response.headers = response_data.get('headers', {})
        mock_response.raise_for_status = MagicMock()
        
        return mock_response
    
    def _extract_service_name(self, url: str) -> str:
        """Extract service name from URL."""
        if 'auth' in url or ':8000' in url:
            return 'auth'
        elif 'ac_service' in url or ':8001' in url:
            return 'ac'
        elif 'integrity' in url or ':8002' in url:
            return 'integrity'
        elif 'fv_service' in url or ':8003' in url:
            return 'fv'
        elif 'gs_service' in url or ':8004' in url:
            return 'gs'
        elif 'pgc_service' in url or ':8005' in url:
            return 'pgc'
        else:
            return 'unknown'
    
    def _extract_endpoint(self, url: str) -> str:
        """Extract endpoint from URL."""
        if '/health' in url:
            return 'health'
        elif '/principles' in url:
            return 'principles'
        elif '/bias-detection' in url:
            return 'bias_detection'
        elif '/synthesis' in url:
            return 'synthesis'
        elif '/verify' in url:
            return 'verify'
        elif '/compile' in url:
            return 'compile'
        elif '/login' in url:
            return 'login'
        else:
            return 'default'
    
    def _get_response_data(self, service: str, endpoint: str, method: str) -> Dict:
        """Get response data for service/endpoint combination."""
        service_responses = self.service_responses.get(service, {})
        endpoint_responses = service_responses.get(endpoint, {})
        
        if isinstance(endpoint_responses, dict) and method.lower() in endpoint_responses:
            return endpoint_responses[method.lower()]
        elif isinstance(endpoint_responses, dict) and 'default' in endpoint_responses:
            return endpoint_responses['default']
        elif not isinstance(endpoint_responses, dict):
            return {'json': endpoint_responses, 'status_code': 200}
        else:
            return self._get_default_response(service, endpoint)
    
    def _get_default_response(self, service: str, endpoint: str) -> Dict:
        """Get default response for unknown service/endpoint."""
        default_responses = {
            'health': {'json': {'status': 'ok', 'service': service}, 'status_code': 200},
            'default': {'json': {'message': f'Mock response from {service}'}, 'status_code': 200},
        }
        
        return default_responses.get(endpoint, default_responses['default'])


class MockLLMService:
    """Enhanced mock for LLM service interactions."""
    
    def __init__(self):
        self.generation_count = 0
        self.embedding_count = 0
        self.call_history = []
    
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock text generation."""
        self.generation_count += 1
        
        call_record = {
            'method': 'generate_text',
            'prompt': prompt,
            'kwargs': kwargs,
            'timestamp': datetime.utcnow().isoformat(),
        }
        self.call_history.append(call_record)
        
        # Simulate different responses based on prompt content
        if 'principle' in prompt.lower():
            generated_text = f"Generated principle based on: {prompt[:50]}..."
        elif 'policy' in prompt.lower():
            generated_text = f"Generated policy based on: {prompt[:50]}..."
        elif 'synthesis' in prompt.lower():
            generated_text = f"Synthesized content: {prompt[:50]}..."
        else:
            generated_text = f"Generated response: {prompt[:50]}..."
        
        return {
            'generated_text': generated_text,
            'confidence': 0.85 + (self.generation_count % 10) * 0.01,  # Vary confidence
            'tokens_used': len(prompt.split()) * 2,
            'model': 'mock-llm-v1',
            'generation_id': f'gen_{self.generation_count}',
        }
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Mock embedding generation."""
        self.embedding_count += 1
        
        call_record = {
            'method': 'generate_embedding',
            'text': text,
            'timestamp': datetime.utcnow().isoformat(),
        }
        self.call_history.append(call_record)
        
        # Generate deterministic but varied embeddings
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Create 768-dimensional embedding (common size)
        embedding = []
        for i in range(768):
            value = ((hash_int + i) % 1000) / 1000.0 - 0.5  # Range: -0.5 to 0.5
            embedding.append(value)
        
        return embedding
    
    def get_generation_stats(self) -> Dict[str, int]:
        """Get generation statistics."""
        return {
            'total_generations': self.generation_count,
            'total_embeddings': self.embedding_count,
            'total_calls': len(self.call_history),
        }


class MockZ3Solver:
    """Enhanced mock for Z3 formal verification solver."""
    
    def __init__(self):
        self.constraints = []
        self.check_count = 0
        self.satisfiable_results = ['sat', 'unsat', 'unknown']
        self.current_result_index = 0
    
    def add(self, constraint):
        """Mock adding constraint."""
        self.constraints.append(str(constraint))
    
    def check(self):
        """Mock constraint checking."""
        self.check_count += 1
        
        # Cycle through different results for testing
        result = self.satisfiable_results[self.current_result_index]
        self.current_result_index = (self.current_result_index + 1) % len(self.satisfiable_results)
        
        return result
    
    def model(self):
        """Mock model generation."""
        mock_model = MagicMock()
        mock_model.evaluate = MagicMock(return_value=True)
        return mock_model
    
    def push(self):
        """Mock solver state push."""
        pass
    
    def pop(self):
        """Mock solver state pop."""
        if self.constraints:
            self.constraints.pop()
    
    def reset(self):
        """Reset solver state."""
        self.constraints.clear()
        self.check_count = 0
        self.current_result_index = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get solver statistics."""
        return {
            'constraints_added': len(self.constraints),
            'checks_performed': self.check_count,
            'current_constraints': self.constraints.copy(),
        }


# =============================================================================
# Context Managers for Mock Patching
# =============================================================================

@asynccontextmanager
async def mock_all_services(service_responses: Optional[Dict] = None):
    """Context manager to mock all external services."""

    # Create enhanced mocks
    httpx_mock = EnhancedHTTPXMock(service_responses)
    llm_mock = MockLLMService()
    z3_mock = MockZ3Solver()

    # Register mocks
    mock_manager.register_service_mock('httpx', httpx_mock)
    mock_manager.register_service_mock('llm', llm_mock)
    mock_manager.register_service_mock('z3', z3_mock)

    # Apply patches (only for modules that exist)
    patches = []

    try:
        # Only patch httpx which we know exists
        httpx_patch = patch('httpx.AsyncClient', return_value=httpx_mock)
        patches.append(httpx_patch)
        httpx_patch.__enter__()

        # Try to patch other modules if they exist
        try:
            z3_patch = patch('z3.Solver', return_value=z3_mock)
            patches.append(z3_patch)
            z3_patch.__enter__()
        except ImportError:
            pass  # z3 not available, skip patching

        yield {
            'httpx': httpx_mock,
            'llm': llm_mock,
            'z3': z3_mock,
            'manager': mock_manager,
        }

    finally:
        # Cleanup patches
        for patch_obj in reversed(patches):
            try:
                patch_obj.__exit__(None, None, None)
            except:
                pass

        # Cleanup mocks
        mock_manager.reset_all_mocks()


@asynccontextmanager
async def mock_service_communication():
    """Context manager specifically for cross-service communication mocking."""
    
    service_responses = {
        'auth': {
            'health': {'status': 'ok', 'service': 'auth'},
            'verify': {'valid': True, 'user_id': 'test_user'},
        },
        'ac': {
            'health': {'status': 'ok', 'service': 'ac'},
            'principles': [{'id': 1, 'title': 'Test Principle'}],
        },
        'fv': {
            'health': {'status': 'ok', 'service': 'fv'},
            'bias_detection': {
                'post': {
                    'json': {
                        'overall_bias_score': 0.1,
                        'risk_level': 'low',
                        'summary': 'Mock bias detection analysis completed with low risk level',
                        'policy_rule_ids': [1],
                        'results': [],
                        'recommendations': ['Continue monitoring for bias patterns'],
                        'human_review_required': False
                    },
                    'status_code': 200
                },
                'default': {
                    'json': {
                        'overall_bias_score': 0.1,
                        'risk_level': 'low',
                        'summary': 'Mock bias detection analysis completed with low risk level',
                        'policy_rule_ids': [1],
                        'results': [],
                        'recommendations': ['Continue monitoring for bias patterns'],
                        'human_review_required': False
                    },
                    'status_code': 200
                }
            },
        },
        'gs': {
            'health': {'status': 'ok', 'service': 'gs'},
            'synthesis': {'synthesized_policy': 'Test policy'},
        },
        'integrity': {
            'health': {'status': 'ok', 'service': 'integrity'},
            'verify': {'valid': True},
        },
        'pgc': {
            'health': {'status': 'ok', 'service': 'pgc'},
            'compile': {'compiled_policy': 'package main\nallow = true'},
        },
    }
    
    async with mock_all_services(service_responses) as mocks:
        yield mocks


# =============================================================================
# Utility Functions
# =============================================================================

def create_mock_response(status_code: int = 200, json_data: Optional[Dict] = None, 
                        headers: Optional[Dict] = None) -> MagicMock:
    """Create a mock HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    mock_response.text = json.dumps(json_data or {})
    mock_response.headers = headers or {}
    mock_response.raise_for_status = MagicMock()
    
    return mock_response


def assert_service_called(service_name: str, method: str, min_calls: int = 1) -> bool:
    """Assert that a service was called with specific method."""
    call_history = mock_manager.get_call_history(service_name)
    method_calls = [call for call in call_history if call['method'] == method]
    
    return len(method_calls) >= min_calls


def get_service_call_count(service_name: str, method: Optional[str] = None) -> int:
    """Get the number of calls made to a service/method."""
    call_history = mock_manager.get_call_history(service_name)

    if method:
        return len([call for call in call_history if call['method'] == method])
    else:
        return len(call_history)


# =============================================================================
# Database Mocking Utilities
# =============================================================================

class MockDatabaseSession:
    """Enhanced mock database session with realistic behavior."""

    def __init__(self):
        self.data_store = {}
        self.transaction_active = False
        self.call_history = []
        self.next_id = 1

    async def __aenter__(self):
        """Async context manager entry."""
        self.transaction_active = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        self.transaction_active = False

    def add(self, instance):
        """Mock adding instance to session."""
        self._record_call('add', instance)

        # Simulate ID assignment for new instances
        if not hasattr(instance, 'id') or instance.id is None:
            instance.id = self.next_id
            self.next_id += 1

        # Store in mock data store
        table_name = instance.__class__.__name__.lower()
        if table_name not in self.data_store:
            self.data_store[table_name] = {}

        self.data_store[table_name][instance.id] = instance

    async def commit(self):
        """Mock commit operation."""
        self._record_call('commit')
        # In real implementation, this would persist changes
        pass

    async def rollback(self):
        """Mock rollback operation."""
        self._record_call('rollback')
        # In real implementation, this would revert changes
        pass

    async def close(self):
        """Mock session close."""
        self._record_call('close')
        self.transaction_active = False

    async def execute(self, statement, parameters=None):
        """Mock SQL execution."""
        self._record_call('execute', statement, parameters)

        # Create mock result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_result.fetchone.return_value = None
        mock_result.scalar.return_value = None

        return mock_result

    async def scalar(self, statement, parameters=None):
        """Mock scalar query."""
        self._record_call('scalar', statement, parameters)
        return None

    async def scalars(self, statement, parameters=None):
        """Mock scalars query."""
        self._record_call('scalars', statement, parameters)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.first.return_value = None
        return mock_result

    def get(self, model_class, primary_key):
        """Mock get by primary key."""
        self._record_call('get', model_class, primary_key)

        table_name = model_class.__name__.lower()
        if table_name in self.data_store:
            return self.data_store[table_name].get(primary_key)
        return None

    def query(self, *args):
        """Mock query builder."""
        self._record_call('query', args)
        return MockQuery(self.data_store)

    def _record_call(self, method, *args, **kwargs):
        """Record method call for verification."""
        call_record = {
            'method': method,
            'args': args,
            'kwargs': kwargs,
            'timestamp': datetime.utcnow().isoformat(),
        }
        self.call_history.append(call_record)

    def get_call_history(self):
        """Get all recorded calls."""
        return self.call_history.copy()

    def reset(self):
        """Reset session state."""
        self.data_store.clear()
        self.call_history.clear()
        self.next_id = 1
        self.transaction_active = False


class MockQuery:
    """Mock SQLAlchemy query object."""

    def __init__(self, data_store):
        self.data_store = data_store
        self.filters = []
        self.order_by_clauses = []
        self.limit_value = None
        self.offset_value = None

    def filter(self, *criterion):
        """Mock query filter."""
        self.filters.extend(criterion)
        return self

    def filter_by(self, **kwargs):
        """Mock query filter by keyword arguments."""
        self.filters.append(kwargs)
        return self

    def order_by(self, *criterion):
        """Mock query ordering."""
        self.order_by_clauses.extend(criterion)
        return self

    def limit(self, limit):
        """Mock query limit."""
        self.limit_value = limit
        return self

    def offset(self, offset):
        """Mock query offset."""
        self.offset_value = offset
        return self

    async def all(self):
        """Mock get all results."""
        # Return empty list for simplicity
        return []

    async def first(self):
        """Mock get first result."""
        return None

    async def one(self):
        """Mock get one result."""
        return None

    async def one_or_none(self):
        """Mock get one or none result."""
        return None

    async def count(self):
        """Mock count results."""
        return 0


@asynccontextmanager
async def mock_database_session():
    """Context manager for mocked database session."""
    session = MockDatabaseSession()

    with patch('shared.database.AsyncSessionLocal', return_value=session), \
         patch('shared.database.get_async_db', return_value=session):

        try:
            yield session
        finally:
            session.reset()
