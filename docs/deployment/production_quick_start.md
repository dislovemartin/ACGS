# ACGS-PGP Production Quick Start Guide

## 1. Start All Services
```bash
# Start main services
docker-compose up -d

# Start monitoring stack
./start_monitoring.sh
```

## 2. Load Authentication Tokens
```bash
# Source authentication tokens
source auth_tokens.env

# Test authentication
./test_rbac.sh
```

## 3. Run Comprehensive Tests
```bash
# Test all workflows
./test_comprehensive_workflow.sh

# Check system health
./health_check.sh
```

## 4. Monitor System
- **Grafana Dashboard**: http://localhost:3001 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090
- **Service Health**: ./health_check.sh

## 5. Backup Operations
```bash
# Create backup
./backup_database_comprehensive.sh

# Monitor backups
./monitor_backups.sh

# Test restore (if needed)
./restore_database.sh <backup_file>
```

## 6. Emergency Procedures
- **Service Issues**: Check `disaster_recovery_playbook.md`
- **Database Problems**: Run `./restore_database.sh`
- **Security Incidents**: Follow incident response procedures

## Key URLs
- AC Service: http://localhost:8001
- GS Service: http://localhost:8004
- FV Service: http://localhost:8003
- Integrity Service: http://localhost:8002
- PGC Service: http://localhost:8005
- Monitoring: http://localhost:3001

## Support
- Documentation: `backup_strategy.md`, `disaster_recovery_playbook.md`
- Health Checks: `./health_check.sh`
- Logs: `docker-compose logs <service>`
