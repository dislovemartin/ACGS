# Governance Structure Service (`gs_service`)

## Overview

The Governance Structure Service (`gs_service`) is responsible for managing the organizational governance structure related to AI within the ACGS-PGP system. It defines roles, responsibilities, decision-making processes, and escalation paths. This service helps map policies to accountable parties. In some contexts, this service is also referred to as the Governance Synthesizer Service, as it may be involved in generating policies (e.g., Datalog rules) from principles, potentially using LLMs. Currently, this service defines the framework for governance structures. LLM-driven policy synthesis and advanced generation capabilities are planned for Phase 2.

## Core Responsibilities

-   Managing and defining organizational roles relevant to AI governance.
-   Mapping responsibilities to these roles.
-   Defining decision-making workflows and escalation paths.
-   Facilitating the assignment of policies to accountable individuals or groups.
-   Potentially, synthesizing governance policies from high-level principles.
-   Integration with `shared/models.py` for relevant data models.

## API Endpoints

Detailed API documentation is available via Swagger UI at `/api/v1/gs/docs` when the service is running.

Key endpoints typically include operations related to:
-   Managing governance roles and responsibilities.
-   Defining and retrieving organizational structures.
-   Linking policies to governance structures.
-   Policy synthesis (if applicable).

## Dependencies

-   FastAPI
-   SQLAlchemy (via `shared` module)
-   Pydantic (via `shared` module)
Refer to `requirements.txt` for specific package versions. Core shared models are typically in `shared/models.py`.

## Local Development

For general setup, refer to the main project `README.md` and `docs/developer_guide.md`. This service can be run using Uvicorn: `uvicorn app.main:app --host 0.0.0.0 --port 8002`.
