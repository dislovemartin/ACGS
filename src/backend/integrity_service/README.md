# Integrity Service

## Purpose
Stores policies, audit logs, and cryptographic data to ensure traceability and verifiability.

## Main Features
- Policy storage and retrieval
- Audit and logging endpoints
- PGP assurance and cryptographic utilities

## Key API Endpoints
- `/api/v1/policies` - manage stored policies
- `/api/v1/audit` - access audit logs
- `/api/v1/crypto` - cryptographic operations
- `/api/v1/integrity` - general integrity checks
- `/api/v1/pgp-assurance` - manage PGP certificates
- `/api/v1/research` - store research data

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and configure:
   - `DATABASE_URL` - PostgreSQL connection
   - `APP_ENV` - `development` or `production`

### Running Service
```bash
uvicorn main:app --reload
```

### Running Tests
_No dedicated tests for this service_
