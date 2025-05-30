# Integrity & Verifiability Service (`integrity_service`)

## Overview

The Integrity & Verifiability Service (`integrity_service`) is responsible for ensuring the integrity of critical data within the ACGS-PGP system. This includes policies, audit logs, and verification results. It may involve mechanisms like cryptographic hashing, digital signatures, or blockchain-based logging to maintain a verifiable trail. This service also manages audit logs from all other services. In its current phase, the Data Integrity Service establishes the groundwork for managing audit logs. Advanced mechanisms like cryptographic hashing/signatures for all artifacts or blockchain logging are future enhancements.

## Core Responsibilities

-   Providing mechanisms for ensuring data integrity for policies, audit logs, and verification results.
-   Managing and storing audit logs from all services in a secure and verifiable manner.
-   Potentially implementing cryptographic hashing or digital signatures for data elements.
-   Integration with `shared/models.py` for relevant data models (e.g., for audit logs).

## API Endpoints

Detailed API documentation is available via Swagger UI at `/api/v1/integrity/docs` when the service is running.

Key endpoints typically include operations related to:
-   Storing and retrieving audit logs.
-   Verifying data integrity (if applicable).

## Dependencies

-   FastAPI
-   SQLAlchemy (via `shared` module)
-   Pydantic (via `shared` module)
Refer to `requirements.txt` for specific package versions. Core shared models are typically in `shared/models.py`.

## Local Development

For general setup, refer to the main project `README.md` and `docs/developer_guide.md`. This service can be run using Uvicorn: `uvicorn app.main:app --host 0.0.0.0 --port 8005`.
