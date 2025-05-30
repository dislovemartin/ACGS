# ACGS-PGP: AI Compliance Governance System - Policy Generation Platform

The ACGS-PGP framework is a microservices-based system designed to facilitate the creation, management, verification, and audit of AI governance policies. It aims to integrate constitutional principles with dynamic, AI-driven rule synthesis and verifiable runtime enforcement.

## Overview

This project implements the core components of the ACGS-PGP framework, including:
-   **Authentication Service (`auth_service`):** Manages user authentication, authorization, and RBAC (Admin/Policy Manager/Auditor roles).
-   **Audit & Compliance Service (`ac_service`):** Manages AI governance principles with enhanced constitutional features, meta-rules, Constitutional Council, and conflict resolution mechanisms.
-   **Governance Synthesis Service (`gs_service`):** Generates policies using LLM integration with constitutional prompting, contextual analysis, and AlphaEvolve integration for evolutionary computation governance.
-   **Formal Verification Service (`fv_service`):** Verifies synthesized policies against principles using Z3 SMT solver integration, tiered validation (Automated/HITL/Rigorous), and safety property checking.
-   **Integrity & Verifiability Service (`integrity_service`):** Stores policies, verification results, audit logs, and implements PGP Assurance with cryptographic integrity (digital signatures, SHA3-256 hashing, Merkle trees).
-   **Protective Governance Controls Service (`pgc_service`):** Enforces policies at runtime with real-time governance decisions, AlphaEvolve enforcement, and performance optimization for sub-20ms latency.
-   **Frontend Service:** A React-based SPA for user interaction with Constitutional Council workflows, policy management, and governance dashboards.

## Technology Stack

-   **Backend:** Python (FastAPI) with async/await patterns
-   **Frontend:** JavaScript (React) with governance dashboards
-   **Database:** PostgreSQL with JSONB support for constitutional data
-   **LLM Integration:** OpenAI GPT-4 for constitutional prompting and policy synthesis
-   **Formal Verification:** Z3 SMT solver for mathematical verification
-   **Cryptography:** PGP/GPG for digital signatures, SHA3-256 for hashing, Merkle trees for integrity
-   **Containerization:** Docker with multi-stage builds
-   **Orchestration:** Docker Compose (local development), Kubernetes (production deployment)
-   **Database Migrations:** Alembic with constitutional schema enhancements
-   **API Gateway:** Nginx with service routing and load balancing
-   **Monitoring:** Prometheus and Grafana integration
-   **Authentication:** JWT tokens with RBAC (Role-Based Access Control)

## Project Structure

The project is organized into several main directories:
-   `migrations/`: Database migration scripts (Alembic).
-   `src/`: Contains all source code.
    -   `backend/`: Backend microservices and shared modules.
        -   `ac_service/`: Audit & Compliance Service
        -   `auth_service/`: Authentication Service
        -   `fv_service/`: Formal Verification Service
        -   `gs_service/`: Governance Synthesis Service
        -   `integrity_service/`: Integrity & Verifiability Service
        -   `pgc_service/`: Protective Governance Controls Service
        -   `shared/`: Shared Python modules (database models, schemas, utilities)
    -   `frontend/`: React frontend application.
    -   `alphaevolve_gs_engine/`: AlphaEvolve integration engine.
-   `tests/`: Centralized test directory.
    -   `unit/`: Unit tests organized by service.
    -   `integration/`: Integration tests for cross-service functionality.
    -   `e2e/`: End-to-end workflow tests.
-   `config/`: All configuration files.
    -   `docker/`: Docker Compose and Dockerfile configurations.
    -   `k8s/`: Kubernetes deployment manifests.
    -   `env/`: Environment variable templates.
    -   `monitoring/`: Monitoring and alerting configurations.
-   `docs/`: Project documentation organized by type.
    -   `api/`: API documentation and schemas.
    -   `deployment/`: Deployment guides and checklists.
    -   `development/`: Developer guides and contribution docs.
    -   `research/`: Research papers and academic content.
    -   `user/`: User guides and tutorials.
-   `scripts/`: Utility scripts for development, testing, and deployment.
-   `data/`: Test data, policy corpus, and sample datasets.
-   `tools/`: Development tools and build utilities.

## Local Development Setup

### Prerequisites

-   Docker
-   Docker Compose

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd ACGS
    ```

2.  **Configure Environment Variables:**
    *   Copy the environment template to the root directory and update the variables, especially `DATABASE_URL` and service-specific secrets like `AUTH_SERVICE_SECRET_KEY`.
        ```bash
        cp config/env/.env.example .env
        ```
    *   Navigate to the `src/frontend` directory, copy `frontend/.env.example` to `frontend/.env`, and update `REACT_APP_API_BASE_URL` if necessary (default is `/api` which assumes Nginx proxying from root or a specific host port).
        ```bash
        cd src/frontend
        cp .env.example .env
        cd ../..
        ```
        The `REACT_APP_API_BASE_URL` in `src/frontend/.env` should typically be `/api` if you are accessing the frontend via `http://localhost:3000` and the Nginx gateway (defined in `config/docker/docker-compose.yml`) is serving backend APIs at `http://localhost:8000/api/...`. The `proxy` setting in `src/frontend/package.json` (e.g., `"proxy": "http://localhost:8000"`) can also handle this for development by proxying frontend's `/api` calls to the backend Nginx.

3.  **Build and Run Services using Docker Compose:**
    From the project root directory (`ACGS-master/`):

    **Primary Command to Start the System:**
    ```bash
    docker-compose -f config/docker/docker-compose.yml up --build -d
    ```
    This command will:
    *   Build Docker images for all services.
    *   Start containers for each service, including PostgreSQL and Nginx.
    *   Run database migrations via the `alembic-runner` service.

4.  **Accessing Services:**
    *   **Frontend:** `http://localhost:3000` (served by React development server, proxied by Docker Compose)
    *   **Backend API Gateway (Nginx):** `http://localhost:8000`
        *   Auth Service: `http://localhost:8000/api/auth/`
        *   AC Service: `http://localhost:8000/api/ac/`
        *   GS Service: `http://localhost:8000/api/gs/`
        *   FV Service: `http://localhost:8000/api/fv/`
        *   Integrity Service: `http://localhost:8000/api/integrity/`
        *   PGC Service: `http://localhost:8000/api/pgc/`
    *   API documentation for each service is typically available at `/docs` or `/redoc` on their respective Nginx paths (e.g., `http://localhost:8000/api/auth/docs`).

5.  **Database Migrations (Manual, if needed):**
    The `alembic-runner` service runs migrations on startup. To run them manually:
    ```bash
    docker-compose -f config/docker/docker-compose.yml exec alembic-runner alembic upgrade head
    ```
    To create a new migration after changing models in `src/backend/shared/models.py`:
    ```bash
    docker-compose -f config/docker/docker-compose.yml exec alembic-runner alembic revision -m "your_migration_message" --autogenerate
    ```
    Remember to review and edit the autogenerated script.

6.  **Stopping Services:**
    ```bash
    docker-compose -f config/docker/docker-compose.yml down
    ```
    To remove volumes (including PostgreSQL data):
    ```bash
    docker-compose -f config/docker/docker-compose.yml down -v
    ```

## Documentation

Detailed documentation can be found in the `/docs` directory, organized by type:

### API Documentation (`docs/api/`)
- API schemas and endpoint documentation

### Deployment Documentation (`docs/deployment/`)
- `deployment.md`: Deployment guides for Docker Compose and Kubernetes
- Deployment checklists and production guides

### Development Documentation (`docs/development/`)
- `developer_guide.md`: Information for developers contributing to the project
- `REORGANIZATION_SUMMARY.md`: Details about the framework reorganization
- Development workflows and contribution guidelines

### Research Documentation (`docs/research/`)
- Academic papers and research content
- Framework design and theoretical foundations

### User Documentation (`docs/user/`)
- `user_guide.md`: How to use the platform (from a user's perspective)
- User tutorials and guides

### Core Documentation
- `docs/architecture.md`: System architecture overview
- `docs/security.md`: Security considerations
- `docs/roadmap.md`: Project development roadmap

## Kubernetes Deployment

For deployment to Kubernetes, refer to the instructions in `config/k8s/README.md`.

## Contributing

Please refer to `docs/development/developer_guide.md` for guidelines on contributing to the project.
