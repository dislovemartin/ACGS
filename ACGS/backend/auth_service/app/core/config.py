# ACGS/backend/auth_service/app/core/config.py
import os
from typing import Any, List, Optional, Union 
from pydantic import AnyHttpUrl, field_validator, ValidationInfo 
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore' 
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ACGS-PGP Auth Service"

    SECRET_KEY: str = "your_strong_jwt_secret_key_for_auth_service" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CSRF_SECRET_KEY: str = "your_strong_csrf_secret_key_for_auth_service"

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/acgs_pgp_db"
    
    BACKEND_CORS_ORIGINS: Union[List[AnyHttpUrl], str] = "http://localhost:3000,http://localhost:3001"

    TEST_DATABASE_URL: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development" # विकास, staging, production

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[List[str], str]) -> List[AnyHttpUrl]:
        if isinstance(v, str):
            if not v.strip(): return [] 
            return [AnyHttpUrl(origin.strip()) for origin in v.split(',')]
        elif isinstance(v, list):
            return [AnyHttpUrl(origin) for origin in v]
        raise ValueError("BACKEND_CORS_ORIGINS must be a string or list of strings")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        # This validator ensures DATABASE_URL is a string.
        # Test specific URL override is handled by test configurations (e.g. conftest.py patching settings).
        # test_db_url = info.data.get("TEST_DATABASE_URL") # info.data is deprecated, use info.values in Pydantic v2
        # For pydantic_settings, direct access to other fields during validation is tricky.
        # It's better to let TEST_DATABASE_URL override DATABASE_URL in the test setup.
        # This validator should just ensure v is a valid string or use the default.
        if isinstance(v, str) and v:
            return v
        # If TEST_DATABASE_URL is set in env and DATABASE_URL is not, this logic is complex.
        # Simplification: test setup should patch settings.DATABASE_URL directly.
        return v or "postgresql+asyncpg://user:password@localhost:5432/acgs_pgp_db"


settings = Settings()
