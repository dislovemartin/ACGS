# ACGS-PGP Project Roadmap

This document outlines the planned features and development milestones for the AI Compliance Governance System - Policy Generation Platform (ACGS-PGP).

## Phase 1: Core Platform & MVP (Current Focus)

*   **[DONE] Foundational Directory Structure:** Establish the basic project layout.
*   **[DONE] Core Microservices Shells:**
    *   Authentication Service (`auth_service`)
    *   Audit & Compliance Service (`ac_service`)
    *   Policy Generation & Customization Service (`pgc_service`)
    *   Formal Verification Service (`fv_service`) - Mock/Placeholder
    *   Governance Structure Service (`gs_service`) - Mock/Placeholder
    *   Data Integrity Service (`integrity_service`) - Mock/Placeholder
*   **[DONE] Shared Backend Components:** Database models (`shared/models.py`), Pydantic schemas (`shared/schemas.py`), database connection (`shared/database.py`).
*   **[DONE] Database Setup & Migrations:** PostgreSQL with Alembic for migrations. Initial schema for users, principles, guidelines, audit logs.
*   **[DONE] Frontend Shell:** React application structure, basic routing, placeholder pages.
*   **[DONE] Containerization:** Dockerfiles for all services and frontend.
*   **[DONE] Orchestration (Basic):**
    *   `docker-compose.yml` for local development.
    *   Initial Kubernetes manifests for each service.
*   **[DONE] Basic User Authentication:** User registration (to be added), login, JWT issuance.
*   **[IN PROGRESS] Principles & Guidelines Management (`ac_service`):**
    *   API endpoints to list principles and guidelines.
    *   Frontend pages to display principles and guidelines.
*   **[IN PROGRESS] Policy Generation (`pgc_service` - Mock):**
    *   API endpoint to accept policy requirements and return a mock generated policy.
    *   Frontend page to submit requirements and display generated policy.
*   **[IN PROGRESS] Policy Customization (`pgc_service` - Mock):**
    *   API endpoint to accept customizations for a policy.
    *   Frontend elements to input customizations.
*   **[DONE] Basic CI/CD Pipeline:** GitHub Actions workflow for tests (placeholder) and Docker builds (placeholder).
*   **[DONE] Documentation:**
    *   Initial `README.md` files for services and key directories.
    *   `architecture.md`, `deployment.md`, `developer_guide.md`, `user_guide.md`, `security.md`, `roadmap.md`.

## Phase 2: Enhanced Features & Integrations

*   **User Management & RBAC (`auth_service`):**
    *   Admin panel for user management.
    *   Define and assign roles (e.g., Admin, Policy Creator, Auditor, Viewer).
    *   Implement RBAC across all services.
*   **Real Policy Generation (`pgc_service`):**
    *   Integrate with an actual LLM (e.g., via OpenAI API, Hugging Face Transformers, local Ollama).
    *   Develop sophisticated prompting strategies for policy generation.
    *   Allow selection of principles/guidelines to inform generation.
    *   Implement policy templates.
*   **Advanced Policy Editing & Versioning (`pgc_service`):**
    *   Rich text editor for policy documents.
    *   Track policy versions and history.
    *   Allow comparison between versions.
*   **Formal Verification Integration (`fv_service`):**
    *   Develop concrete integrations with one or more formal verification tools (e.g., TLA+, Proverif, model checkers).
    *   Define a clear process for translating policies/system designs into verifiable models.
    *   API endpoints to submit verification tasks and retrieve results.
    *   Frontend UI to manage verification requests and display results.
*   **Governance Structure Implementation (`gs_service`):**
    *   Develop models and APIs for defining organizational roles, responsibilities, and decision-making workflows related to AI.
    *   Allow mapping of policies to these governance structures.
*   **Enhanced Data Integrity (`integrity_service`):**
    *   Implement mechanisms for data signing or hashing for key artifacts (policies, verification results).
    *   Secure and more detailed audit logging capabilities.
    *   API for querying audit logs with filtering.
*   **Frontend Enhancements:**
    *   Improved UI/UX across all pages.
    *   Interactive dashboards with visualizations.
    *   Notifications system.
*   **Testing Coverage:**
    *   Increase unit, integration, and end-to-end test coverage for all services.
*   **CI/CD Pipeline Improvements:**
    *   Automated deployment to staging environments.
    *   Security scanning (SAST, DAST, dependency checks).

## Phase 3: Production Readiness & Advanced Capabilities

*   **Monitoring & Logging:**
    *   Implement centralized logging (e.g., ELK Stack, Grafana Loki).
    *   Set up monitoring and alerting (e.g., Prometheus, Grafana).
*   **Scalability & Performance Optimization:**
    *   Load testing and performance tuning of services.
    *   Optimize database queries and resource usage.
*   **Advanced Security Hardening:**
    *   Regular penetration testing.
    *   Implement advanced security measures based on audits (e.g., WAF, IDS/IPS).
*   **Compliance Automation & Reporting:**
    *   Tools to help automate compliance checks against policies.
    *   Generate compliance reports.
*   **External System Integrations:**
    *   Integrate with other enterprise systems (e.g., GRC tools, document management systems).
*   **User Feedback & Iteration:**
    *   Gather user feedback from pilot deployments and iterate on features.
*   **Comprehensive Documentation:**
    *   Detailed API documentation (Swagger/OpenAPI).
    *   Updated user and administrator manuals.

## Future Ideas (Beyond Core Roadmap)

*   **AI-Assisted Policy Analysis:** Use NLP to analyze existing policies for gaps or inconsistencies.
*   **Multi-language Support for Policies.**
*   **Support for Different Regulatory Frameworks:** Templates and guidelines specific to GDPR, HIPAA, ISO 27001, etc.
*   **Collaborative Policy Editing Features.**
*   **Risk Management Module Integration.**

This roadmap is a living document and will be updated based on project progress, feedback, and evolving requirements.
