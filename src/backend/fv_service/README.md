# FV Service

## Purpose
Performs formal verification of policies using SMT solvers to ensure correctness and safety.

## Main Features
- Verify policies against safety properties
- Cross-domain testing utilities
- WebSocket interface for live verification

## Key API Endpoints
- `/api/v1/verify` - submit policies for verification
- `/api/v1/cross-domain-testing` - run cross-domain tests

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set:
   - `AC_SERVICE_URL` - URL of the AC service
   - `INTEGRITY_SERVICE_URL` - URL of the Integrity service

### Running Service
```bash
uvicorn main:app --reload
```

### Running Tests
_No dedicated tests for this service_
