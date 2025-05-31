# ACGS-PGP Production Operations Runbook

## Overview

This runbook provides step-by-step procedures for common production operations, incident response, and maintenance tasks for the ACGS-PGP system with integrated monitoring.

## Quick Reference

### Emergency Contacts
- **On-Call Engineer**: +1-XXX-XXX-XXXX
- **DevOps Team**: devops@company.com
- **Engineering Manager**: manager@company.com

### Critical URLs
- **Grafana Dashboards**: http://localhost:3001 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090
- **API Gateway**: http://localhost:8000
- **Production API**: https://api.acgs-pgp.example.com

### Service Health Checks
```bash
# Quick health check all services
for port in 8000 8001 8002 8003 8004 8005; do
  echo "Port $port: $(curl -s http://localhost:$port/health | jq -r '.status // "ERROR"')"
done
```

## Incident Response Procedures

### Severity Levels

#### P0 - Critical (Complete System Down)
- **Response Time**: Immediate (< 5 minutes)
- **Escalation**: Immediate to on-call engineer and manager
- **Communication**: Update status page every 15 minutes

#### P1 - High (Service Degradation)
- **Response Time**: 15 minutes
- **Escalation**: After 30 minutes if not resolved
- **Communication**: Update status page every 30 minutes

#### P2 - Medium (Non-critical Issues)
- **Response Time**: 2 hours
- **Escalation**: After 4 hours if not resolved
- **Communication**: Internal team notification

### Common Incident Scenarios

#### Scenario 1: Service Completely Down

**Symptoms:**
- Health checks failing
- 5xx errors in logs
- Grafana showing service as down

**Immediate Actions:**
```bash
# 1. Check service status
docker-compose ps

# 2. Check logs for errors
docker-compose logs service_name --tail=50

# 3. Restart service
docker-compose restart service_name

# 4. Verify recovery
curl http://localhost:PORT/health
```

**If restart doesn't work:**
```bash
# 1. Check resource usage
docker stats

# 2. Check disk space
df -h

# 3. Check database connectivity
docker exec acgs_postgres_db pg_isready -U acgs_user

# 4. Full system restart if necessary
docker-compose down && docker-compose up -d
```

#### Scenario 2: High Response Times

**Symptoms:**
- API response times > 500ms
- Grafana showing high latency
- User complaints about slow performance

**Investigation Steps:**
```bash
# 1. Check current response times
curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, rate(acgs_http_request_duration_seconds_bucket[5m]))"

# 2. Identify slow endpoints
curl -s "http://localhost:9090/api/v1/query?query=topk(10, histogram_quantile(0.95, rate(acgs_http_request_duration_seconds_bucket[5m])))"

# 3. Check database performance
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# 4. Check resource usage
docker stats
```

**Mitigation Actions:**
```bash
# 1. Scale up if resource constrained
docker-compose up -d --scale auth_service=2

# 2. Clear connection pools
docker-compose restart auth_service ac_service

# 3. Enable query caching if available
# 4. Consider temporary rate limiting increase
```

#### Scenario 3: Authentication Failures

**Symptoms:**
- Users cannot log in
- High authentication failure rate in Grafana
- JWT validation errors

**Investigation:**
```bash
# 1. Check authentication metrics
curl -s "http://localhost:9090/api/v1/query?query=rate(acgs_auth_failures_total[5m])"

# 2. Check auth service logs
docker-compose logs auth_service | grep -i error

# 3. Test authentication endpoint
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test@example.com", "password": "testpass"}'
```

**Resolution:**
```bash
# 1. Verify JWT secret is set
echo $AUTH_SERVICE_SECRET_KEY

# 2. Check database user table
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "SELECT count(*) FROM users;"

# 3. Restart auth service
docker-compose restart auth_service

# 4. If JWT secret compromised, rotate it
export AUTH_SERVICE_SECRET_KEY=$(openssl rand -base64 32)
docker-compose restart auth_service
```

## Monitoring and Alerting

### Key Dashboards

#### 1. ACGS-PGP Overview Dashboard
- **URL**: http://localhost:3001/d/acgs-overview
- **Purpose**: System-wide health and performance
- **Key Metrics**: Service uptime, response times, error rates

#### 2. Service Performance Dashboard
- **URL**: http://localhost:3001/d/acgs-services
- **Purpose**: Individual service metrics
- **Key Metrics**: CPU, memory, request rates per service

#### 3. Authentication Dashboard
- **URL**: http://localhost:3001/d/acgs-auth
- **Purpose**: Authentication and security metrics
- **Key Metrics**: Login success rates, failed attempts, JWT usage

#### 4. Database Performance Dashboard
- **URL**: http://localhost:3001/d/acgs-database
- **Purpose**: Database health and performance
- **Key Metrics**: Connection pools, query times, lock waits

### Alert Investigation

#### High Error Rate Alert
```bash
# 1. Check which service has errors
curl -s "http://localhost:9090/api/v1/query?query=rate(acgs_http_requests_total{status=~'5..'}[5m])"

# 2. Check recent deployments
git log --oneline -10

# 3. Check service logs
docker-compose logs service_name | grep ERROR

# 4. Check dependencies
curl http://localhost:8001/health  # Check AC service
curl http://localhost:8002/health  # Check Integrity service
```

#### Database Connection Alert
```bash
# 1. Check connection count
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "SELECT count(*) FROM pg_stat_activity;"

# 2. Check for long-running queries
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"

# 3. Kill long-running queries if necessary
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '10 minutes';"
```

## Maintenance Procedures

### Planned Maintenance

#### Service Updates
```bash
# 1. Announce maintenance window
# 2. Create backup
docker exec acgs_postgres_db pg_dump -U acgs_user acgs_pgp_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Update service
git pull origin main
docker-compose build service_name
docker-compose up -d service_name

# 4. Verify deployment
./scripts/validate_production_deployment.sh

# 5. Monitor for issues
# 6. Announce completion
```

#### Database Maintenance
```bash
# 1. Create backup
docker exec acgs_postgres_db pg_dump -U acgs_user acgs_pgp_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Run maintenance queries
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "VACUUM ANALYZE;"

# 3. Update statistics
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "ANALYZE;"

# 4. Check for unused indexes
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db -c "SELECT schemaname, tablename, attname, n_distinct, correlation FROM pg_stats WHERE schemaname = 'public';"
```

### Emergency Procedures

#### Complete System Recovery
```bash
# 1. Stop all services
docker-compose down

# 2. Check system resources
df -h
free -h
docker system df

# 3. Clean up if needed
docker system prune -f

# 4. Restore from backup if necessary
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db < backup_latest.sql

# 5. Start services
docker-compose up -d

# 6. Validate deployment
./scripts/validate_production_deployment.sh
```

#### Database Recovery
```bash
# 1. Stop services that use database
docker-compose stop auth_service ac_service integrity_service fv_service gs_service pgc_service

# 2. Create current backup
docker exec acgs_postgres_db pg_dump -U acgs_user acgs_pgp_db > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Restore from known good backup
docker exec acgs_postgres_db dropdb -U acgs_user acgs_pgp_db
docker exec acgs_postgres_db createdb -U acgs_user acgs_pgp_db
docker exec acgs_postgres_db psql -U acgs_user -d acgs_pgp_db < backup_known_good.sql

# 4. Run migrations if needed
docker-compose run --rm alembic-runner alembic upgrade head

# 5. Restart services
docker-compose up -d
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
CREATE INDEX CONCURRENTLY idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Update table statistics
ANALYZE policies;
ANALYZE audit_logs;
ANALYZE users;
```

### Application Optimization
```bash
# 1. Monitor memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 2. Check for memory leaks
curl -s "http://localhost:9090/api/v1/query?query=increase(container_memory_usage_bytes{name=~'acgs_.*'}[1h])"

# 3. Optimize connection pools
# Edit docker-compose.yml to adjust pool sizes
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=50

# 4. Enable caching where appropriate
REDIS_URL=redis://redis:6379/0
CACHE_TTL=300
```

## Security Procedures

### Security Incident Response
```bash
# 1. Identify the threat
docker-compose logs | grep -i "security\|attack\|breach"

# 2. Block suspicious IPs
iptables -A INPUT -s SUSPICIOUS_IP -j DROP

# 3. Rotate secrets if compromised
export AUTH_SERVICE_SECRET_KEY=$(openssl rand -base64 32)
export AUTH_SERVICE_CSRF_SECRET_KEY=$(openssl rand -base64 32)

# 4. Restart affected services
docker-compose restart auth_service

# 5. Monitor for continued threats
curl -s "http://localhost:9090/api/v1/query?query=acgs_security_events_total"
```

### Regular Security Tasks
```bash
# Weekly security log review
docker-compose logs | grep -E "(SECURITY|WARNING|ERROR)" | tail -100

# Monthly vulnerability scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image acgs_auth_service:latest

# Quarterly penetration testing
# Schedule external security assessment
```

## Backup and Recovery

### Automated Backups
```bash
# Daily database backup
0 2 * * * docker exec acgs_postgres_db pg_dump -U acgs_user acgs_pgp_db | gzip > /backups/daily/acgs_$(date +\%Y\%m\%d).sql.gz

# Weekly full system backup
0 3 * * 0 tar -czf /backups/weekly/acgs_full_$(date +\%Y\%m\%d).tar.gz /opt/acgs-pgp

# Monthly archive
0 4 1 * * cp /backups/weekly/acgs_full_$(date +\%Y\%m01).tar.gz /backups/monthly/
```

### Recovery Testing
```bash
# Monthly recovery test
# 1. Create test environment
# 2. Restore from backup
# 3. Validate functionality
# 4. Document results
```

## Contact Information

### Escalation Matrix
1. **On-Call Engineer**: Primary contact for all incidents
2. **DevOps Team Lead**: Escalate after 30 minutes for P0, 2 hours for P1
3. **Engineering Manager**: Escalate after 1 hour for P0, 4 hours for P1
4. **CTO**: Escalate for extended outages or security incidents

### External Contacts
- **Cloud Provider Support**: [Provider-specific contact]
- **Database Support**: [PostgreSQL support if applicable]
- **Security Team**: security@company.com
