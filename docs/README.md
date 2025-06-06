# ACGS-PGP Documentation

This directory contains detailed documentation for the ACGS-PGP (Artificial Constitutionalism: Self-Synthesizing Prompt Governance Compiler) framework and the AlphaEvolve-ACGS Integration System. Below is a guide to the documents available:

-   **`README.md`**: You are here! This file provides an overview of the documentation structure within the `docs/` directory.
-   **`architecture.md`**: Describes the overall system architecture of ACGS-PGP, including its microservices, data storage solutions, communication flows, and the core technology stack. Essential for understanding how the various components interact.
-   **`data_models.md`**: Details the core data models (SQLAlchemy classes in `shared/models.py`) used throughout the ACGS-PGP system, such as User, Policy, Principle, and AuditLog. Crucial for developers working with the database and APIs.
-   **`deployment.md`**: Provides instructions for deploying the ACGS-PGP system using Docker Compose for local development/testing and Kubernetes for staging/production environments.
-   **`developer_guide.md`**: A comprehensive guide for developers contributing to the project. It covers initial setup, development workflow (backend/frontend), coding guidelines, API design, inter-service communication patterns, the contribution process, and debugging/troubleshooting tips.
-   **`research_overview.md`**: Offers a consolidated view of the research contributions and theoretical underpinnings of the ACGS-PGP framework and the AlphaEvolve-ACGS Integration System, with links to key research papers and related project resources.
-   **`roadmap.md`**: Outlines the project's development phases, planned features, current progress, and future milestones for the ACGS-PGP system.
-   **`security.md`**: Discusses security considerations, best practices, potential threats, and measures implemented or planned to ensure the security of the ACGS-PGP system.
-   **`user_guide.md`**: Explains how to use the ACGS-PGP platform from an end-user's perspective, covering its features, functionalities, and user interface interactions.

## Microservice Guides

Each backend service has its own README with setup details and API overviews:

- **ac_service**: [README](../src/backend/ac_service/README.md)
- **auth_service**: [README](../src/backend/auth_service/README.md)
- **ec_service**: [README](../src/backend/ec_service/README.md)
- **federated_service**: [README](../src/backend/federated_service/README.md)
- **fv_service**: [README](../src/backend/fv_service/README.md)
- **gs_service**: [README](../src/backend/gs_service/README.md)
- **integrity_service**: [README](../src/backend/integrity_service/README.md)
- **monitoring**: [README](../src/backend/monitoring/README.md)
- **pgc_service**: [README](../src/backend/pgc_service/README.md)
- **research_service**: [README](../src/backend/research_service/README.md)
- **shared**: [README](../src/backend/shared/README.md)
- **workflow_service**: [README](../src/backend/workflow_service/README.md)

Please refer to the main project [README.md](../README.md) for general project information and setup instructions.
