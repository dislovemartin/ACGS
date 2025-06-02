# QEC-Enhanced AlphaEvolve-ACGS Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the QEC (Quality, Error, and Correction) enhanced AlphaEvolve-ACGS system in production environments.

## Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended for production)
- **Memory**: 8GB RAM minimum (16GB+ recommended)
- **Storage**: 50GB available space
- **Network**: Stable internet connection for LLM API calls
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2

### Software Dependencies
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.9+
- **PostgreSQL**: 13+
- **Redis**: 6.0+ (for caching)
- **Nginx**: 1.18+ (for load balancing)

## Installation Steps

### 1. Clone and Setup Repository
```bash
git clone https://github.com/your-org/ACGS-master.git
cd ACGS-master

# Create environment file
cp .env.example .env
```

### 2. Configure Environment Variables
Edit `.env` file with your configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://acgs_user:secure_password@localhost:5434/acgs_db
POSTGRES_USER=acgs_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=acgs_db

# Service Ports
AC_SERVICE_PORT=8001
GS_SERVICE_PORT=8004
FV_SERVICE_PORT=8003
PGC_SERVICE_PORT=8005
INTEGRITY_SERVICE_PORT=8002
FRONTEND_PORT=8000

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GROQ_API_KEY=your_groq_api_key

# QEC Configuration
QEC_ENABLED=true
QEC_FIDELITY_THRESHOLD=0.85
QEC_ALERT_WEBHOOK_URL=https://your-monitoring-system.com/webhooks/alerts

# Redis Configuration (for QEC caching)
REDIS_URL=redis://localhost:6379/0

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
```

### 3. Initialize Database Schema
```bash
# Run Alembic migrations
cd src/backend/shared
alembic upgrade head

# Verify QEC enhancement tables
psql $DATABASE_URL -c "\dt qec_*"
```

### 4. Build and Deploy Services
```bash
# Build all services
docker-compose build

# Start core services
docker-compose up -d postgres redis

# Wait for database to be ready
sleep 10

# Start application services
docker-compose up -d ac_service gs_service fv_service pgc_service integrity_service

# Start monitoring stack
docker-compose up -d prometheus grafana

# Start frontend
docker-compose up -d frontend nginx
```

### 5. Verify Deployment
```bash
# Check service health
curl http://localhost:8001/health  # AC Service
curl http://localhost:8004/health  # GS Service
curl http://localhost:8003/health  # FV Service
curl http://localhost:8005/health  # PGC Service
curl http://localhost:8002/health  # Integrity Service

# Check QEC components
curl http://localhost:8001/api/v1/fidelity/current
```

## QEC Component Configuration

### Constitutional Distance Calculator
```yaml
# config/qec_distance_calculator.yaml
distance_calculator:
  weights:
    language_ambiguity: 0.3
    criteria_formality: 0.4
    historical_success: 0.3
  ambiguity_patterns:
    - "should"
    - "might"
    - "could"
    - "appropriate"
    - "reasonable"
  cache_ttl: 3600  # 1 hour
```

### Error Prediction Model
```yaml
# config/qec_error_prediction.yaml
error_prediction:
  retrain_interval: 100
  max_log_history: 10000
  prediction_cache_ttl: 3600
  confidence_threshold: 0.7
  feature_weights:
    description_complexity: 0.25
    ambiguity_score: 0.30
    historical_success: 0.25
    category_complexity: 0.20
```

### Recovery Strategy Dispatcher
```yaml
# config/qec_recovery_strategies.yaml
strategies:
  syntax_error:
    primary: "simplified_syntax_prompt"
    fallback: "decompose_principle"
    max_attempts: 2
    timeout_seconds: 30
  semantic_conflict:
    primary: "explicit_disambiguation"
    fallback: "human_clarification"
    max_attempts: 3
    timeout_seconds: 45
  complexity_high:
    primary: "decompose_principle"
    fallback: "human_clarification"
    max_attempts: 2
    timeout_seconds: 60
```

### Constitutional Fidelity Monitor
```yaml
# config/qec_fidelity_monitor.yaml
fidelity_monitor:
  calculation_interval_seconds: 300  # 5 minutes
  max_history_size: 1000
  weights:
    principle_coverage: 0.25
    synthesis_success: 0.20
    enforcement_reliability: 0.20
    adaptation_speed: 0.15
    stakeholder_satisfaction: 0.10
    appeal_frequency: 0.10
  thresholds:
    green: 0.85
    amber: 0.70
    red: 0.55
  alerts:
    webhook_url: "${QEC_ALERT_WEBHOOK_URL}"
    retry_attempts: 3
    retry_delay: 5
```

## Performance Optimization

### Database Optimization
```sql
-- Create indexes for QEC tables
CREATE INDEX CONCURRENTLY idx_qec_distance_calculations_principle_id 
ON qec_distance_calculations(principle_id);

CREATE INDEX CONCURRENTLY idx_qec_distance_calculations_calculated_at 
ON qec_distance_calculations(calculated_at);

CREATE INDEX CONCURRENTLY idx_qec_synthesis_logs_timestamp 
ON qec_synthesis_attempt_logs(timestamp);

-- Optimize PostgreSQL settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

### Redis Caching Configuration
```redis
# redis.conf optimizations
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Nginx Load Balancing
```nginx
# nginx.conf
upstream ac_service {
    server ac_service:8001;
    # Add more instances for scaling
    # server ac_service_2:8001;
}

upstream gs_service {
    server gs_service:8004;
}

server {
    listen 80;
    server_name your-domain.com;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location /api/v1/conflict-resolution/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://ac_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location /api/v1/synthesis/ {
        proxy_pass http://gs_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Monitoring and Alerting

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'acgs-services'
    static_configs:
      - targets: 
        - 'ac_service:8001'
        - 'gs_service:8004'
        - 'fv_service:8003'
        - 'pgc_service:8005'
        - 'integrity_service:8002'
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'qec-fidelity'
    static_configs:
      - targets: ['ac_service:8001']
    metrics_path: '/api/v1/fidelity/metrics'
    scrape_interval: 30s
```

### Grafana Dashboard
Import the provided QEC dashboard (`monitoring/grafana/qec_dashboard.json`) which includes:
- Constitutional Fidelity Score over time
- QEC component performance metrics
- Error prediction accuracy
- Recovery strategy success rates
- System resource utilization

### Alert Rules
```yaml
# alerts.yml
groups:
  - name: qec_alerts
    rules:
      - alert: LowConstitutionalFidelity
        expr: constitutional_fidelity_score < 0.70
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Constitutional fidelity below threshold"
          description: "Fidelity score {{ $value }} is below 0.70"

      - alert: HighErrorPredictionRisk
        expr: avg_error_prediction_risk > 0.80
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error prediction risk detected"
          description: "Average risk score {{ $value }} exceeds 0.80"
```

## Security Configuration

### Authentication and Authorization
```yaml
# security.yml
auth:
  jwt_secret: "your-secure-jwt-secret"
  jwt_expiry: 3600  # 1 hour
  refresh_token_expiry: 604800  # 7 days
  
rbac:
  roles:
    admin:
      permissions: ["*"]
    policy_manager:
      permissions: ["conflict_resolution:*", "fidelity:read"]
    auditor:
      permissions: ["fidelity:read", "conflicts:read"]
```

### HTTPS Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

## Backup and Recovery

### Database Backup
```bash
#!/bin/bash
# backup_script.sh
BACKUP_DIR="/backups/acgs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump $DATABASE_URL > "$BACKUP_DIR/acgs_backup_$TIMESTAMP.sql"

# Compress backup
gzip "$BACKUP_DIR/acgs_backup_$TIMESTAMP.sql"

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### QEC Data Backup
```bash
# Backup QEC-specific tables
pg_dump $DATABASE_URL \
  --table=qec_distance_calculations \
  --table=qec_error_predictions \
  --table=qec_synthesis_attempt_logs \
  > qec_data_backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### Common Issues

1. **QEC Components Not Available**
   ```bash
   # Check if QEC modules are properly installed
   python -c "from alphaevolve_gs_engine.services.qec_enhancement import ConstitutionalDistanceCalculator"
   
   # Verify environment variable
   echo $QEC_ENABLED
   ```

2. **High Memory Usage**
   ```bash
   # Monitor memory usage
   docker stats
   
   # Adjust Redis memory limit
   redis-cli CONFIG SET maxmemory 256mb
   ```

3. **Slow API Responses**
   ```bash
   # Check database connections
   psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
   
   # Monitor query performance
   psql $DATABASE_URL -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
   ```

### Log Analysis
```bash
# View service logs
docker-compose logs -f ac_service
docker-compose logs -f gs_service

# Search for QEC-related logs
docker-compose logs ac_service | grep -i "qec\|constitutional\|fidelity"

# Monitor error rates
docker-compose logs --since=1h | grep -i error | wc -l
```

## Scaling Considerations

### Horizontal Scaling
- Deploy multiple instances of each service behind load balancers
- Use Redis Cluster for distributed caching
- Implement database read replicas for read-heavy workloads

### Vertical Scaling
- Increase container resource limits
- Optimize database configuration for larger datasets
- Tune JVM/Python memory settings

### Auto-scaling
```yaml
# docker-compose.override.yml for auto-scaling
version: '3.8'
services:
  ac_service:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```
