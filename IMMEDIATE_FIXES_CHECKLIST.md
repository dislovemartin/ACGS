# ACGS-PGP Immediate Fixes Checklist
*Priority: CRITICAL - Execute within next 4 hours*

## ✅ Completed Tasks
- [x] Comprehensive codebase analysis
- [x] Issue identification and root cause analysis
- [x] Refinement plan creation

## 🔥 Critical Fixes (Execute Now)

### 1. Authentication Service Routing Fix
**Issue:** Multiple conflicting main.py files causing 404 errors
**Time Estimate:** 30 minutes

**Tasks:**
- [ ] Consolidate auth_service main.py files
- [ ] Update Docker configuration to use correct main.py
- [ ] Verify API routing includes all endpoints
- [ ] Test login/registration endpoints

**Files to Fix:**
- `src/backend/auth_service/main.py` (keep this one)
- `auth_service/main.py` (remove or rename)
- `backend/auth_service/main.py` (remove or rename)
- `src/backend/auth_service/Dockerfile` (verify CMD)

### 2. Database Migration and Schema Fix
**Issue:** Missing tables, connection errors
**Time Estimate:** 45 minutes

**Tasks:**
- [ ] Run Alembic migrations: `alembic upgrade head`
- [ ] Verify all shared models are imported
- [ ] Test database connectivity from all services
- [ ] Create missing tables if needed

**Commands to Run:**
```bash
cd migrations
alembic upgrade head
python -c "from shared.database import create_db_and_tables; import asyncio; asyncio.run(create_db_and_tables())"
```

### 3. Service-to-Service Authentication
**Issue:** 401 errors between services
**Time Estimate:** 60 minutes

**Tasks:**
- [ ] Implement internal service authentication bypass
- [ ] Add service discovery configuration
- [ ] Update CORS settings for internal communication
- [ ] Test cross-service API calls

### 4. Missing API Endpoints
**Issue:** 404 errors on Constitutional Council endpoints
**Time Estimate:** 45 minutes

**Tasks:**
- [ ] Verify all routers are properly included in main.py files
- [ ] Check endpoint path configurations
- [ ] Test Meta-Rules and Constitutional Council endpoints
- [ ] Validate Phase 1 feature endpoints

## 🚨 Validation Tests (After Fixes)

### Authentication Flow Test
```bash
# Test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# Test login
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

### Service Health Checks
```bash
curl http://localhost:8000/health  # Auth Service
curl http://localhost:8001/health  # AC Service
curl http://localhost:8002/health  # Integrity Service
curl http://localhost:8003/health  # FV Service
curl http://localhost:8004/health  # GS Service
curl http://localhost:8005/health  # PGC Service
```

### Database Connectivity Test
```bash
# Run from project root
python -c "
import asyncio
from shared.database import get_async_db
async def test_db():
    async for db in get_async_db():
        print('Database connection successful')
        break
asyncio.run(test_db())
"
```

## 📊 Success Criteria

**Before Fixes:**
- Test Success Rate: 46.7% (7/15 tests)
- Authentication: FAILING
- Database: FAILING
- Cross-Service: FAILING

**After Fixes Target:**
- Test Success Rate: >80% (12/15 tests)
- Authentication: PASSING
- Database: PASSING
- Cross-Service: PASSING

## 🔧 Tools and Commands

### Docker Management
```bash
# Rebuild services after fixes
docker-compose -f docker-compose-test.yml down
docker-compose -f docker-compose-test.yml build --no-cache
docker-compose -f docker-compose-test.yml up -d

# Check service logs
docker-compose -f docker-compose-test.yml logs auth_service
docker-compose -f docker-compose-test.yml logs ac_service
```

### Database Management
```bash
# Reset database if needed
docker-compose -f docker-compose-test.yml down -v
docker-compose -f docker-compose-test.yml up -d postgres_db
# Wait for postgres to be ready, then run migrations
```

### Testing
```bash
# Run comprehensive test suite
python test_comprehensive_acgs_validation.py

# Run specific service tests
python -m pytest src/backend/auth_service/app/tests/ -v
```

## 🚨 Rollback Plan

If fixes cause additional issues:

1. **Revert to backup:**
   ```bash
   git stash  # Save current changes
   git checkout HEAD~1  # Go back one commit
   ```

2. **Restore Docker state:**
   ```bash
   docker-compose -f docker-compose-test.yml down -v
   docker-compose -f docker-compose-test.yml up -d
   ```

3. **Database rollback:**
   ```bash
   alembic downgrade -1  # Go back one migration
   ```

## 📝 Progress Tracking

**Start Time:** ___________
**Estimated Completion:** ___________

### Task Progress
- [ ] Auth Service Fix (30 min) - Started: _____ Completed: _____
- [ ] Database Migration (45 min) - Started: _____ Completed: _____
- [ ] Service Auth (60 min) - Started: _____ Completed: _____
- [ ] Missing Endpoints (45 min) - Started: _____ Completed: _____
- [ ] Validation Tests (30 min) - Started: _____ Completed: _____

**Total Estimated Time:** 3.5 hours
**Actual Time:** ___________

---

*Execute tasks in order. Update progress as you go. Escalate immediately if any task takes >150% of estimated time.*
