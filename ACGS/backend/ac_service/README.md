# AC Service (Audit & Compliance Service)

The Audit & Compliance Service (`ac_service`) is responsible for managing AI governance principles and guidelines. It allows users to browse and understand the core tenets of AI governance and provides API endpoints for retrieving these principles and their associated guidelines.

## Core Functionalities

-   CRUD operations for AI governance principles.
-   Management of principle versions and statuses.
-   (Future) Management of guidelines associated with principles.

## API Endpoints

The primary API endpoints are exposed under `/api/v1/principles`. Refer to the auto-generated OpenAPI documentation at `/api/v1/principles/docs` (when the service is running via Nginx gateway) or `/docs` (if accessing the service directly) for detailed specifications.

## Technology Stack

-   Python 3.10+
-   FastAPI
-   SQLAlchemy (with PostgreSQL via `shared` module)
-   Pydantic

## Setup and Running

This service is designed to be run as a Docker container, orchestrated by Docker Compose for local development or Kubernetes for staging/production.

1.  **Prerequisites:**
    *   Docker and Docker Compose installed.
    *   A running PostgreSQL instance (managed by Docker Compose).
    *   Environment variables configured (see root `.env.example`).

2.  **Build and Run (via Docker Compose from project root):**
    ```bash
    docker-compose up --build -d ac_service
    ```

3.  **Local Development (without Docker, for direct testing):**
    *   Ensure you are in the `ACGS/backend/ac_service` directory.
    *   Set up a Python virtual environment and install dependencies:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        pip install -r requirements.txt
        pip install -r ../../requirements.txt # For shared dependencies if not handled otherwise
        ```
    *   Ensure the `DATABASE_URL` environment variable is set correctly to point to your PostgreSQL instance.
    *   Run the FastAPI application using Uvicorn:
        ```bash
        # From ACGS/backend/ac_service directory
        PYTHONPATH=../.. uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
        ```
        (The `PYTHONPATH=../..` is to help Python find the `shared` module located at the project root.)

## Dependencies

-   Refer to `requirements.txt`.
-   Shared modules from `ACGS/shared/`.
