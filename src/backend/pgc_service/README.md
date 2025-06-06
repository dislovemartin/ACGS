# PGC Service

## Purpose
Enforces governance policies in real time using the Open Policy Agent.

## Main Features
- Runtime enforcement of synthesized policies
- AlphaEvolve enforcement integration
- Incremental compilation and low latency modes

## Key API Endpoints
- `/api/v1/enforcement` - evaluate requests against policies
- `/api/v1/alphaevolve` - run AlphaEvolve enforcement logic
- `/api/v1/incremental` - incremental policy compilation
- `/api/v1/ultra-low-latency` - optimized enforcement path

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set:
   - `INTEGRITY_SERVICE_URL` - URL of the Integrity service
   - `POLICY_REFRESH_INTERVAL_SECONDS` - policy reload interval

### Running Service
```bash
uvicorn main:app --reload
```

### Running Tests
```bash
pytest tests
```
