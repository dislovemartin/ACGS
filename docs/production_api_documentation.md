# ACGS-PGP Production API Documentation

## Overview

The ACGS-PGP (AI Compliance Governance System - Policy Generation Platform) provides a comprehensive microservices-based API for AI governance, policy management, and compliance verification. This documentation covers the production deployment with monitoring, load balancing, and security features.

## Architecture

### Microservices

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| Authentication Service | 8000 | User authentication, JWT tokens, CSRF protection | `/health` |
| AC Service | 8001 | Artificial Constitution management, principles, meta-rules | `/health` |
| Integrity Service | 8002 | Policy integrity, audit logs, cryptographic verification | `/health` |
| FV Service | 8003 | Formal verification using Z3 SMT solver | `/health` |
| GS Service | 8004 | Governance synthesis, LLM integration, policy generation | `/health` |
| PGC Service | 8005 | Protective governance controls, policy enforcement | `/health` |

### Infrastructure Services

| Service | Port | Purpose | Access | Production URL |
|---------|------|---------|--------|----------------|
| Nginx Gateway | 80/443 | Load balancing, reverse proxy, SSL termination | Main entry point | https://api.acgs-pgp.example.com |
| PostgreSQL | 5432 | Primary database with connection pooling | Internal only | Internal cluster |
| Prometheus | 9090 | Metrics collection and alerting | http://localhost:9090 | https://metrics.acgs-pgp.example.com |
| Grafana | 3001 | Monitoring dashboards with <30s refresh | http://localhost:3001 | https://monitoring.acgs-pgp.example.com |
| AlertManager | 9093 | Alert routing and notification | Internal only | Internal cluster |

### Production Environment Variables

```bash
# Core Configuration
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:password@postgres-cluster:5432/acgs_pgp_db
BACKEND_CORS_ORIGINS=https://app.acgs-pgp.example.com,https://admin.acgs-pgp.example.com

# Security Configuration
AUTH_SERVICE_SECRET_KEY=your_production_jwt_secret_key_256_bits
AUTH_SERVICE_CSRF_SECRET_KEY=your_production_csrf_secret_key_256_bits
AUTH_SERVICE_ACCESS_TOKEN_EXPIRE_MINUTES=15
AUTH_SERVICE_REFRESH_TOKEN_EXPIRE_DAYS=7

# Monitoring Configuration
PROMETHEUS_RETENTION_TIME=30d
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure_production_password
ALERT_WEBHOOK_URL=https://alerts.acgs-pgp.example.com/webhook

# Performance Tuning
POSTGRES_MAX_CONNECTIONS=200
NGINX_WORKER_PROCESSES=auto
NGINX_WORKER_CONNECTIONS=1024
```

## API Endpoints

### Authentication Service (Port 8000)

#### Core Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (returns JWT + refresh token)
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user profile
- `GET /auth/csrf-token` - Get CSRF token for form submissions

#### Health and Monitoring
- `GET /health` - Service health check with database connectivity
- `GET /metrics` - Prometheus metrics endpoint with authentication metrics
- `GET /auth/health/detailed` - Detailed health check with dependencies
- `GET /auth/metrics/auth` - Authentication-specific metrics (login rates, token usage)

#### Production Examples

**Health Check Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy"
  },
  "metrics": {
    "active_sessions": 150,
    "requests_per_minute": 45
  }
}
```

**Authentication Flow with Monitoring:**
```bash
# 1. Register with rate limiting
curl -X POST https://api.acgs-pgp.example.com/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 192.168.1.100" \
  -d '{"email": "user@company.com", "password": "SecurePass123!", "full_name": "John Doe"}'

# 2. Login with CSRF protection
curl -X POST https://api.acgs-pgp.example.com/auth/login \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: csrf_token_here" \
  -c cookies.txt \
  -d '{"username": "user@company.com", "password": "SecurePass123!"}'

# 3. Access protected endpoint
curl -X GET https://api.acgs-pgp.example.com/auth/me \
  -H "Authorization: Bearer jwt_token_here" \
  -H "X-CSRF-Token: csrf_token_here" \
  -b cookies.txt
```

### AC Service (Port 8001)

#### Principles Management
- `GET /api/v1/principles/` - List all principles
- `POST /api/v1/principles/` - Create new principle
- `GET /api/v1/principles/{id}` - Get specific principle
- `PUT /api/v1/principles/{id}` - Update principle
- `DELETE /api/v1/principles/{id}` - Delete principle

#### Constitutional Council
- `GET /api/v1/constitutional-council/amendments` - List amendments
- `POST /api/v1/constitutional-council/amendments` - Propose amendment
- `POST /api/v1/constitutional-council/amendments/{id}/vote` - Vote on amendment
- `GET /api/v1/constitutional-council/amendments/{id}/comments` - Get amendment comments

### Integrity Service (Port 8002)

#### Policy Management
- `GET /api/v1/policies/` - List policies
- `POST /api/v1/policies/` - Create policy
- `GET /api/v1/policies/{id}` - Get policy details
- `PUT /api/v1/policies/{id}` - Update policy

#### Audit Operations
- `GET /api/v1/audit/logs` - Get audit logs
- `POST /api/v1/audit/logs` - Create audit entry

#### Cryptographic Operations (Phase 3)
- `POST /api/v1/crypto/sign` - Sign data with PGP
- `POST /api/v1/crypto/verify` - Verify PGP signature
- `POST /api/v1/crypto/hash` - Generate SHA3-256 hash
- `GET /api/v1/crypto/keys` - List available keys

### FV Service (Port 8003)

#### Formal Verification
- `POST /api/v1/verify/policy` - Verify policy using Z3
- `POST /api/v1/verify/constraint` - Verify constraint satisfaction
- `GET /api/v1/verify/status/{job_id}` - Get verification status

#### Algorithmic Fairness (Phase 3)
- `POST /api/v1/verify/fairness` - Check algorithmic fairness
- `GET /api/v1/verify/bias-metrics` - Get bias detection metrics

### GS Service (Port 8004)

#### Policy Synthesis
- `POST /api/v1/synthesize/policy` - Generate policy using LLM
- `POST /api/v1/synthesize/constitutional` - Constitutional synthesis
- `GET /api/v1/synthesize/templates` - Get policy templates

#### AlphaEvolve Integration (Phase 2)
- `POST /api/v1/alphaevolve/evolve` - Trigger evolutionary optimization
- `GET /api/v1/alphaevolve/population` - Get current population
- `GET /api/v1/alphaevolve/metrics` - Get evolution metrics

### PGC Service (Port 8005)

#### Policy Enforcement
- `POST /api/v1/enforcement/evaluate` - Evaluate policy compliance
- `GET /api/v1/enforcement/rules` - Get active enforcement rules
- `POST /api/v1/enforcement/rules` - Create enforcement rule

#### AlphaEvolve Enforcement (Phase 2)
- `POST /api/v1/alphaevolve/enforce` - Enforce evolved policies
- `GET /api/v1/alphaevolve/compliance` - Check compliance status

## Authentication and Security

### JWT Authentication
All API endpoints (except health checks and public endpoints) require JWT authentication:

```bash
# Get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password"}'

# Use JWT token in requests
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### CSRF Protection
Form submissions require CSRF tokens:

```bash
# Get CSRF token
curl -X GET http://localhost:8000/auth/csrf-token \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Use CSRF token in POST requests
curl -X POST http://localhost:8001/api/v1/principles/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Principle", "description": "Test"}'
```

### Rate Limiting
API endpoints are rate-limited:
- Default: 100 requests per minute per IP
- Authentication endpoints: 10 requests per minute per IP
- Monitoring endpoints: No rate limiting

## Monitoring and Metrics

### Prometheus Metrics
All services expose metrics at `/metrics` endpoint:

```bash
# Get auth service metrics
curl http://localhost:8000/metrics

# Get all service metrics via Nginx
curl http://localhost:8000/metrics/auth
curl http://localhost:8000/metrics/ac
curl http://localhost:8000/metrics/integrity
curl http://localhost:8000/metrics/fv
curl http://localhost:8000/metrics/gs
curl http://localhost:8000/metrics/pgc
```

### Key Metrics
- `acgs_http_requests_total` - Total HTTP requests by service, method, endpoint, status
- `acgs_http_request_duration_seconds` - Request duration histogram
- `acgs_auth_attempts_total` - Authentication attempts by type and status
- `acgs_database_connections` - Database connection pool status
- `acgs_service_calls_total` - Inter-service communication metrics
- `acgs_errors_total` - Error counts by type and severity

### Grafana Dashboards
Access monitoring dashboards at http://localhost:3001:
- Username: `admin`
- Password: `admin123`

Available dashboards:
- **ACGS-PGP Overview**: System-wide metrics and health
- **Service Performance**: Individual service performance metrics
- **Authentication Metrics**: Login success rates, token usage
- **Database Performance**: Query times, connection pools
- **Error Analysis**: Error rates and types across services

## Load Balancing and Scaling

### Horizontal Scaling
Services can be scaled horizontally by adding instances:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  auth_service_2:
    build: ./backend/auth_service
    container_name: acgs_auth_service_2
    environment:
      - DATABASE_URL=postgresql+asyncpg://acgs_user:acgs_password@postgres_db:5432/acgs_pgp_db
    depends_on:
      - postgres_db
```

Update nginx.conf to include new instances:
```nginx
upstream auth_service_upstream {
    least_conn;
    server auth_service:8000 max_fails=3 fail_timeout=30s weight=1;
    server auth_service_2:8000 max_fails=3 fail_timeout=30s weight=1;
    keepalive 32;
}
```

### Load Testing
Validate performance under load:

```bash
# Run load test with 100 concurrent users for 5 minutes
./scripts/load_test_monitoring.sh 100 300

# Monitor during load test
curl http://localhost:9090/api/v1/query?query=rate(acgs_http_requests_total[5m])
```

## Error Handling

### Standard Error Responses
All services return consistent error formats:

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "uuid-string"
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing/invalid JWT)
- `403` - Forbidden (CSRF failure, insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (business logic errors)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error

## Production Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Monitoring stack deployed
- [ ] Load balancing configured

### Post-deployment
- [ ] Health checks passing
- [ ] Metrics collection working
- [ ] Grafana dashboards accessible
- [ ] Alert rules configured
- [ ] Load testing completed
- [ ] Security scan passed

### Monitoring Targets
- API response times < 200ms (95th percentile)
- Error rates < 5%
- Service uptime > 99.5%
- Authentication success rate > 95%
- Database query times < 100ms (95th percentile)

## Support and Troubleshooting

### Common Issues
1. **Service not responding**: Check health endpoints and logs
2. **High response times**: Check database connections and query performance
3. **Authentication failures**: Verify JWT configuration and CSRF tokens
4. **Metrics not collecting**: Check Prometheus configuration and service endpoints

### Log Analysis
```bash
# View service logs
docker-compose logs -f auth_service
docker-compose logs -f --tail=100 --timestamps

# Check specific errors
docker-compose logs auth_service | grep ERROR
```

### Performance Debugging
```bash
# Check resource usage
docker stats

# Monitor request rates
curl -s "http://localhost:9090/api/v1/query?query=rate(acgs_http_requests_total[5m])"

# Check response times
curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, rate(acgs_http_request_duration_seconds_bucket[5m]))"
```

## Quick Start Guide

### 1. Deploy Full Stack
```bash
# Clone repository
git clone <repository-url>
cd ACGS-master

# Deploy monitoring infrastructure
chmod +x scripts/deploy_monitoring.sh
./scripts/deploy_monitoring.sh

# Start all services
cd config/docker
docker-compose up -d

# Verify deployment
./scripts/load_test_monitoring.sh 10 60
```

### 2. Access Services
- **API Gateway**: http://localhost:8000
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Frontend**: http://localhost:3000

### 3. Test Authentication
```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test User"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test@example.com", "password": "testpass123"}'
```
