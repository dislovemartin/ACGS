# ACGS-PGP Troubleshooting Guide

This guide provides solutions for common issues encountered when deploying and operating the ACGS-PGP framework with Phase 1-3 features.

## Quick Diagnostics

### **System Health Check**
```bash
# Check all services status
docker-compose -f config/docker/docker-compose.yml ps

# Verify deployment
python scripts/verify_acgs_deployment.sh

# Check database connectivity
python scripts/health_check.sh
```

### **Service Logs**
```bash
# View all service logs
docker-compose -f config/docker/docker-compose.yml logs

# View specific service logs
docker-compose -f config/docker/docker-compose.yml logs ac_service
docker-compose -f config/docker/docker-compose.yml logs gs_service
docker-compose -f config/docker/docker-compose.yml logs fv_service
```

## Common Issues and Solutions

### **1. Database Connection Issues**

#### **Symptoms:**
- Services failing to start
- "Connection refused" errors
- Database migration failures

#### **Solutions:**
```bash
# Check PostgreSQL container status
docker-compose -f config/docker/docker-compose.yml ps postgres

# Verify database URL in environment
grep DATABASE_URL .env

# Restart database service
docker-compose -f config/docker/docker-compose.yml restart postgres

# Manual database connection test
docker-compose -f config/docker/docker-compose.yml exec postgres psql -U acgs_user -d acgs_db
```

#### **Common Fixes:**
- Ensure `DATABASE_URL` uses service name: `postgresql://acgs_user:acgs_password@postgres:5432/acgs_db`
- Check PostgreSQL container logs for startup errors
- Verify database credentials match between services and PostgreSQL configuration

### **2. LLM Integration Issues**

#### **Symptoms:**
- Constitutional prompting failures
- "OpenAI API key not found" errors
- Policy synthesis timeouts

#### **Solutions:**
```bash
# Verify OpenAI API key
grep OPENAI_API_KEY .env

# Test LLM connectivity
python -c "
import openai
openai.api_key = 'your-api-key'
response = openai.ChatCompletion.create(
    model='gpt-4',
    messages=[{'role': 'user', 'content': 'Test'}],
    max_tokens=10
)
print('LLM connection successful')
"

# Check GS service logs for LLM errors
docker-compose -f config/docker/docker-compose.yml logs gs_service | grep -i openai
```

#### **Common Fixes:**
- Ensure valid OpenAI API key is set in environment variables
- Check API key permissions and billing status
- Verify network connectivity to OpenAI services
- Increase timeout values for LLM requests

### **3. Z3 Formal Verification Issues**

#### **Symptoms:**
- Verification timeouts
- Z3 solver crashes
- "Z3 not found" errors

#### **Solutions:**
```bash
# Check Z3 installation in FV service
docker-compose -f config/docker/docker-compose.yml exec fv_service python -c "import z3; print(z3.get_version_string())"

# Test Z3 solver functionality
docker-compose -f config/docker/docker-compose.yml exec fv_service python -c "
import z3
s = z3.Solver()
x = z3.Int('x')
s.add(x > 0)
print('Z3 solver status:', s.check())
"

# Check FV service logs
docker-compose -f config/docker/docker-compose.yml logs fv_service | grep -i z3
```

#### **Common Fixes:**
- Increase Z3 timeout values in environment configuration
- Reduce memory usage by limiting Z3 solver complexity
- Check Z3 installation in Docker container
- Verify formal verification input format

### **4. PGP Cryptographic Integrity Issues**

#### **Symptoms:**
- Signature verification failures
- "PGP key not found" errors
- Cryptographic integrity check failures

#### **Solutions:**
```bash
# Check PGP key configuration
grep PGP_ .env

# Verify PGP key availability
docker-compose -f config/docker/docker-compose.yml exec integrity_service gpg --list-keys

# Test PGP signing functionality
docker-compose -f config/docker/docker-compose.yml exec integrity_service python -c "
import gnupg
gpg = gnupg.GPG()
keys = gpg.list_keys()
print('Available PGP keys:', len(keys))
"

# Check integrity service logs
docker-compose -f config/docker/docker-compose.yml logs integrity_service | grep -i pgp
```

#### **Common Fixes:**
- Generate PGP keys if not present: `gpg --gen-key`
- Import existing PGP keys into container
- Verify PGP key ID and passphrase in environment
- Check file permissions for PGP key files

### **5. Constitutional Council Issues**

#### **Symptoms:**
- Amendment proposal failures
- Voting mechanism errors
- Constitutional Council access denied

#### **Solutions:**
```bash
# Check Constitutional Council user roles
docker-compose -f config/docker/docker-compose.yml exec ac_service python -c "
from shared.database import get_db
from shared.models import User
db = next(get_db())
council_users = db.query(User).filter(User.role == 'constitutional_council').all()
print(f'Constitutional Council members: {len(council_users)}')
"

# Verify amendment workflow
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/ac/constitutional-council/amendments

# Check AC service logs for council operations
docker-compose -f config/docker/docker-compose.yml logs ac_service | grep -i council
```

#### **Common Fixes:**
- Ensure users have correct Constitutional Council role
- Verify amendment proposal format and validation
- Check voting deadline and status
- Validate Constitutional Council permissions

### **6. Performance Issues**

#### **Symptoms:**
- Slow governance decisions (>20ms)
- High memory usage
- Database query timeouts

#### **Solutions:**
```bash
# Monitor system resources
docker stats

# Check database performance
docker-compose -f config/docker/docker-compose.yml exec postgres psql -U acgs_user -d acgs_db -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Profile service performance
docker-compose -f config/docker/docker-compose.yml exec pgc_service python -m cProfile -s cumtime app/main.py
```

#### **Common Fixes:**
- Add database indexes for frequently queried fields
- Implement caching for constitutional principles
- Optimize database connection pooling
- Scale services horizontally if needed

## Service-Specific Troubleshooting

### **Auth Service Issues**
- JWT token validation failures
- User registration/login problems
- RBAC permission errors

### **AC Service Issues**
- Principle management errors
- Meta-rule conflicts
- Constitutional amendment workflow problems

### **GS Service Issues**
- Policy synthesis failures
- Constitutional prompting errors
- AlphaEvolve integration problems

### **FV Service Issues**
- Formal verification timeouts
- Z3 solver memory issues
- Bias detection failures

### **Integrity Service Issues**
- Audit log corruption
- PGP signature failures
- Hash chain validation errors

### **PGC Service Issues**
- Runtime enforcement failures
- Governance penalty calculation errors
- Performance optimization issues

## Emergency Procedures

### **System Recovery**
```bash
# Stop all services
docker-compose -f config/docker/docker-compose.yml down

# Clean up containers and volumes
docker-compose -f config/docker/docker-compose.yml down -v
docker system prune -f

# Restore from backup
python scripts/restore_database.sh

# Restart system
docker-compose -f config/docker/docker-compose.yml up --build -d
```

### **Database Recovery**
```bash
# Create database backup
python scripts/backup_database.sh

# Restore from specific backup
python scripts/restore_database.sh backup_2024_01_15.sql
```

## Getting Help

### **Log Collection**
```bash
# Collect all logs for support
mkdir -p logs
docker-compose -f config/docker/docker-compose.yml logs > logs/all_services.log
docker-compose -f config/docker/docker-compose.yml ps > logs/service_status.log
```

### **System Information**
```bash
# Collect system information
docker version > logs/docker_version.log
docker-compose version > logs/compose_version.log
python --version > logs/python_version.log
```

### **Support Channels**
- GitHub Issues: Report bugs and feature requests
- Documentation: Check latest documentation updates
- Community Forum: Ask questions and share solutions

For persistent issues, provide the collected logs and system information when seeking support.
