# ACGS-Master High-Priority Task Setup Instructions

## 🎯 Overview

This document provides comprehensive instructions for setting up and executing the highest-value tasks for the ACGS-master repository. These tasks are designed to achieve maximum impact in reliability, governance synthesis, performance, security, and documentation.

## 📋 Master Task Framework

Based on the repository analysis and existing task structure, we have identified **5 High-Value Workstreams** that will yield the greatest uplift:

### 1. 🧪 **Automated Tests & Coverage to ≥90%**
### 2. 🏛️ **Governance Synthesis & Enforcement Hardening** 
### 3. ⚡ **Performance & Scalability Audit**
### 4. 🔒 **Security & Compliance Sweep**
### 5. 📚 **Documentation & Developer Onboarding**

---

## 🚀 Task Setup Instructions

### Prerequisites

1. **Repository Access**: Ensure you're in `/home/dislove/ACGS-master`
2. **Environment Setup**: Python 3.10+, Go 1.19+, Docker, PostgreSQL
3. **Dependencies**: Install all requirements from `requirements.txt` files
4. **TaskMaster**: Existing TaskMaster AI system is configured and ready

### Initial Repository Scan

Execute this comprehensive scan to understand current state:

```bash
# 1. Check existing test coverage
python scripts/coverage_analysis.py

# 2. Review current task status
tm get-tasks

# 3. Validate service health
python test_service_integration.py

# 4. Check security status
python security_hardening.py

# 5. Review documentation completeness
find docs/ -name "*.md" -exec wc -l {} +
```

---

## 📊 Current State Assessment

### ✅ **Completed Components (95% Complete)**
- Phase 1: Enhanced Principle Management, Constitutional Prompting, Meta-Rules
- Phase 2: AlphaEvolve Integration, Evolutionary Computation Governance  
- Phase 3: Formal Verification (Z3), Algorithmic Fairness, Cryptographic Integrity

### 🚨 **Critical Gaps Requiring Immediate Attention**
- Integration test success rate: 63.6% (7/11) → Target: 100%
- Service communication validation needed
- Performance optimization required
- Security hardening incomplete
- Documentation gaps identified

---

## 🎯 High-Value Task 1: Automated Tests & Coverage ≥90%

### **Objective**: Achieve comprehensive test coverage and reliability

### **Current Status**: 
- Test Success Rate: 63.6% (7/11 tests passing)
- Coverage: Needs analysis from `coverage.json`

### **Implementation Steps**:

1. **Analyze Current Coverage**
   ```bash
   # Parse existing coverage reports
   python -c "
   import json
   with open('coverage.json', 'r') as f:
       data = json.load(f)
   print('Current coverage:', data.get('totals', {}).get('percent_covered', 'Unknown'))
   "
   ```

2. **Identify Low-Coverage Modules**
   ```bash
   # Review comprehensive test report
   python -c "
   import json
   with open('acgs_comprehensive_test_report.json', 'r') as f:
       report = json.load(f)
   for test in report.get('test_results', []):
       if not test.get('passed', False):
           print(f'FAILING: {test.get(\"test_name\", \"Unknown\")}')
   "
   ```

3. **Execute Test Fixes**
   ```bash
   # Run existing test suite
   python test_comprehensive_acgs_validation.py
   
   # Fix integration tests (Task 1 from TaskMaster)
   tm get-task --id 1
   
   # Update Constitutional Council fixtures (Task 1.2)
   tm get-task --id 1.2
   ```

4. **Create Missing Tests**
   - Write unit tests for uncovered modules in `tests/unit/`
   - Add integration tests for cross-service communication
   - Implement mocking for external dependencies (LLM APIs, databases)

5. **Configure CI Pipeline**
   ```bash
   # Create GitHub Actions workflow
   mkdir -p .github/workflows
   # Add CI configuration with coverage requirements
   ```

### **Success Criteria**:
- ✅ Test success rate ≥90% (13/15 tests)
- ✅ Code coverage ≥90% across all modules
- ✅ CI pipeline fails if coverage drops below 90%
- ✅ All governance rule generators have acceptance tests

### **Deliverables**:
- Updated test files in `tests/` directory
- CI configuration in `.github/workflows/`
- Coverage report showing improvement metrics

---

## 🎯 High-Value Task 2: Governance Synthesis & Enforcement Hardening

### **Objective**: Ensure robust, verifiable policy synthesis and enforcement

### **Current Status**:
- Constitutional prompting implemented
- Z3 formal verification available
- OPA integration needs validation

### **Implementation Steps**:

1. **Validate Policy Synthesis Pipeline**
   ```bash
   # Test constitutional prompting
   python -c "
   from backend.gs_service.app.core.constitutional_prompting import ConstitutionalPromptBuilder
   # Test principle → Rego conversion
   "
   
   # Test Z3 formal verification
   python -c "
   from backend.fv_service.app.core.smt_solver_integration import Z3SMTSolver
   # Test SMT solving capabilities
   "
   ```

2. **Implement Rego Validation Pipeline**
   ```bash
   # Create validation script
   cat > scripts/validate_rego.py << 'EOF'
   #!/usr/bin/env python3
   """Validate all generated Rego policies for syntax and semantics"""
   import subprocess
   import sys
   
   def validate_rego_syntax(rego_file):
       """Run opa fmt and opa eval on Rego file"""
       try:
           subprocess.run(['opa', 'fmt', rego_file], check=True)
           subprocess.run(['opa', 'eval', '-d', rego_file, 'data'], check=True)
           return True
       except subprocess.CalledProcessError:
           return False
   
   # Add SMT verification logic here
   EOF
   
   chmod +x scripts/validate_rego.py
   ```

3. **Integrate Runtime Enforcement**
   ```bash
   # Test OPA middleware integration
   python test_comprehensive_features.py
   
   # Benchmark policy decision latency
   python performance_optimization.py
   ```

4. **Implement Caching Strategy**
   ```python
   # Add to Redis configuration
   POLICY_CACHE_CONFIG = {
       "opa_decisions": {"ttl": 300, "max_size": 1000},
       "principle_mappings": {"ttl": 1800, "max_size": 500}
   }
   ```

### **Success Criteria**:
- ✅ All generated Rego policies pass syntax validation
- ✅ SMT solver verifies 100% of safety-critical rules
- ✅ Policy decision latency <50ms (95th percentile)
- ✅ Runtime enforcement blocks/allows requests correctly

### **Deliverables**:
- `scripts/validate_rego.py` validation script
- Performance benchmark report
- Live demonstration of policy enforcement
- Updated generator code with inline documentation

---

## 🎯 High-Value Task 3: Performance & Scalability Audit

### **Objective**: Optimize system performance for production workloads

### **Current Status**:
- Performance optimization script exists
- Baseline metrics need establishment
- Bottlenecks need identification

### **Implementation Steps**:

1. **Establish Performance Baseline**
   ```bash
   # Run comprehensive performance analysis
   python performance_optimization.py
   
   # Generate performance report
   python -c "
   import json
   with open('performance_analysis_results.json', 'r') as f:
       data = json.load(f)
   print('Performance baseline established')
   "
   ```

2. **Identify and Optimize Hotspots**
   ```bash
   # Database query optimization
   psql -d acgs_db -f scripts/database_performance_optimization.sql
   
   # Implement caching layers
   # Redis for LLM responses, OPA decisions, principle queries
   ```

3. **Load Testing**
   ```bash
   # Simulate concurrent requests
   python -c "
   import asyncio
   import aiohttp
   import time
   
   async def load_test():
       # Implement 100+ concurrent request simulation
       pass
   
   asyncio.run(load_test())
   "
   ```

4. **Horizontal Scalability Testing**
   ```bash
   # Test Kubernetes scaling
   kubectl scale deployment acgs-services --replicas=5
   
   # Monitor performance under scale-out
   ```

### **Performance Targets**:
- Database queries: <100ms average
- LLM inference: <5 seconds
- Z3 verification: <2 seconds  
- Cryptographic operations: <200ms
- Overall API response: <1 second (95th percentile)

### **Success Criteria**:
- ✅ ≥30% latency reduction achieved
- ✅ Effective caching implementation
- ✅ Horizontal scaling validated
- ✅ Performance monitoring dashboard deployed

### **Deliverables**:
- Performance analysis report with before/after metrics
- Optimized database queries and indexes
- Caching implementation
- Kubernetes scaling configuration

---

## 🎯 High-Value Task 4: Security & Compliance Sweep

### **Objective**: Achieve zero critical vulnerabilities and security best practices

### **Current Status**:
- Security audit results available in `acgs_security_audit_*.json`
- Authentication system implemented
- Security hardening script exists

### **Implementation Steps**:

1. **Dependency Security Scan**
   ```bash
   # Scan Python dependencies
   pip-audit --format=json --output=security_scan_python.json
   
   # Scan for outdated packages
   pip list --outdated
   
   # Update vulnerable packages
   pip install --upgrade package_name
   ```

2. **Code Security Analysis**
   ```bash
   # Run bandit for Python security issues
   bandit -r src/ -f json -o security_bandit_report.json
   
   # Check for hardcoded secrets
   grep -r "password\|secret\|key" src/ --exclude-dir=__pycache__
   ```

3. **Security Hardening Implementation**
   ```bash
   # Execute security hardening
   python security_hardening.py
   
   # Validate security configuration
   python scripts/security_infrastructure_audit.py
   ```

4. **Add Security CI Pipeline**
   ```yaml
   # Add to .github/workflows/security.yml
   name: Security Scan
   on: [push, pull_request]
   jobs:
     security:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Run security scan
           run: |
             pip install bandit safety
             bandit -r src/
             safety check
   ```

### **Security Requirements**:
- JWT tokens with 256-bit keys
- SQL injection and XSS protection
- Rate limiting: 100 requests/minute per IP
- HTTPS/TLS 1.3 enforcement
- Multi-factor authentication support

### **Success Criteria**:
- ✅ Zero critical vulnerabilities
- ✅ All dependencies updated to secure versions
- ✅ Security CI pipeline implemented
- ✅ Penetration testing passed

### **Deliverables**:
- `security_bulletin.md` with findings and remediations
- Updated `requirements.txt` with secure versions
- Security CI pipeline configuration
- Security monitoring alerts

---

## 🎯 High-Value Task 5: Documentation & Developer Onboarding

### **Objective**: Enable rapid developer onboarding and system understanding

### **Current Status**:
- Extensive documentation exists in `docs/`
- README needs refresh for newcomers
- Quickstart guide missing

### **Implementation Steps**:

1. **Refresh Main README**
   ```bash
   # Update README.md with current status
   # Add badges for build, coverage, license
   # Include quick start instructions
   ```

2. **Create Developer Quickstart**
   ```bash
   # Create comprehensive quickstart guide
   mkdir -p docs/quickstart
   cat > docs/quickstart/README.md << 'EOF'
   # ACGS Developer Quickstart
   
   ## Prerequisites
   - Python 3.10+
   - Docker & Docker Compose
   - PostgreSQL
   
   ## Quick Setup
   1. Clone repository
   2. Install dependencies
   3. Start services
   4. Run sample governance scenario
   EOF
   ```

3. **Update Technical Documentation**
   ```bash
   # Review and update existing docs
   find docs/ -name "*.md" -exec grep -l "TODO\|FIXME\|XXX" {} \;
   
   # Update API documentation
   # Generate OpenAPI/Swagger docs
   ```

4. **Validate Documentation**
   ```bash
   # Test quickstart instructions
   # Ensure all commands work
   # Verify sample scenarios run successfully
   ```

### **Success Criteria**:
- ✅ Newcomer can set up system in <10 minutes
- ✅ All documentation is current and accurate
- ✅ API documentation is complete
- ✅ Troubleshooting guides are comprehensive

### **Deliverables**:
- Updated `README.md` with badges and quick start
- `docs/quickstart/README.md` comprehensive guide
- Updated API documentation
- Validated setup procedures

---

## 🔧 Execution Framework

### **Task Execution Order**:
1. **Week 1**: Tasks 1 & 4 (Tests & Security) - Foundation
2. **Week 2**: Tasks 2 & 3 (Governance & Performance) - Core Systems  
3. **Week 3**: Task 5 (Documentation) - Knowledge Transfer
4. **Week 4**: Integration & Validation - Final Polish

### **Progress Tracking**:
```bash
# Create progress tracking
cat > TASK_PROGRESS.md << 'EOF'
# ACGS Master Task Progress

## Task 1: Automated Tests & Coverage ≥90%
- [ ] Coverage analysis completed
- [ ] Missing tests identified  
- [ ] Test fixes implemented
- [ ] CI pipeline configured

## Task 2: Governance Synthesis & Enforcement
- [ ] Policy synthesis validated
- [ ] Rego validation pipeline created
- [ ] Runtime enforcement tested
- [ ] Performance benchmarked

## Task 3: Performance & Scalability Audit  
- [ ] Baseline established
- [ ] Hotspots optimized
- [ ] Load testing completed
- [ ] Scaling validated

## Task 4: Security & Compliance Sweep
- [ ] Dependencies scanned
- [ ] Vulnerabilities fixed
- [ ] Security CI implemented
- [ ] Compliance verified

## Task 5: Documentation & Developer Onboarding
- [ ] README refreshed
- [ ] Quickstart created
- [ ] API docs updated
- [ ] Setup validated
EOF
```

### **Quality Gates**:
- Each task must pass validation before proceeding
- All changes must be committed to feature branches
- Pull requests required for all major changes
- Documentation must be updated with each change

### **Success Metrics**:
- Test coverage: 63.6% → 90%+
- Performance: Establish baseline → 30% improvement
- Security: Current vulnerabilities → Zero critical
- Documentation: Gaps identified → Complete coverage
- Developer onboarding: Unknown → <10 minutes

---

## 🎉 Expected Outcomes

Upon completion of all 5 high-value tasks:

1. **Reliability**: 90%+ test coverage with robust CI/CD
2. **Governance**: Verified, performant policy synthesis and enforcement
3. **Performance**: Optimized system ready for production workloads
4. **Security**: Zero critical vulnerabilities with ongoing monitoring
5. **Usability**: Comprehensive documentation enabling rapid onboarding

**Total Estimated Effort**: 3-4 weeks with systematic execution
**Risk Mitigation**: Each task has rollback procedures and validation steps
**Continuous Integration**: All changes validated through automated testing

This framework provides a clear, actionable roadmap to achieve production readiness while maintaining the architectural integrity of the ACGS-PGP system.
