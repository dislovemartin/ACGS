#!/usr/bin/env python3
"""
Test suite for centralized configuration management.
Tests ACGSConfig class and configuration loading functionality.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open
import sys

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/backend/shared'))

from utils import ACGSConfig, get_config, reset_config


class TestACGSConfig:
    """Test cases for ACGSConfig class."""
    
    def setup_method(self):
        """Reset configuration before each test."""
        reset_config()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_config()
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = ACGSConfig()
        
        # Test environment settings
        assert config.get('environment') == 'development'
        assert config.get('debug') is False
        
        # Test service URLs
        assert config.get_service_url('auth') == 'http://localhost:8000'
        assert config.get_service_url('ac') == 'http://localhost:8001'
        assert config.get_service_url('fv') == 'http://localhost:8003'
        
        # Test internal URLs
        assert config.get_service_url('auth', internal=True) == 'http://auth_service:8000'
        assert config.get_service_url('ac', internal=True) == 'http://ac_service:8001'
        
        # Test API configuration
        assert config.get('api_version') == 'v1'
        assert 'http://localhost:3000' in config.get('cors_origins')
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production',
        'DEBUG': 'true',
        'AUTH_SERVICE_URL': 'https://auth.example.com',
        'JWT_SECRET_KEY': 'test-secret-key',
        'TEST_MODE': 'true'
    })
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        config = ACGSConfig()
        
        assert config.get('environment') == 'production'
        assert config.get('debug') is True
        assert config.get_service_url('auth') == 'https://auth.example.com'
        assert config.get('jwt_secret_key') == 'test-secret-key'
        assert config.is_test_mode() is True
        assert config.is_production() is True
    
    def test_service_url_with_api_path(self):
        """Test service URL construction with API paths."""
        config = ACGSConfig()
        
        # Test with API path
        url = config.get_service_url('ac', api_path='/principles')
        assert url == 'http://localhost:8001/api/v1/principles'
        
        # Test with leading slash
        url = config.get_service_url('fv', api_path='bias-detection')
        assert url == 'http://localhost:8003/api/v1/bias-detection'
        
        # Test internal URL with API path
        url = config.get_service_url('gs', internal=True, api_path='/synthesis')
        assert url == 'http://gs_service:8004/api/v1/synthesis'
    
    def test_database_url_selection(self):
        """Test database URL selection based on test mode."""
        config = ACGSConfig()
        
        # Default mode (not test)
        db_url = config.get_database_url()
        assert 'acgs_pgp_db' in db_url
        
        # Test mode
        db_url = config.get_database_url(test_mode=True)
        assert 'test_acgs_db' in db_url
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test missing required configuration
        with patch.dict(os.environ, {'JWT_SECRET_KEY': ''}, clear=True):
            with pytest.raises(ValueError, match="Missing required configuration"):
                ACGSConfig()
    
    def test_invalid_service_name(self):
        """Test error handling for invalid service names."""
        config = ACGSConfig()
        
        with pytest.raises(ValueError, match="Unknown service"):
            config.get_service_url('invalid_service')
    
    def test_config_to_dict(self):
        """Test configuration dictionary export."""
        config = ACGSConfig()
        config_dict = config.to_dict()
        
        # Check that sensitive information is redacted
        assert config_dict['jwt_secret_key'] == '***REDACTED***'
        
        # Check that other values are present
        assert 'environment' in config_dict
        assert 'service_urls' in config_dict
    
    def test_global_config_singleton(self):
        """Test global configuration singleton behavior."""
        # First call creates instance
        config1 = get_config()
        
        # Second call returns same instance
        config2 = get_config()
        
        assert config1 is config2
        
        # Reset and get new instance
        reset_config()
        config3 = get_config()
        
        assert config3 is not config1
    
    def test_env_file_loading(self):
        """Test loading configuration from .env file."""
        env_content = """
ENVIRONMENT=testing
AUTH_SERVICE_URL=http://test.example.com:8000
JWT_SECRET_KEY=test-file-secret
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            f.flush()
            
            try:
                config = ACGSConfig(env_file=f.name)
                
                assert config.get('environment') == 'testing'
                assert config.get_service_url('auth') == 'http://test.example.com:8000'
                assert config.get('jwt_secret_key') == 'test-file-secret'
            finally:
                os.unlink(f.name)
    
    def test_nested_config_access(self):
        """Test nested configuration access using dot notation."""
        config = ACGSConfig()
        
        # Test nested access
        auth_url = config.get('service_urls.auth')
        assert auth_url == 'http://localhost:8000'
        
        # Test with default value
        missing_value = config.get('service_urls.nonexistent', 'default')
        assert missing_value == 'default'
        
        # Test deeply nested access
        cors_origins = config.get('cors_origins')
        assert isinstance(cors_origins, list)


class TestConfigurationIntegration:
    """Integration tests for configuration system."""
    
    def setup_method(self):
        """Reset configuration before each test."""
        reset_config()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_config()
    
    @patch.dict(os.environ, {
        'TEST_MODE': 'true',
        'AUTH_SERVICE_URL': 'http://test-auth:8000',
        'AC_SERVICE_URL': 'http://test-ac:8001'
    })
    def test_cross_service_communication_config(self):
        """Test configuration for cross-service communication."""
        config = get_config()
        
        # Test that test mode is detected
        assert config.is_test_mode()
        
        # Test service URL construction for cross-service calls
        auth_health_url = config.get_service_url('auth', api_path='/health')
        assert auth_health_url == 'http://test-auth:8000/api/v1/health'
        
        ac_principles_url = config.get_service_url('ac', api_path='/principles')
        assert ac_principles_url == 'http://test-ac:8001/api/v1/principles'
    
    def test_configuration_consistency(self):
        """Test that configuration is consistent across multiple accesses."""
        config1 = get_config()
        config2 = get_config()
        
        # Should be the same instance
        assert config1 is config2
        
        # Should have consistent values
        assert config1.get('environment') == config2.get('environment')
        assert config1.get_service_url('auth') == config2.get_service_url('auth')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
