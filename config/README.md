# ACGS-PGP Configuration

This directory contains all configuration files for the AI Compliance Governance System - Policy Generation Platform (ACGS-PGP).

## Directory Structure

### `docker/`
Docker and Docker Compose configurations:
- `docker-compose.yml` - Main development environment
- `docker-compose.monitoring.yml` - Monitoring stack (Prometheus, Grafana)
- `nginx.conf` - API gateway configuration
- Service-specific Dockerfiles (if any)

### `k8s/`
Kubernetes deployment manifests:
- `deployment.yaml` - Main deployment configuration
- `ac-service.yaml` - Audit & Compliance Service
- `auth-service.yaml` - Authentication Service
- `fv-service.yaml` - Formal Verification Service
- `gs-service.yaml` - Governance Synthesis Service
- `integrity-service.yaml` - Integrity Service
- `pgc-service.yaml` - Protective Governance Controls Service
- `frontend-deployment.yaml` - Frontend deployment
- `postgres-deployment.yaml` - PostgreSQL database
- `postgres-service.yaml` - Database service

### `env/`
Environment variable templates:
- `.env.example` - Main environment variables template
- `.env.production` - Production environment template
- Service-specific environment files

### `monitoring/`
Monitoring and alerting configurations:
- `prometheus.yml` - Prometheus configuration
- `alertmanager.yml` - Alert manager rules
- Grafana dashboards (if any)

## Configuration Management

### Development Environment
1. Copy `.env.example` to `.env`
2. Modify values for your local setup
3. Use `docker-compose.yml` for local development

### Production Environment
1. Use `.env.production` as template
2. Set secure values for all secrets
3. Deploy using Kubernetes manifests
4. Configure monitoring and alerting

### Environment Variables

#### Database Configuration
- `DATABASE_URL` - PostgreSQL connection string
- `POSTGRES_USER` - Database username
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_DB` - Database name

#### Service URLs
- `AC_SERVICE_URL` - Audit & Compliance Service endpoint
- `AUTH_SERVICE_URL` - Authentication Service endpoint
- `FV_SERVICE_URL` - Formal Verification Service endpoint
- `GS_SERVICE_URL` - Governance Synthesis Service endpoint
- `INTEGRITY_SERVICE_URL` - Integrity Service endpoint
- `PGC_SERVICE_URL` - Protective Governance Controls Service endpoint

#### External Services
- `LLM_API_ENDPOINT` - LLM service endpoint
- `LLM_API_KEY` - LLM API key
- `OPENAI_API_KEY` - OpenAI API key
- `SMT_SOLVER_PATH` - Z3 solver binary path

#### Security Configuration
- `SECRET_KEY` - JWT signing key
- `CSRF_SECRET_KEY` - CSRF protection key
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

#### Constitutional Framework
- `CONSTITUTIONAL_COUNCIL_ENABLED` - Enable Constitutional Council
- `AC_AMENDMENT_THRESHOLD` - Amendment approval threshold
- `AC_VOTING_PERIOD_HOURS` - Voting period duration
- `CRYPTOGRAPHIC_INTEGRITY_ENABLED` - Enable PGP Assurance

## Deployment Configurations

### Docker Compose
- Development and testing environment
- All services in containers
- Shared volumes for development
- Hot reloading enabled

### Kubernetes
- Production-ready deployment
- Horizontal pod autoscaling
- Service discovery
- ConfigMaps and Secrets management
- Ingress configuration

### Monitoring
- Prometheus metrics collection
- Grafana dashboards
- Alert manager notifications
- Health checks and probes

## Security Considerations

1. **Secrets Management**: Use Kubernetes Secrets or external secret managers
2. **Network Security**: Configure proper ingress and network policies
3. **Database Security**: Use encrypted connections and strong passwords
4. **API Security**: Enable HTTPS and proper authentication
5. **Container Security**: Use minimal base images and security scanning

## Configuration Validation

Before deployment, validate configurations:
1. Check all required environment variables are set
2. Verify service connectivity
3. Test database connections
4. Validate SSL/TLS certificates
5. Run configuration tests

For detailed deployment instructions, see the deployment documentation in `docs/deployment/`.
