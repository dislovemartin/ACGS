# EC Service

## Purpose
Provides evolutionary computation capabilities used for governed model evolution and performance monitoring.

## Main Features
- Oversight of evolutionary algorithms and operators
- AlphaEvolve integration for iterative improvement
- Reporting and monitoring of experiment progress

## Key API Endpoints
- `/api/v1/oversight` - manage evolutionary oversight tasks
- `/api/v1/alphaevolve` - run AlphaEvolve processes
- `/api/v1/reporting` - fetch execution reports
- `/api/v1/monitoring` - monitor ongoing runs
- `/api/v1/wina/performance` - WINA performance metrics

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. No special environment variables are required.

### Running Service
```bash
uvicorn main:app --reload
```

### Running Tests
_No dedicated tests for this service_
