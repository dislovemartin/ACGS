# ACGS-PGP Kubernetes Production Deployment Guide

This guide provides step-by-step instructions for deploying ACGS-PGP to Kubernetes with integrated monitoring, load balancing, and security features for production environments.

## Prerequisites

### Cluster Requirements
- **Kubernetes:** Version 1.21+ with RBAC enabled
- **kubectl:** Configured to access your cluster
- **Helm:** Version 3.0+ for monitoring stack deployment
- **Ingress Controller:** Nginx, Traefik, or cloud provider ingress
- **Storage Class:** For persistent volumes (PostgreSQL, Prometheus, Grafana)

### Resource Requirements
- **Minimum:** 8 CPU cores, 16GB RAM, 100GB storage
- **Recommended:** 16 CPU cores, 32GB RAM, 500GB storage
- **High Availability:** 3+ worker nodes with anti-affinity rules

## Step 1: Namespace and RBAC Setup

```bash
# Create namespace
kubectl create namespace acgs-pgp

# Create service account with appropriate permissions
kubectl apply -f k8s/rbac/
```

## Step 2: Secrets and ConfigMaps

### Database Secrets
```bash
kubectl create secret generic postgres-credentials \
  --from-literal=user=acgs_user \
  --from-literal=password=secure_production_password \
  --from-literal=database_url=postgresql+asyncpg://acgs_user:secure_production_password@postgres-service:5432/acgs_pgp_db \
  -n acgs-pgp
```

### Authentication Secrets
```bash
kubectl create secret generic auth-secrets \
  --from-literal=jwt_secret_key=your_256_bit_jwt_secret_key \
  --from-literal=csrf_secret_key=your_256_bit_csrf_secret_key \
  --from-literal=algorithm=HS256 \
  -n acgs-pgp
```

### LLM Integration Secrets
```bash
kubectl create secret generic llm-secrets \
  --from-literal=openai_api_key=your_openai_api_key \
  --from-literal=openai_model=gpt-4 \
  -n acgs-pgp
```

### PGP Cryptographic Secrets
```bash
kubectl create secret generic pgp-secrets \
  --from-literal=pgp_key_id=your_pgp_key_id \
  --from-literal=pgp_passphrase=your_pgp_passphrase \
  --from-file=pgp_private_key=./keys/private.asc \
  --from-file=pgp_public_key=./keys/public.asc \
  -n acgs-pgp
```

### Application ConfigMap
```bash
kubectl create configmap acgs-config \
  --from-literal=environment=production \
  --from-literal=log_level=INFO \
  --from-literal=cors_origins=https://app.acgs-pgp.example.com,https://admin.acgs-pgp.example.com \
  --from-literal=z3_timeout_seconds=30 \
  --from-literal=z3_max_memory_mb=1024 \
  -n acgs-pgp
```

## Step 3: Deploy Monitoring Stack

### Prometheus Operator
```bash
# Add Prometheus community Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus Operator with custom values
helm install prometheus-operator prometheus-community/kube-prometheus-stack \
  --namespace acgs-pgp \
  --values k8s/monitoring/prometheus-values.yaml \
  --wait
```

### Custom ACGS-PGP Monitoring
```bash
# Deploy custom ServiceMonitors and PrometheusRules
kubectl apply -f k8s/monitoring/service-monitors.yaml
kubectl apply -f k8s/monitoring/prometheus-rules.yaml
kubectl apply -f k8s/monitoring/grafana-dashboards.yaml
```

## Step 4: Deploy Database

### PostgreSQL with High Availability
```bash
# Deploy PostgreSQL cluster
kubectl apply -f k8s/database/postgres-cluster.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s -n acgs-pgp

# Run database migrations
kubectl apply -f k8s/database/migration-job.yaml
kubectl wait --for=condition=complete job/alembic-migration --timeout=300s -n acgs-pgp
```

## Step 5: Deploy ACGS-PGP Services

### Core Services Deployment
```bash
# Deploy services in dependency order
kubectl apply -f k8s/services/auth-service.yaml
kubectl apply -f k8s/services/ac-service.yaml
kubectl apply -f k8s/services/integrity-service.yaml
kubectl apply -f k8s/services/fv-service.yaml
kubectl apply -f k8s/services/gs-service.yaml
kubectl apply -f k8s/services/pgc-service.yaml

# Wait for all services to be ready
kubectl wait --for=condition=available deployment --all --timeout=600s -n acgs-pgp
```

### Load Balancer and Ingress
```bash
# Deploy Nginx load balancer
kubectl apply -f k8s/ingress/nginx-configmap.yaml
kubectl apply -f k8s/ingress/nginx-deployment.yaml

# Deploy ingress with SSL termination
kubectl apply -f k8s/ingress/acgs-ingress.yaml
```

## Step 6: Deploy Frontend

```bash
# Deploy React frontend
kubectl apply -f k8s/frontend/frontend-deployment.yaml

# Configure frontend ingress
kubectl apply -f k8s/frontend/frontend-ingress.yaml
```

## Step 7: Validation and Testing

### Health Check Validation
```bash
# Check all pods are running
kubectl get pods -n acgs-pgp

# Verify service health endpoints
kubectl port-forward svc/nginx-service 8080:80 -n acgs-pgp &
for service in auth ac integrity fv gs pgc; do
  echo "Checking $service health..."
  curl -f http://localhost:8080/api/$service/health
done
```

### Monitoring Validation
```bash
# Access Grafana dashboard
kubectl port-forward svc/prometheus-operator-grafana 3000:80 -n acgs-pgp &
echo "Grafana available at http://localhost:3000"
echo "Username: admin"
kubectl get secret prometheus-operator-grafana -o jsonpath="{.data.admin-password}" -n acgs-pgp | base64 --decode

# Check Prometheus targets
kubectl port-forward svc/prometheus-operator-kube-p-prometheus 9090:9090 -n acgs-pgp &
echo "Prometheus available at http://localhost:9090"
```

### Load Testing
```bash
# Run production load test
kubectl apply -f k8s/testing/load-test-job.yaml
kubectl logs -f job/acgs-load-test -n acgs-pgp
```

## Step 8: Production Configuration

### Horizontal Pod Autoscaler
```bash
# Deploy HPA for auto-scaling
kubectl apply -f k8s/autoscaling/hpa.yaml

# Verify HPA status
kubectl get hpa -n acgs-pgp
```

### Network Policies
```bash
# Apply network security policies
kubectl apply -f k8s/security/network-policies.yaml
```

### Backup Configuration
```bash
# Deploy backup CronJobs
kubectl apply -f k8s/backup/postgres-backup.yaml
kubectl apply -f k8s/backup/monitoring-backup.yaml
```

## Production Monitoring Targets

### Performance Metrics
- **API Response Times:** <200ms (95th percentile)
- **Service Uptime:** >99.5% availability
- **Pod CPU Usage:** <70% average
- **Pod Memory Usage:** <80% average
- **Database Connections:** <80% of max pool size

### Alerting Rules
- **Service Down:** Alert if any service is down for >2 minutes
- **High Error Rate:** Alert if error rate >5% for >5 minutes
- **High Response Time:** Alert if 95th percentile >500ms for >5 minutes
- **Database Issues:** Alert on connection failures or slow queries
- **Resource Exhaustion:** Alert on high CPU/memory usage

## Troubleshooting

### Common Issues
1. **Pod Startup Failures:** Check resource limits and secrets
2. **Service Discovery Issues:** Verify DNS and service configurations
3. **Database Connection Errors:** Check credentials and network policies
4. **Monitoring Not Working:** Verify ServiceMonitor configurations

### Debugging Commands
```bash
# Check pod logs
kubectl logs -f deployment/auth-service -n acgs-pgp

# Describe pod for events
kubectl describe pod <pod-name> -n acgs-pgp

# Check service endpoints
kubectl get endpoints -n acgs-pgp

# Test service connectivity
kubectl run debug --image=busybox -it --rm --restart=Never -n acgs-pgp -- sh
```

## Security Considerations

### Network Security
- All inter-service communication within cluster
- Network policies restrict unnecessary traffic
- Ingress with SSL/TLS termination
- No direct database access from outside cluster

### Secret Management
- All sensitive data stored in Kubernetes secrets
- Secrets mounted as volumes, not environment variables
- Regular secret rotation procedures
- Integration with external secret management systems

### RBAC and Access Control
- Least privilege service accounts
- Role-based access control for kubectl access
- Audit logging enabled
- Regular security assessments

## Maintenance Procedures

### Rolling Updates
```bash
# Update service image
kubectl set image deployment/auth-service auth-service=new-image:tag -n acgs-pgp

# Monitor rollout
kubectl rollout status deployment/auth-service -n acgs-pgp
```

### Database Maintenance
```bash
# Run database migrations
kubectl create job --from=cronjob/postgres-backup manual-backup -n acgs-pgp
kubectl apply -f k8s/database/migration-job.yaml
```

### Monitoring Maintenance
```bash
# Update Grafana dashboards
kubectl apply -f k8s/monitoring/grafana-dashboards.yaml

# Reload Prometheus configuration
kubectl annotate prometheus prometheus-operator-kube-p-prometheus prometheus.io/reload=true -n acgs-pgp
```
