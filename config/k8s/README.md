# Kubernetes Configuration for ACGS-PGP

This directory contains Kubernetes manifest files for deploying the AI Compliance Governance System - Policy Generation Platform and its services.

## Overview

The deployment is structured with separate YAML files for each microservice, including:
-   `Deployment` objects to manage pod replicas.
-   `Service` objects to expose services internally within the cluster or externally.

Common configurations like database credentials or shared secrets would typically be managed using Kubernetes `Secret` objects (not included here for brevity, but referenced in deployments). Configurable application settings might use `ConfigMap` objects.

## Files

-   `ac-service.yaml`: Deployment and Service for the Audit & Compliance Service.
-   `auth-service.yaml`: Deployment and Service for the Authentication Service.
-   `fv-service.yaml`: Deployment and Service for the Formal Verification Service.
-   `gs-service.yaml`: Deployment and Service for the Governance Structure Service.
-   `integrity-service.yaml`: Deployment and Service for the Data Integrity Service.
-   `pgc-service.yaml`: Deployment and Service for the Policy Generation & Customization Service.
-   `frontend-deployment.yaml`: Deployment and Service for the Frontend (React) application.
-   `postgres-deployment.yaml`: Deployment for PostgreSQL database (example, consider a managed DB in production).
-   `postgres-service.yaml`: Service for PostgreSQL database.
-   `deployment.yaml`: A generic placeholder deployment file. Individual service files are preferred.
-   `service.yaml`: A generic placeholder service file. (Likely to be removed or replaced by an Ingress controller or API Gateway setup in a more complex deployment).

## Prerequisites

-   A running Kubernetes cluster.
-   `kubectl` configured to communicate with your cluster.
-   Docker images for each service pushed to a container registry accessible by your cluster (e.g., Docker Hub, GCR, ECR). Remember to replace placeholder image names like `yourdockerhubusername/service-name:latest` in the YAML files with your actual image paths.
-   Necessary `Secret` objects created in your cluster for sensitive data (e.g., `postgres-credentials` for database username/password, `auth-secrets` for JWT secret keys). Example secret creation (replace with your actual values):
    ```bash
    kubectl create secret generic postgres-credentials \
      --from-literal=user='yourdbuser' \
      --from-literal=password='yourdbpassword' \
      --from-literal=database_url='postgresql://yourdbuser:yourdbpassword@postgres-service:5432/acgs_db'
    
    kubectl create secret generic auth-secrets \
      --from-literal=secret_key='yourjwtsecretkey'
    ```
-  A `ConfigMap` for non-sensitive PostgreSQL configuration:
    ```bash
    kubectl create configmap postgres-config --from-literal=db_name='acgs_db'
    ```
- (If using `postgres-deployment.yaml` with PVC) A `PersistentVolumeClaim` (PVC) named `postgres-pvc` and a `PersistentVolume` (PV) available, or a default `StorageClass` that can dynamically provision PVs.

## Deployment Steps

1.  **Apply Secrets and ConfigMaps:**
    Ensure all required secrets (like `postgres-credentials`, `auth-secrets`) and configmaps (`postgres-config`) are created in your Kubernetes cluster first.

2.  **Deploy PostgreSQL (if using the provided example):**
    ```bash
    kubectl apply -f postgres-deployment.yaml
    kubectl apply -f postgres-service.yaml
    ```
    Wait for PostgreSQL to be up and running.

3.  **Deploy Backend Services:**
    Apply the deployment and service YAML files for each backend microservice:
    ```bash
    kubectl apply -f auth-service.yaml
    kubectl apply -f ac-service.yaml
    kubectl apply -f integrity-service.yaml
    kubectl apply -f fv-service.yaml
    kubectl apply -f gs-service.yaml
    kubectl apply -f pgc-service.yaml
    # ... and any other backend services
    ```

4.  **Deploy Frontend:**
    ```bash
    kubectl apply -f frontend-deployment.yaml
    ```

5.  **Verify Deployments:**
    Check the status of your pods, deployments, and services:
    ```bash
    kubectl get pods
    kubectl get deployments
    kubectl get services
    ```
    View logs for a specific pod:
    ```bash
    kubectl logs <pod-name>
    # e.g. kubectl logs auth-service-deployment-xxxxxxxxx-yyyyy
    ```

6.  **Accessing the Application:**
    -   Backend services are typically exposed as `ClusterIP` and accessed by other services within the cluster using their service name (e.g., `http://auth-service:8000`).
    -   The Frontend service might be of type `LoadBalancer` or `NodePort` for external access, or accessed via an Ingress controller. If using `LoadBalancer`, find its external IP: `kubectl get service frontend-service`.

## Notes

-   **Image Paths:** Remember to replace placeholder image paths (e.g., `yourdockerhubusername/...`) in the deployment YAMLs with your actual image paths from your container registry.
-   **Resource Limits & Requests:** For production, add CPU and memory requests and limits to your container specs in the deployment files to ensure stable performance and resource allocation.
-   **Configuration Management:** Consider using tools like Helm or Kustomize for more advanced configuration management and templating of your Kubernetes manifests, especially as the project grows.
-   **Ingress/API Gateway:** For managing external access to multiple services, an Ingress controller or an API Gateway is recommended instead of exposing each service with a `LoadBalancer`.
-   **Persistent Storage for PostgreSQL:** The example `postgres-deployment.yaml` references a PVC. Ensure you have appropriate PVs and StorageClasses configured in your cluster, or use a managed database service from your cloud provider for production.
