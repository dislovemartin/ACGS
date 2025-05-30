# backend/auth_service/app/core/config.py
import os
from typing import Any, Dict, List, Optional

from pydantic import AnyHttpUrl, root_field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    # IMPORTANT: This key is loaded from the environment variable SECRET_KEY.
    # Ensure it is set to a strong, unique value in your environment.
    # For local development, you can set it in a .env file.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "please_change_me_in_production_or_env")

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    ALGORITHM: str = "HS256"

    # Refresh Token settings
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    CSRF_SECRET_KEY: str = os.getenv("CSRF_SECRET_KEY", "a_default_csrf_secret_key_change_me")

    # Backend CORS origins
    # Example for local development if your frontend runs on port 3000:
    # BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Project Name
    PROJECT_NAME: str = "ACGS-PGP Auth Service"

    # Database
    # SQLALCHEMY_DATABASE_URI will be directly set from DATABASE_URL env var
    # This aligns with shared/database.py which also reads DATABASE_URL
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/acgs_pgp_db")

    # Test Database URL. If set, it overrides SQLALCHEMY_DATABASE_URI during tests.
    # This logic is often handled in test conftest.py by patching settings or a dedicated test settings instance.
    # For simplicity in config, we can allow it to be overridden if TEST_ASYNC_DATABASE_URL is set.
    TEST_ASYNC_DATABASE_URL: Optional[str] = os.getenv("TEST_ASYNC_DATABASE_URL", None)

    @root_validator(pre=False)
    @classmethod
    def assemble_db_connection(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # Prioritize TEST_ASYNC_DATABASE_URL if set (e.g., during testing)
        test_db_url = info.data.get("TEST_ASYNC_DATABASE_URL")
        if test_db_url:
            values["SQLALCHEMY_DATABASE_URI"] = test_db_url
        # Otherwise, SQLALCHEMY_DATABASE_URI (from DATABASE_URL) is used.
        return values

    class Config:
        case_sensitive = True
        # Load environment variables from .env file for local development
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
