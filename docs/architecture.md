# ACGS-PGP System Architecture

## 1. Overview

The AI Compliance Governance System - Policy Generation Platform (ACGS-PGP) is designed as a microservices-based architecture to ensure modularity, scalability, and maintainability. The system facilitates the creation, management, verification, and audit of AI governance policies.

## 2. Core Components (Microservices)

The system comprises the following core microservices, each running in its own Docker container and managed by Kubernetes:

*   **Authentication Service (`auth_service`):**
    *   Handles user registration, login, and session management.
    *   Issues JWT tokens for authenticating API requests.
    *   Manages user roles and permissions (future enhancement).

*   **Audit & Compliance Service (`ac_service`):**
    *   Manages AI governance principles and guidelines.
    *   Allows users to browse and understand the core tenets of AI governance.
    *   Provides endpoints for retrieving principles and their associated guidelines.

*   **Policy Generation & Customization Service (`pgc_service`):**
    *   Core engine for *evaluating* AI policies based on user requirements, existing templates, and selected principles using its Datalog engine.
    *   Allows users to customize generated policies (customization input is manual in Phase 1).
    *   In Phase 1, PGC Service focuses on evaluating policies using its Datalog engine; advanced policy generation is handled by GS Service.

*   **Formal Verification Service (`fv_service`):**
    *   Integrates with formal verification tools (e.g., TLA+, Z3, custom model checkers) to mathematically verify properties of AI policies or system designs against specifications.
    *   Accepts policy definitions/models and properties to check.
    *   Returns verification results.
    *   Currently, the Formal Verification Service provides a foundational interface (mock implementation). Integration with specific formal verification tools is planned for Phase 2.

*   **Governance Structure Service (`gs_service`):**
    *   Manages the organizational governance structure related to AI.
    *   Defines roles, responsibilities, decision-making processes, and escalation paths.
    *   Helps map policies to accountable parties.
    *   Currently, this service defines the framework for governance structures. LLM-driven policy synthesis and advanced generation capabilities are planned for Phase 2.

*   **Data Integrity Service (`integrity_service`):**
    *   Provides mechanisms for ensuring the integrity of critical data, such as policies, audit logs, and verification results.
    *   May involve cryptographic hashing, digital signatures, or blockchain-based logging.
    *   Manages audit logs from all services.
    *   In its current phase, the Data Integrity Service establishes the groundwork for managing audit logs. Advanced mechanisms like cryptographic hashing/signatures for all artifacts or blockchain logging are future enhancements.

*   **Frontend Service:**
    *   A React-based single-page application (SPA) providing the user interface for interacting with all backend services.
    *   Served via Nginx.

## 3. Data Storage

*   **PostgreSQL Database:**
    *   A central relational database (e.g., PostgreSQL) is used to store:
        *   User credentials (hashed).
        *   AI principles and guidelines.
        *   Generated policies and their versions.
        *   Audit logs.
        *   Governance structure definitions.
        *   Formal verification requests and results.
    *   Each service may have its own schema within this database or access a shared schema as appropriate. Alembic is used for database schema migrations.

## 4. Communication Flow

*   **API Gateway (Conceptual):** While not explicitly implemented as a separate service in the initial setup, in a production environment, an API Gateway (e.g., Kong, Traefik, Nginx Plus) would typically sit in front of the backend microservices. It would handle:
    *   Request routing to the appropriate service.
    *   Load balancing.
    *   Authentication (validating JWT tokens).
    *   Rate limiting.
    *   SSL termination.
    *   For the current setup, the frontend `apiClient` and Docker Compose/Kubernetes service definitions manage direct service communication or routing.

*   **Inter-service Communication:**
    *   Services communicate with each other via RESTful APIs (HTTP/JSON).
    *   Synchronous communication is typical for direct requests.
    *   Asynchronous communication (e.g., via a message queue like RabbitMQ or Kafka) could be introduced for tasks like triggering formal verification or complex policy generation steps to improve responsiveness, but is not part of the initial core design.
    (Future Enhancement: A detailed sequence diagram illustrating key interaction flows will be added in a future update.)

## 5. Technology Stack Summary

*   **Backend:** Python (FastAPI)
*   **Frontend:** JavaScript (React)
*   **Database:** PostgreSQL
*   **Containerization:** Docker
*   **Orchestration:** Kubernetes
*   **Database Migrations:** Alembic
*   **API Specification (Implied):** OpenAPI (FastAPI automatically generates this)

## 6. High-Level Diagram

```
[Client Browser (React Frontend)] <--> [API Gateway (Nginx in K8s Ingress / Docker Compose routing)]
                                    |
                                    +--> [Auth Service] <--> [PostgreSQL]
                                    |
                                    +--> [AC Service] <--> [PostgreSQL]
                                    |
                                    +--> [PGC Service] <--> [PostgreSQL] (+ LLM/External Tools)
                                    |
                                    +--> [FV Service] <--> [PostgreSQL] (+ Formal Verification Tools)
                                    |
                                    +--> [GS Service] <--> [PostgreSQL]
                                    |
                                    +--> [Integrity Service] <--> [PostgreSQL]
```

## 7. Scalability and Availability

*   **Scalability:** Microservices can be scaled independently by increasing the number of replicas in Kubernetes.
*   **Availability:** Kubernetes provides self-healing and rolling updates to ensure high availability. Database replication and failover would be configured for production databases.

## 8. Security Considerations

*   Authentication and Authorization using JWT.
*   HTTPS for all external communication (managed by Ingress or LoadBalancer in K8s).
*   Secrets management for sensitive data (e.g., DB passwords, API keys) using Kubernetes Secrets.
*   Input validation in all services.
*   Regular security audits and dependency scanning.
*   (Refer to `security.md` for more details).

## 9. Future Enhancements

*   **Dedicated API Gateway:** Implement a full-fledged API Gateway.
*   **Message Queue:** Introduce asynchronous communication for long-running tasks.
*   **Service Mesh:** Consider a service mesh (e.g., Istio, Linkerd) for advanced traffic management, observability, and security in inter-service communication.
*   **CI/CD:** Robust CI/CD pipeline for automated testing and deployment (initial setup in GitHub Actions).
*   **Monitoring and Logging:** Centralized logging (e.g., ELK stack, Grafana Loki) and monitoring (e.g., Prometheus, Grafana).
