# Audit & Compliance Service (`ac_service`)

## Overview

The Audit & Compliance Service (`ac_service`) is responsible for managing AI governance principles and guidelines within the ACGS-PGP system. It allows users to browse and understand the core tenets of AI governance, forming a foundational layer for policy creation and verification.

## Core Responsibilities

-   Managing and providing access to AI governance principles.
-   Managing and providing access to guidelines associated with these principles.
-   Facilitating audit and compliance workflows by making these documents readily available.
-   Integration with `shared/models.py` for relevant data models.

## API Endpoints

Detailed API documentation is available via Swagger UI at `/api/v1/ac/docs` when the service is running.

Key endpoints typically include operations related to:
-   Retrieving and managing governance principles.
-   Retrieving and managing guidelines.

## Dependencies

-   FastAPI
-   SQLAlchemy (via `shared` module)
-   Pydantic (via `shared` module)
Refer to `requirements.txt` for specific package versions. Core shared models are typically in `shared/models.py`.

## Local Development

For general setup, refer to the main project `README.md` and `docs/developer_guide.md`. This service can be run using Uvicorn: `uvicorn app.main:app --host 0.0.0.0 --port 8001`.
