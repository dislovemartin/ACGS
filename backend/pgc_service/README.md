# Policy Governance & Compliance Service (`pgc_service`)

## Overview

The Policy Governance & Compliance Service (`pgc_service`) is responsible for the enforcement of policies within the ACGS-PGP system. It utilizes a Datalog engine (`pyDatalog`) to evaluate defined policies against given contextual information and facts. Its core role is to act as a Policy Enforcement Engine.

Policy *generation*, *synthesis*, and *template management* are primarily handled by the **GS Service (Governance Synthesizer Service)**. This `pgc_service` focuses on the evaluation and enforcement aspect.

## Core Responsibilities

*   Receives policy evaluation requests.
*   Interprets and loads relevant policy rules (expressed in Datalog or translatable to Datalog).
*   Queries the Datalog engine with the facts from the request.
*   Returns the outcome of the policy evaluation (e.g., allow/deny, obligations, explanations).
*   Integration with `shared/models.py` for relevant data models if applicable for storing evaluation contexts or results.

## API Endpoints

Detailed API documentation is available via Swagger UI at `/api/v1/pgc/docs` when the service is running.

Key endpoints typically include:
*   `/evaluate` (or similar for policy evaluation)
*   `/check_compliance` (or similar)

## Datalog Engine

The core logic for policy evaluation resides in `app/core/datalog_engine.py`. Ensure that Datalog rules are correctly formulated and loaded for the engine to process. (Note: Specific Datalog rule conventions are being established. Detailed documentation will be added as the service's Datalog capabilities for policy evaluation are further refined.)

## Dependencies

-   Python 3.9+
-   FastAPI
-   pyDatalog
-   SQLAlchemy (via `shared` module, if used for policy/result storage)
-   Pydantic (via `shared` module)
Refer to `requirements.txt` for specific package versions.

## Local Development

For general setup, refer to the main project `README.md` and `docs/developer_guide.md`. This service can be run using Uvicorn: `uvicorn app.main:app --host 0.0.0.0 --port 8004`.

To install dependencies:
```bash
pip install -r requirements.txt
```

---
*This README will be expanded with more details on specific Datalog rule conventions, policy evaluation examples, and operational notes as the service evolves.*
