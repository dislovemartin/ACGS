# ACGS-PGP Developer Guide

This guide provides instructions and best practices for developers contributing to the AI Compliance Governance System - Policy Generation Platform (ACGS-PGP).

## 1. Project Setup

Refer to the `README.md` in the root directory and the `docs/deployment.md` for initial project setup using Docker Compose for local development.

### Key Steps:
1.  **Clone the repository.**
2.  **Set up environment variables:** Create `.env` files from `.env.example` in the root and `frontend` directories. Pay special attention to `DATABASE_URL`, `SECRET_KEY` (for `auth_service`), and any external API keys (e.g., for LLMs used by `pgc_service`).
3.  **Install dependencies (if working outside Docker for specific tasks):**
    *   Root: `pip install -r requirements.txt` (for Alembic, shared tools)
    *   Each backend service: `pip install -r backend/<service_name>/requirements.txt`
    *   Frontend: `cd frontend && npm install`
4.  **Run services using Docker Compose:** `docker-compose up --build -d` (from root).

## 2. Development Workflow

### Backend Service Development (FastAPI)

*   **Directory Structure (per service, e.g., `backend/auth_service/`):**
    *   `app/`: Main application code.
        *   `__init__.py`: Makes `app` a Python package.
        *   `main.py`: FastAPI app instantiation, root endpoints, including routers.
        *   `api/`: API endpoint routers (e.g., `auth.py` for authentication routes).
        *   `core/`: Configuration (`config.py`), core logic not part of API or CRUD.
        *   `crud/`: Functions for Create, Read, Update, Delete database operations (to be added).
        *   `models/`: SQLAlchemy models (definitions often in `backend/shared/models.py`).
        *   `schemas/`: Pydantic schemas for request/response validation and serialization.
        *   `tests/`: Pytest unit and integration tests.
    *   `Dockerfile`: Docker build instructions for the service.
    *   `requirements.txt`: Python dependencies for the service.

*   **Creating New Endpoints:**
    1.  Define Pydantic schemas for request and response in `app/schemas/`.
    2.  If database interaction is needed, define SQLAlchemy models in `backend/shared/models.py` (if shared) or `app/models/` (if service-specific).
    3.  Implement CRUD functions in `app/crud/` (to be created).
    4.  Create a new router in `app/api/` or add to an existing one. Import and use CRUD functions.
    5.  Include the router in `app/main.py`.
    6.  Write tests in `app/tests/`.

*   **Database Migrations (Alembic):**
    *   Models are primarily defined in `backend/shared/models.py`.
    *   When you change a model, you need to create a new migration script:
        ```bash
        # From the root acgs-pgp directory, after activating your venv with root requirements installed
        # Or using the alembic-runner service in Docker:
        docker-compose exec alembic-runner alembic revision -m "your_migration_message" --autogenerate
        ```
    *   Review the generated script in `db/migrations/versions/`.
    *   Apply migrations:
        ```bash
        docker-compose exec alembic-runner alembic upgrade head
        # Or on service startup if `command` in docker-compose.yml for alembic-runner is set to upgrade head.
        ```
    *   Ensure `db/env.py` correctly imports `Base` from `backend.shared.models` for autogenerate to work.

*   **Testing:**
    *   Use `pytest` for backend tests.
    *   Place tests in `backend/<service_name>/app/tests/`.
    *   Run tests from the root directory or service directory. Example:
        ```bash
        # From root, to run all tests for auth_service (ensure PYTHONPATH is set or use venv)
        # python -m pytest backend/auth_service/app/tests 
        # Or via docker-compose if test script is configured in service's Dockerfile or a dedicated test service
        ```
    *   The CI pipeline (`.github/workflows/main.yml`) should also run these tests.

### Frontend Service Development (React)

*   **Directory Structure (`frontend/src/`):**
    *   `api/`: API client (Axios) and endpoint definitions.
    *   `components/`: Reusable UI components (currently empty, to be populated).
    *   `pages/`: Page-level components.
    *   `App.js`: Main router and layout structure.
    *   `index.js`: Application entry point.
    *   Other standard Create React App files.

*   **Creating New Components/Pages:**
    1.  Create new `.js` (or `.jsx`) files in `components/` or `pages/`.
    2.  Import and use them where needed.
    3.  For pages, add routes in `App.js`.
    4.  For API interactions, add functions to `api/index.js`.

*   **State Management:**
    *   Initially, component-local state (`useState`, `useEffect`) is fine.
    *   For global state (e.g., user authentication status), consider React Context API or a state management library like Redux or Zustand as the application grows.

*   **Styling:**
    *   Global styles in `index.css` and `App.css`.
    *   Component-specific styles can be done using CSS Modules, styled-components, or Tailwind CSS (if added). For now, `App.css` contains some basic form and page styling examples.

*   **Testing:**
    *   Use Jest and React Testing Library.
    *   Place tests alongside components (e.g., `MyComponent.test.js`).
    *   Run tests: `cd frontend && npm test`.

## 3. Coding Guidelines & Best Practices

*   **Python (Backend):**
    *   Follow PEP 8 style guidelines. Use a linter like Flake8 and a formatter like Black.
    *   Use type hints for all function signatures and important variables.
    *   Write clear, concise comments, especially for complex logic.
    *   Structure imports: standard library, then third-party, then local application imports.
    *   Handle exceptions gracefully and provide meaningful error messages in API responses.
    *   Ensure all API endpoints have appropriate request and response models (Pydantic schemas).

*   **JavaScript (Frontend):**
    *   Follow a consistent style guide (e.g., Airbnb, StandardJS). Use ESLint and Prettier.
    *   Use functional components with Hooks.
    *   Write clear comments.
    *   Handle API errors and provide user feedback.

*   **General:**
    *   **Git:**
        *   Use feature branches for new development (`git checkout -b feature/my-new-feature`).
        *   Write clear, concise commit messages.
        *   Rebase your feature branch on `main` before creating a Pull Request to resolve conflicts.
        *   Ensure tests pass before pushing and creating a PR.
    *   **Secrets:** Never commit secrets or sensitive credentials to the repository. Use environment variables and `.env` files (ignored by Git) for local development, and Kubernetes Secrets or similar for production.
    *   **Dependencies:** Keep dependencies up-to-date and regularly check for vulnerabilities. Document reasons for choosing specific libraries.
    *   **Documentation:**
        *   Update relevant documentation (`README.md`, `docs/*`) when adding features or making significant changes.
        *   Document API endpoints (FastAPI does this automatically via OpenAPI, but ensure docstrings are clear).

## 4. API Design

*   Strive for RESTful API design principles.
*   Use standard HTTP methods (GET, POST, PUT, DELETE).
*   Use standard HTTP status codes.
*   Version APIs if/when breaking changes are introduced (e.g., `/api/v1/...`).

## 5. Error Handling

*   Backend services should return appropriate HTTP status codes and JSON error responses, e.g.:
    ```json
    { "detail": "Error message or object with more info" }
    ```
*   Frontend should catch errors from API calls and display user-friendly messages.

## 6. Environment Variables

*   **Backend:** Use `pydantic-settings` in `core/config.py` to load settings from environment variables and `.env` files.
*   **Frontend:** Use `REACT_APP_` prefixed environment variables, accessible via `process.env.REACT_APP_...`. Store them in `.env` files in the `frontend` directory.

## 7. CI/CD

*   A basic CI/CD pipeline is set up in `.github/workflows/main.yml`.
*   It currently includes placeholders for running tests and building/pushing Docker images.
*   Expand this pipeline to include:
    *   Linting and code style checks.
    *   Comprehensive test execution for all services.
    *   Automated Docker image builds and pushes to a container registry.
    *   Automated deployment to staging/production Kubernetes environments (with appropriate safeguards).

This guide should evolve as the project grows. Contributions to this guide are welcome!
