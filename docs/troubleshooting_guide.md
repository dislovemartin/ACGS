# ACGS-PGP Production Troubleshooting Guide

## Overview

This guide provides step-by-step troubleshooting procedures for common issues in the ACGS-PGP production environment, including service failures, performance problems, authentication issues, and monitoring alerts.

## 🚨 Current Critical Issues (Phase 2.3)

### **Integrity Service Database DNS Resolution Failure**
- **Status:** ❌ CRITICAL - Service Down
- **Impact:** Cryptographic verification and PGP assurance unavailable
- **Symptoms:** Integrity service fails to start, database connection errors
- **Quick Fix:** See [Integrity Service DNS Resolution](#integrity-service-dns-resolution) section below

### **Security Middleware Health Endpoint Blocking**
- **Status:** ⚠️ MEDIUM - Workaround Available
- **Impact:** Health monitoring may show false negatives
- **Symptoms:** Health checks return 405 Method Not Allowed
- **Quick Fix:** See [Security Middleware Configuration](#security-middleware-configuration) section below

## Critical Issue Resolution

### Integrity Service DNS Resolution

#### Problem
The Integrity Service fails to start due to database DNS resolution issues, preventing cryptographic verification and PGP assurance functionality.

#### Symptoms
```bash
# Container logs show DNS resolution errors
docker-compose logs integrity_service

# Common error messages:
# "could not translate host name to address: Name or service not known"
# "connection to server failed: could not connect to server"
```

#### Solution
```bash
# 1. Check database connectivity from host
ping postgres_db
nslookup postgres_db

# 2. Update database URL with direct IP (temporary fix)
# In .env file, replace hostname with IP:
DATABASE_URL=postgresql://acgs_user:password@172.18.0.2:5432/acgs_db

# 3. Restart integrity service
docker-compose restart integrity_service

# 4. Verify service health
curl http://localhost:8002/health
```

#### Permanent Fix
```bash
# 1. Update Docker Compose network configuration
# Add explicit network aliases in docker-compose.yml:
services:
  postgres_db:
    networks:
      acgs_network:
        aliases:
          - postgres
          - database

# 2. Update service dependencies
# Ensure integrity_service depends_on postgres_db
```

### Security Middleware Configuration

#### Problem
Security middleware blocks health check endpoints, causing monitoring to show false negatives.

#### Symptoms
```bash
# Health checks return 405 Method Not Allowed
curl -X GET http://localhost:8002/health
# Response: {"error": "Method Not Allowed", "detail": "Method GET not allowed for /health"}
```

#### Solution
```bash
# 1. Update security middleware configuration
# In src/backend/shared/security_middleware.py, whitelist health endpoints

# 2. Restart affected services
docker-compose restart integrity_service gs_service fv_service pgc_service

# 3. Verify health checks work
curl http://localhost:8001/health  # AC Service
curl http://localhost:8002/health  # Integrity Service
curl http://localhost:8003/health  # FV Service
```

#### Configuration Update
```python
# In security_middleware.py, ensure health endpoints are whitelisted:
HEALTH_ENDPOINTS = ["/health", "/api/health", "/api/v1/health"]

# Skip security validation for health checks
if request.url.path in HEALTH_ENDPOINTS:
    return await call_next(request)
```

## Quick Diagnostic Commands

### System Health Check
```bash
# Check all container status
docker-compose ps

# Check service health endpoints
curl http://localhost:8000/health  # Auth Service
curl http://localhost:8001/health  # AC Service
curl http://localhost:8002/health  # Integrity Service
curl http://localhost:8003/health  # FV Service
curl http://localhost:8004/health  # GS Service
curl http://localhost:8005/health  # PGC Service
curl http://localhost:8006/health  # EC Service (WINA Optimization)

# Check monitoring services
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3001/api/health  # Grafana
```

### Resource Usage
```bash
# Check container resource usage
docker stats

# Check disk usage
df -h

# Check memory usage
free -h

# Check system load
uptime
```

## Common Issues and Solutions

### 1. Service Not Starting

#### Symptoms
- Container exits immediately
- Health check fails
- Service not accessible

#### Diagnosis
```bash
# Check container logs
docker-compose logs service_name

# Check container status
docker-compose ps service_name

# Check for port conflicts
netstat -tulpn | grep :8000
```

#### Common Causes and Solutions

**Database Connection Issues**
```bash
# Check database connectivity
docker exec acgs_postgres_db pg_isready -U acgs_user

# Verify database URL
echo $DATABASE_URL

# Check database logs
docker-compose logs postgres_db
```

**Missing Dependencies**
```bash
# Rebuild container with latest dependencies
docker-compose build service_name --no-cache

# Check requirements.txt
cat backend/service_name/requirements.txt
```

**Environment Variables**
```bash
# Check environment variables
docker-compose config

# Verify .env file
cat .env
```

### 2. High Response Times

#### Symptoms
- API responses > 200ms
- Grafana dashboard shows high latency
- Prometheus alerts firing

#### Diagnosis
```bash
# Check current response times
curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, rate(acgs_http_request_duration_seconds_bucket[5m]))"

# Check database query performance
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check resource usage
docker stats
```

#### Solutions

**Database Optimization**
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_policies_created_at ON policies(created_at);
CREATE INDEX CONCURRENTLY idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM policies WHERE status = 'active';
```

**Connection Pool Tuning**
```python
# Increase connection pool size
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=50
```

**Caching Implementation**
```python
# Add Redis caching for frequently accessed data
REDIS_URL=redis://redis:6379/0
CACHE_TTL=300  # 5 minutes
```

### 3. Authentication Failures

#### Symptoms
- Users cannot log in
- JWT token validation fails
- CSRF errors

#### Diagnosis
```bash
# Check authentication metrics
curl -s "http://localhost:9090/api/v1/query?query=acgs_auth_attempts_total"

# Check auth service logs
docker-compose logs auth_service | grep -i error

# Test authentication endpoint
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test@example.com", "password": "testpass"}'
```

#### Solutions

**JWT Secret Key Issues**
```bash
# Verify JWT secret is set
echo $AUTH_SERVICE_SECRET_KEY

# Regenerate JWT secret (will invalidate existing tokens)
openssl rand -base64 32
```

**CSRF Token Problems**
```bash
# Get CSRF token
curl -X GET http://localhost:8000/auth/csrf-token \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Verify CSRF secret
echo $AUTH_SERVICE_CSRF_SECRET_KEY
```

**Database User Issues**
```sql
-- Check user exists
SELECT * FROM users WHERE email = 'user@example.com';

-- Reset user password
UPDATE users SET password_hash = '$2b$12$...' WHERE email = 'user@example.com';
```

### 4. Database Connection Issues

#### Symptoms
- "Connection refused" errors
- "Too many connections" errors
- Slow database queries

#### Diagnosis
```bash
# Check database container
docker-compose logs postgres_db

# Check connection count
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "SELECT count(*) FROM pg_stat_activity;"

# Check database configuration
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "SHOW max_connections;"
```

#### Solutions

**Connection Pool Configuration**
```bash
# Increase PostgreSQL max connections
echo "max_connections = 200" >> postgresql.conf

# Tune connection pool settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
```

**Connection Leaks**
```python
# Ensure proper connection cleanup
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 5. Monitoring Issues

#### Symptoms
- Prometheus not collecting metrics
- Grafana dashboards empty
- Alerts not firing

#### Diagnosis
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check metrics endpoints
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics

# Check Prometheus configuration
docker exec acgs_prometheus cat /etc/prometheus/prometheus.yml
```

#### Solutions

**Metrics Collection**
```bash
# Restart Prometheus to reload config
docker-compose restart prometheus

# Check service discovery
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'
```

**Grafana Dashboard Issues**
```bash
# Check Grafana logs
docker-compose logs grafana

# Verify datasource connection
curl -u admin:admin123 http://localhost:3001/api/datasources
```

### 6. Load Balancing Issues

#### Symptoms
- Uneven load distribution
- Some instances not receiving traffic
- Session persistence problems

#### Diagnosis
```bash
# Check Nginx upstream status
curl http://localhost:8000/nginx_health

# Check Nginx logs
docker-compose logs nginx_gateway

# Test load distribution
for i in {1..10}; do curl -s http://localhost:8000/auth/health; done
```

#### Solutions

**Nginx Configuration**
```nginx
# Verify upstream configuration
upstream auth_service_upstream {
    least_conn;
    server auth_service:8000 max_fails=3 fail_timeout=30s;
    server auth_service_2:8000 max_fails=3 fail_timeout=30s;
}
```

**Health Check Configuration**
```bash
# Ensure health checks are working
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### 7. WINA Optimization Issues (EC Service)

#### Symptoms
- Poor policy synthesis accuracy
- High GFLOPs usage despite optimization
- Constitutional compliance failures
- EC service performance degradation

#### Diagnosis
```bash
# Check EC service logs
docker-compose logs ec_service | grep -i "wina\|optimization\|gflops"

# Check WINA performance metrics
curl http://localhost:8006/api/v1/wina/performance/metrics

# Check constitutional fidelity score
curl http://localhost:8006/api/v1/monitoring/constitutional-fidelity

# Check WINA configuration
docker-compose exec ec_service env | grep WINA
```

#### Solutions

**WINA Configuration Tuning**
```bash
# Adjust optimization targets (less aggressive)
WINA_GFLOPS_REDUCTION_TARGET=0.45  # Reduced from 0.55
WINA_SYNTHESIS_ACCURACY_THRESHOLD=0.90  # Lowered threshold

# Enable/disable specific optimizations
WINA_SVD_ENABLED=true
WINA_GATING_ENABLED=false  # Disable if causing issues
```

**Constitutional Compliance Issues**
```bash
# Check constitutional principles integration
curl http://localhost:8001/api/v1/principles/ | jq '.[] | select(.is_active == true)'

# Verify AC service connectivity
docker-compose exec ec_service curl -f http://ac_service:8001/health

# Reset constitutional fidelity monitoring
curl -X POST http://localhost:8006/api/v1/monitoring/validate-governance
```

**Performance Optimization**
```bash
# Monitor GFLOPs reduction
curl http://localhost:8006/api/v1/wina/performance/gflops

# Check synthesis accuracy trends
curl http://localhost:8006/api/v1/wina/performance/synthesis-accuracy

# Run performance benchmark
curl -X POST http://localhost:8006/api/v1/wina/performance/benchmark
```

### 8. Constitutional Council Issues

#### Symptoms
- Amendment proposals not being processed
- Voting mechanisms failing
- Council member authentication issues
- Democratic governance workflow failures

#### Diagnosis
```bash
# Check Constitutional Council status
curl http://localhost:8001/api/v1/constitutional-council/amendments

# Verify council member roles
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "
SELECT email, role, is_active FROM users WHERE role = 'constitutional_council';"

# Check amendment voting status
curl http://localhost:8001/api/v1/constitutional-council/amendments/{id}/votes

# Check AC service logs for council operations
docker-compose logs ac_service | grep -i "council\|amendment\|vote"
```

#### Solutions

**Council Member Management**
```sql
-- Add council member
INSERT INTO users (email, username, full_name, role, is_active)
VALUES ('council@example.com', 'council_member', 'Council Member', 'constitutional_council', true);

-- Verify council member permissions
SELECT u.email, u.role, COUNT(av.id) as votes_cast
FROM users u
LEFT JOIN amendment_votes av ON u.id = av.voter_id
WHERE u.role = 'constitutional_council'
GROUP BY u.id, u.email, u.role;
```

**Amendment Workflow Issues**
```bash
# Check voting period configuration
echo $AC_VOTING_PERIOD_HOURS

# Verify amendment threshold
echo $AC_AMENDMENT_THRESHOLD

# Check for expired voting periods
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "
SELECT id, title, status, voting_deadline
FROM constitutional_amendments
WHERE voting_deadline < NOW() AND status = 'voting';"
```

## Performance Optimization

### Database Optimization
```sql
-- Identify slow queries
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_policies_status ON policies(status);
CREATE INDEX CONCURRENTLY idx_audit_logs_user_id ON audit_logs(user_id);

-- Update table statistics
ANALYZE policies;
ANALYZE audit_logs;
```

### Application Optimization
```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)

# Implement caching
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_cached_policy(policy_id: str):
    return await get_policy(policy_id)
```

### Monitoring Optimization
```yaml
# Reduce scrape intervals for high-volume metrics
scrape_configs:
  - job_name: 'acgs-services'
    scrape_interval: 30s  # Increased from 15s
    metrics_path: '/metrics'
```

## Emergency Procedures

### Service Recovery
```bash
# Quick service restart
docker-compose restart service_name

# Full system restart
docker-compose down
docker-compose up -d

# Rollback to previous version
git checkout previous_tag
docker-compose up -d --build
```

### Database Recovery
```bash
# Restore from backup
docker exec acgs_postgres_db pg_restore -U acgs_user -d acgs_pgp_db /backup/latest.dump

# Point-in-time recovery
docker exec acgs_postgres_db pg_basebackup -U acgs_user -D /recovery -Ft -z -P
```

### Security Incident Response
```bash
# Block suspicious IP
iptables -A INPUT -s SUSPICIOUS_IP -j DROP

# Revoke all JWT tokens (change secret)
export AUTH_SERVICE_SECRET_KEY=$(openssl rand -base64 32)
docker-compose restart auth_service

# Enable maintenance mode
echo "maintenance" > /tmp/maintenance_mode
```

## Monitoring and Alerting

### Grafana Dashboard Interpretation

#### ACGS-PGP Overview Dashboard
Access at: http://localhost:3001/d/acgs-overview

**Key Panels to Monitor:**
```bash
# Service Health Status
- Green: All services operational (target: 100%)
- Yellow: Degraded performance (investigate if >5%)
- Red: Service down (immediate action required)

# API Response Times
- Target: 95th percentile < 200ms
- Warning: 200-500ms (investigate performance)
- Critical: >500ms (immediate optimization needed)

# Error Rates by Service
- Target: <5% error rate
- Warning: 5-10% (check logs and recent deployments)
- Critical: >10% (potential system failure)

# Database Performance
- Connection Pool Usage: <80% (scale if approaching limit)
- Query Duration: <100ms average (optimize slow queries)
- Active Connections: Monitor for connection leaks
```

#### Authentication Metrics Dashboard
```bash
# Login Success Rate
curl -s "http://localhost:9090/api/v1/query?query=rate(acgs_auth_success_total[5m]) / rate(acgs_auth_attempts_total[5m]) * 100"

# Failed Login Attempts by IP
curl -s "http://localhost:9090/api/v1/query?query=topk(10, sum by (source_ip) (rate(acgs_auth_failures_total[5m])))"

# JWT Token Usage
curl -s "http://localhost:9090/api/v1/query?query=acgs_jwt_tokens_active"
```

#### Performance Monitoring Queries
```bash
# Top 10 slowest endpoints
curl -s "http://localhost:9090/api/v1/query?query=topk(10, histogram_quantile(0.95, rate(acgs_http_request_duration_seconds_bucket[5m])))"

# Memory usage by service
curl -s "http://localhost:9090/api/v1/query?query=container_memory_usage_bytes{name=~'acgs_.*'}"

# CPU usage trends
curl -s "http://localhost:9090/api/v1/query?query=rate(container_cpu_usage_seconds_total{name=~'acgs_.*'}[5m]) * 100"
```

### Key Metrics to Monitor

#### Performance Targets
- **API Response Time**: 95th percentile < 200ms
- **Service Uptime**: >99.5% availability
- **Error Rate**: <5% across all services
- **Authentication Success Rate**: >95%
- **Database Query Time**: <100ms (95th percentile)
- **Concurrent Users**: Support 100+ without degradation

#### Resource Utilization Targets
- **CPU Usage**: <70% average per service
- **Memory Usage**: <80% of allocated memory
- **Database Connections**: <80% of max pool size
- **Disk Usage**: <85% of available space
- **Network Bandwidth**: <80% of available capacity

### Advanced Alert Rules

#### Custom Prometheus Queries for Troubleshooting
```bash
# Detect service communication failures
curl -s "http://localhost:9090/api/v1/query?query=rate(acgs_service_calls_total{status='error'}[5m])"

# Monitor database connection pool exhaustion
curl -s "http://localhost:9090/api/v1/query?query=acgs_database_connections / acgs_database_max_connections * 100"

# Track memory leaks
curl -s "http://localhost:9090/api/v1/query?query=increase(container_memory_usage_bytes{name=~'acgs_.*'}[1h])"

# Identify high-traffic endpoints
curl -s "http://localhost:9090/api/v1/query?query=topk(10, rate(acgs_http_requests_total[5m]))"
```

### Alert Escalation Matrix

| Severity | Response Time | Notification Method | Escalation |
|----------|---------------|-------------------|------------|
| **Info** | 24 hours | Log only | None |
| **Warning** | 4 hours | Email to team | After 8 hours |
| **Critical** | 30 minutes | SMS + Email | After 1 hour |
| **Emergency** | Immediate | Phone call + SMS | After 15 minutes |

#### Alert Routing Configuration
```yaml
# AlertManager routing rules
route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'critical-alerts'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK'
    channel: '#acgs-alerts'
    title: 'ACGS-PGP Critical Alert'
  email_configs:
  - to: 'oncall@company.com'
    subject: 'ACGS-PGP Critical Alert'
```

### Log Analysis and Correlation

#### Centralized Logging Queries
```bash
# Correlate errors across services
docker-compose logs --since=1h | grep -E "(ERROR|CRITICAL)" | sort

# Authentication failure analysis
docker-compose logs auth_service | grep "authentication failed" | \
  awk '{print $1, $2, $NF}' | sort | uniq -c | sort -nr

# Database connection issues
docker-compose logs | grep -i "connection" | grep -i "error"

# Rate limiting violations
docker-compose logs nginx_gateway | grep "429" | \
  awk '{print $1}' | sort | uniq -c | sort -nr
```

#### Performance Correlation
```bash
# Correlate high response times with resource usage
curl -s "http://localhost:9090/api/v1/query_range?query=acgs_http_request_duration_seconds&start=$(date -d '1 hour ago' +%s)&end=$(date +%s)&step=60"

# Memory usage during high load
curl -s "http://localhost:9090/api/v1/query_range?query=container_memory_usage_bytes{name=~'acgs_.*'}&start=$(date -d '1 hour ago' +%s)&end=$(date +%s)&step=60"
```

## Preventive Maintenance

### Daily Tasks
- [ ] Check service health endpoints
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Verify backup completion

### Weekly Tasks
- [ ] Analyze performance metrics
- [ ] Review security logs
- [ ] Update dependencies
- [ ] Test disaster recovery procedures

### Monthly Tasks
- [ ] Performance optimization review
- [ ] Security vulnerability scan
- [ ] Capacity planning assessment
- [ ] Documentation updates

## Contact Information

### Escalation Contacts
- **Level 1**: DevOps Team (devops@company.com)
- **Level 2**: Engineering Manager (manager@company.com)
- **Level 3**: CTO (cto@company.com)

### External Support
- **Database**: PostgreSQL Support
- **Monitoring**: Grafana Labs Support
- **Infrastructure**: Cloud Provider Support

## Additional Resources

- [Production API Documentation](production_api_documentation.md)
- [Security Configuration Guide](security_configuration.md)
- [Deployment Checklist](../DEPLOYMENT_CHECKLIST.md)
- [Monitoring Runbook](monitoring_runbook.md)
