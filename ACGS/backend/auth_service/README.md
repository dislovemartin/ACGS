# Auth Service

The Authentication Service (`auth_service`) is responsible for user registration, login, session management, and token issuance (JWTs). It forms the primary security layer for user-facing interactions with the ACGS-PGP platform.

## Core Functionalities

-   User registration with password hashing (Argon2).
-   User login with username/password, issuing JWT access and refresh tokens.
-   Tokens are primarily managed via secure, HttpOnly cookies.
-   CSRF (Cross-Site Request Forgery) protection for cookie-based sessions.
-   Refresh token mechanism for renewing access tokens.
-   Logout functionality that revokes tokens and clears cookies.
-   Retrieval of current authenticated user's details (`/me` endpoint).
-   (Future/Placeholder) User management (CRUD for users by admins).
-   (Future/Placeholder) Role and permission management.

## API Endpoints

The primary API endpoints are exposed under `/api/v1/auth`. Refer to the auto-generated OpenAPI documentation at `/api/v1/auth/docs` (when the service is running via Nginx gateway) or `/docs` (if accessing the service directly) for detailed specifications.

Key endpoints include:
-   `/register`
-   `/token` (login)
-   `/token/refresh`
-   `/logout`
-   `/me`
-   `/users/` (admin-only user management, placeholder)

## Technology Stack

-   Python 3.10+
-   FastAPI
-   SQLAlchemy (with PostgreSQL via `shared` module)
-   Pydantic
-   Argon2 (for password hashing via `argon2-cffi`)
-   python-jose (for JWT handling)
-   fastapi-csrf-protect (for CSRF protection)
-   slowapi (for rate limiting)

## Setup and Running

This service is designed to be run as a Docker container, orchestrated by Docker Compose for local development or Kubernetes for staging/production.

1.  **Prerequisites:**
    *   Docker and Docker Compose installed.
    *   A running PostgreSQL instance (managed by Docker Compose).
    *   Environment variables configured (see root `.env.example`), especially:
        *   `DATABASE_URL`
        *   `AUTH_SERVICE_SECRET_KEY` (for JWTs)
        *   `AUTH_SERVICE_CSRF_SECRET_KEY`

2.  **Build and Run (via Docker Compose from project root):**
    ```bash
    docker-compose up --build -d auth_service
    ```

3.  **Local Development (without Docker, for direct testing):**
    *   Ensure you are in the `ACGS/backend/auth_service` directory.
    *   Set up a Python virtual environment and install dependencies:
        ```bash
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        pip install -r ../../requirements.txt # For shared dependencies
        ```
    *   Ensure required environment variables (`DATABASE_URL`, `SECRET_KEY`, `CSRF_SECRET_KEY`, etc.) are set.
    *   Run the FastAPI application using Uvicorn:
        ```bash
        # From ACGS/backend/auth_service directory
        PYTHONPATH=../.. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ```

## Dependencies

-   Refer to `requirements.txt`.
-   Shared modules from `ACGS/shared/`.
