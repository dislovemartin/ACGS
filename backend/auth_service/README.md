# Authentication Service (`auth_service`)

This service is responsible for managing user authentication and authorization within the ACGS-PGP system.

## Core Responsibilities

-   User registration and login.
-   Issuing and validating JWT access and refresh tokens.
-   Password hashing and management.
-   CSRF protection mechanisms.
-   Integration with `shared/models.py` for User and RefreshToken models.
-   Integration with `shared/schemas.py` for User and Token DTOs.

## API Endpoints

Detailed API documentation is available via Swagger UI at `/api/v1/auth/docs` when the service is running.

Key endpoints typically include:
-   `/api/v1/auth/register`
-   `/api/v1/auth/login`
-   `/api/v1/auth/logout`
-   `/api/v1/auth/refresh`
-   `/api/v1/auth/me` (to get current user details)

## Dependencies

-   FastAPI
-   SQLAlchemy (via `shared` module)
-   Pydantic (via `shared` module)
-   Passlib for password hashing
-   Python-JOSE for JWTs

Refer to `requirements.txt` for specific package versions.
