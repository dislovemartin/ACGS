# Workflow Service

## Purpose
Manages long-running workflows and exposes monitoring and recovery endpoints.

## Main Features
- Create and control workflow executions
- Monitoring dashboard and metrics
- Recovery and testing utilities

## Key API Endpoints
- `/workflows` - create and list workflows
- `/workflows/{workflow_id}/start` - start a workflow
- `/workflows/{workflow_id}/status` - check status
- `/monitoring/dashboard` - view monitoring dashboard
- `/recovery/checkpoints` - create recovery checkpoints

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
_No dedicated tests for this service_
