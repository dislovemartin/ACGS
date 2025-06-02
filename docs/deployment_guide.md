# ACGS-PGP Deployment Guide

## 🎯 Overview

This guide provides comprehensive deployment instructions for the **ACGS-PGP (AI Compliance Governance System - Policy Generation Platform)** across development, staging, and production environments.

## 🏗️ System Requirements

### **Minimum Requirements**
- **CPU**: 4 cores (8 recommended)
- **RAM**: 8GB (16GB recommended)
- **Storage**: 50GB SSD (100GB recommended)
- **Network**: 1Gbps connection
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Docker-compatible Linux

### **Production Requirements**
- **CPU**: 16+ cores with AVX2 support
- **RAM**: 32GB+ (64GB for high-load scenarios)
- **Storage**: 500GB+ NVMe SSD with backup
- **Network**: 10Gbps connection with redundancy
- **Load Balancer**: Nginx/HAProxy with SSL termination

## 🐳 Docker Deployment

### **Prerequisites**
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### **Environment Setup**
```bash
# Clone repository
git clone https://github.com/dislovemartin/ACGS.git
cd ACGS-master

# Copy environment configuration
cp config/env/.env.example config/env/.env

# Configure environment variables (see Environment Configuration section)
nano config/env/.env
```

### **Development Deployment**
```bash
# Navigate to Docker configuration
cd config/docker

# Start all services
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs -f --tail=50

# Run database migrations
docker-compose exec auth_service alembic upgrade head
docker-compose exec ac_service alembic upgrade head
docker-compose exec integrity_service alembic upgrade head
docker-compose exec fv_service alembic upgrade head
docker-compose exec gs_service alembic upgrade head
docker-compose exec pgc_service alembic upgrade head

# Seed test data
docker-compose exec auth_service python scripts/seed_test_data.py
```

### **Production Deployment**
```bash
# Use production Docker Compose configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Deploy monitoring stack
./scripts/deploy_monitoring.sh

# Configure SSL certificates (Let's Encrypt)
./scripts/setup_ssl.sh your-domain.com

# Run health checks
./scripts/health_check_all_services.sh

# Load test deployment
./scripts/load_test_monitoring.sh 100 300
```

## ☸️ Kubernetes Deployment

### **Prerequisites**
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

### **Cluster Setup**
```bash
# Create namespace
kubectl create namespace acgs-pgp

# Apply ConfigMaps and Secrets
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/

# Deploy PostgreSQL with persistent storage
kubectl apply -f k8s/postgres/

# Deploy Redis cluster
kubectl apply -f k8s/redis/

# Deploy core services
kubectl apply -f k8s/services/

# Deploy ingress controller
kubectl apply -f k8s/ingress/

# Verify deployment
kubectl get pods -n acgs-pgp
kubectl get services -n acgs-pgp
kubectl get ingress -n acgs-pgp
```

### **Helm Chart Deployment**
```bash
# Add ACGS-PGP Helm repository
helm repo add acgs-pgp ./helm/acgs-pgp
helm repo update

# Install with custom values
helm install acgs-pgp acgs-pgp/acgs-pgp \
  --namespace acgs-pgp \
  --values helm/values-production.yaml \
  --set global.environment=production \
  --set global.domain=your-domain.com

# Upgrade deployment
helm upgrade acgs-pgp acgs-pgp/acgs-pgp \
  --namespace acgs-pgp \
  --values helm/values-production.yaml

# Monitor deployment
helm status acgs-pgp -n acgs-pgp
kubectl logs -f deployment/auth-service -n acgs-pgp
```

## 🔧 Environment Configuration

### **Core Configuration**
```bash
# Project Settings
PROJECT_NAME="ACGS-PGP"
ENVIRONMENT="production"  # development, staging, production
VERSION="1.0.0"

# Database Configuration
DATABASE_URL="postgresql+asyncpg://acgs_user:secure_password@postgres-cluster:5432/acgs_pgp_db"
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Service Ports
AUTH_SERVICE_PORT=8000
AC_SERVICE_PORT=8001
INTEGRITY_SERVICE_PORT=8002
FV_SERVICE_PORT=8003
GS_SERVICE_PORT=8004
PGC_SERVICE_PORT=8005
EC_SERVICE_PORT=8006
```

### **Security Configuration**
```bash
# JWT Configuration
AUTH_SERVICE_SECRET_KEY="your_production_jwt_secret_key_256_bits_minimum"
AUTH_SERVICE_ALGORITHM="HS256"
AUTH_SERVICE_ACCESS_TOKEN_EXPIRE_MINUTES=15
AUTH_SERVICE_REFRESH_TOKEN_EXPIRE_DAYS=7

# CSRF Protection
AUTH_SERVICE_CSRF_SECRET_KEY="your_production_csrf_secret_key_256_bits_minimum"
CSRF_TOKEN_EXPIRE_MINUTES=60

# CORS Configuration
BACKEND_CORS_ORIGINS="https://app.your-domain.com,https://admin.your-domain.com"

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=20
```

### **LLM Configuration**
```bash
# Primary LLM Provider
LLM_PROVIDER="openai"
OPENAI_API_KEY="your_production_openai_api_key"
OPENAI_MODEL_NAME="gpt-4"

# LLM Reliability
LLM_RELIABILITY_THRESHOLD=0.999
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SECONDS=30
LLM_FALLBACK_ENABLED=true

# Alternative Providers
GROQ_API_KEY="your_groq_api_key"
GEMINI_API_KEY="your_gemini_api_key"
```

### **Feature Configuration**
```bash
# Constitutional Framework
CONSTITUTIONAL_COUNCIL_ENABLED=true
AC_AMENDMENT_THRESHOLD=0.67
AC_VOTING_PERIOD_HOURS=168

# AlphaEvolve Integration
ALPHAEVOLVE_ENABLED=true
EVOLUTIONARY_COMPUTATION_ENABLED=true

# QEC Enhancement
QEC_ENABLED=true
QEC_FIDELITY_THRESHOLD=0.85

# WINA Optimization
WINA_ENABLED=true
WINA_GFLOPS_REDUCTION_TARGET=0.55
WINA_SYNTHESIS_ACCURACY_THRESHOLD=0.95

# Cryptographic Integrity
CRYPTOGRAPHIC_INTEGRITY_ENABLED=true
PGP_ASSURANCE_ENABLED=true
```

## 📊 Monitoring Setup

### **Prometheus Configuration**
```bash
# Deploy Prometheus
docker-compose -f monitoring/docker-compose.monitoring.yml up -d prometheus

# Configure scrape targets
cp monitoring/prometheus/prometheus.yml.example monitoring/prometheus/prometheus.yml

# Verify metrics collection
curl http://localhost:9090/api/v1/targets
```

### **Grafana Setup**
```bash
# Deploy Grafana
docker-compose -f monitoring/docker-compose.monitoring.yml up -d grafana

# Import dashboards
./scripts/import_grafana_dashboards.sh

# Access Grafana
# URL: http://localhost:3001
# Username: admin
# Password: admin123 (change in production)
```

### **AlertManager Configuration**
```bash
# Configure alert rules
cp monitoring/alertmanager/alertmanager.yml.example monitoring/alertmanager/alertmanager.yml

# Set up notification channels (Slack, email, etc.)
nano monitoring/alertmanager/alertmanager.yml

# Deploy AlertManager
docker-compose -f monitoring/docker-compose.monitoring.yml up -d alertmanager
```

## 🔒 Security Hardening

### **SSL/TLS Configuration**
```bash
# Generate SSL certificates (Let's Encrypt)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Configure SSL in Nginx
cp config/nginx/nginx.conf.ssl.example config/nginx/nginx.conf

# Test SSL configuration
sudo nginx -t
sudo systemctl reload nginx

# Verify SSL rating
curl -I https://your-domain.com
```

### **Firewall Configuration**
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 9090/tcp  # Prometheus (restrict to monitoring network)
sudo ufw allow 3001/tcp  # Grafana (restrict to admin network)

# Verify firewall status
sudo ufw status verbose
```

### **Database Security**
```bash
# Configure PostgreSQL security
sudo -u postgres psql -c "ALTER USER acgs_user PASSWORD 'secure_random_password';"
sudo -u postgres psql -c "REVOKE ALL ON SCHEMA public FROM PUBLIC;"
sudo -u postgres psql -c "GRANT ALL ON SCHEMA public TO acgs_user;"

# Enable SSL for database connections
echo "ssl = on" >> /etc/postgresql/13/main/postgresql.conf
echo "ssl_cert_file = '/etc/ssl/certs/server.crt'" >> /etc/postgresql/13/main/postgresql.conf
echo "ssl_key_file = '/etc/ssl/private/server.key'" >> /etc/postgresql/13/main/postgresql.conf

sudo systemctl restart postgresql
```

## 🧪 Testing Deployment

### **Health Checks**
```bash
# Run comprehensive health checks
./scripts/health_check_all_services.sh

# Test individual services
curl http://localhost:8000/health  # Auth Service
curl http://localhost:8001/health  # AC Service
curl http://localhost:8002/health  # Integrity Service
curl http://localhost:8003/health  # FV Service
curl http://localhost:8004/health  # GS Service
curl http://localhost:8005/health  # PGC Service
curl http://localhost:8006/health  # EC Service
```

### **Integration Testing**
```bash
# Run integration test suite
./scripts/run_integration_tests.sh

# Test authentication flow
./scripts/test_auth_flow.sh

# Test policy synthesis pipeline
./scripts/test_policy_pipeline.sh

# Test Constitutional Council workflows
./scripts/test_constitutional_council.sh
```

### **Load Testing**
```bash
# Run load tests with different scenarios
./scripts/load_test_monitoring.sh 50 300   # 50 users, 5 minutes
./scripts/load_test_monitoring.sh 100 600  # 100 users, 10 minutes
./scripts/load_test_monitoring.sh 200 900  # 200 users, 15 minutes

# Monitor performance during load tests
watch -n 5 'curl -s http://localhost:9090/api/v1/query?query=rate(acgs_http_requests_total[5m])'
```

## 🔄 Backup and Recovery

### **Database Backup**
```bash
# Automated backup script
./scripts/backup_database.sh

# Manual backup
docker-compose exec postgres_db pg_dump -U acgs_user acgs_pgp_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker-compose exec -T postgres_db psql -U acgs_user acgs_pgp_db < backup_20240115_120000.sql
```

### **Configuration Backup**
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz config/ monitoring/ k8s/

# Backup Docker volumes
docker run --rm -v acgs_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_backup.tar.gz /data
```

## 📈 Performance Optimization

### **Database Optimization**
```bash
# Optimize PostgreSQL configuration
echo "shared_buffers = 256MB" >> /etc/postgresql/13/main/postgresql.conf
echo "effective_cache_size = 1GB" >> /etc/postgresql/13/main/postgresql.conf
echo "work_mem = 4MB" >> /etc/postgresql/13/main/postgresql.conf
echo "maintenance_work_mem = 64MB" >> /etc/postgresql/13/main/postgresql.conf

sudo systemctl restart postgresql
```

### **Application Optimization**
```bash
# Configure connection pooling
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=30
export DB_POOL_TIMEOUT=30

# Enable Redis caching
export REDIS_URL="redis://redis:6379/0"
export REDIS_MAX_CONNECTIONS=100

# Configure parallel processing
export PARALLEL_MAX_CONCURRENT=50
export PARALLEL_BATCH_SIZE=25
```

## 🚨 Troubleshooting

### **Common Issues**

1. **Service startup failures**
   ```bash
   # Check logs
   docker-compose logs service_name
   
   # Verify environment variables
   docker-compose exec service_name env | grep -E "(DATABASE|AUTH|LLM)"
   
   # Test database connectivity
   docker-compose exec service_name python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.execute('SELECT 1').scalar())"
   ```

2. **High response times**
   ```bash
   # Check database performance
   docker-compose exec postgres_db psql -U acgs_user -d acgs_pgp_db -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
   
   # Monitor resource usage
   docker stats
   
   # Check connection pools
   curl http://localhost:9090/api/v1/query?query=acgs_database_connections
   ```

3. **Authentication failures**
   ```bash
   # Verify JWT configuration
   docker-compose exec auth_service python -c "import jwt; print('JWT library working')"
   
   # Check CSRF token generation
   curl -X GET http://localhost:8000/auth/csrf-token -H "Authorization: Bearer valid_jwt_token"
   
   # Verify CORS settings
   curl -H "Origin: https://app.your-domain.com" -H "Access-Control-Request-Method: POST" -X OPTIONS http://localhost:8000/auth/login
   ```

### **Log Analysis**
```bash
# Centralized logging
docker-compose logs -f --tail=100 --timestamps

# Filter by service
docker-compose logs auth_service | grep ERROR

# Search for specific patterns
docker-compose logs | grep -E "(ERROR|CRITICAL|Exception)"

# Monitor real-time logs
tail -f /var/log/acgs-pgp/*.log
```

## 📞 Support

### **Documentation**
- [API Documentation](./production_api_documentation.md)
- [Architecture Guide](./architecture_documentation.md)
- [Security Guide](./security_documentation.md)
- [Troubleshooting Guide](./troubleshooting_guide.md)

### **Monitoring Dashboards**
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Health Checks**: http://localhost:8000/health

### **Emergency Contacts**
- **System Administrator**: admin@your-domain.com
- **DevOps Team**: devops@your-domain.com
- **Security Team**: security@your-domain.com

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Maintainer**: ACGS-PGP Development Team
