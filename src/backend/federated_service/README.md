# Federated Service

## Purpose
Implements privacy-preserving federated evaluation across distributed environments.

## Main Features
- Federated policy evaluation workflows
- Secure aggregation of results
- Privacy metrics computation

## Key API Endpoints
- `/api/v1/federated` - manage evaluation rounds
- `/api/v1/aggregation` - run secure result aggregation
- `/api/v1/privacy` - compute privacy metrics

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. No additional environment variables are required.

### Running Service
```bash
uvicorn main:app --reload
```

### Running Tests
```bash
pytest tests
```
