import importlib
import os
import sys
from pathlib import Path
import pytest


def reload_endpoints():
    """Reload endpoints with minimal dependencies."""
    # Provide placeholder for missing security helper
    import src.backend.auth_service.app.core.security as security
    if not hasattr(security, "get_current_active_user_from_cookie"):
        setattr(security, "get_current_active_user_from_cookie", lambda: None)

    # Ensure the schemas module refers to the actual schemas.py file
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "src/backend/auth_service/app/schemas.py"
    spec = importlib.util.spec_from_file_location("temp_schemas", schema_path)
    schemas_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schemas_mod)
    sys.modules["src.backend.auth_service.app.schemas"] = schemas_mod

    import src.backend.auth_service.app.api.endpoints as endpoints
    importlib.reload(endpoints)
    return endpoints


@pytest.mark.unit
def test_secure_cookie_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    endpoints = reload_endpoints()
    assert endpoints.SECURE_COOKIE is False


@pytest.mark.unit
def test_secure_cookie_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    endpoints = reload_endpoints()
    assert endpoints.SECURE_COOKIE is True
