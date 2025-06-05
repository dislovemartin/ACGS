# Tests for Centralized Configuration Management

import pytest
import os
import tempfile
import json
from unittest.mock import patch
from pathlib import Path

from src.backend.shared.utils import (
    ACGSConfig, ACGSConfigModel, Environment,
    DatabaseConfig, ServiceUrlsConfig, SecurityConfig,
    AIModelConfig, MonitoringConfig
)


class TestCentralizedConfiguration:
    """Test suite for Centralized Configuration Management."""

    @pytest.fixture
    def temp_env_file(self):
        """Create temporary environment file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""
ENVIRONMENT=testing
DEBUG=true
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test_db
JWT_SECRET_KEY=test-secret-key-for-testing-purposes-only
AUTH_SERVICE_URL=http://localhost:8000
AC_SERVICE_URL=http://localhost:8001
INTEGRITY_SERVICE_URL=http://localhost:8002
FV_SERVICE_URL=http://localhost:8003
GS_SERVICE_URL=http://localhost:8004
PGC_SERVICE_URL=http://localhost:8005
ANTHROPIC_API_KEY=test-anthropic-key
OPENAI_API_KEY=test-openai-key
""")
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            
            # Create base config
            base_config = {
                "LOG_LEVEL": "DEBUG",
                "METRICS_ENABLED": "true"
            }
            with open(config_dir / "base.json", 'w') as f:
                json.dump(base_config, f)
            
            # Create environment-specific config
            test_config = {
                "DB_ECHO_LOG": "true",
                "TEST_MODE": "true"
            }
            with open(config_dir / "testing.json", 'w') as f:
                json.dump(test_config, f)
            
            yield temp_dir

    def test_pydantic_config_models(self):
        """Test Pydantic configuration models validation."""
        # Test DatabaseConfig
        db_config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost:5432/db",
            echo_log=True,
            pool_size=15,
            max_overflow=25
        )
        assert db_config.url.startswith("postgresql+asyncpg://")
        assert db_config.pool_size == 15

        # Test invalid database URL
        with pytest.raises(ValueError, match="Database URL must use supported scheme"):
            DatabaseConfig(url="invalid://url")

        # Test ServiceUrlsConfig
        service_config = ServiceUrlsConfig(
            auth="http://localhost:8000",
            ac="http://localhost:8001",
            integrity="http://localhost:8002",
            fv="http://localhost:8003",
            gs="http://localhost:8004",
            pgc="http://localhost:8005"
        )
        assert service_config.auth == "http://localhost:8000"

        # Test invalid service URL
        with pytest.raises(ValueError, match="Service URL must start with http"):
            ServiceUrlsConfig(
                auth="invalid-url",
                ac="http://localhost:8001",
                integrity="http://localhost:8002",
                fv="http://localhost:8003",
                gs="http://localhost:8004",
                pgc="http://localhost:8005"
            )

    def test_security_config_validation(self):
        """Test security configuration validation."""
        # Test valid security config
        security_config = SecurityConfig(
            jwt_secret_key="a-very-long-secret-key-for-testing-purposes-only",
            jwt_algorithm="HS256",
            jwt_access_token_expire_minutes=30,
            jwt_refresh_token_expire_days=7,
            cors_origins=["http://localhost:3000"]
        )
        assert len(security_config.jwt_secret_key) >= 32

        # Test invalid JWT secret (too short)
        with pytest.raises(ValueError):
            SecurityConfig(jwt_secret_key="short")

        # Test default JWT secret rejection
        with pytest.raises(ValueError, match="JWT secret key must be changed"):
            SecurityConfig(jwt_secret_key="your-secret-key-change-in-production")

    def test_ai_model_config_validation(self):
        """Test AI model configuration validation."""
        ai_config = AIModelConfig(
            primary="claude-3-7-sonnet-20250219",
            research="sonar-pro",
            fallback="claude-3-5-sonnet",
            max_tokens=32000,
            temperature=0.3,
            research_temperature=0.1
        )
        assert ai_config.max_tokens == 32000
        assert 0.0 <= ai_config.temperature <= 2.0

        # Test invalid temperature
        with pytest.raises(ValueError):
            AIModelConfig(temperature=3.0)  # Too high

    def test_monitoring_config_validation(self):
        """Test monitoring configuration validation."""
        monitoring_config = MonitoringConfig(
            log_level="INFO",
            metrics_enabled=True,
            prometheus_port=9090
        )
        assert monitoring_config.log_level == "INFO"

        # Test invalid log level
        with pytest.raises(ValueError, match="Log level must be one of"):
            MonitoringConfig(log_level="INVALID")

    def test_acgs_config_initialization(self, temp_env_file):
        """Test ACGS configuration initialization."""
        config = ACGSConfig(env_file=temp_env_file)
        
        assert config.environment == Environment.TESTING
        assert config.is_testing()
        assert not config.is_production()
        
        # Test configuration access
        assert config.get_database_url().startswith("postgresql+asyncpg://")
        assert config.get_service_url("auth") == "http://localhost:8000"

    def test_environment_specific_config_loading(self, temp_config_dir):
        """Test environment-specific configuration loading."""
        with patch('os.getcwd', return_value=temp_config_dir):
            config = ACGSConfig(environment="testing")
            
            # Should load both base and testing configs
            assert config.environment == Environment.TESTING

    def test_validated_config_model(self, temp_env_file):
        """Test validated Pydantic configuration model."""
        config = ACGSConfig(env_file=temp_env_file)
        validated_config = config.get_validated_config()
        
        assert isinstance(validated_config, ACGSConfigModel)
        assert validated_config.environment == Environment.TESTING
        assert isinstance(validated_config.database, DatabaseConfig)
        assert isinstance(validated_config.security, SecurityConfig)

    def test_secure_config_summary(self, temp_env_file):
        """Test secure configuration summary (no sensitive data)."""
        config = ACGSConfig(env_file=temp_env_file)
        summary = config.get_secure_config_summary()
        
        assert 'environment' in summary
        assert 'database_configured' in summary
        assert 'ai_providers_configured' in summary
        
        # Should not contain sensitive information
        assert 'jwt_secret_key' not in str(summary)
        assert 'test-secret-key' not in str(summary)

    def test_critical_config_validation(self, temp_env_file):
        """Test critical configuration validation."""
        config = ACGSConfig(env_file=temp_env_file)
        issues = config.validate_critical_config()
        
        # Should be a list (may be empty for valid config)
        assert isinstance(issues, list)

    def test_production_config_validation(self):
        """Test production-specific configuration validation."""
        # Test with production environment and default JWT secret (should fail validation)
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'JWT_SECRET_KEY': 'your-secret-key-change-in-production',  # Default value should fail in production
            'DATABASE_URL': 'postgresql+asyncpg://user:pass@localhost:5432/db',
            'AUTH_SERVICE_URL': 'http://localhost:8000',
            'AC_SERVICE_URL': 'http://localhost:8001',
            'INTEGRITY_SERVICE_URL': 'http://localhost:8002',
            'FV_SERVICE_URL': 'http://localhost:8003',
            'GS_SERVICE_URL': 'http://localhost:8004',
            'PGC_SERVICE_URL': 'http://localhost:8005'
        }):
            # Should fail during construction due to invalid JWT secret in production
            with pytest.raises(ValueError, match="JWT secret key must be changed from default value"):
                config = ACGSConfig()

    def test_config_template_export(self, temp_env_file):
        """Test configuration template export."""
        config = ACGSConfig(env_file=temp_env_file)
        
        # Export without secrets
        template = config.export_config_template(include_secrets=False)
        assert 'environment_variables' in template
        assert 'service_urls' in template
        assert 'ai_configuration' in template
        assert 'ai_api_keys' not in template
        
        # Export with secrets
        template_with_secrets = config.export_config_template(include_secrets=True)
        assert 'ai_api_keys' in template_with_secrets

    def test_config_to_dict_redaction(self, temp_env_file):
        """Test configuration dictionary export with sensitive data redaction."""
        config = ACGSConfig(env_file=temp_env_file)
        config_dict = config.to_dict()
        
        # Should redact sensitive information
        assert config_dict['jwt_secret_key'] == '***REDACTED***'
        
        # Should redact API keys
        if 'ai_api_keys' in config_dict:
            for provider, key in config_dict['ai_api_keys'].items():
                if key is not None:
                    assert key == '***REDACTED***'

    def test_environment_enum(self):
        """Test Environment enum functionality."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"
        assert Environment.TESTING == "testing"

    def test_config_caching_and_reset(self, temp_env_file):
        """Test configuration caching and reset functionality."""
        from src.backend.shared.utils import get_config, reset_config
        
        # Reset any existing config
        reset_config()
        
        # Get config (should create new instance)
        config1 = get_config(temp_env_file)
        config2 = get_config(temp_env_file)
        
        # Should return same instance (cached)
        assert config1 is config2
        
        # Reset and get again
        reset_config()
        config3 = get_config(temp_env_file)
        
        # Should be different instance after reset
        assert config1 is not config3

    def test_config_error_handling(self):
        """Test configuration error handling."""
        # Test with production environment and default JWT secret (should fail)
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'JWT_SECRET_KEY': 'your-secret-key-change-in-production'  # Default value should fail in production
        }, clear=True):
            with pytest.raises(ValueError):
                config = ACGSConfig()
                config.get_validated_config()  # Should fail validation

    def test_config_file_loading_error_handling(self):
        """Test configuration file loading error handling."""
        # Test with a non-existent environment file
        with patch.dict(os.environ, {'ENVIRONMENT': 'testing'}):
            # Should handle missing config files gracefully
            config = ACGSConfig(env_file="/non/existent/file.env")
            assert config is not None
            assert config.environment == Environment.TESTING

    @pytest.mark.parametrize("environment", [
        Environment.DEVELOPMENT,
        Environment.STAGING,
        Environment.PRODUCTION,
        Environment.TESTING
    ])
    def test_environment_specific_behavior(self, environment):
        """Test environment-specific configuration behavior."""
        with patch.dict(os.environ, {'ENVIRONMENT': environment.value}):
            config = ACGSConfig()
            
            assert config.environment == environment
            
            if environment == Environment.PRODUCTION:
                assert config.is_production()
            elif environment == Environment.DEVELOPMENT:
                assert config.is_development()
            elif environment == Environment.TESTING:
                assert config.is_testing()

    def test_config_validation_with_missing_services(self):
        """Test configuration validation with missing service URLs."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DATABASE_URL': 'postgresql+asyncpg://user:pass@localhost:5432/db',
            'JWT_SECRET_KEY': 'test-secret-key-for-testing-purposes-only',
            'AUTH_SERVICE_URL': '',  # Empty service URL should trigger validation error
            'AC_SERVICE_URL': 'invalid-url-without-protocol',  # Invalid URL format
        }, clear=True):
            # Should fail during construction due to invalid service URLs
            with pytest.raises(ValueError, match="Service URL must start with http"):
                config = ACGSConfig()
