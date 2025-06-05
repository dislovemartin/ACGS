# Formal Verification Service (`fv_service`)

## Overview

The Formal Verification Service (`fv_service`) is responsible for the formal verification of AI policies and system specifications within the ACGS-PGP system. It integrates with formal verification tools to mathematically verify properties of AI policies or system designs against their specifications. Currently, the Formal Verification Service provides a foundational interface (mock implementation). Integration with specific formal verification tools is planned for Phase 2.

## Core Responsibilities

-   Accepting policy definitions/models and properties to be checked.
-   Integrating with formal verification tools (e.g., TLA+, Z3, custom model checkers).
-   Returning verification results (e.g., success, failure, counterexamples).
-   Storing and managing verification requests and results, potentially using `shared/models.py`.

## API Endpoints

Detailed API documentation is available via Swagger UI at `/api/v1/fv/docs` when the service is running.

Key endpoints typically include operations related to:
-   Submitting policies/specifications for verification.
-   Retrieving verification status and results.

## Dependencies

-   FastAPI
-   SQLAlchemy (via `shared` module)
-   Pydantic (via `shared` module)
-   Specific libraries for interacting with formal verification tools.
Refer to `requirements.txt` for specific package versions. Core shared models are typically in `shared/models.py`.

## Local Development

For general setup, refer to the main project `README.md` and `docs/developer_guide.md`. This service can be run using Uvicorn: `uvicorn app.main:app --host 0.0.0.0 --port 8003`.
