## ACGS-PGP Codebase Guidelines

**Introduction:**

These guidelines are designed to ensure the ACGS-PGP framework is developed, maintained, and evolved in a consistent, secure, scalable, and robust manner. They are derived from an analysis of the existing codebase, architectural documents (`architecture.md`, `developer_guide.md`, `security.md`, `ACGS-pgp.md`, `AI Governance Compiler.md` OCRs), and deployment configurations (Docker, Kubernetes). Adherence to these guidelines will promote code quality, reduce technical debt, and facilitate collaboration.

---

**A. Core Python (FastAPI) & JavaScript (React) Best Practices**

1.  **Guideline: Consistent Use of Asynchronous Programming in FastAPI.**
    *   **Rationale:** FastAPI is built for asynchronous I/O. Using `async` and `await` correctly for all I/O-bound operations (database calls, external API requests, file operations if any) prevents blocking the event loop, ensuring high concurrency and performance. This aligns with the microservice architecture's need for responsive services.
    *   **Example (Good - from `ac_service/app/api/v1/principles.py`):**
        ```python
        @router.post("/", response_model=schemas.Principle, status_code=status.HTTP_201_CREATED)
        async def create_principle_endpoint(
            principle: schemas.PrincipleCreate,
            db: AsyncSession = Depends(get_async_db), # Async DB session
            current_user: Optional[User] = Depends(require_admin_role)
        ):
            # ...
            created_principle = await crud.create_principle(db=db, principle=principle, user_id=user_id) # await DB operation
            return created_principle
        ```
    *   **Impact if Ignored:** Blocking operations can severely degrade service performance and responsiveness, leading to timeouts and poor user experience.
    *   **Tools/Verification:** Code reviews, static analysis (linters that can detect blocking calls in async functions if available). Ensure all database CRUD functions are `async` and awaited.

2.  **Guideline: Leverage Pydantic for Data Validation and Serialization.**
    *   **Rationale:** Pydantic models (used extensively in `schemas.py` files) provide automatic request/response data validation, serialization, and documentation (for OpenAPI). This reduces boilerplate, improves security by preventing invalid data, and enhances developer experience.
    *   **Example (Good - from `auth_service/app/schemas/user.py`):**
        ```python
        class UserCreate(UserBase):
            password: str = Field(..., min_length=8) # Example validation
            email: EmailStr # Built-in Pydantic type for email validation
        ```
    *   **Impact if Ignored:** Increased risk of invalid data, security vulnerabilities (e.g., injection if not properly validated elsewhere), more verbose and error-prone manual validation code.
    *   **Tools/Verification:** FastAPI automatically integrates Pydantic. Code reviews to ensure comprehensive models for all API DTOs.

3.  **Guideline: Use FastAPI's Dependency Injection for Reusable Logic and Resource Management.**
    *   **Rationale:** Dependency Injection (DI) (e.g., `Depends(get_async_db)`, `Depends(require_admin_role)`) promotes cleaner, more testable code by decoupling components. It's ideal for managing database sessions, authentication/authorization, and other shared resources.
    *   **Impact if Ignored:** Tightly coupled code, harder to test, boilerplate code for resource management in every endpoint.
    *   **Tools/Verification:** Code reviews. Ensure common logic like DB session management and auth checks are implemented as dependencies.

4.  **Guideline: Consistent Use of Functional Components and Hooks in React.**
    *   **Rationale:** The frontend (`frontend/`) is based on Create React App. Modern React development favors functional components and hooks (`useState`, `useEffect`, `useContext`) for managing state and side effects, leading to more readable and maintainable code.
    *   **Impact if Ignored:** Inconsistent coding styles, potential for legacy class component patterns making the codebase harder to understand and maintain for new developers.
    *   **Tools/Verification:** ESLint with React plugins, code reviews.

5.  **Guideline: Type Hinting in Python.**
    *   **Rationale:** Python type hints improve code readability, help catch type-related errors early (with tools like MyPy), and enhance IDE support. FastAPI leverages them extensively.
    *   **Example (Good - from `shared/database.py`):**
        ```python
        async def get_async_db() -> AsyncSession: # Return type hint
            async with AsyncSessionLocal() as session:
                # ...
        ```
    *   **Impact if Ignored:** Reduced code clarity, harder to refactor, potential for runtime type errors.
    *   **Tools/Verification:** MyPy, Pylance/Pyright in IDEs. Aim for comprehensive type coverage.

---

**B. Architecture & Design Patterns**

1.  **Guideline: Adhere to Microservice Principles and Clear Service Boundaries.**
    *   **Rationale:** The system is designed as microservices (`auth_service`, `ac_service`, etc.) for modularity and scalability. Each service should have a single, well-defined responsibility and communicate via explicit APIs. This aligns with the "Core Components" section in `architecture.md`.
    *   **Impact if Ignored:** Monolithic tendencies, tight coupling reducing deployability and scalability, increased complexity in understanding and maintaining the system.
    *   **Tools/Verification:** Architectural reviews. Ensure services do not directly access each other's databases. Communication should occur via defined REST APIs (as seen with `*_client.py` files).

2.  **Guideline: Stateless Services Where Possible.**
    *   **Rationale:** Stateless services are easier to scale horizontally, test, and manage. State should be managed in dedicated persistence layers (PostgreSQL) or caches.
    *   **Impact if Ignored:** Scalability issues, complexity in managing session affinity if state is held in service instances.
    *   **Tools/Verification:** Code reviews. Avoid storing session-specific state in service instance variables.

3.  **Guideline: Consistent API Design Across Services.**
    *   **Rationale:** Uniform API design (URL structure, HTTP methods, request/response formats, error handling) improves developer experience, simplifies client-side integration, and makes the system easier to understand and debug. FastAPI helps with response/request formats via Pydantic.
    *   **Example:** All services use `/api/v1/` prefix for their endpoints. Resource naming should be consistent (e.g., plural nouns for collections).
    *   **Impact if Ignored:** Increased integration complexity, inconsistent client-side handling, harder to learn and use the APIs.
    *   **Tools/Verification:** API design reviews. Use shared Pydantic models for common DTOs if applicable (though service-specific schemas are generally good for decoupling).

4.  **Guideline: Centralized Identity and Access Management (IAM).**
    *   **Rationale:** The `auth_service` handles authentication. Role-Based Access Control (RBAC) logic, while currently somewhat distributed in placeholder `core/auth.py` files, should ideally be managed or defined centrally, with `auth_service` being the authority for user roles and permissions. JWTs are used for API authentication.
    *   **Impact if Ignored:** Inconsistent authorization logic, security vulnerabilities, difficulty in managing user permissions globally.
    *   **Tools/Verification:** Review `auth_service` implementation and how other services consume JWTs and perform authorization. Consolidate role/permission definitions.

---

**C. Concurrency (Asyncio in FastAPI)**

1.  **Guideline: Prefer `async def` for all I/O-Bound Operations in FastAPI Endpoints.**
    *   **Rationale:** As stated in A1, this is crucial for FastAPI's performance model. All database interactions (`crud.py` functions) and inter-service HTTP calls (`*_client.py` files) are correctly `async`.
    *   **Impact if Ignored:** Performance bottlenecks, reduced throughput.
    *   **Tools/Verification:** Code reviews. Ensure no synchronous blocking calls exist in `async def` functions.

2.  **Guideline: Use BackgroundTasks for Long-Running, Non-Blocking Operations.**
    *   **Rationale:** For tasks that don't need to complete before returning a response to the client (e.g., sending an email, triggering a lengthy verification process as hinted in `gs_service/app/api/v1/synthesize.py`), use FastAPI's `BackgroundTasks`.
    *   **Example (Conceptual, from `gs_service/app/api/v1/synthesize.py`):**
        ```python
        background_tasks.add_task(
            integrity_client.integrity_service_client.record_synthesis_event,
            # ...
        )
        background_tasks.add_task(
            fv_client.fv_service_client.request_verification_of_rules,
            # ...
        )
        return gs_schemas.SynthesisResponse(
            message="Synthesis process initiated...", # Return immediately
            # ...
        )
        ```
    *   **Impact if Ignored:** Long response times for clients if such tasks are performed synchronously within the request-response cycle.
    *   **Tools/Verification:** Code reviews for endpoints that might trigger long operations.

---

**D. Datastore Usage (PostgreSQL, SQLAlchemy, Alembic)**

1.  **Guideline: Use Alembic for All Database Schema Migrations.**
    *   **Rationale:** Alembic (`db/migrations/`) provides robust, version-controlled schema migration capabilities. This is essential for evolving the database schema in a consistent and manageable way across different environments.
    *   **Impact if Ignored:** Inconsistent database schemas across environments, difficulty in deploying updates, potential data loss or corruption.
    *   **Tools/Verification:** Ensure all schema changes are accompanied by an Alembic migration script. Review auto-generated scripts carefully.

2.  **Guideline: Define Clear Relationships and Constraints in SQLAlchemy Models.**
    *   **Rationale:** SQLAlchemy models in `shared/models.py` should accurately reflect database relationships (one-to-one, one-to-many, many-to-many) using `relationship()` and enforce data integrity using `ForeignKey`, `nullable=False`, `unique=True`, etc.
    *   **Example (Good - from `shared/models.py`):**
        ```python
        class User(Base):
            # ...
            refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

        class RefreshToken(Base):
            # ...
            user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
            user = relationship("User", back_populates="refresh_tokens")
        ```
    *   **Impact if Ignored:** Data integrity issues, orphaned records, inefficient queries if relationships are not well-defined.
    *   **Tools/Verification:** Code reviews of models. Database diagramming tools.

3.  **Guideline: Optimize Database Queries.**
    *   **Rationale:** Inefficient queries can be a major performance bottleneck. Use SQLAlchemy efficiently: select only necessary columns, use `joinedload` or `selectinload` for eager loading of related data to avoid N+1 query problems, and add database indexes for frequently queried columns.
    *   **Example (Conceptual for eager loading):**
        ```python
        # Instead of:
        # result = await db.execute(select(models.Principle))
        # principles = result.scalars().all()
        # for p in principles: _ = p.created_by # N+1 if created_by is lazy loaded and accessed in loop

        # Consider:
        # from sqlalchemy.orm import joinedload
        # result = await db.execute(select(models.Principle).options(joinedload(models.Principle.created_by)))
        # principles = result.scalars().all()
        ```
    *   **Impact if Ignored:** Slow API responses, high database load.
    *   **Tools/Verification:** Query analysis tools (e.g., `EXPLAIN` in PostgreSQL), performance profiling. Review CRUD operations for N+1 patterns. Ensure indexes are present (e.g., on `PolicyRule.verification_status`, `AuditLog.timestamp`, `AuditLog.service_name`).

4.  **Guideline: Implement Data Encryption at Rest for PostgreSQL.**
    *   **Rationale:** While not directly in application code, the PostgreSQL database stores sensitive information (user data, policies). Encryption at rest (e.g., using cloud provider features or PostgreSQL's own capabilities like `pgcrypto` for column-level encryption if needed, or full disk encryption) is crucial for data security.
    *   **Impact if Ignored:** Data breaches can expose sensitive information if underlying storage is compromised.
    *   **Tools/Verification:** Infrastructure review, cloud provider configuration checks.

---

**E. Performance Optimization**

1.  **Guideline: Implement Rate Limiting on Public/Sensitive API Endpoints.**
    *   **Rationale:** Protects services from abuse, DoS attacks, and excessive load. The `auth_service` uses `slowapi` which is good. This should be considered for other services with public-facing or resource-intensive endpoints.
    *   **Example (from `auth_service/app/api/endpoints.py`):**
        ```python
        @router.post("/token")
        @limiter.limit("5/minute") # Apply rate limit
        async def login_for_access_token(...):
            # ...
        ```
    *   **Impact if Ignored:** Services vulnerable to DoS, performance degradation under high load from a few clients.
    *   **Tools/Verification:** Code review. Identify critical endpoints and apply appropriate limits.

2.  **Guideline: Use Caching for Frequently Accessed, Rarely Changed Data.**
    *   **Rationale:** Reduces load on services and databases. For example, `ac_service` principles might be good candidates for caching if they don't change often. The `PolicyManager` in `pgc_service` implements a refresh interval for rules, which is a form of caching.
    *   **Impact if Ignored:** Unnecessary load on backend services and database, slower response times.
    *   **Tools/Verification:** Identify read-heavy, rarely updated data. Consider libraries like `fastapi-cache` or Redis for distributed caching.

3.  **Guideline: Profile and Monitor Application Performance.**
    *   **Rationale:** Regularly profile applications to identify bottlenecks (CPU, I/O, memory). Implement comprehensive monitoring and telemetry (see Section J).
    *   **Impact if Ignored:** Performance issues may go unnoticed until they become critical.
    *   **Tools/Verification:** Profilers (e.g., `cProfile`, `Pyinstrument`), APM tools (Prometheus, Grafana, OpenTelemetry).

---

**F. Security**

1.  **Guideline: Secure Management of Secrets.**
    *   **Rationale:** API keys, database credentials, JWT `SECRET_KEY`, `CSRF_SECRET_KEY` must never be hardcoded. Use environment variables, `.env` files (ignored by Git) for local development, and Kubernetes Secrets for production deployments (as indicated in `k8s/README.md`).
    *   **Impact if Ignored:** High risk of credential leakage, leading to unauthorized access and system compromise.
    *   **Tools/Verification:** Code scanning for hardcoded secrets. Review K8s secret configurations.

2.  **Guideline: Enforce HTTPS for All External Communication.**
    *   **Rationale:** Protects data in transit from eavesdropping and tampering. This is mentioned as managed by Ingress/LoadBalancer in K8s (`security.md`).
    *   **Impact if Ignored:** Sensitive data (including JWTs if not in cookies, user credentials) can be intercepted.
    *   **Tools/Verification:** Infrastructure configuration review.

3.  **Guideline: Implement Robust CSRF Protection for Cookie-Based Authentication.**
    *   **Rationale:** Since `auth_service` uses cookies for session management, CSRF protection is vital. `fastapi-csrf-protect` is used, which is good. Ensure frontend correctly sends the CSRF token in headers for state-changing requests.
    *   **Impact if Ignored:** Users vulnerable to CSRF attacks, allowing attackers to perform actions on their behalf.
    *   **Tools/Verification:** Security testing. Review frontend API client to ensure `X-CSRF-Token` header is sent.

4.  **Guideline: Input Validation at API Boundaries.**
    *   **Rationale:** Pydantic models (A2) handle this for request bodies. Ensure path parameters and query parameters are also validated if they influence critical logic or database queries.
    *   **Impact if Ignored:** Potential for injection attacks, unexpected errors, or crashes.
    *   **Tools/Verification:** Code reviews.

5.  **Guideline: Regular Dependency Scanning and Updates.**
    *   **Rationale:** Outdated dependencies can contain known vulnerabilities. Use tools to scan `requirements.txt` and `package.json` and update dependencies regularly. `SECURITY.md` mentions this.
    *   **Impact if Ignored:** System vulnerable to exploits targeting known flaws in third-party libraries.
    *   **Tools/Verification:** `pip-audit`, `npm audit`, GitHub Dependabot, Snyk.

6.  **Guideline: Adhere to the Principle of Least Privilege for Service Accounts and User Roles.**
    *   **Rationale:** Services and users should only have the permissions necessary to perform their functions. This minimizes the potential damage if an account or service is compromised.
    *   **Impact if Ignored:** A compromised account/service with excessive privileges can lead to a wider system breach.
    *   **Tools/Verification:** Review RBAC configurations (Section B4). Review K8s service account permissions.

7.  **Guideline: Secure Inter-Service Communication within Kubernetes.**
    *   **Rationale:** While internal, inter-service communication can be a target. Use Kubernetes NetworkPolicies to restrict traffic. Consider mTLS via a service mesh (Istio, Linkerd) for sensitive services, as mentioned in `architecture.md` (Future Enhancements).
    *   **Impact if Ignored:** Potential for lateral movement by attackers if one service is compromised.
    *   **Tools/Verification:** Kubernetes NetworkPolicy review.

---

**G. Testing**

1.  **Guideline: Comprehensive Test Coverage (Unit, Integration, E2E).**
    *   **Rationale:** Ensures code quality, reduces regressions, and validates functionality. The `auth_service` has good examples of integration tests. This needs to be extended to all services.
    *   **Impact if Ignored:** Higher bug rates, regressions, difficulty in refactoring, lower confidence in deployments.
    *   **Tools/Verification:** `pytest` for backend, Jest/RTL for frontend. Code coverage tools (e.g., `pytest-cov`). Aim for >80-90% coverage on critical paths.

2.  **Guideline: Write Testable Code.**
    *   **Rationale:** Design code (especially business logic) to be easily testable in isolation. Use dependency injection, pure functions where possible.
    *   **Impact if Ignored:** Difficult and brittle tests, low test coverage.
    *   **Tools/Verification:** Code reviews focusing on testability.

3.  **Guideline: Database State Management for Tests.**
    *   **Rationale:** Integration tests interacting with the database need a clean, predictable state. The `auth_service/app/tests/conftest.py` sets up a test database and uses transaction rollbacks or table recreation, which is good practice.
    *   **Impact if Ignored:** Flaky tests, tests interfering with each other.
    *   **Tools/Verification:** Review `conftest.py` and test setup for other services.

---

**H. Code Style & Documentation**

1.  **Guideline: Consistent Code Formatting and Linting.**
    *   **Rationale:** Improves readability and maintainability, reduces cognitive load when switching between files/services.
    *   **Python**: Black for formatting, Flake8 for linting.
    *   **JavaScript**: Prettier for formatting, ESLint for linting.
    *   **Impact if Ignored:** Inconsistent code, harder to read and review.
    *   **Tools/Verification:** Pre-commit hooks, CI checks for formatting and linting.

2.  **Guideline: Comprehensive Code Documentation (Docstrings, Comments).**
    *   **Rationale:** Explains complex logic, API usage, and design decisions. Python docstrings (e.g., Google, NumPy, or Sphinx style) for modules, classes, functions. JSDoc for React components and functions.
    *   **Impact if Ignored:** Code becomes difficult to understand, maintain, and onboard new developers.
    *   **Tools/Verification:** Code reviews. Docstring coverage tools.

3.  **Guideline: Maintain Up-to-Date Project Documentation.**
    *   **Rationale:** `README.md` files at project and service levels, `docs/` directory for architecture, deployment, developer guides are crucial. Keep them current as the system evolves. The existing `docs/` structure is a good start.
    *   **Impact if Ignored:** Outdated information leads to confusion, errors, and slower development.
    *   **Tools/Verification:** Documentation reviews as part of PR process.

4.  **Guideline: Clear Naming Conventions.**
    *   **Rationale:** Use descriptive and consistent names for variables, functions, classes, modules, and services. Follow Python's PEP 8 and common JavaScript conventions.
    *   **Impact if Ignored:** Code becomes harder to understand.
    *   **Tools/Verification:** Code reviews, linters.

---

**I. Dependency Management (pip, npm)**

1.  **Guideline: Pin Dependency Versions.**
    *   **Rationale:** Use `requirements.txt` (Python) and `package-lock.json` (Node.js) to pin exact dependency versions. This ensures reproducible builds and avoids unexpected breaking changes from transitive dependencies.
    *   **Impact if Ignored:** Builds can break unpredictably, different developers/environments might have different behavior.
    *   **Tools/Verification:** `pip freeze > requirements.txt`. `npm ci` uses `package-lock.json`.

2.  **Guideline: Regularly Update Dependencies and Manage Breaking Changes.**
    *   **Rationale:** While pinning is important, dependencies should be updated periodically to get security patches and new features. Do this in a controlled manner, testing thoroughly.
    *   **Impact if Ignored:** Accumulation of technical debt, missed security updates.
    *   **Tools/Verification:** Dependabot, manual review of changelogs.

---

**J. Error Handling & Logging**

1.  **Guideline: Consistent and Structured Error Handling.**
    *   **Rationale:** FastAPI services should return consistent JSON error responses with appropriate HTTP status codes. Use `HTTPException` for this. Gracefully handle exceptions within services.
    *   **Impact if Ignored:** Inconsistent client-side error handling, difficult to debug issues.
    *   **Tools/Verification:** Code reviews. Define standard error response schemas if needed.

2.  **Guideline: Implement Structured and Centralized Logging.**
    *   **Rationale:** Essential for observability, debugging, and auditing.
        *   **Structured Logging**: Log in JSON format for easier parsing and analysis by log management systems. Include contextual information (e.g., request ID, user ID, service name).
        *   **Centralized Logging**: Ship logs from all services to a central platform (e.g., ELK Stack, Grafana Loki, cloud provider logging services) as suggested in `architecture.md` (Future Enhancements).
    *   **Example (Conceptual Python):**
        ```python
        import logging
        logger = logging.getLogger(__name__)
        # Configure logger to output JSON
        # ...
        logger.info({"event": "user_login", "user_id": user.id, "status": "success"})
        ```
    *   **Impact if Ignored:** Difficult to trace issues across services, troubleshoot production problems, or perform security audits.
    *   **Tools/Verification:** Review logging implementation. Ensure logs are shipped to a central system in production.

3.  **Guideline: Use Correlation IDs for Tracing Requests Across Services.**
    *   **Rationale:** In a microservice architecture, a single user request might involve multiple services. A unique correlation ID (passed via headers) allows tracing the entire lifecycle of a request across these services in logs.
    *   **Impact if Ignored:** Extremely difficult to debug issues that span multiple services.
    *   **Tools/Verification:** Implement middleware to generate/propagate correlation IDs. Logging should include this ID. OpenTelemetry can help manage this.

---

**K. Service-Specific Considerations**

1.  **Guideline (`auth_service`): Secure JWT and CSRF Secret Management.**
    *   **Rationale:** The `SECRET_KEY` for JWTs and `CSRF_SECRET_KEY` are highly sensitive. Their compromise would break authentication and CSRF protection. They are correctly loaded from environment variables.
    *   **Impact if Ignored:** System-wide security breach.
    *   **Tools/Verification:** Ensure these are never hardcoded and are managed via K8s Secrets in production.

2.  **Guideline (`auth_service`): Persistent Storage for Access Token JTI Revocation List.**
    *   **Rationale:** The current `revoked_access_jti_blacklist` in `auth_service/app/core/security.py` is in-memory. For production, this list needs to be persisted (e.g., Redis, database table) to survive service restarts and be shared across multiple instances if scaled.
    *   **Impact if Ignored:** Logout/revocation effectiveness is limited; revoked tokens might still be usable after a restart or on other instances.
    *   **Tools/Verification:** Architectural review. Implement persistent JTI blacklist.

3.  **Guideline (`gs_service`, `fv_service`): Manage Complexity of External Tool Integration.**
    *   **Rationale:** These services integrate with LLMs and SMT solvers (currently mocked). Real integrations will involve network calls, specific data formats, and error handling. Design these integrations to be resilient and configurable.
    *   **Impact if Ignored:** Unreliable synthesis or verification processes, tight coupling to specific external tool versions.
    *   **Tools/Verification:** Design reviews for external integrations. Use client libraries with good error handling and retry mechanisms.

4.  **Guideline (`integrity_service`): Ensure Tamper-Evident Audit Logging.**
    *   **Rationale:** Audit logs are critical for compliance and security. Consider techniques like cryptographic hashing of log entries or chaining if high integrity is required, as suggested in the roadmap for Phase 2.
    *   **Impact if Ignored:** Audit logs might be susceptible to tampering, reducing their reliability.
    *   **Tools/Verification:** Review audit log storage and access controls.

5.  **Guideline (`pgc_service`): Performance of Datalog Engine.**
    *   **Rationale:** The `pgc_service` uses `pyDatalog` for runtime policy evaluation. Its performance under high load with complex rulesets needs to be monitored and potentially optimized. The roadmap mentions evaluating alternatives if needed.
    *   **Impact if Ignored:** High latency in policy enforcement, impacting application performance.
    *   **Tools/Verification:** Load testing `pgc_service`. Profiling Datalog query execution.

