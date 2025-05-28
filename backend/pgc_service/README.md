# PGC Service (Policy Governance & Compliance Service)

**Core Role: Policy Enforcement Engine**

This service is responsible for the enforcement of policies. It utilizes a Datalog engine (`pyDatalog`) to evaluate defined policies against given contextual information and facts.

## Key Responsibilities

*   Receives policy evaluation requests.
*   Interprets and loads relevant policy rules (expressed in Datalog or translatable to Datalog).
*   Queries the Datalog engine with the facts from the request.
*   Returns the outcome of the policy evaluation (e.g., allow/deny, obligations, explanations).

**Note:** Policy *generation*, *synthesis*, and *template management* are primarily handled by the **GS Service (Governance Synthesizer Service)**. This `pgc_service` focuses on the evaluation and enforcement aspect.

## Setup & Dependencies

- Python 3.9+
- FastAPI
- pyDatalog
- Other dependencies as listed in `requirements.txt`.

To install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 800X # Replace 800X with actual port
```

## API Endpoints

*(To be documented - e.g., `/evaluate`, `/check_compliance`)*

## Datalog Engine

The core logic for policy evaluation resides in `app/core/datalog_engine.py`. Ensure that Datalog rules are correctly formulated and loaded.

---

*This README should be expanded with details on API specifications, specific Datalog rule conventions, and operational notes.*
