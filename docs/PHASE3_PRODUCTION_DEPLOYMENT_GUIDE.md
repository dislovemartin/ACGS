# Phase 3 Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying ACGS Phase 3 to production with performance optimization and security compliance features.

## Prerequisites

### System Requirements
- **CPU**: 8+ cores (16+ recommended for high load)
- **Memory**: 16GB+ RAM (32GB+ recommended)
- **Storage**: 100GB+ SSD storage
- **Network**: 1Gbps+ network connectivity
- **OS**: Ubuntu 20.04+ or CentOS 8+

### Software Dependencies
- Docker 24.0+
- Docker Compose 2.20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7.0+
- Nginx 1.20+

## Pre-Deployment Checklist

### 1. Environment Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Security Configuration
```bash
# Generate secure secrets
openssl rand -hex 32 > /etc/acgs/jwt_secret
openssl rand -hex 32 > /etc/acgs/db_password
openssl rand -hex 32 > /etc/acgs/redis_password

# Set proper permissions
sudo chmod 600 /etc/acgs/*
sudo chown acgs:acgs /etc/acgs/*
```

### 3. SSL/TLS Certificates
```bash
# Generate SSL certificates (use Let's Encrypt for production)
sudo certbot certonly --nginx -d your-domain.com
```

## Production Deployment Steps

### Step 1: Clone and Configure Repository
```bash
# Clone repository
git clone https://github.com/your-org/ACGS-master.git
cd ACGS-master

# Checkout production branch
git checkout production

# Copy production configuration
cp config/env/production.env.example config/env/production.env
```

### Step 2: Configure Environment Variables
Edit `config/env/production.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql://acgs_user:$(cat /etc/acgs/db_password)@postgres:5432/acgs_prod
REDIS_URL=redis://:$(cat /etc/acgs/redis_password)@redis:6379/0

# Security Configuration
JWT_SECRET_KEY=$(cat /etc/acgs/jwt_secret)
SECURITY_RATE_LIMIT_REQUESTS=100
SECURITY_RATE_LIMIT_WINDOW_MINUTES=1

# Performance Configuration
PERFORMANCE_MAX_POLICY_DECISION_LATENCY_MS=50
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
CACHE_MAX_SIZE=10000

# Monitoring Configuration
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=$(cat /etc/acgs/grafana_password)

# Service URLs
AC_SERVICE_URL=http://ac_service:8001
INTEGRITY_SERVICE_URL=http://integrity_service:8002
FV_SERVICE_URL=http://fv_service:8003
GS_SERVICE_URL=http://gs_service:8004
PGC_SERVICE_URL=http://pgc_service:8005
```

### Step 3: Deploy Infrastructure Services
```bash
# Deploy database and cache
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Wait for services to be ready
./scripts/wait-for-services.sh postgres:5432 redis:6379

# Run database migrations
docker-compose -f docker-compose.prod.yml exec postgres psql -U acgs_user -d acgs_prod -f /migrations/production_schema.sql
```

### Step 4: Deploy ACGS Services
```bash
# Deploy all ACGS services
docker-compose -f docker-compose.prod.yml up -d

# Verify service health
./scripts/validate_production_deployment.sh
```

### Step 5: Deploy Monitoring Stack
```bash
# Deploy monitoring services
docker-compose -f docker-compose-monitoring.yml up -d

# Configure Grafana dashboards
./scripts/setup_grafana_dashboards.sh

# Verify monitoring endpoints
curl http://localhost:9090/api/v1/targets  # Prometheus
curl http://localhost:3002/api/health      # Grafana
```

### Step 6: Configure Load Balancer
```bash
# Configure Nginx load balancer
sudo cp config/nginx/production.conf /etc/nginx/sites-available/acgs-prod
sudo ln -s /etc/nginx/sites-available/acgs-prod /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Performance Optimization

### 1. Database Optimization
```sql
-- Apply production database optimizations
\i config/database/production_optimizations.sql

-- Configure connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET work_mem = '64MB';
```

### 2. Cache Configuration
```bash
# Configure Redis for production
echo "maxmemory 8gb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
sudo systemctl restart redis
```

### 3. Application Tuning
```bash
# Set production environment variables
export WORKERS_PER_CORE=2
export MAX_WORKERS=16
export WEB_CONCURRENCY=8
export WORKER_TIMEOUT=120
```

## Security Hardening

### 1. Network Security
```bash
# Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 9090/tcp  # Prometheus (internal only)
sudo ufw allow 3002/tcp  # Grafana (internal only)
```

### 2. Application Security
```bash
# Enable security headers
export SECURITY_HEADERS_ENABLED=true
export CORS_ORIGINS="https://your-domain.com"
export CSRF_PROTECTION_ENABLED=true

# Configure rate limiting
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_REQUESTS=100
export RATE_LIMIT_WINDOW=60
```

### 3. SSL/TLS Configuration
```nginx
# Nginx SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
add_header Strict-Transport-Security "max-age=63072000" always;
```

## Monitoring and Alerting

### 1. Prometheus Configuration
```yaml
# Add production alert rules
groups:
- name: production_alerts
  rules:
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(acgs_policy_decision_duration_seconds_bucket[5m])) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High policy decision latency detected"
```

### 2. Grafana Dashboards
```bash
# Import production dashboards
curl -X POST \
  http://admin:$(cat /etc/acgs/grafana_password)@localhost:3002/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @config/monitoring/grafana/dashboards/production-overview.json
```

### 3. Log Management
```bash
# Configure centralized logging
docker-compose -f docker-compose.logging.yml up -d elasticsearch kibana logstash

# Configure log rotation
echo "/var/log/acgs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 acgs acgs
}" > /etc/logrotate.d/acgs
```

## Health Checks and Validation

### 1. Service Health Validation
```bash
#!/bin/bash
# Health check script
services=("ac_service:8001" "integrity_service:8002" "fv_service:8003" "gs_service:8004" "pgc_service:8005")

for service in "${services[@]}"; do
    if curl -f http://$service/health > /dev/null 2>&1; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is unhealthy"
        exit 1
    fi
done
```

### 2. Performance Validation
```bash
# Run performance tests
python scripts/phase3_load_testing.py --production-mode

# Validate latency targets
if [ $(curl -s http://localhost:8004/api/v1/performance/metrics | jq '.latency_p95_ms') -lt 50 ]; then
    echo "✅ Latency target met"
else
    echo "❌ Latency target exceeded"
fi
```

### 3. Security Validation
```bash
# Run security tests
python scripts/phase3_security_penetration_testing.py --production-mode

# Validate security compliance
./scripts/security_compliance_check.sh
```

## Backup and Recovery

### 1. Database Backup
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/acgs/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h postgres -U acgs_user acgs_prod | gzip > $BACKUP_DIR/database.sql.gz

# Configuration backup
tar -czf $BACKUP_DIR/config.tar.gz config/

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR s3://acgs-backups/$(date +%Y%m%d)/ --recursive
```

### 2. Disaster Recovery
```bash
# Recovery procedure
#!/bin/bash
RESTORE_DATE=$1

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore database
gunzip -c /backups/acgs/$RESTORE_DATE/database.sql.gz | psql -h postgres -U acgs_user acgs_prod

# Restore configuration
tar -xzf /backups/acgs/$RESTORE_DATE/config.tar.gz

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage
```bash
# Check memory usage
docker stats

# Optimize JVM settings
export JAVA_OPTS="-Xmx4g -Xms2g -XX:+UseG1GC"
```

#### 2. Database Connection Issues
```bash
# Check connection pool
docker-compose exec postgres psql -U acgs_user -c "SELECT * FROM pg_stat_activity;"

# Increase connection limit
docker-compose exec postgres psql -U acgs_user -c "ALTER SYSTEM SET max_connections = 300;"
```

#### 3. Cache Performance Issues
```bash
# Check Redis memory usage
docker-compose exec redis redis-cli info memory

# Clear cache if needed
docker-compose exec redis redis-cli flushall
```

## Maintenance Procedures

### 1. Rolling Updates
```bash
# Zero-downtime deployment
./scripts/rolling_update.sh --version=v1.2.3
```

### 2. Scaling
```bash
# Scale services horizontally
docker-compose -f docker-compose.prod.yml up -d --scale gs_service=3
```

### 3. Monitoring Maintenance
```bash
# Update monitoring configuration
docker-compose -f docker-compose-monitoring.yml restart prometheus grafana
```

## Support and Escalation

### Contact Information
- **Production Issues**: production-support@acgs.com
- **Security Incidents**: security@acgs.com
- **Emergency Escalation**: +1-555-ACGS-911

### Documentation Links
- [API Documentation](./api/README.md)
- [Architecture Guide](./architecture.md)
- [Security Documentation](./security.md)
- [Troubleshooting Guide](./troubleshooting.md)
