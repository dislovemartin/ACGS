# ACGS-PGP Deployment Guide

This comprehensive guide provides instructions for deploying the AI Compliance Governance System - Policy Generation Platform (ACGS-PGP) with all Phase 1-3 features including Constitutional Council, AlphaEvolve integration, Z3 formal verification, and PGP cryptographic integrity.

## Prerequisites

### **System Requirements**
*   **Docker:** Version 20.10+ with Docker Compose v2
*   **Kubernetes:** Version 1.21+ for production deployment
*   **kubectl:** Configured to interact with your Kubernetes cluster
*   **Git:** For cloning the repository
*   **Python:** 3.9+ for local development and testing

### **External Dependencies**
*   **OpenAI API Key:** Required for constitutional prompting and LLM integration
*   **Z3 SMT Solver:** Automatically installed in containers for formal verification
*   **PGP/GPG Keys:** For cryptographic integrity (can be generated during setup)
*   **Container Registry:** Access to Docker Hub, GCR, ECR, or similar for production

### **Hardware Requirements**
*   **Development:** 8GB RAM, 4 CPU cores, 20GB disk space
*   **Production:** 16GB RAM, 8 CPU cores, 100GB disk space (minimum)
*   **Database:** SSD storage recommended for sub-20ms governance decision latency

## Part 1: Docker Compose Deployment (Local Development)

This setup provides a complete ACGS-PGP environment with all Phase 1-3 features for local development and testing.

### **Step 1: Repository Setup**
```bash
git clone https://github.com/dislovemartin/ACGS.git
cd ACGS-master
```

### **Step 2: Environment Configuration**

#### **Core Environment Variables**
Copy and configure the main environment file:
```bash
cp config/env/.env.example .env
```

Edit `.env` with the following required variables:
```bash
# Database Configuration
DATABASE_URL=postgresql://acgs_user:acgs_password@postgres:5432/acgs_db

# Authentication
AUTH_SERVICE_SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# LLM Integration (Required for Constitutional Prompting)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4

# Z3 Formal Verification
Z3_TIMEOUT_SECONDS=30
Z3_MAX_MEMORY_MB=1024

# PGP Cryptographic Integrity
PGP_KEY_ID=your-pgp-key-id
PGP_PASSPHRASE=your-pgp-passphrase

# Service Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

#### **Frontend Configuration**
```bash
cd src/frontend
cp .env.example .env
```

Edit `src/frontend/.env`:
```bash
REACT_APP_API_BASE_URL=/api
REACT_APP_ENVIRONMENT=development
REACT_APP_ENABLE_CONSTITUTIONAL_COUNCIL=true
REACT_APP_ENABLE_ALPHAEVOLVE=true
```

### **Step 3: Deploy Monitoring Infrastructure**
Deploy the complete monitoring stack with Prometheus, Grafana, and AlertManager:
```bash
# Deploy monitoring infrastructure
chmod +x scripts/deploy_monitoring.sh
./scripts/deploy_monitoring.sh

# Verify monitoring stack deployment
curl -f http://localhost:9090/api/v1/status/config  # Prometheus
curl -f http://localhost:3001/api/health           # Grafana
```

### **Step 4: Build and Deploy Services**
From the project root directory:
```bash
# Build and start all services with monitoring
docker-compose -f config/docker/docker-compose.yml up --build -d

# Verify all services are running
docker-compose -f config/docker/docker-compose.yml ps

# Check service health endpoints
for port in 8000 8001 8002 8003 8004 8005; do
  echo "Checking service on port $port..."
  curl -f http://localhost:$port/health || echo "Service on port $port not ready"
done
```

### **Step 5: Validate Monitoring Integration**
```bash
# Run monitoring validation script
./scripts/load_test_monitoring.sh 10 60

# Check metrics collection
curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result[] | select(.metric.job | startswith("acgs"))'

# Verify Grafana dashboards
curl -s -u admin:admin123 http://localhost:3001/api/dashboards/home
```

### **Step 6: Initialize Constitutional Framework**
```bash
# Load test data including constitutional principles
python scripts/load_test_data.py

# Verify constitutional setup
python scripts/verify_acgs_deployment.sh

# Test complete policy pipeline with monitoring
python scripts/test_policy_pipeline.py --with-monitoring
```

### **Step 7: Access Services and Monitoring**

#### **Frontend Applications**
*   **Constitutional Dashboard:** `http://localhost:3000`
*   **Policy Management Interface:** `http://localhost:3000/policies`
*   **Constitutional Council Portal:** `http://localhost:3000/council`

#### **Backend API Services**
*   **API Gateway:** `http://localhost:8000`
*   **Auth Service:** `http://localhost:8000/api/auth/` ([docs](http://localhost:8000/api/auth/docs))
*   **AC Service:** `http://localhost:8000/api/ac/` ([docs](http://localhost:8000/api/ac/docs))
*   **GS Service:** `http://localhost:8000/api/gs/` ([docs](http://localhost:8000/api/gs/docs))
*   **FV Service:** `http://localhost:8000/api/fv/` ([docs](http://localhost:8000/api/fv/docs))
*   **Integrity Service:** `http://localhost:8000/api/integrity/` ([docs](http://localhost:8000/api/integrity/docs))
*   **PGC Service:** `http://localhost:8000/api/pgc/` ([docs](http://localhost:8000/api/pgc/docs))

#### **Monitoring and Observability**
*   **Grafana Dashboards:** `http://localhost:3001` (admin/admin123)
    - ACGS-PGP Overview Dashboard
    - Service Performance Metrics
    - Authentication and Security Metrics
    - Database Performance Dashboard
    - Error Analysis and Alerting
*   **Prometheus Metrics:** `http://localhost:9090`
    - Service health and performance metrics
    - Custom ACGS-PGP business metrics
    - Infrastructure and resource metrics
*   **AlertManager:** `http://localhost:9093` (Internal)
    - Alert routing and notification management
    - Integration with external notification systems

#### **Production Monitoring Targets**
- **API Response Times:** <200ms (95th percentile)
- **Service Uptime:** >99.5% availability
- **Authentication Success Rate:** >95%
- **Database Query Times:** <100ms (95th percentile)
- **Error Rates:** <5% across all services
- **Concurrent Users:** Support for 100+ concurrent users

5.  **Database Migrations (Manual, if needed):**
    The `alembic-runner` service in `docker-compose.yml` is configured to run migrations on startup. If you need to run migrations manually:
    ```bash
    docker-compose exec alembic-runner alembic upgrade head 
    # or to create a new migration:
    # docker-compose exec alembic-runner alembic revision -m "your_migration_message" 
    ```
    Ensure `DATABASE_URL` in your root `.env` file is correctly picked up by the `alembic-runner` service.

6.  **Stopping Services:**
    ```bash
    docker-compose down
    ```
    To remove volumes (e.g., PostgreSQL data):
    ```bash
    docker-compose down -v
    ```

## Part 2: Kubernetes Deployment (Staging/Production)

Refer to the `acgs-pgp/k8s/README.md` file for detailed instructions on deploying to Kubernetes. The general steps involve:

1.  **Prerequisites:** Ensure all prerequisites listed in `k8s/README.md` are met (Kubernetes cluster, `kubectl`, Docker images pushed to a registry, secrets created).
2.  **Image Tagging:** Make sure your Docker images are tagged appropriately and pushed to your container registry. Update the `image:` fields in all Kubernetes YAML files (`k8s/*.yaml`) to point to your images.
3.  **Apply Secrets and ConfigMaps:** Create necessary Kubernetes `Secret` and `ConfigMap` objects in your cluster (e.g., for database credentials, JWT secrets, PostgreSQL configuration).
4.  **Deploy PostgreSQL:** Apply the `postgres-deployment.yaml` and `postgres-service.yaml` (or use a managed cloud database).
5.  **Deploy Backend Services:** Apply the YAML files for each backend service (`auth-service.yaml`, `ac-service.yaml`, etc.).
6.  **Deploy Frontend Service:** Apply the `frontend-deployment.yaml`.
7.  **Verify:** Use `kubectl get pods`, `kubectl get services`, `kubectl logs <pod-name>` to check the status.
8.  **Expose Application:** Configure an Ingress controller or use LoadBalancer services to expose the frontend and potentially an API gateway for backend services.

## Troubleshooting

*   **Service Connection Issues (Docker Compose):**
    *   Ensure `DATABASE_URL` in `.env` points to the Docker Compose PostgreSQL service name (e.g., `postgresql://user:password@postgres:5432/acgs_db`).
    *   Check Nginx routing configuration in `docker-compose.yml` if services are not accessible via `http://localhost:8000`.
*   **Service Connection Issues (Kubernetes):**
    *   Verify `DATABASE_URL` in secrets points to the Kubernetes service name for PostgreSQL (e.g., `postgres-service:5432`).
    *   Check `ClusterIP` service definitions and ensure target ports match container ports.
    *   Use `kubectl logs` to inspect service startup errors.
    *   Ensure DNS resolution is working within the cluster.
*   **Migration Errors:**
    *   Ensure the `DATABASE_URL` is correct and the database server is accessible from where Alembic is run (either `alembic-runner` container or your local environment if running directly).
    *   Check that `Base` from `shared.models` (or `shared.database`) is correctly imported in `alembic/env.py` so Alembic can detect model changes for autogeneration.
*   **Image Pull Errors (Kubernetes):**
    *   Ensure image names and tags are correct in deployment YAMLs.
    *   Verify the Kubernetes cluster has permissions to pull from your container registry (e.g., using `imagePullSecrets`).
