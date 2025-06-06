# GS Service

## Purpose
Synthesizes enforceable governance policies from constitutional principles and provides monitoring utilities.

## Main Features
- Policy synthesis and management
- AlphaEvolve integration for governance tuning
- Reliability and performance monitoring

## Key API Endpoints
- `/api/v1/synthesize` - generate policies from principles
- `/api/v1/policy-management` - manage compiled policies
- `/api/v1/constitutional-reports` - produce governance reports
- `/api/v1/alphaevolve` - run AlphaEvolve governance workflows
- `/api/v1/performance` - access performance metrics

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
```bash
pytest tests
```
