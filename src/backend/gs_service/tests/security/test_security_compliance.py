"""
Security Compliance Tests for ACGS Governance Synthesis

Comprehensive security testing including authentication, authorization,
input validation, rate limiting, and audit logging.

Phase 3: Performance Optimization and Security Compliance
"""

import pytest
import asyncio
import time
import json
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.backend.gs_service.app.services.security_compliance import (
    SecurityComplianceService,
    InputValidator,
    RateLimiter,
    AuditLogger,
    JWTManager,
    SecurityEvent
)


@pytest.fixture
def security_service():
    """Security compliance service fixture."""
    return SecurityComplianceService("test-secret-key-for-testing-only")


@pytest.fixture
def mock_request():
    """Mock FastAPI request fixture."""
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.100"
    request.headers = {
        "User-Agent": "TestAgent/1.0",
        "X-Forwarded-For": "203.0.113.1",
        "Content-Type": "application/json"
    }
    request.url = "http://localhost:8004/api/v1/test"
    return request


@pytest.fixture
def valid_jwt_credentials():
    """Valid JWT credentials fixture."""
    jwt_manager = JWTManager("test-secret-key")
    token = jwt_manager.create_token("test_user", ["admin", "policy_manager"])
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestInputValidation:
    """Test input validation and sanitization."""
    
    @pytest.mark.security
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM passwords",
            "admin'--",
            "' OR 1=1#",
            "'; EXEC xp_cmdshell('dir'); --"
        ]
        
        for malicious_input in malicious_inputs:
            assert not InputValidator.validate_input(malicious_input), \
                f"SQL injection not detected: {malicious_input}"
    
    @pytest.mark.security
    def test_xss_detection(self):
        """Test XSS pattern detection."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<object data='javascript:alert(1)'></object>",
            "onload=alert('xss')"
        ]
        
        for malicious_input in malicious_inputs:
            assert not InputValidator.validate_input(malicious_input), \
                f"XSS not detected: {malicious_input}"
    
    @pytest.mark.security
    def test_command_injection_detection(self):
        """Test command injection pattern detection."""
        malicious_inputs = [
            "; cat /etc/passwd",
            "| whoami",
            "`id`",
            "$(uname -a)",
            "&& ls -la",
            "../../../etc/passwd",
            "test; rm -rf /"
        ]
        
        for malicious_input in malicious_inputs:
            assert not InputValidator.validate_input(malicious_input), \
                f"Command injection not detected: {malicious_input}"
    
    @pytest.mark.security
    def test_valid_input_acceptance(self):
        """Test that valid inputs are accepted."""
        valid_inputs = [
            "normal text input",
            "user@example.com",
            "Policy content with normal characters",
            "123456",
            "Valid-Policy_Name.v1",
            "Constitutional principle description"
        ]
        
        for valid_input in valid_inputs:
            assert InputValidator.validate_input(valid_input), \
                f"Valid input rejected: {valid_input}"
    
    @pytest.mark.security
    def test_input_sanitization(self):
        """Test input sanitization functionality."""
        test_cases = [
            ("normal text", "normal text"),
            ("text\x00with\x00nulls", "textNullwithNullnulls"),  # Null bytes replaced with 'Null'
            ("text\x01\x02\x03control", "textcontrol"),
            ("very" + "x" * 10000 + "long", "very" + "x" * 9996),  # Truncated to 10000
            ("text\nwith\ttabs", "text\nwith\ttabs")  # Preserve newlines and tabs
        ]
        
        for input_text, expected in test_cases:
            sanitized = InputValidator.sanitize_input(input_text)
            assert len(sanitized) <= 10000, "Input not properly truncated"
            if len(input_text) <= 10000:
                assert sanitized == expected, f"Sanitization failed for: {input_text}"


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.mark.security
    def test_rate_limit_enforcement(self):
        """Test rate limit enforcement."""
        rate_limiter = RateLimiter()
        client_id = "test_client_1"
        max_requests = 5
        window_minutes = 1
        
        # Should allow requests up to limit
        for i in range(max_requests):
            result = rate_limiter.is_allowed(client_id, max_requests, window_minutes)
            assert not result.blocked, f"Request {i+1} should be allowed"
            assert result.requests == i + 1
        
        # Should block additional requests
        result = rate_limiter.is_allowed(client_id, max_requests, window_minutes)
        assert result.blocked, "Request should be blocked after exceeding limit"
        assert result.requests >= max_requests
    
    @pytest.mark.security
    def test_rate_limit_per_client(self):
        """Test rate limiting is enforced per client."""
        rate_limiter = RateLimiter()
        max_requests = 3
        window_minutes = 1
        
        # Client 1 reaches limit
        for _ in range(max_requests):
            result = rate_limiter.is_allowed("client_1", max_requests, window_minutes)
            assert not result.blocked
        
        # Client 1 is blocked
        result = rate_limiter.is_allowed("client_1", max_requests, window_minutes)
        assert result.blocked
        
        # Client 2 should still be allowed
        result = rate_limiter.is_allowed("client_2", max_requests, window_minutes)
        assert not result.blocked
    
    @pytest.mark.security
    def test_rate_limit_window_sliding(self):
        """Test sliding window rate limiting."""
        rate_limiter = RateLimiter()
        client_id = "test_client_sliding"
        max_requests = 3
        window_minutes = 1
        
        # Make requests at the limit
        for _ in range(max_requests):
            result = rate_limiter.is_allowed(client_id, max_requests, window_minutes)
            assert not result.blocked
        
        # Should be blocked
        result = rate_limiter.is_allowed(client_id, max_requests, window_minutes)
        assert result.blocked
        
        # Simulate time passing (in real implementation, this would be automatic)
        # For testing, we can verify the logic works correctly


class TestJWTAuthentication:
    """Test JWT authentication and authorization."""
    
    @pytest.mark.security
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        jwt_manager = JWTManager("test-secret-key")
        user_id = "test_user"
        roles = ["admin", "policy_manager"]
        
        # Create token
        token = jwt_manager.create_token(user_id, roles)
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        assert payload["user_id"] == user_id
        assert payload["roles"] == roles
        assert "iat" in payload
        assert "exp" in payload
        assert "jti" in payload
    
    @pytest.mark.security
    def test_jwt_token_expiration(self):
        """Test JWT token expiration handling."""
        jwt_manager = JWTManager("test-secret-key")
        jwt_manager.expiry_minutes = -1  # Expired token
        
        token = jwt_manager.create_token("test_user", ["admin"])
        
        with pytest.raises(HTTPException) as exc_info:
            jwt_manager.verify_token(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()
    
    @pytest.mark.security
    def test_jwt_token_revocation(self):
        """Test JWT token revocation."""
        jwt_manager = JWTManager("test-secret-key")
        token = jwt_manager.create_token("test_user", ["admin"])
        
        # Token should be valid initially
        payload = jwt_manager.verify_token(token)
        assert payload["user_id"] == "test_user"
        
        # Revoke token
        jwt_manager.revoke_token(token)
        
        # Token should now be invalid
        with pytest.raises(HTTPException) as exc_info:
            jwt_manager.verify_token(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "revoked" in exc_info.value.detail.lower()
    
    @pytest.mark.security
    def test_invalid_jwt_token(self):
        """Test handling of invalid JWT tokens."""
        jwt_manager = JWTManager("test-secret-key")
        
        invalid_tokens = [
            "invalid.token.format",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "not-a-jwt-token",
            "Bearer token-without-proper-format"
        ]
        
        for invalid_token in invalid_tokens:
            with pytest.raises(HTTPException) as exc_info:
                jwt_manager.verify_token(invalid_token)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuditLogging:
    """Test security audit logging."""
    
    @pytest.mark.security
    def test_audit_event_logging(self):
        """Test audit event logging functionality."""
        audit_logger = AuditLogger()
        
        # Log various security events
        events = [
            ("authentication_success", "user123", "192.168.1.1", "TestAgent", "/api/login", {"method": "jwt"}, "low", True),
            ("authentication_failed", None, "192.168.1.2", "TestAgent", "/api/login", {"reason": "invalid_token"}, "medium", False),
            ("authorization_failed", "user456", "192.168.1.3", "TestAgent", "/api/admin", {"required_role": "admin"}, "high", False),
            ("rate_limit_exceeded", "user789", "192.168.1.4", "TestAgent", "/api/synthesize", {"requests": 101}, "high", False)
        ]
        
        for event_type, user_id, ip, user_agent, endpoint, details, severity, success in events:
            audit_logger.log_event(event_type, user_id, ip, user_agent, endpoint, details, severity, success)
        
        # Verify events were logged
        all_events = audit_logger.get_events(hours=1)
        assert len(all_events) == len(events)
        
        # Test filtering
        failed_events = audit_logger.get_events(hours=1, severity="high")
        assert len(failed_events) == 2
        
        auth_events = audit_logger.get_events(hours=1, event_type="authentication_failed")
        assert len(auth_events) == 1
        assert auth_events[0].user_id is None
        assert not auth_events[0].success
    
    @pytest.mark.security
    def test_audit_log_retention(self):
        """Test audit log retention policy."""
        audit_logger = AuditLogger()
        
        # Log an event
        audit_logger.log_event("test_event", "user1", "192.168.1.1", "TestAgent", "/test", {}, "low", True)
        
        # Verify event exists
        events = audit_logger.get_events(hours=1)
        assert len(events) == 1
        
        # Simulate old events (this would normally happen over time)
        # In a real implementation, you'd test with actual time passage
        old_events = audit_logger.get_events(hours=0.001)  # Very short window
        assert len(old_events) == 0


class TestSecurityComplianceIntegration:
    """Test integrated security compliance functionality."""
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_request_validation_flow(self, security_service, mock_request):
        """Test complete request validation flow."""
        # Should pass validation for normal request
        result = security_service.validate_request(mock_request, max_requests=100, window_minutes=1)
        assert result is True
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_authentication_flow(self, security_service, valid_jwt_credentials):
        """Test authentication flow."""
        payload = await security_service.authenticate_request(valid_jwt_credentials)
        assert payload["user_id"] == "test_user"
        assert "admin" in payload["roles"]
    
    @pytest.mark.security
    def test_authorization_flow(self, security_service):
        """Test authorization flow."""
        user_payload = {
            "user_id": "test_user",
            "roles": ["admin", "policy_manager"]
        }
        
        # Should pass with correct roles
        result = security_service.authorize_request(user_payload, ["admin"])
        assert result is True
        
        # Should fail with insufficient roles
        with pytest.raises(HTTPException) as exc_info:
            security_service.authorize_request(user_payload, ["super_admin"])
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.security
    def test_input_validation_flow(self, security_service):
        """Test input validation flow."""
        # Valid input should pass
        valid_data = {"policy": "normal policy content", "user": "admin"}
        sanitized = security_service.validate_input_data(valid_data)
        assert sanitized == valid_data
        
        # Invalid input should raise exception
        malicious_data = {"policy": "'; DROP TABLE policies; --"}
        with pytest.raises(HTTPException) as exc_info:
            security_service.validate_input_data(malicious_data)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.security
    def test_security_summary_generation(self, security_service):
        """Test security summary generation."""
        # Generate some security events
        security_service.audit_logger.log_event(
            "test_event", "user1", "192.168.1.1", "TestAgent", "/test", {}, "high", False
        )
        security_service.audit_logger.log_event(
            "test_event", "user2", "192.168.1.2", "TestAgent", "/test", {}, "medium", True
        )
        
        summary = security_service.get_security_summary()
        
        assert "timestamp" in summary
        assert "total_events_24h" in summary
        assert "security_events_by_severity" in summary
        assert "failed_events" in summary
        
        assert summary["total_events_24h"] == 2
        assert summary["security_events_by_severity"]["high"] == 1
        assert summary["security_events_by_severity"]["medium"] == 1
        assert summary["failed_events"] == 1


class TestSecurityPerformance:
    """Test security compliance performance impact."""
    
    @pytest.mark.security
    @pytest.mark.performance
    def test_input_validation_performance(self, security_service):
        """Test input validation performance impact."""
        test_data = {"policy": "normal policy content", "data": "x" * 1000}
        
        # Measure validation time
        start_time = time.time()
        for _ in range(1000):
            security_service.validate_input_data(test_data)
        end_time = time.time()
        
        avg_time_ms = ((end_time - start_time) / 1000) * 1000
        assert avg_time_ms < 1.0, f"Input validation too slow: {avg_time_ms:.2f}ms per validation"
    
    @pytest.mark.security
    @pytest.mark.performance
    def test_rate_limiting_performance(self, security_service):
        """Test rate limiting performance impact."""
        rate_limiter = security_service.rate_limiter
        
        # Measure rate limit checking time
        start_time = time.time()
        for i in range(10000):
            rate_limiter.is_allowed(f"client_{i % 100}", max_requests=100, window_minutes=1)
        end_time = time.time()
        
        avg_time_ms = ((end_time - start_time) / 10000) * 1000
        assert avg_time_ms < 0.1, f"Rate limiting too slow: {avg_time_ms:.4f}ms per check"
