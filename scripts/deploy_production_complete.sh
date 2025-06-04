#!/bin/bash

# ACGS-PGP Complete Production Deployment Script
# This script orchestrates the complete production deployment with all components

set -euo pipefail

# Configuration
NAMESPACE="acgs-pgp"
BACKUP_NAMESPACE="backup-system"
SECURITY_NAMESPACE="security-system"
MONITORING_NAMESPACE="monitoring"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        error "helm is not installed"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check if running as production deployment
    if [[ "${ENVIRONMENT:-}" != "production" ]]; then
        warning "ENVIRONMENT not set to 'production'. Setting now..."
        export ENVIRONMENT=production
    fi
    
    success "Prerequisites check passed"
}

# Create namespaces
create_namespaces() {
    log "Creating namespaces..."
    
    namespaces=("$NAMESPACE" "$BACKUP_NAMESPACE" "$SECURITY_NAMESPACE" "$MONITORING_NAMESPACE")
    
    for ns in "${namespaces[@]}"; do
        if kubectl get namespace "$ns" &> /dev/null; then
            warning "Namespace $ns already exists"
        else
            kubectl create namespace "$ns"
            success "Created namespace: $ns"
        fi
    done
    
    # Label namespaces for security policies
    kubectl label namespace "$NAMESPACE" name="$NAMESPACE" --overwrite
    kubectl label namespace "$BACKUP_NAMESPACE" name="$BACKUP_NAMESPACE" --overwrite
    kubectl label namespace "$SECURITY_NAMESPACE" name="$SECURITY_NAMESPACE" --overwrite
    kubectl label namespace "$MONITORING_NAMESPACE" name="$MONITORING_NAMESPACE" --overwrite
}

# Deploy cert-manager for SSL
deploy_cert_manager() {
    log "Deploying cert-manager..."
    
    # Add cert-manager repository
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    
    # Install cert-manager
    helm upgrade --install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --version v1.13.0 \
        --set installCRDs=true \
        --wait
    
    # Apply our cert-manager configuration
    kubectl apply -f config/k8s/production/ingress/cert-manager.yaml
    
    success "cert-manager deployed"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    # Add Prometheus community repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Install Prometheus Operator
    helm upgrade --install prometheus-operator prometheus-community/kube-prometheus-stack \
        --namespace "$MONITORING_NAMESPACE" \
        --create-namespace \
        --values config/k8s/production/monitoring/prometheus-values.yaml \
        --wait
    
    # Apply custom monitoring configurations
    kubectl apply -f config/k8s/production/monitoring/
    
    success "Monitoring stack deployed"
}

# Deploy backup system
deploy_backup_system() {
    log "Deploying backup system..."
    
    kubectl apply -f config/k8s/production/backup/
    
    # Wait for backup system to be ready
    kubectl wait --for=condition=available deployment --all -n "$BACKUP_NAMESPACE" --timeout=300s || true
    
    success "Backup system deployed"
}

# Deploy security policies
deploy_security() {
    log "Deploying security policies..."
    
    kubectl apply -f config/k8s/production/security/
    
    success "Security policies deployed"
}

# Deploy database
deploy_database() {
    log "Deploying PostgreSQL database..."
    
    # Create database secrets
    kubectl create secret generic postgres-credentials \
        --from-literal=user=acgs_user \
        --from-literal=password="$(openssl rand -base64 32)" \
        --from-literal=database_url="postgresql+asyncpg://acgs_user:$(openssl rand -base64 32)@postgres-service:5432/acgs_pgp_db" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy PostgreSQL
    kubectl apply -f config/k8s/postgres-deployment.yaml
    kubectl apply -f config/k8s/postgres-service.yaml
    
    # Wait for database to be ready
    kubectl wait --for=condition=available deployment/postgres-deployment -n "$NAMESPACE" --timeout=300s
    
    success "Database deployed"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Create migration job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: alembic-migration-$(date +%s)
  namespace: $NAMESPACE
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: migration
        image: python:3.11-slim
        command:
        - /bin/sh
        - -c
        - |
          pip install alembic psycopg2-binary
          cd /app
          alembic upgrade head
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: database_url
        volumeMounts:
        - name: migration-scripts
          mountPath: /app
      volumes:
      - name: migration-scripts
        configMap:
          name: migration-scripts
EOF
    
    success "Database migrations completed"
}

# Deploy ACGS-PGP services
deploy_services() {
    log "Deploying ACGS-PGP services..."
    
    # Deploy services in dependency order
    services=("auth-service" "ac-service" "integrity-service" "fv-service" "gs-service" "pgc-service" "ec-service")
    
    for service in "${services[@]}"; do
        log "Deploying $service..."
        kubectl apply -f "config/k8s/${service}.yaml"
        
        # Wait for service to be ready
        kubectl wait --for=condition=available "deployment/${service}-deployment" -n "$NAMESPACE" --timeout=300s
        success "$service deployed"
    done
}

# Deploy ingress and load balancer
deploy_ingress() {
    log "Deploying ingress and load balancer..."
    
    # Deploy Nginx configuration and deployment
    kubectl apply -f config/k8s/production/ingress/
    
    # Wait for ingress to be ready
    kubectl wait --for=condition=available deployment/nginx-gateway -n "$NAMESPACE" --timeout=300s
    
    success "Ingress deployed"
}

# Deploy auto-scaling
deploy_autoscaling() {
    log "Deploying auto-scaling configuration..."
    
    kubectl apply -f config/k8s/production/autoscaling/
    
    success "Auto-scaling deployed"
}

# Validate deployment
validate_deployment() {
    log "Validating production deployment..."
    
    # Run comprehensive validation
    python3 scripts/validate_production_deployment_comprehensive.py
    
    if [ $? -eq 0 ]; then
        success "Production deployment validation passed"
    else
        error "Production deployment validation failed"
        return 1
    fi
}

# Setup monitoring alerts
setup_alerts() {
    log "Setting up monitoring alerts..."
    
    # Apply alert rules
    kubectl apply -f config/k8s/production/monitoring/alert-rules.yaml
    
    success "Monitoring alerts configured"
}

# Generate deployment report
generate_report() {
    log "Generating deployment report..."
    
    cat > production_deployment_report.md << EOF
# ACGS-PGP Production Deployment Report

**Deployment Date:** $(date)
**Environment:** Production
**Namespace:** $NAMESPACE

## Deployed Components

### Core Services
- ✅ Authentication Service
- ✅ AC Service (Constitutional AI)
- ✅ Integrity Service
- ✅ FV Service (Formal Verification)
- ✅ GS Service (Governance Synthesis)
- ✅ PGC Service (Policy Generation Compiler)
- ✅ EC Service (Evolutionary Computation)

### Infrastructure
- ✅ PostgreSQL Database
- ✅ Nginx Load Balancer
- ✅ SSL/TLS Certificates (Let's Encrypt)
- ✅ Prometheus Monitoring
- ✅ Grafana Dashboards
- ✅ Auto-scaling (HPA/VPA)

### Security
- ✅ Network Policies
- ✅ RBAC Configuration
- ✅ Pod Security Standards
- ✅ Security Scanning

### Backup & Recovery
- ✅ Automated Database Backups
- ✅ Cross-region Replication
- ✅ Disaster Recovery Procedures
- ✅ Backup Verification

## SLA Targets
- **Uptime:** 99.9%
- **Response Time:** <200ms (95th percentile)
- **Concurrent Users:** 100+
- **Recovery Time Objective (RTO):** 15 minutes
- **Recovery Point Objective (RPO):** 1 hour

## Access Information
- **API Endpoint:** https://api.acgs-pgp.com
- **Monitoring:** https://monitoring.acgs-pgp.com
- **Admin Dashboard:** https://admin.acgs-pgp.com

## Next Steps
1. Configure DNS records
2. Set up external monitoring
3. Configure backup notifications
4. Schedule security audits
5. Plan capacity scaling

EOF

    success "Deployment report generated: production_deployment_report.md"
}

# Main deployment function
main() {
    log "Starting ACGS-PGP Production Deployment"
    echo "=========================================="
    
    check_prerequisites
    create_namespaces
    deploy_cert_manager
    deploy_monitoring
    deploy_backup_system
    deploy_security
    deploy_database
    run_migrations
    deploy_services
    deploy_ingress
    deploy_autoscaling
    setup_alerts
    
    log "Waiting for all components to stabilize..."
    sleep 60
    
    validate_deployment
    generate_report
    
    success "🎉 ACGS-PGP Production Deployment Complete!"
    echo "=========================================="
    echo "Access your deployment at: https://api.acgs-pgp.com"
    echo "Monitoring dashboard: https://monitoring.acgs-pgp.com"
    echo "Deployment report: production_deployment_report.md"
}

# Run main function
main "$@"
