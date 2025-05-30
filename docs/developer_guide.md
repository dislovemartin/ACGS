# ACGS-PGP Developer Guide

This comprehensive guide provides instructions and best practices for developers contributing to the AI Compliance Governance System - Policy Generation Platform (ACGS-PGP) with all Phase 1-3 features including Constitutional Council, AlphaEvolve integration, Z3 formal verification, and PGP cryptographic integrity.

## 1. Development Environment Setup

### **Prerequisites**
- Docker 20.10+ with Docker Compose v2
- Python 3.9+ for local development
- Node.js 16+ for frontend development
- Git with proper SSH/HTTPS configuration
- OpenAI API key for LLM integration
- Basic understanding of constitutional AI governance principles

### **Initial Setup**
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/dislovemartin/ACGS.git
    cd ACGS-master
    ```

2.  **Environment Configuration:**
    ```bash
    # Copy environment templates
    cp config/env/.env.example .env
    cd src/frontend && cp .env.example .env && cd ../..

    # Configure critical variables in .env
    # - DATABASE_URL: PostgreSQL connection string
    # - OPENAI_API_KEY: Required for constitutional prompting
    # - JWT_SECRET_KEY: Authentication security
    # - PGP_KEY_ID: Cryptographic integrity
    ```

3.  **Development Dependencies (Optional for local work):**
    ```bash
    # Python virtual environment
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate   # Windows

    # Install development tools
    pip install -r tools/requirements.txt

    # Frontend dependencies
    cd src/frontend && npm install && cd ../..
    ```

4.  **Start Development Environment:**
    ```bash
    # Build and start all services
    docker-compose -f config/docker/docker-compose.yml up --build -d

    # Load constitutional test data
    python scripts/load_test_data.py

    # Verify deployment
    python scripts/verify_acgs_deployment.sh
    ```

## 2. Development Workflow

### 2.1 Data Models
A thorough understanding of the core data models is essential for developing new features and maintaining the system. These models define the structure of data persisted in the database and are shared across multiple backend services. Detailed descriptions of models such as `User`, `Policy`, `Principle`, `AuditLog`, and their relationships can be found in the [Data Models Guide](./data_models.md).

### 2.2 Backend Service Development (FastAPI)

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
    3.  Implement CRUD functions in `app/crud/` (to be created). (Note: Standardized CRUD function patterns and their detailed documentation are evolving. Please refer to existing service implementations for current examples. Comprehensive guidance will be added once patterns are finalized.)
    4.  Create a new router in `app/api/` or add to an existing one. Import and use CRUD functions.
    5.  Include the router in `app/main.py`.
    6.  Write tests in `app/tests/`.

*   **Database Migrations (Alembic):**
    *   Models are primarily defined in `backend/shared/models.py`. Refer to the [Data Models Guide](./data_models.md) for details on these models.
    *   When you change a model, you need to create a new migration script:
        ```bash
        # From the root acgs-pgp directory, after activating your venv with root requirements installed
        # Or using the alembic-runner service in Docker:
        docker-compose exec alembic-runner alembic revision -m "your_migration_message" --autogenerate
        ```
    *   Review the generated script in `alembic/versions/` (Note: the path was `db/migrations/versions/` in the original text, but `alembic/versions` is more standard for Alembic setup and matches the project structure).
    *   Apply migrations:
        ```bash
        docker-compose exec alembic-runner alembic upgrade head
        # Or on service startup if `command` in docker-compose.yml for alembic-runner is set to upgrade head.
        ```
    *   Ensure `alembic/env.py` correctly imports `Base` from `shared.database` and target metadata from your models (e.g., `from shared.models import Base` and ensure all models are imported where `Base` is defined or are accessible) for autogenerate to work.

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
    *   `components/`: Reusable UI components (currently empty, to be populated). The `frontend/src/components/` directory is for reusable UI components, which are actively being developed. Detailed documentation for these components will be provided as they are finalized and stabilized.
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

## 3. Contribution Workflow

Contributing to ACGS-PGP involves a structured workflow to ensure code quality, consistency, and effective collaboration. This section outlines the typical steps for contributing.

**a. Finding and Discussing Work:**
*   **Check GitHub Issues:** Look for existing issues labeled `help wanted` or `good first issue` if you're new.
*   **Propose Changes:** For significant new features, bug fixes, or architectural changes, it's highly recommended to open a GitHub Issue first. This allows for discussion and alignment before development begins. Describe the problem or feature and your proposed solution.

**b. Local Environment Setup:**
*   Ensure your local development environment is set up correctly by following the instructions in the main project `README.md` and Section 1 ("Project Setup") of this guide.
*   **Pre-commit Hooks:** Install pre-commit hooks to automatically run linters and formatters before each commit. Run this once after cloning:
    ```bash
    pre-commit install
    ```

**c. Branching:**
*   **Base Branch:** All feature branches should typically be based on the `main` branch.
*   **Branch Naming:** Use descriptive branch names prefixed with a type, for example:
    *   `feature/name-of-feature` (e.g., `feature/user-profile-page`)
    *   `bugfix/issue-number-description` (e.g., `bugfix/42-fix-login-error`)
    *   `docs/update-section` (e.g., `docs/improve-contributing-guide`)
    *   `refactor/component-name` (e.g., `refactor/auth-service-jwt-handling`)

**d. Developing and Making Changes:**
*   **Coding Guidelines:** Adhere to the coding guidelines detailed in Section 4 ("Coding Guidelines & Best Practices"). This includes:
    *   Python: PEP 8, Black for formatting, Flake8 for linting, type hints.
    *   JavaScript: Consistent style (ESLint, Prettier), functional components with Hooks.
*   **Unit Tests:** Write new unit tests for any new functionality or bug fixes. Ensure existing tests are updated if necessary.
    *   Backend tests are typically in `backend/<service_name>/app/tests/`.
    *   Frontend tests are co-located with components.
*   **Documentation:** Update any relevant documentation if your changes affect system behavior, APIs, architecture, or user guides. This includes service READMEs, files in the `docs/` directory (like `data_models.md` or `architecture.md`), and inline code comments.
*   **Pre-commit Checks:** Before committing, ensure pre-commit hooks run and pass. You can also run them manually on all files:
    ```bash
    pre-commit run --all-files
    ```
    This helps catch formatting and linting issues early.

**e. Testing Locally:**
*   Before submitting your changes, run all relevant tests locally to ensure they pass:
    *   Backend: `python -m pytest backend/<service_name>/app/tests/` (or run all tests).
    *   Frontend: `cd frontend && npm test`.
*   Confirm that linters and formatters (via pre-commit hooks) are clean.

**f. Committing Changes:**
*   **Commit Messages:** Write clear, concise, and informative commit messages.
    *   Use the imperative mood (e.g., "Add user registration endpoint" instead of "Added user registration" or "Adds user registration").
    *   The first line should be a short summary (around 50 characters).
    *   If more detail is needed, leave a blank line after the summary and then provide a more detailed explanation.
*   **Logical Commits:** Group related changes into logical commits. Avoid making overly large commits that bundle unrelated changes.

**g. Keeping Feature Branch Updated:**
*   Periodically update your feature branch with the latest changes from the `main` branch (or the project's primary integration branch):
    ```bash
    git fetch origin
    git rebase origin/main
    ```
    This helps minimize merge conflicts and ensures your changes are based on the most recent codebase. Resolve any conflicts that arise during the rebase.

**h. Submitting a Pull Request (PR):**
*   **Target Branch:** PRs should typically target the `main` branch.
*   **Create PR:** Push your feature branch to your fork on GitHub and create a Pull Request.
*   **PR Title and Description:**
    *   **Title:** Write a clear and concise title that summarizes the PR's purpose.
    *   **Description:**
        *   Provide a detailed explanation of the changes made.
        *   Link to any relevant GitHub Issue(s) (e.g., "Fixes #123" or "Resolves #123").
        *   Describe how your changes have been tested (e.g., unit tests added, manual testing steps).
*   **CI Checks:** The project's CI pipeline (configured in `.github/workflows/ci.yml`) will automatically run when you open a PR. These checks include linters, tests (though currently, the `ci.yml` primarily shows LaTeX, markdown, and secret scanning; backend/frontend tests should be part of this), and other quality assurance steps. Ensure these checks pass.

**i. Code Review Process:**
*   Once a PR is submitted, maintainers or other designated developers will review your changes.
*   Be prepared to discuss your changes and address any feedback or questions from reviewers.
*   If changes are requested:
    *   Make the necessary updates in your local feature branch.
    *   Commit the changes and push them to your remote feature branch. The PR will update automatically.
    *   Clearly communicate when you've addressed the comments.

**j. Merging the PR:**
*   After the PR is approved by reviewers and all CI checks have passed, a maintainer will merge it into the `main` branch.

**k. Post-Merge (Optional):**
*   Once your PR is merged, you can typically delete your local and remote feature branch to keep your repository clean:
    ```bash
    git branch -d feature/my-cool-feature
    git push origin --delete feature/my-cool-feature
    ```

## 4. Coding Guidelines & Best Practices

*   **Python (Backend):**
    *   Follow PEP 8 style guidelines. Use a linter like Flake8 and a formatter like Black. (These are partially enforced by pre-commit hooks).
    *   Use type hints for all function signatures and important variables.
    *   Write clear, concise comments, especially for complex logic.
    *   Structure imports: standard library, then third-party, then local application imports. (Consider adding `isort` to pre-commit hooks).
    *   Handle exceptions gracefully and provide meaningful error messages in API responses.
    *   Ensure all API endpoints have appropriate request and response models (Pydantic schemas).

*   **JavaScript (Frontend):**
    *   Follow a consistent style guide (e.g., Airbnb, StandardJS). Use ESLint and Prettier. (Ensure these are in pre-commit hooks if not already).
    *   Use functional components with Hooks.
    *   Write clear comments.
    *   Handle API errors and provide user feedback.

*   **General:**
    *   **Secrets:** Never commit secrets or sensitive credentials to the repository. Use environment variables and `.env` files (ignored by Git) for local development, and Kubernetes Secrets or similar for production. (Trufflehog in CI helps detect these).
    *   **Dependencies:** Keep dependencies up-to-date and regularly check for vulnerabilities. Document reasons for choosing specific libraries.
    *   **Documentation:**
    *   Update relevant documentation (`README.md`, `docs/*`, including `docs/data_models.md` if model structures change) when adding features or making significant changes.
        *   Document API endpoints (FastAPI does this automatically via OpenAPI, but ensure docstrings are clear).

## 5. API Design

*   Strive for RESTful API design principles.
*   Use standard HTTP methods (GET, POST, PUT, DELETE).
*   Use standard HTTP status codes.
*   Version APIs if/when breaking changes are introduced (e.g., `/api/v1/...`).

### 4.5 Inter-Service Communication Patterns

Developing features often requires one backend service to call another. Understanding how these services communicate is crucial.

**a. Primary Mechanism:**
Inter-service communication within the ACGS-PGP system is primarily synchronous, using RESTful APIs over HTTP/JSON. Each service exposes endpoints that others can call to request data or trigger actions.

**b. Service Addressing:**
*   **Local Development (Docker Compose):** Services are typically addressed via the Nginx API Gateway defined in `docker-compose.yml`. The base URL is usually `http://nginx:<port>/api/<service-prefix>/` from within the Docker network (where `<port>` is Nginx's internal port, often 80), or `http://localhost:8000/api/<service-prefix>/` when accessed from the host machine. The Nginx gateway routes requests to the appropriate backend service based on the path prefix (e.g., `/api/auth` to `auth_service`, `/api/pgc` to `pgc_service`).
*   **Kubernetes Deployment:** In Kubernetes, services are typically addressed via their Kubernetes service names (e.g., `http://auth-service.namespace.svc.cluster.local/api/auth/`) for direct internal calls, or through an Ingress controller which acts as the API gateway for external and potentially internal traffic.

**c. Request/Response Conventions:**
*   **Data Transfer Objects (DTOs):** Pydantic schemas are extensively used for request validation and response serialization. Schemas defined in `backend/shared/schemas.py` are preferred for common data structures to ensure consistency across services. Service-specific schemas are defined within `backend/<service_name>/app/schemas/`.
*   **Error Responses:** Standardized JSON error responses are used, as detailed in Section 5 ("Error Handling"). Typically, this involves a `{"detail": "Error message or object with more info"}` structure.

**d. Standard HTTP Status Codes:**
Services should use standard HTTP status codes to indicate the outcome of an API request. Common codes include:
    *   `200 OK`: Request succeeded.
    *   `201 Created`: Request succeeded, and a new resource was created.
    *   `204 No Content`: Request succeeded, but there is no content to return (e.g., for DELETE operations).
    *   `400 Bad Request`: The server could not understand the request due to invalid syntax or missing parameters (often a Pydantic validation error).
    *   `401 Unauthorized`: Authentication is required, and the client has not provided valid credentials (e.g., missing or invalid JWT).
    *   `403 Forbidden`: The client is authenticated but does not have permission to access the requested resource.
    *   `404 Not Found`: The requested resource could not be found.
    *   `409 Conflict`: The request could not be completed due to a conflict with the current state of the resource (e.g., trying to create a unique resource that already exists).
    *   `422 Unprocessable Entity`: The request was well-formed but could not be processed due to semantic errors (FastAPI uses this for validation errors by default).
    *   `500 Internal ServerError`: An unexpected error occurred on the server.

**e. Authentication for Service Calls:**
If a service endpoint requires authentication (which is common for most non-public endpoints), the calling service must include a valid JWT in the `Authorization` header, typically as a Bearer token (e.g., `Authorization: Bearer <token>`). This is consistent with how client-to-gateway authentication works. Services should be configured to validate these tokens, potentially by calling an endpoint on the `auth_service` or using a shared JWT validation utility.

**f. Shared DTOs/Schemas:**
As mentioned, utilizing `shared/schemas.py` for common Data Transfer Objects (DTOs) is highly encouraged. This practice minimizes code duplication and reduces the risk of inconsistencies when services exchange data.

**g. Future Considerations:**
While current communication is synchronous, `docs/architecture.md` notes that asynchronous communication (e.g., via a message queue like RabbitMQ or Kafka) may be introduced in the future for tasks like triggering formal verification or complex policy generation steps to improve system responsiveness and resilience. Developers should be mindful of this potential evolution when designing new features that might benefit from asynchronous patterns.

## 5. Error Handling

*   Backend services should return appropriate HTTP status codes (see "Standard HTTP Status Codes" in section 4.5.d) and JSON error responses. The standard error response body is:
    ```json
    { "detail": "Error message or object with more info" }
    ```
    For validation errors from FastAPI (often returning a 422 status code), the "detail" field might contain an array of error objects specifying the location and type of error.
*   Frontend should catch errors from API calls and display user-friendly messages.

## 6. Environment Variables

*   **Backend:** Use `pydantic-settings` in `core/config.py` to load settings from environment variables and `.env` files.
*   **Frontend:** Use `REACT_APP_` prefixed environment variables, accessible via `process.env.REACT_APP_...`. Store them in `.env` files in the `frontend` directory.

## 7. CI/CD

*   The CI/CD pipeline, configured in `.github/workflows/`, currently automates linting, some unit tests (Python, Markdown), secret scanning, and Docker image builds. More comprehensive integration and end-to-end tests are planned for future phases.
*   Planned expansions for the CI/CD pipeline include:
    *   More comprehensive linting and code style checks across frontend and backend.
    *   Broader unit and integration test execution for all services.
    *   Automated Docker image pushes to a container registry upon successful builds on the main branch.
    *   Automated deployment to staging/production Kubernetes environments (with appropriate safeguards).

## 8. Debugging and Troubleshooting Common Issues

This section provides practical advice for debugging common issues encountered during development. For deployment-specific troubleshooting, also refer to the "Troubleshooting" section in `docs/deployment.md`.

**a. General Debugging Strategies:**

*   **Accessing Service Logs:** Logs are your first port of call for understanding application behavior and errors.
    *   **Docker Compose:** View logs for a specific service:
        ```bash
        docker-compose logs <service_name>
        ```
        To follow logs in real-time (tail):
        ```bash
        docker-compose logs -f <service_name>
        ```
        To view logs for all services:
        ```bash
        docker-compose logs -f
        ```
    *   **Kubernetes:** View logs for a specific pod and container:
        ```bash
        kubectl logs <pod_name> -c <container_name>
        ```
        To follow logs in real-time:
        ```bash
        kubectl logs -f <pod_name> -c <container_name>
        ```
*   **Python Debugger (`pdb`):** For backend services, you can use Python's built-in debugger. Insert `import pdb; pdb.set_trace()` in your Python code where you want to start debugging. When the code executes, you'll get an interactive console in the terminal where the service is running (or in Docker logs if running detached).
*   **Browser Developer Tools:** For frontend debugging:
    *   **Console:** Check for JavaScript errors, `console.log()` outputs.
    *   **Network Tab:** Inspect API requests and responses, check status codes, and view payload data.
    *   **Elements/Inspector:** Examine the HTML structure and CSS styles.
    *   **Sources Tab:** Set breakpoints in JavaScript code.
*   **Isolate the Problem:** Try to break down the problem into smaller parts. If possible, create a minimal reproducible example to demonstrate the issue. This helps in pinpointing the root cause.

**b. Docker Compose Specific Issues:**

*   **Service Connectivity:**
    *   Ensure environment variables for service connections (e.g., `DATABASE_URL` in a backend service's `.env` or its Docker environment block in `docker-compose.yml`) use the correct Docker Compose service names (e.g., `postgres`, `auth_service`) as hostnames, not `localhost` or `127.0.0.1`. Refer to `docker-compose.yml` for defined service names.
    *   See also `docs/deployment.md` "Troubleshooting" for more on `DATABASE_URL`.
*   **Port Conflicts:** If a service fails to start, check if the host ports it's trying to use (e.g., `8000:8000` for Nginx, `3000:3000` for frontend) are already in use by another application on your machine. Change the host port in `docker-compose.yml` if necessary (e.g., `8001:8000`).
*   **Volume Issues:** Ensure volume mounts in `docker-compose.yml` are correctly configured, especially paths to shared code or configuration files. Incorrect paths can lead to "file not found" errors or outdated code running in containers.
*   **Service Status:** Check the status of all services:
    ```bash
    docker-compose ps
    ```
    Ensure all essential services (like `postgres`, `nginx`, and the service you're working on) are `Up` or `Running`.
*   **Rebuilding Images:** If you've made changes to a `Dockerfile` or files copied during the image build, they might not be reflected unless you rebuild the image.
    ```bash
    docker-compose up --build -d <service_name> # Rebuild specific service
    docker-compose up --build -d                # Rebuild all services
    ```
*   **Resource Limits:** Docker Desktop (or other Docker environments) may have resource limits (CPU, memory). If services are slow or crashing unexpectedly, check these settings.

**c. Kubernetes Specific Issues (Brief Overview):**

For detailed Kubernetes troubleshooting, always refer to `k8s/README.md` and the "Troubleshooting" section in `docs/deployment.md`.

*   **Pod Startup Errors:** Use `kubectl describe pod <pod_name>` to get detailed information about a pod's state, including events that might indicate why it's not starting (e.g., image pull errors, readiness/liveness probe failures, ConfigMap/Secret mounting issues).
*   **Cluster Events:** Check for cluster-level issues or events related to your application:
    ```bash
    kubectl get events --sort-by='.lastTimestamp'
    ```
*   **Common Areas:**
    *   **ConfigMap/Secret Issues:** Ensure they are correctly created, mounted into pods, and that data is being read as expected (e.g., environment variables from secrets).
    *   **Networking/DNS:** Inter-pod communication relies on Kubernetes DNS. If services can't reach each other by their service names, investigate DNS resolution and network policies.

**d. Backend Service Issues (FastAPI):**

*   **422 Unprocessable Entity Errors:** FastAPI returns this status code when request validation fails (e.g., incorrect data types, missing required fields). The response body will typically contain a `detail` field with an array of objects, each specifying the error location (e.g., `body`, `query`, `path`) and type. Carefully examine this detail.
*   **Database Connection Issues:**
    *   Double-check the `DATABASE_URL` in the service's `.env` file (or environment variables if deployed). Ensure it's correct for the environment (Docker Compose service name, Kubernetes service name, or external DB address).
    *   Verify the database server is running and accessible from the service container.
*   **Alembic Migration Problems:**
    *   **Migrations Not Generated:** If you've changed SQLAlchemy models in `shared/models.py`, ensure you've generated a new migration script:
        ```bash
        docker-compose exec alembic-runner alembic revision -m "your_migration_message" --autogenerate
        ```
    *   **Migrations Not Applied:** Ensure migrations are applied when services start (as configured for `alembic-runner` in `docker-compose.yml`) or by running manually:
        ```bash
        docker-compose exec alembic-runner alembic upgrade head
        ```
    *   **Verify Current Version:** You can check the current database schema version by querying the `alembic_version` table in your PostgreSQL database (e.g., using `psql` or a DB client).
    *   Refer to `docs/deployment.md` "Troubleshooting > Migration Errors" for more.

**e. Frontend Service Issues (React):**

*   **API Connectivity:**
    *   Verify `REACT_APP_API_BASE_URL` in `frontend/.env` is correctly set to point to your API gateway (e.g., `http://localhost:8000/api` for local Docker Compose setup).
    *   Use the browser's Network tab to inspect failed API calls. Check the request URL, headers, payload, and response status code and body.
    *   If using Nginx as a proxy (common in Docker Compose), check Nginx logs for errors: `docker-compose logs nginx`.
*   **JavaScript Errors:** Open the browser's JavaScript console to check for runtime errors, unhandled promise rejections, etc.
*   **State Management Debugging:**
    *   Use React DevTools browser extension to inspect component hierarchy, props, and state.
    *   If using a global state management library (like Redux, Zustand), use their specific devtools for deeper state inspection and action tracing.
*   **Build Issues:** If the React app doesn't build or fails with errors, check the terminal output from the `frontend` service (`docker-compose logs -f frontend`) for specific error messages from `react-scripts`.

**f. Seeking Further Assistance:**

*   **Check Existing GitHub Issues:** Someone might have encountered and solved a similar problem. Search open and closed issues.
*   **Ask Colleagues/Maintainers:** If you're stuck after trying the above, don't hesitate to ask for help from project maintainers or other developers on the team. Provide clear details about the problem, what you've tried, and any relevant logs or error messages.

This guide should evolve as the project grows. Contributions to this guide are welcome!
