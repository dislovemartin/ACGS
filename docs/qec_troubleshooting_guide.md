# QEC-Enhanced AlphaEvolve-ACGS Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting procedures for the QEC (Quality, Error, and Correction) enhanced AlphaEvolve-ACGS system, covering common issues, diagnostic procedures, and resolution steps.

## Quick Diagnostic Commands

### System Health Check
```bash
# Check all service status
docker-compose ps

# Verify QEC components
curl -s http://localhost:8001/api/v1/fidelity/current | jq '.qec_enhanced'

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Verify Redis connectivity
redis-cli ping
```

### Performance Metrics
```bash
# Check API response times
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8001/health

# Monitor resource usage
docker stats --no-stream

# Check database performance
psql $DATABASE_URL -c "SELECT schemaname,tablename,n_tup_ins,n_tup_upd,n_tup_del FROM pg_stat_user_tables WHERE schemaname='public';"
```

## Common Issues and Solutions

### 1. QEC Components Not Available

**Symptoms:**
- API returns `501 Not Implemented` for QEC endpoints
- Logs show "QEC components not available"
- Constitutional fidelity endpoint returns error

**Diagnosis:**
```bash
# Check QEC module installation
python -c "from alphaevolve_gs_engine.services.qec_enhancement import ConstitutionalDistanceCalculator; print('QEC available')"

# Verify environment configuration
echo $QEC_ENABLED

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

**Solutions:**
```bash
# Install QEC modules
cd src/alphaevolve_gs_engine
pip install -e .

# Set environment variable
export QEC_ENABLED=true

# Restart services
docker-compose restart ac_service gs_service
```

### 2. High Constitutional Fidelity Calculation Time

**Symptoms:**
- Fidelity endpoint timeouts
- High CPU usage during fidelity calculations
- Slow system response times

**Diagnosis:**
```bash
# Monitor fidelity calculation performance
curl -w "Time: %{time_total}s\n" http://localhost:8001/api/v1/fidelity/current

# Check principle count
psql $DATABASE_URL -c "SELECT COUNT(*) FROM constitutional_principles;"

# Monitor CPU usage
top -p $(pgrep -f ac_service)
```

**Solutions:**
```bash
# Enable Redis caching
export REDIS_URL=redis://localhost:6379/0

# Optimize calculation interval
# Edit config/qec_fidelity_monitor.yaml
calculation_interval_seconds: 600  # Increase to 10 minutes

# Add database indexes
psql $DATABASE_URL -c "CREATE INDEX CONCURRENTLY idx_principles_distance_score ON constitutional_principles(distance_score);"
```

### 3. Error Prediction Model Accuracy Issues

**Symptoms:**
- Low prediction confidence scores
- Frequent prediction failures
- Inconsistent error predictions

**Diagnosis:**
```bash
# Check model accuracy
curl http://localhost:8001/api/v1/qec/model-stats

# Review prediction logs
docker-compose logs gs_service | grep -i "error.prediction"

# Check training data volume
psql $DATABASE_URL -c "SELECT COUNT(*) FROM qec_synthesis_attempt_logs;"
```

**Solutions:**
```bash
# Retrain model with more data
curl -X POST http://localhost:8001/api/v1/qec/retrain-model

# Adjust confidence threshold
# Edit config/qec_error_prediction.yaml
confidence_threshold: 0.6  # Lower threshold

# Clear prediction cache
redis-cli FLUSHDB
```

### 4. Recovery Strategy Failures

**Symptoms:**
- High failure rates in conflict resolution
- Recovery strategies not being applied
- Escalation to human too frequently

**Diagnosis:**
```bash
# Check recovery strategy performance
curl http://localhost:8001/api/v1/qec/recovery-stats

# Review strategy configuration
cat config/qec_recovery_strategies.yaml

# Check attempt history
psql $DATABASE_URL -c "SELECT recovery_strategy, COUNT(*) FROM qec_synthesis_attempt_logs GROUP BY recovery_strategy;"
```

**Solutions:**
```bash
# Update strategy configuration
# Edit config/qec_recovery_strategies.yaml
semantic_conflict:
  max_attempts: 4  # Increase attempts
  timeout_seconds: 60  # Increase timeout

# Clear attempt history for fresh start
curl -X DELETE http://localhost:8001/api/v1/qec/clear-history

# Restart recovery dispatcher
docker-compose restart ac_service
```

### 5. Database Performance Issues

**Symptoms:**
- Slow query responses
- High database CPU usage
- Connection pool exhaustion

**Diagnosis:**
```bash
# Check slow queries
psql $DATABASE_URL -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Monitor connections
psql $DATABASE_URL -c "SELECT count(*) as connections, state FROM pg_stat_activity GROUP BY state;"

# Check table sizes
psql $DATABASE_URL -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

**Solutions:**
```bash
# Add missing indexes
psql $DATABASE_URL -c "
CREATE INDEX CONCURRENTLY idx_qec_distance_calc_updated_at ON qec_distance_calculations(score_updated_at);
CREATE INDEX CONCURRENTLY idx_qec_error_pred_timestamp ON qec_error_predictions(prediction_timestamp);
"

# Optimize PostgreSQL settings
psql $DATABASE_URL -c "
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET effective_cache_size = '2GB';
ALTER SYSTEM SET work_mem = '16MB';
SELECT pg_reload_conf();
"

# Clean old data
psql $DATABASE_URL -c "DELETE FROM qec_synthesis_attempt_logs WHERE timestamp < NOW() - INTERVAL '30 days';"
```

### 6. Memory Leaks and High Memory Usage

**Symptoms:**
- Gradually increasing memory usage
- Out of memory errors
- Service crashes

**Diagnosis:**
```bash
# Monitor memory usage over time
docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}" --no-stream

# Check Python memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# Profile memory usage
pip install memory-profiler
python -m memory_profiler your_script.py
```

**Solutions:**
```bash
# Restart services periodically
# Add to crontab
0 2 * * * docker-compose restart ac_service gs_service

# Optimize Python garbage collection
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# Limit container memory
# In docker-compose.yml
services:
  ac_service:
    mem_limit: 2g
    memswap_limit: 2g
```

### 7. Cross-Service Communication Failures

**Symptoms:**
- Services unable to communicate
- Timeout errors between services
- Inconsistent data across services

**Diagnosis:**
```bash
# Test service connectivity
curl http://ac_service:8001/health
curl http://gs_service:8004/health

# Check network configuration
docker network ls
docker network inspect acgs_default

# Monitor service logs
docker-compose logs -f --tail=100
```

**Solutions:**
```bash
# Restart networking
docker-compose down
docker-compose up -d

# Check service discovery
# Ensure services use correct hostnames in docker-compose.yml

# Add health checks
# In docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Performance Tuning

### Database Optimization
```sql
-- Analyze table statistics
ANALYZE constitutional_principles;
ANALYZE qec_distance_calculations;
ANALYZE qec_synthesis_attempt_logs;

-- Vacuum tables
VACUUM ANALYZE constitutional_principles;
VACUUM ANALYZE qec_distance_calculations;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
WHERE schemaname = 'public' 
ORDER BY idx_scan DESC;
```

### Redis Optimization
```bash
# Monitor Redis performance
redis-cli INFO stats

# Optimize memory usage
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory 512mb

# Monitor slow queries
redis-cli CONFIG SET slowlog-log-slower-than 10000
redis-cli SLOWLOG GET 10
```

### Application Tuning
```python
# Optimize QEC component initialization
# In your application startup
import asyncio
from alphaevolve_gs_engine.services.qec_enhancement import ConstitutionalFidelityMonitor

# Pre-initialize components
fidelity_monitor = ConstitutionalFidelityMonitor()
await fidelity_monitor.warm_cache()
```

## Monitoring and Alerting

### Key Metrics to Monitor
```yaml
# Prometheus metrics
- constitutional_fidelity_score
- qec_error_prediction_accuracy
- qec_recovery_strategy_success_rate
- api_response_time_seconds
- database_connection_count
- memory_usage_bytes
- cpu_usage_percent
```

### Alert Thresholds
```yaml
alerts:
  - name: LowFidelityScore
    condition: constitutional_fidelity_score < 0.70
    severity: warning
    
  - name: HighErrorRate
    condition: error_rate > 0.05
    severity: critical
    
  - name: SlowAPIResponse
    condition: api_response_time_p95 > 1.0
    severity: warning
    
  - name: HighMemoryUsage
    condition: memory_usage_percent > 85
    severity: warning
```

## Log Analysis

### Important Log Patterns
```bash
# QEC component errors
grep -i "qec.*error\|constitutional.*error\|fidelity.*error" /var/log/acgs/*.log

# Performance issues
grep -i "timeout\|slow\|performance" /var/log/acgs/*.log

# Authentication failures
grep -i "auth.*fail\|unauthorized\|forbidden" /var/log/acgs/*.log

# Database issues
grep -i "database.*error\|connection.*error\|sql.*error" /var/log/acgs/*.log
```

### Log Aggregation
```bash
# Centralized logging with ELK stack
# logstash.conf
input {
  file {
    path => "/var/log/acgs/*.log"
    type => "acgs"
  }
}

filter {
  if [type] == "acgs" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{WORD:service} - %{LOGLEVEL:level} - %{GREEDYDATA:message}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "acgs-logs-%{+YYYY.MM.dd}"
  }
}
```

## Emergency Procedures

### Service Recovery
```bash
# Emergency restart all services
docker-compose down --remove-orphans
docker-compose up -d

# Rollback to previous version
git checkout previous-stable-tag
docker-compose build
docker-compose up -d
```

### Data Recovery
```bash
# Restore from backup
psql $DATABASE_URL < /backups/acgs_backup_latest.sql

# Rebuild QEC data
curl -X POST http://localhost:8001/api/v1/qec/rebuild-cache
```

### Failover Procedures
```bash
# Switch to backup database
export DATABASE_URL=postgresql://backup-db:5432/acgs_db
docker-compose restart

# Enable maintenance mode
curl -X POST http://localhost:8001/api/v1/maintenance/enable
```

## Contact Information

For additional support:
- **Technical Issues**: Create issue in GitHub repository
- **Performance Problems**: Contact DevOps team
- **Security Concerns**: Contact security team immediately
- **Emergency**: Use on-call escalation procedures

## Useful Commands Reference

```bash
# Quick health check
curl -s http://localhost:8001/health | jq '.'

# Check QEC status
curl -s http://localhost:8001/api/v1/fidelity/current | jq '.level'

# Monitor logs in real-time
docker-compose logs -f ac_service | grep -i qec

# Database quick check
psql $DATABASE_URL -c "SELECT COUNT(*) FROM constitutional_principles;"

# Redis status
redis-cli info replication

# System resources
docker system df
docker system prune -f
```
