## ACGS-PGP Codebase Guidelines

**Introduction:**

These guidelines ensure the ACGS-PGP framework is developed and maintained consistently, securely, and robustly. Adherence promotes code quality, reduces technical debt, and facilitates collaboration.

---

**A. Core Python (FastAPI) & JavaScript (React) Best Practices**

1.  **Guideline: Consistent Use of Asynchronous Programming in FastAPI.**
    *   **Rationale:** FastAPI requires `async`/`await` for all I/O-bound operations (database calls, external APIs) to prevent blocking and ensure high concurrency.
    *   **Example:**
        ```python
        async def create_principle_endpoint(
            principle: schemas.PrincipleCreate,
            db: AsyncSession = Depends(get_async_db),
            current_user: Optional[User] = Depends(require_admin_role)
        ):
            created_principle = await crud.create_principle(db=db, principle=principle, user_id=user_id)
            return created_principle
        ```
    *   **Impact if Ignored:** Performance degradation, timeouts, poor user experience.

2.  **Guideline: Leverage Pydantic for Data Validation and Serialization.**
    *   **Rationale:** Pydantic models provide automatic validation, serialization, and API documentation while improving security.
    *   **Impact if Ignored:** Security vulnerabilities, verbose manual validation code.

3.  **Guideline: Use FastAPI's Dependency Injection for Reusable Logic.**
    *   **Rationale:** DI (e.g., `Depends(get_async_db)`) promotes cleaner, testable code by decoupling components.
    *   **Impact if Ignored:** Tightly coupled code, harder to test.

4.  **Guideline: Use Functional Components and Hooks in React.**
    *   **Rationale:** Modern React favors functional components and hooks for better maintainability.
    *   **Impact if Ignored:** Inconsistent coding styles, harder maintenance.

5.  **Guideline: Type Hinting in Python.**
    *   **Rationale:** Type hints improve readability, catch errors early, and enhance IDE support.
    *   **Impact if Ignored:** Reduced clarity, harder refactoring, runtime errors.

---

**B. Architecture & Design Patterns**

1.  **Guideline: Adhere to Microservice Principles and Stateless Design.**
    *   **Rationale:** Each service should have single responsibility, communicate via APIs, and remain stateless for scalability. State belongs in persistence layers (PostgreSQL) or caches.
    *   **Impact if Ignored:** Monolithic tendencies, tight coupling, scalability issues.

2.  **Guideline: Consistent API Design Across Services.**
    *   **Rationale:** Uniform API design (URL structure, HTTP methods, error handling) improves developer experience and simplifies integration.
    *   **Example:** All services use `/api/v1/` prefix. Use consistent resource naming.
    *   **Impact if Ignored:** Integration complexity, inconsistent client handling.

3.  **Guideline: Centralized Identity and Access Management (IAM).**
    *   **Rationale:** The `auth_service` handles authentication and should be the authority for RBAC. JWTs are used for API authentication.
    *   **Impact if Ignored:** Inconsistent authorization, security vulnerabilities.

---

**C. Concurrency (Asyncio in FastAPI)**

1.  **Guideline: Prefer `async def` for all I/O-Bound Operations.**
    *   **Rationale:** Crucial for FastAPI's performance model. All database and inter-service calls should be `async`.
    *   **Impact if Ignored:** Performance bottlenecks, reduced throughput.

2.  **Guideline: Use BackgroundTasks for Long-Running Operations.**
    *   **Rationale:** For tasks that don't need to complete before returning a response, use FastAPI's `BackgroundTasks`.
    *   **Impact if Ignored:** Long response times for clients.

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

3.  **Guideline: Optimize Database Queries and Implement Encryption.**
    *   **Rationale:** Use SQLAlchemy efficiently with eager loading to avoid N+1 queries. Add indexes for frequently queried columns. Implement encryption at rest for sensitive data.
    *   **Impact if Ignored:** Slow API responses, high database load, data breach risks.

---

**E. Performance Optimization**

1.  **Guideline: Implement Rate Limiting, Caching, and Performance Monitoring.**
    *   **Rationale:** Protect services from abuse with rate limiting. Use caching for frequently accessed data. Regularly profile and monitor applications.
    *   **Impact if Ignored:** DoS vulnerabilities, unnecessary database load, unnoticed performance issues.

---

**F. Security**

1.  **Guideline: Secure Management of Secrets and Communications.**
    *   **Rationale:** Never hardcode secrets. Use environment variables and Kubernetes Secrets. Enforce HTTPS for external communication. Implement CSRF protection for cookie-based auth.
    *   **Impact if Ignored:** Credential leakage, data interception, CSRF attacks.

2.  **Guideline: Input Validation and Dependency Management.**
    *   **Rationale:** Validate all API inputs. Regularly scan and update dependencies to patch vulnerabilities.
    *   **Impact if Ignored:** Injection attacks, exploitation of known vulnerabilities.

3.  **Guideline: Principle of Least Privilege and Network Security.**
    *   **Rationale:** Grant minimal necessary permissions. Use NetworkPolicies to restrict inter-service communication.
    *   **Impact if Ignored:** Wider system breach if compromised, lateral movement attacks.

---

**G. Testing**

1.  **Guideline: Comprehensive Test Coverage and Testable Code Design.**
    *   **Rationale:** Ensure quality with unit, integration, and E2E tests. Design code for testability using dependency injection. Manage database state properly for integration tests.
    *   **Impact if Ignored:** Higher bug rates, regressions, flaky tests.

---

**H. Code Style & Documentation**

1.  **Guideline: Consistent Code Style, Documentation, and Naming.**
    *   **Rationale:** Use consistent formatting (Black/Prettier), comprehensive documentation (docstrings/JSDoc), and clear naming conventions. Maintain up-to-date project documentation.
    *   **Impact if Ignored:** Inconsistent code, harder to understand and maintain.

---

**I. Dependency Management (pip, npm)**

1.  **Guideline: Pin Dependency Versions and Regular Updates.**
    *   **Rationale:** Pin exact versions for reproducible builds. Update dependencies periodically for security patches while testing thoroughly.
    *   **Impact if Ignored:** Unpredictable builds, missed security updates.

---

**J. Error Handling & Logging**

1.  **Guideline: Consistent Error Handling and Structured Logging.**
    *   **Rationale:** Return consistent JSON error responses with appropriate HTTP status codes. Implement structured, centralized logging with correlation IDs for tracing requests across services.
    *   **Impact if Ignored:** Inconsistent error handling, difficult debugging across services.

---

**K. Service-Specific Considerations**

1.  **Guideline (`auth_service`): Secure Secret Management and Persistent Token Revocation.**
    *   **Rationale:** Manage JWT and CSRF secrets securely via K8s Secrets. Implement persistent storage for token revocation lists to survive restarts.
    *   **Impact if Ignored:** System-wide security breach, ineffective token revocation.

2.  **Guideline (`gs_service`, `fv_service`): Resilient External Tool Integration.**
    *   **Rationale:** Design integrations with LLMs and SMT solvers to be resilient and configurable with proper error handling.
    *   **Impact if Ignored:** Unreliable synthesis/verification processes.

3.  **Guideline (`integrity_service`): Tamper-Evident Audit Logging.**
    *   **Rationale:** Implement cryptographic techniques for audit log integrity if high security is required.
    *   **Impact if Ignored:** Audit logs susceptible to tampering.

4.  **Guideline (`pgc_service`): Monitor Datalog Engine Performance.**
    *   **Rationale:** Monitor and optimize `pyDatalog` performance under high load with complex rulesets.
    *   **Impact if Ignored:** High latency in policy enforcement.

