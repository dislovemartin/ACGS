# Deployment Guide for ACGS-PGP

This guide provides instructions for deploying the AI Compliance Governance System - Policy Generation Platform (ACGS-PGP) using Docker Compose (for local development/testing) and Kubernetes (for staging/production).

## Prerequisites

*   **Docker:** Installed and running (for both Docker Compose and Kubernetes).
*   **Docker Compose:** Installed (for local deployment).
*   **Kubernetes Cluster:** Access to a running Kubernetes cluster (e.g., Minikube, Kind, Docker Desktop K8s, or a cloud provider's K8s service like GKE, EKS, AKS).
*   **`kubectl`:** Configured to interact with your Kubernetes cluster.
*   **Container Registry:** Access to a container registry (e.g., Docker Hub, GCR, ECR) where your service images are pushed.
*   **Git:** For cloning the repository.
*   **Environment Configuration:** Prepare `.env` files as needed (see `.env.example` files in the root and frontend directories).

## Part 1: Docker Compose Deployment (Local Development)

This setup is ideal for local development and testing.

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd acgs-pgp
    ```

2.  **Configure Environment Variables:**
    *   Copy `acgs-pgp/.env.example` to `acgs-pgp/.env`.
    *   Review and update variables in `.env`, especially `DATABASE_URL`, `SECRET_KEY` (for `auth_service`), and any API keys for LLMs if `pgc_service` uses them.
    *   Copy `acgs-pgp/frontend/.env.example` to `acgs-pgp/frontend/.env`.
    *   Update `REACT_APP_API_BASE_URL` in `frontend/.env` if your services will be exposed on a different base path by Docker Compose (though the default proxy setup in `frontend/package.json` and Nginx config in `docker-compose.yml` usually handles `http://localhost:8000` for the backend).

3.  **Build and Run Services:**
    From the `acgs-pgp` root directory:
    ```bash
    docker-compose up --build -d
    ```
    This command will:
    *   Build Docker images for all services defined in `docker-compose.yml`.
    *   Start containers for each service.
    *   Run database migrations using the `alembic-runner` service.

4.  **Accessing Services:**
    *   **Frontend:** `http://localhost:3000` (served by React development server via Docker Compose)
    *   **Backend Services (example `auth_service`):** `http://localhost:8000/auth/` (as routed by Nginx in Docker Compose)
    *   Other backend services will be available under `http://localhost:8000/<service_prefix>/`. Check `nginx.conf` in `docker-compose.yml` for routing rules.

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
