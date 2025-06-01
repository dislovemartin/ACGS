# ACGS/shared/utils.py

import logging
import os
from datetime import datetime, timezone, timedelta
import re
from typing import Optional, Dict, Any, Union
from dotenv import load_dotenv

# Setup basic logger
# In a real application, you'd likely use a more sophisticated logging setup,
# possibly configured in each service's main.py or from a central config.
logging.basicConfig(level=logging.INFO) # Consider making level configurable
logger = logging.getLogger("acgs_shared_utils")

def get_utc_now() -> datetime:
    """Returns the current datetime in UTC."""
    return datetime.now(timezone.utc)

def create_timestamp_str(dt_object: Optional[datetime] = None) -> str:
    """Creates a standardized ISO 8601 timestamp string from a datetime object."""
    if dt_object is None:
        dt_object = get_utc_now()
    return dt_object.isoformat()

def parse_timestamp_str(timestamp_str: str) -> Optional[datetime]:
    """Parses an ISO 8601 timestamp string into a datetime object."""
    if not timestamp_str: # Handle empty string case
        return None
    try:
        # More robust parsing for various ISO 8601 formats
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid timestamp format: {timestamp_str}. Error: {e}")
        return None

def calculate_expiration_time(minutes: int) -> datetime:
    """Calculates an expiration datetime from now + minutes in UTC."""
    return get_utc_now() + timedelta(minutes=minutes)

def sanitize_input(text: Optional[str]) -> str: # text can be Optional[str]
    """
    Basic input sanitization.
    Removes potentially harmful characters or sequences.
    This is a very basic example and should be expanded based on specific needs
    and supplemented by context-aware escaping (e.g., HTML escaping, SQL parameterization).
    """
    if not isinstance(text, str): # If text is None or not a string, return empty string
        return ""
    # Remove control characters except for common whitespace like newline, tab, carriage return
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    # Add other sanitization rules as needed, e.g., for SQL injection, XSS.
    # However, for SQL, always prefer parameterized queries. For XSS, use templating engines' auto-escaping.
    return text.strip()

def generate_short_id(length: int = 8) -> str:
    """Generates a short, somewhat unique ID. Not cryptographically secure."""
    import random
    import string
    if length <= 0:
        raise ValueError("Length must be a positive integer.")
    characters = string.ascii_lowercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))

class CommonHTTPErrorMessages:
    """Common error messages for HTTP exceptions."""
    NOT_FOUND = "Resource not found."
    UNAUTHORIZED = "Not authorized to access this resource."
    FORBIDDEN = "Access forbidden."
    BAD_REQUEST = "Bad request."
    INTERNAL_SERVER_ERROR = "Internal server error."
    INVALID_CREDENTIALS = "Invalid credentials."
    VALIDATION_ERROR = "Validation error."

# Example utility for pagination (can be expanded)
class Paginator:
    def __init__(self, items: list, page: int = 1, per_page: int = 10):
        if not isinstance(page, int) or page < 1:
            page = 1
        if not isinstance(per_page, int) or per_page < 1:
            per_page = 10
            
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total_items = len(items)
        # Ensure total_pages is at least 1 if there are items, 0 otherwise
        if self.total_items == 0:
            self.total_pages = 0
        else:
            self.total_pages = (self.total_items + self.per_page - 1) // self.per_page
        
        # Adjust page if it's out of bounds after total_pages calculation
        if self.total_items > 0 and self.page > self.total_pages :
            self.page = self.total_pages
        elif self.total_items == 0: # if no items, page should be 1 or 0 depending on convention
            self.page = 1


    def get_page_items(self) -> list:
        if self.total_items == 0:
            return []
        start_index = (self.page - 1) * self.per_page
        end_index = start_index + self.per_page
        return self.items[start_index:end_index]

    def has_next(self) -> bool:
        return self.page < self.total_pages

    def has_prev(self) -> bool:
        return self.page > 1 and self.total_pages > 0 # No prev if on page 1 or no pages

    def get_pagination_details(self) -> dict:
        return {
            "page": self.page,
            "per_page": self.per_page,
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "has_next": self.has_next(),
            "has_prev": self.has_prev(),
            "items_on_page": len(self.get_page_items())
        }

# Centralized Configuration Management
class ACGSConfig:
    """
    Centralized configuration management for ACGS-PGP services.
    Handles environment variables, service URLs, and cross-service communication settings.
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration with optional environment file.

        Args:
            env_file: Path to .env file. If None, uses default discovery.
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from common locations
            for env_path in ['.env', '../.env', '../../.env', '../../../.env']:
                if os.path.exists(env_path):
                    load_dotenv(env_path)
                    break

        self._config = self._load_configuration()
        self._validate_configuration()

    def _load_configuration(self) -> Dict[str, Any]:
        """Load all configuration from environment variables."""
        return {
            # Environment settings
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',

            # Database configuration
            'database_url': os.getenv(
                'DATABASE_URL',
                'postgresql+asyncpg://acgs_user:acgs_password@postgres_db:5432/acgs_pgp_db'
            ),
            'db_echo_log': os.getenv('DB_ECHO_LOG', 'false').lower() == 'true',

            # Service URLs (with fallbacks for different environments)
            'service_urls': {
                'auth': os.getenv('AUTH_SERVICE_URL', 'http://localhost:8000'),
                'ac': os.getenv('AC_SERVICE_URL', 'http://localhost:8001'),
                'integrity': os.getenv('INTEGRITY_SERVICE_URL', 'http://localhost:8002'),
                'fv': os.getenv('FV_SERVICE_URL', 'http://localhost:8003'),
                'gs': os.getenv('GS_SERVICE_URL', 'http://localhost:8004'),
                'pgc': os.getenv('PGC_SERVICE_URL', 'http://localhost:8005'),
            },

            # Docker internal service URLs (for container-to-container communication)
            'internal_service_urls': {
                'auth': os.getenv('AUTH_SERVICE_INTERNAL_URL', 'http://auth_service:8000'),
                'ac': os.getenv('AC_SERVICE_INTERNAL_URL', 'http://ac_service:8001'),
                'integrity': os.getenv('INTEGRITY_SERVICE_INTERNAL_URL', 'http://integrity_service:8002'),
                'fv': os.getenv('FV_SERVICE_INTERNAL_URL', 'http://fv_service:8003'),
                'gs': os.getenv('GS_SERVICE_INTERNAL_URL', 'http://gs_service:8004'),
                'pgc': os.getenv('PGC_SERVICE_INTERNAL_URL', 'http://pgc_service:8005'),
            },

            # API configuration
            'api_version': os.getenv('API_VERSION', 'v1'),
            'cors_origins': os.getenv(
                'BACKEND_CORS_ORIGINS',
                'http://localhost:3000,http://localhost:3001'
            ).split(','),

            # Security settings
            'jwt_secret_key': os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production'),
            'jwt_algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
            'jwt_access_token_expire_minutes': int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
            'jwt_refresh_token_expire_days': int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7')),

            # External service configuration
            'llm_api_endpoint': os.getenv('LLM_API_ENDPOINT', 'http://mock_llm_service/generate'),

            # AI Model Configuration for ACGS-PGP
            'ai_models': {
                'primary': os.getenv('ACGS_PRIMARY_LLM_MODEL', 'claude-3-7-sonnet-20250219'),
                'research': os.getenv('ACGS_RESEARCH_LLM_MODEL', 'sonar-pro'),
                'fallback': os.getenv('ACGS_FALLBACK_LLM_MODEL', 'claude-3-5-sonnet'),
                'gemini_2_5_flash': 'gemini-2.5-flash-preview-04-17',
                'deepseek_r1': 'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B',
                'deepseek_r1_openrouter': 'deepseek/deepseek-chat-v3-0324',
            },

            # Model settings
            'llm_settings': {
                'max_tokens': int(os.getenv('ACGS_LLM_MAX_TOKENS', '64000')),
                'temperature': float(os.getenv('ACGS_LLM_TEMPERATURE', '0.2')),
                'research_temperature': float(os.getenv('ACGS_RESEARCH_TEMPERATURE', '0.1')),
            },

            # Model enablement flags
            'model_features': {
                'enable_gemini_2_5_flash': os.getenv('ENABLE_GEMINI_2_5_FLASH', 'true').lower() == 'true',
                'enable_deepseek_r1': os.getenv('ENABLE_DEEPSEEK_R1', 'true').lower() == 'true',
                'enable_bias_detection_llm': os.getenv('ENABLE_BIAS_DETECTION_LLM', 'true').lower() == 'true',
            },

            # API Keys for AI services
            'ai_api_keys': {
                'anthropic': os.getenv('ANTHROPIC_API_KEY'),
                'openai': os.getenv('OPENAI_API_KEY'),
                'google': os.getenv('GOOGLE_API_KEY'),
                'perplexity': os.getenv('PERPLEXITY_API_KEY'),
                'huggingface': os.getenv('HUGGINGFACE_API_KEY'),
                'openrouter': os.getenv('OPENROUTER_API_KEY'),
                'mistral': os.getenv('MISTRAL_API_KEY'),
                'xai': os.getenv('XAI_API_KEY'),
            },

            # External AI service endpoints
            'ai_endpoints': {
                'huggingface': os.getenv('HUGGINGFACE_API_ENDPOINT', 'https://api-inference.huggingface.co/models'),
                'openrouter': 'https://openrouter.ai/api/v1',
            },

            # Monitoring and logging
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'metrics_enabled': os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
            'prometheus_port': int(os.getenv('PROMETHEUS_PORT', '9090')),

            # Testing configuration
            'test_mode': os.getenv('TEST_MODE', 'false').lower() == 'true',
            'test_database_url': os.getenv(
                'TEST_DATABASE_URL',
                'postgresql+asyncpg://test_user:test_password@localhost:5433/test_acgs_db'
            ),
        }

    def _validate_configuration(self) -> None:
        """Validate critical configuration values."""
        required_configs = [
            'database_url',
            'jwt_secret_key',
        ]

        missing_configs = []
        for config_key in required_configs:
            if not self._config.get(config_key):
                missing_configs.append(config_key)

        if missing_configs:
            raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")

        # Validate service URLs format
        for service_name, url in self._config['service_urls'].items():
            if not url.startswith(('http://', 'https://')):
                logger.warning(f"Service URL for {service_name} may be invalid: {url}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key with optional default."""
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_service_url(self, service_name: str, internal: bool = False, api_path: str = '') -> str:
        """
        Get service URL for cross-service communication.

        Args:
            service_name: Name of the service (auth, ac, integrity, fv, gs, pgc)
            internal: Whether to use internal Docker URLs
            api_path: Additional API path to append

        Returns:
            Complete service URL
        """
        url_key = 'internal_service_urls' if internal else 'service_urls'
        base_url = self._config[url_key].get(service_name)

        if not base_url:
            raise ValueError(f"Unknown service: {service_name}")

        # Construct full URL
        if api_path:
            if not api_path.startswith('/'):
                api_path = '/' + api_path
            return f"{base_url}/api/{self._config['api_version']}{api_path}"
        else:
            return base_url

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self._config['environment'] == 'development'

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self._config['environment'] == 'production'

    def is_test_mode(self) -> bool:
        """Check if running in test mode."""
        return self._config['test_mode']

    def get_database_url(self, test_mode: Optional[bool] = None) -> str:
        """Get appropriate database URL based on environment."""
        if test_mode is None:
            test_mode = self.is_test_mode()

        return self._config['test_database_url'] if test_mode else self._config['database_url']

    def get_ai_model(self, model_type: str = 'primary') -> str:
        """
        Get AI model identifier for specified type.

        Args:
            model_type: Type of model ('primary', 'research', 'fallback', 'gemini_2_5_flash', 'deepseek_r1')

        Returns:
            Model identifier string
        """
        return self._config['ai_models'].get(model_type, self._config['ai_models']['primary'])

    def get_ai_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for specified AI provider.

        Args:
            provider: AI provider name ('anthropic', 'openai', 'google', 'huggingface', etc.)

        Returns:
            API key string or None if not configured
        """
        return self._config['ai_api_keys'].get(provider)

    def is_model_enabled(self, model_feature: str) -> bool:
        """
        Check if specific AI model feature is enabled.

        Args:
            model_feature: Feature name ('enable_gemini_2_5_flash', 'enable_deepseek_r1', etc.)

        Returns:
            True if enabled, False otherwise
        """
        return self._config['model_features'].get(model_feature, False)

    def get_llm_settings(self) -> Dict[str, Any]:
        """Get LLM configuration settings."""
        return self._config['llm_settings'].copy()

    def get_ai_endpoint(self, provider: str) -> Optional[str]:
        """
        Get API endpoint for specified AI provider.

        Args:
            provider: AI provider name ('huggingface', 'openrouter')

        Returns:
            Endpoint URL or None if not configured
        """
        return self._config['ai_endpoints'].get(provider)

    def get_model_config_for_taskmaster(self) -> Dict[str, Any]:
        """
        Get model configuration formatted for TaskMaster AI integration.

        Returns:
            Dictionary with model configuration for TaskMaster
        """
        return {
            'models': {
                'main': {
                    'provider': 'anthropic',
                    'modelId': self.get_ai_model('primary'),
                    'maxTokens': self._config['llm_settings']['max_tokens'],
                    'temperature': self._config['llm_settings']['temperature']
                },
                'research': {
                    'provider': 'perplexity',
                    'modelId': self.get_ai_model('research'),
                    'maxTokens': 8700,
                    'temperature': self._config['llm_settings']['research_temperature']
                },
                'fallback': {
                    'provider': 'anthropic',
                    'modelId': self.get_ai_model('fallback'),
                    'maxTokens': self._config['llm_settings']['max_tokens'],
                    'temperature': self._config['llm_settings']['temperature']
                },
                # Additional models for testing and research
                'gemini_2_5_flash': {
                    'provider': 'google',
                    'modelId': self.get_ai_model('gemini_2_5_flash'),
                    'maxTokens': 32000,
                    'temperature': 0.1,
                    'enabled': self.is_model_enabled('enable_gemini_2_5_flash')
                },
                'deepseek_r1_hf': {
                    'provider': 'huggingface',
                    'modelId': self.get_ai_model('deepseek_r1'),
                    'maxTokens': 8192,
                    'temperature': 0.2,
                    'enabled': self.is_model_enabled('enable_deepseek_r1'),
                    'endpoint': self.get_ai_endpoint('huggingface')
                },
                'deepseek_r1_openrouter': {
                    'provider': 'openrouter',
                    'modelId': self.get_ai_model('deepseek_r1_openrouter'),
                    'maxTokens': 8192,
                    'temperature': 0.2,
                    'enabled': self.is_model_enabled('enable_deepseek_r1')
                }
            },
            'api_keys': {
                provider: key for provider, key in self._config['ai_api_keys'].items()
                if key is not None
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary (for debugging)."""
        # Return copy without sensitive information
        config_copy = self._config.copy()
        config_copy['jwt_secret_key'] = '***REDACTED***'

        # Redact API keys
        if 'ai_api_keys' in config_copy:
            config_copy['ai_api_keys'] = {
                provider: '***REDACTED***' if key else None
                for provider, key in config_copy['ai_api_keys'].items()
            }

        return config_copy


# Global configuration instance
_global_config: Optional[ACGSConfig] = None


def get_config(env_file: Optional[str] = None) -> ACGSConfig:
    """
    Get global configuration instance.

    Args:
        env_file: Optional path to environment file

    Returns:
        ACGSConfig instance
    """
    global _global_config

    if _global_config is None:
        _global_config = ACGSConfig(env_file)

    return _global_config


def reset_config() -> None:
    """Reset global configuration (useful for testing)."""
    global _global_config
    _global_config = None


# You might add more project-specific utilities here.
