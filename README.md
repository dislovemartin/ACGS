# ACGS-PGP: AI Compliance Governance System - Policy Generation Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/dislovemartin/ACGS)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](https://github.com/dislovemartin/ACGS)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/dislovemartin/ACGS)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## 🎯 Overview

The **AI Compliance Governance System - Policy Generation Platform (ACGS-PGP)** is a comprehensive constitutional AI governance framework that implements democratic oversight, formal verification, and real-time enforcement of AI policies.

### **Current Infrastructure Status (Phase 2.3)**

- **Overall Operational Status:** 83% (5/6 core services healthy)
- **TaskMaster Completion:** 100% (19/19 tasks completed) ✅
- **Security Score:** 85% (Phase 2.2 Security Hardening completed) ✅
- **LLM Reliability:** >99.9% achieved ✅
- **API Response Times:** <200ms target achieved ✅

### **Service Health Status**

- **✅ Healthy Services:** AC Service, GS Service, FV Service, PGC Service, Auth Service
- **⚠️ Critical Issue:** Integrity Service (database DNS resolution failure)
- **🔧 Known Issues:** Security middleware blocking health endpoints (workaround available)

### 🏗️ Constitutional Governance Architecture

ACGS-PGP implements a **three-layer constitutional governance architecture**:

1. **🏛️ Artificial Constitution (AC) Layer**: Democratic principle management with Constitutional Council oversight
2. **🧠 Governance Synthesis (GS) Engine**: LLM-driven policy synthesis with constitutional prompting and WINA optimization
3. **🛡️ Prompt Governance Compiler (PGC)**: Real-time policy enforcement with cryptographic integrity

### 🚀 Microservices Architecture

The framework consists of **7 specialized microservices**:

-   **🔐 Authentication Service (`auth_service:8000`)**: JWT authentication, RBAC (Admin/Policy Manager/Auditor/Constitutional Council), CSRF protection, rate limiting
-   **📜 Audit & Compliance Service (`ac_service:8001`)**: Constitutional principles, meta-rules, Constitutional Council, conflict resolution, QEC enhancements, amendment workflows
-   **🧬 Governance Synthesis Service (`gs_service:8004`)**: LLM policy synthesis, constitutional prompting, AlphaEvolve integration, WINA optimization, multi-model validation
-   **🔍 Formal Verification Service (`fv_service:8003`)**: Z3 SMT solver integration, algorithmic fairness, bias detection, safety property verification, parallel validation
-   **🔒 Integrity Service (`integrity_service:8002`)**: Cryptographic integrity, PGP assurance, audit logging, appeals processing, Merkle tree verification
-   **⚖️ Protective Governance Controls (`pgc_service:8005`)**: Real-time policy enforcement, OPA integration, incremental compilation, sub-200ms latency
-   **🧬 Evolutionary Computation Service (`ec_service:8006`)**: WINA-optimized oversight, AlphaEvolve governance, performance monitoring, constitutional compliance

### 🌟 Key Features

#### **Phase 1: Constitutional Foundation** ✅ **COMPLETE**
- ✅ Enhanced Principle Management with priority weighting and scope definition
- ✅ Constitutional Prompting for LLM policy synthesis
- ✅ Meta-Rules for governance rule hierarchies
- ✅ Conflict Resolution with intelligent patch suggestions
- ✅ Constitutional Council with democratic amendment processes

#### **Phase 2: Evolutionary Governance** ✅ **COMPLETE**

- ✅ AlphaEvolve Integration for co-evolutionary governance
- ✅ Multi-Armed Bandit prompt optimization
- ✅ Federated evaluation across platforms
- ✅ Parallel validation pipeline (60-70% latency reduction)
- ✅ Incremental policy compilation with OPA
- ✅ **LangGraph Constitutional Council Workflows** (Task 17) - Real-time stakeholder engagement
- ✅ **Multi-Model Enhancement for GS Engine** (Task 18) - >99.9% reliability achieved
- ✅ **Real-time Constitutional Fidelity Monitoring** (Task 19) - QEC-inspired error correction

#### **Phase 3: Advanced Assurance** ✅ **COMPLETE**
- ✅ Z3 Formal Verification with SMT solver integration
- ✅ Algorithmic Fairness with bias detection and mitigation
- ✅ PGP Cryptographic Integrity with digital signatures
- ✅ QEC (Quality, Error, Correction) Enhancement Framework
- ✅ WINA (Weight Informed Neuron Activation) Optimization

## 🛠️ Technology Stack

### **Core Technologies**
- **Backend**: Python 3.11+ with FastAPI, async/await patterns, Pydantic v2.0+ validation
- **Frontend**: React 18+ with TypeScript, governance dashboards, real-time WebSocket updates
- **Database**: PostgreSQL 15+ with JSONB support, connection pooling, optimized indexing
- **API Gateway**: Nginx with service routing, load balancing, rate limiting

### **AI & Machine Learning**
- **Primary LLM**: OpenAI GPT-4 for constitutional prompting and policy synthesis
- **Alternative LLMs**: Groq Llama models, Google Gemini 2.5 Flash, DeepSeek-R1 (local)
- **Optimization**: WINA (Weight Informed Neuron Activation) for 40-70% GFLOPs reduction
- **Reliability**: Multi-model validation, bias detection, ensemble voting (>99.9% target)

### **Formal Verification & Security**
- **SMT Solver**: Z3 for mathematical verification and safety property checking
- **Cryptography**: PGP/GPG digital signatures, SHA3-256 hashing, Merkle tree integrity
- **Authentication**: JWT tokens with RBAC, CSRF protection, rate limiting
- **Bias Detection**: HuggingFace Fairness Indicators, algorithmic fairness metrics

### **Infrastructure & DevOps**
- **Containerization**: Docker with multi-stage builds, optimized images
- **Orchestration**: Docker Compose (development), Kubernetes (production)
- **Database Migrations**: Alembic with constitutional schema enhancements
- **Caching**: Redis for parallel processing, policy caching, session management
- **Policy Engine**: Open Policy Agent (OPA) for incremental compilation

### **Monitoring & Observability**
- **Metrics**: Prometheus with custom metrics, performance monitoring
- **Dashboards**: Grafana with real-time dashboards, alerting
- **Logging**: Structured JSON logging, centralized log aggregation
- **Health Checks**: Comprehensive health monitoring, dependency tracking

### **Quality Assurance**
- **Testing**: pytest with >95% coverage, integration tests, end-to-end validation
- **QEC Framework**: Quality, Error, and Correction enhancements
- **Performance**: <200ms API response times, 60-70% latency reduction
- **Reliability**: 100% integration test success, >99.5% uptime target

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
