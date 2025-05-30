# ACGS-PGP API Documentation

This directory contains comprehensive API documentation for all ACGS-PGP microservices.

## Service APIs

### Authentication Service (`auth_service`)
- **Base URL:** `http://localhost:8000/api/auth/`
- **Documentation:** [auth_service_api.md](auth_service_api.md)
- **Interactive Docs:** `http://localhost:8000/api/auth/docs`
- **Features:** User authentication, RBAC, JWT token management

### Audit & Compliance Service (`ac_service`)
- **Base URL:** `http://localhost:8000/api/ac/`
- **Documentation:** [ac_service_api.md](ac_service_api.md)
- **Interactive Docs:** `http://localhost:8000/api/ac/docs`
- **Features:** Constitutional principles, meta-rules, Constitutional Council, conflict resolution

### Governance Synthesis Service (`gs_service`)
- **Base URL:** `http://localhost:8000/api/gs/`
- **Documentation:** [gs_service_api.md](gs_service_api.md)
- **Interactive Docs:** `http://localhost:8000/api/gs/docs`
- **Features:** Policy synthesis, constitutional prompting, LLM integration, AlphaEvolve governance

### Formal Verification Service (`fv_service`)
- **Base URL:** `http://localhost:8000/api/fv/`
- **Documentation:** [fv_service_api.md](fv_service_api.md)
- **Interactive Docs:** `http://localhost:8000/api/fv/docs`
- **Features:** Z3 SMT solver integration, tiered validation, safety property checking

### Integrity & Verifiability Service (`integrity_service`)
- **Base URL:** `http://localhost:8000/api/integrity/`
- **Documentation:** [integrity_service_api.md](integrity_service_api.md)
- **Interactive Docs:** `http://localhost:8000/api/integrity/docs`
- **Features:** Audit logs, PGP assurance, cryptographic integrity, policy storage

### Protective Governance Controls Service (`pgc_service`)
- **Base URL:** `http://localhost:8000/api/pgc/`
- **Documentation:** [pgc_service_api.md](pgc_service_api.md)
- **Interactive Docs:** `http://localhost:8000/api/pgc/docs`
- **Features:** Runtime policy enforcement, real-time governance, AlphaEvolve enforcement

## Common API Patterns

### Authentication
All API endpoints (except public health checks) require authentication via JWT tokens:

```bash
curl -H "Authorization: Bearer <your_jwt_token>" \
     http://localhost:8000/api/ac/principles
```

### Response Format
All APIs follow a consistent response format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Handling
Error responses include detailed information:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid principle data",
    "details": { ... }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Pagination
List endpoints support pagination:

```bash
GET /api/ac/principles?page=1&limit=20&sort=created_at&order=desc
```

## Service Integration Patterns

### Cross-Service Communication
Services communicate using internal service tokens and standardized schemas:

1. **AC Service → GS Service:** Principle retrieval for constitutional prompting
2. **GS Service → FV Service:** Policy verification requests
3. **FV Service → Integrity Service:** Verification result storage
4. **PGC Service → All Services:** Runtime governance enforcement

### Constitutional Workflow
The complete constitutional governance workflow:

1. **Principle Management** (AC Service): Define constitutional principles
2. **Constitutional Prompting** (GS Service): Generate policies with constitutional guidance
3. **Formal Verification** (FV Service): Verify policies against principles
4. **Integrity Assurance** (Integrity Service): Store with cryptographic signatures
5. **Runtime Enforcement** (PGC Service): Enforce policies in real-time

## Development and Testing

### Local Development
Start all services with Docker Compose:

```bash
docker-compose -f config/docker/docker-compose.yml up --build -d
```

### API Testing
Use the provided test scripts:

```bash
# Load test data
python scripts/load_test_data.py

# Run API tests
python -m pytest tests/integration/test_api_endpoints.py
```

### Interactive Documentation
Each service provides Swagger UI documentation at `/docs` endpoint:
- Auth Service: http://localhost:8000/api/auth/docs
- AC Service: http://localhost:8000/api/ac/docs
- GS Service: http://localhost:8000/api/gs/docs
- FV Service: http://localhost:8000/api/fv/docs
- Integrity Service: http://localhost:8000/api/integrity/docs
- PGC Service: http://localhost:8000/api/pgc/docs

## Security Considerations

### Authentication & Authorization
- JWT tokens with configurable expiration
- Role-based access control (Admin, Policy Manager, Auditor)
- Service-to-service authentication with internal tokens

### Data Protection
- HTTPS enforcement in production
- Input validation and sanitization
- Rate limiting and request throttling
- Audit logging for all operations

### Constitutional Compliance
- All operations logged for constitutional audit
- Principle-based access control
- Cryptographic integrity verification
- Democratic governance through Constitutional Council

For detailed endpoint documentation, refer to the individual service API documentation files.
