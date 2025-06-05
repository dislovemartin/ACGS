#!/usr/bin/env python3
"""
ACGS-PGP Test Generators

Provides utilities for generating parameterized tests to improve coverage
and test edge cases across all ACGS-PGP components.
"""

import pytest
import itertools
from typing import List, Dict, Any, Tuple, Union
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

# =============================================================================
# Test Data Generators
# =============================================================================

class TestDataGenerator:
    """Generate test data for comprehensive coverage."""
    
    @staticmethod
    def generate_principle_test_data() -> List[Dict[str, Any]]:
        """Generate test data for AC principles."""
        return [
            # Valid principles
            {
                'id': 1,
                'title': 'Fairness Principle',
                'content': 'All users should be treated fairly and without discrimination',
                'priority_weight': 0.9,
                'scope': 'global',
                'normative_statement': 'Users must be treated equally',
                'constraints': ['no_discrimination', 'equal_access'],
                'rationale': 'Ensures fair treatment for all users'
            },
            {
                'id': 2,
                'title': 'Privacy Principle',
                'content': 'User privacy must be protected at all times',
                'priority_weight': 0.8,
                'scope': 'data_processing',
                'normative_statement': 'Privacy is a fundamental right',
                'constraints': ['data_minimization', 'consent_required'],
                'rationale': 'Protects user privacy and builds trust'
            },
            # Edge cases
            {
                'id': 3,
                'title': '',  # Empty title
                'content': 'Test principle with empty title',
                'priority_weight': 0.5,
                'scope': 'test',
                'normative_statement': 'Test statement',
                'constraints': [],
                'rationale': 'Test edge case'
            },
            {
                'id': 4,
                'title': 'A' * 1000,  # Very long title
                'content': 'Test principle with very long title',
                'priority_weight': 1.0,
                'scope': 'test',
                'normative_statement': 'Test statement',
                'constraints': ['test'],
                'rationale': 'Test edge case'
            },
            # Invalid data
            {
                'id': 5,
                'title': 'Invalid Priority',
                'content': 'Test principle with invalid priority',
                'priority_weight': 1.5,  # Invalid priority > 1.0
                'scope': 'test',
                'normative_statement': 'Test statement',
                'constraints': ['test'],
                'rationale': 'Test edge case'
            }
        ]
    
    @staticmethod
    def generate_policy_test_data() -> List[Dict[str, Any]]:
        """Generate test data for policies."""
        return [
            # Valid Rego policies
            {
                'id': 1,
                'title': 'Access Control Policy',
                'content': '''
                    package acgs.access_control
                    default allow = false
                    allow {
                        input.user.role == "admin"
                    }
                ''',
                'format': 'rego',
                'version': '1.0.0',
                'status': 'active'
            },
            # JSON policy
            {
                'id': 2,
                'title': 'Data Processing Policy',
                'content': '{"rules": [{"effect": "allow", "action": "read", "resource": "data"}]}',
                'format': 'json',
                'version': '1.0.0',
                'status': 'active'
            },
            # YAML policy
            {
                'id': 3,
                'title': 'Security Policy',
                'content': '''
                    apiVersion: v1
                    kind: SecurityPolicy
                    metadata:
                      name: test-security
                    spec:
                      rules:
                        - effect: allow
                          action: access
                ''',
                'format': 'yaml',
                'version': '1.0.0',
                'status': 'active'
            },
            # Invalid policies
            {
                'id': 4,
                'title': 'Invalid Rego',
                'content': 'package invalid syntax error',
                'format': 'rego',
                'version': '1.0.0',
                'status': 'draft'
            }
        ]
    
    @staticmethod
    def generate_bias_detection_test_data() -> List[Dict[str, Any]]:
        """Generate test data for bias detection."""
        return [
            # Balanced dataset
            {
                'dataset': [
                    {'age': 25, 'income': 50000, 'gender': 'female', 'ethnicity': 'group_a', 'outcome': 1},
                    {'age': 30, 'income': 60000, 'gender': 'male', 'ethnicity': 'group_a', 'outcome': 1},
                    {'age': 35, 'income': 55000, 'gender': 'female', 'ethnicity': 'group_b', 'outcome': 1},
                    {'age': 40, 'income': 65000, 'gender': 'male', 'ethnicity': 'group_b', 'outcome': 1},
                ],
                'protected_attributes': ['gender', 'ethnicity'],
                'expected_bias': False
            },
            # Biased dataset
            {
                'dataset': [
                    {'age': 25, 'income': 50000, 'gender': 'female', 'ethnicity': 'group_a', 'outcome': 0},
                    {'age': 30, 'income': 60000, 'gender': 'male', 'ethnicity': 'group_a', 'outcome': 1},
                    {'age': 35, 'income': 55000, 'gender': 'female', 'ethnicity': 'group_b', 'outcome': 0},
                    {'age': 40, 'income': 65000, 'gender': 'male', 'ethnicity': 'group_b', 'outcome': 1},
                ],
                'protected_attributes': ['gender'],
                'expected_bias': True
            },
            # Empty dataset
            {
                'dataset': [],
                'protected_attributes': ['gender'],
                'expected_bias': None  # Should handle gracefully
            }
        ]
    
    @staticmethod
    def generate_auth_test_data() -> List[Dict[str, Any]]:
        """Generate test data for authentication."""
        return [
            # Valid credentials
            {
                'username': 'test_user',
                'password': 'SecurePassword123!',
                'email': 'test@example.com',
                'role': 'user',
                'expected_success': True
            },
            {
                'username': 'admin_user',
                'password': 'AdminPassword456!',
                'email': 'admin@example.com',
                'role': 'admin',
                'expected_success': True
            },
            # Invalid credentials
            {
                'username': 'test_user',
                'password': 'wrong_password',
                'email': 'test@example.com',
                'role': 'user',
                'expected_success': False
            },
            # Edge cases
            {
                'username': '',  # Empty username
                'password': 'password',
                'email': 'test@example.com',
                'role': 'user',
                'expected_success': False
            },
            {
                'username': 'a' * 1000,  # Very long username
                'password': 'password',
                'email': 'test@example.com',
                'role': 'user',
                'expected_success': False
            }
        ]


# =============================================================================
# Parameterized Test Decorators
# =============================================================================

def parametrize_principles():
    """Decorator for parameterizing principle tests."""
    test_data = TestDataGenerator.generate_principle_test_data()
    return pytest.mark.parametrize("principle_data", test_data)


def parametrize_policies():
    """Decorator for parameterizing policy tests."""
    test_data = TestDataGenerator.generate_policy_test_data()
    return pytest.mark.parametrize("policy_data", test_data)


def parametrize_bias_detection():
    """Decorator for parameterizing bias detection tests."""
    test_data = TestDataGenerator.generate_bias_detection_test_data()
    return pytest.mark.parametrize("bias_data", test_data)


def parametrize_auth():
    """Decorator for parameterizing authentication tests."""
    test_data = TestDataGenerator.generate_auth_test_data()
    return pytest.mark.parametrize("auth_data", test_data)


def parametrize_http_methods():
    """Decorator for parameterizing HTTP method tests."""
    methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    return pytest.mark.parametrize("http_method", methods)


def parametrize_status_codes():
    """Decorator for parameterizing HTTP status code tests."""
    status_codes = [200, 201, 400, 401, 403, 404, 422, 500]
    return pytest.mark.parametrize("status_code", status_codes)


def parametrize_database_operations():
    """Decorator for parameterizing database operation tests."""
    operations = ['create', 'read', 'update', 'delete', 'list']
    return pytest.mark.parametrize("operation", operations)


# =============================================================================
# Edge Case Generators
# =============================================================================

class EdgeCaseGenerator:
    """Generate edge cases for comprehensive testing."""
    
    @staticmethod
    def generate_string_edge_cases() -> List[str]:
        """Generate string edge cases."""
        return [
            '',  # Empty string
            ' ',  # Single space
            '\n',  # Newline
            '\t',  # Tab
            'a' * 1000,  # Very long string
            '🚀🎉💥',  # Unicode emojis
            'SELECT * FROM users;',  # SQL injection attempt
            '<script>alert("xss")</script>',  # XSS attempt
            '../../etc/passwd',  # Path traversal attempt
            'null',  # String "null"
            'undefined',  # String "undefined"
            '0',  # String zero
            'true',  # String boolean
            'false',  # String boolean
        ]
    
    @staticmethod
    def generate_numeric_edge_cases() -> List[Union[int, float]]:
        """Generate numeric edge cases."""
        return [
            0,  # Zero
            -1,  # Negative
            1,  # Positive
            float('inf'),  # Infinity
            float('-inf'),  # Negative infinity
            float('nan'),  # NaN
            2**31 - 1,  # Max 32-bit int
            -2**31,  # Min 32-bit int
            2**63 - 1,  # Max 64-bit int
            -2**63,  # Min 64-bit int
            0.1 + 0.2,  # Floating point precision issue
            1e-10,  # Very small number
            1e10,  # Very large number
        ]
    
    @staticmethod
    def generate_datetime_edge_cases() -> List[datetime]:
        """Generate datetime edge cases."""
        now = datetime.now()
        return [
            datetime.min,  # Minimum datetime
            datetime.max,  # Maximum datetime
            now,  # Current time
            now - timedelta(days=365),  # One year ago
            now + timedelta(days=365),  # One year from now
            datetime(2000, 1, 1),  # Y2K
            datetime(2038, 1, 19),  # Unix timestamp limit
            datetime(1970, 1, 1),  # Unix epoch
        ]


# =============================================================================
# Mock Generators
# =============================================================================

class MockGenerator:
    """Generate mocks for testing."""
    
    @staticmethod
    def create_mock_database_session():
        """Create a mock database session."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.scalar = AsyncMock()
        mock_session.scalars = AsyncMock()
        return mock_session
    
    @staticmethod
    def create_mock_http_client():
        """Create a mock HTTP client."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.text = '{"status": "ok"}'
        
        mock_client.get.return_value = mock_response
        mock_client.post.return_value = mock_response
        mock_client.put.return_value = mock_response
        mock_client.patch.return_value = mock_response
        mock_client.delete.return_value = mock_response
        mock_client.aclose = AsyncMock()
        
        return mock_client
    
    @staticmethod
    def create_mock_llm_service():
        """Create a mock LLM service."""
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = {
            'generated_text': 'Mock LLM response',
            'confidence': 0.95,
            'tokens_used': 150,
        }
        mock_llm.embed.return_value = [0.1] * 768  # Mock embedding
        return mock_llm


# =============================================================================
# Test Utilities
# =============================================================================

def assert_coverage_improved(before_coverage: float, after_coverage: float, 
                           min_improvement: float = 1.0):
    """Assert that coverage has improved by at least the minimum amount."""
    improvement = after_coverage - before_coverage
    assert improvement >= min_improvement, (
        f"Coverage improvement {improvement:.2f}% is less than "
        f"minimum required {min_improvement:.2f}%"
    )


def skip_if_no_coverage_data():
    """Skip test if coverage data is not available."""
    import os
    if not os.path.exists('coverage.json'):
        pytest.skip("Coverage data not available")


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Generate test data examples
    generator = TestDataGenerator()
    
    print("Principle test data:")
    for principle in generator.generate_principle_test_data()[:2]:
        print(f"  - {principle['title']}: {principle['content'][:50]}...")
    
    print("\nEdge case examples:")
    edge_gen = EdgeCaseGenerator()
    print(f"  String edge cases: {len(edge_gen.generate_string_edge_cases())} cases")
    print(f"  Numeric edge cases: {len(edge_gen.generate_numeric_edge_cases())} cases")
    print(f"  Datetime edge cases: {len(edge_gen.generate_datetime_edge_cases())} cases")
    
    print("\nMock examples:")
    mock_gen = MockGenerator()
    db_mock = mock_gen.create_mock_database_session()
    http_mock = mock_gen.create_mock_http_client()
    llm_mock = mock_gen.create_mock_llm_service()
    print(f"  Created mocks: database, HTTP client, LLM service")
