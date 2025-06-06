# AC Service

## Purpose
Provides constitutional management including principles, council workflows, and conflict resolution mechanisms.

## Main Features
- Manage principles and guidelines
- Support Constitutional Council voting and amendments
- Monitor fidelity and handle conflict resolution events

## Key API Endpoints
- `/api/v1/principles` - CRUD operations for constitutional principles
- `/api/v1/constitutional-council` - council management and voting
- `/api/v1/conflict-resolution` - resolve policy conflicts
- `/api/v1/fidelity` - track adherence to principles
- `/api/v1/dashboard` - WebSocket dashboard updates

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and configure:
   - `DATABASE_URL` - PostgreSQL connection string
   - `APP_ENV` - `development` or `production`
   - `AUTH_SERVICE_TOKEN` - token for internal calls

### Running Service
```bash
uvicorn main:app --reload
```

### Running Tests
```bash
pytest tests
```
